"""
Main extraction engine for converting legislation text to machine-readable rules.
Orchestrates the entire extraction pipeline with advanced prompting strategies.
"""

import asyncio
import logging
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

from .config import Config, ProcessingConfig
from .models import LegislationRule, ExtractionJob, ProcessingStatus
from .event_system import Event, event_bus
from .prompting_strategies import PromptingStrategies
from .openai_service import OpenAIService
from .utils import SafeJsonParser

logger = logging.getLogger(__name__)

@tool
def extract_rule_conditions(legislation_text: str, focus_area: str) -> str:
    """Extract specific rule conditions from legislation text."""
    
    prompt = f"""
    Extract specific rule conditions from the following legislation text, focusing on {focus_area}.
    
    Return a JSON object with conditions in json-rules-engine format.
    
    Text: {legislation_text}
    
    Focus on identifying:
    - Specific facts that can be evaluated
    - Comparison operators (equal, greaterThan, contains, etc.)
    - Values to compare against
    - Data domains (data_transfer, data_usage, data_storage) and roles (controller, processor, joint_controller)
    
    Return valid JSON only.
    """
    
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )
        
        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error extracting conditions: {str(e)}"

@tool
def analyze_data_domains(legislation_text: str) -> str:
    """Analyze and identify relevant data domains in legislation."""
    
    prompt = f"""
    Analyze the following legislation text and identify which data domains are relevant:
    - data_transfer
    - data_usage
    - data_storage
    
    Text: {legislation_text}
    
    Return a JSON object mapping each identified domain to its relevance and reasoning.
    """
    
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )
        
        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing domains: {str(e)}"

