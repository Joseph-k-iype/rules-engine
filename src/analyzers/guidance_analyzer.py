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
from ..validators import ODRLLogicalValidator  # ← ADD THIS LINE

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
        """
        Stage 5: Synthesize all analyses into structured ODRL components
        with logical consistency validation.
        
        This method:
        1. Calls LLM to synthesize all previous analyses
        2. Parses and sanitizes the response
        3. Validates for logical duplications
        4. Auto-resolves duplications if found
        5. Re-validates after resolution
        6. Returns clean, consistent ODRL components
        
        Args:
            guidance_text: Complete guidance text
            rule_name: Name/title of the rule
            framework_type: DSS or DataVISA
            restriction_condition: restriction or condition
            initial_analysis: Stage 1 analysis output
            odrl_extraction: Stage 2 extraction output
            constraint_analysis: Stage 3 constraint analysis
            data_categories: Stage 4 data category identification
            
        Returns:
            ODRLComponents with validated and consistent data
        """
        
        logger.info(f"Stage 5: Synthesizing ODRL components for {rule_name}")
        
        # Build the synthesis prompt
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
        
        # Prepare messages for LLM
        messages = [
            SystemMessage(content=(
                "You are an expert system for creating ODRL policies. "
                "Synthesize complex analyses into precise, machine-readable ODRL structures. "
                "CRITICAL: Avoid creating duplicate constraints in both permissions and prohibitions. "
                "Each constraint should appear in only ONE place. Use logical reasoning to determine "
                "whether a constraint belongs in permissions or prohibitions. "
                "Prefer positive framing (permissions with positive operators) over negative framing. "
                "Return only valid JSON with actual extracted data, not template instructions."
            )),
            HumanMessage(content=prompt)
        ]
        
        try:
            # Get LLM response with lower temperature for consistency
            logger.debug(f"Requesting LLM synthesis for {rule_name}")
            response = await self.openai_service.get_completion(
                messages=messages,
                temperature=0.1,  # Lower temperature for more deterministic, consistent output
                max_tokens=4000
            )
            
            logger.debug(f"Received LLM response for {rule_name}")
            
            # Parse JSON response
            parsed_data = self.json_parser.parse_json_safely(response.content)
            
            if not parsed_data:
                logger.error(f"Failed to parse synthesis response for {rule_name}")
                logger.debug(f"Raw response: {response.content[:500]}...")
                return ODRLComponents(
                    extraction_reasoning="Failed to parse LLM response"
                )
            
            # Log LLM reasoning if provided
            if 'reasoning' in parsed_data:
                logger.info(f"LLM Reasoning for {rule_name}:")
                reasoning_lines = parsed_data['reasoning'].split('\n')
                for line in reasoning_lines[:10]:  # Log first 10 lines
                    if line.strip():
                        logger.info(f"  {line.strip()}")
                if len(reasoning_lines) > 10:
                    logger.info(f"  ... ({len(reasoning_lines) - 10} more lines)")
            
            # Sanitize data types to ensure proper structure
            logger.debug(f"Sanitizing parsed data for {rule_name}")
            
            # Ensure list fields are lists
            for key in ['actions', 'data_categories', 'data_subjects']:
                if key in parsed_data:
                    if not isinstance(parsed_data[key], list):
                        logger.warning(f"{key} is not a list, converting to empty list")
                        parsed_data[key] = []
                else:
                    parsed_data[key] = []
            
            # Sanitize rule lists (permissions, prohibitions, constraints)
            for key in ['permissions', 'prohibitions', 'constraints']:
                if key in parsed_data:
                    parsed_data[key] = self._sanitize_rule_list(
                        parsed_data.get(key), 
                        f'{key}'
                    )
                else:
                    parsed_data[key] = []
            
            # Sanitize parties structure
            if 'parties' in parsed_data:
                if isinstance(parsed_data['parties'], dict):
                    for key in ['controllers', 'processors', 'assigners', 
                            'assignees', 'third_parties']:
                        if key in parsed_data['parties']:
                            if not isinstance(parsed_data['parties'][key], list):
                                logger.warning(
                                    f'parties.{key} is not a list, converting to empty list'
                                )
                                parsed_data['parties'][key] = []
                        else:
                            parsed_data['parties'][key] = []
                else:
                    logger.warning("parties is not a dict, creating empty structure")
                    parsed_data['parties'] = {
                        'controllers': [],
                        'processors': [],
                        'assigners': [],
                        'assignees': [],
                        'third_parties': []
                    }
            else:
                parsed_data['parties'] = {
                    'controllers': [],
                    'processors': [],
                    'assigners': [],
                    'assignees': [],
                    'third_parties': []
                }
            
            # Create initial components from parsed data
            logger.debug(f"Creating ODRLComponents for {rule_name}")
            try:
                components = ODRLComponents(**parsed_data)
            except ValidationError as e:
                logger.error(f"Pydantic validation error for {rule_name}: {e}")
                logger.error(f"Parsed data keys: {list(parsed_data.keys())}")
                return ODRLComponents(
                    extraction_reasoning=f"Validation error: {str(e)}"
                )
            
            # ═══════════════════════════════════════════════════════════════
            # VALIDATION STEP: Check for logical duplications
            # ═══════════════════════════════════════════════════════════════
            
            logger.info(f"Validating logical consistency for {rule_name}")
            validator = ODRLLogicalValidator(strict_mode=False)
            validation_results = validator.validate_components(components)
            
            if not validation_results.valid:
                logger.warning(f"⚠️  Logical inconsistencies found in {rule_name}:")
                logger.warning(f"   Total errors: {len(validation_results.errors)}")
                logger.warning(f"   Total duplications: {len(validation_results.duplications)}")
                
                # Log each error
                for error in validation_results.errors:
                    logger.warning(f"  ❌ {error}")
                
                # Log suggestions
                for suggestion in validation_results.suggestions:
                    logger.info(f"  💡 {suggestion}")
                
                # AUTO-RESOLVE: Remove duplications
                if validation_results.duplications:
                    logger.info(f"Attempting auto-resolution for {rule_name}...")
                    
                    # Apply auto-resolution
                    components = validator.auto_resolve_duplications(
                        components, 
                        validation_results
                    )
                    
                    # Re-validate after resolution
                    logger.info(f"Re-validating after auto-resolution...")
                    revalidation = validator.validate_components(components)
                    
                    if revalidation.valid:
                        logger.info(f"✅ Auto-resolution successful for {rule_name}")
                        logger.info(f"   All logical duplications resolved")
                    else:
                        logger.warning(
                            f"⚠️  Some issues remain after auto-resolution for {rule_name}"
                        )
                        if revalidation.errors:
                            logger.warning(f"   Remaining errors: {len(revalidation.errors)}")
                            for error in revalidation.errors[:3]:  # Log first 3
                                logger.warning(f"   - {error}")
            else:
                logger.info(f"✅ No logical duplications found in {rule_name}")
            
            # Log final component statistics
            logger.info(f"Stage 5 synthesis complete for {rule_name}")
            logger.info(f"  - Actions: {len(components.actions)}")
            logger.info(f"  - Permissions: {len(components.permissions)}")
            logger.info(f"  - Prohibitions: {len(components.prohibitions)}")
            logger.info(f"  - Constraints: {len(components.constraints)}")
            logger.info(f"  - Data categories: {len(components.data_categories)}")
            logger.info(f"  - Data subjects: {len(components.data_subjects)}")
            
            # Log warnings if prohibitions still exist (might be intentional)
            if len(components.prohibitions) > 0:
                logger.debug(f"  Note: {len(components.prohibitions)} prohibition(s) present")
                for i, prohib in enumerate(components.prohibitions):
                    if isinstance(prohib, dict):
                        action = prohib.get('action', 'unknown')
                        constraint_count = len(prohib.get('constraints', []))
                        logger.debug(f"    Prohibition {i}: action={action}, constraints={constraint_count}")
            
            return components
            
        except ValidationError as e:
            logger.error(f"Pydantic validation error for {rule_name}: {e}")
            logger.error(f"Parsed data structure:")
            if parsed_data:
                for key in parsed_data.keys():
                    logger.error(f"  - {key}: {type(parsed_data[key])}")
            
            # Return minimal valid structure with error info
            return ODRLComponents(
                extraction_reasoning=f"Validation error: {str(e)}"
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in synthesis for {rule_name}: {e}")
            logger.exception("Full traceback:")
            return ODRLComponents(
                extraction_reasoning=f"Error in synthesis: {str(e)}"
            )


    def _sanitize_rule_list(self, data: Any, field_name: str) -> List[Dict]:
        """
        Sanitize rule lists to ensure they contain only valid dictionaries.
        
        Args:
            data: Data to sanitize
            field_name: Name of the field for logging
            
        Returns:
            List of valid dictionaries
        """
        if not data:
            return []
        
        if not isinstance(data, list):
            logger.warning(f"{field_name} is not a list: {type(data)}")
            return []
        
        sanitized = []
        for i, item in enumerate(data):
            if isinstance(item, dict):
                sanitized.append(item)
            else:
                logger.warning(
                    f"Non-dict item in {field_name}[{i}]: {type(item)}, skipping"
                )
        
        return sanitized