"""
Rule models and extraction results for the legislation rules converter.
CORRECTED VERSION with complete RDF/JSON-LD generation from original code.
"""
import json
import os
import csv
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging

from .enums import DataRole, DataCategory, DocumentLevel
from .base_models import RuleCondition, RuleEvent, RuleAction, UserAction, IntegratedRule

logger = logging.getLogger(__name__)

# Optional RDF imports
try:
    import rdflib
    from rdflib import Graph, Namespace, URIRef, Literal, BNode
    from rdflib.namespace import RDF, RDFS, XSD
    RDF_AVAILABLE = True
except ImportError:
    RDF_AVAILABLE = False


class LegislationRule(BaseModel):
    """Complete rule structure aligned with json-rules-engine format."""
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Human-readable rule description")
    source_article: str = Field(..., description="Source legislation article/section")
    source_file: str = Field(..., description="Source PDF filename")

    conditions: Dict[str, List[RuleCondition]] = Field(
        ..., 
        description="Rule conditions with 'all', 'any', or 'not' logic"
    )
    event: RuleEvent = Field(..., description="Event triggered when conditions are met")

    # Actions - Now optional to allow inference
    actions: List[RuleAction] = Field(default_factory=list, description="Actions inferred from legislative text")
    user_actions: List[UserAction] = Field(default_factory=list, description="User-specific actions inferred from legislation")

    priority: int = Field(default=1, description="Rule priority (1-10)")

    # Required fields with validation
    primary_impacted_role: Optional[DataRole] = Field(None, description="Primary role most impacted by this rule")
    secondary_impacted_role: Optional[DataRole] = Field(None, description="Secondary role impacted by this rule")
    data_category: List[DataCategory] = Field(default_factory=list, description="Categories of data this rule applies to")

    # Updated country metadata structure
    applicable_countries: List[str] = Field(..., description="Countries where this rule applies")
    adequacy_countries: List[str] = Field(default_factory=list, description="Adequacy countries")

    # Document levels processed
    source_documents: Dict[str, Optional[str]] = Field(default_factory=dict, description="Source documents by level")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata including chunking info")

    # Metadata
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_method: str = Field(default="llm_analysis_with_inferred_actions")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")

    @field_validator('conditions', mode='after')
    @classmethod
    def validate_conditions_structure(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Conditions must be a dictionary")
        valid_keys = {'all', 'any', 'not'}
        if not any(key in valid_keys for key in v.keys()):
            raise ValueError("Conditions must contain 'all', 'any', or 'not' keys")
        return v

    @field_validator('actions', mode='after')
    @classmethod
    def validate_actions_optional(cls, v):
        return v if v is not None else []

    @field_validator('primary_impacted_role', mode='before')
    @classmethod
    def validate_primary_role(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return DataRole(v)
            except ValueError:
                return None
        elif isinstance(v, DataRole):
            return v
        return None

    @field_validator('secondary_impacted_role', mode='before')
    @classmethod
    def validate_secondary_role(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return DataRole(v)
            except ValueError:
                return None
        elif isinstance(v, DataRole):
            return v
        return None

    @field_validator('data_category', mode='before')
    @classmethod
    def validate_data_category(cls, v):
        if not v:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, str):
                    try:
                        result.append(DataCategory(item))
                    except ValueError:
                        continue
                elif isinstance(item, DataCategory):
                    result.append(item)
            return result
        return []


class ExtractionResult(BaseModel):
    """Complete result of legislation analysis."""

    rules: List[LegislationRule] = Field(..., description="Extracted rules")
    summary: str = Field(..., description="Summary of extraction")
    total_rules: int = Field(..., description="Total number of rules extracted")
    total_actions: int = Field(default=0, description="Total number of rule actions extracted")
    total_user_actions: int = Field(default=0, description="Total number of user actions extracted")
    processing_time: float = Field(..., description="Processing time in seconds")
    embeddings: Optional[List[List[float]]] = Field(None, description="Rule embeddings")

    # Integrated standards output
    integrated_rules: List[IntegratedRule] = Field(default_factory=list, description="Integrated standards rules")

    # Processing metadata
    documents_processed: Dict[str, List[str]] = Field(default_factory=dict, description="Documents processed by level")
    chunking_metadata: Dict[str, Any] = Field(default_factory=dict, description="Information about document chunking")

    def save_json(self, filepath: str):
        """Save rules to JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                [rule.model_dump() for rule in self.rules], 
                f, 
                indent=2, 
                default=str,
                ensure_ascii=False
            )

    def save_integrated_json(self, filepath: str):
        """Save integrated rules to JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                [rule.model_dump() for rule in self.integrated_rules],
                f,
                indent=2,
                default=str,
                ensure_ascii=False
            )

    def save_integrated_ttl(self, filepath: str):
        """Save integrated rules in TTL format."""
        if not RDF_AVAILABLE:
            print(f"Warning: Cannot generate TTL file - rdflib not available")
            return

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        turtle_content = self._generate_turtle_with_rdflib()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(turtle_content)

    def save_integrated_jsonld(self, filepath: str):
        """Save integrated rules in JSON-LD format."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        jsonld_content = self._generate_jsonld()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(jsonld_content, f, indent=2, ensure_ascii=False)

    def save_csv(self, filepath: str):
        """Save extraction results to a comprehensive CSV file with robust error handling - COMPLETE VERSION."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            print(f"   Attempting to save CSV to: {filepath}")
            print(f"   Number of rules to save: {len(self.rules)}")

            if not self.rules:
                print(f"   Warning: No rules to save to CSV")
                # Create empty CSV with headers
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'id', 'rule_name', 'rule_description', 'primary_impacted_role', 
                        'secondary_impacted_role', 'data_category', 'applicable_countries', 
                        'adequacy_countries', 'conditions_logic_type', 'count_of_conditions', 
                        'details_of_conditions', 'rule_actions', 'user_actions', 
                        'source_article', 'source_file'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                print(f"   Empty CSV file created: {filepath}")
                return

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'id', 'rule_name', 'rule_description', 'primary_impacted_role', 
                    'secondary_impacted_role', 'data_category', 'applicable_countries', 
                    'adequacy_countries', 'conditions_logic_type', 'count_of_conditions', 
                    'details_of_conditions', 'rule_actions', 'user_actions', 
                    'source_article', 'source_file'
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                saved_count = 0
                for rule in self.rules:
                    try:
                        # Handle enum values and lists safely with individual error handling
                        primary_role = ''
                        if rule.primary_impacted_role:
                            try:
                                primary_role = rule.primary_impacted_role.value if hasattr(rule.primary_impacted_role, 'value') else str(rule.primary_impacted_role)
                            except:
                                primary_role = str(rule.primary_impacted_role)

                        secondary_role = ''
                        if rule.secondary_impacted_role:
                            try:
                                secondary_role = rule.secondary_impacted_role.value if hasattr(rule.secondary_impacted_role, 'value') else str(rule.secondary_impacted_role)
                            except:
                                secondary_role = str(rule.secondary_impacted_role)

                        data_cats = ''
                        try:
                            data_cats = '; '.join([cat.value if hasattr(cat, 'value') else str(cat) for cat in rule.data_category])
                        except Exception as e:
                            data_cats = f"Error processing data categories: {e}"

                        # Process conditions with comprehensive error handling
                        conditions_logic = ''
                        total_conditions = 0
                        conditions_detail_text = ''

                        try:
                            conditions_logic = '; '.join(rule.conditions.keys())
                            total_conditions = sum(len(conditions) for conditions in rule.conditions.values())

                            # Create detailed conditions description
                            condition_details = []
                            for logic_type, conditions in rule.conditions.items():
                                for i, condition in enumerate(conditions, 1):
                                    try:
                                        operator_val = condition.operator.value if hasattr(condition.operator, 'value') else str(condition.operator)
                                        role_val = 'none'
                                        if condition.role:
                                            role_val = condition.role.value if hasattr(condition.role, 'value') else str(condition.role)

                                        domains = 'none'
                                        try:
                                            domain_list = [d.value if hasattr(d, 'value') else str(d) for d in condition.data_domain]
                                            domains = ', '.join(domain_list) if domain_list else 'none'
                                        except:
                                            domains = 'none'

                                        detail = f"[{logic_type.upper()}-{i}] {condition.fact} {operator_val} {condition.value} (Role: {role_val}, Domains: {domains}) - {condition.description}"
                                        condition_details.append(detail)
                                    except Exception as e:
                                        condition_details.append(f"[{logic_type.upper()}-{i}] Error processing condition: {e}")

                            conditions_detail_text = ' | '.join(condition_details)
                        except Exception as e:
                            conditions_detail_text = f"Error processing conditions: {e}"

                        # Process rule actions with error handling
                        rule_actions_text = 'None'
                        try:
                            rule_action_details = []
                            for action in rule.actions:
                                try:
                                    detail = f"[{action.action_type}] {action.title}: {action.description} (Priority: {action.priority}, Confidence: {action.confidence_score:.2f})"
                                    rule_action_details.append(detail)
                                except Exception as e:
                                    rule_action_details.append(f"Error processing action: {e}")

                            rule_actions_text = ' | '.join(rule_action_details) if rule_action_details else 'None'
                        except Exception as e:
                            rule_actions_text = f"Error processing rule actions: {e}"

                        # Process user actions with error handling
                        user_actions_text = 'None'
                        try:
                            user_action_details = []
                            for action in rule.user_actions:
                                try:
                                    detail = f"[{action.action_type}] {action.title}: {action.description} (Priority: {action.priority}, Confidence: {action.confidence_score:.2f})"
                                    user_action_details.append(detail)
                                except Exception as e:
                                    user_action_details.append(f"Error processing user action: {e}")

                            user_actions_text = ' | '.join(user_action_details) if user_action_details else 'None'
                        except Exception as e:
                            user_actions_text = f"Error processing user actions: {e}"

                        # Create row with error handling for each field
                        row = {
                            'id': str(rule.id),
                            'rule_name': str(rule.name),
                            'rule_description': str(rule.description),
                            'primary_impacted_role': primary_role,
                            'secondary_impacted_role': secondary_role,
                            'data_category': data_cats,
                            'applicable_countries': '; '.join(rule.applicable_countries) if rule.applicable_countries else '',
                            'adequacy_countries': '; '.join(rule.adequacy_countries) if rule.adequacy_countries else '',
                            'conditions_logic_type': conditions_logic,
                            'count_of_conditions': total_conditions,
                            'details_of_conditions': conditions_detail_text,
                            'rule_actions': rule_actions_text,
                            'user_actions': user_actions_text,
                            'source_article': str(rule.source_article),
                            'source_file': str(rule.source_file)
                        }
                        writer.writerow(row)
                        saved_count += 1

                    except Exception as e:
                        logger.error(f"Error processing rule {rule.id} for CSV: {e}")
                        print(f"   Error processing rule {rule.id}: {e}")
                        continue

            print(f"   CSV Rules with Dual Actions saved: {filepath}")
            print(f"   Successfully saved {saved_count} out of {len(self.rules)} rules to CSV")

        except Exception as e:
            logger.error(f"Error saving CSV file: {e}")
            print(f"   Error saving CSV file: {e}")
            import traceback
            traceback.print_exc()

    def _generate_turtle_with_rdflib(self) -> str:
        """Generate Turtle RDF representation with complete rule information and decision trees - COMPLETE VERSION."""
        if not RDF_AVAILABLE:
            return "# Error: rdflib not available for TTL generation"

        from ..config import Config

        g = Graph()

        # Define namespaces with updated v2.1 URIs
        DPV = Namespace(Config.DPV_NAMESPACE)
        DPV_PD = Namespace(Config.DPV_PD_NAMESPACE)
        DPV_ACTION = Namespace(Config.ACTION_NAMESPACE)
        ODRL = Namespace(Config.ODRL_NAMESPACE)
        ODRE = Namespace("https://w3id.org/def/odre#")
        RULES = Namespace("https://w3id.org/legislation-rules#")

        # Bind namespaces
        g.bind("dpv", DPV)
        g.bind("dpv-pd", DPV_PD)
        g.bind("dpv-action", DPV_ACTION)
        g.bind("odrl", ODRL)
        g.bind("odre", ODRE)
        g.bind("rules", RULES)
        g.bind("rdf", RDF)
        g.bind("rdfs", RDFS)
        g.bind("xsd", XSD)

        # Process both original rules and integrated rules for complete coverage
        for rule in self.rules:
            rule_id_encoded = urllib.parse.quote(rule.id, safe=':/')
            rule_uri = URIRef(f"urn:rule:{rule_id_encoded}")

            # Core rule information
            g.add((rule_uri, RDF.type, RULES.LegislationRule))
            g.add((rule_uri, RDFS.label, Literal(rule.name)))
            g.add((rule_uri, RULES.description, Literal(rule.description)))
            g.add((rule_uri, RULES.sourceArticle, Literal(rule.source_article)))
            g.add((rule_uri, RULES.sourceFile, Literal(rule.source_file)))
            g.add((rule_uri, RULES.priority, Literal(rule.priority, datatype=XSD.integer)))
            g.add((rule_uri, RULES.confidenceScore, Literal(rule.confidence_score, datatype=XSD.float)))

            # Roles
            if rule.primary_impacted_role:
                primary_role_val = rule.primary_impacted_role.value if hasattr(rule.primary_impacted_role, 'value') else str(rule.primary_impacted_role)
                g.add((rule_uri, RULES.primaryImpactedRole, Literal(primary_role_val)))

            if rule.secondary_impacted_role:
                secondary_role_val = rule.secondary_impacted_role.value if hasattr(rule.secondary_impacted_role, 'value') else str(rule.secondary_impacted_role)
                g.add((rule_uri, RULES.secondaryImpactedRole, Literal(secondary_role_val)))

            # Data categories
            for category in rule.data_category:
                category_val = category.value if hasattr(category, 'value') else str(category)
                g.add((rule_uri, RULES.dataCategory, Literal(category_val)))

            # Countries
            for country in rule.applicable_countries:
                g.add((rule_uri, RULES.applicableCountry, Literal(country)))

            for country in rule.adequacy_countries:
                g.add((rule_uri, RULES.adequacyCountry, Literal(country)))

            # Conditions with full decision tree logic
            for logic_type, conditions in rule.conditions.items():
                # Create a decision tree node for each logic type
                logic_uri = URIRef(f"urn:rule:{rule_id_encoded}:logic:{logic_type}")
                g.add((rule_uri, RULES.hasDecisionLogic, logic_uri))
                g.add((logic_uri, RDF.type, RULES.DecisionLogic))
                g.add((logic_uri, RULES.logicType, Literal(logic_type)))

                for i, condition in enumerate(conditions):
                    condition_uri = URIRef(f"urn:rule:{rule_id_encoded}:condition:{logic_type}:{i}")
                    g.add((logic_uri, RULES.hasCondition, condition_uri))
                    g.add((condition_uri, RDF.type, RULES.RuleCondition))
                    g.add((condition_uri, RULES.fact, Literal(condition.fact)))

                    operator_val = condition.operator.value if hasattr(condition.operator, 'value') else str(condition.operator)
                    g.add((condition_uri, RULES.operator, Literal(operator_val)))
                    g.add((condition_uri, RULES.value, Literal(str(condition.value))))
                    g.add((condition_uri, RULES.description, Literal(condition.description)))
                    g.add((condition_uri, RULES.reasoning, Literal(condition.reasoning)))

                    if condition.role:
                        role_val = condition.role.value if hasattr(condition.role, 'value') else str(condition.role)
                        g.add((condition_uri, RULES.role, Literal(role_val)))

                    # Data domains
                    for domain in condition.data_domain:
                        domain_val = domain.value if hasattr(domain, 'value') else str(domain)
                        g.add((condition_uri, RULES.dataDomain, Literal(domain_val)))

                    # Document metadata
                    level_val = condition.document_level.value if hasattr(condition.document_level, 'value') else str(condition.document_level)
                    g.add((condition_uri, RULES.documentLevel, Literal(level_val)))

                    if condition.chunk_reference:
                        g.add((condition_uri, RULES.chunkReference, Literal(condition.chunk_reference)))

            # Rule Actions
            for i, action in enumerate(rule.actions):
                action_uri = URIRef(f"urn:rule:{rule_id_encoded}:action:{i}")
                g.add((rule_uri, RULES.hasRuleAction, action_uri))
                g.add((action_uri, RDF.type, RULES.RuleAction))
                g.add((action_uri, RULES.actionType, Literal(action.action_type)))
                g.add((action_uri, RULES.title, Literal(action.title)))
                g.add((action_uri, RULES.description, Literal(action.description)))
                g.add((action_uri, RULES.priority, Literal(action.priority)))
                g.add((action_uri, RULES.legislativeRequirement, Literal(action.legislative_requirement)))
                g.add((action_uri, RULES.dataImpact, Literal(action.data_impact)))
                g.add((action_uri, RULES.confidenceScore, Literal(action.confidence_score, datatype=XSD.float)))

                # Data specific steps
                for step in action.data_specific_steps:
                    g.add((action_uri, RULES.dataSpecificStep, Literal(step)))

                # Verification methods
                for method in action.verification_method:
                    g.add((action_uri, RULES.verificationMethod, Literal(method)))

                if action.responsible_role:
                    g.add((action_uri, RULES.responsibleRole, Literal(action.responsible_role)))

                if action.timeline:
                    g.add((action_uri, RULES.timeline, Literal(action.timeline)))

            # User Actions
            for i, action in enumerate(rule.user_actions):
                action_uri = URIRef(f"urn:rule:{rule_id_encoded}:userAction:{i}")
                g.add((rule_uri, RULES.hasUserAction, action_uri))
                g.add((action_uri, RDF.type, RULES.UserAction))
                g.add((action_uri, RULES.actionType, Literal(action.action_type)))
                g.add((action_uri, RULES.title, Literal(action.title)))
                g.add((action_uri, RULES.description, Literal(action.description)))
                g.add((action_uri, RULES.priority, Literal(action.priority)))
                g.add((action_uri, RULES.legislativeRequirement, Literal(action.legislative_requirement)))
                g.add((action_uri, RULES.complianceOutcome, Literal(action.compliance_outcome)))
                g.add((action_uri, RULES.confidenceScore, Literal(action.confidence_score, datatype=XSD.float)))

                # User data steps
                for step in action.user_data_steps:
                    g.add((action_uri, RULES.userDataStep, Literal(step)))

                # Affected data categories
                for category in action.affected_data_categories:
                    g.add((action_uri, RULES.affectedDataCategory, Literal(category)))

                # User verification steps
                for step in action.user_verification_steps:
                    g.add((action_uri, RULES.userVerificationStep, Literal(step)))

                if action.user_role_context:
                    g.add((action_uri, RULES.userRoleContext, Literal(action.user_role_context)))

                if action.timeline:
                    g.add((action_uri, RULES.timeline, Literal(action.timeline)))

            # Event information
            g.add((rule_uri, RULES.eventType, Literal(rule.event.type)))

            # Metadata
            g.add((rule_uri, RULES.extractedAt, Literal(rule.extracted_at.isoformat(), datatype=XSD.dateTime)))
            g.add((rule_uri, RULES.extractionMethod, Literal(rule.extraction_method)))

        # Add integrated rules for semantic web properties
        for integrated_rule in self.integrated_rules:
            rule_id_encoded = urllib.parse.quote(integrated_rule.id, safe=':/')
            rule_uri = URIRef(f"urn:rule:{rule_id_encoded}")

            # ODRE Properties
            g.add((rule_uri, RDF.type, ODRE.EnforceablePolicy))
            g.add((rule_uri, RDF.type, DPV.ProcessingActivity))
            g.add((rule_uri, ODRE.enforceable, Literal(integrated_rule.odre_enforceable, datatype=XSD.boolean)))
            g.add((rule_uri, ODRE.enforcement_mode, Literal(integrated_rule.odre_enforcement_mode)))
            g.add((rule_uri, ODRE.action_inference, Literal(integrated_rule.odre_action_inference, datatype=XSD.boolean)))
            g.add((rule_uri, ODRE.user_action_inference, Literal(integrated_rule.odre_user_action_inference, datatype=XSD.boolean)))

            # DPV Properties
            for processing in integrated_rule.dpv_hasProcessing:
                g.add((rule_uri, DPV.hasProcessing, URIRef(processing)))

            for purpose in integrated_rule.dpv_hasPurpose:
                g.add((rule_uri, DPV.hasPurpose, URIRef(purpose)))

            for data in integrated_rule.dpv_hasPersonalData:
                g.add((rule_uri, DPV.hasPersonalData, URIRef(data)))

            # Rule actions
            for action in integrated_rule.dpv_hasRuleAction:
                g.add((rule_uri, DPV_ACTION.hasRuleAction, URIRef(action)))

            # User actions
            for action in integrated_rule.dpv_hasUserAction:
                g.add((rule_uri, DPV_ACTION.hasUserAction, URIRef(action)))

            if integrated_rule.dpv_hasDataController:
                g.add((rule_uri, DPV.hasDataController, URIRef(integrated_rule.dpv_hasDataController)))

            if integrated_rule.dpv_hasDataProcessor:
                g.add((rule_uri, DPV.hasDataProcessor, URIRef(integrated_rule.dpv_hasDataProcessor)))

            for location in integrated_rule.dpv_hasLocation:
                g.add((rule_uri, DPV.hasLocation, URIRef(location)))

        # Serialize to Turtle format
        turtle_output = g.serialize(format='turtle')
        if isinstance(turtle_output, bytes):
            return turtle_output.decode('utf-8')
        return turtle_output

    def _generate_jsonld(self) -> Dict[str, Any]:
        """Generate JSON-LD representation with complete rule information and decision trees - COMPLETE VERSION."""
        from ..config import Config
        
        context = {
            "@context": {
                "dpv": Config.DPV_NAMESPACE,
                "dpv-pd": Config.DPV_PD_NAMESPACE,
                "dpv-action": Config.ACTION_NAMESPACE,
                "odrl": Config.ODRL_NAMESPACE,
                "odre": "https://w3id.org/def/odre#",
                "rules": "https://w3id.org/legislation-rules#",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "xsd": "http://www.w3.org/2001/XMLSchema#"
            }
        }

        graph = []

        # Process all original rules with complete information
        for rule in self.rules:
            rule_jsonld = {
                "@id": f"urn:rule:{rule.id}",
                "@type": "rules:LegislationRule",
                "rdfs:label": rule.name,
                "rules:description": rule.description,
                "rules:sourceArticle": rule.source_article,
                "rules:sourceFile": rule.source_file,
                "rules:priority": {
                    "@value": rule.priority,
                    "@type": "xsd:integer"
                },
                "rules:confidenceScore": {
                    "@value": rule.confidence_score,
                    "@type": "xsd:float"
                }
            }

            # Roles
            if rule.primary_impacted_role:
                primary_role_val = rule.primary_impacted_role.value if hasattr(rule.primary_impacted_role, 'value') else str(rule.primary_impacted_role)
                rule_jsonld["rules:primaryImpactedRole"] = primary_role_val

            if rule.secondary_impacted_role:
                secondary_role_val = rule.secondary_impacted_role.value if hasattr(rule.secondary_impacted_role, 'value') else str(rule.secondary_impacted_role)
                rule_jsonld["rules:secondaryImpactedRole"] = secondary_role_val

            # Data categories
            data_categories = []
            for category in rule.data_category:
                category_val = category.value if hasattr(category, 'value') else str(category)
                data_categories.append(category_val)
            if data_categories:
                rule_jsonld["rules:dataCategory"] = data_categories

            # Countries
            if rule.applicable_countries:
                rule_jsonld["rules:applicableCountry"] = rule.applicable_countries

            if rule.adequacy_countries:
                rule_jsonld["rules:adequacyCountry"] = rule.adequacy_countries

            # Decision Logic and Conditions
            decision_logic = []
            for logic_type, condition_list in rule.conditions.items():
                logic_obj = {
                    "@type": "rules:DecisionLogic",
                    "rules:logicType": logic_type,
                    "rules:hasCondition": []
                }

                for i, condition in enumerate(condition_list):
                    operator_val = condition.operator.value if hasattr(condition.operator, 'value') else str(condition.operator)
                    role_val = condition.role.value if condition.role and hasattr(condition.role, 'value') else str(condition.role) if condition.role else None
                    level_val = condition.document_level.value if hasattr(condition.document_level, 'value') else str(condition.document_level)

                    condition_obj = {
                        "@type": "rules:RuleCondition",
                        "rules:fact": condition.fact,
                        "rules:operator": operator_val,
                        "rules:value": str(condition.value),
                        "rules:description": condition.description,
                        "rules:reasoning": condition.reasoning,
                        "rules:documentLevel": level_val
                    }

                    if role_val:
                        condition_obj["rules:role"] = role_val

                    if condition.chunk_reference:
                        condition_obj["rules:chunkReference"] = condition.chunk_reference

                    # Data domains
                    domains = []
                    for domain in condition.data_domain:
                        domain_val = domain.value if hasattr(domain, 'value') else str(domain)
                        domains.append(domain_val)
                    if domains:
                        condition_obj["rules:dataDomain"] = domains

                    logic_obj["rules:hasCondition"].append(condition_obj)

                decision_logic.append(logic_obj)

            if decision_logic:
                rule_jsonld["rules:hasDecisionLogic"] = decision_logic

            # Rule Actions
            rule_actions = []
            for action in rule.actions:
                action_obj = {
                    "@type": "rules:RuleAction",
                    "rules:actionType": action.action_type,
                    "rules:title": action.title,
                    "rules:description": action.description,
                    "rules:priority": action.priority,
                    "rules:legislativeRequirement": action.legislative_requirement,
                    "rules:dataImpact": action.data_impact,
                    "rules:confidenceScore": {
                        "@value": action.confidence_score,
                        "@type": "xsd:float"
                    }
                }

                if action.data_specific_steps:
                    action_obj["rules:dataSpecificStep"] = action.data_specific_steps

                if action.verification_method:
                    action_obj["rules:verificationMethod"] = action.verification_method

                if action.responsible_role:
                    action_obj["rules:responsibleRole"] = action.responsible_role

                if action.timeline:
                    action_obj["rules:timeline"] = action.timeline

                rule_actions.append(action_obj)

            if rule_actions:
                rule_jsonld["rules:hasRuleAction"] = rule_actions

            # User Actions
            user_actions = []
            for action in rule.user_actions:
                action_obj = {
                    "@type": "rules:UserAction",
                    "rules:actionType": action.action_type,
                    "rules:title": action.title,
                    "rules:description": action.description,
                    "rules:priority": action.priority,
                    "rules:legislativeRequirement": action.legislative_requirement,
                    "rules:complianceOutcome": action.compliance_outcome,
                    "rules:confidenceScore": {
                        "@value": action.confidence_score,
                        "@type": "xsd:float"
                    }
                }

                if action.user_data_steps:
                    action_obj["rules:userDataStep"] = action.user_data_steps

                if action.affected_data_categories:
                    action_obj["rules:affectedDataCategory"] = action.affected_data_categories

                if action.user_verification_steps:
                    action_obj["rules:userVerificationStep"] = action.user_verification_steps

                if action.user_role_context:
                    action_obj["rules:userRoleContext"] = action.user_role_context

                if action.timeline:
                    action_obj["rules:timeline"] = action.timeline

                user_actions.append(action_obj)

            if user_actions:
                rule_jsonld["rules:hasUserAction"] = user_actions

            # Event information
            rule_jsonld["rules:eventType"] = rule.event.type

            # Metadata
            rule_jsonld["rules:extractedAt"] = {
                "@value": rule.extracted_at.isoformat(),
                "@type": "xsd:dateTime"
            }
            rule_jsonld["rules:extractionMethod"] = rule.extraction_method

            graph.append(rule_jsonld)

        # Add integrated rules for semantic web properties
        for integrated_rule in self.integrated_rules:
            # Find the corresponding original rule
            original_rule_id = integrated_rule.id.replace("integrated:", "")

            integrated_jsonld = {
                "@id": f"urn:rule:{integrated_rule.id}",
                "@type": ["odre:EnforceablePolicy", "dpv:ProcessingActivity"],
                "rdfs:label": integrated_rule.source_article,

                # ODRE Properties
                "odre:enforceable": integrated_rule.odre_enforceable,
                "odre:enforcement_mode": integrated_rule.odre_enforcement_mode,
                "odre:action_inference": integrated_rule.odre_action_inference,
                "odre:user_action_inference": integrated_rule.odre_user_action_inference,

                # DPV Properties
                "dpv:hasProcessing": [{"@id": uri} for uri in integrated_rule.dpv_hasProcessing],
                "dpv:hasPurpose": [{"@id": uri} for uri in integrated_rule.dpv_hasPurpose],
                "dpv:hasPersonalData": [{"@id": uri} for uri in integrated_rule.dpv_hasPersonalData],
                "dpv:hasLocation": [{"@id": uri} for uri in integrated_rule.dpv_hasLocation],
                "dpv-action:hasRuleAction": [{"@id": uri} for uri in integrated_rule.dpv_hasRuleAction],
                "dpv-action:hasUserAction": [{"@id": uri} for uri in integrated_rule.dpv_hasUserAction],
                "dpv-action:hasDocumentLevel": integrated_rule.source_document_levels,
                "dpv-action:hasChunkReference": integrated_rule.chunk_references,

                # ODRL Properties
                "odrl:permission": integrated_rule.odrl_permission,
                "odrl:prohibition": integrated_rule.odrl_prohibition,
                "odrl:obligation": integrated_rule.odrl_obligation,
                "odrl:hasPermissionCount": {
                    "@value": len(integrated_rule.odrl_permission),
                    "@type": "xsd:integer"
                },
                "odrl:hasProhibitionCount": {
                    "@value": len(integrated_rule.odrl_prohibition),
                    "@type": "xsd:integer"
                },
                "odrl:hasObligationCount": {
                    "@value": len(integrated_rule.odrl_obligation),
                    "@type": "xsd:integer"
                },

                # Link to original rule
                "rules:originalRule": {"@id": f"urn:rule:{original_rule_id}"},

                # Metadata
                "dpv:hasConfidenceScore": {
                    "@value": integrated_rule.confidence_score,
                    "@type": "xsd:float"
                },
                "dpv:extractedAt": {
                    "@value": integrated_rule.extracted_at.isoformat(),
                    "@type": "xsd:dateTime"
                },
                "dpv:sourceLegislation": integrated_rule.source_legislation
            }

            # Optional properties
            if integrated_rule.dpv_hasDataController:
                integrated_jsonld["dpv:hasDataController"] = {"@id": integrated_rule.dpv_hasDataController}
            if integrated_rule.dpv_hasDataProcessor:
                integrated_jsonld["dpv:hasDataProcessor"] = {"@id": integrated_rule.dpv_hasDataProcessor}

            graph.append(integrated_jsonld)

        return {**context, "@graph": graph}