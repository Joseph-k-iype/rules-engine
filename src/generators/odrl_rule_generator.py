"""
ODRL Rule Generator - Creates machine-readable ODRL policies from extracted components.
Generates W3C ODRL-compliant JSON-LD output.

Location: src/generators/odrl_rule_generator.py
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ODRLRuleGenerator:
    """
    Generates W3C ODRL 2.2 compliant policies.
    Creates machine-readable rules with proper ODRL structure.
    """
    
    # ODRL namespace
    ODRL_NS = "http://www.w3.org/ns/odrl/2/"
    ODRL_CONTEXT = "http://www.w3.org/ns/odrl.jsonld"
    
    # Common ODRL actions
    ODRL_ACTIONS = {
        "use": f"{ODRL_NS}use",
        "transfer": f"{ODRL_NS}transfer",
        "distribute": f"{ODRL_NS}distribute",
        "reproduce": f"{ODRL_NS}reproduce",
        "modify": f"{ODRL_NS}modify",
        "delete": f"{ODRL_NS}delete",
        "read": f"{ODRL_NS}read",
        "write": f"{ODRL_NS}write",
        "execute": f"{ODRL_NS}execute",
        "play": f"{ODRL_NS}play",
        "display": f"{ODRL_NS}display",
        "print": f"{ODRL_NS}print",
        "stream": f"{ODRL_NS}stream",
        "sell": f"{ODRL_NS}sell",
        "give": f"{ODRL_NS}give",
        "lend": f"{ODRL_NS}lend",
        "share": f"{ODRL_NS}share",
        "derive": f"{ODRL_NS}derive",
        "annotate": f"{ODRL_NS}annotate",
        "archive": f"{ODRL_NS}archive"
    }
    
    # ODRL operators
    ODRL_OPERATORS = {
        "eq": f"{ODRL_NS}eq",
        "neq": f"{ODRL_NS}neq",
        "gt": f"{ODRL_NS}gt",
        "lt": f"{ODRL_NS}lt",
        "gteq": f"{ODRL_NS}gteq",
        "lteq": f"{ODRL_NS}lteq",
        "isA": f"{ODRL_NS}isA",
        "isPartOf": f"{ODRL_NS}isPartOf",
        "isAllOf": f"{ODRL_NS}isAllOf",
        "isAnyOf": f"{ODRL_NS}isAnyOf",
        "isNoneOf": f"{ODRL_NS}isNoneOf"
    }
    
    # Common constraint left operands
    ODRL_LEFT_OPERANDS = {
        "dateTime": f"{ODRL_NS}dateTime",
        "delayPeriod": f"{ODRL_NS}delayPeriod",
        "elapsedTime": f"{ODRL_NS}elapsedTime",
        "event": f"{ODRL_NS}event",
        "count": f"{ODRL_NS}count",
        "percentage": f"{ODRL_NS}percentage",
        "spatial": f"{ODRL_NS}spatial",
        "purpose": f"{ODRL_NS}purpose",
        "industry": f"{ODRL_NS}industry",
        "fileFormat": f"{ODRL_NS}fileFormat",
        "deliveryChannel": f"{ODRL_NS}deliveryChannel",
        "language": f"{ODRL_NS}language",
        "media": f"{ODRL_NS}media",
        "timeInterval": f"{ODRL_NS}timeInterval",
        "unitOfCount": f"{ODRL_NS}unitOfCount",
        "version": f"{ODRL_NS}version"
    }
    
    def __init__(self):
        """Initialize ODRL rule generator."""
        pass
    
    def generate_policy(
        self,
        policy_id: str,
        rule_name: str,
        odrl_components: Any,  # ODRLComponents from analyzer
        framework_type: str,
        restriction_condition: str,
        data_category_uuids: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete ODRL policy.
        
        Args:
            policy_id: Unique identifier for the policy (from CSV)
            rule_name: Human-readable rule name
            odrl_components: Extracted ODRL components
            framework_type: DSS or DataVISA
            restriction_condition: restriction or condition
            data_category_uuids: Mapping of data category names to UUIDs
            
        Returns:
            ODRL policy as dictionary (JSON-LD)
        """
        policy_uid = f"urn:policy:{policy_id}"
        
        policy = {
            "@context": self.ODRL_CONTEXT,
            "@type": "Policy",
            "uid": policy_uid,
            "profile": f"urn:profile:{framework_type.lower()}",
            "dc:title": rule_name,
            "dc:description": f"{framework_type} {restriction_condition}: {rule_name}",
            "dc:created": datetime.utcnow().isoformat(),
            "dc:identifier": policy_id
        }
        
        # Add permissions
        if odrl_components.permissions:
            permissions = []
            for perm in odrl_components.permissions:
                odrl_perm = self._create_permission(perm, data_category_uuids)
                if odrl_perm:
                    permissions.append(odrl_perm)
            
            if permissions:
                policy["permission"] = permissions
        
        # Add prohibitions
        if odrl_components.prohibitions:
            prohibitions = []
            for prohib in odrl_components.prohibitions:
                odrl_prohib = self._create_prohibition(prohib, data_category_uuids)
                if odrl_prohib:
                    prohibitions.append(odrl_prohib)
            
            if prohibitions:
                policy["prohibition"] = prohibitions
        
        # Add metadata about data categories
        if odrl_components.data_categories:
            policy["dc:subject"] = odrl_components.data_categories
        
        # Add geographic scope
        if odrl_components.geographic_scope:
            policy["dc:coverage"] = odrl_components.geographic_scope
        
        # Add purpose if specified
        if odrl_components.purpose:
            policy["dc:purpose"] = odrl_components.purpose
        
        # Add custom metadata
        policy["custom:framework"] = framework_type
        policy["custom:type"] = restriction_condition
        policy["custom:confidenceScore"] = odrl_components.confidence_score
        
        if data_category_uuids:
            policy["custom:dataCategoryUUIDs"] = data_category_uuids
        
        return policy
    
    def _create_permission(
        self, 
        permission: Dict[str, Any],
        data_category_uuids: Dict[str, str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create ODRL permission from extracted permission data."""
        try:
            odrl_permission = {}
            
            # Add action
            action = permission.get("action")
            if action:
                action_uri = self._get_action_uri(action)
                odrl_permission["action"] = action_uri
            else:
                # Default to 'use' if no action specified
                odrl_permission["action"] = self.ODRL_ACTIONS["use"]
            
            # Add target (asset)
            target = permission.get("target")
            if target:
                odrl_permission["target"] = self._create_asset_reference(target)
            
            # Add assigner
            assigner = permission.get("assigner")
            if assigner:
                odrl_permission["assigner"] = self._create_party_reference(assigner, "assigner")
            
            # Add assignee
            assignee = permission.get("assignee")
            if assignee:
                odrl_permission["assignee"] = self._create_party_reference(assignee, "assignee")
            
            # Add constraints
            constraints = permission.get("constraints", [])
            if constraints:
                odrl_constraints = []
                for constraint in constraints:
                    odrl_constraint = self._create_constraint(constraint)
                    if odrl_constraint:
                        odrl_constraints.append(odrl_constraint)
                
                if odrl_constraints:
                    odrl_permission["constraint"] = odrl_constraints
            
            # Add duties
            duties = permission.get("duties", [])
            if duties:
                odrl_duties = []
                for duty in duties:
                    odrl_duty = self._create_duty(duty)
                    if odrl_duty:
                        odrl_duties.append(odrl_duty)
                
                if odrl_duties:
                    odrl_permission["duty"] = odrl_duties
            
            # Add description as comment
            description = permission.get("description")
            if description:
                odrl_permission["rdfs:comment"] = description
            
            return odrl_permission
        
        except Exception as e:
            logger.error(f"Error creating permission: {e}")
            logger.error(f"Permission data: {permission}")
            return None
    
    def _create_prohibition(
        self, 
        prohibition: Dict[str, Any],
        data_category_uuids: Dict[str, str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create ODRL prohibition from extracted prohibition data."""
        try:
            odrl_prohibition = {}
            
            # Add action
            action = prohibition.get("action")
            if action:
                action_uri = self._get_action_uri(action)
                odrl_prohibition["action"] = action_uri
            else:
                # Default to 'use' if no action specified
                odrl_prohibition["action"] = self.ODRL_ACTIONS["use"]
            
            # Add target (asset)
            target = prohibition.get("target")
            if target:
                odrl_prohibition["target"] = self._create_asset_reference(target)
            
            # Add assigner
            assigner = prohibition.get("assigner")
            if assigner:
                odrl_prohibition["assigner"] = self._create_party_reference(assigner, "assigner")
            
            # Add assignee
            assignee = prohibition.get("assignee")
            if assignee:
                odrl_prohibition["assignee"] = self._create_party_reference(assignee, "assignee")
            
            # Add constraints
            constraints = prohibition.get("constraints", [])
            if constraints:
                odrl_constraints = []
                for constraint in constraints:
                    odrl_constraint = self._create_constraint(constraint)
                    if odrl_constraint:
                        odrl_constraints.append(odrl_constraint)
                
                if odrl_constraints:
                    odrl_prohibition["constraint"] = odrl_constraints
            
            # Add description as comment
            description = prohibition.get("description")
            if description:
                odrl_prohibition["rdfs:comment"] = description
            
            return odrl_prohibition
        
        except Exception as e:
            logger.error(f"Error creating prohibition: {e}")
            logger.error(f"Prohibition data: {prohibition}")
            return None
    
    def _create_constraint(self, constraint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create ODRL constraint."""
        try:
            odrl_constraint = {}
            
            # Left operand
            left_operand = constraint.get("leftOperand")
            if left_operand:
                left_uri = self._get_left_operand_uri(left_operand)
                odrl_constraint["leftOperand"] = left_uri
            else:
                logger.warning(f"Constraint missing leftOperand: {constraint}")
                return None
            
            # Operator
            operator = constraint.get("operator", "eq")
            operator_uri = self._get_operator_uri(operator)
            odrl_constraint["operator"] = operator_uri
            
            # Right operand
            right_operand = constraint.get("rightOperand")
            if right_operand is not None:
                odrl_constraint["rightOperand"] = right_operand
            else:
                logger.warning(f"Constraint missing rightOperand: {constraint}")
                return None
            
            # Description as comment
            description = constraint.get("description")
            if description:
                odrl_constraint["rdfs:comment"] = description
            
            return odrl_constraint
        
        except Exception as e:
            logger.error(f"Error creating constraint: {e}")
            return None
    
    def _create_duty(self, duty: str or Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create ODRL duty."""
        try:
            odrl_duty = {}
            
            if isinstance(duty, str):
                # Simple duty description
                odrl_duty["action"] = self.ODRL_ACTIONS["use"]  # Generic action
                odrl_duty["rdfs:comment"] = duty
            elif isinstance(duty, dict):
                # Structured duty
                action = duty.get("action", "use")
                odrl_duty["action"] = self._get_action_uri(action)
                
                if duty.get("description"):
                    odrl_duty["rdfs:comment"] = duty["description"]
            
            return odrl_duty
        
        except Exception as e:
            logger.error(f"Error creating duty: {e}")
            return None
    
    def _create_asset_reference(self, target: str) -> str:
        """Create asset reference URI."""
        if target.startswith("http://") or target.startswith("https://") or target.startswith("urn:"):
            return target
        else:
            # Create URN for non-URI targets
            return f"urn:asset:{target.replace(' ', '_')}"
    
    def _create_party_reference(self, party: str, role: str) -> Dict[str, Any]:
        """Create party reference with role."""
        if party.startswith("http://") or party.startswith("https://") or party.startswith("urn:"):
            party_uri = party
        else:
            party_uri = f"urn:party:{party.replace(' ', '_')}"
        
        return {
            "uid": party_uri,
            "role": role
        }
    
    def _get_action_uri(self, action: str) -> str:
        """Get ODRL action URI, creating custom if needed."""
        action_lower = action.lower().strip()
        
        # Check standard ODRL actions
        if action_lower in self.ODRL_ACTIONS:
            return self.ODRL_ACTIONS[action_lower]
        
        # Try to find similar action
        for key, uri in self.ODRL_ACTIONS.items():
            if key in action_lower or action_lower in key:
                return uri
        
        # Create custom action URI
        custom_action = action.replace(" ", "_").replace("-", "_")
        return f"{self.ODRL_NS}{custom_action}"
    
    def _get_operator_uri(self, operator: str) -> str:
        """Get ODRL operator URI."""
        operator_lower = operator.lower().strip()
        
        if operator_lower in self.ODRL_OPERATORS:
            return self.ODRL_OPERATORS[operator_lower]
        
        # Try common aliases
        aliases = {
            "equals": "eq",
            "equal": "eq",
            "==": "eq",
            "not_equal": "neq",
            "!=": "neq",
            "greater_than": "gt",
            ">": "gt",
            "less_than": "lt",
            "<": "lt",
            ">=": "gteq",
            "<=": "lteq"
        }
        
        if operator_lower in aliases:
            return self.ODRL_OPERATORS[aliases[operator_lower]]
        
        # Default to eq
        return self.ODRL_OPERATORS["eq"]
    
    def _get_left_operand_uri(self, left_operand: str) -> str:
        """Get ODRL left operand URI, creating custom if needed."""
        operand_lower = left_operand.lower().strip()
        
        # Check standard operands
        if operand_lower in self.ODRL_LEFT_OPERANDS:
            return self.ODRL_LEFT_OPERANDS[operand_lower]
        
        # Try to find similar operand
        for key, uri in self.ODRL_LEFT_OPERANDS.items():
            if key in operand_lower or operand_lower in key:
                return uri
        
        # Create custom left operand
        custom_operand = left_operand.replace(" ", "_").replace("-", "_")
        return f"{self.ODRL_NS}{custom_operand}"
    
    def validate_policy(self, policy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate ODRL policy structure.
        
        Returns:
            Validation report with issues found
        """
        issues = []
        warnings = []
        
        # Check required fields
        if "@context" not in policy:
            issues.append("Missing @context")
        
        if "@type" not in policy:
            issues.append("Missing @type")
        
        if "uid" not in policy:
            issues.append("Missing uid")
        
        # Check for at least one rule
        has_permission = "permission" in policy and policy["permission"]
        has_prohibition = "prohibition" in policy and policy["prohibition"]
        
        if not has_permission and not has_prohibition:
            warnings.append("Policy has no permissions or prohibitions")
        
        # Validate permissions
        if "permission" in policy:
            for i, perm in enumerate(policy["permission"]):
                if "action" not in perm:
                    issues.append(f"Permission {i}: missing action")
        
        # Validate prohibitions
        if "prohibition" in policy:
            for i, prohib in enumerate(policy["prohibition"]):
                if "action" not in prohib:
                    issues.append(f"Prohibition {i}: missing action")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }