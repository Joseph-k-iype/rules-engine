"""
Enhanced ReAct Tools for Coverage-Based ODRL to Rego Conversion
Includes jurisdiction extraction, AST validation, and regex pattern tools
"""
import json
import re
from typing import Dict, Any, List, Optional
from langchain.tools import tool


# ============================================================================
# Coverage/Jurisdiction Extraction Tools (NEW)
# ============================================================================

@tool
def extract_coverage_and_jurisdictions(odrl_json: str) -> Dict[str, Any]:
    """
    Extract coverage (countries/jurisdictions) from ODRL policy.
    Groups rules by jurisdiction + action combinations.
    
    Args:
        odrl_json: JSON string of the ODRL policy
        
    Returns:
        Coverage groups, jurisdiction patterns, and hierarchy
    """
    try:
        policy = json.loads(odrl_json) if isinstance(odrl_json, str) else odrl_json
        
        coverage_groups = []
        jurisdiction_map = {}
        action_jurisdiction_map = {}
        
        # Extract from permissions
        for perm_idx, perm in enumerate(policy.get("permission", [])):
            coverage_info = _extract_coverage_from_rule(perm, "permission", perm_idx)
            if coverage_info:
                coverage_groups.append(coverage_info)
                action = perm.get("action", "unknown")
                if action not in action_jurisdiction_map:
                    action_jurisdiction_map[action] = []
                action_jurisdiction_map[action].extend(coverage_info["jurisdictions"])
        
        # Extract from prohibitions
        for prohib_idx, prohib in enumerate(policy.get("prohibition", [])):
            coverage_info = _extract_coverage_from_rule(prohib, "prohibition", prohib_idx)
            if coverage_info:
                coverage_groups.append(coverage_info)
                action = prohib.get("action", "unknown")
                if action not in action_jurisdiction_map:
                    action_jurisdiction_map[action] = []
                action_jurisdiction_map[action].extend(coverage_info["jurisdictions"])
        
        # Build jurisdiction hierarchy
        hierarchy = _build_jurisdiction_hierarchy(coverage_groups)
        
        # Generate regex patterns for jurisdiction matching
        regex_patterns = _generate_jurisdiction_regex_patterns(coverage_groups)
        
        return {
            "coverage_groups": coverage_groups,
            "action_jurisdiction_map": action_jurisdiction_map,
            "jurisdiction_hierarchy": hierarchy,
            "regex_patterns": regex_patterns,
            "total_jurisdictions": len(set(sum([g["jurisdictions"] for g in coverage_groups], [])))
        }
    
    except Exception as e:
        return {"error": f"Failed to extract coverage: {str(e)}"}


@tool
def extract_custom_original_data(odrl_json: str) -> Dict[str, Any]:
    """
    Extract and map custom:originalData identifiers to rules.
    These IDs are used to traverse the JSON structure.
    
    Args:
        odrl_json: JSON string of the ODRL policy
        
    Returns:
        Mapping of original data IDs to rule details
    """
    try:
        policy = json.loads(odrl_json) if isinstance(odrl_json, str) else odrl_json
        
        original_data_map = {}
        
        def extract_original_data(obj, path=""):
            """Recursively extract custom:originalData"""
            if isinstance(obj, dict):
                if "custom:originalData" in obj:
                    original_id = obj["custom:originalData"].get("id")
                    if original_id:
                        original_data_map[original_id] = {
                            "data": obj,
                            "path": path,
                            "type": obj.get("@type", "unknown")
                        }
                
                for key, value in obj.items():
                    extract_original_data(value, f"{path}.{key}" if path else key)
            
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    extract_original_data(item, f"{path}[{idx}]")
        
        extract_original_data(policy)
        
        return {
            "original_data_map": original_data_map,
            "total_tracked_rules": len(original_data_map),
            "traversal_guide": "Use IDs to reference specific rules across transformations"
        }
    
    except Exception as e:
        return {"error": f"Failed to extract original data: {str(e)}"}


