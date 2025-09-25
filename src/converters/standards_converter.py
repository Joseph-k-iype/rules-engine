"""
Standards converter for DPV, ODRL, and ODRE integration.
Enhanced with combined actions structure and decision-making capabilities.
"""
from datetime import datetime
from typing import Dict, Any, List

from ..models.rules import LegislationRule
from ..models.base_models import IntegratedRule, CombinedAction
from ..models.enums import ProcessingPurpose, LegalBasis
from ..config import Config


class DPVConcepts:
    """DPV (Data Privacy Vocabulary) concept mappings with GDPR-compliant processing purposes, combined actions, and decision support."""

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

    # Decision mappings for DPV
    DECISION_TYPES = {
        "data_transfer": f"{DPV_ACTION}DataTransferDecision",
        "data_processing": f"{DPV_ACTION}DataProcessingDecision",
        "data_collection": f"{DPV_ACTION}DataCollectionDecision",
        "data_storage": f"{DPV_ACTION}DataStorageDecision",
        "data_deletion": f"{DPV_ACTION}DataDeletionDecision",
        "consent_requirement": f"{DPV_ACTION}ConsentDecision",
        "access_permission": f"{DPV_ACTION}AccessDecision",
        "sharing_permission": f"{DPV_ACTION}SharingDecision",
        "compliance_status": f"{DPV_ACTION}ComplianceDecision"
    }

    DECISION_CONTEXTS = {
        "cross_border_transfer": f"{DPV_ACTION}CrossBorderContext",
        "internal_processing": f"{DPV_ACTION}InternalProcessingContext",
        "third_party_sharing": f"{DPV_ACTION}ThirdPartySharingContext",
        "data_subject_request": f"{DPV_ACTION}DataSubjectRequestContext",
        "regulatory_compliance": f"{DPV_ACTION}RegulatoryComplianceContext",
        "security_assessment": f"{DPV_ACTION}SecurityAssessmentContext"
    }

    DECISION_OUTCOMES = {
        "yes": f"{DPV_ACTION}PermittedOutcome",
        "no": f"{DPV_ACTION}ProhibitedOutcome",
        "maybe": f"{DPV_ACTION}ConditionalOutcome"
    }

    # Action category mappings
    ACTION_CATEGORIES = {
        "organizational": f"{DPV_ACTION}OrganizationalAction",
        "individual": f"{DPV_ACTION}IndividualAction"
    }

    # Dynamic action mapping (no hardcoded actions) - combined approach
    @classmethod
    def get_combined_action_uri(cls, action_type: str, action_category: str) -> str:
        """Generate combined action URI dynamically based on action type and category."""
        category_prefix = action_category.capitalize() if action_category else ""
        action_name = ''.join(word.capitalize() for word in action_type.replace('_', ' ').split())
        return f"{cls.DPV_ACTION}{category_prefix}{action_name}"

    # Backwards compatibility methods
    @classmethod
    def get_action_uri(cls, action_type: str, is_user_action: bool = False) -> str:
        """Generate action URI dynamically based on action type (backwards compatibility)."""
        action_category = "individual" if is_user_action else "organizational"
        return cls.get_combined_action_uri(action_type, action_category)

    # Dynamic decision mapping
    @classmethod
    def get_decision_uri(cls, decision_type: str, decision_context: str, outcome: str) -> str:
        """Generate decision URI dynamically based on decision components."""
        decision_name = ''.join(word.capitalize() for word in decision_type.replace('_', ' ').split())
        context_name = ''.join(word.capitalize() for word in decision_context.replace('_', ' ').split())
        outcome_name = ''.join(word.capitalize() for word in outcome.split())
        return f"{cls.DPV_ACTION}{decision_name}{context_name}{outcome_name}"


