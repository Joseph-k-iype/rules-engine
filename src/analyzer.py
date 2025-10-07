"""
Main legislation analyzer with enhanced dual action inference, decision-making, chunking support, and whole document analysis.
Enhanced with decision inference capabilities for yes/no/maybe outcomes.
"""
import json
import logging
from datetime import datetime
from typing import Any, List, Dict, Union, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import re

from .config import Config
from .models.rules import LegislationRule, ExtractionResult
from .models.base_models import CountryMetadata, DocumentChunk
from .models.enums import DataRole, DataCategory
from .services.openai_service import OpenAIService
from .services.metadata_manager import MetadataManager
from .services.rule_manager import RuleManager
from .processors.pdf_processor import MultiLevelPDFProcessor
from .converters.standards_converter import StandardsConverter
from .prompting.strategies import PromptingStrategies
from .utils.json_parser import SafeJsonParser
from .tools.langchain_tools import (
    extract_rule_conditions, analyze_data_domains, identify_roles_responsibilities,
    infer_data_processing_actions, infer_compliance_verification_actions,
    infer_data_subject_rights_actions, infer_user_actionable_tasks,
    infer_user_compliance_tasks, infer_user_rights_support_tasks,
    infer_decision_scenarios, infer_conditional_permissions
)

logger = logging.getLogger(__name__)


