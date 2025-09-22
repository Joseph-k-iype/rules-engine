"""
Main legislation analyzer with enhanced dual action inference, chunking support, whole document analysis, and decision inference.
COMPLETE VERSION with all original functionality preserved plus decision-making capabilities, no interfaces, no duplication.
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Union, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .config import Config
from .models.rules import LegislationRule, ExtractionResult
from .models.base_models import CountryMetadata, DocumentChunk, DecisionOutcome, DecisionRule
from .models.enums import DataRole, DataCategory, DecisionType, DecisionContext, RequiredActionType
from .services.openai_service import OpenAIService
from .services.metadata_manager import MetadataManager
from .services.rule_manager import RuleManager
from .processors.pdf_processor import MultiLevelPDFProcessor
from .converters.standards_converter import StandardsConverter
from .prompting.strategies import PromptingStrategies
from .utils.json_parser import SafeJsonParser
from .tools.langchain_tools import (
    extract_rule_conditions_with_decisions, analyze_data_domains_with_decision_context, 
    identify_roles_responsibilities_with_decision_authority, infer_data_processing_actions_with_decisions,
    infer_compliance_verification_actions_with_decisions, infer_data_subject_rights_actions_with_decisions,
    infer_user_actionable_tasks_with_decisions, infer_user_compliance_tasks_with_decisions,
    infer_user_rights_support_tasks_with_decisions, infer_decision_enabling_actions
)

logger = logging.getLogger(__name__)


class DecisionInferenceEngine:
    """Engine for inferring decisions from legislative context - internal use only."""
    
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        self.json_parser = SafeJsonParser()
    
    async def infer_decisions_from_text(self, legislation_text: str, context: str = "") -> List[DecisionOutcome]:
        """Infer decision outcomes from legislative text."""
        try:
            prompt = PromptingStrategies.decision_inference_prompt(legislation_text, context)
            
            messages = [
                SystemMessage(content="You are a legal decision analysis expert. Analyze legislative text to identify decision scenarios and outcomes using logical, testable statements."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.openai_service.chat_completion(messages)
            parsed_response = self.json_parser.parse_json_response(response)
            
            decisions = []
            if isinstance(parsed_response, list):
                for decision_data in parsed_response:
                    try:
                        decision = DecisionOutcome.model_validate(decision_data)
                        decisions.append(decision)
                    except Exception as e:
                        logger.warning(f"Error parsing decision outcome: {e}")
                        continue
            elif isinstance(parsed_response, dict) and "decisions" in parsed_response:
                for decision_data in parsed_response["decisions"]:
                    try:
                        decision = DecisionOutcome.model_validate(decision_data)
                        decisions.append(decision)
                    except Exception as e:
                        logger.warning(f"Error parsing decision outcome: {e}")
                        continue
            
            return decisions
            
        except Exception as e:
            logger.error(f"Error in decision inference: {e}")
            return []
    
    async def create_decision_rules_from_conditions(self, legislation_rule: LegislationRule) -> List[DecisionRule]:
        """Create decision rules based on rule conditions and context."""
        decision_rules = []
        
        try:
            # Analyze the rule to extract decision scenarios
            rule_text = f"{legislation_rule.description} {legislation_rule.source_article}"
            
            # Identify potential decision contexts from conditions
            decision_contexts = set()
            for logic_type, conditions in legislation_rule.conditions.items():
                for condition in conditions:
                    for domain in condition.data_domain:
                        domain_value = domain.value if hasattr(domain, 'value') else str(domain)
                        if domain_value == "data_transfer":
                            decision_contexts.add(DecisionContext.DATA_TRANSFER)
                        elif domain_value == "data_usage":
                            decision_contexts.add(DecisionContext.DATA_PROCESSING)
                        elif domain_value == "data_storage":
                            decision_contexts.add(DecisionContext.DATA_STORAGE)
                        elif domain_value == "data_collection":
                            decision_contexts.add(DecisionContext.DATA_COLLECTION)
                        elif domain_value == "data_deletion":
                            decision_contexts.add(DecisionContext.DATA_DELETION)
            
            # Create decision rules for each context
            for context in decision_contexts:
                decision_rule = await self._create_decision_rule_for_context(
                    legislation_rule, context, rule_text
                )
                if decision_rule:
                    decision_rules.append(decision_rule)
            
            # If no specific contexts found, create a general processing decision rule
            if not decision_contexts:
                general_rule = await self._create_decision_rule_for_context(
                    legislation_rule, DecisionContext.DATA_PROCESSING, rule_text
                )
                if general_rule:
                    decision_rules.append(general_rule)
                    
        except Exception as e:
            logger.error(f"Error creating decision rules: {e}")
        
        return decision_rules
    
    async def _create_decision_rule_for_context(
        self, legislation_rule: LegislationRule, context: DecisionContext, rule_text: str
    ) -> Optional[DecisionRule]:
        """Create a decision rule for a specific context."""
        try:
            context_questions = {
                DecisionContext.DATA_TRANSFER: "Can this data be transferred?",
                DecisionContext.DATA_PROCESSING: "Can this data be processed?",
                DecisionContext.DATA_STORAGE: "Can this data be stored?",
                DecisionContext.DATA_COLLECTION: "Can this data be collected?",
                DecisionContext.DATA_SHARING: "Can this data be shared?",
                DecisionContext.DATA_DELETION: "Must this data be deleted?",
                DecisionContext.CONSENT_MANAGEMENT: "Is consent required?",
                DecisionContext.RIGHTS_EXERCISE: "Can this right be exercised?",
                DecisionContext.COMPLIANCE_VERIFICATION: "Is compliance verified?"
            }
            
            question = context_questions.get(context, "Is this action permitted?")
            
            # Analyze the rule text for decision logic
            decision_prompt = f"""
            Based on the following rule information, create a decision rule for the question: "{question}"
            
            Rule Text: {rule_text}
            Rule Description: {legislation_rule.description}
            Context: {context.value}
            
            Determine:
            1. Default decision if no conditions are met
            2. Conditions that would change the decision
            3. Required actions for conditional approvals
            4. Reasons for prohibitive decisions
            
            Look for:
            - YES indicators: "may", "can", "is permitted", "allowed"
            - NO indicators: "shall not", "must not", "prohibited", "forbidden"
            - MAYBE indicators: "provided that", "if", "subject to", "only if"
            
            Express all requirements as logical, testable conditions.
            Do not reference document structure or sources.
            
            Return a JSON object with:
            {{
                "default_decision": "yes/no/maybe/unknown",
                "conditional_decisions": [
                    {{"conditions": ["condition1", "condition2"], "decision": "yes/no/maybe"}}
                ],
                "requirements_for_yes": ["requirement1", "requirement2"],
                "requirements_for_maybe": ["action1", "action2"],
                "reasons_for_no": ["reason1", "reason2"],
                "applicable_scenarios": ["scenario1", "scenario2"]
            }}
            """
            
            messages = [
                SystemMessage(content="You are a legal decision rule expert. Create structured decision rules from legislative text using logical, testable conditions."),
                HumanMessage(content=decision_prompt)
            ]
            
            response = await self.openai_service.chat_completion(messages)
            parsed_response = self.json_parser.parse_json_response(response)
            
            if "error" in parsed_response:
                logger.warning(f"Error parsing decision rule response: {parsed_response}")
                return None
            
            # Convert string actions to enum values
            requirements_for_maybe = []
            if "requirements_for_maybe" in parsed_response:
                for req in parsed_response["requirements_for_maybe"]:
                    try:
                        # Map common requirement strings to enum values
                        if "mask" in req.lower():
                            requirements_for_maybe.append(RequiredActionType.DATA_MASKING)
                        elif "encrypt" in req.lower():
                            requirements_for_maybe.append(RequiredActionType.DATA_ENCRYPTION)
                        elif "consent" in req.lower():
                            requirements_for_maybe.append(RequiredActionType.CONSENT_OBTAINMENT)
                        elif "safeguard" in req.lower():
                            requirements_for_maybe.append(RequiredActionType.SAFEGUARDS_IMPLEMENTATION)
                        elif "adequacy" in req.lower():
                            requirements_for_maybe.append(RequiredActionType.ADEQUACY_VERIFICATION)
                        elif "document" in req.lower():
                            requirements_for_maybe.append(RequiredActionType.DOCUMENTATION_COMPLETION)
                        elif "assess" in req.lower():
                            requirements_for_maybe.append(RequiredActionType.IMPACT_ASSESSMENT)
                        elif "approval" in req.lower():
                            requirements_for_maybe.append(RequiredActionType.APPROVAL_OBTAINMENT)
                        elif "notification" in req.lower():
                            requirements_for_maybe.append(RequiredActionType.NOTIFICATION_COMPLETION)
                        elif "security" in req.lower():
                            requirements_for_maybe.append(RequiredActionType.SECURITY_MEASURES)
                        elif "access" in req.lower():
                            requirements_for_maybe.append(RequiredActionType.ACCESS_CONTROLS)
                        else:
                            # Default to documentation for unrecognized requirements
                            requirements_for_maybe.append(RequiredActionType.DOCUMENTATION_COMPLETION)
                    except Exception:
                        continue
            
            # Determine default decision
            default_decision = DecisionType.UNKNOWN
            if "default_decision" in parsed_response:
                try:
                    default_decision = DecisionType(parsed_response["default_decision"].lower())
                except ValueError:
                    default_decision = DecisionType.UNKNOWN
            
            decision_rule = DecisionRule(
                id=f"decision_{legislation_rule.id}_{context.value}",
                question=question,
                context=context,
                default_decision=default_decision,
                conditional_decisions=parsed_response.get("conditional_decisions", []),
                requirements_for_yes=parsed_response.get("requirements_for_yes", []),
                requirements_for_maybe=requirements_for_maybe,
                reasons_for_no=parsed_response.get("reasons_for_no", []),
                source_rule_id=legislation_rule.id,
                confidence_score=0.8,
                applicable_scenarios=parsed_response.get("applicable_scenarios", [])
            )
            
            return decision_rule
            
        except Exception as e:
            logger.error(f"Error creating decision rule for context {context}: {e}")
            return None


class LegislationAnalyzer:
    """Main analyzer with enhanced dual action inference, chunking support, whole document analysis, and decision inference."""

    def __init__(self):
        self.openai_service = OpenAIService()
        self.json_parser = SafeJsonParser()
        self.rule_manager = RuleManager()
        self.metadata_manager = MetadataManager()
        self.multi_level_processor = MultiLevelPDFProcessor()
        self.standards_converter = StandardsConverter()
        self.decision_engine = DecisionInferenceEngine(self.openai_service)

        # Initialize LangChain model
        self.llm = ChatOpenAI(
            model=Config.CHAT_MODEL,
            openai_api_key=Config.API_KEY,
            openai_api_base=Config.BASE_URL
        )

        # Create react agent with all tools including decision-enabled tools
        self.tools = [
            extract_rule_conditions_with_decisions,
            analyze_data_domains_with_decision_context, 
            identify_roles_responsibilities_with_decision_authority,
            infer_data_processing_actions_with_decisions,
            infer_compliance_verification_actions_with_decisions,
            infer_data_subject_rights_actions_with_decisions,
            infer_user_actionable_tasks_with_decisions,
            infer_user_compliance_tasks_with_decisions,
            infer_user_rights_support_tasks_with_decisions,
            infer_decision_enabling_actions
        ]

        self.memory = MemorySaver()
        self.agent = create_react_agent(self.llm, self.tools, checkpointer=self.memory)

    async def process_legislation_folder(self, folder_path: str = None) -> ExtractionResult:
        """Process all configured legislation entries with decision inference - no duplication."""
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
                total_decision_rules=0,
                total_decisions=0,
                processing_time=0.0
            )

        all_new_rules = []
        documents_processed = {}
        chunking_metadata = {}
        decision_contexts = set()
        start_time = datetime.utcnow()
        
        # Track processed content to avoid duplication
        processed_content_hashes = set()

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

                result = await self.analyze_legislation_with_levels_and_decisions(
                    entry_documents=entry_documents,
                    entry_id=entry_id,
                    metadata=metadata,
                    processed_content_hashes=processed_content_hashes
                )

                all_new_rules.extend(result.rules)
                decision_contexts.update(result.decision_contexts)

            except Exception as e:
                logger.error(f"Error processing entry {entry_id}: {e}")
                continue

        end_time = datetime.utcnow()
        total_processing_time = (end_time - start_time).total_seconds()
        total_actions = sum(len(rule.actions) for rule in all_new_rules)
        total_user_actions = sum(len(rule.user_actions) for rule in all_new_rules)
        total_decision_rules = sum(len(rule.decision_rules) for rule in all_new_rules)
        total_decisions = sum(1 for rule in all_new_rules if rule.decision_outcome or rule.decision_rules)

        if all_new_rules:
            rule_texts = [f"{rule.description} {rule.source_article}" for rule in all_new_rules]
            embeddings = await self.openai_service.get_embeddings(rule_texts)
        else:
            embeddings = []

        # Save rules without duplication
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
            summary=f"Processed {len(processing_entries)} entries, extracted {len(all_new_rules)} rules with {total_actions} rule actions, {total_user_actions} user actions, {total_decision_rules} decision rules, and {total_decisions} decision-enabled rules",
            total_rules=len(all_new_rules),
            total_actions=total_actions,
            total_user_actions=total_user_actions,
            total_decision_rules=total_decision_rules,
            total_decisions=total_decisions,
            decision_contexts=list(decision_contexts),
            processing_time=total_processing_time,
            embeddings=embeddings,
            integrated_rules=integrated_rules,
            documents_processed=documents_processed,
            chunking_metadata=chunking_metadata
        )

        return result

    async def analyze_legislation_with_levels_and_decisions(
        self, 
        entry_documents: Dict[str, Union[str, List[DocumentChunk]]],
        entry_id: str,
        metadata: CountryMetadata,
        processed_content_hashes: set
    ) -> ExtractionResult:
        """Analyze legislation from multiple document levels with chunking support, whole document analysis, and decision inference - no duplication."""
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
            decision_contexts = set()

            # Enhanced: First pass - comprehensive document understanding with decision inference
            for level, content in entry_documents.items():
                logger.info(f"Performing comprehensive analysis with decision inference of {level} document...")

                if isinstance(content, list):  # Chunked document
                    # For chunked documents, first get overall understanding
                    full_text = "\n\n".join([chunk.content for chunk in content])
                    
                    # Check for content duplication
                    content_hash = hash(full_text)
                    if content_hash in processed_content_hashes:
                        logger.info(f"Skipping duplicate content in {level}")
                        continue
                    processed_content_hashes.add(content_hash)
                    
                    comprehensive_analysis = await self._apply_comprehensive_document_analysis_with_decisions(
                        full_text, existing_context + metadata_context, level, f"Full document with {len(content)} chunks"
                    )

                    # Then process each chunk with context of the whole document
                    for chunk in content:
                        chunk_info = f"Chunk {chunk.chunk_index + 1} of {chunk.total_chunks} (positions {chunk.start_pos}-{chunk.end_pos})"

                        chunk_rules = await self._process_text_chunk_with_context_and_decisions(
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
                        
                        # Collect decision contexts
                        for rule in chunk_rules:
                            if rule.decision_outcome:
                                decision_contexts.add(rule.decision_outcome.context.value)
                            for decision_rule in rule.decision_rules:
                                decision_contexts.add(decision_rule.context.value)
                        
                        logger.info(f"Processed {len(chunk_rules)} rules from chunk {chunk.chunk_index + 1}")

                else:  # Single document
                    # Check for content duplication
                    content_hash = hash(content)
                    if content_hash in processed_content_hashes:
                        logger.info(f"Skipping duplicate content in {level}")
                        continue
                    processed_content_hashes.add(content_hash)
                    
                    comprehensive_analysis = await self._apply_comprehensive_document_analysis_with_decisions(
                        content, existing_context + metadata_context, level, ""
                    )

                    level_rules = await self._process_text_chunk_with_context_and_decisions(
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
                    
                    # Collect decision contexts
                    for rule in level_rules:
                        if rule.decision_outcome:
                            decision_contexts.add(rule.decision_outcome.context.value)
                        for decision_rule in rule.decision_rules:
                            decision_contexts.add(decision_rule.context.value)
                    
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
            total_decision_rules = sum(len(rule.decision_rules) for rule in all_rules)
            total_decisions = sum(1 for rule in all_rules if rule.decision_outcome or rule.decision_rules)

            result = ExtractionResult(
                rules=all_rules,
                summary=f"Extracted {len(all_rules)} rules with {total_actions} rule actions, {total_user_actions} user actions, {total_decision_rules} decision rules, and {total_decisions} decision-enabled rules from {entry_id}",
                total_rules=len(all_rules),
                total_actions=total_actions,
                total_user_actions=total_user_actions,
                total_decision_rules=total_decision_rules,
                total_decisions=total_decisions,
                decision_contexts=list(decision_contexts),
                processing_time=processing_time,
                embeddings=embeddings,
                integrated_rules=integrated_rules,
                documents_processed={entry_id: list(entry_documents.keys())}
            )

            logger.info(f"Analysis completed: {len(all_rules)} rules with {total_actions} rule actions, {total_user_actions} user actions, {total_decision_rules} decision rules, and {total_decisions} decision-enabled rules extracted in {processing_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Error analyzing legislation with levels and decisions: {e}")
            raise

    async def _apply_comprehensive_document_analysis_with_decisions(self, legislation_text: str, existing_context: str = "", level: str = "level_1", chunk_info: str = "") -> str:
        """Apply comprehensive document analysis to understand the entire document with decision inference."""
        prompt = PromptingStrategies.comprehensive_document_analysis_prompt(legislation_text, existing_context, level, chunk_info)

        messages = [
            SystemMessage(content="You are a legal text analyst with decision inference capabilities. Analyze the ENTIRE document comprehensively including decision-making scenarios. Use logical, testable statements without referencing document structure."),
            HumanMessage(content=prompt)
        ]

        return await self.openai_service.chat_completion(messages)

    async def _process_text_chunk_with_context_and_decisions(
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

        # Step 1: Focused analysis with comprehensive context and decision inference
        focused_analysis = await self._apply_focused_analysis_with_context_and_decisions(
            text, existing_context + metadata_context, level, chunk_info, comprehensive_analysis
        )

        # Step 2: Expert verification including decision logic
        verified_analysis = await self._apply_expert_verification_with_decisions(
            text, focused_analysis, level
        )

        # Step 3: Use react agent for TRIPLE action inference (rule + user + decision-enabling actions) with document context
        agent_analysis = await self._run_triple_action_inference_agent_with_context(
            text, f"{entry_id} - {level}", metadata.country, chunk_reference, comprehensive_analysis
        )

        # Step 4: Synthesize into rules with TRIPLE actions and decision inference
        rules = await self._synthesize_rules_with_triple_actions_and_decisions(
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
            comprehensive_analysis=comprehensive_analysis
        )

        # Step 5: Add decision inference to each rule
        enhanced_rules = []
        for rule in rules:
            try:
                # Infer decisions from the rule context
                decisions = await self.decision_engine.infer_decisions_from_text(
                    text, f"Rule: {rule.description}"
                )
                
                # Add primary decision if found
                if decisions:
                    rule.decision_outcome = decisions[0]  # Use the first/primary decision
                
                # Create decision rules based on conditions
                decision_rules = await self.decision_engine.create_decision_rules_from_conditions(rule)
                rule.decision_rules = decision_rules
                
                # Update enables_decisions list
                if rule.decision_outcome:
                    context = rule.decision_outcome.context.value
                    decision = rule.decision_outcome.decision.value
                    rule.enables_decisions.append(f"{decision} for {context}")
                
                for decision_rule in decision_rules:
                    context = decision_rule.context.value
                    rule.enables_decisions.append(f"decision framework for {context}")
                
                enhanced_rules.append(rule)
                
            except Exception as e:
                logger.warning(f"Error adding decision inference to rule {rule.id}: {e}")
                # Add rule without decision enhancement
                enhanced_rules.append(rule)

        return enhanced_rules

    async def _apply_focused_analysis_with_context_and_decisions(self, legislation_text: str, existing_context: str = "", level: str = "level_1", chunk_info: str = "", comprehensive_analysis: str = "") -> str:
        """Apply focused analysis with comprehensive document context and decision inference."""
        context_section = f"\n\nCOMPREHENSIVE DOCUMENT ANALYSIS:\n{comprehensive_analysis}\n" if comprehensive_analysis else ""
        prompt = PromptingStrategies.focused_analysis_with_decision_inference_prompt(legislation_text, existing_context + context_section, level, chunk_info)

        messages = [
            SystemMessage(content="You are a legal text analyst with decision inference capabilities. Analyze only what is present in the legislation text using the comprehensive document context. Include decision-making analysis using logical, testable statements."),
            HumanMessage(content=prompt)
        ]

        return await self.openai_service.chat_completion(messages)

    async def _apply_expert_verification_with_decisions(self, legislation_text: str, preliminary_analysis: str, level: str = "level_1") -> str:
        """Apply expert verification to validate findings including decision logic."""
        prompt = PromptingStrategies.expert_verification_with_decisions_prompt(legislation_text, preliminary_analysis, level)

        messages = [
            SystemMessage(content="You are a legal compliance expert with decision analysis expertise. Verify analysis accuracy against source text including decision logic using logical, testable statements."),
            HumanMessage(content=prompt)
        ]

        return await self.openai_service.chat_completion(messages)

    async def _run_triple_action_inference_agent_with_context(self, legislation_text: str, article_reference: str, countries: List[str], chunk_reference: Optional[str] = None, comprehensive_analysis: str = "") -> str:
        """Run react agent for TRIPLE action inference (rule + user + decision-enabling) with comprehensive document context."""
        try:
            config = {"configurable": {"thread_id": f"analysis_{datetime.utcnow().timestamp()}"}}

            chunk_info = f" (Chunk: {chunk_reference})" if chunk_reference else ""
            context_section = f"\n\nCOMPREHENSIVE DOCUMENT CONTEXT:\n{comprehensive_analysis}\n" if comprehensive_analysis else ""

            message = f"""
            Analyze the following legislation text and infer THREE TYPES of actions: organizational rule actions, practical user actions, AND decision-enabling actions.
            {context_section}

            Article: {article_reference}{chunk_info}
            Countries: {', '.join(countries)}
            Text: {legislation_text}

            Use the available tools to:
            1. Identify specific rule conditions related to data processing with decision impact
            2. Analyze data domains and categories involved with decision contexts
            3. Identify roles and responsibilities for data handling with decision authority

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

            DECISION-ENABLING ACTION INFERENCE (Decision Actions):
            12. Infer actions that enable or change decision outcomes
            13. Focus on actions required for conditional permissions
            14. Identify actions that convert "maybe" decisions to "yes" decisions
            15. Map actions to decision contexts (transfer, processing, storage, etc.)

            FOCUS CONSTRAINTS:
            - RULE ACTIONS: Organizational, policy-level, systematic data actions
            - USER ACTIONS: Individual, practical, implementable data tasks
            - DECISION ACTIONS: Actions that enable, condition, or change decision outcomes
            - Base ALL actions on explicit legislative requirements
            - Focus on concrete data operations: encryption, masking, access control, deletion, backup
            - Express actions as logical, testable requirements
            - Do not reference document structure or sources in action descriptions
            - Use the comprehensive document context to understand relationships
            - Identify decision scenarios and conditional requirements

            Provide analysis that enables creation of machine-readable rules with organizational rule actions, practical user actions, AND decision-enabling actions.
            Express all findings as logical, actionable statements without document references.
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
            logger.error(f"Error running triple action inference agent: {e}")
            return f"Error in agent analysis: {str(e)}"

    async def _synthesize_rules_with_triple_actions_and_decisions(
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
        comprehensive_analysis: str
    ) -> List[LegislationRule]:
        """Synthesize all analyses into comprehensive structured rules with maximum rule extraction and decision inference."""

        applicable_countries_json = json.dumps(applicable_countries)
        adequacy_countries_json = json.dumps(adequacy_countries)
        source_files_json = json.dumps(source_files)

        synthesis_prompt = PromptingStrategies.synthesis_with_decisions_prompt_template(
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
            comprehensive_analysis=comprehensive_analysis
        )

        messages = [
            SystemMessage(content="You are a comprehensive legal-tech expert with decision analysis capabilities. Extract EVERY possible rule from the legislation including decision-making scenarios. Create multiple specific rules rather than trying to combine everything. Use logical, testable statements without document references. Focus on practical data operations and decision outcomes."),
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
                    rule_data.setdefault("name", "Legislative Rule with Decision Capability")
                    rule_data.setdefault("description", "Rule extracted from legislation with decision inference")

                    # Use advanced inference for role and data category
                    if not rule_data.get("primary_impacted_role"):
                        rule_data["primary_impacted_role"] = await self._infer_primary_role_advanced(legislation_text)

                    if not rule_data.get("data_category") or len(rule_data.get("data_category", [])) == 0:
                        rule_data["data_category"] = await self._infer_data_categories_advanced(legislation_text)

                    # Process remaining fields with validation
                    rule_data = self._validate_and_fix_rule_data_with_decisions(
                        rule_data, article_reference, source_files, applicable_countries, 
                        adequacy_countries, document_level, chunk_reference
                    )

                    # Validate and create the rule using Pydantic
                    rule = LegislationRule.model_validate(rule_data)
                    rules.append(rule)
                    
                    decision_info = ""
                    if rule.decision_outcome or rule.decision_rules:
                        decision_info = f" with decision capabilities"
                    
                    logger.info(f"Successfully created comprehensive rule: {rule.name} with {len(rule.actions)} actions, {len(rule.user_actions)} user actions{decision_info}")

                except Exception as e:
                    logger.warning(f"Skipping invalid rule due to error: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error processing comprehensive rule data: {e}")

        # If no rules were created, create minimal rules to ensure coverage
        if not rules:
            logger.warning("No rules could be parsed, creating comprehensive minimal rules from legislation")
            minimal_rules = await self._create_comprehensive_minimal_rules_with_decisions(
                legislation_text, article_reference, source_files, document_level, 
                chunk_reference, applicable_countries, adequacy_countries
            )
            rules.extend(minimal_rules)
            
        return rules

    async def _infer_primary_role_advanced(self, legislation_text: str) -> str:
        """Infer primary impacted role using advanced prompting strategies."""
        try:
            prompt = PromptingStrategies.role_inference_prompt(legislation_text)
            
            messages = [
                SystemMessage(content="You are a legal text analyst specializing in data protection roles. Analyze the text to determine the primary impacted role."),
                HumanMessage(content=prompt)
            ]

            response = await self.openai_service.chat_completion(messages)
            
            role = response.strip().lower()
            valid_roles = ["controller", "processor", "joint_controller", "data_subject"]
            
            if role in valid_roles:
                return role
            else:
                return self._infer_primary_role_fallback(legislation_text)
                
        except Exception as e:
            logger.warning(f"Error in advanced role inference: {e}")
            return self._infer_primary_role_fallback(legislation_text)

    def _infer_primary_role_fallback(self, legislation_text: str) -> str:
        """Fallback role inference using keyword matching."""
        text_lower = legislation_text.lower()
        
        if "controller" in text_lower and text_lower.count("controller") > text_lower.count("processor"):
            return "controller"
        elif "processor" in text_lower and text_lower.count("processor") > text_lower.count("controller"):
            return "processor"
        elif "data subject" in text_lower or "individual" in text_lower:
            return "data_subject"
        elif "joint" in text_lower and "controller" in text_lower:
            return "joint_controller"
        else:
            return "controller"

    async def _infer_data_categories_advanced(self, legislation_text: str) -> List[str]:
        """Infer data categories using advanced prompting strategies."""
        try:
            prompt = PromptingStrategies.data_category_inference_prompt(legislation_text)
            
            messages = [
                SystemMessage(content="You are a legal text analyst specializing in data categories. Analyze the text to identify relevant data categories."),
                HumanMessage(content=prompt)
            ]

            response = await self.openai_service.chat_completion(messages)
            parsed_response = self.json_parser.parse_json_response(response)
            
            if "error" not in parsed_response and isinstance(parsed_response, list):
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
                    
            return self._infer_data_categories_fallback(legislation_text)
                
        except Exception as e:
            logger.warning(f"Error in advanced data category inference: {e}")
            return self._infer_data_categories_fallback(legislation_text)

    def _infer_data_categories_fallback(self, legislation_text: str) -> List[str]:
        """Fallback data category inference using keyword matching."""
        text_lower = legislation_text.lower()
        categories = []
        
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
        
        if not categories:
            categories.append("personal_data")
        elif "personal_data" not in categories and "personal data" in text_lower:
            categories.insert(0, "personal_data")
            
        return categories

    def _validate_and_fix_rule_data_with_decisions(
        self, rule_data: dict, article_reference: str, source_files: dict, 
        applicable_countries: List[str], adequacy_countries: List[str], 
        document_level: str, chunk_reference: Optional[str]
    ) -> dict:
        """Validate and fix rule data structure with decision capabilities."""
        
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

        # Ensure event field exists with decision context
        if "event" not in rule_data:
            rule_data["event"] = {
                "type": "compliance_required", 
                "params": {},
                "decision_context": "data_processing"
            }

        # Fix conditions structure with decision impact - ensure logical statements
        if "conditions" not in rule_data:
            rule_data["conditions"] = {
                "all": [{
                    "fact": f"legislative_requirement_applies",
                    "operator": "equal",
                    "value": True,
                    "description": f"When legislative requirement for {rule_data.get('description', 'compliance')} applies",
                    "data_domain": ["data_usage"],
                    "role": rule_data.get("primary_impacted_role", "controller"),
                    "reasoning": f"Condition extracted from legislative text requiring compliance",
                    "document_level": document_level,
                    "chunk_reference": chunk_reference or "none",
                    "decision_impact": "maybe",
                    "conditional_requirement": "documentation_completion"
                }]
            }

        # Ensure actions, user_actions, and decision-related fields are lists
        rule_data.setdefault("actions", [])
        rule_data.setdefault("user_actions", [])
        rule_data.setdefault("decision_rules", [])
        rule_data.setdefault("enables_decisions", [])

        # Set extraction method to include decision inference
        rule_data["extraction_method"] = "llm_analysis_with_decision_inference"

        return rule_data

    async def _create_comprehensive_minimal_rules_with_decisions(
        self, legislation_text: str, article_reference: str, source_files: Dict[str, Optional[str]],
        document_level: str, chunk_reference: Optional[str], applicable_countries: List[str], 
        adequacy_countries: List[str]
    ) -> List[LegislationRule]:
        """Create multiple minimal rules with decision capabilities to ensure comprehensive coverage when parsing fails."""
        minimal_rules = []
        
        roles_to_process = ["controller", "processor", "data_subject"]
        data_categories_inferred = await self._infer_data_categories_advanced(legislation_text)
        
        for i, role in enumerate(roles_to_process):
            try:
                rule_data = {
                    "id": f"minimal_decision_rule_{role}_{datetime.utcnow().timestamp()}_{i}",
                    "name": f"Legislative Requirement with Decision Framework for {role.title()}",
                    "description": f"Requirement extracted from legislation for {role} with decision inference capabilities",
                    "source_article": article_reference,
                    "source_file": source_files.get("level_1", "unknown"),
                    "primary_impacted_role": role,
                    "data_category": data_categories_inferred,
                    "conditions": {
                        "all": [{
                            "fact": f"{role}_legislative_compliance_required",
                            "operator": "equal",
                            "value": True,
                            "description": f"Legislative compliance requirements for {role} are applicable",
                            "data_domain": ["data_usage"],
                            "role": role,
                            "reasoning": f"Minimal condition for {role} based on legislative requirements",
                            "document_level": document_level,
                            "chunk_reference": chunk_reference or "none",
                            "decision_impact": "maybe",
                            "conditional_requirement": "documentation_completion"
                        }]
                    },
                    "event": {
                        "type": "compliance_required", 
                        "params": {},
                        "decision_context": "data_processing"
                    },
                    "priority": 1,
                    "actions": [],
                    "user_actions": [],
                    "decision_rules": [],
                    "enables_decisions": [f"processing decision for {role}"],
                    "confidence_score": 0.5,
                    "applicable_countries": applicable_countries,
                    "adequacy_countries": adequacy_countries,
                    "source_documents": source_files,
                    "processing_metadata": {
                        "extraction_method": "comprehensive_minimal_fallback_with_decisions",
                        "chunk_reference": chunk_reference or "none",
                        "role_specific": role
                    }
                }

                rule = LegislationRule.model_validate(rule_data)
                minimal_rules.append(rule)
                logger.info(f"Created minimal rule with decision framework for {role}")

            except Exception as e:
                logger.error(f"Failed to create minimal rule with decisions for {role}: {e}")
        
        return minimal_rules