@tool
def generate_regex_patterns_for_jurisdictions(jurisdictions: str) -> Dict[str, str]:
    """
    Generate regex patterns for matching jurisdictions and their hierarchies.
    Supports partial matching and hierarchical jurisdiction structures.
    
    Args:
        jurisdictions: JSON string list of jurisdictions
        
    Returns:
        Regex patterns for each jurisdiction and common patterns
    """
    try:
        jurisdiction_list = json.loads(jurisdictions) if isinstance(jurisdictions, str) else jurisdictions
        
        patterns = {}
        
        for jurisdiction in jurisdiction_list:
            # Exact match pattern
            patterns[f"{jurisdiction}_exact"] = f"^{re.escape(jurisdiction)}$"
            
            # Prefix match for hierarchical (e.g., "US" matches "US:CA", "US:NY")
            patterns[f"{jurisdiction}_prefix"] = f"^{re.escape(jurisdiction)}:"
            
            # Contains match (flexible)
            patterns[f"{jurisdiction}_contains"] = f".*{re.escape(jurisdiction)}.*"
            
            # Case-insensitive match
            patterns[f"{jurisdiction}_case_insensitive"] = f"(?i)^{re.escape(jurisdiction)}$"
        
        # Common patterns
        patterns["any_us_state"] = r"^US:[A-Z]{2}$"
        patterns["any_eu_country"] = r"^EU:[A-Z]{2}$"
        patterns["any_country_code"] = r"^[A-Z]{2}$"
        patterns["hierarchical"] = r"^[A-Z]{2}(:[A-Z0-9_]+)*$"
        
        return {
            "patterns": patterns,
            "rego_usage": {
                "exact": 'regex.match(pattern, input.jurisdiction)',
                "find_all": 'regex.find_all_string_submatch_n(pattern, input.jurisdiction, 1)',
                "partial": 'regex.find_all_string_submatch_n(pattern, input.jurisdiction, -1)'
            }
        }
    
    except Exception as e:
        return {"error": f"Failed to generate regex patterns: {str(e)}"}


# ============================================================================
# AST Generation and Validation Tools (NEW)
# ============================================================================

@tool
def generate_ast_from_policy(odrl_json: str) -> Dict[str, Any]:
    """
    Generate Abstract Syntax Tree (AST) from ODRL policy for logical validation.
    The AST represents the logical structure of permissions, prohibitions, and constraints.
    
    Args:
        odrl_json: JSON string of the ODRL policy
        
    Returns:
        AST representation with nodes for rules, constraints, and logical operations
    """
    try:
        policy = json.loads(odrl_json) if isinstance(odrl_json, str) else odrl_json
        
        ast_root = {
            "node_type": "policy",
            "node_id": "root",
            "value": policy.get("@id", "unknown"),
            "children": [],
            "parent_id": None,
            "metadata": {
                "policy_type": policy.get("@type", "unknown")
            }
        }
        
        # Process permissions
        permission_nodes = []
        for perm_idx, perm in enumerate(policy.get("permission", [])):
            perm_node = _create_rule_ast_node(perm, "permission", perm_idx, "root")
            permission_nodes.append(perm_node)
        
        # Process prohibitions
        prohibition_nodes = []
        for prohib_idx, prohib in enumerate(policy.get("prohibition", [])):
            prohib_node = _create_rule_ast_node(prohib, "prohibition", prohib_idx, "root")
            prohibition_nodes.append(prohib_node)
        
        ast_root["children"] = permission_nodes + prohibition_nodes
        
        # Calculate AST statistics
        ast_stats = _calculate_ast_statistics(ast_root)
        
        return {
            "ast_tree": ast_root,
            "statistics": ast_stats,
            "analysis": "AST generated successfully for logical validation"
        }
    
    except Exception as e:
        return {"error": f"Failed to generate AST: {str(e)}"}


