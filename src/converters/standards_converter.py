"""
Standards converter for DPV, ODRL, and ODRE integration.
"""
from datetime import datetime
from typing import Dict, Any, List

from ..models.rules import LegislationRule
from ..models.base_models import IntegratedRule
from ..models.enums import ProcessingPurpose, LegalBasis
from ..config import Config


class DPVConcepts:
    """DPV (Data Privacy Vocabulary) concept mappings with GDPR-compliant processing purposes."""

    # Updated DPV Core Namespaces v2.1
    DPV = Config.DPV_NAMESPACE
    DPV_PD = Config.DPV_PD_NAMESPACE
    DPV_TECH = Config.DPV_TECH_NAMESPACE
    DPV_LEGAL = Config.DPV_LEGAL_NAMESPACE
    DPV_ACTION = Config.ACTION_NAMESPACE

    # GDPR-Compliant Processing Purposes
    PROCESSING_PURPOSES = {
        ProcessingPurpose.CONSENT.value: f"{DPV}Consent",
        ProcessingPurpose.CONTRACTUAL_NECESSITY.value: f"{DPV}ContractualNecessity",
        ProcessingPurpose.LEGAL_OBLIGATION.value: f"{DPV}LegalObligation",
        ProcessingPurpose.VITAL_INTERESTS.value: f"{DPV}VitalInterests",
        ProcessingPurpose.PUBLIC_TASK.value: f"{DPV}PublicTask",
        ProcessingPurpose.LEGITIMATE_INTERESTS.value: f"{DPV}LegitimateInterests"
    }

    # GDPR-Compliant Legal Basis
    LEGAL_BASIS = {
        LegalBasis.CONSENT.value: f"{DPV}Consent",
        LegalBasis.CONTRACTUAL_OBLIGATION.value: f"{DPV}ContractualObligation",
        LegalBasis.LEGAL_OBLIGATION.value: f"{DPV}LegalObligation",
        LegalBasis.VITAL_INTERESTS.value: f"{DPV}VitalInterests",
        LegalBasis.PUBLIC_INTEREST_OFFICIAL_AUTHORITY.value: f"{DPV}PublicInterestOfficialAuthority",
        LegalBasis.LEGITIMATE_INTERESTS.value: f"{DPV}LegitimateInterests"
    }

    PROCESSING_OPERATIONS = {
        "collect": f"{DPV}Collect",
        "store": f"{DPV}Store", 
        "use": f"{DPV}Use",
        "share": f"{DPV}Share",
        "transfer": f"{DPV}Transfer",
        "delete": f"{DPV}Erase",
        "process": f"{DPV}Process",
        "access": f"{DPV}Access"
    }

    DATA_CATEGORIES = {
        "personal_data": f"{DPV}PersonalData",
        "sensitive_data": f"{DPV}SensitivePersonalData",
        "biometric_data": f"{DPV_PD}Biometric",
        "health_data": f"{DPV_PD}Health",
        "financial_data": f"{DPV_PD}Financial",
        "location_data": f"{DPV_PD}Location",
        "behavioral_data": f"{DPV_PD}Behavioral",
        "identification_data": f"{DPV_PD}Identifying"
    }

    ROLES = {
        "controller": f"{DPV}DataController",
        "processor": f"{DPV}DataProcessor",
        "joint_controller": f"{DPV}JointDataControllers",
        "data_subject": f"{DPV}DataSubject"
    }

    # Dynamic action mapping (no hardcoded actions)
    @classmethod
    def get_action_uri(cls, action_type: str, is_user_action: bool = False) -> str:
        """Generate action URI dynamically based on action type."""
        action_prefix = "User" if is_user_action else ""
        action_name = ''.join(word.capitalize() for word in action_type.replace('_', ' ').split())
        return f"{cls.DPV_ACTION}{action_prefix}{action_name}"