@tool
def identify_roles_responsibilities(legislation_text: str) -> str:
    """Identify roles and responsibilities in legislation."""
    
    prompt = f"""
    Identify the roles and responsibilities mentioned in this legislation:
    - controller
    - processor 
    - joint_controller
    
    Text: {legislation_text}
    
    For each role, identify their specific obligations and responsibilities.
    Return a JSON object with role mappings.
    """
    
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )
        
        response = client.chat.completions.create(
            model=Config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error identifying roles: {str(e)}"

class ExtractionResult:
    """Result of legislation extraction."""
    
    def __init__(self, rules: List[LegislationRule], summary: str, 
                 total_rules: int, processing_time: float,
                 embeddings: Optional[List[List[float]]] = None):
        self.rules = rules
        self.summary = summary
        self.total_rules = total_rules
        self.processing_time = processing_time
        self.embeddings = embeddings

class ExtractionEngine:
    """Main engine for extracting rules from legislation."""
    
    def __init__(self, openai_service: OpenAIService, rule_manager, 
                 standards_converter, ontology_manager):
        self.openai_service = openai_service
        self.rule_manager = rule_manager
        self.standards_converter = standards_converter
        self.ontology_manager = ontology_manager
        self.json_parser = SafeJsonParser()
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model=Config.CHAT_MODEL,
            openai_api_key=Config.API_KEY,
            openai_api_base=Config.BASE_URL
        )
        
        # Create react agent with tools
        self.tools = [
            extract_rule_conditions,
            analyze_data_domains, 
            identify_roles_responsibilities
        ]
        
        # Memory for conversation state
        self.memory = MemorySaver()
        
        # Create react agent
        self.agent = create_react_agent(
            self.llm,
            self.tools,
            checkpointer=self.memory
        )
        
        # Active extraction jobs
        self.active_jobs: Dict[str, ExtractionJob] = {}
    
    async def extract_from_text(
        self, 
        legislation_text: str, 
        article_reference: str = "", 
        source_file: str = "",
        applicable_countries: List[str] = None,
        adequacy_countries: List[str] = None,
        job_id: str = None
    ) -> ExtractionResult:
        """Extract rules from legislation text."""
        
        # Create job if not provided
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        # Create and track job
        job = ExtractionJob(
            job_id=job_id,
            source_file=source_file or "text_input",
            status=ProcessingStatus.IN_PROGRESS
        )
        self.active_jobs[job_id] = job
        
        try:
            start_time = datetime.utcnow()
            
            # Default to empty lists if not provided
            if applicable_countries is None:
                applicable_countries = []
            if adequacy_countries is None:
                adequacy_countries = []
            
            logger.info(f"Starting extraction for job {job_id}: {article_reference}")
            
            # Publish processing start event
            await event_bus.publish_event(Event(
                event_type="processing_started",
                data={
                    "job_id": job_id,
                    "source_file": source_file,
                    "article_reference": article_reference
                },
                source="extraction_engine"
            ))
            
            # Update job progress
            await self._update_job_progress(job_id, 10.0)
            
            # Get existing rules context
            existing_context = self.rule_manager.get_context_summary()
            
            # Create metadata context for LLM
            metadata_context = f"""
            LEGISLATION METADATA:
            - Applicable Countries: {', '.join(applicable_countries) if applicable_countries else 'Not specified'}
            - Adequacy Countries: {', '.join(adequacy_countries) if adequacy_countries else 'None specified'}
            """
            
            # Step 1: Apply advanced prompting strategies with context
            await self._update_job_progress(job_id, 20.0)
            cot_analysis = await self._apply_chain_of_thought(legislation_text, existing_context + metadata_context)
            
            await self._update_job_progress(job_id, 35.0)
            moe_analysis = await self._apply_mixture_of_experts(legislation_text, existing_context + metadata_context)
            
            await self._update_job_progress(job_id, 50.0)
            mot_analysis = await self._apply_mixture_of_thought(legislation_text, existing_context + metadata_context)
            
            await self._update_job_progress(job_id, 65.0)
            mor_analysis = await self._apply_mixture_of_reasoning(legislation_text, existing_context + metadata_context)
            
            # Step 2: Use react agent for comprehensive analysis
            await self._update_job_progress(job_id, 75.0)
            agent_analysis = await self._run_react_agent(legislation_text, article_reference)
            
            # Step 3: Synthesize all analyses into structured rules
            await self._update_job_progress(job_id, 85.0)
            rules = await self._synthesize_rules(
                legislation_text, 
                article_reference,
                source_file,
                existing_context,
                metadata_context,
                applicable_countries,
                adequacy_countries,
                cot_analysis,
                moe_analysis, 
                mot_analysis,
                mor_analysis,
                agent_analysis
            )
            
            # Step 4: Generate embeddings for rules
            await self._update_job_progress(job_id, 95.0)
            embeddings = None
            if rules:
                rule_texts = [f"{rule.description} {rule.source_article}" for rule in rules]
                embeddings = await self.openai_service.get_embeddings(rule_texts)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Update job completion
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = end_time
            job.extracted_rules_count = len(rules)
            job.progress = 100.0
            
            # Create result
            result = ExtractionResult(
                rules=rules,
                summary=f"Extracted {len(rules)} rules from {article_reference}",
                total_rules=len(rules),
                processing_time=processing_time,
                embeddings=embeddings
            )
            
            # Publish completion event
            await event_bus.publish_event(Event(
                event_type="processing_completed",
                data={
                    "job_id": job_id,
                    "rules_extracted": len(rules),
                    "processing_time": processing_time
                },
                source="extraction_engine"
            ))
            
            logger.info(f"Extraction completed for job {job_id}: {len(rules)} rules in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            # Update job failure
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            
            # Publish failure event
            await event_bus.publish_event(Event(
                event_type="processing_failed",
                data={
                    "job_id": job_id,
                    "error": str(e)
                },
                source="extraction_engine"
            ))
            
            logger.error(f"Extraction failed for job {job_id}: {e}")
            raise
        finally:
            # Clean up job after some time
            asyncio.create_task(self._cleanup_job(job_id, delay=300))  # 5 minutes
    
    async def extract_batch(
        self, 
        extraction_tasks: List[Dict[str, Any]]
    ) -> List[ExtractionResult]:
        """Extract rules from multiple texts in parallel."""
        
        logger.info(f"Starting batch extraction of {len(extraction_tasks)} tasks")
        
        # Create semaphore to limit concurrent extractions
        semaphore = asyncio.Semaphore(Config.MAX_CONCURRENT_PROCESSES)
        
        async def extract_with_semaphore(task):
            async with semaphore:
                return await self.extract_from_text(**task)
        
        # Run extractions concurrently
        tasks = [extract_with_semaphore(task) for task in extraction_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = []
        failed_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch extraction failed: {result}")
                failed_count += 1
            else:
                successful_results.append(result)
        
        logger.info(f"Batch extraction completed: {len(successful_results)} successful, {failed_count} failed")
        return successful_results
    
    async def _apply_chain_of_thought(self, legislation_text: str, existing_context: str = "") -> str:
        """Apply Chain of Thought prompting strategy."""
        prompt = PromptingStrategies.chain_of_thought_prompt(legislation_text, existing_context)
        
        messages = [
            SystemMessage(content="You are an expert legal analyst. Use step-by-step reasoning."),
            HumanMessage(content=prompt)
        ]
        
        return await self.openai_service.chat_completion(messages)
    
    async def _apply_mixture_of_experts(self, legislation_text: str, existing_context: str = "") -> str:
        """Apply Mixture of Experts prompting strategy."""
        prompt = PromptingStrategies.mixture_of_experts_prompt(legislation_text, existing_context)
        
        messages = [
            SystemMessage(content="You are a panel of legal experts with different specializations."),
            HumanMessage(content=prompt)
        ]
        
        return await self.openai_service.chat_completion(messages)
    
    async def _apply_mixture_of_thought(self, legislation_text: str, existing_context: str = "") -> str:
        """Apply Mixture of Thought prompting strategy."""
        prompt = PromptingStrategies.mixture_of_thought_prompt(legislation_text, existing_context)
        
        messages = [
            SystemMessage(content="Apply diverse thinking approaches to comprehensive analysis."),
            HumanMessage(content=prompt)
        ]
        
        return await self.openai_service.chat_completion(messages)
    
    async def _apply_mixture_of_reasoning(self, legislation_text: str, existing_context: str = "") -> str:
        """Apply Mixture of Reasoning prompting strategy.""" 
        prompt = PromptingStrategies.mixture_of_reasoning_prompt(legislation_text, existing_context)
        
        messages = [
            SystemMessage(content="Use multiple reasoning strategies for thorough analysis."),
            HumanMessage(content=prompt)
        ]
        
        return await self.openai_service.chat_completion(messages)
    
    async def _run_react_agent(self, legislation_text: str, article_reference: str) -> str:
        """Run the react agent for comprehensive analysis."""
        try:
            config = {"configurable": {"thread_id": f"analysis_{datetime.utcnow().timestamp()}"}}
            
            message = f"""
            Analyze the following legislation and use all available tools to extract comprehensive information:
            
            Article: {article_reference}
            Text: {legislation_text}
            
            Use the tools to:
            1. Extract specific rule conditions
            2. Analyze data domains
            3. Identify roles and responsibilities
            
            Provide a comprehensive analysis that can be used to create machine-readable rules.
            """
            
            result = self.agent.invoke(
                {"messages": [HumanMessage(content=message)]},
                config
            )
            
            # Extract the final message content
            if result and "messages" in result:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif isinstance(last_message, dict) and 'content' in last_message:
                    return last_message['content']
            
            return "Agent analysis completed but no content returned"
            
        except Exception as e:
            logger.error(f"Error running react agent: {e}")
            return f"Error in agent analysis: {str(e)}"
    
    async def _synthesize_rules(
        self, 
        legislation_text: str,
        article_reference: str,
        source_file: str,
        existing_context: str,
        metadata_context: str,
        applicable_countries: List[str],
        adequacy_countries: List[str],
        cot_analysis: str,
        moe_analysis: str, 
        mot_analysis: str,
        mor_analysis: str,
        agent_analysis: str
    ) -> List[LegislationRule]:
        """Synthesize all analyses into structured rules."""
        
        # Handle JSON serialization first, before the f-string
        applicable_countries_json = json.dumps(applicable_countries)
        adequacy_countries_json = json.dumps(adequacy_countries)
        
        synthesis_prompt = f"""
        Based on the comprehensive analyses below, create machine-readable rules in JSON format that align with json-rules-engine structure.
        
        EXISTING RULES CONTEXT:
        {existing_context}
        
        METADATA CONTEXT:
        {metadata_context}
        
        ORIGINAL LEGISLATION:
        Article: {article_reference}
        Source File: {source_file}
        Text: {legislation_text}
        
        ANALYSIS RESULTS:
        
        Chain of Thought Analysis:
        {cot_analysis}
        
        Mixture of Experts Analysis:
        {moe_analysis}
        
        Mixture of Thought Analysis:
        {mot_analysis}
        
        Mixture of Reasoning Analysis:
        {mor_analysis}
        
        Agent Tool Analysis:
        {agent_analysis}
        
        REQUIREMENTS:
        1. Create rules in json-rules-engine format with conditions containing 'all', 'any', or 'not' keys
        2. Each condition must have: fact, operator, value, description, data_domain, role, reasoning
        3. Use exact enum values: data_domain from ["data_transfer", "data_usage", "data_storage"] - leave empty array if not in document
        4. Use exact enum values: role from ["controller", "processor", "joint_controller"] - leave null if not in document
        5. Use exact enum values: operator from ["equal", "notEqual", "greaterThan", "lessThan", "greaterThanInclusive", "lessThanInclusive", "contains", "doesNotContain", "in", "notIn"]
        6. Use exact enum values: primary_impacted_role from ["controller", "processor", "joint_controller"] - leave null if not clearly specified in document
        7. Use exact enum values: data_category from ["personal_data", "sensitive_data", "biometric_data", "health_data", "financial_data", "location_data", "behavioral_data", "identification_data"] - leave empty array if not in document
        8. Use the provided country metadata for applicable_countries and adequacy_countries
        9. Provide confidence scores (0.0-1.0) for each rule
        10. Consider existing rules context to maintain consistency and avoid duplication
        11. DO NOT make up roles or data categories that are not explicitly mentioned in the legislation
        
        Return a JSON array of rules. Each rule must follow this exact structure:
        {{
            "id": "unique_id_based_on_content",
            "name": "rule_name", 
            "description": "human_readable_description",
            "source_article": "{article_reference}",
            "source_file": "{source_file}",
            "conditions": {{
                "all": [
                    {{
                        "fact": "fact_name",
                        "operator": "equal",
                        "value": "comparison_value",
                        "path": "$.optional.json.path",
                        "description": "condition_description",
                        "data_domain": [],
                        "role": null,
                        "reasoning": "why_this_condition_was_extracted"
                    }}
                ]
            }},
            "event": {{
                "type": "compliance_required",
                "params": {{
                    "action": "specific_action_required"
                }}
            }},
            "priority": 1,
            "primary_impacted_role": null,
            "secondary_impacted_role": null,
            "data_category": [],
            "applicable_countries": {applicable_countries_json},
            "adequacy_countries": {adequacy_countries_json},
            "confidence_score": 0.85
        }}
        
        Return ONLY valid JSON array with exact enum values as specified OR null for roles/empty arrays for categories not found in document, no other text.
        """
        
        messages = [
            SystemMessage(content="You are a legal-tech expert. Return only valid JSON with exact enum values as specified."),
            HumanMessage(content=synthesis_prompt)
        ]
        
        response = await self.openai_service.chat_completion(messages)
        
        # Parse JSON response safely
        parsed_data = self.json_parser.parse_json_response(response)
        
        if "error" in parsed_data:
            logger.error(f"Failed to parse rules JSON: {parsed_data}")
            return []
        
        # Convert to Pydantic models
        rules = []
        try:
            if isinstance(parsed_data, list):
                rule_data_list = parsed_data
            elif isinstance(parsed_data, dict) and "rules" in parsed_data:
                rule_data_list = parsed_data["rules"]
            else:
                rule_data_list = [parsed_data]
            
            for rule_data in rule_data_list:
                try:
                    # Ensure required fields have defaults
                    rule_data.setdefault("priority", 1)
                    rule_data.setdefault("confidence_score", 0.8)
                    rule_data.setdefault("source_article", article_reference)
                    rule_data.setdefault("source_file", source_file)
                    rule_data.setdefault("applicable_countries", applicable_countries)
                    rule_data.setdefault("adequacy_countries", adequacy_countries)
                    
                    # Create rule - Pydantic v2 will handle validation and enum conversion
                    rule = LegislationRule(**rule_data)
                    rules.append(rule)
                    
                except Exception as e:
                    logger.warning(f"Skipping invalid rule: {e}")
                    logger.debug(f"Rule data: {rule_data}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error creating rule objects: {e}")
            
        return rules
    
    async def _update_job_progress(self, job_id: str, progress: float):
        """Update job progress."""
        if job_id in self.active_jobs:
            self.active_jobs[job_id].progress = progress
            
            # Publish progress event
            await event_bus.publish_event(Event(
                event_type="processing_progress",
                data={
                    "job_id": job_id,
                    "progress": progress
                },
                source="extraction_engine"
            ))
    
    async def _cleanup_job(self, job_id: str, delay: int = 300):
        """Clean up job after delay."""
        await asyncio.sleep(delay)
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]
            logger.debug(f"Cleaned up job: {job_id}")
    
    def get_job_status(self, job_id: str) -> Optional[ExtractionJob]:
        """Get status of a specific job."""
        return self.active_jobs.get(job_id)
    
    def get_all_jobs(self) -> Dict[str, ExtractionJob]:
        """Get all active jobs."""
        return self.active_jobs.copy()
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel an active job."""
        if job_id in self.active_jobs:
            self.active_jobs[job_id].status = ProcessingStatus.CANCELLED
            logger.info(f"Cancelled job: {job_id}")
            return True
        return False

# Global extraction engine instance
extraction_engine = None

async def initialize_extraction_engine(openai_service, rule_manager, 
                                     standards_converter, ontology_manager) -> ExtractionEngine:
    """Initialize the global extraction engine."""
    global extraction_engine
    extraction_engine = ExtractionEngine(
        openai_service, rule_manager, standards_converter, ontology_manager
    )
    logger.info("Extraction engine initialized successfully")
    return extraction_engine

def get_extraction_engine() -> ExtractionEngine:
    """Get the global extraction engine instance."""
    return extraction_engine