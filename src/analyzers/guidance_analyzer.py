"""
LLM-based guidance analyzer for extracting ODRL components from guidance text.
Uses advanced prompting strategies for comprehensive analysis.
Integrates with existing PromptingStrategies framework.

Location: src/analyzers/guidance_analyzer.py
"""
import logging
from typing import Dict, List, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field, ValidationError

from ..services.openai_service import OpenAIService
from ..utils.json_parser import SafeJsonParser
from ..prompting.strategies import PromptingStrategies

logger = logging.getLogger(__name__)


class ODRLComponents(BaseModel):
    """Extracted ODRL components from guidance text."""
    
    # Core ODRL elements
    actions: List[str] = Field(default_factory=list, description="Actions that can be performed")
    permissions: List[Dict[str, Any]] = Field(default_factory=list, description="Permitted actions with details")
    prohibitions: List[Dict[str, Any]] = Field(default_factory=list, description="Prohibited actions with details")
    constraints: List[Dict[str, Any]] = Field(default_factory=list, description="Constraints and conditions")
    
    # Data context
    data_categories: List[str] = Field(default_factory=list, description="Types of data involved")
    data_subjects: List[str] = Field(default_factory=list, description="Who the data is about")
    
    # Parties and roles
    parties: Dict[str, List[str]] = Field(default_factory=dict, description="Parties involved by role")
    
    # Additional context
    purpose: Optional[str] = Field(None, description="Purpose of processing")
    legal_basis: Optional[str] = Field(None, description="Legal basis for processing")
    geographic_scope: List[str] = Field(default_factory=list, description="Geographic applicability")
    
    # Evidence and verification
    evidence_requirements: List[str] = Field(default_factory=list, description="Evidence needed")
    verification_methods: List[str] = Field(default_factory=list, description="How to verify compliance")
    
    # Metadata
    confidence_score: float = Field(0.8, description="Confidence in extraction")
    extraction_reasoning: str = Field("", description="Reasoning for extraction")


