"""
ODRL Policy Validators

This module provides validation classes for ODRL policies to ensure
logical consistency and prevent duplicate constraints between permissions
and prohibitions.

Created: 2025
Author: Auto-generated for ODRL Policy System
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConstraintDuplication:
    """Represents a detected constraint duplication."""
    type: str  # 'exact_duplicate' or 'logical_inverse'
    constraint_key: str
    description: str
    permission: Dict[str, Any]
    prohibition: Dict[str, Any]
    suggestion: str


@dataclass
class ValidationResult:
    """Results from policy validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    duplications: List[ConstraintDuplication]
    suggestions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'valid': self.valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'duplications': [
                {
                    'type': dup.type,
                    'constraint_key': dup.constraint_key,
                    'description': dup.description,
                    'suggestion': dup.suggestion
                }
                for dup in self.duplications
            ],
            'suggestions': self.suggestions
        }


class ODRLLogicalValidator:
    """
    Validates ODRL components for logical consistency and detects duplications
    between permissions and prohibitions.
    
    This validator ensures that:
    1. Constraints don't appear in both permissions and prohibitions
    2. Logical inverse constraints are not duplicated
    3. No internal contradictions exist within rules
    4. Operators are semantically appropriate
    """
    
    # Operator pairs that are logical inverses
    INVERSE_OPERATORS = {
        'eq': 'neq',
        'neq': 'eq',
        'isAnyOf': 'isNoneOf',
        'isNoneOf': 'isAnyOf',
        'isAllOf': 'isNoneOf',
        'gt': 'lteq',
        'lt': 'gteq',
        'gteq': 'lt',
        'lteq': 'gt',
        'isPartOf': 'isNotPartOf',
        'isNotPartOf': 'isPartOf'
    }
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize the validator.
        
        Args:
            strict_mode: If True, treat warnings as errors
        """
        self.strict_mode = strict_mode
    
    def validate_components(self, components) -> ValidationResult:
        """
        Validate ODRL components for logical consistency.
        
        Args:
            components: ODRLComponents object to validate
            
        Returns:
            ValidationResult with validation results including errors and warnings
        """
        errors = []
        warnings = []
        duplications = []
        suggestions = []
        
        # Convert components to dict format if needed
        permissions = self._extract_rules(components, 'permissions')
        prohibitions = self._extract_rules(components, 'prohibitions')
        
        # Check for constraint duplications between permissions and prohibitions
        found_duplications = self._find_constraint_duplications(
            permissions,
            prohibitions
        )
        
        if found_duplications:
            duplications.extend(found_duplications)
            
            for dup in found_duplications:
                error_msg = f"Logical duplication detected: {dup.description}"
                errors.append(error_msg)
                suggestions.append(f"Suggestion for '{dup.constraint_key}': {dup.suggestion}")
                
                logger.warning(f"  ❌ {error_msg}")
        
        # Check for contradictory constraints within same rule
        perm_conflicts = self._check_internal_contradictions(permissions, 'permission')
        prohib_conflicts = self._check_internal_contradictions(prohibitions, 'prohibition')
        
        internal_conflicts = perm_conflicts + prohib_conflicts
        if internal_conflicts:
            errors.extend(internal_conflicts)
            for conflict in internal_conflicts:
                logger.warning(f"  ❌ Internal contradiction: {conflict}")
        
        # Check for empty constraints
        empty_warnings = self._check_empty_constraints(permissions, prohibitions)
        if empty_warnings:
            warnings.extend(empty_warnings)
        
        # Determine if valid
        is_valid = len(errors) == 0
        if self.strict_mode and warnings:
            is_valid = False
        
        return ValidationResult(
            valid=is_valid,
            errors=errors,
            warnings=warnings,
            duplications=duplications,
            suggestions=suggestions
        )
    
    def _extract_rules(self, components, rule_type: str) -> List[Dict]:
        """Extract rules from components object."""
        if hasattr(components, rule_type):
            rules = getattr(components, rule_type)
            if isinstance(rules, list):
                return rules
            return []
        return []
    
    def _find_constraint_duplications(
        self,
        permissions: List[Dict],
        prohibitions: List[Dict]
    ) -> List[ConstraintDuplication]:
        """
        Find constraints that appear in both permissions and prohibitions,
        especially those that are logical inverses of each other.
        """
        duplications = []
        
        # Extract constraints from permissions with context
        perm_constraints = self._extract_constraints_with_context(permissions, 'permission')
        
        # Extract constraints from prohibitions with context
        prohib_constraints = self._extract_constraints_with_context(prohibitions, 'prohibition')
        
        # Check for exact duplicates (same leftOperand, operator, rightOperand)
        for perm_constraint in perm_constraints:
            for prohib_constraint in prohib_constraints:
                if self._are_constraints_identical(perm_constraint, prohib_constraint):
                    duplication = ConstraintDuplication(
                        type='exact_duplicate',
                        constraint_key=perm_constraint['leftOperand'],
                        description=(
                            f"Constraint '{perm_constraint['leftOperand']}' appears identically "
                            f"in both permission and prohibition with operator '{perm_constraint['operator']}' "
                            f"and value '{perm_constraint['rightOperand']}'"
                        ),
                        permission=perm_constraint,
                        prohibition=prohib_constraint,
                        suggestion=(
                            "Remove from prohibition - this constraint should only appear once. "
                            "Keep in permission as it defines when action is allowed."
                        )
                    )
                    duplications.append(duplication)
        
        # Check for logical inverses (same leftOperand, inverse operators)
        for perm_constraint in perm_constraints:
            for prohib_constraint in prohib_constraints:
                if self._are_constraints_logical_inverses(perm_constraint, prohib_constraint):
                    duplication = ConstraintDuplication(
                        type='logical_inverse',
                        constraint_key=perm_constraint['leftOperand'],
                        description=(
                            f"Constraint '{perm_constraint['leftOperand']}' appears as logical inverse "
                            f"in permission (operator: {perm_constraint['operator']}) and "
                            f"prohibition (operator: {prohib_constraint['operator']}) "
                            f"with values '{perm_constraint['rightOperand']}' and '{prohib_constraint['rightOperand']}'"
                        ),
                        permission=perm_constraint,
                        prohibition=prohib_constraint,
                        suggestion=(
                            f"These constraints are logically equivalent. Keep only the permission with "
                            f"operator '{perm_constraint['operator']}' to define when action is allowed. "
                            f"Remove the prohibition as it's redundant."
                        )
                    )
                    duplications.append(duplication)
        
        return duplications
    
    def _extract_constraints_with_context(
        self,
        rules: List[Dict],
        rule_type: str
    ) -> List[Dict]:
        """Extract all constraints from rules with context about their parent rule."""
        constraints = []
        
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                continue
                
            rule_constraints = rule.get('constraints', [])
            if not isinstance(rule_constraints, list):
                rule_constraints = [rule_constraints] if rule_constraints else []
            
            for constraint in rule_constraints:
                if not isinstance(constraint, dict):
                    continue
                    
                constraint_with_context = constraint.copy()
                constraint_with_context['rule_type'] = rule_type
                constraint_with_context['rule_index'] = i
                constraint_with_context['rule_action'] = rule.get('action', '')
                constraint_with_context['rule_description'] = rule.get('description', '')
                constraints.append(constraint_with_context)
        
        return constraints
    
    def _are_constraints_identical(self, c1: Dict, c2: Dict) -> bool:
        """Check if two constraints are exactly identical."""
        return (
            c1.get('leftOperand') == c2.get('leftOperand') and
            c1.get('operator') == c2.get('operator') and
            self._normalize_value(c1.get('rightOperand')) == 
            self._normalize_value(c2.get('rightOperand'))
        )
    
    def _are_constraints_logical_inverses(self, c1: Dict, c2: Dict) -> bool:
        """
        Check if two constraints are logical inverses of each other.
        E.g., (requestor eq X) and (requestor neq X)
        """
        if c1.get('leftOperand') != c2.get('leftOperand'):
            return False
        
        op1 = c1.get('operator')
        op2 = c2.get('operator')
        
        # Check if operators are inverses
        if self.INVERSE_OPERATORS.get(op1) != op2:
            return False
        
        # Check if right operands are the same (or inverse for sets)
        val1 = self._normalize_value(c1.get('rightOperand'))
        val2 = self._normalize_value(c2.get('rightOperand'))
        
        return val1 == val2
    
    def _normalize_value(self, value: Any) -> str:
        """Normalize constraint values for comparison."""
        if value is None:
            return ''
        if isinstance(value, list):
            return str(sorted([str(v).lower().strip() for v in value]))
        return str(value).lower().strip()
    
    def _check_internal_contradictions(
        self, 
        rules: List[Dict],
        rule_type: str
    ) -> List[str]:
        """
        Check for contradictions within the same rule's constraints.
        E.g., purpose eq X AND purpose eq Y (where X != Y)
        """
        contradictions = []
        
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                continue
                
            constraints = rule.get('constraints', [])
            if not isinstance(constraints, list):
                continue
            
            # Group constraints by leftOperand
            operand_groups = {}
            for constraint in constraints:
                if not isinstance(constraint, dict):
                    continue
                    
                operand = constraint.get('leftOperand')
                if operand:
                    if operand not in operand_groups:
                        operand_groups[operand] = []
                    operand_groups[operand].append(constraint)
            
            # Check for contradictions within each group
            for operand, group_constraints in operand_groups.items():
                if len(group_constraints) > 1:
                    # Check for contradictory operators
                    for j, c1 in enumerate(group_constraints):
                        for c2 in group_constraints[j+1:]:
                            if self._are_contradictory(c1, c2):
                                contradictions.append(
                                    f"{rule_type.capitalize()} {i} has contradictory constraints on '{operand}': "
                                    f"{c1.get('operator')} {c1.get('rightOperand')} AND "
                                    f"{c2.get('operator')} {c2.get('rightOperand')}"
                                )
        
        return contradictions
    
    def _are_contradictory(self, c1: Dict, c2: Dict) -> bool:
        """Check if two constraints with same leftOperand are contradictory."""
        op1 = c1.get('operator')
        op2 = c2.get('operator')
        val1 = c1.get('rightOperand')
        val2 = c2.get('rightOperand')
        
        # Same operand with eq but different values
        if op1 == 'eq' and op2 == 'eq' and val1 != val2:
            return True
        
        # eq and neq with same value
        if (op1 == 'eq' and op2 == 'neq' and val1 == val2) or \
           (op1 == 'neq' and op2 == 'eq' and val1 == val2):
            return True
        
        return False
    
    def _check_empty_constraints(
        self,
        permissions: List[Dict],
        prohibitions: List[Dict]
    ) -> List[str]:
        """Check for rules with empty or missing constraints."""
        warnings = []
        
        for i, perm in enumerate(permissions):
            if isinstance(perm, dict):
                constraints = perm.get('constraints', [])
                if not constraints or (isinstance(constraints, list) and len(constraints) == 0):
                    warnings.append(f"Permission {i} has no constraints (unrestricted permission)")
        
        for i, prohib in enumerate(prohibitions):
            if isinstance(prohib, dict):
                constraints = prohib.get('constraints', [])
                if not constraints or (isinstance(constraints, list) and len(constraints) == 0):
                    warnings.append(f"Prohibition {i} has no constraints (blanket prohibition)")
        
        return warnings
    
    def auto_resolve_duplications(
        self,
        components,
        validation_result: ValidationResult
    ):
        """
        Automatically resolve duplications by removing redundant constraints.
        Prefers keeping permissions over prohibitions for positive framing.
        
        Args:
            components: ODRLComponents object to modify
            validation_result: ValidationResult containing duplications
            
        Returns:
            Modified components object
        """
        if not validation_result.duplications:
            return components
        
        logger.info("Auto-resolving constraint duplications...")
        
        # Track constraints to remove from prohibitions
        prohibitions_to_modify = {}
        
        for duplication in validation_result.duplications:
            prohib = duplication.prohibition
            prohib_idx = prohib['rule_index']
            
            if prohib_idx not in prohibitions_to_modify:
                prohibitions_to_modify[prohib_idx] = []
            
            # Mark this constraint for removal
            prohibitions_to_modify[prohib_idx].append({
                'leftOperand': prohib['leftOperand'],
                'operator': prohib['operator'],
                'rightOperand': prohib['rightOperand']
            })
        
        # Get prohibitions list
        prohibitions = self._extract_rules(components, 'prohibitions')
        
        # Remove duplicate constraints from prohibitions
        for prohib_idx, constraints_to_remove in prohibitions_to_modify.items():
            if prohib_idx < len(prohibitions):
                prohibition = prohibitions[prohib_idx]
                if not isinstance(prohibition, dict):
                    continue
                    
                original_constraints = prohibition.get('constraints', [])
                if not isinstance(original_constraints, list):
                    original_constraints = []
                
                # Filter out duplicate constraints
                filtered_constraints = [
                    c for c in original_constraints
                    if not any(
                        self._are_constraints_identical(c, rem)
                        for rem in constraints_to_remove
                    )
                ]
                
                prohibition['constraints'] = filtered_constraints
                
                removed_count = len(original_constraints) - len(filtered_constraints)
                if removed_count > 0:
                    logger.info(
                        f"  Removed {removed_count} duplicate constraint(s) from prohibition {prohib_idx}"
                    )
        
        # Remove empty prohibitions (those with no constraints and no action)
        if hasattr(components, 'prohibitions'):
            components.prohibitions = [
                p for p in prohibitions
                if (isinstance(p, dict) and (p.get('constraints') or p.get('action')))
            ]
        
        logger.info("Auto-resolution complete")
        return components


class ODRLSemanticValidator:
    """
    Additional semantic validation for ODRL policies.
    Checks for logical sense and best practices.
    """
    
    def __init__(self):
        """Initialize semantic validator."""
        pass
    
    def validate_policy_structure(self, policy: Dict) -> List[str]:
        """
        Validate the overall structure of an ODRL policy.
        
        Args:
            policy: Complete ODRL policy dictionary
            
        Returns:
            List of validation issues found
        """
        issues = []
        
        # Check for required top-level fields
        required_fields = ['@context', '@type', 'uid']
        for field in required_fields:
            if field not in policy:
                issues.append(f"Missing required field: {field}")
        
        # Check for at least one rule
        has_permission = bool(policy.get('permission'))
        has_prohibition = bool(policy.get('prohibition'))
        has_obligation = bool(policy.get('obligation'))
        
        if not (has_permission or has_prohibition or has_obligation):
            issues.append("Policy has no rules (no permission, prohibition, or obligation)")
        
        return issues
    
    def suggest_improvements(self, components) -> List[str]:
        """
        Suggest improvements to the policy structure.
        
        Args:
            components: ODRLComponents object
            
        Returns:
            List of suggestions for improvement
        """
        suggestions = []
        
        permissions = self._extract_rules(components, 'permissions')
        prohibitions = self._extract_rules(components, 'prohibitions')
        
        # Suggest using isAnyOf instead of multiple eq constraints
        for rule_list, rule_type in [(permissions, 'permission'), (prohibitions, 'prohibition')]:
            for i, rule in enumerate(rule_list):
                if not isinstance(rule, dict):
                    continue
                    
                constraints = rule.get('constraints', [])
                if not isinstance(constraints, list):
                    continue
                
                # Check for multiple eq constraints on same leftOperand
                operand_counts = {}
                for c in constraints:
                    if not isinstance(c, dict):
                        continue
                    op = c.get('operator')
                    left = c.get('leftOperand')
                    if op == 'eq' and left:
                        operand_counts[left] = operand_counts.get(left, 0) + 1
                
                for operand, count in operand_counts.items():
                    if count > 1:
                        suggestions.append(
                            f"{rule_type.capitalize()} {i}: Consider using 'isAnyOf' "
                            f"instead of multiple 'eq' constraints for '{operand}'"
                        )
        
        return suggestions
    
    def _extract_rules(self, components, rule_type: str) -> List[Dict]:
        """Extract rules from components object."""
        if hasattr(components, rule_type):
            rules = getattr(components, rule_type)
            if isinstance(rules, list):
                return rules
            return []
        return []