class LegislationAnalyzer:
    """Main analyzer with enhanced dual action inference, decision-making, chunking support, and whole document analysis."""

    def __init__(self):
        self.openai_service = OpenAIService()
        self.json_parser = SafeJsonParser()
        self.rule_manager = RuleManager()
        self.metadata_manager = MetadataManager()
        self.multi_level_processor = MultiLevelPDFProcessor()
        self.standards_converter = StandardsConverter()

        # Initialize LangChain model
        self.llm = ChatOpenAI(
            model=Config.CHAT_MODEL,
            openai_api_key=Config.API_KEY,
            openai_api_base=Config.BASE_URL
        )

        # Create react agent with all tools including decision inference
        self.tools = [
            extract_rule_conditions,
            analyze_data_domains, 
            identify_roles_responsibilities,
            infer_data_processing_actions,
            infer_compliance_verification_actions,
            infer_data_subject_rights_actions,
            infer_user_actionable_tasks,
            infer_user_compliance_tasks,
            infer_user_rights_support_tasks,
            infer_decision_scenarios,
            infer_conditional_permissions
        ]

        self.memory = MemorySaver()
        self.agent = create_react_agent(self.llm, self.tools, checkpointer=self.memory)

    async def process_legislation_folder(self, folder_path: str = None) -> ExtractionResult:
        """Process all configured legislation entries with decision inference."""
        if folder_path is None:
            folder_path = Config.LEGISLATION_PDF_PATH

        import os
        os.makedirs(folder_path, exist_ok=True)

        processing_entries = self.metadata_manager.get_all_processing_entries()

        if not processing_entries:
            logger.warning("No processing entries found in metadata configuration")
            return ExtractionResult(
                rules=[],
                summary="No configured entries to process",
                total_rules=0,
                total_actions=0,
                total_user_actions=0,
                total_decisions=0,
                processing_time=0.0
            )

        all_new_rules = []
        documents_processed = {}
        chunking_metadata = {}
        start_time = datetime.utcnow()

        for entry_id, metadata in processing_entries:
            try:
                logger.info(f"Processing entry: {entry_id}")

                entry_documents = self.multi_level_processor.process_country_documents(
                    entry_id, metadata, folder_path
                )

                if not entry_documents:
                    logger.warning(f"No documents found for entry {entry_id}")
                    continue

                documents_processed[entry_id] = list(entry_documents.keys())

                # Track chunking metadata
                for level, content in entry_documents.items():
                    if isinstance(content, list):  # Chunked document
                        chunking_metadata[f"{entry_id}_{level}"] = {
                            "chunks": len(content),
                            "chunk_size": Config.CHUNK_SIZE,
                            "overlap_size": Config.OVERLAP_SIZE
                        }

                result = await self.analyze_legislation_with_levels(
                    entry_documents=entry_documents,
                    entry_id=entry_id,
                    metadata=metadata
                )

                all_new_rules.extend(result.rules)

            except Exception as e:
                logger.error(f"Error processing entry {entry_id}: {e}")
                continue

        end_time = datetime.utcnow()
        total_processing_time = (end_time - start_time).total_seconds()
        total_actions = sum(len(rule.actions) for rule in all_new_rules)
        total_user_actions = sum(len(rule.user_actions) for rule in all_new_rules)
        total_decisions = sum(len(rule.decisions) for rule in all_new_rules)

        if all_new_rules:
            rule_texts = [f"{rule.description} {rule.source_article}" for rule in all_new_rules]
            embeddings = await self.openai_service.get_embeddings(rule_texts)
        else:
            embeddings = []

        if all_new_rules:
            self.rule_manager.save_rules(all_new_rules)

        integrated_rules = []
        for rule in all_new_rules:
            try:
                integrated_rule = self.standards_converter.json_rules_to_integrated(rule)
                integrated_rules.append(integrated_rule)
            except Exception as e:
                logger.warning(f"Error converting rule {rule.id} to integrated format: {e}")
                continue

        result = ExtractionResult(
            rules=all_new_rules,
            summary=f"Processed {len(processing_entries)} entries, extracted {len(all_new_rules)} rules with {total_actions} rule actions, {total_user_actions} user actions, and {total_decisions} decisions",
            total_rules=len(all_new_rules),
            total_actions=total_actions,
            total_user_actions=total_user_actions,
            total_decisions=total_decisions,
            processing_time=total_processing_time,
            embeddings=embeddings,
            integrated_rules=integrated_rules,
            documents_processed=documents_processed,
            chunking_metadata=chunking_metadata
        )

        return result

    async def analyze_legislation_with_levels(
        self, 
        entry_documents: Dict[str, Union[str, List[DocumentChunk]]],
        entry_id: str,
        metadata: CountryMetadata
    ) -> ExtractionResult:
        """Analyze legislation from multiple document levels with chunking support, whole document analysis, and decision inference."""
        start_time = datetime.utcnow()

        try:
            logger.info(f"Starting comprehensive analysis with decision inference for entry: {entry_id}")
            logger.info(f"Countries: {metadata.country}")

            existing_context = self.rule_manager.get_context_summary()

            metadata_context = f"""
            ENTRY METADATA:
            - Entry ID: {entry_id}
            - Applicable Countries: {', '.join(metadata.country)}
            - Adequacy Countries: {', '.join(metadata.adequacy_country) if metadata.adequacy_country else 'None specified'}
            - Document Levels Available: {', '.join(entry_documents.keys())}
            """

            all_rules = []

            # Enhanced: First pass - comprehensive document understanding with decision inference
            for level, content in entry_documents.items():
                logger.info(f"Performing comprehensive analysis with decision inference of {level} document...")

                if isinstance(content, list):  # Chunked document
                    # For chunked documents, first get overall understanding
                    full_text = "\n\n".join([chunk.content for chunk in content])
                    comprehensive_analysis = await self._apply_comprehensive_document_analysis(
                        full_text, existing_context + metadata_context, level, f"Full document with {len(content)} chunks"
                    )

                    # Then process each chunk with context of the whole document
                    for chunk in content:
                        chunk_info = f"Chunk {chunk.chunk_index + 1} of {chunk.total_chunks} (positions {chunk.start_pos}-{chunk.end_pos})"

                        chunk_rules = await self._process_text_chunk_with_context(
                            text=chunk.content,
                            chunk_reference=chunk.chunk_id,
                            entry_id=entry_id,
                            level=level,
                            metadata=metadata,
                            existing_context=existing_context,
                            metadata_context=metadata_context,
                            chunk_info=chunk_info,
                            comprehensive_analysis=comprehensive_analysis
                        )

                        all_rules.extend(chunk_rules)
                        logger.info(f"Processed {len(chunk_rules)} rules from chunk {chunk.chunk_index + 1}")

                else:  # Single document
                    comprehensive_analysis = await self._apply_comprehensive_document_analysis(
                        content, existing_context + metadata_context, level, ""
                    )

                    level_rules = await self._process_text_chunk_with_context(
                        text=content,
                        chunk_reference=None,
                        entry_id=entry_id,
                        level=level,
                        metadata=metadata,
                        existing_context=existing_context,
                        metadata_context=metadata_context,
                        chunk_info="",
                        comprehensive_analysis=comprehensive_analysis
                    )

                    all_rules.extend(level_rules)
                    logger.info(f"Processed {len(level_rules)} rules from {level} document")

            if all_rules:
                rule_texts = [f"{rule.description} {rule.source_article}" for rule in all_rules]
                embeddings = await self.openai_service.get_embeddings(rule_texts)
            else:
                embeddings = []

            integrated_rules = []
            for rule in all_rules:
                try:
                    integrated_rule = self.standards_converter.json_rules_to_integrated(rule)
                    integrated_rules.append(integrated_rule)
                except Exception as e:
                    logger.warning(f"Error converting rule {rule.id} to integrated format: {e}")
                    continue

            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            total_actions = sum(len(rule.actions) for rule in all_rules)
            total_user_actions = sum(len(rule.user_actions) for rule in all_rules)
            total_decisions = sum(len(rule.decisions) for rule in all_rules)

            result = ExtractionResult(
                rules=all_rules,
                summary=f"Extracted {len(all_rules)} rules with {total_actions} rule actions, {total_user_actions} user actions, and {total_decisions} decisions from {entry_id}",
                total_rules=len(all_rules),
                total_actions=total_actions,
                total_user_actions=total_user_actions,
                total_decisions=total_decisions,
                processing_time=processing_time,
                embeddings=embeddings,
                integrated_rules=integrated_rules,
                documents_processed={entry_id: list(entry_documents.keys())}
            )

            logger.info(f"Analysis completed: {len(all_rules)} rules with {total_actions} rule actions, {total_user_actions} user actions, and {total_decisions} decisions extracted in {processing_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Error analyzing legislation with levels: {e}")
            raise

    async def _apply_comprehensive_document_analysis(self, legislation_text: str, existing_context: str = "", level: str = "level_1", chunk_info: str = "") -> str:
        """Apply comprehensive document analysis to understand the entire document."""
        prompt = PromptingStrategies.comprehensive_document_analysis_prompt(legislation_text, existing_context, level, chunk_info)

        messages = [
            SystemMessage(content="You are a legal text analyst. Analyze the ENTIRE document comprehensively. Use simple, clear English without document references."),
            HumanMessage(content=prompt)
        ]

        return await self.openai_service.chat_completion(messages)

    async def _process_text_chunk_with_context(
        self,
        text: str,
        chunk_reference: Optional[str],
        entry_id: str,
        level: str,
        metadata: CountryMetadata,
        existing_context: str,
        metadata_context: str,
        chunk_info: str,
        comprehensive_analysis: str
    ) -> List[LegislationRule]:
        """Process a single text chunk with full document context and decision inference."""

        # Step 1: Focused analysis with comprehensive context
        focused_analysis = await self._apply_focused_analysis_with_context(
            text, existing_context + metadata_context, level, chunk_info, comprehensive_analysis
        )

        # Step 2: Expert verification
        verified_analysis = await self._apply_expert_verification(
            text, focused_analysis, level
        )

        # Step 3: Use react agent for DUAL action inference with document context
        agent_analysis = await self._run_dual_action_inference_agent_with_context(
            text, f"{entry_id} - {level}", metadata.country, chunk_reference, comprehensive_analysis
        )

        # Step 4: Decision inference
        decision_analysis = await self._run_decision_inference_agent(
            text, focused_analysis, agent_analysis, f"{entry_id} - {level}", metadata.country
        )

        # Step 5: Synthesize into rules with DUAL actions, full context, and decisions
        rules = await self._synthesize_rules_with_dual_actions_decisions_and_context(
            legislation_text=text,
            article_reference=f"{entry_id} - {level}",
            source_files={
                "level_1": metadata.file_level_1,
                "level_2": metadata.file_level_2,
                "level_3": metadata.file_level_3
            },
            document_level=level,
            chunk_reference=chunk_reference,
            existing_context=existing_context,
            metadata_context=metadata_context,
            applicable_countries=metadata.country,
            adequacy_countries=metadata.adequacy_country,
            focused_analysis=focused_analysis,
            verified_analysis=verified_analysis,
            agent_analysis=agent_analysis,
            comprehensive_analysis=comprehensive_analysis,
            decision_analysis=decision_analysis
        )

        return rules

    async def _apply_focused_analysis_with_context(self, legislation_text: str, existing_context: str = "", level: str = "level_1", chunk_info: str = "", comprehensive_analysis: str = "") -> str:
        """Apply focused analysis with comprehensive document context."""
        context_section = f"\n\nCOMPREHENSIVE DOCUMENT ANALYSIS:\n{comprehensive_analysis}\n" if comprehensive_analysis else ""
        prompt = PromptingStrategies.focused_analysis_prompt(legislation_text, existing_context + context_section, level, chunk_info)

        messages = [
            SystemMessage(content="You are a legal text analyst. Analyze only what is present in the legislation text using the comprehensive document context. Use simple, clear English without document references."),
            HumanMessage(content=prompt)
        ]

        return await self.openai_service.chat_completion(messages)

    async def _apply_expert_verification(self, legislation_text: str, preliminary_analysis: str, level: str = "level_1") -> str:
        """Apply expert verification to validate findings."""
        prompt = PromptingStrategies.expert_verification_prompt(legislation_text, preliminary_analysis, level)

        messages = [
            SystemMessage(content="You are a legal compliance expert. Verify analysis accuracy against source text. Use simple, clear English without document references."),
            HumanMessage(content=prompt)
        ]

        return await self.openai_service.chat_completion(messages)

    async def _run_dual_action_inference_agent_with_context(self, legislation_text: str, article_reference: str, countries: List[str], chunk_reference: Optional[str] = None, comprehensive_analysis: str = "") -> str:
        """Run react agent for DUAL action inference with comprehensive document context."""
        try:
            config = {"configurable": {"thread_id": f"analysis_{datetime.utcnow().timestamp()}"}}

            chunk_info = f" (Chunk: {chunk_reference})" if chunk_reference else ""
            context_section = f"\n\nCOMPREHENSIVE DOCUMENT CONTEXT:\n{comprehensive_analysis}\n" if comprehensive_analysis else ""

            message = f"""
            Analyze the following legislation text and infer BOTH organizational rule actions AND practical user actions.
            {context_section}

            Article: {article_reference}{chunk_info}
            Countries: {', '.join(countries)}
            Text: {legislation_text}

            Use the available tools to:
            1. Identify specific rule conditions related to data processing
            2. Analyze data domains and categories involved
            3. Identify roles and responsibilities for data handling

            ORGANIZATIONAL ACTION INFERENCE (Rule Actions):
            4. Infer data processing actions required by organizations/controllers/processors
            5. Focus on practical data operations like encryption, masking, access controls
            6. Infer compliance verification actions for organizational compliance
            7. Infer actions related to data subject rights that organizations must implement

            USER ACTION INFERENCE (User Actions):
            8. Infer user actionable tasks that individuals can perform with their data
            9. Focus on individual data protection like personal encryption, privacy settings
            10. Infer user compliance tasks for individual compliance
            11. Infer user rights support tasks that individuals can implement

            FOCUS CONSTRAINTS:
            - RULE ACTIONS: Organizational, policy-level, systematic data actions
            - USER ACTIONS: Individual, practical, implementable data tasks
            - Base ALL actions on explicit legislative requirements
            - Focus on concrete data operations: encryption, masking, access control, deletion, backup
            - Ensure actions reference specific articles and are in simple English without document references
            - Use the comprehensive document context to understand relationships

            Provide analysis that enables creation of machine-readable rules with BOTH organizational rule actions AND practical user actions.
            """

            result = self.agent.invoke(
                {"messages": [HumanMessage(content=message)]},
                config
            )

            if result and "messages" in result:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif isinstance(last_message, dict) and 'content' in last_message:
                    return last_message['content']

            return "Agent analysis completed but no content returned"

        except Exception as e:
            logger.error(f"Error running dual action inference agent: {e}")
            return f"Error in agent analysis: {str(e)}"

    async def _run_decision_inference_agent(self, legislation_text: str, focused_analysis: str, agent_analysis: str, article_reference: str, countries: List[str]) -> str:
        """Run react agent for decision inference with yes/no/maybe outcomes."""
        try:
            config = {"configurable": {"thread_id": f"decision_analysis_{datetime.utcnow().timestamp()}"}}

            message = f"""
            Analyze the following legislation text and previous analyses to identify decision scenarios with yes/no/maybe outcomes.

            Article: {article_reference}
            Countries: {', '.join(countries)}
            Text: {legislation_text}

            Previous Focused Analysis: {focused_analysis}
            Previous Agent Analysis: {agent_analysis}

            Use the available tools to:
            1. Infer decision scenarios that result in yes/no/maybe outcomes
            2. Identify conditional permissions and their requirements
            3. Focus on practical decision points like:
               - Cross-border data transfers (allowed/prohibited/conditional)
               - Data processing authorizations (permitted/forbidden/requires safeguards)
               - Consent requirements (required/not required/depends on circumstances)
               - Data sharing permissions (allowed/prohibited/needs additional protection)
               - Automated decision making (permitted/forbidden/requires oversight)
               - Compliance assessments (compliant/non-compliant/needs additional measures)

            DECISION INFERENCE REQUIREMENTS:
            - Base ALL decisions on explicit legislative requirements
            - Identify clear conditions for yes/no/maybe outcomes
            - Link decisions to specific actions required for compliance
            - Use simple, clear English without legal jargon or document references
            - Focus on practical, implementable decision scenarios
            - Ensure decisions are logical and traceable to source text

            EXAMPLES OF DECISION SCENARIOS:
            - "Data transfer to third country is allowed if adequate protection is ensured" → MAYBE (requires adequate protection)
            - "Processing sensitive data requires explicit consent" → NO unless consent obtained
            - "Automated decision making requires human oversight" → MAYBE (requires human oversight)
            - "Personal data must be deleted when purpose is fulfilled" → YES for deletion when purpose ends

            Provide decision analysis that enables creation of machine-readable decision rules with clear yes/no/maybe logic.
            """

            result = self.agent.invoke(
                {"messages": [HumanMessage(content=message)]},
                config
            )

            if result and "messages" in result:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                elif isinstance(last_message, dict) and 'content' in last_message:
                    return last_message['content']

            return "Decision inference completed but no content returned"

        except Exception as e:
            logger.error(f"Error running decision inference agent: {e}")
            return f"Error in decision analysis: {str(e)}"

    async def _synthesize_rules_with_dual_actions_decisions_and_context(
        self, 
        legislation_text: str,
        article_reference: str,
        source_files: Dict[str, Optional[str]],
        document_level: str,
        chunk_reference: Optional[str],
        existing_context: str,
        metadata_context: str,
        applicable_countries: List[str],
        adequacy_countries: List[str],
        focused_analysis: str,
        verified_analysis: str,
        agent_analysis: str,
        comprehensive_analysis: str,
        decision_analysis: str
    ) -> List[LegislationRule]:
        """Synthesize all analyses into comprehensive structured rules with maximum rule extraction and decision support."""

        applicable_countries_json = json.dumps(applicable_countries)
        adequacy_countries_json = json.dumps(adequacy_countries)
        source_files_json = json.dumps(source_files)

        synthesis_prompt = PromptingStrategies.synthesis_prompt_template(
            legislation_text=legislation_text,
            article_reference=article_reference,
            source_files=source_files_json,
            document_level=document_level,
            chunk_reference=chunk_reference or "none",
            existing_context=existing_context,
            metadata_context=metadata_context,
            applicable_countries=applicable_countries_json,
            adequacy_countries=adequacy_countries_json,
            focused_analysis=focused_analysis,
            verified_analysis=verified_analysis,
            agent_analysis=agent_analysis,
            comprehensive_analysis=comprehensive_analysis,
            decision_analysis=decision_analysis
        )

        messages = [
            SystemMessage(content="You are a comprehensive legal-tech expert. Extract EVERY possible rule and decision from the legislation. Create multiple specific rules rather than trying to combine everything. Use simple, clear English without document references. Focus on practical data operations and decision scenarios."),
            HumanMessage(content=synthesis_prompt)
        ]

        response = await self.openai_service.chat_completion(messages)

        parsed_data = self.json_parser.parse_json_response(response)

        if "error" in parsed_data:
            logger.error(f"Failed to parse rules JSON: {parsed_data}")
            return []

        rules = []
        try:
            if isinstance(parsed_data, list):
                rule_data_list = parsed_data
            elif isinstance(parsed_data, dict) and "rules" in parsed_data:
                rule_data_list = parsed_data["rules"]
            else:
                rule_data_list = [parsed_data] if parsed_data else []

            for rule_data in rule_data_list:
                try:
                    # Ensure critical fields are populated
                    rule_data.setdefault("id", f"synthesis_rule_{datetime.utcnow().timestamp()}")
                    rule_data.setdefault("name", "Legislative Rule")
                    rule_data.setdefault("description", "Rule extracted from legislation")

                    # CORRECTED: Use proper prompting strategies for role inference
                    if not rule_data.get("primary_impacted_role"):
                        rule_data["primary_impacted_role"] = await self._infer_primary_role_advanced(legislation_text)

                    # CORRECTED: Use proper prompting strategies for data category inference
                    if not rule_data.get("data_category") or len(rule_data.get("data_category", [])) == 0:
                        rule_data["data_category"] = await self._infer_data_categories_advanced(legislation_text)

                    # Process remaining fields with validation
                    rule_data = self._validate_and_fix_rule_data(rule_data, article_reference, source_files, applicable_countries, adequacy_countries, document_level, chunk_reference)

                    # Validate and create the rule using Pydantic
                    rule = LegislationRule.model_validate(rule_data)
                    rules.append(rule)
                    logger.info(f"Successfully created comprehensive rule: {rule.name} with {len(rule.actions)} actions, {len(rule.user_actions)} user actions, and {len(rule.decisions)} decisions")

                except Exception as e:
                    logger.warning(f"Skipping invalid rule due to error: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error processing comprehensive rule data: {e}")

        # If no rules were created, create minimal rules to ensure coverage
        if not rules:
            logger.warning("No rules could be parsed, creating comprehensive minimal rules from legislation")
            minimal_rules = await self._create_comprehensive_minimal_rules(
                legislation_text, article_reference, source_files, document_level, 
                chunk_reference, applicable_countries, adequacy_countries
            )
            rules.extend(minimal_rules)
            
        return rules

    async def _infer_primary_role_advanced(self, legislation_text: str) -> str:
        """CORRECTED: Infer primary impacted role using advanced prompting strategies."""
        try:
            prompt = PromptingStrategies.role_inference_prompt(legislation_text)
            
            messages = [
                SystemMessage(content="You are a legal text analyst specializing in data protection roles. Analyze the text to determine the primary impacted role."),
                HumanMessage(content=prompt)
            ]

            response = await self.openai_service.chat_completion(messages)
            
            # Clean and validate response
            role = response.strip().lower()
            valid_roles = ["controller", "processor", "joint_controller", "data_subject"]
            
            if role in valid_roles:
                return role
            else:
                # Fallback to keyword analysis
                return self._infer_primary_role_fallback(legislation_text)
                
        except Exception as e:
            logger.warning(f"Error in advanced role inference: {e}")
            return self._infer_primary_role_fallback(legislation_text)

    def _infer_primary_role_fallback(self, legislation_text: str) -> str:
        """Fallback role inference using keyword matching."""
        text_lower = legislation_text.lower()
        
        # Simple keyword-based inference
        if "controller" in text_lower and text_lower.count("controller") > text_lower.count("processor"):
            return "controller"
        elif "processor" in text_lower and text_lower.count("processor") > text_lower.count("controller"):
            return "processor"
        elif "data subject" in text_lower or "individual" in text_lower:
            return "data_subject"
        elif "joint" in text_lower and "controller" in text_lower:
            return "joint_controller"
        else:
            return "controller"  # Default

    async def _infer_data_categories_advanced(self, legislation_text: str) -> List[str]:
        """CORRECTED: Infer data categories using advanced prompting strategies."""
        try:
            prompt = PromptingStrategies.data_category_inference_prompt(legislation_text)
            
            messages = [
                SystemMessage(content="You are a legal text analyst specializing in data categories. Analyze the text to identify relevant data categories."),
                HumanMessage(content=prompt)
            ]

            response = await self.openai_service.chat_completion(messages)
            
            # Parse JSON response
            parsed_response = self.json_parser.parse_json_response(response)
            
            if "error" not in parsed_response and isinstance(parsed_response, list):
                # Validate categories
                valid_categories = [
                    "personal_data", "sensitive_data", "biometric_data", "health_data",
                    "financial_data", "location_data", "behavioral_data", "identification_data"
                ]
                
                result_categories = []
                for category in parsed_response:
                    if category in valid_categories:
                        result_categories.append(category)
                
                if result_categories:
                    return result_categories
                    
            # Fallback to keyword analysis
            return self._infer_data_categories_fallback(legislation_text)
                
        except Exception as e:
            logger.warning(f"Error in advanced data category inference: {e}")
            return self._infer_data_categories_fallback(legislation_text)

    def _infer_data_categories_fallback(self, legislation_text: str) -> List[str]:
        """Fallback data category inference using keyword matching."""
        text_lower = legislation_text.lower()
        categories = []
        
        # Map keywords to categories
        category_keywords = {
            "sensitive_data": ["sensitive", "special category", "special categories"],
            "health_data": ["health", "medical", "healthcare"],
            "biometric_data": ["biometric", "fingerprint", "facial recognition"],
            "financial_data": ["financial", "payment", "bank", "credit"],
            "location_data": ["location", "GPS", "tracking", "geolocation"],
            "behavioral_data": ["behavioral", "profiling", "behavioral analysis"],
            "identification_data": ["identification", "identity", "ID", "passport"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.append(category)
        
        # Always include personal_data if no specific categories found
        if not categories:
            categories.append("personal_data")
        elif "personal_data" not in categories and "personal data" in text_lower:
            categories.insert(0, "personal_data")
            
        return categories

    def _validate_and_fix_rule_data(self, rule_data: dict, article_reference: str, source_files: dict, applicable_countries: List[str], adequacy_countries: List[str], document_level: str, chunk_reference: Optional[str]) -> dict:
        """Validate and fix rule data structure."""
        
        # Ensure required fields
        rule_data.setdefault("source_article", article_reference)
        rule_data.setdefault("source_file", source_files.get("level_1", "unknown"))
        rule_data.setdefault("applicable_countries", applicable_countries)
        rule_data.setdefault("adequacy_countries", adequacy_countries)
        rule_data.setdefault("source_documents", source_files)

        # Handle numeric fields
        if isinstance(rule_data.get("priority"), str):
            try:
                rule_data["priority"] = int(rule_data["priority"])
            except ValueError:
                rule_data["priority"] = 1
        else:
            rule_data.setdefault("priority", 1)

        if isinstance(rule_data.get("confidence_score"), str):
            try:
                rule_data["confidence_score"] = float(rule_data["confidence_score"])
            except ValueError:
                rule_data["confidence_score"] = 0.8
        else:
            rule_data.setdefault("confidence_score", 0.8)

        # Ensure event field exists
        if "event" not in rule_data:
            rule_data["event"] = {"type": "compliance_required", "params": {}}

        # Fix conditions structure
        if "conditions" not in rule_data:
            rule_data["conditions"] = {
                "all": [{
                    "fact": f"legislative_requirement_{rule_data.get('name', 'default').lower().replace(' ', '_')}",
                    "operator": "equal",
                    "value": True,
                    "description": f"When {rule_data.get('description', 'legislative requirement')} applies",
                    "data_domain": ["data_usage"],
                    "role": rule_data.get("primary_impacted_role", "controller"),
                    "reasoning": f"Condition extracted from {article_reference}",
                    "document_level": document_level,
                    "chunk_reference": chunk_reference or "none"
                }]
            }

        # Ensure actions, user_actions, and decisions are lists
        rule_data.setdefault("actions", [])
        rule_data.setdefault("user_actions", [])
        rule_data.setdefault("decisions", [])

        return rule_data

    async def _create_comprehensive_minimal_rules(
        self, legislation_text: str, article_reference: str, source_files: Dict[str, Optional[str]],
        document_level: str, chunk_reference: Optional[str], applicable_countries: List[str], 
        adequacy_countries: List[str]
    ) -> List[LegislationRule]:
        """Create multiple minimal rules to ensure comprehensive coverage when parsing fails."""
        minimal_rules = []
        
        roles_to_process = ["controller", "processor", "data_subject"]
        # CORRECTED: Use advanced inference for data categories
        data_categories_inferred = await self._infer_data_categories_advanced(legislation_text)
        
        for i, role in enumerate(roles_to_process):
            try:
                rule_data = {
                    "id": f"minimal_rule_{role}_{datetime.utcnow().timestamp()}_{i}",
                    "name": f"Legislative Requirement for {role.title()}",
                    "description": f"Requirement extracted from {article_reference} for {role}",
                    "source_article": article_reference,
                    "source_file": source_files.get("level_1", "unknown"),
                    "primary_impacted_role": role,
                    "data_category": data_categories_inferred,
                    "conditions": {
                        "all": [{
                            "fact": f"{role}_legislative_requirement",
                            "operator": "equal",
                            "value": True,
                            "description": f"Legislative requirements for {role} apply",
                            "data_domain": ["data_usage"],
                            "role": role,
                            "reasoning": f"Minimal condition for {role} based on {article_reference}",
                            "document_level": document_level,
                            "chunk_reference": chunk_reference or "none"
                        }]
                    },
                    "event": {"type": "compliance_required", "params": {}},
                    "priority": 1,
                    "actions": [],
                    "user_actions": [],
                    "decisions": [],
                    "confidence_score": 0.5,
                    "applicable_countries": applicable_countries,
                    "adequacy_countries": adequacy_countries,
                    "source_documents": source_files,
                    "processing_metadata": {
                        "extraction_method": "comprehensive_minimal_fallback",
                        "chunk_reference": chunk_reference or "none",
                        "role_specific": role
                    }
                }

                rule = LegislationRule.model_validate(rule_data)
                minimal_rules.append(rule)
                logger.info(f"Created minimal rule for {role}")

            except Exception as e:
                logger.error(f"Failed to create minimal rule for {role}: {e}")
        
        return minimal_rules
    async def process_legislation_folder_to_odrl(self, folder_path: str = None) -> Dict[str, Any]:
        """
        Process all configured legislation entries and convert to ODRL format.
        Aligned EXACTLY with CSV to ODRL output structure.
        NO TRUNCATION - all text preserved in full.
        
        Returns:
            Dict with 'policies', 'processing_time', 'documents_processed', 
            'successful', 'failed', 'total_entries'
        """
        from .analyzers.guidance_analyzer import GuidanceAnalyzer
        from .generators.odrl_rule_generator import ODRLRuleGenerator
        from .managers.data_category_manager import DataCategoryManager
        
        if folder_path is None:
            folder_path = Config.LEGISLATION_PDF_PATH

        import os
        os.makedirs(folder_path, exist_ok=True)

        processing_entries = self.metadata_manager.get_all_processing_entries()

        if not processing_entries:
            logger.warning("No processing entries found in metadata configuration")
            return {
                'policies': [],
                'processing_time': 0.0,
                'documents_processed': {},
                'successful': 0,
                'failed': 0,
                'total_entries': 0
            }

        guidance_analyzer = GuidanceAnalyzer()
        odrl_generator = ODRLRuleGenerator()
        data_category_manager = DataCategoryManager()
        
        all_policies = []
        documents_processed = {}
        start_time = datetime.utcnow()
        
        statistics = {
            'total_entries': 0,
            'successful': 0,
            'failed': 0
        }

        for entry_id, metadata in processing_entries:
            try:
                logger.info(f"Processing entry for ODRL conversion: {entry_id}")

                # Process PDFs from all levels
                entry_documents = self.multi_level_processor.process_country_documents(
                    entry_id, metadata, folder_path
                )

                if not entry_documents:
                    logger.warning(f"No documents found for entry {entry_id}")
                    continue

                documents_processed[entry_id] = list(entry_documents.keys())

                # Extract text from all levels
                full_text = ""
                source_files = {
                    "level_1": metadata.file_level_1,
                    "level_2": metadata.file_level_2,
                    "level_3": metadata.file_level_3
                }
                
                for level, content in entry_documents.items():
                    if isinstance(content, list):  # Chunked document
                        level_text = "\n\n".join([chunk.content for chunk in content])
                    else:
                        level_text = content
                    full_text += f"\n\n--- {level.upper()} ---\n\n{level_text}"

                # Split text into rule segments
                rule_segments = self._segment_text_into_rules(full_text, entry_id)
                
                print(f"\n📄 Processing {entry_id}: {len(rule_segments)} rule segments found")
                print("-"*80)
                
                statistics['total_entries'] += len(rule_segments)

                for idx, segment in enumerate(rule_segments, 1):
                    try:
                        rule_name = segment.get('title', f"{entry_id}_rule_{idx}")
                        rule_text = segment.get('text', '')
                        
                        if len(rule_text.strip()) < 100:  # Skip very short segments
                            continue
                        
                        print(f"\n[{idx}/{len(rule_segments)}] Analyzing: {rule_name}")
                        print(f"    Text length: {len(rule_text)} chars")
                        
                        # Analyze using guidance analyzer (SAME AS CSV TO ODRL)
                        print("    🔍 Analyzing guidance...")
                        odrl_components = await guidance_analyzer.analyze_guidance(
                            guidance_text=rule_text,
                            rule_name=rule_name,
                            framework_type="PDF",
                            restriction_condition="mixed",
                            rule_id=f"{entry_id}_{idx}"
                        )
                        
                        print(f"    ✅ Extracted {len(odrl_components.actions)} actions, "
                            f"{len(odrl_components.permissions)} permissions, "
                            f"{len(odrl_components.prohibitions)} prohibitions")
                        
                        # Discover and add data categories
                        category_uuids = {}
                        if odrl_components.data_categories:
                            print(f"    📊 Processing {len(odrl_components.data_categories)} data categories...")
                            category_uuids = await data_category_manager.discover_and_add_categories(
                                odrl_components.data_categories
                            )
                        
                        # Generate ODRL policy (EXACT SAME AS CSV TO ODRL)
                        print("    🗂️ Generating ODRL policy...")
                        policy = odrl_generator.generate_policy(
                            policy_id=f"{entry_id}_{idx}",
                            rule_name=rule_name,
                            odrl_components=odrl_components,
                            framework_type="PDF",
                            restriction_condition="mixed",
                            data_category_uuids=category_uuids
                        )
                        
                        # Add metadata - NO TRUNCATION
                        policy['custom:originalData'] = {
                            'id': f"{entry_id}_{idx}",
                            'rule_name': rule_name,
                            'framework': "PDF",
                            'type': "mixed",
                            'entry_id': entry_id,
                            'rule_index': idx,
                            'source_files': source_files,
                            'countries': metadata.country,
                            'adequacy_countries': metadata.adequacy_country or [],
                            'guidance_text': rule_text  # FULL TEXT, NOT TRUNCATED
                        }
                        
                        # Validate policy
                        validation = odrl_generator.validate_policy(policy)
                        if not validation['valid']:
                            print(f"    ⚠️ Validation issues: {validation['issues']}")
                            statistics['failed'] += 1
                        else:
                            statistics['successful'] += 1
                        
                        if validation['warnings']:
                            print(f"    ⚠️ Warnings: {validation['warnings']}")
                        
                        all_policies.append(policy)
                        print(f"    ✅ Policy created successfully")
                        
                    except Exception as e:
                        logger.error(f"Error processing segment {idx} in {entry_id}: {e}")
                        print(f"    ❌ Error: {e}")
                        statistics['failed'] += 1
                        continue

            except Exception as e:
                logger.error(f"Error processing entry {entry_id}: {e}")
                continue

        end_time = datetime.utcnow()
        total_processing_time = (end_time - start_time).total_seconds()

        # Save data categories
        print(f"\n💾 Saving data categories...")
        data_category_manager.save_categories()
        
        cat_stats = data_category_manager.get_statistics()
        print(f"    Total categories: {cat_stats['total_categories']}")
        print(f"    Saved to: {cat_stats['categories_file']}")
        
        print(f"\n🎉 Conversion complete!")
        
        return {
            'policies': all_policies,
            'processing_time': total_processing_time,
            'documents_processed': documents_processed,
            'successful': statistics['successful'],
            'failed': statistics['failed'],
            'total_entries': statistics['total_entries']
        }


    # METHOD 2: Add this complete method to LegislationAnalyzer class

    def _segment_text_into_rules(self, text: str, entry_id: str) -> List[Dict[str, str]]:
        """
        Segment text into potential rules.
        Enhanced to detect various section markers.
        NO TRUNCATION - preserves full text.
        
        Args:
            text: Full text to segment
            entry_id: Entry identifier
            
        Returns:
            List of dictionaries with 'title' and 'text' keys
        """
        segments = []
        
        # Try to find article/section markers with multiple patterns
        patterns = [
            r'(?:Article|Art\.|ARTICLE)\s+(\d+[A-Za-z]?)[:.]\s*([^\n]+)',
            r'(?:Section|Sec\.|SECTION)\s+(\d+[A-Za-z]?)[:.]\s*([^\n]+)',
            r'(?:Clause|CLAUSE)\s+(\d+[A-Za-z]?)[:.]\s*([^\n]+)',
            r'(?:Rule|RULE)\s+(\d+[A-Za-z]?)[:.]\s*([^\n]+)',
            r'(?:Chapter|CHAPTER)\s+(\d+[A-Za-z]?)[:.]\s*([^\n]+)',
            r'(?:Paragraph|Para\.|PARAGRAPH)\s+(\d+[A-Za-z]?)[:.]\s*([^\n]+)',
            r'(\d+[A-Za-z]?)\.\s+([A-Z][^\n]+)',  # Numbered sections like "1. Title"
        ]
        
        matches = []
        for pattern in patterns:
            found = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
            if found:
                matches = found
                break
        
        if matches:
            # Split by detected markers
            for i, match in enumerate(matches):
                start_pos = match.start()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                
                segment_text = text[start_pos:end_pos].strip()
                
                # Extract title from match groups
                if len(match.groups()) >= 2:
                    number, title = match.group(1), match.group(2)
                    segment_title = f"{entry_id} - {number} {title.strip()}"
                else:
                    segment_title = f"{entry_id} - Segment {i + 1}"
                
                if len(segment_text) > 100:  # Only keep substantial segments
                    segments.append({
                        'title': segment_title,
                        'text': segment_text  # NO TRUNCATION
                    })
        else:
            # No clear article structure, split by length with overlap
            chunk_size = 3000
            overlap = 200
            
            for i in range(0, len(text), chunk_size - overlap):
                segment_text = text[i:i + chunk_size].strip()
                if len(segment_text) > 100:
                    segments.append({
                        'title': f"{entry_id} - Segment {len(segments) + 1}",
                        'text': segment_text  # NO TRUNCATION
                    })
        
        # If no segments created, use full text
        if not segments:
            segments = [{
                'title': entry_id,
                'text': text  # NO TRUNCATION
            }]
        
        return segments