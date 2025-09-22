"""
Standards converter for DPV, ODRL, and ODRE integration with decision-making capabilities.
"""
from datetime import datetime
from typing import Dict, Any, List

from ..models.rules import LegislationRule
from ..models.base_models import IntegratedRule, DecisionOutcome
from ..models.enums import ProcessingPurpose, LegalBasis, DecisionType, DecisionContext, RequiredActionType
from ..config import Config


class DPVConcepts:
    """DPV (Data Privacy Vocabulary) concept mappings with GDPR-compliant processing purposes and decision concepts."""

    # Updated DPV Core Namespaces v2.1
    DPV = Config.DPV_NAMESPACE
    DPV_PD = Config.DPV_PD_NAMESPACE
    DPV_TECH = Config.DPV_TECH_NAMESPACE
    DPV_LEGAL = Config.DPV_LEGAL_NAMESPACE
    DPV_ACTION = Config.ACTION_NAMESPACE
    
    # Decision Framework Namespace
    DECISION = "https://w3id.org/decision-framework#"

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

    # Decision Types Mapping
    DECISION_TYPES = {
        DecisionType.YES.value: f"{DECISION}PermittedDecision",
        DecisionType.NO.value: f"{DECISION}ProhibitedDecision", 
        DecisionType.MAYBE.value: f"{DECISION}ConditionalDecision",
        DecisionType.UNKNOWN.value: f"{DECISION}UnknownDecision"
    }

    # Decision Contexts Mapping
    DECISION_CONTEXTS = {
        DecisionContext.DATA_TRANSFER.value: f"{DECISION}DataTransferContext",
        DecisionContext.DATA_PROCESSING.value: f"{DECISION}DataProcessingContext",
        DecisionContext.DATA_STORAGE.value: f"{DECISION}DataStorageContext",
        DecisionContext.DATA_COLLECTION.value: f"{DECISION}DataCollectionContext",
        DecisionContext.DATA_SHARING.value: f"{DECISION}DataSharingContext",
        DecisionContext.DATA_DELETION.value: f"{DECISION}DataDeletionContext",
        DecisionContext.CONSENT_MANAGEMENT.value: f"{DECISION}ConsentManagementContext",
        DecisionContext.RIGHTS_EXERCISE.value: f"{DECISION}RightsExerciseContext",
        DecisionContext.COMPLIANCE_VERIFICATION.value: f"{DECISION}ComplianceVerificationContext"
    }

    # Required Action Types Mapping
    REQUIRED_ACTIONS = {
        RequiredActionType.DATA_MASKING.value: f"{DPV_ACTION}DataMasking",
        RequiredActionType.DATA_ENCRYPTION.value: f"{DPV_ACTION}DataEncryption",
        RequiredActionType.DATA_ANONYMIZATION.value: f"{DPV_ACTION}DataAnonymization",
        RequiredActionType.CONSENT_OBTAINMENT.value: f"{DPV_ACTION}ConsentObtainment",
        RequiredActionType.CONSENT_VERIFICATION.value: f"{DPV_ACTION}ConsentVerification",
        RequiredActionType.LEGAL_BASIS_ESTABLISHMENT.value: f"{DPV_ACTION}LegalBasisEstablishment",
        RequiredActionType.ADEQUACY_VERIFICATION.value: f"{DPV_ACTION}AdequacyVerification",
        RequiredActionType.SAFEGUARDS_IMPLEMENTATION.value: f"{DPV_ACTION}SafeguardsImplementation",
        RequiredActionType.DOCUMENTATION_COMPLETION.value: f"{DPV_ACTION}DocumentationCompletion",
        RequiredActionType.AUDIT_COMPLETION.value: f"{DPV_ACTION}AuditCompletion",
        RequiredActionType.APPROVAL_OBTAINMENT.value: f"{DPV_ACTION}ApprovalObtainment",
        RequiredActionType.NOTIFICATION_COMPLETION.value: f"{DPV_ACTION}NotificationCompletion",
        RequiredActionType.IMPACT_ASSESSMENT.value: f"{DPV_ACTION}ImpactAssessment",
        RequiredActionType.SECURITY_MEASURES.value: f"{DPV_ACTION}SecurityMeasures",
        RequiredActionType.ACCESS_CONTROLS.value: f"{DPV_ACTION}AccessControls"
    }

    # Dynamic action mapping (no hardcoded actions)
    @classmethod
    def get_action_uri(cls, action_type: str, is_user_action: bool = False) -> str:
        """Generate action URI dynamically based on action type."""
        action_prefix = "User" if is_user_action else ""
        action_name = ''.join(word.capitalize() for word in action_type.replace('_', ' ').split())
        return f"{cls.DPV_ACTION}{action_prefix}{action_name}"

    @classmethod
    def get_decision_action_uri(cls, action_type: str) -> str:
        """Generate decision-enabling action URI dynamically."""
        action_name = ''.join(word.capitalize() for word in action_type.replace('_', ' ').split())
        return f"{cls.DECISION}Enable{action_name}Decision"