class GuidanceAnalyzer:
    """
    Analyzes guidance text using LLM to extract ODRL components.
    Uses complex prompting strategies for accurate extraction.
    """
    
    def __init__(self):
        """Initialize guidance analyzer with LLM service."""
        self.openai_service = OpenAIService()
        self.json_parser = SafeJsonParser()
    
    async def analyze_guidance(
        self, 
        guidance_text: str,
        rule_name: str,
        framework_type: str,
        restriction_condition: str,
        rule_id: str
    ) -> ODRLComponents:
        """
        Comprehensive analysis of guidance text to extract ODRL components.
        
        Args:
            guidance_text: Complete guidance text
            rule_name: Name/title of the rule
            framework_type: DSS or DataVISA
            restriction_condition: restriction or condition
            rule_id: Unique identifier
            
        Returns:
            ODRLComponents with extracted information
        """
        logger.info(f"Analyzing guidance for rule: {rule_name} ({rule_id})")
        
        # Multi-stage analysis for comprehensive extraction
        
        # Stage 1: Initial comprehensive analysis
        initial_analysis = await self._stage1_comprehensive_analysis(
            guidance_text, rule_name, framework_type, restriction_condition
        )
        
        # Stage 2: ODRL-specific extraction
        odrl_extraction = await self._stage2_odrl_extraction(
            guidance_text, rule_name, initial_analysis
        )
        
        # Stage 3: Constraint analysis
        constraint_analysis = await self._stage3_constraint_analysis(
            guidance_text, rule_name, odrl_extraction
        )
        
        # Stage 4: Data category identification
        data_categories = await self._stage4_data_category_identification(
            guidance_text, rule_name, constraint_analysis
        )
        
        # Stage 5: Synthesis and verification
        final_components = await self._stage5_synthesis(
            guidance_text, rule_name, framework_type, restriction_condition,
            initial_analysis, odrl_extraction, constraint_analysis, data_categories
        )
        
        return final_components
    
    async def _stage1_comprehensive_analysis(
        self, 
        guidance_text: str, 
        rule_name: str,
        framework_type: str,
        restriction_condition: str
    ) -> str:
        """Stage 1: Comprehensive understanding of guidance text."""
        
        prompt = PromptingStrategies.odrl_comprehensive_guidance_analysis(
            guidance_text=guidance_text,
            rule_name=rule_name,
            framework_type=framework_type,
            restriction_condition=restriction_condition
        )
        
        messages = [
            SystemMessage(content="You are a legal and data protection expert analyzing regulatory guidance. Analyze text comprehensively to extract all relevant compliance requirements."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.openai_service.chat_completion(messages)
        logger.info(f"Stage 1 analysis complete for {rule_name}")
        
        return response
    
    async def _stage2_odrl_extraction(
        self, 
        guidance_text: str, 
        rule_name: str,
        initial_analysis: str
    ) -> str:
        """Stage 2: Extract ODRL-specific components."""
        
        prompt = PromptingStrategies.odrl_component_extraction(
            guidance_text=guidance_text,
            rule_name=rule_name,
            initial_analysis=initial_analysis
        )
        
        messages = [
            SystemMessage(content="You are an ODRL specialist. Extract policy components according to ODRL ontology standards."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.openai_service.chat_completion(messages)
        logger.info(f"Stage 2 ODRL extraction complete for {rule_name}")
        
        return response
    
    async def _stage3_constraint_analysis(
        self, 
        guidance_text: str, 
        rule_name: str,
        odrl_extraction: str
    ) -> str:
        """Stage 3: Detailed constraint analysis."""
        
        prompt = PromptingStrategies.odrl_constraint_analysis(
            guidance_text=guidance_text,
            rule_name=rule_name,
            odrl_extraction=odrl_extraction
        )
        
        messages = [
            SystemMessage(content="You are an expert in ODRL constraints. Analyze and structure constraints according to ODRL specification."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.openai_service.chat_completion(messages)
        logger.info(f"Stage 3 constraint analysis complete for {rule_name}")
        
        return response
    
    async def _stage4_data_category_identification(
        self, 
        guidance_text: str, 
        rule_name: str,
        constraint_analysis: str
    ) -> str:
        """Stage 4: Identify specific data categories."""
        
        prompt = PromptingStrategies.odrl_data_category_identification(
            guidance_text=guidance_text,
            rule_name=rule_name,
            constraint_analysis=constraint_analysis
        )
        
        messages = [
            SystemMessage(content="You are a data classification expert. Identify and categorize all types of data mentioned in regulatory guidance."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.openai_service.chat_completion(messages)
        logger.info(f"Stage 4 data category identification complete for {rule_name}")
        
        return response
    
    def _sanitize_string_list(self, data: Any, field_name: str) -> List[str]:
        """
        Sanitize a field that should be a list of strings.
        Handles cases where LLM returns dicts, instructions, or malformed data.
        """
        if not data:
            return []
        
        if not isinstance(data, list):
            logger.warning(f"{field_name} is not a list, converting: {type(data)}")
            return []
        
        sanitized = []
        for item in data:
            if isinstance(item, str):
                # Skip instruction-like strings
                if len(item) > 200 or item.lower().startswith(('list all', 'include', 'complete list', 'use precise')):
                    logger.warning(f"Skipping instruction-like string in {field_name}: {item[:100]}")
                    continue
                sanitized.append(item)
            elif isinstance(item, dict):
                # Try to extract meaningful string from dict
                if 'name' in item:
                    sanitized.append(str(item['name']))
                elif 'category_name' in item:
                    sanitized.append(str(item['category_name']))
                elif 'action' in item:
                    sanitized.append(str(item['action']))
                else:
                    logger.warning(f"Dict in {field_name} has no extractable string: {item}")
            else:
                logger.warning(f"Non-string item in {field_name}: {type(item)}")
        
        return sanitized
    
    def _sanitize_dict_list(self, data: Any, field_name: str) -> List[Dict[str, Any]]:
        """
        Sanitize a field that should be a list of dictionaries.
        """
        if not data:
            return []
        
        if not isinstance(data, list):
            logger.warning(f"{field_name} is not a list: {type(data)}")
            return []
        
        sanitized = []
        for item in data:
            if isinstance(item, dict):
                sanitized.append(item)
            else:
                logger.warning(f"Non-dict item in {field_name}: {type(item)}")
        
        return sanitized
    
    async def _stage5_synthesis(
        self,
        guidance_text: str,
        rule_name: str,
        framework_type: str,
        restriction_condition: str,
        initial_analysis: str,
        odrl_extraction: str,
        constraint_analysis: str,
        data_categories: str
    ) -> ODRLComponents:
        """Stage 5: Synthesize all analyses into structured ODRL components."""
        
        prompt = PromptingStrategies.odrl_synthesis_prompt(
            guidance_text=guidance_text,
            rule_name=rule_name,
            framework_type=framework_type,
            restriction_condition=restriction_condition,
            initial_analysis=initial_analysis,
            odrl_extraction=odrl_extraction,
            constraint_analysis=constraint_analysis,
            data_categories=data_categories
        )
        
        messages = [
            SystemMessage(content="You are an expert system for creating ODRL policies. Synthesize complex analyses into precise, machine-readable ODRL structures. Return only valid JSON with actual extracted data, not template instructions."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.openai_service.chat_completion(messages)
        
        # Parse JSON response
        parsed_data = self.json_parser.parse_json_response(response)
        
        if "error" in parsed_data:
            logger.error(f"Failed to parse synthesis JSON for {rule_name}: {parsed_data}")
            # Return minimal structure
            return ODRLComponents(
                extraction_reasoning=f"Failed to parse JSON: {parsed_data.get('error', 'Unknown error')}"
            )
        
        # Sanitize the parsed data before creating ODRLComponents
        try:
            # Sanitize string lists
            if 'actions' in parsed_data:
                parsed_data['actions'] = self._sanitize_string_list(parsed_data['actions'], 'actions')
            
            if 'data_categories' in parsed_data:
                parsed_data['data_categories'] = self._sanitize_string_list(parsed_data['data_categories'], 'data_categories')
            
            if 'data_subjects' in parsed_data:
                parsed_data['data_subjects'] = self._sanitize_string_list(parsed_data['data_subjects'], 'data_subjects')
            
            if 'geographic_scope' in parsed_data:
                parsed_data['geographic_scope'] = self._sanitize_string_list(parsed_data['geographic_scope'], 'geographic_scope')
            
            if 'evidence_requirements' in parsed_data:
                parsed_data['evidence_requirements'] = self._sanitize_string_list(parsed_data['evidence_requirements'], 'evidence_requirements')
            
            if 'verification_methods' in parsed_data:
                parsed_data['verification_methods'] = self._sanitize_string_list(parsed_data['verification_methods'], 'verification_methods')
            
            # Sanitize dict lists
            if 'permissions' in parsed_data:
                parsed_data['permissions'] = self._sanitize_dict_list(parsed_data['permissions'], 'permissions')
            
            if 'prohibitions' in parsed_data:
                parsed_data['prohibitions'] = self._sanitize_dict_list(parsed_data['prohibitions'], 'prohibitions')
            
            if 'constraints' in parsed_data:
                parsed_data['constraints'] = self._sanitize_dict_list(parsed_data['constraints'], 'constraints')
            
            # Ensure parties is a dict with list values
            if 'parties' in parsed_data:
                if isinstance(parsed_data['parties'], dict):
                    for key, value in parsed_data['parties'].items():
                        if isinstance(value, list):
                            parsed_data['parties'][key] = self._sanitize_string_list(value, f'parties.{key}')
                        else:
                            parsed_data['parties'][key] = []
                else:
                    parsed_data['parties'] = {}
            
            # Create components with sanitized data
            components = ODRLComponents(**parsed_data)
            logger.info(f"Stage 5 synthesis complete for {rule_name}")
            logger.info(f"  - Actions: {len(components.actions)}")
            logger.info(f"  - Permissions: {len(components.permissions)}")
            logger.info(f"  - Prohibitions: {len(components.prohibitions)}")
            logger.info(f"  - Constraints: {len(components.constraints)}")
            logger.info(f"  - Data categories: {len(components.data_categories)}")
            
            return components
            
        except ValidationError as e:
            logger.error(f"Pydantic validation error for {rule_name}: {e}")
            logger.error(f"Parsed data: {parsed_data}")
            
            # Return minimal valid structure with error info
            return ODRLComponents(
                extraction_reasoning=f"Validation error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error creating ODRLComponents for {rule_name}: {e}")
            logger.error(f"Parsed data: {parsed_data}")
            return ODRLComponents(
                extraction_reasoning=f"Error creating components: {str(e)}"
            )