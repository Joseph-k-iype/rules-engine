"""
ReAct Tools for ODRL to Rego Conversion - COMPLETE VERSION
Includes ALL original tools PLUS intelligent type inference
"""
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Add project root to path for type inference engine
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Try to import type inference engine (graceful fallback if not available)
try:
    from src.agents.type_inference_engine import get_type_inference_engine
    TYPE_INFERENCE_AVAILABLE = True
except ImportError:
    TYPE_INFERENCE_AVAILABLE = False
    print("Warning: Type inference engine not available. Using basic type detection.")


# ============================================================================
# ODRL Parser Tools (ALL ORIGINAL FUNCTIONALITY)
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
            "obligation_count": len(obligations),
            "has_context": "@context" in policy
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
                "refinement": perm.get("refinement"),
                "rdfs_comment": perm.get("rdfs:comment", "")
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
                "remedy": prohib.get("remedy"),
                "rdfs_comment": prohib.get("rdfs:comment", "")
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
                "xone": constraint.get("xone"),
                "rdfs_comment": constraint.get("rdfs:comment", "")
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
# Type Inference Tools (ORIGINAL + ENHANCED)
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
        "isAnyOf": {"rego": "in", "type_hint": "set", "description": "Is any of"},
        "isAllOf": {"rego": "all", "type_hint": "set", "description": "Is all of"},
        "isNoneOf": {"rego": "not in", "type_hint": "set", "description": "Is none of"},
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
    
    if re.match(r'\d{4}-\d{2}-\d{2}$', str(right_operand)):
        return {
            "type": "temporal_date",
            "pattern": f'time.parse_rfc3339_ns("{right_operand}T00:00:00Z")',
            "rego_function": ["time.parse_rfc3339_ns"]
        }
    
    # Duration pattern (ISO 8601)
    if re.match(r'^P(\d+Y)?(\d+M)?(\d+D)?(T(\d+H)?(\d+M)?(\d+S)?)?$', str(right_operand)):
        return {
            "type": "temporal_duration",
            "pattern": f'time.parse_duration_ns("{right_operand}")',
            "rego_function": ["time.parse_duration_ns"]
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
        
        # Handle different value types
        if value_analysis["type"].startswith("temporal"):
            if operator in ["lt", "lteq"]:
                pattern = f'time.now_ns() {op_analysis["rego"]} {value_analysis["pattern"]}'
            else:
                pattern = f'{value_analysis["pattern"]} {op_analysis["rego"]} time.now_ns()'
        elif isinstance(right_op, list):
            # Handle sets/arrays
            formatted_values = ', '.join([f'"{v}"' if isinstance(v, str) else str(v) for v in right_op])
            pattern = f'{input_ref} in {{{formatted_values}}}'
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
# TYPE INFERENCE TOOLS (NEW - INTELLIGENT TYPE DETECTION)
# ============================================================================

@tool
def extract_and_infer_constraints(odrl_json: str) -> Dict[str, Any]:
    """
    Extract ALL constraints from ODRL policy and infer their data types.
    Uses intelligent type inference engine if available.
    
    Args:
        odrl_json: JSON string of the ODRL policy
        
    Returns:
        All constraints with inferred types and Rego recommendations
    """
    try:
        policy = json.loads(odrl_json) if isinstance(odrl_json, str) else odrl_json
        
        all_constraints = []
        
        # Process permissions
        for perm_idx, perm in enumerate(policy.get("permission", [])):
            for const_idx, constraint in enumerate(perm.get("constraint", [])):
                result = _analyze_constraint_with_inference(
                    constraint, 
                    f"permission_{perm_idx}_constraint_{const_idx}",
                    "permission"
                )
                all_constraints.append(result)
        
        # Process prohibitions
        for prohib_idx, prohib in enumerate(policy.get("prohibition", [])):
            for const_idx, constraint in enumerate(prohib.get("constraint", [])):
                result = _analyze_constraint_with_inference(
                    constraint,
                    f"prohibition_{prohib_idx}_constraint_{const_idx}",
                    "prohibition"
                )
                all_constraints.append(result)
        
        # Summarize findings
        type_summary = {}
        for c in all_constraints:
            data_type = c.get("inferred_type", "unknown")
            type_summary[data_type] = type_summary.get(data_type, 0) + 1
        
        return {
            "constraints": all_constraints,
            "total_count": len(all_constraints),
            "type_summary": type_summary,
            "analysis": f"Analyzed {len(all_constraints)} constraints with intelligent type inference",
            "type_inference_available": TYPE_INFERENCE_AVAILABLE
        }
    
    except Exception as e:
        return {"error": f"Failed to extract and infer constraints: {str(e)}"}


def _analyze_constraint_with_inference(
    constraint: Dict[str, Any],
    constraint_id: str,
    source: str
) -> Dict[str, Any]:
    """Internal: Analyze a single constraint with type inference"""
    
    left_op = constraint.get("leftOperand")
    operator = constraint.get("operator")
    right_op = constraint.get("rightOperand")
    rdfs_comment = constraint.get("rdfs:comment", "")
    
    if TYPE_INFERENCE_AVAILABLE:
        # Use intelligent type inference engine
        engine = get_type_inference_engine()
        type_info = engine.infer_type(right_op, left_op, rdfs_comment)
        rego_expr = engine.generate_rego_expression(left_op, operator, right_op, type_info)
        
        return {
            "id": constraint_id,
            "source": source,
            "leftOperand": left_op,
            "operator": operator,
            "rightOperand": right_op,
            "rdfs_comment": rdfs_comment,
            "inferred_type": type_info["inferred_type"],
            "rego_type": type_info["rego_type"],
            "rego_expression": rego_expr["rego_expression"],
            "explanation": rego_expr["explanation"],
            "recommended_functions": type_info["recommended_functions"],
            "requires_parsing": type_info["requires_parsing"]
        }
    else:
        # Fallback to basic type detection
        basic_type = _basic_type_detection(right_op)
        basic_pattern = _basic_rego_pattern(left_op, operator, right_op, basic_type)
        
        return {
            "id": constraint_id,
            "source": source,
            "leftOperand": left_op,
            "operator": operator,
            "rightOperand": right_op,
            "rdfs_comment": rdfs_comment,
            "inferred_type": basic_type,
            "rego_type": basic_type,
            "rego_expression": basic_pattern,
            "explanation": f"Basic pattern for {basic_type}",
            "recommended_functions": [],
            "requires_parsing": False
        }


def _basic_type_detection(value: Any) -> str:
    """Basic type detection fallback"""
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "number_int"
    elif isinstance(value, float):
        return "number_float"
    elif isinstance(value, list):
        return "set_string" if all(isinstance(v, str) for v in value) else "array"
    elif isinstance(value, str):
        if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
            return "datetime"
        return "string"
    return "unknown"


def _basic_rego_pattern(left_op: str, operator: str, right_op: Any, data_type: str) -> str:
    """Generate basic Rego pattern"""
    input_ref = f"input.{left_op}"
    
    if data_type == "datetime":
        return f'time.now_ns() < time.parse_rfc3339_ns("{right_op}")'
    elif data_type in ["number_int", "number_float"]:
        op_map = {"eq": "==", "neq": "!=", "lt": "<", "gt": ">", "lteq": "<=", "gteq": ">="}
        rego_op = op_map.get(operator, "==")
        return f"{input_ref} {rego_op} {right_op}"
    elif data_type == "set_string" or isinstance(right_op, list):
        values = ', '.join([f'"{v}"' if isinstance(v, str) else str(v) for v in right_op])
        return f'{input_ref} in {{{values}}}'
    else:
        return f'{input_ref} == "{right_op}"'


@tool
def infer_constraint_type(constraint_json: str) -> Dict[str, Any]:
    """
    Infer the data type of a single constraint.
    
    Args:
        constraint_json: JSON string of a single constraint
        
    Returns:
        Detailed type inference result
    """
    try:
        constraint = json.loads(constraint_json) if isinstance(constraint_json, str) else constraint_json
        
        left_op = constraint.get("leftOperand")
        right_op = constraint.get("rightOperand")
        rdfs_comment = constraint.get("rdfs:comment", "")
        
        if TYPE_INFERENCE_AVAILABLE:
            engine = get_type_inference_engine()
            type_info = engine.infer_type(right_op, left_op, rdfs_comment)
            
            return {
                "leftOperand": left_op,
                "rightOperand": right_op,
                "inferred_type": type_info["inferred_type"],
                "rego_type": type_info["rego_type"],
                "recommended_functions": type_info["recommended_functions"],
                "comparison_operators": type_info["comparison_operators"],
                "requires_parsing": type_info["requires_parsing"],
                "reasoning": f"Inferred as {type_info['inferred_type']} based on value analysis"
            }
        else:
            basic_type = _basic_type_detection(right_op)
            return {
                "leftOperand": left_op,
                "rightOperand": right_op,
                "inferred_type": basic_type,
                "rego_type": basic_type,
                "recommended_functions": [],
                "comparison_operators": ["eq", "neq"],
                "requires_parsing": False,
                "reasoning": f"Basic detection: {basic_type}"
            }
    
    except Exception as e:
        return {"error": f"Failed to infer type: {str(e)}"}


@tool
def generate_typed_rego_pattern(constraint_json: str) -> Dict[str, Any]:
    """
    Generate Rego pattern with appropriate data type handling.
    
    Args:
        constraint_json: JSON string of a constraint with actual values
        
    Returns:
        Rego pattern with correct type handling
    """
    try:
        constraint = json.loads(constraint_json) if isinstance(constraint_json, str) else constraint_json
        
        left_op = constraint.get("leftOperand")
        operator = constraint.get("operator")
        right_op = constraint.get("rightOperand")
        rdfs_comment = constraint.get("rdfs:comment", "")
        
        if TYPE_INFERENCE_AVAILABLE:
            engine = get_type_inference_engine()
            type_info = engine.infer_type(right_op, left_op, rdfs_comment)
            rego_expr = engine.generate_rego_expression(left_op, operator, right_op, type_info)
            
            return {
                "rego_pattern": rego_expr["rego_expression"],
                "comment": f"# {rego_expr['explanation']}",
                "inferred_type": type_info["inferred_type"],
                "actual_value": right_op,
                "type_reasoning": f"Detected {type_info['inferred_type']} - using {rego_expr['type']} pattern"
            }
        else:
            # Fallback
            basic_type = _basic_type_detection(right_op)
            basic_pattern = _basic_rego_pattern(left_op, operator, right_op, basic_type)
            
            return {
                "rego_pattern": basic_pattern,
                "comment": f"# Basic pattern for {basic_type}",
                "inferred_type": basic_type,
                "actual_value": right_op,
                "type_reasoning": f"Basic detection: {basic_type}"
            }
    
    except Exception as e:
        return {"error": f"Failed to generate pattern: {str(e)}"}


@tool
def generate_complete_typed_rule(rule_json: str) -> Dict[str, Any]:
    """
    Generate a complete Rego rule with proper type handling for all constraints.
    
    Args:
        rule_json: JSON string with rule type, action, and constraints
        
    Returns:
        Complete Rego rule with typed constraints
    """
    try:
        rule = json.loads(rule_json) if isinstance(rule_json, str) else rule_json
        
        rule_type = rule.get("type", "allow")
        action = rule.get("action", "")
        constraints = rule.get("constraints", [])
        
        lines = []
        lines.append(f"# Rule: {rule_type} {action}")
        
        constraint_patterns = []
        for constraint in constraints:
            result = generate_typed_rego_pattern(json.dumps(constraint))
            if "error" not in result:
                constraint_patterns.append({
                    "pattern": result["rego_pattern"],
                    "comment": result["comment"],
                    "type": result["inferred_type"]
                })
        
        # Add comments
        for cp in constraint_patterns:
            lines.append(cp["comment"])
        
        # Add rule definition
        rule_keyword = "allow" if rule_type == "allow" else "deny"
        lines.append(f"{rule_keyword} if {{")
        
        # Add action check
        if action:
            action_value = action.split("/")[-1] if "/" in action else action
            lines.append(f'    input.action == "{action_value}"')
        
        # Add constraint patterns
        for cp in constraint_patterns:
            lines.append(f"    {cp['pattern']}")
        
        lines.append("}")
        
        return {
            "rego_code": "\n".join(lines),
            "constraint_count": len(constraint_patterns),
            "types_used": [cp["type"] for cp in constraint_patterns],
            "uses_intelligent_typing": TYPE_INFERENCE_AVAILABLE
        }
    
    except Exception as e:
        return {"error": f"Failed to generate rule: {str(e)}"}


@tool
def generate_type_inference_report(odrl_json: str) -> Dict[str, Any]:
    """
    Generate a comprehensive type inference report for all constraints.
    
    Args:
        odrl_json: JSON string of the ODRL policy
        
    Returns:
        Detailed report of type inference for all constraints
    """
    try:
        result = extract_and_infer_constraints(odrl_json)
        
        if "error" in result:
            return result
        
        constraints = result.get("constraints", [])
        
        # Group by type
        by_type = {}
        for c in constraints:
            t = c.get("inferred_type", "unknown")
            if t not in by_type:
                by_type[t] = []
            by_type[t].append({
                "leftOperand": c.get("leftOperand"),
                "rightOperand": c.get("rightOperand"),
                "rego_expression": c.get("rego_expression")
            })
        
        # Create report
        report_lines = [
            "# Type Inference Report",
            f"# Total Constraints: {len(constraints)}",
            f"# Type Inference Engine: {'Available' if TYPE_INFERENCE_AVAILABLE else 'Not Available (using fallback)'}",
            "",
            "## Types Detected:",
        ]
        
        for dtype, instances in by_type.items():
            report_lines.append(f"\n### {dtype.upper()} ({len(instances)} instances)")
            for inst in instances[:5]:  # Show first 5
                report_lines.append(f"  - {inst['leftOperand']}: {inst['rightOperand']}")
                report_lines.append(f"    Rego: {inst['rego_expression']}")
            if len(instances) > 5:
                report_lines.append(f"  ... and {len(instances) - 5} more")
        
        return {
            "report": "\n".join(report_lines),
            "types_found": list(by_type.keys()),
            "type_counts": {k: len(v) for k, v in by_type.items()},
            "type_inference_available": TYPE_INFERENCE_AVAILABLE
        }
    
    except Exception as e:
        return {"error": f"Failed to generate report: {str(e)}"}


# ============================================================================
# Rego Validation Tools (ORIGINAL FUNCTIONALITY)
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
                # Skip default declarations, package, import
                if not any(stripped.startswith(x) for x in ['default ', 'package ', 'import ']):
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
    "fix_missing_if",
    # New type inference tools
    "extract_and_infer_constraints",
    "infer_constraint_type",
    "generate_typed_rego_pattern",
    "generate_complete_typed_rule",
    "generate_type_inference_report"
]