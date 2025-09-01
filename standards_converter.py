"""
Standards converter for DPV+ODRL+ODRE integration.
Converts JSON Rules Engine format to W3C standards-compliant formats.
"""

import logging
import urllib.parse
from typing import Dict, Any, List

from .config import Config
from .models import LegislationRule, IntegratedRule, DataRole, DataCategory, DataDomain

logger = logging.getLogger(__name__)

class DPVConcepts:
    """DPV (Data Privacy Vocabulary) concept mappings and utilities."""
    
    # DPV Core Namespaces
    DPV = Config.DPV_NAMESPACE
    DPV_PD = "https://w3id.org/dpv/dpv-pd#"
    DPV_LEGAL = "https://w3id.org/dpv/legal/"
    DPV_TECH = "https://w3id.org/dpv/tech#"
    
    # DPV Core Concepts
    PROCESSING_PURPOSES = {
        "service_provision": f"{DPV}ServiceProvision",
        "marketing": f"{DPV}Marketing", 
        "analytics": f"{DPV}Analytics",
        "compliance": f"{DPV}LegalCompliance",
        "research": f"{DPV}Research",
        "security": f"{DPV}ServiceSecurity"
    }
    
    PROCESSING_OPERATIONS = {
        "collect": f"{DPV}Collect",
        "store": f"{DPV}Store", 
        "use": f"{DPV}Use",
        "share": f"{DPV}Share",
        "transfer": f"{DPV}Transfer",
        "delete": f"{DPV}Erase"
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
    
    LEGAL_BASIS = {
        "consent": f"{DPV}Consent",
        "contract": f"{DPV}Contract", 
        "legal_obligation": f"{DPV}LegalObligation",
        "vital_interests": f"{DPV}VitalInterests",
        "public_task": f"{DPV}PublicTask",
        "legitimate_interests": f"{DPV}LegitimateInterests"
    }
    
    ROLES = {
        "controller": f"{DPV}DataController",
        "processor": f"{DPV}DataProcessor",
        "joint_controller": f"{DPV}JointDataControllers"
    }
    
    TECHNICAL_MEASURES = {
        "encryption": f"{DPV_TECH}Encryption",
        "access_control": f"{DPV_TECH}AccessControl",
        "anonymisation": f"{DPV_TECH}Anonymisation",
        "pseudonymisation": f"{DPV_TECH}Pseudonymisation"
    }

class ODREFramework:
    """ODRE (Open Digital Rights Enforcement) Framework - Unified DPV+ODRL Integration."""
    
    ODRE_NAMESPACE = Config.ODRE_NAMESPACE
    
    @staticmethod
    def create_integrated_policy(legislation_rule: LegislationRule, dpv_elements: Dict[str, Any], odrl_elements: Dict[str, Any]) -> IntegratedRule:
        """Create integrated DPV+ODRL+ODRE policy from legislation rule."""
        
        integrated_rule = IntegratedRule(
            id=f"odre:{legislation_rule.id}",
            
            # DPV elements
            dpv_hasProcessing=dpv_elements.get("hasProcessing", []),
            dpv_hasPurpose=dpv_elements.get("hasPurpose", []),
            dpv_hasPersonalData=dpv_elements.get("hasPersonalData", []),
            dpv_hasDataController=dpv_elements.get("hasDataController"),
            dpv_hasDataProcessor=dpv_elements.get("hasDataProcessor"),
            dpv_hasLegalBasis=dpv_elements.get("hasLegalBasis"),
            dpv_hasTechnicalMeasure=dpv_elements.get("hasTechnicalMeasure", []),
            dpv_hasOrganisationalMeasure=dpv_elements.get("hasOrganisationalMeasure", []),
            dpv_hasLocation=dpv_elements.get("hasLocation", []),
            dpv_hasRecipient=dpv_elements.get("hasRecipient", []),
            
            # ODRL elements
            odrl_permission=odrl_elements.get("permission", []),
            odrl_prohibition=odrl_elements.get("prohibition", []),
            odrl_obligation=odrl_elements.get("obligation", []),
            odrl_profile=odrl_elements.get("profile"),
            odrl_conflict=odrl_elements.get("conflict"),
            
            # ODRE enforcement
            odre_temporal_enforcement=ODREFramework._has_temporal_constraints(odrl_elements),
            
            # Metadata
            source_legislation=legislation_rule.source_file,
            source_article=legislation_rule.source_article,
            confidence_score=legislation_rule.confidence_score
        )
        
        return integrated_rule
    
    @staticmethod
    def _has_temporal_constraints(odrl_elements: Dict[str, Any]) -> bool:
        """Check if ODRL elements have temporal constraints."""
        all_rules = (odrl_elements.get("permission", []) + 
                    odrl_elements.get("prohibition", []) + 
                    odrl_elements.get("obligation", []))
        
        for rule in all_rules:
            if "constraint" in rule:
                for constraint in rule["constraint"]:
                    if constraint.get("leftOperand") in ["dateTime", "date", "time"]:
                        return True
        return False

class StandardsConverter:
    """Converts between JSON Rules Engine and integrated DPV+ODRL+ODRE format."""
    
    def __init__(self):
        self.dpv_concepts = DPVConcepts()
        self.odre_framework = ODREFramework()
        self._conversion_cache: Dict[str, IntegratedRule] = {}
    
    def _safe_uri_encode(self, text: str) -> str:
        """Safely encode text for use in URIs, handling special characters."""
        if not text:
            return ""
        # URL encode the text, keeping only safe characters for URIs
        return urllib.parse.quote(text, safe='')
    
    def json_rules_to_integrated(self, legislation_rule: LegislationRule) -> IntegratedRule:
        """Convert JSON Rules Engine rule to integrated DPV+ODRL+ODRE format."""
        
        # Check cache first
        cache_key = f"{legislation_rule.id}_{legislation_rule.extracted_at}"
        if cache_key in self._conversion_cache:
            return self._conversion_cache[cache_key]
        
        try:
            # Extract DPV elements
            dpv_elements = self._extract_dpv_elements(legislation_rule)
            
            # Extract ODRL elements with proper URI encoding
            odrl_elements = self._extract_odrl_elements(legislation_rule)
            
            # Create integrated rule using ODRE framework
            integrated_rule = self.odre_framework.create_integrated_policy(
                legislation_rule, dpv_elements, odrl_elements
            )
            
            # Cache the result
            self._conversion_cache[cache_key] = integrated_rule
            
            logger.debug(f"Converted rule to integrated format: {legislation_rule.id}")
            return integrated_rule
            
        except Exception as e:
            logger.error(f"Error converting rule {legislation_rule.id} to integrated format: {e}")
            raise
    
    def batch_convert_rules(self, legislation_rules: List[LegislationRule]) -> List[IntegratedRule]:
        """Convert multiple rules to integrated format efficiently."""
        integrated_rules = []
        
        for rule in legislation_rules:
            try:
                integrated_rule = self.json_rules_to_integrated(rule)
                integrated_rules.append(integrated_rule)
            except Exception as e:
                logger.error(f"Skipping rule {rule.id} during batch conversion: {e}")
                continue
        
        logger.info(f"Batch converted {len(integrated_rules)}/{len(legislation_rules)} rules")
        return integrated_rules
    
    def _extract_dpv_elements(self, legislation_rule: LegislationRule) -> Dict[str, Any]:
        """Extract DPV elements from legislation rule."""
        
        # Map data categories to DPV personal data concepts
        dpv_personal_data = []
        for category in legislation_rule.data_category:
            category_value = category.value if hasattr(category, 'value') else str(category)
            if category_value in self.dpv_concepts.DATA_CATEGORIES:
                dpv_personal_data.append(self.dpv_concepts.DATA_CATEGORIES[category_value])
        
        # Map processing operations from rule conditions
        dpv_processing = []
        for logic_type, conditions in legislation_rule.conditions.items():
            for condition in conditions:
                fact_lower = condition.fact.lower()
                if "collect" in fact_lower:
                    dpv_processing.append(self.dpv_concepts.PROCESSING_OPERATIONS["collect"])
                elif "store" in fact_lower:
                    dpv_processing.append(self.dpv_concepts.PROCESSING_OPERATIONS["store"])
                elif "use" in fact_lower:
                    dpv_processing.append(self.dpv_concepts.PROCESSING_OPERATIONS["use"])
                elif "share" in fact_lower:
                    dpv_processing.append(self.dpv_concepts.PROCESSING_OPERATIONS["share"])
                elif "transfer" in fact_lower:
                    dpv_processing.append(self.dpv_concepts.PROCESSING_OPERATIONS["transfer"])
        
        # Map purposes based on rule description and event type
        dpv_purposes = []
        rule_text = f"{legislation_rule.description} {legislation_rule.event.type}".lower()
        if "service" in rule_text or "provision" in rule_text:
            dpv_purposes.append(self.dpv_concepts.PROCESSING_PURPOSES["service_provision"])
        elif "compliance" in rule_text or "legal" in rule_text:
            dpv_purposes.append(self.dpv_concepts.PROCESSING_PURPOSES["compliance"])
        elif "security" in rule_text:
            dpv_purposes.append(self.dpv_concepts.PROCESSING_PURPOSES["security"])
        
        # Map roles
        controller = None
        processor = None
        
        if legislation_rule.primary_impacted_role:
            primary_role_value = legislation_rule.primary_impacted_role.value if hasattr(legislation_rule.primary_impacted_role, 'value') else str(legislation_rule.primary_impacted_role)
            
            if primary_role_value == "controller":
                controller = self.dpv_concepts.ROLES["controller"]
            elif primary_role_value == "processor":
                processor = self.dpv_concepts.ROLES["processor"]
            elif primary_role_value == "joint_controller":
                controller = self.dpv_concepts.ROLES["joint_controller"]
        
        # Map countries to DPV location concepts with proper encoding
        dpv_locations = []
        for country in legislation_rule.applicable_countries:
            encoded_country = self._safe_uri_encode(country.replace(' ', '_'))
            dpv_locations.append(f"dpv:Country_{encoded_country}")
        
        # Identify technical and organizational measures from rule content
        tech_measures = self._extract_technical_measures(legislation_rule)
        org_measures = self._extract_organizational_measures(legislation_rule)
        
        return {
            "hasProcessing": dpv_processing,
            "hasPurpose": dpv_purposes,
            "hasPersonalData": dpv_personal_data,
            "hasDataController": controller,
            "hasDataProcessor": processor,
            "hasLegalBasis": self.dpv_concepts.LEGAL_BASIS["legal_obligation"],
            "hasTechnicalMeasure": tech_measures,
            "hasOrganisationalMeasure": org_measures,
            "hasLocation": dpv_locations,
            "hasRecipient": []
        }
    
    def _extract_technical_measures(self, legislation_rule: LegislationRule) -> List[str]:
        """Extract technical measures from rule content."""
        measures = []
        rule_text = f"{legislation_rule.description} {legislation_rule.event.type}".lower()
        
        if "encrypt" in rule_text:
            measures.append(self.dpv_concepts.TECHNICAL_MEASURES["encryption"])
        if "access control" in rule_text or "authorization" in rule_text:
            measures.append(self.dpv_concepts.TECHNICAL_MEASURES["access_control"])
        if "anonymis" in rule_text or "anonymiz" in rule_text:
            measures.append(self.dpv_concepts.TECHNICAL_MEASURES["anonymisation"])
        if "pseudonym" in rule_text:
            measures.append(self.dpv_concepts.TECHNICAL_MEASURES["pseudonymisation"])
        
        return measures
    
    def _extract_organizational_measures(self, legislation_rule: LegislationRule) -> List[str]:
        """Extract organizational measures from rule content."""
        measures = []
        rule_text = f"{legislation_rule.description} {legislation_rule.event.type}".lower()
        
        # Add organizational measures based on content analysis
        if "training" in rule_text or "awareness" in rule_text:
            measures.append(f"{self.dpv_concepts.DPV}StaffTraining")
        if "policy" in rule_text or "procedure" in rule_text:
            measures.append(f"{self.dpv_concepts.DPV}DataProcessingPolicy")
        if "audit" in rule_text or "review" in rule_text:
            measures.append(f"{self.dpv_concepts.DPV}AuditProcedure")
        
        return measures
    
    def _extract_odrl_elements(self, legislation_rule: LegislationRule) -> Dict[str, Any]:
        """Extract ODRL elements from legislation rule with proper URI encoding."""
        
        # Create ODRL rules based on rule type and conditions
        permissions = []
        prohibitions = []
        obligations = []
        
        # Analyze rule to determine ODRL rule type
        rule_description = legislation_rule.description.lower()
        event_type = legislation_rule.event.type.lower()
        
        if "prohibit" in rule_description or "forbid" in event_type or "not" in event_type:
            prohibition = self._create_odrl_rule(legislation_rule, "prohibition")
            prohibitions.append(prohibition)
        elif "require" in rule_description or "must" in rule_description or "obligation" in event_type:
            obligation = self._create_odrl_rule(legislation_rule, "obligation")
            obligations.append(obligation)
        else:
            permission = self._create_odrl_rule(legislation_rule, "permission")
            permissions.append(permission)
        
        # Properly encode the source file for URI use
        encoded_source_file = self._safe_uri_encode(legislation_rule.source_file)
        
        return {
            "permission": permissions,
            "prohibition": prohibitions,
            "obligation": obligations,
            "profile": f"urn:profile:legislation:{encoded_source_file}",
            "conflict": self._determine_conflict_strategy(legislation_rule)
        }
    
    def _create_odrl_rule(self, legislation_rule: LegislationRule, rule_type: str) -> Dict[str, Any]:
        """Create individual ODRL rule from legislation rule with proper URI encoding."""
        
        # Properly encode the source file and rule ID for URI use
        encoded_source_file = self._safe_uri_encode(legislation_rule.source_file)
        encoded_rule_id = self._safe_uri_encode(legislation_rule.id)
        
        # Determine target asset with encoded components
        target = f"urn:asset:{encoded_source_file}:{encoded_rule_id}"
        
        # Determine action based on data domains
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
        
        if not actions:
            actions = ["use"]  # Default action
        
        # Create constraints from rule conditions
        constraints = []
        for logic_type, conditions in legislation_rule.conditions.items():
            for condition in conditions:
                operator_value = condition.operator.value if hasattr(condition.operator, 'value') else str(condition.operator)
                odrl_constraint = {
                    "leftOperand": self._map_fact_to_odrl_operand(condition.fact),
                    "operator": self._map_operator_to_odrl(operator_value),
                    "rightOperand": condition.value,
                    "comment": condition.description
                }
                constraints.append(odrl_constraint)
        
        # Determine assignee based on roles
        assignee = None
        if legislation_rule.primary_impacted_role:
            primary_role_value = legislation_rule.primary_impacted_role.value if hasattr(legislation_rule.primary_impacted_role, 'value') else str(legislation_rule.primary_impacted_role)
            
            if primary_role_value == "controller":
                assignee = "urn:party:data_controller"
            elif primary_role_value == "processor":
                assignee = "urn:party:data_processor"
        
        rule = {
            "target": target,
            "action": actions[0] if len(actions) == 1 else actions,
            "constraint": constraints,
            "duty": self._create_duties_from_rule(legislation_rule)
        }
        
        if assignee:
            rule["assignee"] = assignee
        
        return rule
    
    def _create_duties_from_rule(self, legislation_rule: LegislationRule) -> List[Dict[str, Any]]:
        """Create ODRL duties from legislation rule."""
        duties = []
        rule_text = f"{legislation_rule.description} {legislation_rule.event.type}".lower()
        
        # Common duties based on rule content
        if "notify" in rule_text or "inform" in rule_text:
            duties.append({
                "action": "notify",
                "constraint": []
            })
        
        if "document" in rule_text or "record" in rule_text:
            duties.append({
                "action": "document",
                "constraint": []
            })
        
        if "delete" in rule_text or "erase" in rule_text:
            duties.append({
                "action": "delete",
                "constraint": [
                    {
                        "leftOperand": "event",
                        "operator": "eq",
                        "rightOperand": "dataSubjectRequest"
                    }
                ]
            })
        
        return duties
    
    def _determine_conflict_strategy(self, legislation_rule: LegislationRule) -> str:
        """Determine ODRL conflict resolution strategy."""
        if legislation_rule.priority >= 8:
            return "prohibit"  # High priority rules should prohibit by default
        elif legislation_rule.priority <= 3:
            return "permit"   # Low priority rules should permit by default
        else:
            return "invalid"  # Medium priority rules make the policy invalid on conflict
    
    def _map_fact_to_odrl_operand(self, fact: str) -> str:
        """Map JSON rules engine fact to ODRL left operand."""
        fact_lower = fact.lower()
        
        if "date" in fact_lower or "time" in fact_lower:
            return "dateTime"
        elif "location" in fact_lower or "country" in fact_lower:
            return "spatial"
        elif "count" in fact_lower or "number" in fact_lower:
            return "count"
        elif "user" in fact_lower or "party" in fact_lower:
            return "party"
        elif "purpose" in fact_lower:
            return "purpose"
        elif "data" in fact_lower and "type" in fact_lower:
            return "dataCategory"
        else:
            return f"custom:{self._safe_uri_encode(fact)}"
    
    def _map_operator_to_odrl(self, operator: str) -> str:
        """Map JSON rules engine operator to ODRL operator."""
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
    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """Get conversion statistics."""
        return {
            "cache_size": len(self._conversion_cache),
            "dpv_concepts_available": len(self.dpv_concepts.DATA_CATEGORIES),
            "processing_operations": len(self.dpv_concepts.PROCESSING_OPERATIONS),
            "legal_basis_options": len(self.dpv_concepts.LEGAL_BASIS)
        }
    
    def clear_cache(self) -> None:
        """Clear the conversion cache."""
        self._conversion_cache.clear()
        logger.info("Standards conversion cache cleared")
    
    def validate_integration(self, integrated_rule: IntegratedRule) -> Dict[str, Any]:
        """Validate an integrated rule for standards compliance."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "dpv_compliant": True,
            "odrl_compliant": True,
            "odre_compliant": True
        }
        
        # Check DPV compliance
        if not integrated_rule.dpv_hasProcessing:
            validation["warnings"].append("No DPV processing operations specified")
        
        if not integrated_rule.dpv_hasPurpose:
            validation["warnings"].append("No DPV purposes specified")
        
        # Check ODRL compliance
        total_rules = (len(integrated_rule.odrl_permission) + 
                      len(integrated_rule.odrl_prohibition) + 
                      len(integrated_rule.odrl_obligation))
        
        if total_rules == 0:
            validation["errors"].append("No ODRL rules specified")
            validation["odrl_compliant"] = False
            validation["valid"] = False
        
        # Check ODRE compliance
        if not integrated_rule.odre_enforceable:
            validation["warnings"].append("Rule is not marked as enforceable")
        
        return validation