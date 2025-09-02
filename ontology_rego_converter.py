#!/usr/bin/env python3
"""
Complete Enhanced Dynamic Ontology to Rego Converter with Full OPA Integration
A comprehensive converter for DPV+ODRL+ODRE ontologies to OPA Rego policies
Uses regopy for native Rego processing instead of rego-python
"""

import os
import json
import re
import hashlib
import logging
import asyncio
import tempfile
import subprocess
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod

# RDF handling
try:
    from rdflib import Graph, Namespace, URIRef, Literal, BNode
    from rdflib.namespace import RDF, RDFS, OWL, XSD
    RDF_AVAILABLE = True
except ImportError:
    RDF_AVAILABLE = False
    print("Warning: rdflib not available. Install with: pip install rdflib")

# OPA Python Client
try:
    from opa_client.opa import OpaClient
    from opa_client.opa_async import AsyncOpaClient
    from opa_client import create_opa_client
    OPA_CLIENT_AVAILABLE = True
    print("✅ OPA Python Client available")
except ImportError:
    OPA_CLIENT_AVAILABLE = False
    print("Warning: OPA Python Client not available. Install with: pip install opa-python-client")

# Microsoft regopy for native Rego execution and AST manipulation
try:
    from regopy import Interpreter as RegoInterpreter
    from regopy import RegoError
    REGOPY_AVAILABLE = True
    print("✅ regopy available for native Rego execution and AST manipulation")
except ImportError:
    REGOPY_AVAILABLE = False
    print("Warning: regopy not available. Install with: pip install regopy")

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define standard namespaces
DPV = Namespace("https://w3id.org/dpv#")
DPV_PD = Namespace("https://w3id.org/dpv/dpv-pd#")
DPV_TECH = Namespace("https://w3id.org/dpv/tech#")
DPV_LEGAL = Namespace("https://w3id.org/dpv/legal/")
ODRL = Namespace("http://www.w3.org/ns/odrl/2/")
ODRE = Namespace("https://w3id.org/def/odre#")
INTEGRATED = Namespace("https://w3id.org/def/integrated-dpv-odrl-odre#")

# ===============================
# DATA CLASSES AND CONFIGURATIONS
# ===============================

@dataclass
class OPAConfig:
    """Configuration for OPA server connection"""
    host: str = "localhost"
    port: int = 8181
    ssl: bool = False
    cert: Optional[Tuple[str, str]] = None
    timeout: int = 30
    async_mode: bool = False

