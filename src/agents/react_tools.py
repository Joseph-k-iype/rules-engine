"""
ReAct Tools for ODRL to Rego Conversion
Tools that agents can use to analyze and convert ODRL policies
"""
import json
import re
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field


# ============================================================================
# ODRL Parser Tools
# ============================================================================

class PolicyMetadata(BaseModel):
    """Metadata extracted from ODRL policy"""
    policy_id: str
    policy_type: str
    has_permissions: bool
    has_prohibitions: bool
    has_obligations: bool
    permission_count: int
    prohibition_count: int


@tool
def extract_policy_metadata(odrl_json: str) -> Dict[str, Any]:
    """
    Extract high-level metadata from an ODRL policy.
    
    Args:
        odrl_json: JSON string of the ODRL policy
        
    Returns:
        Dictionary with policy ID, type, and structural overview
    """
    try:
        policy = json.loads(odrl_json) if isinstance(odrl_json, str) else odrl_json
        
        # Extract policy ID - can be uid, @id, or policyid
        policy_id = policy.get("uid") or policy.get("@id") or policy.get("policyid", "unknown")
        
        # Extract policy type
        policy_type = policy.get("@type", policy.get("policytype", "Set"))
        
        # Count rules
        permissions = policy.get("permission", [])
        prohibitions = policy.get("prohibition", [])
        obligations = policy.get("obligation", [])
        
        return {
            "policy_id": policy_id,
            "policy_type": policy_type,
            "has_permissions": len(permissions) > 0,
            "has_prohibitions": len(prohibitions) > 0,
            "has_obligations": len(obligations) > 0,
            "permission_count": len(permissions),
            "prohibition_count": len(prohibitions),
            "obligation_count": len(obligations)
        }
    except Exception as e:
        return {"error": f"Failed to extract metadata: {str(e)}"}


@tool
def extract_permissions(odrl_json: str) -> Dict[str, Any]:
    """
    Extract all permission rules from ODRL policy with semantic analysis.
    
    Args:
        odrl_json: JSON string of the ODRL policy
        
    Returns:
        Structured list of permissions with actions, targets, constraints
    """
    try:
        policy = json.loads(odrl_json) if isinstance(odrl_json, str) else odrl_json
        permissions = policy.get("permission", [])
        
        extracted = []
        for idx, perm in enumerate(permissions):
            extracted.append({
                "id": f"permission_{idx}",
                "action": perm.get("action"),
                "target": perm.get("target"),
                "assignee": perm.get("assignee"),
                "assigner": perm.get("assigner"),
                "constraints": perm.get("constraint", []),
                "duties": perm.get("duty", []),
                "refinement": perm.get("refinement")
            })
        
        return {
            "permissions": extracted,
            "count": len(extracted),
            "analysis": f"Found {len(extracted)} permission rule(s)"
        }
    except Exception as e:
        return {"error": f"Failed to extract permissions: {str(e)}"}


@tool
def extract_prohibitions(odrl_json: str) -> Dict[str, Any]:
    """
    Extract all prohibition rules from ODRL policy.
    
    Args:
        odrl_json: JSON string of the ODRL policy
        
    Returns:
        Structured list of prohibitions
    """
    try:
        policy = json.loads(odrl_json) if isinstance(odrl_json, str) else odrl_json
        prohibitions = policy.get("prohibition", [])
        
        extracted = []
        for idx, prohib in enumerate(prohibitions):
            extracted.append({
                "id": f"prohibition_{idx}",
                "action": prohib.get("action"),
                "target": prohib.get("target"),
                "assignee": prohib.get("assignee"),
                "assigner": prohib.get("assigner"),
                "constraints": prohib.get("constraint", []),
                "remedy": prohib.get("remedy")
            })
        
        return {
            "prohibitions": extracted,
            "count": len(extracted),
            "analysis": f"Found {len(extracted)} prohibition rule(s)"
        }
    except Exception as e:
        return {"error": f"Failed to extract prohibitions: {str(e)}"}