@tool
def validate_ast_logic(ast_json: str) -> Dict[str, Any]:
    """
    Validate logical correctness of AST.
    Checks for contradictions, missing cases, and logical inconsistencies.
    
    Args:
        ast_json: JSON string of the AST
        
    Returns:
        Validation results with logic correctness score and issues
    """
    try:
        ast = json.loads(ast_json) if isinstance(ast_json, str) else ast_json
        
        issues = []
        traversal_log = []
        
        # Traverse AST and validate
        def traverse_and_validate(node, path=""):
            current_path = f"{path}/{node['node_id']}"
            traversal_log.append(f"Visiting: {current_path} (type: {node['node_type']})")
            
            # Check for logical issues
            if node['node_type'] == 'constraint':
                issue = _validate_constraint_node(node)
                if issue:
                    issues.append(issue)
            
            elif node['node_type'] in ['permission', 'prohibition']:
                issue = _validate_rule_node(node)
                if issue:
                    issues.append(issue)
            
            # Recursively traverse children
            for child in node.get('children', []):
                traverse_and_validate(child, current_path)
        
        traverse_and_validate(ast)
        
        # Check for contradictions between permissions and prohibitions
        contradiction_issues = _check_permission_prohibition_contradictions(ast)
        issues.extend(contradiction_issues)
        
        # Calculate logic correctness score
        total_nodes = len(traversal_log)
        issue_severity_weights = {"critical": 1.0, "warning": 0.5, "info": 0.1}
        penalty = sum(issue_severity_weights.get(issue.get("severity", "warning"), 0.5) for issue in issues)
        correctness_score = max(0.0, 1.0 - (penalty / max(total_nodes, 1)))
        
        return {
            "is_valid": len([i for i in issues if i.get("severity") == "critical"]) == 0,
            "correctness_score": round(correctness_score, 3),
            "issues": issues,
            "traversal_log": traversal_log,
            "total_nodes_validated": total_nodes
        }
    
    except Exception as e:
        return {"error": f"Failed to validate AST: {str(e)}"}


@tool
def traverse_ast_by_coverage(ast_json: str, jurisdiction: str) -> Dict[str, Any]:
    """
    Traverse AST and extract rules applicable to specific jurisdiction.
    
    Args:
        ast_json: JSON string of the AST
        jurisdiction: Target jurisdiction to filter rules
        
    Returns:
        Rules applicable to the specified jurisdiction
    """
    try:
        ast = json.loads(ast_json) if isinstance(ast_json, str) else ast_json
        
        applicable_rules = []
        
        def traverse(node):
            if node['node_type'] in ['permission', 'prohibition']:
                # Check if rule applies to jurisdiction
                coverage = node.get('metadata', {}).get('coverage', [])
                if _matches_jurisdiction(jurisdiction, coverage):
                    applicable_rules.append({
                        "rule_type": node['node_type'],
                        "rule_id": node['node_id'],
                        "action": node.get('value'),
                        "coverage": coverage
                    })
            
            for child in node.get('children', []):
                traverse(child)
        
        traverse(ast)
        
        return {
            "jurisdiction": jurisdiction,
            "applicable_rules": applicable_rules,
            "rule_count": len(applicable_rules)
        }
    
    except Exception as e:
        return {"error": f"Failed to traverse AST: {str(e)}"}


# ============================================================================
# Enhanced Type Inference Tools
# ============================================================================

@tool
def extract_and_infer_constraints_with_coverage(odrl_json: str) -> Dict[str, Any]:
    """
    Extract constraints with type inference AND coverage information.
    Combines type analysis with jurisdiction-based grouping.
    
    Args:
        odrl_json: JSON string of the ODRL policy
        
    Returns:
        Constraints with inferred types and coverage information
    """
    try:
        policy = json.loads(odrl_json) if isinstance(odrl_json, str) else odrl_json
        
        all_constraints = []
        
        # Process permissions with coverage
        for perm_idx, perm in enumerate(policy.get("permission", [])):
            coverage = _extract_coverage_from_rule(perm, "permission", perm_idx)
            jurisdictions = coverage["jurisdictions"] if coverage else []
            
            for const_idx, constraint in enumerate(perm.get("constraint", [])):
                result = _analyze_constraint_with_inference(
                    constraint,
                    f"permission_{perm_idx}_constraint_{const_idx}",
                    "permission"
                )
                result["coverage"] = jurisdictions
                result["action"] = perm.get("action", "unknown")
                all_constraints.append(result)
        
        # Process prohibitions with coverage
        for prohib_idx, prohib in enumerate(policy.get("prohibition", [])):
            coverage = _extract_coverage_from_rule(prohib, "prohibition", prohib_idx)
            jurisdictions = coverage["jurisdictions"] if coverage else []
            
            for const_idx, constraint in enumerate(prohib.get("constraint", [])):
                result = _analyze_constraint_with_inference(
                    constraint,
                    f"prohibition_{prohib_idx}_constraint_{const_idx}",
                    "prohibition"
                )
                result["coverage"] = jurisdictions
                result["action"] = prohib.get("action", "unknown")
                all_constraints.append(result)
        
        # Group by coverage + action
        grouped = {}
        for constraint in all_constraints:
            for jurisdiction in constraint.get("coverage", ["GLOBAL"]):
                action = constraint.get("action", "unknown")
                key = f"{jurisdiction}:{action}"
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(constraint)
        
        return {
            "constraints": all_constraints,
            "grouped_by_coverage": grouped,
            "coverage_action_keys": list(grouped.keys()),
            "total_count": len(all_constraints)
        }
    
    except Exception as e:
        return {"error": f"Failed to extract constraints with coverage: {str(e)}"}