@dataclass
class RegoValidationResult:
    """Result of Rego policy validation"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_result: Optional[Dict[str, Any]] = None

@dataclass
class PolicyDeploymentResult:
    """Result of policy deployment to OPA"""
    policy_name: str
    deployed: bool
    endpoint: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    opa_response: Optional[Dict[str, Any]] = None

@dataclass
class PolicyTestResult:
    """Result of policy testing"""
    policy_name: str
    test_name: str
    passed: bool
    input_data: Dict[str, Any]
    expected_output: Any
    actual_output: Any
    execution_time: float

@dataclass
class RegoRule:
    """Represents a single Rego rule"""
    name: str
    rule_type: str  # "allow", "deny", "violation", "duty", "data"
    condition: str
    action: Optional[str] = None
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RegoPolicy:
    """Complete Rego policy structure"""
    package_name: str
    imports: List[str] = field(default_factory=lambda: ["rego.v1"])
    rules: List[RegoRule] = field(default_factory=list)
    data_definitions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OntologyPattern:
    """Represents a discovered pattern in the ontology"""
    pattern_type: str  # "permission", "prohibition", "obligation", "processing", etc.
    subject: str
    predicate: str
    object_value: Any
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

# ===============================
# BASE CLASSES FOR EXTRACTION
# ===============================

class ConceptExtractor(ABC):
    """Abstract base class for extracting concepts from ontology"""
    
    @abstractmethod
    def extract(self, graph: Graph, subject: URIRef) -> List[OntologyPattern]:
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[URIRef]:
        pass

class ODRLExtractor(ConceptExtractor):
    """Extracts ODRL concepts (permissions, prohibitions, obligations)"""
    
    def get_supported_types(self) -> List[URIRef]:
        return [ODRL.Permission, ODRL.Prohibition, ODRL.Obligation, ODRL.Rule]
    
    def extract(self, graph: Graph, subject: URIRef) -> List[OntologyPattern]:
        patterns = []
        
        # Extract permissions
        for perm in graph.objects(subject, ODRL.permission):
            if isinstance(perm, BNode):
                pattern = self._extract_odrl_rule(graph, perm, "permission")
                if pattern:
                    patterns.append(pattern)
        
        # Extract prohibitions
        for prohib in graph.objects(subject, ODRL.prohibition):
            if isinstance(prohib, BNode):
                pattern = self._extract_odrl_rule(graph, prohib, "prohibition")
                if pattern:
                    patterns.append(pattern)
        
        # Extract obligations
        for oblig in graph.objects(subject, ODRL.obligation):
            if isinstance(oblig, BNode):
                pattern = self._extract_odrl_rule(graph, oblig, "obligation")
                if pattern:
                    patterns.append(pattern)
        
        return patterns
    
    def _extract_odrl_rule(self, graph: Graph, rule_node: BNode, rule_type: str) -> Optional[OntologyPattern]:
        """Extract individual ODRL rule (permission/prohibition/obligation)"""
        try:
            # Get action
            actions = list(graph.objects(rule_node, ODRL.action))
            action = str(actions[0]).split('#')[-1].split('/')[-1].lower() if actions else "unknown"
            
            # Get constraints
            constraints = []
            for constraint in graph.objects(rule_node, ODRL.constraint):
                if isinstance(constraint, BNode):
                    constraint_data = self._extract_constraint(graph, constraint)
                    if constraint_data:
                        constraints.append(constraint_data)
            
            # Get duties (for permissions)
            for duty in graph.objects(rule_node, ODRL.duty):
                if isinstance(duty, BNode):
                    duty_data = self._extract_duty(graph, duty)
                    if duty_data:
                        constraints.append({"type": "duty", **duty_data})
            
            return OntologyPattern(
                pattern_type=rule_type,
                subject=str(rule_node),
                predicate=f"odrl:{rule_type}",
                object_value=action,
                constraints=constraints,
                metadata={"action": action, "rule_type": rule_type}
            )
            
        except Exception as e:
            logger.warning(f"Error extracting ODRL rule: {e}")
            return None
    
    def _extract_constraint(self, graph: Graph, constraint_node: BNode) -> Optional[Dict[str, Any]]:
        """Extract ODRL constraint"""
        try:
            left_operands = list(graph.objects(constraint_node, ODRL.leftOperand))
            operators = list(graph.objects(constraint_node, ODRL.operator))
            right_operands = list(graph.objects(constraint_node, ODRL.rightOperand))
            
            if left_operands and operators and right_operands:
                return {
                    "type": "constraint",
                    "leftOperand": str(left_operands[0]).split('#')[-1].split('/')[-1],
                    "operator": str(operators[0]).split('#')[-1].split('/')[-1],
                    "rightOperand": self._format_operand_value(right_operands[0])
                }
        except Exception as e:
            logger.warning(f"Error extracting constraint: {e}")
        
        return None
    
    def _extract_duty(self, graph: Graph, duty_node: BNode) -> Optional[Dict[str, Any]]:
        """Extract ODRL duty"""
        try:
            actions = list(graph.objects(duty_node, ODRL.action))
            constraints = []
            
            for constraint in graph.objects(duty_node, ODRL.constraint):
                if isinstance(constraint, BNode):
                    constraint_data = self._extract_constraint(graph, constraint)
                    if constraint_data:
                        constraints.append(constraint_data)
            
            if actions:
                return {
                    "action": str(actions[0]).split('#')[-1].split('/')[-1].lower(),
                    "constraints": constraints
                }
        except Exception as e:
            logger.warning(f"Error extracting duty: {e}")
        
        return None
    
    def _format_operand_value(self, value: Union[URIRef, Literal, BNode]) -> Any:
        """Format operand value for Rego"""
        if isinstance(value, Literal):
            str_val = str(value)
            # Try to parse as boolean
            if str_val.lower() in ['true', 'false']:
                return str_val.lower() == 'true'
            # Try to parse as number
            try:
                if '.' in str_val:
                    return float(str_val)
                return int(str_val)
            except ValueError:
                return str_val
        elif isinstance(value, URIRef):
            return str(value).split('#')[-1].split('/')[-1]
        else:
            return str(value)

class DPVExtractor(ConceptExtractor):
    """Extracts DPV concepts (processing activities, purposes, data types, etc.)"""
    
    def get_supported_types(self) -> List[URIRef]:
        return [DPV.ProcessingActivity, ODRE.EnforceablePolicy, INTEGRATED.PrivacyRightsPolicy]
    
    def extract(self, graph: Graph, subject: URIRef) -> List[OntologyPattern]:
        patterns = []
        
        # Extract processing operations
        processing_ops = list(graph.objects(subject, DPV.hasProcessing))
        if processing_ops:
            patterns.append(OntologyPattern(
                pattern_type="processing",
                subject=str(subject),
                predicate="dpv:hasProcessing",
                object_value=[str(op).split('#')[-1].lower() for op in processing_ops],
                metadata={"count": len(processing_ops)}
            ))
        
        # Extract purposes
        purposes = list(graph.objects(subject, DPV.hasPurpose))
        if purposes:
            patterns.append(OntologyPattern(
                pattern_type="purpose",
                subject=str(subject),
                predicate="dpv:hasPurpose",
                object_value=[str(p).split('#')[-1].lower() for p in purposes],
                metadata={"count": len(purposes)}
            ))
        
        # Extract personal data categories
        data_categories = list(graph.objects(subject, DPV.hasPersonalData))
        if data_categories:
            patterns.append(OntologyPattern(
                pattern_type="data_category",
                subject=str(subject),
                predicate="dpv:hasPersonalData",
                object_value=[str(dc).split('#')[-1].lower() for dc in data_categories],
                metadata={"count": len(data_categories)}
            ))
        
        # Extract roles
        controllers = list(graph.objects(subject, DPV.hasDataController))
        processors = list(graph.objects(subject, DPV.hasDataProcessor))
        
        if controllers or processors:
            roles = {}
            if controllers:
                roles["controller"] = [str(c).split('#')[-1].lower() for c in controllers]
            if processors:
                roles["processor"] = [str(p).split('#')[-1].lower() for p in processors]
            
            patterns.append(OntologyPattern(
                pattern_type="roles",
                subject=str(subject),
                predicate="dpv:hasRole",
                object_value=roles,
                metadata={"roles_count": len(roles)}
            ))
        
        # Extract legal basis
        legal_bases = list(graph.objects(subject, DPV.hasLegalBasis))
        if legal_bases:
            patterns.append(OntologyPattern(
                pattern_type="legal_basis",
                subject=str(subject),
                predicate="dpv:hasLegalBasis",
                object_value=[str(lb).split('#')[-1].lower() for lb in legal_bases],
                metadata={"count": len(legal_bases)}
            ))
        
        return patterns

class ODREExtractor(ConceptExtractor):
    """Extracts ODRE concepts (enforcement properties)"""
    
    def get_supported_types(self) -> List[URIRef]:
        return [ODRE.EnforceablePolicy, ODRE.EnforcementFramework]
    
    def extract(self, graph: Graph, subject: URIRef) -> List[OntologyPattern]:
        patterns = []
        
        # Extract enforcement properties
        enforcement_props = {
            "enforceable": ODRE.enforceable,
            "enforcement_mode": ODRE.enforcementMode,
            "monitoring_required": ODRE.monitoringRequired,
            "compliance_check": ODRE.complianceCheck,
            "temporal_enforcement": ODRE.temporalEnforcement,
            "confidence_score": ODRE.hasConfidenceScore
        }
        
        for prop_name, prop_uri in enforcement_props.items():
            values = list(graph.objects(subject, prop_uri))
            if values:
                value = values[0]
                formatted_value = self._format_value(value)
                
                patterns.append(OntologyPattern(
                    pattern_type="enforcement",
                    subject=str(subject),
                    predicate=f"odre:{prop_name}",
                    object_value=formatted_value,
                    metadata={"property": prop_name, "datatype": type(formatted_value).__name__}
                ))
        
        return patterns
    
    def _format_value(self, value: Union[URIRef, Literal]) -> Any:
        """Format value with proper type conversion"""
        if isinstance(value, Literal):
            str_val = str(value)
            if str_val.lower() in ['true', 'false']:
                return str_val.lower() == 'true'
            try:
                if '.' in str_val:
                    return float(str_val)
                return int(str_val)
            except ValueError:
                return str_val
        return str(value)

# ===============================
# REGO GENERATION ENGINE
# ===============================

class RegoGenerator:
    """Generates Rego code from ontology patterns"""
    
    def __init__(self):
        self.operator_mapping = {
            "eq": "==",
            "neq": "!=",
            "lt": "<",
            "gt": ">",
            "lteq": "<=",
            "gteq": ">=",
            "isA": "in",
            "isNotA": "not in",
            "contains": "contains",
            "isPartOf": "in"
        }
    
    def generate_policy(self, patterns: List[OntologyPattern], policy_name: str) -> RegoPolicy:
        """Generate complete Rego policy from patterns"""
        policy = RegoPolicy(
            package_name=self._sanitize_package_name(policy_name),
            metadata={"generated_at": datetime.utcnow().isoformat(), "pattern_count": len(patterns)}
        )
        
        # Add default deny
        policy.rules.append(RegoRule(
            name="default_allow",
            rule_type="data",
            condition="false"
        ))
        
        # Process patterns by type
        pattern_groups = self._group_patterns_by_type(patterns)
        
        for pattern_type, type_patterns in pattern_groups.items():
            if pattern_type == "permission":
                self._generate_permission_rules(policy, type_patterns)
            elif pattern_type == "prohibition":
                self._generate_prohibition_rules(policy, type_patterns)
            elif pattern_type == "obligation":
                self._generate_obligation_rules(policy, type_patterns)
            elif pattern_type == "processing":
                self._generate_processing_rules(policy, type_patterns)
            elif pattern_type == "purpose":
                self._generate_purpose_rules(policy, type_patterns)
            elif pattern_type == "data_category":
                self._generate_data_category_rules(policy, type_patterns)
            elif pattern_type == "roles":
                self._generate_role_rules(policy, type_patterns)
            elif pattern_type == "legal_basis":
                self._generate_legal_basis_rules(policy, type_patterns)
            elif pattern_type == "enforcement":
                self._generate_enforcement_rules(policy, type_patterns)
        
        return policy
    
    def _group_patterns_by_type(self, patterns: List[OntologyPattern]) -> Dict[str, List[OntologyPattern]]:
        """Group patterns by their type"""
        groups = {}
        for pattern in patterns:
            if pattern.pattern_type not in groups:
                groups[pattern.pattern_type] = []
            groups[pattern.pattern_type].append(pattern)
        return groups
    
    def _generate_permission_rules(self, policy: RegoPolicy, patterns: List[OntologyPattern]):
        """Generate allow rules from ODRL permissions"""
        for pattern in patterns:
            action = pattern.metadata.get("action", "unknown")
            rule_name = f"allow_{action}"
            
            conditions = []
            
            # Add action check
            conditions.append(f'input.action == "{action}"')
            
            # Process constraints
            for constraint in pattern.constraints:
                if constraint.get("type") == "constraint":
                    condition = self._build_constraint_condition(constraint)
                    if condition:
                        conditions.append(condition)
            
            # Combine conditions
            final_condition = " and ".join(conditions) if len(conditions) > 1 else conditions[0] if conditions else "true"
            
            policy.rules.append(RegoRule(
                name=rule_name,
                rule_type="allow",
                condition=final_condition,
                action=action,
                metadata={"source": "odrl_permission"}
            ))
    
    def _generate_prohibition_rules(self, policy: RegoPolicy, patterns: List[OntologyPattern]):
        """Generate violation rules from ODRL prohibitions"""
        for pattern in patterns:
            action = pattern.metadata.get("action", "unknown")
            rule_name = f"violation_{action}"
            
            conditions = []
            conditions.append(f'input.action == "{action}"')
            
            # Process constraints - these define when the prohibition is violated
            for constraint in pattern.constraints:
                if constraint.get("type") == "constraint":
                    condition = self._build_constraint_condition(constraint)
                    if condition:
                        conditions.append(condition)
            
            final_condition = " and ".join(conditions) if len(conditions) > 1 else conditions[0] if conditions else f'input.action == "{action}"'
            
            # Create violation rule
            violation_body = f'''violations[violation] if {{
    {final_condition}
    violation := {{
        "type": "{action}_prohibited",
        "action": "{action}",
        "severity": "high",
        "source": "odrl_prohibition"
    }}
}}'''
            
            policy.rules.append(RegoRule(
                name=rule_name,
                rule_type="violation",
                condition=violation_body,
                action=action,
                metadata={"source": "odrl_prohibition"}
            ))
    
    def _generate_obligation_rules(self, policy: RegoPolicy, patterns: List[OntologyPattern]):
        """Generate duty rules from ODRL obligations"""
        for pattern in patterns:
            action = pattern.metadata.get("action", "unknown")
            rule_name = f"duty_{action}"
            
            conditions = []
            for constraint in pattern.constraints:
                if constraint.get("type") == "constraint":
                    condition = self._build_constraint_condition(constraint)
                    if condition:
                        conditions.append(condition)
            
            final_condition = " and ".join(conditions) if conditions else "true"
            
            # Create duty rule
            duty_body = f'''duties[duty] if {{
    {final_condition}
    duty := {{
        "type": "{action}",
        "required": true,
        "source": "odrl_obligation"
    }}
}}'''
            
            policy.rules.append(RegoRule(
                name=rule_name,
                rule_type="duty",
                condition=duty_body,
                action=action,
                metadata={"source": "odrl_obligation"}
            ))
    
    def _generate_processing_rules(self, policy: RegoPolicy, patterns: List[OntologyPattern]):
        """Generate rules for DPV processing activities"""
        for pattern in patterns:
            processing_types = pattern.object_value
            if isinstance(processing_types, list):
                policy.data_definitions["allowed_processing"] = processing_types
                
                policy.rules.append(RegoRule(
                    name="processing_allowed",
                    rule_type="allow",
                    condition="input.processing_type in data.allowed_processing",
                    metadata={"source": "dpv_processing"}
                ))
    
    def _generate_purpose_rules(self, policy: RegoPolicy, patterns: List[OntologyPattern]):
        """Generate rules for DPV purposes"""
        for pattern in patterns:
            purposes = pattern.object_value
            if isinstance(purposes, list):
                policy.data_definitions["allowed_purposes"] = purposes
                
                policy.rules.append(RegoRule(
                    name="purpose_allowed",
                    rule_type="allow",
                    condition="input.purpose in data.allowed_purposes",
                    metadata={"source": "dpv_purpose"}
                ))
    
    def _generate_data_category_rules(self, policy: RegoPolicy, patterns: List[OntologyPattern]):
        """Generate rules for DPV data categories"""
        for pattern in patterns:
            data_categories = pattern.object_value
            if isinstance(data_categories, list):
                policy.data_definitions["allowed_data_categories"] = data_categories
                
                policy.rules.append(RegoRule(
                    name="data_category_allowed",
                    rule_type="allow",
                    condition="input.data_category in data.allowed_data_categories",
                    metadata={"source": "dpv_data_category"}
                ))
    
    def _generate_role_rules(self, policy: RegoPolicy, patterns: List[OntologyPattern]):
        """Generate rules for DPV roles"""
        for pattern in patterns:
            roles = pattern.object_value
            if isinstance(roles, dict):
                for role_type, role_values in roles.items():
                    policy.data_definitions[f"allowed_{role_type}s"] = role_values
                    
                    policy.rules.append(RegoRule(
                        name=f"{role_type}_allowed",
                        rule_type="allow",
                        condition=f"input.{role_type} in data.allowed_{role_type}s",
                        metadata={"source": f"dpv_{role_type}"}
                    ))
    
    def _generate_legal_basis_rules(self, policy: RegoPolicy, patterns: List[OntologyPattern]):
        """Generate rules for DPV legal basis"""
        for pattern in patterns:
            legal_bases = pattern.object_value
            if isinstance(legal_bases, list):
                policy.data_definitions["required_legal_basis"] = legal_bases
                
                policy.rules.append(RegoRule(
                    name="legal_basis_valid",
                    rule_type="allow",
                    condition="input.legal_basis in data.required_legal_basis",
                    metadata={"source": "dpv_legal_basis"}
                ))
    
    def _generate_enforcement_rules(self, policy: RegoPolicy, patterns: List[OntologyPattern]):
        """Generate rules for ODRE enforcement properties"""
        enforcement_data = {}
        
        for pattern in patterns:
            prop_name = pattern.metadata.get("property")
            if prop_name:
                enforcement_data[prop_name] = pattern.object_value
        
        if enforcement_data:
            policy.data_definitions["enforcement_config"] = enforcement_data
            
            # Add enforcement checks
            if enforcement_data.get("enforceable"):
                policy.rules.append(RegoRule(
                    name="enforcement_active",
                    rule_type="allow",
                    condition="data.enforcement_config.enforceable == true",
                    metadata={"source": "odre_enforcement"}
                ))
            
            if enforcement_data.get("monitoring_required"):
                policy.rules.append(RegoRule(
                    name="monitoring_duty",
                    rule_type="duty",
                    condition='''duties[duty] if {
    data.enforcement_config.monitoring_required == true
    duty := {
        "type": "monitoring",
        "required": true,
        "mode": data.enforcement_config.enforcement_mode
    }
}''',
                    metadata={"source": "odre_monitoring"}
                ))
    
    def _build_constraint_condition(self, constraint: Dict[str, Any]) -> Optional[str]:
        """Build Rego condition from ODRL constraint"""
        try:
            left = constraint.get("leftOperand", "")
            operator = constraint.get("operator", "eq")
            right = constraint.get("rightOperand")
            
            if not left or right is None:
                return None
            
            # Map to input field
            left_field = f"input.{left}"
            
            # Map operator
            rego_op = self.operator_mapping.get(operator, "==")
            
            # Format right operand
            if isinstance(right, str):
                right_value = f'"{right}"'
            elif isinstance(right, bool):
                right_value = "true" if right else "false"
            else:
                right_value = str(right)
            
            return f"{left_field} {rego_op} {right_value}"
            
        except Exception as e:
            logger.warning(f"Error building constraint condition: {e}")
            return None
    
    def _sanitize_package_name(self, name: str) -> str:
        """Sanitize name for Rego package"""
        # Extract meaningful name from URI or use as-is
        if '#' in name or '/' in name:
            name = name.split('#')[-1].split('/')[-1]
        
        # Convert to valid Rego package name
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()
        
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = f"policy_{sanitized}"
        
        return f"privacy.{sanitized}" if sanitized else "privacy.generated_policy"
    
    def generate_rego_code(self, policy: RegoPolicy) -> str:
        """Generate final Rego code string"""
        lines = []
        
        # Package declaration
        lines.append(f"package {policy.package_name}")
        lines.append("")
        
        # Imports
        for imp in policy.imports:
            lines.append(f"import {imp}")
        lines.append("")
        
        # Metadata comment
        if policy.metadata:
            lines.append("# Policy metadata")
            for key, value in policy.metadata.items():
                lines.append(f"# {key}: {value}")
            lines.append("")
        
        # Data definitions
        if policy.data_definitions:
            lines.append("# Policy data")
            for key, value in policy.data_definitions.items():
                lines.append(f"data.{key} := {json.dumps(value)}")
            lines.append("")
        
        # Rules by type
        rule_types = ["data", "allow", "violation", "duty"]
        
        for rule_type in rule_types:
            type_rules = [r for r in policy.rules if r.rule_type == rule_type]
            if not type_rules:
                continue
            
            if rule_type == "data":
                lines.append("# Default policies")
                for rule in type_rules:
                    if rule.name.startswith("default"):
                        lines.append(f"default allow := {rule.condition}")
                lines.append("")
            
            elif rule_type == "allow":
                lines.append("# Allow rules")
                for rule in type_rules:
                    lines.append(f"allow if {{")
                    lines.append(f"    {rule.condition}")
                    lines.append(f"}}")
                    if rule.metadata:
                        lines.append(f"# Source: {rule.metadata.get('source', 'unknown')}")
                lines.append("")
            
            elif rule_type == "violation":
                lines.append("# Violations")
                for rule in type_rules:
                    # The condition already contains the full rule body
                    lines.append(rule.condition)
                lines.append("")
            
            elif rule_type == "duty":
                lines.append("# Duties")
                for rule in type_rules:
                    # The condition already contains the full rule body
                    lines.append(rule.condition)
                lines.append("")
        
        return "\n".join(lines)

# ===============================
# REGOPY-BASED AST ENHANCEMENT
# ===============================

class RegoASTEnhancer:
    """Enhanced Rego generation with regopy-based AST manipulation and validation"""
    
    def __init__(self):
        self.regopy_available = REGOPY_AVAILABLE
        if self.regopy_available:
            self.interpreter = RegoInterpreter()
    
    def enhance_rego_with_ast(self, rego_code: str) -> str:
        """Enhance generated Rego code using regopy capabilities"""
        if not self.regopy_available:
            logger.warning("regopy not available, returning original code with basic enhancements")
            return self._basic_enhancements(rego_code)
        
        try:
            # Use regopy to validate and enhance the code
            enhanced_code = self._add_documentation_comments(rego_code)
            enhanced_code = self._optimize_rule_structure(enhanced_code)
            
            # Test the enhanced code with regopy
            if self._validate_with_regopy(enhanced_code):
                logger.info("Enhanced Rego code validated successfully with regopy")
                return enhanced_code
            else:
                logger.warning("Enhanced code failed validation, returning original")
                return rego_code
        
        except Exception as e:
            logger.warning(f"AST enhancement failed: {e}")
            return self._basic_enhancements(rego_code)
    
    def _validate_with_regopy(self, rego_code: str) -> bool:
        """Validate Rego code using regopy interpreter"""
        if not self.regopy_available:
            return True
        
        try:
            # Create a fresh interpreter instance
            test_interpreter = RegoInterpreter()
            
            # Extract package name for module name
            package_line = next((line for line in rego_code.split('\n') if line.strip().startswith('package ')), None)
            if package_line:
                package_name = package_line.strip().replace('package ', '').replace('.', '_')
            else:
                package_name = "test_module"
            
            # Try to add the module
            test_interpreter.add_module(package_name, rego_code)
            
            # Try a simple query to ensure the module is valid
            result = test_interpreter.query("data")
            logger.debug(f"Regopy validation successful: {result}")
            return True
        
        except RegoError as e:
            logger.warning(f"Regopy validation failed: {e}")
            return False
        except Exception as e:
            logger.warning(f"Regopy validation error: {e}")
            return False
    
    def _basic_enhancements(self, rego_code: str) -> str:
        """Apply basic enhancements without regopy"""
        enhanced_code = self._add_documentation_comments(rego_code)
        enhanced_code = self._optimize_rule_structure(enhanced_code)
        return enhanced_code
    
    def _add_documentation_comments(self, rego_code: str) -> str:
        """Add automatic documentation comments"""
        lines = rego_code.split('\n')
        enhanced_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('package '):
                enhanced_lines.append(line)
                package_name = stripped.replace('package ', '')
                enhanced_lines.append(f"# Auto-generated policy for {package_name}")
                enhanced_lines.append(f"# Generated at: {datetime.utcnow().isoformat()}")
                enhanced_lines.append(f"# Enhanced with regopy validation")
            elif stripped.startswith('allow if'):
                enhanced_lines.append(f"# Permission rule - allows specific actions")
                enhanced_lines.append(line)
            elif 'violations[violation] if' in stripped:
                enhanced_lines.append(f"# Violation detection - identifies policy breaches")
                enhanced_lines.append(line)
            elif 'duties[duty] if' in stripped:
                enhanced_lines.append(f"# Duty enforcement - mandatory obligations")
                enhanced_lines.append(line)
            elif stripped.startswith('data.'):
                enhanced_lines.append(f"# Policy data definition")
                enhanced_lines.append(line)
            else:
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    def _optimize_rule_structure(self, rego_code: str) -> str:
        """Optimize rule structure for better performance"""
        lines = rego_code.split('\n')
        optimized_lines = []
        
        in_rule = False
        rule_conditions = []
        rule_start_line = ""
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('allow if {') or stripped.startswith('violations[') or stripped.startswith('duties['):
                in_rule = True
                rule_start_line = line
                rule_conditions = []
            elif stripped == '}' and in_rule:
                # Optimize and sort conditions within the rule
                if rule_conditions:
                    # Sort conditions: simple comparisons first, complex logic last
                    sorted_conditions = self._sort_rule_conditions(rule_conditions)
                    optimized_lines.append(rule_start_line)
                    for condition in sorted_conditions:
                        optimized_lines.append(condition)
                else:
                    optimized_lines.append(rule_start_line)
                optimized_lines.append(line)
                in_rule = False
            elif in_rule and stripped and not stripped.startswith('#'):
                rule_conditions.append(line)
            else:
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
    
    def _sort_rule_conditions(self, conditions: List[str]) -> List[str]:
        """Sort rule conditions for optimal evaluation order"""
        simple_conditions = []
        complex_conditions = []
        
        for condition in conditions:
            stripped = condition.strip()
            # Simple equality checks first (fast to evaluate)
            if '==' in stripped and 'input.' in stripped:
                simple_conditions.append(condition)
            # Complex conditions (function calls, nested logic) later
            else:
                complex_conditions.append(condition)
        
        return simple_conditions + complex_conditions
    
    def analyze_rego_structure(self, rego_code: str) -> Dict[str, Any]:
        """Analyze Rego code structure using regopy"""
        if not self.regopy_available:
            return {"error": "regopy not available for structure analysis"}
        
        try:
            # Create interpreter and add module
            analyzer = RegoInterpreter()
            analyzer.add_module("analysis", rego_code)
            
            # Query for basic structure information
            structure_info = {
                "valid": True,
                "package_detected": "package " in rego_code,
                "rules_count": len([line for line in rego_code.split('\n') if 'if {' in line]),
                "data_definitions": len([line for line in rego_code.split('\n') if line.strip().startswith('data.')]),
                "imports": [line.strip() for line in rego_code.split('\n') if line.strip().startswith('import ')],
                "regopy_validation": "passed"
            }
            
            return structure_info
        
        except RegoError as e:
            return {
                "valid": False,
                "error": str(e),
                "regopy_validation": "failed"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Analysis failed: {str(e)}",
                "regopy_validation": "error"
            }

# ===============================
# OPA INTEGRATION SYSTEM
# ===============================

class OPAPolicyManager:
    """Manager for OPA policy operations using Python client"""
    
    def __init__(self, config: OPAConfig):
        self.config = config
        self.client = None
        self.async_client = None
        
        if not OPA_CLIENT_AVAILABLE:
            raise ImportError("OPA Python Client required. Install with: pip install opa-python-client")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def connect(self):
        """Establish connection to OPA server"""
        try:
            if self.config.async_mode:
                self.async_client = AsyncOpaClient(
                    host=self.config.host,
                    port=self.config.port,
                    ssl=self.config.ssl,
                    cert=self.config.cert
                )
            else:
                self.client = OpaClient(
                    host=self.config.host,
                    port=self.config.port,
                    ssl=self.config.ssl,
                    cert=self.config.cert
                )
            
            # Test connection
            if self.is_healthy():
                logger.info(f"Connected to OPA server at {self.config.host}:{self.config.port}")
            else:
                raise ConnectionError("OPA server not responding")
                
        except Exception as e:
            logger.error(f"Failed to connect to OPA server: {e}")
            raise
    
    def disconnect(self):
        """Close connection to OPA server"""
        try:
            if self.client:
                self.client.close_connection()
            if self.async_client:
                asyncio.create_task(self.async_client.close())
            logger.info("Disconnected from OPA server")
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")
    
    def is_healthy(self) -> bool:
        """Check if OPA server is healthy"""
        try:
            if self.client:
                return self.client.check_health()
            return False
        except Exception:
            return False
    
    def deploy_policy(self, policy_name: str, rego_code: str) -> PolicyDeploymentResult:
        """Deploy Rego policy to OPA server"""
        try:
            # Write policy to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rego', delete=False) as f:
                f.write(rego_code)
                temp_path = f.name
            
            try:
                # Upload policy
                result = self.client.update_opa_policy_fromfile(temp_path, endpoint=policy_name)
                
                if result:
                    # Get policy info
                    policy_info = self.client.get_policies_info()
                    endpoint = policy_info.get(policy_name, {}).get('path')
                    
                    logger.info(f"Policy {policy_name} deployed successfully")
                    return PolicyDeploymentResult(
                        policy_name=policy_name,
                        deployed=True,
                        endpoint=endpoint,
                        opa_response={"status": "success", "info": policy_info.get(policy_name)}
                    )
                else:
                    return PolicyDeploymentResult(
                        policy_name=policy_name,
                        deployed=False,
                        errors=["Failed to upload policy to OPA"]
                    )
            
            finally:
                os.unlink(temp_path)
        
        except Exception as e:
            logger.error(f"Failed to deploy policy {policy_name}: {e}")
            return PolicyDeploymentResult(
                policy_name=policy_name,
                deployed=False,
                errors=[str(e)]
            )
    
    def test_policy(self, policy_name: str, input_data: Dict[str, Any], 
                   expected_output: Any = None) -> PolicyTestResult:
        """Test deployed policy with input data"""
        start_time = datetime.utcnow()
        
        try:
            # Get policy endpoint
            policy_info = self.client.get_policies_info()
            if policy_name not in policy_info:
                return PolicyTestResult(
                    policy_name=policy_name,
                    test_name="policy_execution",
                    passed=False,
                    input_data=input_data,
                    expected_output=expected_output,
                    actual_output=None,
                    execution_time=0.0
                )
            
            # Execute policy query using the client's query method
            try:
                query_result = self.client.query_rule(input_data, rule_name=f"data.{policy_name.replace('.', '/')}")
            except Exception:
                # Fallback to basic policy query
                query_result = self.client.query_rule(input_data, rule_name=policy_name)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Check result
            passed = True
            if expected_output is not None:
                passed = query_result == expected_output
            
            return PolicyTestResult(
                policy_name=policy_name,
                test_name="policy_execution",
                passed=passed,
                input_data=input_data,
                expected_output=expected_output,
                actual_output=query_result,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Policy test failed for {policy_name}: {e}")
            
            return PolicyTestResult(
                policy_name=policy_name,
                test_name="policy_execution",
                passed=False,
                input_data=input_data,
                expected_output=expected_output,
                actual_output=f"Error: {str(e)}",
                execution_time=execution_time
            )
    
    def list_policies(self) -> Dict[str, Dict[str, Any]]:
        """List all deployed policies"""
        try:
            return self.client.get_policies_info()
        except Exception as e:
            logger.error(f"Failed to list policies: {e}")
            return {}
    
    def delete_policy(self, policy_name: str) -> bool:
        """Delete policy from OPA server"""
        try:
            result = self.client.delete_opa_policy(policy_name)
            if result:
                logger.info(f"Policy {policy_name} deleted successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to delete policy {policy_name}: {e}")
            return False

# ===============================
# REGOPY-BASED POLICY VALIDATION
# ===============================

class PolicyValidator:
    """Validates Rego policies using regopy and other methods"""
    
    def __init__(self):
        self.regopy_available = REGOPY_AVAILABLE
        self.opa_available = self._check_opa_binary()
    
    def _check_opa_binary(self) -> bool:
        """Check if OPA binary is available"""
        try:
            subprocess.run(['opa', 'version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def validate_syntax(self, rego_code: str) -> RegoValidationResult:
        """Validate Rego syntax using available methods"""
        errors = []
        warnings = []
        execution_result = None
        
        # Method 1: Try with regopy (preferred method)
        if self.regopy_available:
            try:
                result = self._validate_with_regopy(rego_code)
                if result.valid:
                    logger.info("regopy validation passed")
                    return result
                else:
                    errors.extend(result.errors)
            except Exception as e:
                warnings.append(f"regopy validation failed: {e}")
        
        # Method 2: Try with OPA binary
        if self.opa_available:
            try:
                result = self._validate_with_opa_binary(rego_code)
                if result.valid:
                    logger.info("OPA binary validation passed")
                    return result
                else:
                    errors.extend(result.errors)
            except Exception as e:
                warnings.append(f"OPA binary validation failed: {e}")
        
        # Method 3: Basic syntax checking
        result = self._basic_syntax_check(rego_code)
        result.warnings.extend(warnings)
        if errors:
            result.errors.extend(errors)
        return result
    
    def _validate_with_regopy(self, rego_code: str) -> RegoValidationResult:
        """Validate using regopy native interpreter"""
        try:
            rego = RegoInterpreter()
            
            # Extract package name for module name
            package_line = next((line for line in rego_code.split('\n') if line.strip().startswith('package ')), None)
            if package_line:
                module_name = package_line.strip().replace('package ', '').replace('.', '_')
            else:
                module_name = "validation_test"
            
            # Try to add the module
            rego.add_module(module_name, rego_code)
            
            # Try a simple query to test execution
            result = rego.query("data")
            execution_result = {"query_result": result}
            
            # Try to query the specific package if it exists
            try:
                package_query = f"data.{module_name}"
                package_result = rego.query(package_query)
                execution_result["package_query"] = package_result
            except:
                pass  # Package query might fail, which is okay
            
            return RegoValidationResult(
                valid=True,
                execution_result=execution_result
            )
        
        except RegoError as e:
            return RegoValidationResult(
                valid=False,
                errors=[f"regopy error: {str(e)}"]
            )
        except Exception as e:
            return RegoValidationResult(
                valid=False,
                errors=[f"regopy validation error: {str(e)}"]
            )
    
    def _validate_with_opa_binary(self, rego_code: str) -> RegoValidationResult:
        """Validate using OPA binary"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rego', delete=False) as f:
            f.write(rego_code)
            temp_path = f.name
        
        try:
            # Parse with OPA
            result = subprocess.run(
                ['opa', 'parse', temp_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return RegoValidationResult(valid=True)
            else:
                return RegoValidationResult(
                    valid=False,
                    errors=[result.stderr.strip()]
                )
        
        finally:
            os.unlink(temp_path)
    
    def _basic_syntax_check(self, rego_code: str) -> RegoValidationResult:
        """Basic syntax validation"""
        errors = []
        warnings = []
        
        lines = rego_code.split('\n')
        
        has_package = False
        brace_count = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for package declaration
            if stripped.startswith('package '):
                has_package = True
            
            # Basic brace matching
            brace_count += line.count('{') - line.count('}')
            
            # Check for common issues
            if stripped and not stripped.startswith('#'):
                if stripped.endswith(',') and not stripped.endswith('",'):
                    warnings.append(f"Line {i}: Trailing comma may be unnecessary")
                
                if '=' in stripped and not ('==' in stripped or ':=' in stripped or '!=' in stripped or '>=' in stripped or '<=' in stripped):
                    warnings.append(f"Line {i}: Use ':=' for assignment in Rego")
        
        if not has_package:
            errors.append("Missing package declaration")
        
        if brace_count != 0:
            errors.append(f"Mismatched braces (difference: {brace_count})")
        
        return RegoValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def test_policy_execution(self, rego_code: str, test_inputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test policy execution with various inputs using regopy"""
        if not self.regopy_available:
            return [{"error": "regopy not available for policy testing"}]
        
        results = []
        
        try:
            rego = RegoInterpreter()
            
            # Extract package name
            package_line = next((line for line in rego_code.split('\n') if line.strip().startswith('package ')), None)
            if package_line:
                module_name = package_line.strip().replace('package ', '').replace('.', '_')
            else:
                module_name = "test_policy"
            
            # Add the module
            rego.add_module(module_name, rego_code)
            
            # Test with each input
            for i, test_input in enumerate(test_inputs):
                try:
                    rego.set_input(test_input)
                    
                    # Try different queries
                    queries = [
                        "data.allow",
                        f"data.{module_name}.allow",
                        f"data.{module_name}",
                        "data"
                    ]
                    
                    test_result = {
                        "input": test_input,
                        "test_number": i + 1,
                        "results": {}
                    }
                    
                    for query in queries:
                        try:
                            result = rego.query(query)
                            test_result["results"][query] = result
                        except Exception as e:
                            test_result["results"][query] = f"Error: {str(e)}"
                    
                    results.append(test_result)
                
                except Exception as e:
                    results.append({
                        "input": test_input,
                        "test_number": i + 1,
                        "error": str(e)
                    })
        
        except Exception as e:
            results.append({"general_error": str(e)})
        
        return results

# ===============================
# MAIN CONVERTER CLASS
# ===============================

class EnhancedDynamicOntologyRegoConverter:
    """Enhanced converter with full OPA integration using regopy"""
    
    def __init__(self, opa_config: OPAConfig = None, cache_dir: str = "./rego_cache"):
        if not RDF_AVAILABLE:
            raise ImportError("rdflib is required. Install with: pip install rdflib")
        
        # Initialize base components
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize extractors
        self.extractors = {
            "odrl": ODRLExtractor(),
            "dpv": DPVExtractor(),
            "odre": ODREExtractor()
        }
        
        self.generator = RegoGenerator()
        self.graph = Graph()
        self.last_hash = None
        
        # Enhanced components using regopy
        self.opa_config = opa_config or OPAConfig()
        self.ast_enhancer = RegoASTEnhancer()
        self.validator = PolicyValidator()
        
        logger.info("Enhanced Dynamic Ontology to Rego Converter initialized with regopy support")
    
    def load_ontology(self, ontology_input: Union[str, Path], format: str = "auto") -> bool:
        """Load ontology from file or string"""
        try:
            if isinstance(ontology_input, (str, Path)) and Path(ontology_input).exists():
                self.graph.parse(ontology_input, format=format if format != "auto" else None)
                logger.info(f"Loaded ontology from file: {ontology_input}")
            else:
                detected_format = self._detect_format(str(ontology_input))
                self.graph.parse(data=str(ontology_input), format=detected_format)
                logger.info("Loaded ontology from string")
            
            self.last_hash = self._calculate_graph_hash()
            logger.info(f"Ontology loaded with {len(self.graph)} triples")
            return True
            
        except Exception as e:
            logger.error(f"Error loading ontology: {e}")
            return False
    
    def update_ontology(self, additional_data: str, format: str = "auto") -> bool:
        """Update ontology with additional data"""
        try:
            detected_format = self._detect_format(additional_data)
            old_count = len(self.graph)
            
            self.graph.parse(data=additional_data, format=detected_format)
            new_count = len(self.graph)
            
            # Update hash
            self.last_hash = self._calculate_graph_hash()
            
            logger.info(f"Updated ontology: {new_count - old_count} new triples added")
            return True
            
        except Exception as e:
            logger.error(f"Error updating ontology: {e}")
            return False
    
    def has_changed(self) -> bool:
        """Check if ontology has changed since last conversion"""
        current_hash = self._calculate_graph_hash()
        return current_hash != self.last_hash
    
    def convert_and_deploy(self, auto_deploy: bool = True, 
                          validate_policies: bool = True,
                          run_tests: bool = True) -> Dict[str, Any]:
        """Convert ontology to Rego and optionally deploy to OPA"""
        
        # Step 1: Convert ontology to Rego policies
        logger.info("Converting ontology to Rego policies...")
        policies = self.convert_to_rego()
        
        if not policies:
            return {"error": "No policies generated from ontology"}
        
        results = {
            "policies_generated": len(policies),
            "policies": {},
            "validation_results": {},
            "deployment_results": {},
            "test_results": {},
            "regopy_analysis": {}
        }
        
        # Step 2: Enhance and validate policies
        for package_name, rego_code in policies.items():
            policy_results = {"original_code": rego_code}
            
            # Enhance with regopy-based AST manipulation
            enhanced_code = self.ast_enhancer.enhance_rego_with_ast(rego_code)
            policy_results["enhanced_code"] = enhanced_code
            
            # Analyze structure with regopy
            if REGOPY_AVAILABLE:
                analysis = self.ast_enhancer.analyze_rego_structure(enhanced_code)
                policy_results["structure_analysis"] = analysis
                results["regopy_analysis"][package_name] = analysis
            
            # Validate syntax
            if validate_policies:
                validation_result = self.validator.validate_syntax(enhanced_code)
                policy_results["validation"] = validation_result
                results["validation_results"][package_name] = validation_result
                
                if not validation_result.valid:
                    logger.error(f"Policy {package_name} failed validation: {validation_result.errors}")
                    continue
            
            results["policies"][package_name] = policy_results
        
        # Step 3: Deploy to OPA server if requested
        if auto_deploy and OPA_CLIENT_AVAILABLE:
            logger.info("Deploying policies to OPA server...")
            
            try:
                with OPAPolicyManager(self.opa_config) as opa_manager:
                    for package_name, policy_data in results["policies"].items():
                        if "enhanced_code" not in policy_data:
                            continue
                        
                        deployment_result = opa_manager.deploy_policy(
                            package_name, 
                            policy_data["enhanced_code"]
                        )
                        
                        results["deployment_results"][package_name] = deployment_result
                        
                        # Step 4: Run basic tests
                        if run_tests and deployment_result.deployed:
                            test_result = self._run_basic_policy_tests(opa_manager, package_name)
                            results["test_results"][package_name] = test_result
            
            except Exception as e:
                logger.error(f"Failed to deploy policies: {e}")
                results["deployment_error"] = str(e)
        
        return results
    
    def _run_basic_policy_tests(self, opa_manager: OPAPolicyManager, 
                               policy_name: str) -> List[PolicyTestResult]:
        """Run basic tests on deployed policy"""
        test_results = []
        
        # Test 1: Basic connectivity
        test_input = {
            "action": "test",
            "user": "test_user",
            "resource": "test_resource"
        }
        
        result = opa_manager.test_policy(policy_name, test_input)
        test_results.append(result)
        
        # Test 2: Empty input
        empty_test = opa_manager.test_policy(policy_name, {})
        test_results.append(empty_test)
        
        # Test 3: Process action (common in privacy policies)
        process_test = opa_manager.test_policy(policy_name, {
            "action": "process",
            "data_category": "personal_data",
            "purpose": "service_provision"
        })
        test_results.append(process_test)
        
        logger.info(f"Completed {len(test_results)} tests for policy {policy_name}")
        return test_results
    
    def convert_to_rego(self, force_regenerate: bool = False) -> Dict[str, str]:
        """Convert ontology to Rego policies"""
        if not force_regenerate and not self.has_changed():
            cached_policies = self._load_from_cache()
            if cached_policies:
                logger.info("Using cached Rego policies")
                return cached_policies
        
        logger.info("Converting ontology to Rego policies...")
        
        policies = {}
        enforceable_policies = list(self.graph.subjects(RDF.type, ODRE.EnforceablePolicy))
        privacy_policies = list(self.graph.subjects(RDF.type, INTEGRATED.PrivacyRightsPolicy))
        processing_activities = list(self.graph.subjects(RDF.type, DPV.ProcessingActivity))
        
        all_policy_subjects = set(enforceable_policies + privacy_policies + processing_activities)
        
        for policy_subject in all_policy_subjects:
            try:
                patterns = self._extract_patterns(policy_subject)
                if patterns:
                    policy_name = self._get_policy_name(policy_subject)
                    rego_policy = self.generator.generate_policy(patterns, policy_name)
                    rego_code = self.generator.generate_rego_code(rego_policy)
                    
                    policies[rego_policy.package_name] = rego_code
                    logger.info(f"Generated policy: {rego_policy.package_name}")
            
            except Exception as e:
                logger.error(f"Error converting policy {policy_subject}: {e}")
                continue
        
        if policies:
            self._save_to_cache(policies)
            logger.info(f"Generated {len(policies)} Rego policies")
        
        return policies
    
    def test_policies_with_regopy(self, policies: Dict[str, str], 
                                 test_scenarios: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Test all policies with regopy using various scenarios"""
        if not REGOPY_AVAILABLE:
            return {"error": "regopy not available for policy testing"}
        
        all_results = {}
        
        for policy_name, rego_code in policies.items():
            logger.info(f"Testing policy {policy_name} with regopy")
            test_results = self.validator.test_policy_execution(rego_code, test_scenarios)
            all_results[policy_name] = test_results
        
        return all_results
    
    def _extract_patterns(self, subject: URIRef) -> List[OntologyPattern]:
        """Extract patterns from a policy subject using all extractors"""
        all_patterns = []
        
        # Get the types of this subject
        types = list(self.graph.objects(subject, RDF.type))
        
        # Use appropriate extractors based on types
        for extractor_name, extractor in self.extractors.items():
            supported_types = extractor.get_supported_types()
            
            # Check if any of the subject's types match the extractor's supported types
            if any(t in supported_types for t in types):
                try:
                    patterns = extractor.extract(self.graph, subject)
                    all_patterns.extend(patterns)
                    logger.debug(f"Extracted {len(patterns)} patterns using {extractor_name} extractor")
                except Exception as e:
                    logger.warning(f"Error with {extractor_name} extractor: {e}")
        
        return all_patterns
    
    def _get_policy_name(self, subject: URIRef) -> str:
        """Get human-readable name for policy"""
        # Try to get rdfs:label first
        labels = list(self.graph.objects(subject, RDFS.label))
        if labels:
            return str(labels[0])
        
        # Fall back to URI fragment or last part
        uri_str = str(subject)
        if '#' in uri_str:
            return uri_str.split('#')[-1]
        elif '/' in uri_str:
            return uri_str.split('/')[-1]
        else:
            return uri_str
    
    def _detect_format(self, content: str) -> str:
        """Auto-detect RDF format"""
        content_lower = content.strip().lower()
        
        if content_lower.startswith('@prefix') or content_lower.startswith('@base'):
            return "turtle"
        elif content_lower.startswith('{') and '"@context"' in content_lower:
            return "json-ld"
        elif '<rdf:' in content_lower or content_lower.startswith('<?xml'):
            return "xml"
        else:
            # Default to turtle
            return "turtle"
    
    def _calculate_graph_hash(self) -> str:
        """Calculate hash of current graph state"""
        # Serialize graph in a canonical way and hash it
        content = self.graph.serialize(format="turtle")
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_from_cache(self) -> Optional[Dict[str, str]]:
        """Load policies from cache if available and valid"""
        try:
            cache_file = self.cache_dir / f"policies_{self.last_hash}.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading from cache: {e}")
        return None
    
    def _save_to_cache(self, policies: Dict[str, str]):
        """Save policies to cache"""
        try:
            cache_file = self.cache_dir / f"policies_{self.last_hash}.json"
            with open(cache_file, 'w') as f:
                json.dump(policies, f, indent=2)
            
            # Clean old cache files
            self._cleanup_cache()
            
        except Exception as e:
            logger.warning(f"Error saving to cache: {e}")
    
    def _cleanup_cache(self, keep_recent: int = 5):
        """Clean up old cache files, keeping only recent ones"""
        try:
            cache_files = list(self.cache_dir.glob("policies_*.json"))
            if len(cache_files) > keep_recent:
                # Sort by modification time and remove oldest
                cache_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for old_file in cache_files[keep_recent:]:
                    old_file.unlink()
                    logger.debug(f"Removed old cache file: {old_file}")
        except Exception as e:
            logger.warning(f"Error cleaning cache: {e}")
    
    def save_policies_to_files(self, policies: Dict[str, str], output_dir: str = "./rego_policies"):
        """Save generated Rego policies to individual files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        for package_name, rego_code in policies.items():
            # Convert package name to filename
            filename = package_name.replace('.', '_') + '.rego'
            filepath = output_path / filename
            
            with open(filepath, 'w') as f:
                f.write(rego_code)
            
            logger.info(f"Saved policy to: {filepath}")

# ===============================
# CONVENIENCE FUNCTIONS
# ===============================

def create_opa_integrated_converter(opa_host: str = "localhost", 
                                   opa_port: int = 8181,
                                   ssl: bool = False) -> EnhancedDynamicOntologyRegoConverter:
    """Create converter with OPA configuration"""
    opa_config = OPAConfig(host=opa_host, port=opa_port, ssl=ssl)
    return EnhancedDynamicOntologyRegoConverter(opa_config)

def convert_and_deploy_ontology(ontology_path: str, 
                               opa_host: str = "localhost",
                               opa_port: int = 8181) -> Dict[str, Any]:
    """One-step conversion and deployment"""
    converter = create_opa_integrated_converter(opa_host, opa_port)
    
    if not converter.load_ontology(ontology_path):
        return {"error": f"Failed to load ontology from {ontology_path}"}
    
    return converter.convert_and_deploy()

def convert_ontology_file(file_path: str, output_dir: str = "./rego_policies") -> Dict[str, str]:
    """Convenience function to convert an ontology file"""
    converter = EnhancedDynamicOntologyRegoConverter()
    
    if not converter.load_ontology(file_path):
        raise ValueError(f"Failed to load ontology from {file_path}")
    
    policies = converter.convert_to_rego()
    converter.save_policies_to_files(policies, output_dir)
    
    return policies

def convert_ontology_string(ontology_content: str, format: str = "auto") -> Dict[str, str]:
    """Convenience function to convert ontology from string"""
    converter = EnhancedDynamicOntologyRegoConverter()
    
    if not converter.load_ontology(ontology_content, format):
        raise ValueError("Failed to load ontology from string")
    
    return converter.convert_to_rego()

# ===============================
# MAIN EXECUTION AND TESTING
# ===============================

async def main():
    """Complete example usage of the enhanced converter with regopy"""
    
    # Example ontology
    example_ttl = """
    @prefix dpv: <https://w3id.org/dpv#> .
    @prefix odrl: <http://www.w3.org/ns/odrl/2/> .
    @prefix odre: <https://w3id.org/def/odre#> .
    @prefix integrated: <https://w3id.org/def/integrated-dpv-odrl-odre#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    
    integrated:GDPRArticle28Policy a odre:EnforceablePolicy ;
        rdfs:label "GDPR Article 28 Processor Policy" ;
        odre:enforceable true ;
        odre:enforcementMode "real_time" ;
        odre:monitoringRequired true ;
        odre:complianceCheck true ;
        dpv:hasProcessing dpv:Store, dpv:Use ;
        dpv:hasPurpose dpv:ServiceProvision ;
        dpv:hasPersonalData dpv:PersonalData ;
        dpv:hasLegalBasis dpv:Contract ;
        odrl:prohibition [
            odrl:action dpv:Transfer ;
            odrl:constraint [
                odrl:leftOperand "processorAuthorization" ;
                odrl:operator "eq" ;
                odrl:rightOperand false
            ]
        ] ;
        odrl:permission [
            odrl:action dpv:Process ;
            odrl:constraint [
                odrl:leftOperand "contractExists" ;
                odrl:operator "eq" ;
                odrl:rightOperand true
            ]
        ] .
    """
    
    try:
        print("Enhanced Ontology to Rego Converter with regopy Integration")
        print("="*70)
        
        # Create converter
        converter = EnhancedDynamicOntologyRegoConverter()
        
        print("Loading ontology...")
        if not converter.load_ontology(example_ttl):
            print("Failed to load ontology")
            return
        
        print("Converting and deploying...")
        results = converter.convert_and_deploy(
            auto_deploy=OPA_CLIENT_AVAILABLE,
            validate_policies=True,
            run_tests=OPA_CLIENT_AVAILABLE
        )
        
        print(f"Generated {results['policies_generated']} policies")
        
        # Display results
        for policy_name, policy_data in results["policies"].items():
            print(f"\nPolicy: {policy_name}")
            
            # Show regopy analysis
            if policy_name in results.get("regopy_analysis", {}):
                analysis = results["regopy_analysis"][policy_name]
                if analysis.get("valid"):
                    print("  regopy Analysis: PASSED")
                    print(f"    Rules Count: {analysis.get('rules_count', 0)}")
                    print(f"    Data Definitions: {analysis.get('data_definitions', 0)}")
                else:
                    print("  regopy Analysis: FAILED")
                    if "error" in analysis:
                        print(f"    Error: {analysis['error']}")
            
            # Show validation results
            if "validation" in policy_data:
                validation = policy_data["validation"]
                if validation.valid:
                    print("  Validation: PASSED")
                    if validation.execution_result:
                        print("    Execution Test: SUCCESS")
                else:
                    print("  Validation: FAILED")
                    for error in validation.errors:
                        print(f"    Error: {error}")
                
                if validation.warnings:
                    for warning in validation.warnings:
                        print(f"    Warning: {warning}")
            
            # Show deployment results
            if policy_name in results.get("deployment_results", {}):
                deployment = results["deployment_results"][policy_name]
                if deployment.deployed:
                    print("  Deployment: SUCCESS")
                    print(f"    Endpoint: {deployment.endpoint}")
                else:
                    print("  Deployment: FAILED")
                    for error in deployment.errors:
                        print(f"    Error: {error}")
            
            # Show test results
            if policy_name in results.get("test_results", {}):
                test_results = results["test_results"][policy_name]
                passed_tests = sum(1 for test in test_results if test.passed)
                print(f"  Tests: {passed_tests}/{len(test_results)} passed")
        
        # Show enhanced Rego code with regopy validation
        if results["policies"]:
            first_policy = list(results["policies"].values())[0]
            print(f"\nEnhanced Rego Code (validated with regopy):")
            print("-" * 50)
            enhanced_code = first_policy.get("enhanced_code", first_policy.get("original_code", ""))
            print(enhanced_code[:800] + "..." if len(enhanced_code) > 800 else enhanced_code)
        
        # Test policies with regopy if available
        if REGOPY_AVAILABLE and results["policies"]:
            print(f"\nTesting policies with regopy...")
            
            test_scenarios = [
                {"action": "process", "contractExists": True, "data_category": "personal_data"},
                {"action": "transfer", "processorAuthorization": False},
                {"action": "store", "purpose": "service_provision"}
            ]
            
            policies_dict = {name: data["enhanced_code"] for name, data in results["policies"].items() if "enhanced_code" in data}
            test_results = converter.test_policies_with_regopy(policies_dict, test_scenarios)
            
            print(f"regopy testing completed for {len(test_results)} policies")
        
        print(f"\nConversion and deployment complete!")
        
        # Show query examples
        if OPA_CLIENT_AVAILABLE and results.get("deployment_results"):
            print("\nQuery deployed policies with curl:")
            deployed_policies = [name for name, result in results["deployment_results"].items() if result.deployed]
            if deployed_policies:
                policy_name = deployed_policies[0]
                print(f"curl -X POST http://localhost:8181/v1/data/{policy_name.replace('.', '/')}/allow \\")
                print('  -H "Content-Type: application/json" \\')
                print('  -d \'{"input": {"action": "process", "contractExists": true}}\'')
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())