@tool
def extract_constraints(constraint_data: str) -> Dict[str, Any]:
    """
    Analyze constraint structures including nested logical operators.
    
    Args:
        constraint_data: JSON string of constraint or constraint array
        
    Returns:
        Parsed constraints with structure and evaluation hints
    """
    try:
        constraints = json.loads(constraint_data) if isinstance(constraint_data, str) else constraint_data
        
        if not isinstance(constraints, list):
            constraints = [constraints]
        
        analyzed = []
        for idx, constraint in enumerate(constraints):
            analysis = {
                "id": f"constraint_{idx}",
                "type": "simple" if "leftOperand" in constraint else "logical",
            }
            
            if "leftOperand" in constraint:
                # Simple constraint
                analysis.update({
                    "leftOperand": constraint.get("leftOperand"),
                    "operator": constraint.get("operator"),
                    "rightOperand": constraint.get("rightOperand"),
                    "rdfs_comment": constraint.get("rdfs:comment"),
                    "dataType": constraint.get("dataType")
                })
            else:
                # Logical constraint (and/or/xone)
                for op in ["and", "or", "xone", "andSequence"]:
                    if op in constraint:
                        analysis["logical_operator"] = op
                        analysis["nested_constraints"] = constraint[op]
                        break
            
            analyzed.append(analysis)
        
        return {
            "constraints": analyzed,
            "count": len(analyzed),
            "has_logical": any(c["type"] == "logical" for c in analyzed)
        }
    except Exception as e:
        return {"error": f"Failed to analyze constraints: {str(e)}"}


@tool
def analyze_rdfs_comments(odrl_json: str) -> Dict[str, Any]:
    """
    Extract RDFS comments that provide legislative and business context.
    
    Args:
        odrl_json: JSON string of the ODRL policy
        
    Returns:
        Mapping of components to semantic meanings from comments
    """
    try:
        policy = json.loads(odrl_json) if isinstance(odrl_json, str) else odrl_json
        
        def find_comments(obj, path=""):
            comments = {}
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if key == "rdfs:comment" or key == "comment":
                        comments[path] = value
                    elif isinstance(value, (dict, list)):
                        comments.update(find_comments(value, new_path))
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    comments.update(find_comments(item, f"{path}[{idx}]"))
            return comments
        
        comments = find_comments(policy)
        
        return {
            "comments": comments,
            "count": len(comments),
            "paths": list(comments.keys())
        }
    except Exception as e:
        return {"error": f"Failed to analyze RDFS comments: {str(e)}"}


# ============================================================================
# Type Inference Tools
# ============================================================================

@tool
def analyze_operator(operator: str) -> Dict[str, Any]:
    """
    Analyze ODRL operator semantics and determine type implications.
    
    Args:
        operator: ODRL operator (e.g., 'eq', 'lt', 'gt', 'isAnyOf')
        
    Returns:
        Operator semantics, expected types, and Rego equivalent
    """
    operator_map = {
        "eq": {
            "meaning": "equals",
            "rego": "==",
            "types": ["string", "number", "boolean"],
            "description": "Direct equality comparison"
        },
        "neq": {
            "meaning": "not equals",
            "rego": "!=",
            "types": ["string", "number", "boolean"],
            "description": "Direct inequality comparison"
        },
        "lt": {
            "meaning": "less than",
            "rego": "<",
            "types": ["number", "temporal"],
            "description": "Numeric or temporal comparison"
        },
        "gt": {
            "meaning": "greater than",
            "rego": ">",
            "types": ["number", "temporal"],
            "description": "Numeric or temporal comparison"
        },
        "lteq": {
            "meaning": "less than or equal",
            "rego": "<=",
            "types": ["number", "temporal"],
            "description": "Numeric or temporal comparison with equality"
        },
        "gteq": {
            "meaning": "greater than or equal",
            "rego": ">=",
            "types": ["number", "temporal"],
            "description": "Numeric or temporal comparison with equality"
        },
        "isAnyOf": {
            "meaning": "is any of (set membership)",
            "rego": "in",
            "types": ["string", "number"],
            "description": "Check if value is in a set"
        },
        "isAllOf": {
            "meaning": "is all of (subset)",
            "rego": "custom_function",
            "types": ["array"],
            "description": "Check if all values are present"
        },
        "isNoneOf": {
            "meaning": "is none of (exclusion)",
            "rego": "not in",
            "types": ["string", "number"],
            "description": "Check if value is not in a set"
        }
    }
    
    if operator in operator_map:
        return operator_map[operator]
    else:
        return {
            "meaning": "unknown",
            "rego": "==",
            "types": ["unknown"],
            "description": f"Unknown operator: {operator}"
        }


@tool  
def analyze_rightOperand(value: str) -> Dict[str, Any]:
    """
    Infer data type from rightOperand value format.
    
    Args:
        value: The rightOperand value as string
        
    Returns:
        Type classification and Rego representation
    """
    value_str = str(value)
    
    # Check for ISO 8601 datetime
    if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value_str):
        return {
            "type": "temporal_datetime",
            "format": "ISO 8601",
            "rego_type": "string",
            "rego_function": "time.parse_rfc3339_ns",
            "pattern": f'time.parse_rfc3339_ns("{value_str}")'
        }
    
    # Check for ISO 8601 duration
    if re.match(r'P(\d+Y)?(\d+M)?(\d+D)?(T(\d+H)?(\d+M)?(\d+S)?)?', value_str):
        return {
            "type": "temporal_duration",
            "format": "ISO 8601 duration",
            "rego_type": "string",
            "rego_function": "time.parse_duration_ns",
            "pattern": f'time.parse_duration_ns("{value_str}")'
        }
    
    # Check for URI
    if value_str.startswith("http://") or value_str.startswith("https://"):
        return {
            "type": "uri",
            "rego_type": "string",
            "pattern": f'"{value_str}"'
        }
    
    # Check for number
    try:
        float(value_str)
        if '.' in value_str:
            return {
                "type": "float",
                "rego_type": "number",
                "pattern": value_str
            }
        else:
            return {
                "type": "integer",
                "rego_type": "number",
                "pattern": value_str
            }
    except ValueError:
        pass
    
    # Default to string
    return {
        "type": "string",
        "rego_type": "string",
        "pattern": f'"{value_str}"'
    }


