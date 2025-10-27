"""
Enhanced Agent State for Coverage-Based ODRL to Rego Conversion
Includes AST validation, jurisdiction-based rules, and advanced reasoning tracking
"""
from typing import TypedDict, Dict, Any, List, Optional
from enum import Enum


class ConversionStage(str, Enum):
    """Stages in the ODRL to Rego conversion workflow"""
    INITIALIZATION = "initialization"
    ODRL_PARSING = "odrl_parsing"
    COVERAGE_EXTRACTION = "coverage_extraction"  # NEW: Extract jurisdictions
    TYPE_INFERENCE = "type_inference"
    LOGIC_ANALYSIS = "logic_analysis"
    AST_GENERATION = "ast_generation"  # NEW: Generate AST for validation
    AST_VALIDATION = "ast_validation"  # NEW: Validate logic via AST
    REGO_GENERATION = "rego_generation"
    REFLECTION = "reflection"
    MIXTURE_OF_EXPERTS = "mixture_of_experts"  # NEW: Expert consultation
    CORRECTION = "correction"
    COMPLETED = "completed"
    FAILED = "failed"


class ExpertType(str, Enum):
    """Types of expert agents in mixture of experts pattern"""
    JURISDICTION_EXPERT = "jurisdiction_expert"  # Jurisdiction/coverage analysis
    REGEX_EXPERT = "regex_expert"  # Pattern matching expert
    TYPE_SYSTEM_EXPERT = "type_system_expert"  # Data type expert
    LOGIC_EXPERT = "logic_expert"  # Logical reasoning expert
    REGO_SYNTAX_EXPERT = "rego_syntax_expert"  # Rego syntax expert
    AST_EXPERT = "ast_expert"  # Abstract syntax tree expert


class AgentState(TypedDict, total=False):
    """
    Enhanced agent state with coverage-based rules and AST validation.
    This represents the complete context for ODRL to Rego conversion.
    """
    # Input
    odrl_json: Dict[str, Any]  # The input ODRL JSON-LD document
    existing_rego: Optional[str]  # Existing Rego rules if appending
    
    # Coverage/Jurisdiction Analysis (NEW - PRIMARY GROUPING)
    coverage_groups: List[Dict[str, Any]]  # Grouped by jurisdiction
    jurisdiction_patterns: Dict[str, List[str]]  # action -> [jurisdictions]
    coverage_hierarchy: Dict[str, Any]  # Hierarchical jurisdiction structure
    regex_patterns: Dict[str, str]  # Jurisdiction matching patterns
    custom_original_data: Dict[str, Any]  # Maps custom:originalData id to rules
    
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
    
    # AST Validation (NEW)
    ast_tree: Dict[str, Any]  # Abstract syntax tree representation
    ast_validation_results: Dict[str, Any]  # AST validation results
    ast_traversal_log: List[str]  # Log of AST traversal steps
    logic_correctness_score: float  # 0-1 score from AST analysis
    
    # Generated Rego (Coverage-Based)
    generated_rego: str  # The generated Rego code
    rego_package: str  # Package name for the Rego rules
    rego_imports: List[str]  # Required imports
    rego_rules_by_coverage: Dict[str, List[str]]  # jurisdiction -> [rules]
    
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
    
    # Advanced reasoning (NEW)
    reasoning_chain: List[Dict[str, str]]  # step -> reasoning mapping
    chain_of_thought: List[Dict[str, Any]]  # Detailed CoT reasoning
    
    # Mixture of Experts (NEW)
    expert_analyses: Dict[str, Dict[str, Any]]  # expert_type -> analysis
    expert_consensus: Dict[str, Any]  # Aggregated expert opinions
    expert_disagreements: List[Dict[str, Any]]  # Points of expert disagreement
    
    # Self-reflection (NEW)
    reflection_iterations: List[Dict[str, Any]]  # History of self-reflections
    confidence_scores: Dict[str, float]  # Component -> confidence
    uncertainty_areas: List[str]  # Areas of uncertainty


class RegoValidationResult(TypedDict):
    """Result of Rego validation"""
    is_valid: bool
    syntax_errors: List[str]
    logic_errors: List[str]
    suggestions: List[str]
    confidence_score: float
    ast_validation: Optional[Dict[str, Any]]  # NEW: AST validation details


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
    coverage: List[str]  # NEW: Applicable jurisdictions
    custom_original_data_id: Optional[str]  # NEW: Reference to original data


class CoverageAnalysis(TypedDict):
    """Analysis of coverage/jurisdiction for rules"""
    jurisdictions: List[str]  # List of applicable jurisdictions
    regex_pattern: str  # Regex pattern for matching jurisdictions
    hierarchy_level: int  # Level in jurisdiction hierarchy
    parent_jurisdiction: Optional[str]  # Parent in hierarchy
    action_groups: Dict[str, List[str]]  # action -> [applicable_jurisdictions]


class ASTNode(TypedDict):
    """Node in the Abstract Syntax Tree"""
    node_type: str  # rule, constraint, logical_op, etc.
    node_id: str
    value: Any
    children: List['ASTNode']
    parent_id: Optional[str]
    metadata: Dict[str, Any]


class ExpertAnalysis(TypedDict):
    """Analysis from a single expert in mixture of experts"""
    expert_type: ExpertType
    analysis: str
    confidence: float  # 0-1
    recommendations: List[str]
    reasoning_steps: List[str]
    concerns: List[str]