@tool
def generate_coverage_based_rego_rule(coverage: str, action: str, constraints_json: str) -> Dict[str, Any]:
    """
    Generate a complete Rego rule based on coverage (jurisdiction) and action.
    Uses regex patterns for jurisdiction matching.
    
    Args:
        coverage: Jurisdiction or jurisdiction pattern (e.g., "US", "US:CA", "EU:*")
        action: Action name (e.g., "read", "process", "share")
        constraints_json: JSON string of constraints for this coverage+action combination
        
    Returns:
        Complete Rego rule with coverage-based logic
    """
    try:
        constraints = json.loads(constraints_json) if isinstance(constraints_json, str) else constraints_json
        
        # Generate rule name
        safe_coverage = coverage.replace(":", "_").replace("*", "all")
        safe_action = action.replace(":", "_")
        rule_name = f"allow_{safe_action}_{safe_coverage}"
        
        # Generate jurisdiction matching logic
        jurisdiction_check = _generate_jurisdiction_check(coverage)
        
        # Generate constraint conditions
        constraint_conditions = []
        for constraint in constraints:
            condition = _generate_constraint_condition(constraint)
            if condition:
                constraint_conditions.append(condition)
        
        # Build complete rule
        rule_parts = [
            f"# Rule for {action} in {coverage}",
            f"{rule_name} if {{",
            f"    # Jurisdiction check",
            f"    {jurisdiction_check}",
            ""
        ]
        
        if constraint_conditions:
            rule_parts.append("    # Constraints")
            for condition in constraint_conditions:
                rule_parts.append(f"    {condition}")
        
        rule_parts.append("}")
        
        rule_code = "\n".join(rule_parts)
        
        return {
            "rule_name": rule_name,
            "rule_code": rule_code,
            "coverage": coverage,
            "action": action,
            "constraint_count": len(constraints)
        }
    
    except Exception as e:
        return {"error": f"Failed to generate coverage-based rule: {str(e)}"}


# ============================================================================
# Helper Functions
# ============================================================================

def _extract_coverage_from_rule(rule: Dict[str, Any], rule_type: str, index: int) -> Optional[Dict[str, Any]]:
    """Extract coverage/jurisdiction information from a rule"""
    jurisdictions = []
    
    # Look for coverage in constraints
    for constraint in rule.get("constraint", []):
        left_op = constraint.get("leftOperand", "")
        right_op = constraint.get("rightOperand")
        
        # Check for jurisdiction/coverage/spatial constraints
        if any(keyword in left_op.lower() for keyword in ["jurisdiction", "coverage", "spatial", "region", "country"]):
            if isinstance(right_op, list):
                jurisdictions.extend(right_op)
            elif isinstance(right_op, str):
                jurisdictions.append(right_op)
    
    # Look for custom:originalData
    original_data_id = rule.get("custom:originalData", {}).get("id") if "custom:originalData" in rule else None
    
    # Look for spatial or region properties at rule level
    for key in ["spatial", "region", "jurisdiction", "coverage"]:
        if key in rule:
            value = rule[key]
            if isinstance(value, list):
                jurisdictions.extend(value)
            elif isinstance(value, str):
                jurisdictions.append(value)
    
    if not jurisdictions:
        jurisdictions = ["GLOBAL"]  # Default if no jurisdiction specified
    
    return {
        "rule_type": rule_type,
        "rule_index": index,
        "jurisdictions": list(set(jurisdictions)),  # Remove duplicates
        "action": rule.get("action", "unknown"),
        "original_data_id": original_data_id
    }