@tool
def suggest_rego_pattern(constraint: str) -> Dict[str, Any]:
    """
    Generate Rego code pattern for a specific constraint.
    
    Args:
        constraint: JSON string of the constraint
        
    Returns:
        Rego code pattern with type-safe evaluation
    """
    try:
        c = json.loads(constraint) if isinstance(constraint, str) else constraint
        
        left_op = c.get("leftOperand", "input.unknown")
        operator = c.get("operator", "eq")
        right_op = c.get("rightOperand")
        
        # Analyze types
        op_analysis = analyze_operator(operator)
        value_analysis = analyze_rightOperand(str(right_op))
        
        # Generate pattern
        input_ref = f"input.{left_op}" if not left_op.startswith("input.") else left_op
        
        if value_analysis["type"].startswith("temporal"):
            if operator in ["lt", "lteq"]:
                pattern = f'time.now_ns() {op_analysis["rego"]} {value_analysis["pattern"]}'
            else:
                pattern = f'{value_analysis["pattern"]} {op_analysis["rego"]} time.now_ns()'
        else:
            pattern = f'{input_ref} {op_analysis["rego"]} {value_analysis["pattern"]}'
        
        return {
            "rego_pattern": pattern,
            "variables": [input_ref],
            "functions": value_analysis.get("rego_function", [])
        }
    except Exception as e:
        return {"error": f"Failed to generate pattern: {str(e)}"}


# ============================================================================
# Rego Validation Tools
# ============================================================================

@tool
def check_rego_syntax(rego_code: str) -> Dict[str, Any]:
    """
    Check Rego code for syntax compliance with Rego v1.
    
    Args:
        rego_code: The Rego code to validate
        
    Returns:
        Syntax validation results with errors and suggestions
    """
    errors = []
    suggestions = []
    
    # Check for import rego.v1
    if "import rego.v1" not in rego_code:
        errors.append({
            "line": 1,
            "error": "Missing 'import rego.v1' statement",
            "suggestion": "Add 'import rego.v1' after package declaration"
        })
    
    # Check for 'if' keywords in rules
    lines = rego_code.split('\n')
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Check if line looks like a rule definition without 'if'
        if ':=' in stripped or '=' in stripped:
            if '{' in stripped and 'if' not in stripped:
                # Skip default declarations
                if not stripped.startswith('default '):
                    errors.append({
                        "line": idx,
                        "error": f"Rule definition missing 'if' keyword (Rego v1 requirement)",
                        "suggestion": f"Add 'if' before '{{' on line {idx}"
                    })
    
    # Check for 'contains' in set rules
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if re.match(r'^\w+\s+\w+\s+if\s+{', stripped):
            if 'contains' not in stripped:
                suggestions.append({
                    "line": idx,
                    "suggestion": "Consider using 'contains' for multi-value rules"
                })
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "suggestions": suggestions,
        "error_count": len(errors)
    }


@tool
def fix_missing_if(rego_code: str) -> Dict[str, Any]:
    """
    Automatically add missing 'if' keywords to Rego code.
    
    Args:
        rego_code: The Rego code to fix
        
    Returns:
        Corrected code with 'if' keywords added
    """
    lines = rego_code.split('\n')
    fixed_lines = []
    changes = []
    
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Check if this is a rule that needs 'if'
        if ((':=' in stripped or '=' in stripped) and 
            '{' in stripped and 
            'if' not in stripped and
            not stripped.startswith('default ') and
            not stripped.startswith('package ') and
            not stripped.startswith('import ')):
            
            # Add 'if' before '{'
            fixed_line = line.replace('{', 'if {')
            fixed_lines.append(fixed_line)
            changes.append(f"Line {idx}: Added 'if' keyword")
        else:
            fixed_lines.append(line)
    
    return {
        "corrected_code": '\n'.join(fixed_lines),
        "changes": changes,
        "change_count": len(changes)
    }


# Export all tools
__all__ = [
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