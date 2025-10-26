"""
Agent State Management for ODRL to Rego Conversion
"""
from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum


class ConversionStage(str, Enum):
    """Stages in the ODRL to Rego conversion process"""
    PARSING = "parsing"
    TYPE_INFERENCE = "type_inference"
    LOGIC_ANALYSIS = "logic_analysis"
    REGO_GENERATION = "rego_generation"
    VALIDATION = "validation"
    CORRECTION = "correction"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentState(TypedDict):
    """
    State shared across all agents in the LangGraph workflow.
    This represents the complete context for ODRL to Rego conversion.
    """
    # Input
    odrl_json: Dict[str, Any]  # The input ODRL JSON-LD document
    existing_rego: Optional[str]  # Existing Rego rules if appending
    
    # Parsed ODRL components
    policy_id: str
    policy_type: str
    permissions: List[Dict[str, Any]]
    prohibitions: List[Dict[str, Any]]
    obligations: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    rdfs_comments: Dict[str, str]  # URI -> comment mapping
    custom_properties: Dict[str, Any]  # Custom ODRL extensions
    
    # Type inference results
    inferred_types: Dict[str, str]  # property_path -> data_type
    constraint_evaluations: List[Dict[str, Any]]  # constraint context analysis
    
    # Logic analysis results
    permission_rules: List[Dict[str, Any]]  # structured permission logic
    prohibition_rules: List[Dict[str, Any]]  # structured prohibition logic
    negation_validation: Dict[str, Any]  # prohibition vs permission consistency
    logical_issues: List[str]  # detected logical inconsistencies
    
    # Generated Rego
    generated_rego: str  # The generated Rego code
    rego_package: str  # Package name for the Rego rules
    rego_imports: List[str]  # Required imports
    
    # Validation results
    syntax_errors: List[str]  # Syntax errors in generated Rego
    logic_errors: List[str]  # Logical errors in generated Rego
    validation_passed: bool
    reflection_feedback: str  # Feedback from reflection agent
    
    # Correction tracking
    correction_attempts: int  # Number of correction iterations
    max_corrections: int  # Maximum allowed corrections
    corrections_applied: List[str]  # History of corrections
    
    # Workflow control
    current_stage: ConversionStage
    error_message: Optional[str]
    messages: List[str]  # Log messages throughout the process
    
    # Chain of thought reasoning
    reasoning_chain: List[Dict[str, str]]  # step -> reasoning mapping
    
    # Expert consultation (mixture of experts pattern)
    expert_analyses: Dict[str, str]  # expert_type -> analysis


class RegoValidationResult(TypedDict):
    """Result of Rego validation"""
    is_valid: bool
    syntax_errors: List[str]
    logic_errors: List[str]
    suggestions: List[str]
    confidence_score: float


class ODRLComponentAnalysis(TypedDict):
    """Analysis of a single ODRL component"""
    component_type: str  # permission, prohibition, duty, constraint
    component_id: str
    action: str
    target: Optional[str]
    constraints: List[Dict[str, Any]]
    inferred_data_types: Dict[str, str]
    rego_template: str  # Suggested Rego pattern
    reasoning: str  # Chain of thought for this component