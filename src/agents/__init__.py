"""
Enhanced ODRL to Rego Conversion Agents
Coverage-based approach with Mixture of Experts and AST validation
"""

# Main conversion functions
from .react_workflow import (
    convert_odrl_to_rego_with_coverage,
    convert_odrl_file_to_rego,
    consult_experts
)

# Agent creators
from .react_workflow import (
    create_coverage_parser_agent,
    create_jurisdiction_expert_agent,
    create_regex_expert_agent,
    create_type_system_expert_agent,
    create_logic_expert_agent,
    create_ast_expert_agent,
    create_mixture_of_experts_orchestrator,
    create_coverage_based_rego_generator,
    create_ast_validation_agent,
    create_reflection_agent,
    create_correction_agent
)

# Tools
from .react_tools import (
    # Coverage tools
    extract_coverage_and_jurisdictions,
    extract_custom_original_data,
    generate_regex_patterns_for_jurisdictions,
    
    # AST tools
    generate_ast_from_policy,
    validate_ast_logic,
    traverse_ast_by_coverage,
    
    # Enhanced constraint tools
    extract_and_infer_constraints_with_coverage,
    generate_coverage_based_rego_rule,
    
    # Original tools
    extract_policy_metadata,
    extract_permissions,
    extract_prohibitions,
    extract_constraints,
    analyze_rdfs_comments,
    analyze_operator,
    analyze_rightOperand,
    suggest_rego_pattern,
    check_rego_syntax,
    fix_missing_if
)

__all__ = [
    # Main conversion functions
    "convert_odrl_to_rego_with_coverage",
    "convert_odrl_file_to_rego",
    "consult_experts",
    
    # Agent creators
    "create_coverage_parser_agent",
    "create_jurisdiction_expert_agent",
    "create_regex_expert_agent",
    "create_type_system_expert_agent",
    "create_logic_expert_agent",
    "create_ast_expert_agent",
    "create_mixture_of_experts_orchestrator",
    "create_coverage_based_rego_generator",
    "create_ast_validation_agent",
    "create_reflection_agent",
    "create_correction_agent",
    
    # Coverage tools
    "extract_coverage_and_jurisdictions",
    "extract_custom_original_data",
    "generate_regex_patterns_for_jurisdictions",
    
    # AST tools
    "generate_ast_from_policy",
    "validate_ast_logic",
    "traverse_ast_by_coverage",
    
    # Enhanced tools
    "extract_and_infer_constraints_with_coverage",
    "generate_coverage_based_rego_rule",
    
    # Original tools
    "extract_policy_metadata",
    "extract_permissions",
    "extract_prohibitions",
    "extract_constraints",
    "analyze_rdfs_comments",
    "analyze_operator",
    "analyze_rightOperand",
    "suggest_rego_pattern",
    "check_rego_syntax",
    "fix_missing_if"
]