class StandardsConverter:
    """Converts between JSON Rules Engine and integrated DPV+ODRL+ODRE format with decision-making capabilities."""

    def __init__(self):
        self.dpv_concepts = DPVConcepts()

    def json_rules_to_integrated(self, legislation_rule: LegislationRule) -> IntegratedRule:
        """Convert JSON Rules Engine rule to integrated format with decision capabilities."""

        # Extract DPV elements
        dpv_elements = self._extract_dpv_elements(legislation_rule)

        # Extract ODRL elements  
        odrl_elements = self._extract_odrl_elements(legislation_rule)

        # Extract decision elements
        decision_elements = self._extract_decision_elements(legislation_rule)

        # Create integrated rule
        return self._create_integrated_rule(legislation_rule, dpv_elements, odrl_elements, decision_elements)

    def _extract_dpv_elements(self, legislation_rule: LegislationRule) -> Dict[str, Any]:
        """Extract DPV elements from legislation rule with dynamic action mapping and decision context."""

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

        # Dynamic decision-enabling actions mapping
        dpv_decision_actions = []
        
        # From rule actions that enable decisions
        for action in legislation_rule.actions:
            if hasattr(action, 'enables_decision') and action.enables_decision:
                decision_action_uri = self.dpv_concepts.get_decision_action_uri(action.action_type)
                dpv_decision_actions.append(decision_action_uri)
        
        # From user actions that enable decisions
        for action in legislation_rule.user_actions:
            if hasattr(action, 'enables_decision') and action.enables_decision:
                decision_action_uri = self.dpv_concepts.get_decision_action_uri(action.action_type)
                dpv_decision_actions.append(decision_action_uri)
        
        # From decision outcome required actions
        if legislation_rule.decision_outcome:
            for required_action in legislation_rule.decision_outcome.required_actions:
                required_action_value = required_action.value if hasattr(required_action, 'value') else str(required_action)
                if required_action_value in self.dpv_concepts.REQUIRED_ACTIONS:
                    dpv_decision_actions.append(self.dpv_concepts.REQUIRED_ACTIONS[required_action_value])

        dpv_locations = [f"dpv:Country_{country.replace(' ', '_')}" for country in legislation_rule.applicable_countries]

        return {
            "hasProcessing": dpv_processing,
            "hasPurpose": dpv_purposes,
            "hasPersonalData": dpv_personal_data,
            "hasDataController": controller,
            "hasDataProcessor": processor,
            "hasLocation": dpv_locations,
            "hasRuleAction": dpv_rule_actions,
            "hasUserAction": dpv_user_actions,
            "hasDecisionAction": dpv_decision_actions
        }

    def _extract_odrl_elements(self, legislation_rule: LegislationRule) -> Dict[str, Any]:
        """Extract ODRL elements from legislation rule with decision context."""

        permissions = []
        prohibitions = []
        obligations = []

        rule_description = legislation_rule.description.lower()
        event_type = legislation_rule.event.type.lower()

        # Consider decision outcome for ODRL classification
        if legislation_rule.decision_outcome:
            decision_type = legislation_rule.decision_outcome.decision
            if decision_type == DecisionType.YES:
                permission = self._create_odrl_rule(legislation_rule, "permission")
                permissions.append(permission)
            elif decision_type == DecisionType.NO:
                prohibition = self._create_odrl_rule(legislation_rule, "prohibition")
                prohibitions.append(prohibition)
            elif decision_type == DecisionType.MAYBE:
                # Conditional permission with obligations
                permission = self._create_odrl_rule(legislation_rule, "permission")
                permissions.append(permission)
                obligation = self._create_odrl_rule(legislation_rule, "obligation")
                obligations.append(obligation)
        else:
            # Fallback to text analysis
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

    def _extract_decision_elements(self, legislation_rule: LegislationRule) -> Dict[str, Any]:
        """Extract decision-specific elements from legislation rule."""
        
        decision_elements = {
            "primary_decision": None,
            "decision_rules": [],
            "decision_contexts": [],
            "conditional_requirements": [],
            "enabling_actions": []
        }
        
        # Extract primary decision outcome
        if legislation_rule.decision_outcome:
            decision_elements["primary_decision"] = {
                "decision_type": legislation_rule.decision_outcome.decision.value,
                "context": legislation_rule.decision_outcome.context.value,
                "confidence": legislation_rule.decision_outcome.confidence,
                "reasoning": legislation_rule.decision_outcome.decision_reasoning,
                "legislative_basis": legislation_rule.decision_outcome.legislative_basis,
                "required_actions": [action.value for action in legislation_rule.decision_outcome.required_actions],
                "required_conditions": legislation_rule.decision_outcome.required_conditions
            }
            
            decision_elements["decision_contexts"].append(legislation_rule.decision_outcome.context.value)
            decision_elements["conditional_requirements"].extend(
                [action.value for action in legislation_rule.decision_outcome.required_actions]
            )
        
        # Extract decision rules
        for decision_rule in legislation_rule.decision_rules:
            rule_element = {
                "id": decision_rule.id,
                "question": decision_rule.question,
                "context": decision_rule.context.value,
                "default_decision": decision_rule.default_decision.value,
                "conditional_decisions": decision_rule.conditional_decisions,
                "requirements_for_yes": decision_rule.requirements_for_yes,
                "requirements_for_maybe": [req.value for req in decision_rule.requirements_for_maybe],
                "reasons_for_no": decision_rule.reasons_for_no,
                "applicable_scenarios": decision_rule.applicable_scenarios,
                "confidence_score": decision_rule.confidence_score
            }
            
            decision_elements["decision_rules"].append(rule_element)
            decision_elements["decision_contexts"].append(decision_rule.context.value)
            decision_elements["conditional_requirements"].extend(
                [req.value for req in decision_rule.requirements_for_maybe]
            )
        
        # Extract enabling actions from rule actions
        for action in legislation_rule.actions:
            if hasattr(action, 'enables_decision') and action.enables_decision:
                enabling_element = {
                    "action_id": action.id,
                    "action_type": action.action_type,
                    "title": action.title,
                    "enables_decision": action.enables_decision.decision.value,
                    "decision_context": action.enables_decision.context.value,
                    "decision_reasoning": action.enables_decision.decision_reasoning
                }
                decision_elements["enabling_actions"].append(enabling_element)
        
        # Extract enabling actions from user actions
        for action in legislation_rule.user_actions:
            if hasattr(action, 'enables_decision') and action.enables_decision:
                enabling_element = {
                    "action_id": action.id,
                    "action_type": action.action_type,
                    "title": action.title,
                    "enables_decision": action.enables_decision.decision.value,
                    "decision_context": action.enables_decision.context.value,
                    "decision_reasoning": action.enables_decision.decision_reasoning
                }
                decision_elements["enabling_actions"].append(enabling_element)
        
        # Remove duplicates from lists
        decision_elements["decision_contexts"] = list(set(decision_elements["decision_contexts"]))
        decision_elements["conditional_requirements"] = list(set(decision_elements["conditional_requirements"]))
        
        return decision_elements

    def _create_odrl_rule(self, legislation_rule: LegislationRule, rule_type: str) -> Dict[str, Any]:
        """Create individual ODRL rule from legislation rule with decision context."""

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
        
        # Add standard conditions as constraints
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
        
        # Add decision-specific constraints
        if legislation_rule.decision_outcome and legislation_rule.decision_outcome.required_actions:
            for required_action in legislation_rule.decision_outcome.required_actions:
                action_value = required_action.value if hasattr(required_action, 'value') else str(required_action)
                constraint = {
                    "leftOperand": "required_action",
                    "operator": "eq",
                    "rightOperand": action_value,
                    "comment": f"Required action for conditional decision: {action_value.replace('_', ' ')}"
                }
                constraints.append(constraint)

        rule = {
            "target": target,
            "action": actions[0] if len(actions) == 1 else actions,
            "constraint": constraints
        }
        
        # Add decision context if available
        if legislation_rule.decision_outcome:
            rule["decisionContext"] = legislation_rule.decision_outcome.context.value
            rule["decisionType"] = legislation_rule.decision_outcome.decision.value

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

    def _create_integrated_rule(
        self, legislation_rule: LegislationRule, dpv_elements: Dict[str, Any], 
        odrl_elements: Dict[str, Any], decision_elements: Dict[str, Any]
    ) -> IntegratedRule:
        """Create integrated rule with decision-making capabilities."""

        source_levels = []
        chunk_refs = []
        for logic_type, conditions in legislation_rule.conditions.items():
            for condition in conditions:
                level_value = condition.document_level.value if hasattr(condition.document_level, 'value') else str(condition.document_level)
                if level_value not in source_levels:
                    source_levels.append(level_value)
                if condition.chunk_reference and condition.chunk_reference not in chunk_refs:
                    chunk_refs.append(condition.chunk_reference)

        # Create primary decision outcome for integrated rule
        primary_decision = None
        if decision_elements["primary_decision"]:
            pd = decision_elements["primary_decision"]
            # Map required actions to URIs
            required_action_uris = []
            for action in pd["required_actions"]:
                if action in self.dpv_concepts.REQUIRED_ACTIONS:
                    required_action_uris.append(self.dpv_concepts.REQUIRED_ACTIONS[action])
            
            primary_decision = DecisionOutcome(
                decision=DecisionType(pd["decision_type"]),
                context=DecisionContext(pd["context"]),
                confidence=pd["confidence"],
                required_actions=[RequiredActionType(action) for action in pd["required_actions"]],
                required_conditions=pd["required_conditions"],
                decision_reasoning=pd["reasoning"],
                legislative_basis=pd["legislative_basis"]
            )

        return IntegratedRule(
            id=f"integrated:{legislation_rule.id}",
            primary_decision=primary_decision,
            decision_rules=legislation_rule.decision_rules,
            dpv_hasProcessing=dpv_elements.get("hasProcessing", []),
            dpv_hasPurpose=dpv_elements.get("hasPurpose", []),
            dpv_hasPersonalData=dpv_elements.get("hasPersonalData", []),
            dpv_hasDataController=dpv_elements.get("hasDataController"),
            dpv_hasDataProcessor=dpv_elements.get("hasDataProcessor"),
            dpv_hasLocation=dpv_elements.get("hasLocation", []),
            dpv_hasRuleAction=dpv_elements.get("hasRuleAction", []),
            dpv_hasUserAction=dpv_elements.get("hasUserAction", []),
            dpv_hasDecisionAction=dpv_elements.get("hasDecisionAction", []),
            odrl_permission=odrl_elements.get("permission", []),
            odrl_prohibition=odrl_elements.get("prohibition", []),
            odrl_obligation=odrl_elements.get("obligation", []),
            odre_enforcement_mode="decision_based",
            odre_decision_inference=True,
            source_document_levels=source_levels,
            chunk_references=chunk_refs,
            source_legislation=legislation_rule.source_file,
            source_article=legislation_rule.source_article,
            confidence_score=legislation_rule.confidence_score
        )

    def integrated_to_json_rules(self, integrated_rule: IntegratedRule) -> Dict[str, Any]:
        """Convert integrated rule back to JSON rules format (if needed) with decision information."""
        
        decision_info = {}
        if integrated_rule.primary_decision:
            decision_info = {
                "primary_decision": {
                    "decision": integrated_rule.primary_decision.decision.value,
                    "context": integrated_rule.primary_decision.context.value,
                    "confidence": integrated_rule.primary_decision.confidence,
                    "required_actions": [action.value for action in integrated_rule.primary_decision.required_actions],
                    "reasoning": integrated_rule.primary_decision.decision_reasoning
                }
            }
        
        decision_rules_info = []
        for rule in integrated_rule.decision_rules:
            decision_rules_info.append({
                "id": rule.id,
                "question": rule.question,
                "context": rule.context.value,
                "default_decision": rule.default_decision.value,
                "requirements_for_maybe": [req.value for req in rule.requirements_for_maybe]
            })
        
        return {
            "id": integrated_rule.id.replace("integrated:", ""),
            "source_legislation": integrated_rule.source_legislation,
            "source_article": integrated_rule.source_article,
            "decision_capabilities": {
                **decision_info,
                "decision_rules": decision_rules_info
            },
            "dpv_elements": {
                "processing": integrated_rule.dpv_hasProcessing,
                "purpose": integrated_rule.dpv_hasPurpose,
                "personal_data": integrated_rule.dpv_hasPersonalData,
                "rule_actions": integrated_rule.dpv_hasRuleAction,
                "user_actions": integrated_rule.dpv_hasUserAction,
                "decision_actions": integrated_rule.dpv_hasDecisionAction
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