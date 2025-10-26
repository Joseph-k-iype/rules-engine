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
        constraint_data: JSON string or dict of constraints
        
    Returns:
        Parsed constraints with structure and patterns
    """
    try:
        if isinstance(constraint_data, str):
            constraints = json.loads(constraint_data)
        else:
            constraints = constraint_data
        
        if not isinstance(constraints, list):
            constraints = [constraints]
        
        analyzed = []
        for idx, constraint in enumerate(constraints):
            analyzed.append({
                "id": f"constraint_{idx}",
                "leftOperand": constraint.get("leftOperand"),
                "operator": constraint.get("operator"),
                "rightOperand": constraint.get("rightOperand"),
                "unit": constraint.get("unit"),
                "dataType": constraint.get("dataType"),
                "and": constraint.get("and"),
                "or": constraint.get("or"),
                "xone": constraint.get("xone")
            })
        
        return {
            "constraints": analyzed,
            "count": len(analyzed),
            "has_logical_operators": any(c.get("and") or c.get("or") or c.get("xone") for c in analyzed)
        }
    except Exception as e:
        return {"error": f"Failed to extract constraints: {str(e)}"}


@tool
def analyze_rdfs_comments(odrl_json: str) -> Dict[str, Any]:
    """
    Extract RDFS comments for semantic context.
    
    Args:
        odrl_json: JSON string of the ODRL policy
        
    Returns:
        Mapping of URIs to their rdfs:comment values
    """
    try:
        policy = json.loads(odrl_json) if isinstance(odrl_json, str) else odrl_json
        comments = {}
        
        def extract_comments(obj, path=""):
            if isinstance(obj, dict):
                if "rdfs:comment" in obj:
                    uri = obj.get("@id", path)
                    comments[uri] = obj["rdfs:comment"]
                for key, value in obj.items():
                    extract_comments(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_comments(item, f"{path}[{i}]")
        
        extract_comments(policy)
        
        return {
            "comments": comments,
            "count": len(comments),
            "analysis": f"Found {len(comments)} RDFS comment(s)"
        }
    except Exception as e:
        return {"error": f"Failed to analyze RDFS comments: {str(e)}"}


# ============================================================================
# Type Inference Tools
# ============================================================================

@tool
def analyze_operator(operator: str) -> Dict[str, Any]:
    """
    Analyze ODRL operator and suggest Rego equivalent.
    
    Args:
        operator: ODRL operator (eq, neq, lt, gt, lteq, gteq, etc.)
        
    Returns:
        Operator analysis with Rego mapping
    """
    operator_map = {
        "eq": {"rego": "==", "type_hint": "any", "description": "Equal to"},
        "neq": {"rego": "!=", "type_hint": "any", "description": "Not equal to"},
        "lt": {"rego": "<", "type_hint": "numeric/temporal", "description": "Less than"},
        "gt": {"rego": ">", "type_hint": "numeric/temporal", "description": "Greater than"},
        "lteq": {"rego": "<=", "type_hint": "numeric/temporal", "description": "Less than or equal"},
        "gteq": {"rego": ">=", "type_hint": "numeric/temporal", "description": "Greater than or equal"},
        "isA": {"rego": "==", "type_hint": "type/class", "description": "Is instance of"},
        "hasPart": {"rego": "in", "type_hint": "array/set", "description": "Contains element"},
        "isPartOf": {"rego": "in", "type_hint": "array/set", "description": "Is element of"}
    }
    
    analysis = operator_map.get(operator, {
        "rego": "==",
        "type_hint": "unknown",
        "description": "Unknown operator"
    })
    
    return {
        "operator": operator,
        "rego": analysis["rego"],
        "type_hint": analysis["type_hint"],
        "description": analysis["description"]
    }


@tool
def analyze_rightOperand(right_operand: str) -> Dict[str, Any]:
    """
    Infer data type from rightOperand value.
    
    Args:
        right_operand: The right operand value
        
    Returns:
        Type analysis with Rego pattern
    """
    # Temporal patterns
    if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', str(right_operand)):
        return {
            "type": "temporal_datetime",
            "pattern": f'time.parse_rfc3339_ns("{right_operand}")',
            "rego_function": ["time.parse_rfc3339_ns", "time.now_ns"]
        }
    
    if re.match(r'\d{4}-\d{2}-\d{2}', str(right_operand)):
        return {
            "type": "temporal_date",
            "pattern": f'time.parse_rfc3339_ns("{right_operand}T00:00:00Z")',
            "rego_function": ["time.parse_rfc3339_ns"]
        }
    
    # Numeric
    try:
        if '.' in str(right_operand):
            float(right_operand)
            return {
                "type": "numeric_float",
                "pattern": str(right_operand),
                "rego_function": []
            }
        else:
            int(right_operand)
            return {
                "type": "numeric_int",
                "pattern": str(right_operand),
                "rego_function": []
            }
    except (ValueError, TypeError):
        pass
    
    # URI
    if str(right_operand).startswith("http://") or str(right_operand).startswith("https://"):
        return {
            "type": "uri",
            "pattern": f'"{right_operand}"',
            "rego_function": []
        }
    
    # Boolean
    if str(right_operand).lower() in ["true", "false"]:
        return {
            "type": "boolean",
            "pattern": str(right_operand).lower(),
            "rego_function": []
        }
    
    # Default to string
    return {
        "type": "string",
        "pattern": f'"{right_operand}"',
        "rego_function": []
    }


@tool
def suggest_rego_pattern(constraint: str) -> Dict[str, Any]:
    """
    Generate Rego code pattern for a constraint.
    
    Args:
        constraint: JSON string of constraint
        
    Returns:
        Rego code pattern with variables and functions
    """
    try:
        c = json.loads(constraint) if isinstance(constraint, str) else constraint
        
        left_op = c.get("leftOperand", "")
        operator = c.get("operator", "eq")
        right_op = c.get("rightOperand", "")
        
        op_analysis = analyze_operator(operator)
        value_analysis = analyze_rightOperand(right_op)
        
        # Generate input reference
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