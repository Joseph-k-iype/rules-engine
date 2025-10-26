"""
ODRL to Rego Conversion Agents
LangGraph ReAct-based multi-agent system for policy conversion
"""

# ReAct workflow (recommended)
from .react_workflow import (
    convert_odrl_to_rego_react,
    convert_odrl_file_to_rego,
    create_odrl_parser_agent,
    create_type_inference_agent,
    create_rego_generator_agent,
    create_reflection_agent,
    create_correction_agent
)

# ReAct tools
from .react_tools import (
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
    "convert_odrl_to_rego_react",
    "convert_odrl_file_to_rego",
    
    # Agent creators
    "create_odrl_parser_agent",
    "create_type_inference_agent",
    "create_rego_generator_agent",
    "create_reflection_agent",
    "create_correction_agent",
    
    # Tools
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