class StandardsConverter:
    """Converts between JSON Rules Engine and integrated DPV+ODRL+ODRE format."""

    def __init__(self):
        self.dpv_concepts = DPVConcepts()

    def json_rules_to_integrated(self, legislation_rule: LegislationRule) -> IntegratedRule:
        """Convert JSON Rules Engine rule to integrated format."""

        # Extract DPV elements
        dpv_elements = self._extract_dpv_elements(legislation_rule)

        # Extract ODRL elements  
        odrl_elements = self._extract_odrl_elements(legislation_rule)

        # Create integrated rule
        return self._create_integrated_rule(legislation_rule, dpv_elements, odrl_elements)

    def _extract_dpv_elements(self, legislation_rule: LegislationRule) -> Dict[str, Any]:
        """Extract DPV elements from legislation rule with dynamic action mapping."""

        dpv_personal_data = []
        for category in legislation_rule.data_category:
            category_value = category.value if hasattr(category, 'value') else str(category)
            if category_value in self.dpv_concepts.DATA_CATEGORIES:
                dpv_personal_data.append(self.dpv_concepts.DATA_CATEGORIES[category_value])

        dpv_processing = []
        for logic_type, conditions in legislation_rule.conditions.items():
            for condition in conditions:
                fact_lower = condition.fact.lower()
                for operation, uri in self.dpv_concepts.PROCESSING_OPERATIONS.items():
                    if operation in fact_lower:
                        dpv_processing.append(uri)

        # Dynamic purpose mapping based on rule content
        dpv_purposes = []
        rule_text = f"{legislation_rule.description} {legislation_rule.event.type}".lower()
        for purpose_key, purpose_uri in self.dpv_concepts.PROCESSING_PURPOSES.items():
            if purpose_key.replace("_", " ") in rule_text:
                dpv_purposes.append(purpose_uri)

        controller = None
        processor = None
        if legislation_rule.primary_impacted_role:
            primary_role_value = legislation_rule.primary_impacted_role.value if hasattr(legislation_rule.primary_impacted_role, 'value') else str(legislation_rule.primary_impacted_role)
            if primary_role_value in self.dpv_concepts.ROLES:
                if primary_role_value == "controller":
                    controller = self.dpv_concepts.ROLES["controller"]
                elif primary_role_value == "processor":
                    processor = self.dpv_concepts.ROLES["processor"]

        # Dynamic rule actions mapping
        dpv_rule_actions = []
        for action in legislation_rule.actions:
            action_uri = self.dpv_concepts.get_action_uri(action.action_type, is_user_action=False)
            dpv_rule_actions.append(action_uri)

        # Dynamic user actions mapping
        dpv_user_actions = []
        for action in legislation_rule.user_actions:
            action_uri = self.dpv_concepts.get_action_uri(action.action_type, is_user_action=True)
            dpv_user_actions.append(action_uri)

        dpv_locations = [f"dpv:Country_{country.replace(' ', '_')}" for country in legislation_rule.applicable_countries]

        return {
            "hasProcessing": dpv_processing,
            "hasPurpose": dpv_purposes,
            "hasPersonalData": dpv_personal_data,
            "hasDataController": controller,
            "hasDataProcessor": processor,
            "hasLocation": dpv_locations,
            "hasRuleAction": dpv_rule_actions,
            "hasUserAction": dpv_user_actions
        }

    def _extract_odrl_elements(self, legislation_rule: LegislationRule) -> Dict[str, Any]:
        """Extract ODRL elements from legislation rule."""

        permissions = []
        prohibitions = []
        obligations = []

        rule_description = legislation_rule.description.lower()
        event_type = legislation_rule.event.type.lower()

        if "prohibit" in rule_description or "forbid" in event_type:
            prohibition = self._create_odrl_rule(legislation_rule, "prohibition")
            prohibitions.append(prohibition)
        elif "require" in rule_description or "must" in rule_description:
            obligation = self._create_odrl_rule(legislation_rule, "obligation")
            obligations.append(obligation)
        else:
            permission = self._create_odrl_rule(legislation_rule, "permission")
            permissions.append(permission)

        return {
            "permission": permissions,
            "prohibition": prohibitions,
            "obligation": obligations
        }

    def _create_odrl_rule(self, legislation_rule: LegislationRule, rule_type: str) -> Dict[str, Any]:
        """Create individual ODRL rule from legislation rule."""

        target = f"urn:asset:{legislation_rule.source_file}:{legislation_rule.id}"

        actions = []
        for logic_type, conditions in legislation_rule.conditions.items():
            for condition in conditions:
                for domain in condition.data_domain:
                    domain_value = domain.value if hasattr(domain, 'value') else str(domain)
                    if domain_value == "data_transfer":
                        actions.append("transfer")
                    elif domain_value == "data_usage":
                        actions.append("use")
                    elif domain_value == "data_storage":
                        actions.append("store")
                    elif domain_value == "data_collection":
                        actions.append("collect")
                    elif domain_value == "data_deletion":
                        actions.append("delete")

        if not actions:
            actions = ["use"]

        constraints = []
        for logic_type, conditions in legislation_rule.conditions.items():
            for condition in conditions:
                operator_value = condition.operator.value if hasattr(condition.operator, 'value') else str(condition.operator)
                constraint = {
                    "leftOperand": condition.fact,
                    "operator": self._map_operator_to_odrl(operator_value),
                    "rightOperand": condition.value,
                    "comment": condition.description
                }
                constraints.append(constraint)

        rule = {
            "target": target,
            "action": actions[0] if len(actions) == 1 else actions,
            "constraint": constraints
        }

        return rule

    def _map_operator_to_odrl(self, operator: str) -> str:
        """Map operators to ODRL format."""
        mapping = {
            "equal": "eq",
            "notEqual": "neq",
            "greaterThan": "gt", 
            "lessThan": "lt",
            "greaterThanInclusive": "gteq",
            "lessThanInclusive": "lteq",
            "contains": "isA",
            "doesNotContain": "isNotA",
            "in": "isPartOf",
            "notIn": "isNotPartOf"
        }
        return mapping.get(operator, "eq")

    def _create_integrated_rule(self, legislation_rule: LegislationRule, dpv_elements: Dict[str, Any], odrl_elements: Dict[str, Any]) -> IntegratedRule:
        """Create integrated rule."""

        source_levels = []
        chunk_refs = []
        for logic_type, conditions in legislation_rule.conditions.items():
            for condition in conditions:
                level_value = condition.document_level.value if hasattr(condition.document_level, 'value') else str(condition.document_level)
                if level_value not in source_levels:
                    source_levels.append(level_value)
                if condition.chunk_reference and condition.chunk_reference not in chunk_refs:
                    chunk_refs.append(condition.chunk_reference)

        return IntegratedRule(
            id=f"integrated:{legislation_rule.id}",
            dpv_hasProcessing=dpv_elements.get("hasProcessing", []),
            dpv_hasPurpose=dpv_elements.get("hasPurpose", []),
            dpv_hasPersonalData=dpv_elements.get("hasPersonalData", []),
            dpv_hasDataController=dpv_elements.get("hasDataController"),
            dpv_hasDataProcessor=dpv_elements.get("hasDataProcessor"),
            dpv_hasLocation=dpv_elements.get("hasLocation", []),
            dpv_hasRuleAction=dpv_elements.get("hasRuleAction", []),
            dpv_hasUserAction=dpv_elements.get("hasUserAction", []),
            odrl_permission=odrl_elements.get("permission", []),
            odrl_prohibition=odrl_elements.get("prohibition", []),
            odrl_obligation=odrl_elements.get("obligation", []),
            source_document_levels=source_levels,
            chunk_references=chunk_refs,
            source_legislation=legislation_rule.source_file,
            source_article=legislation_rule.source_article,
            confidence_score=legislation_rule.confidence_score
        )

    def integrated_to_json_rules(self, integrated_rule: IntegratedRule) -> Dict[str, Any]:
        """Convert integrated rule back to JSON rules format (if needed)."""
        # Implementation for reverse conversion
        return {
            "id": integrated_rule.id.replace("integrated:", ""),
            "source_legislation": integrated_rule.source_legislation,
            "source_article": integrated_rule.source_article,
            "dpv_elements": {
                "processing": integrated_rule.dpv_hasProcessing,
                "purpose": integrated_rule.dpv_hasPurpose,
                "personal_data": integrated_rule.dpv_hasPersonalData,
                "rule_actions": integrated_rule.dpv_hasRuleAction,
                "user_actions": integrated_rule.dpv_hasUserAction
            },
            "odrl_elements": {
                "permissions": integrated_rule.odrl_permission,
                "prohibitions": integrated_rule.odrl_prohibition,
                "obligations": integrated_rule.odrl_obligation
            },
            "odre_properties": {
                "enforceable": integrated_rule.odre_enforceable,
                "enforcement_mode": integrated_rule.odre_enforcement_mode,
                "action_inference": integrated_rule.odre_action_inference,
                "user_action_inference": integrated_rule.odre_user_action_inference
            },
            "metadata": {
                "source_document_levels": integrated_rule.source_document_levels,
                "chunk_references": integrated_rule.chunk_references,
                "extracted_at": integrated_rule.extracted_at.isoformat(),
                "confidence_score": integrated_rule.confidence_score
            }
        }