class StandardsConverter:
    """Converts between JSON Rules Engine and integrated DPV+ODRL+ODRE format with combined actions and decision support."""

    def __init__(self):
        self.dpv_concepts = DPVConcepts()

    def json_rules_to_integrated(self, legislation_rule: LegislationRule) -> IntegratedRule:
        """Convert JSON Rules Engine rule to integrated format with combined actions and decision support."""

        # Extract DPV elements with combined actions
        dpv_elements = self._extract_dpv_elements_with_combined_actions(legislation_rule)

        # Extract ODRL elements  
        odrl_elements = self._extract_odrl_elements(legislation_rule)

        # Create integrated rule
        return self._create_integrated_rule_with_combined_actions(legislation_rule, dpv_elements, odrl_elements)

    def _extract_dpv_elements_with_combined_actions(self, legislation_rule: LegislationRule) -> Dict[str, Any]:
        """Extract DPV elements from legislation rule with combined action mapping."""

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

        # Combined actions mapping (replaces separate rule and user actions)
        dpv_combined_actions = []
        
        # Process rule actions as organizational
        for action in legislation_rule.actions:
            action_uri = self.dpv_concepts.get_combined_action_uri(action.action_type, "organizational")
            dpv_combined_actions.append(action_uri)

        # Process user actions as individual
        for action in legislation_rule.user_actions:
            action_uri = self.dpv_concepts.get_combined_action_uri(action.action_type, "individual")
            dpv_combined_actions.append(action_uri)

        # Backwards compatibility - separate action lists (deprecated)
        dpv_rule_actions = []
        for action in legislation_rule.actions:
            action_uri = self.dpv_concepts.get_action_uri(action.action_type, is_user_action=False)
            dpv_rule_actions.append(action_uri)

        dpv_user_actions = []
        for action in legislation_rule.user_actions:
            action_uri = self.dpv_concepts.get_action_uri(action.action_type, is_user_action=True)
            dpv_user_actions.append(action_uri)

        # Dynamic decision mapping
        dpv_decisions = []
        dpv_decision_outcomes = []
        for decision in legislation_rule.decisions:
            decision_type_value = decision.decision_type.value if hasattr(decision.decision_type, 'value') else str(decision.decision_type)
            decision_context_value = decision.decision_context.value if hasattr(decision.decision_context, 'value') else str(decision.decision_context)
            outcome_value = decision.outcome.value if hasattr(decision.outcome, 'value') else str(decision.outcome)
            
            # Map decision type
            if decision_type_value in self.dpv_concepts.DECISION_TYPES:
                dpv_decisions.append(self.dpv_concepts.DECISION_TYPES[decision_type_value])
            
            # Map decision outcome
            if outcome_value in self.dpv_concepts.DECISION_OUTCOMES:
                dpv_decision_outcomes.append(self.dpv_concepts.DECISION_OUTCOMES[outcome_value])
            
            # Create combined decision URI
            combined_decision_uri = self.dpv_concepts.get_decision_uri(decision_type_value, decision_context_value, outcome_value)
            dpv_decisions.append(combined_decision_uri)

        dpv_locations = [f"dpv:Country_{country.replace(' ', '_')}" for country in legislation_rule.applicable_countries]

        return {
            "hasProcessing": dpv_processing,
            "hasPurpose": dpv_purposes,
            "hasPersonalData": dpv_personal_data,
            "hasDataController": controller,
            "hasDataProcessor": processor,
            "hasLocation": dpv_locations,
            # New combined actions
            "hasCombinedAction": dpv_combined_actions,
            # Backwards compatibility (deprecated)
            "hasRuleAction": dpv_rule_actions,
            "hasUserAction": dpv_user_actions,
            # Decisions
            "hasDecision": dpv_decisions,
            "hasDecisionOutcome": dpv_decision_outcomes
        }

    def _extract_odrl_elements(self, legislation_rule: LegislationRule) -> Dict[str, Any]:
        """Extract ODRL elements from legislation rule with decision support."""

        permissions = []
        prohibitions = []
        obligations = []

        rule_description = legislation_rule.description.lower()
        event_type = legislation_rule.event.type.lower()

        # Analyze decisions to determine ODRL policies
        for decision in legislation_rule.decisions:
            outcome_value = decision.outcome.value if hasattr(decision.outcome, 'value') else str(decision.outcome)
            decision_type_value = decision.decision_type.value if hasattr(decision.decision_type, 'value') else str(decision.decision_type)
            
            if outcome_value == "yes":
                permission = self._create_odrl_rule_from_decision(legislation_rule, decision, "permission")
                permissions.append(permission)
            elif outcome_value == "no":
                prohibition = self._create_odrl_rule_from_decision(legislation_rule, decision, "prohibition")
                prohibitions.append(prohibition)
            elif outcome_value == "maybe":
                # Maybe decisions become conditional permissions (permissions with constraints)
                conditional_permission = self._create_odrl_rule_from_decision(legislation_rule, decision, "conditional_permission")
                permissions.append(conditional_permission)
                
                # Also create obligations for the required actions
                if decision.required_actions_for_maybe:
                    obligation = self._create_odrl_rule_from_decision(legislation_rule, decision, "obligation")
                    obligations.append(obligation)

        # Fallback to traditional analysis if no decisions present
        if not permissions and not prohibitions and not obligations:
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

    def _create_odrl_rule_from_decision(self, legislation_rule: LegislationRule, decision, rule_type: str) -> Dict[str, Any]:
        """Create ODRL rule from decision scenario."""

        target = f"urn:asset:{legislation_rule.source_file}:{legislation_rule.id}:{decision.id}"

        # Map decision type to ODRL action
        decision_type_value = decision.decision_type.value if hasattr(decision.decision_type, 'value') else str(decision.decision_type)
        action_mapping = {
            "data_transfer": "transfer",
            "data_processing": "use",
            "data_collection": "collect",
            "data_storage": "store",
            "data_deletion": "delete",
            "access_permission": "read",
            "sharing_permission": "distribute"
        }
        
        action = action_mapping.get(decision_type_value, "use")

        constraints = []
        
        # Add constraints based on decision outcome and conditions
        outcome_value = decision.outcome.value if hasattr(decision.outcome, 'value') else str(decision.outcome)
        
        if outcome_value == "maybe" or rule_type == "conditional_permission":
            # Add constraints for maybe conditions
            for condition in decision.conditions_for_maybe:
                constraint = {
                    "leftOperand": "required_condition",
                    "operator": "eq",
                    "rightOperand": condition,
                    "comment": f"Required condition: {condition}"
                }
                constraints.append(constraint)
                
            # Add constraints for required actions
            for action_required in decision.required_actions_for_maybe:
                constraint = {
                    "leftOperand": "required_action",
                    "operator": "eq", 
                    "rightOperand": action_required,
                    "comment": f"Required action: {action_required}"
                }
                constraints.append(constraint)
        
        elif outcome_value == "yes":
            # Add constraints for yes conditions
            for condition in decision.conditions_for_yes:
                constraint = {
                    "leftOperand": "fulfillment_condition",
                    "operator": "eq",
                    "rightOperand": condition,
                    "comment": f"Fulfillment condition: {condition}"
                }
                constraints.append(constraint)
        
        elif outcome_value == "no":
            # Add constraints for no conditions
            for condition in decision.conditions_for_no:
                constraint = {
                    "leftOperand": "prohibition_condition",
                    "operator": "eq",
                    "rightOperand": condition,
                    "comment": f"Prohibition condition: {condition}"
                }
                constraints.append(constraint)

        # Add geographic constraints if cross-border
        if decision.cross_border:
            if decision.source_jurisdiction:
                constraint = {
                    "leftOperand": "source_jurisdiction",
                    "operator": "eq",
                    "rightOperand": decision.source_jurisdiction,
                    "comment": f"Source jurisdiction: {decision.source_jurisdiction}"
                }
                constraints.append(constraint)
            
            if decision.target_jurisdiction:
                constraint = {
                    "leftOperand": "target_jurisdiction", 
                    "operator": "eq",
                    "rightOperand": decision.target_jurisdiction,
                    "comment": f"Target jurisdiction: {decision.target_jurisdiction}"
                }
                constraints.append(constraint)

        rule = {
            "target": target,
            "action": action,
            "constraint": constraints,
            "decision_scenario": decision.scenario,
            "decision_rationale": decision.rationale,
            "decision_outcome": outcome_value
        }

        return rule

    def _create_odrl_rule(self, legislation_rule: LegislationRule, rule_type: str) -> Dict[str, Any]:
        """Create individual ODRL rule from legislation rule (fallback method)."""

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

    def _create_integrated_rule_with_combined_actions(self, legislation_rule: LegislationRule, dpv_elements: Dict[str, Any], odrl_elements: Dict[str, Any]) -> IntegratedRule:
        """Create integrated rule with combined actions and decision support."""

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
            
            # New combined actions field
            dpv_hasAction=dpv_elements.get("hasCombinedAction", []),
            
            # Backwards compatibility (deprecated)
            dpv_hasRuleAction=dpv_elements.get("hasRuleAction", []),
            dpv_hasUserAction=dpv_elements.get("hasUserAction", []),
            
            # Decisions
            dpv_hasDecision=dpv_elements.get("hasDecision", []),
            dpv_hasDecisionOutcome=dpv_elements.get("hasDecisionOutcome", []),
            
            odrl_permission=odrl_elements.get("permission", []),
            odrl_prohibition=odrl_elements.get("prohibition", []),
            odrl_obligation=odrl_elements.get("obligation", []),
            
            # ODRE properties with updated enforcement mode
            odre_enforcement_mode="combined_action_based",
            
            source_document_levels=source_levels,
            chunk_references=chunk_refs,
            source_legislation=legislation_rule.source_file,
            source_article=legislation_rule.source_article,
            confidence_score=legislation_rule.confidence_score
        )

    def integrated_to_json_rules(self, integrated_rule: IntegratedRule) -> Dict[str, Any]:
        """Convert integrated rule back to JSON rules format (if needed) with combined actions support."""
        
        # Get combined actions (either from new field or backwards compatibility)
        combined_actions = integrated_rule.get_combined_actions()
        
        return {
            "id": integrated_rule.id.replace("integrated:", ""),
            "source_legislation": integrated_rule.source_legislation,
            "source_article": integrated_rule.source_article,
            "dpv_elements": {
                "processing": integrated_rule.dpv_hasProcessing,
                "purpose": integrated_rule.dpv_hasPurpose,
                "personal_data": integrated_rule.dpv_hasPersonalData,
                # Combined actions
                "actions": combined_actions,
                # Backwards compatibility
                "rule_actions": integrated_rule.dpv_hasRuleAction,
                "user_actions": integrated_rule.dpv_hasUserAction,
                # Decisions
                "decisions": integrated_rule.dpv_hasDecision,
                "decision_outcomes": integrated_rule.dpv_hasDecisionOutcome
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
                "user_action_inference": integrated_rule.odre_user_action_inference,
                "decision_inference": integrated_rule.odre_decision_inference
            },
            "metadata": {
                "source_document_levels": integrated_rule.source_document_levels,
                "chunk_references": integrated_rule.chunk_references,
                "extracted_at": integrated_rule.extracted_at.isoformat(),
                "confidence_score": integrated_rule.confidence_score
            }
        }