def _build_jurisdiction_hierarchy(coverage_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build hierarchical structure of jurisdictions"""
    hierarchy = {}
    
    for group in coverage_groups:
        for jurisdiction in group["jurisdictions"]:
            parts = jurisdiction.split(":")
            
            current_level = hierarchy
            for part in parts:
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
    
    return hierarchy


def _generate_jurisdiction_regex_patterns(coverage_groups: List[Dict[str, Any]]) -> Dict[str, str]:
    """Generate regex patterns for jurisdiction matching"""
    patterns = {}
    all_jurisdictions = set()
    
    for group in coverage_groups:
        all_jurisdictions.update(group["jurisdictions"])
    
    for jurisdiction in all_jurisdictions:
        patterns[jurisdiction] = f"^{re.escape(jurisdiction)}$"
        patterns[f"{jurisdiction}_hierarchy"] = f"^{re.escape(jurisdiction)}:.*$"
    
    return patterns


def _create_rule_ast_node(rule: Dict[str, Any], rule_type: str, index: int, parent_id: str) -> Dict[str, Any]:
    """Create AST node for a rule"""
    node_id = f"{rule_type}_{index}"
    
    node = {
        "node_type": rule_type,
        "node_id": node_id,
        "value": rule.get("action", "unknown"),
        "children": [],
        "parent_id": parent_id,
        "metadata": {
            "rule_index": index,
            "target": rule.get("target"),
            "assignee": rule.get("assignee"),
            "coverage": _extract_coverage_from_rule(rule, rule_type, index)["jurisdictions"]
        }
    }
    
    # Add constraint children
    for const_idx, constraint in enumerate(rule.get("constraint", [])):
        const_node = {
            "node_type": "constraint",
            "node_id": f"{node_id}_constraint_{const_idx}",
            "value": constraint,
            "children": [],
            "parent_id": node_id,
            "metadata": {
                "leftOperand": constraint.get("leftOperand"),
                "operator": constraint.get("operator"),
                "rightOperand": constraint.get("rightOperand")
            }
        }
        node["children"].append(const_node)
    
    return node


def _calculate_ast_statistics(ast_root: Dict[str, Any]) -> Dict[str, int]:
    """Calculate statistics about the AST"""
    stats = {
        "total_nodes": 0,
        "permission_nodes": 0,
        "prohibition_nodes": 0,
        "constraint_nodes": 0,
        "max_depth": 0
    }
    
    def traverse(node, depth=0):
        stats["total_nodes"] += 1
        stats["max_depth"] = max(stats["max_depth"], depth)
        
        if node["node_type"] == "permission":
            stats["permission_nodes"] += 1
        elif node["node_type"] == "prohibition":
            stats["prohibition_nodes"] += 1
        elif node["node_type"] == "constraint":
            stats["constraint_nodes"] += 1
        
        for child in node.get("children", []):
            traverse(child, depth + 1)
    
    traverse(ast_root)
    return stats


def _validate_constraint_node(node: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Validate a constraint node in the AST"""
    metadata = node.get("metadata", {})
    left_op = metadata.get("leftOperand")
    operator = metadata.get("operator")
    right_op = metadata.get("rightOperand")
    
    if not left_op or not operator:
        return {
            "severity": "critical",
            "node_id": node["node_id"],
            "message": f"Constraint missing leftOperand or operator"
        }
    
    if right_op is None:
        return {
            "severity": "warning",
            "node_id": node["node_id"],
            "message": f"Constraint has no rightOperand value"
        }
    
    return None


def _validate_rule_node(node: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Validate a rule node in the AST"""
    if not node.get("value") or node["value"] == "unknown":
        return {
            "severity": "critical",
            "node_id": node["node_id"],
            "message": f"Rule has no action specified"
        }
    
    if not node.get("children"):
        return {
            "severity": "info",
            "node_id": node["node_id"],
            "message": f"Rule has no constraints (unconditional)"
        }
    
    return None


def _check_permission_prohibition_contradictions(ast: Dict[str, Any]) -> List[Dict[str, str]]:
    """Check for contradictions between permissions and prohibitions"""
    issues = []
    
    permissions = {}
    prohibitions = {}
    
    def collect_rules(node):
        if node["node_type"] == "permission":
            action = node["value"]
            coverage = tuple(sorted(node["metadata"].get("coverage", [])))
            key = (action, coverage)
            permissions[key] = node
        elif node["node_type"] == "prohibition":
            action = node["value"]
            coverage = tuple(sorted(node["metadata"].get("coverage", [])))
            key = (action, coverage)
            prohibitions[key] = node
        
        for child in node.get("children", []):
            collect_rules(child)
    
    collect_rules(ast)
    
    # Check for same action+coverage in both permissions and prohibitions
    for key in permissions:
        if key in prohibitions:
            action, coverage = key
            issues.append({
                "severity": "critical",
                "node_id": f"{permissions[key]['node_id']}_vs_{prohibitions[key]['node_id']}",
                "message": f"Contradiction: Action '{action}' both permitted and prohibited for coverage {coverage}"
            })
    
    return issues


def _matches_jurisdiction(target: str, coverage_list: List[str]) -> bool:
    """Check if target jurisdiction matches any in coverage list"""
    for coverage in coverage_list:
        if coverage == "GLOBAL":
            return True
        if target == coverage:
            return True
        # Check hierarchical match (e.g., "US:CA" matches "US")
        if target.startswith(coverage + ":"):
            return True
        if coverage.startswith(target + ":"):
            return True
    return False


def _analyze_constraint_with_inference(
    constraint: Dict[str, Any],
    constraint_id: str,
    source: str
) -> Dict[str, Any]:
    """Analyze constraint with type inference"""
    left_op = constraint.get("leftOperand")
    operator = constraint.get("operator")
    right_op = constraint.get("rightOperand")
    rdfs_comment = constraint.get("rdfs:comment", "")
    
    # Simple type inference
    inferred_type = "string"
    if isinstance(right_op, bool):
        inferred_type = "boolean"
    elif isinstance(right_op, int):
        inferred_type = "integer"
    elif isinstance(right_op, float):
        inferred_type = "float"
    elif isinstance(right_op, list):
        inferred_type = "array"
    elif isinstance(right_op, str):
        if re.match(r'^\d{4}-\d{2}-\d{2}', right_op):
            inferred_type = "datetime"
        elif re.match(r'^P\d+[YMWD]', right_op):
            inferred_type = "duration"
    
    return {
        "id": constraint_id,
        "source": source,
        "leftOperand": left_op,
        "operator": operator,
        "rightOperand": right_op,
        "rdfs_comment": rdfs_comment,
        "inferred_type": inferred_type
    }


def _generate_jurisdiction_check(coverage: str) -> str:
    """Generate Rego code for jurisdiction checking"""
    if coverage == "GLOBAL":
        return "true  # Global rule applies to all jurisdictions"
    
    if "*" in coverage:
        # Wildcard pattern
        pattern = coverage.replace("*", ".*")
        return f'regex.match("{pattern}", input.jurisdiction)'
    
    if ":" in coverage:
        # Hierarchical jurisdiction - check exact or child jurisdictions
        return f'(input.jurisdiction == "{coverage}" || startswith(input.jurisdiction, "{coverage}:"))'
    
    # Exact match
    return f'input.jurisdiction == "{coverage}"'


def _generate_constraint_condition(constraint: Dict[str, Any]) -> Optional[str]:
    """Generate Rego condition from constraint"""
    left_op = constraint.get("leftOperand", "")
    operator = constraint.get("operator", "")
    right_op = constraint.get("rightOperand")
    inferred_type = constraint.get("inferred_type", "string")
    
    if not left_op or not operator:
        return None
    
    # Map ODRL operators to Rego
    operator_map = {
        "eq": "==",
        "neq": "!=",
        "lt": "<",
        "lteq": "<=",
        "gt": ">",
        "gteq": ">=",
        "isAnyOf": "in",
        "isNoneOf": "not in"
    }
    
    rego_op = operator_map.get(operator, "==")
    input_ref = f"input.{left_op}" if not left_op.startswith("input.") else left_op
    
    # Format right operand based on type
    if inferred_type == "datetime":
        return f'time.now_ns() {rego_op} time.parse_rfc3339_ns("{right_op}")'
    elif inferred_type in ["integer", "float"]:
        return f'{input_ref} {rego_op} {right_op}'
    elif inferred_type == "boolean":
        return f'{input_ref} {rego_op} {str(right_op).lower()}'
    elif inferred_type == "array":
        values = ', '.join([f'"{v}"' if isinstance(v, str) else str(v) for v in right_op])
        return f'{input_ref} {rego_op} {{{values}}}'
    else:
        return f'{input_ref} {rego_op} "{right_op}"'


# Re-export original tools for backward compatibility
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