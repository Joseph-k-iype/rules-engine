"""
Data models for the Legislation Rules Converter.
Contains all Pydantic models for rules, conditions, events, and standards integration.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .config import ModelConfig

class DataDomain(str, Enum):
    """Data domains as per privacy regulations."""
    DATA_TRANSFER = "data_transfer"
    DATA_USAGE = "data_usage" 
    DATA_STORAGE = "data_storage"

class DataRole(str, Enum):
    """Roles in data processing."""
    CONTROLLER = "controller"
    PROCESSOR = "processor"
    JOINT_CONTROLLER = "joint_controller"

class DataCategory(str, Enum):
    """Categories of personal data."""
    PERSONAL_DATA = "personal_data"
    SENSITIVE_DATA = "sensitive_data"
    BIOMETRIC_DATA = "biometric_data"
    HEALTH_DATA = "health_data"
    FINANCIAL_DATA = "financial_data"
    LOCATION_DATA = "location_data"
    BEHAVIORAL_DATA = "behavioral_data"
    IDENTIFICATION_DATA = "identification_data"

class ConditionOperator(str, Enum):
    """Operators for rule conditions."""
    EQUAL = "equal"
    NOT_EQUAL = "notEqual"
    GREATER_THAN = "greaterThan"
    LESS_THAN = "lessThan"
    GREATER_THAN_EQUAL = "greaterThanInclusive"
    LESS_THAN_EQUAL = "lessThanInclusive"
    CONTAINS = "contains"
    NOT_CONTAINS = "doesNotContain"
    IN = "in"
    NOT_IN = "notIn"

class RuleCondition(BaseModel):
    """Individual condition within a rule."""
    model_config = ConfigDict(use_enum_values=True)
    
    fact: str = Field(..., description="The fact/data point to evaluate")
    operator: ConditionOperator = Field(..., description="Comparison operator")
    value: Union[str, int, float, bool, List[Any]] = Field(..., description="Value to compare against")
    path: Optional[str] = Field(None, description="JSONPath to navigate nested objects")
    description: str = Field(..., description="Human-readable description of this condition")
    data_domain: List[DataDomain] = Field(default_factory=list, description="Applicable data domains")
    role: Optional[DataRole] = Field(None, description="Role this condition applies to")
    reasoning: str = Field(..., description="LLM reasoning for why this condition was extracted")

    @field_validator('data_domain', mode='before')
    @classmethod
    def validate_data_domain(cls, v):
        """Ensure data_domain is properly converted to enum values."""
        if not v:
            return []
        
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, str):
                    try:
                        result.append(DataDomain(item))
                    except ValueError:
                        continue
                elif isinstance(item, DataDomain):
                    result.append(item)
            return result
        else:
            return []

    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        """Ensure role is properly converted to enum - allow None."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return DataRole(v)
            except ValueError:
                return None
        elif isinstance(v, DataRole):
            return v
        else:
            return None

    @field_validator('operator', mode='before')
    @classmethod
    def validate_operator(cls, v):
        """Ensure operator is properly converted to enum."""
        if isinstance(v, str):
            try:
                return ConditionOperator(v)
            except ValueError:
                return ConditionOperator.EQUAL
        elif isinstance(v, ConditionOperator):
            return v
        else:
            return ConditionOperator.EQUAL

class RuleEvent(BaseModel):
    """Event triggered when rule conditions are met."""
    type: str = Field(..., description="Type of event/action")
    params: Dict[str, Any] = Field(default_factory=dict, description="Event parameters")

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
    priority: int = Field(default=1, description="Rule priority (1-10)")
    
    # Required fields with validation
    primary_impacted_role: Optional[DataRole] = Field(None, description="Primary role most impacted by this rule")
    secondary_impacted_role: Optional[DataRole] = Field(None, description="Secondary role impacted by this rule")
    data_category: List[DataCategory] = Field(default_factory=list, description="Categories of data this rule applies to")
    
    # Country metadata
    applicable_countries: List[str] = Field(default_factory=list, description="Countries where this rule applies")
    adequacy_countries: List[str] = Field(default_factory=list, description="Adequacy countries (optional)")
    
    # Metadata
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_method: str = Field(default="llm_analysis")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    
    @field_validator('conditions', mode='after')
    @classmethod
    def validate_conditions_structure(cls, v):
        """Ensure conditions follow json-rules-engine format."""
        if not isinstance(v, dict):
            raise ValueError("Conditions must be a dictionary")
        
        valid_keys = {'all', 'any', 'not'}
        if not any(key in valid_keys for key in v.keys()):
            raise ValueError("Conditions must contain 'all', 'any', or 'not' keys")
        return v

    @field_validator('primary_impacted_role', mode='before')
    @classmethod
    def validate_primary_role(cls, v):
        """Ensure primary role is properly converted to enum."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return DataRole(v)
            except ValueError:
                return None
        elif isinstance(v, DataRole):
            return v
        else:
            return None

    @field_validator('secondary_impacted_role', mode='before')
    @classmethod
    def validate_secondary_role(cls, v):
        """Ensure secondary role is properly converted to enum."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return DataRole(v)
            except ValueError:
                return None
        elif isinstance(v, DataRole):
            return v
        else:
            return None

    @field_validator('data_category', mode='before')
    @classmethod
    def validate_data_category(cls, v):
        """Ensure data categories are properly converted to enums."""
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
        else:
            return []

class DPVRule(BaseModel):
    """Rule expressed using DPV vocabulary."""
    id: str = Field(..., description="Unique rule identifier")
    type: str = Field(default="dpv:ProcessingActivity", description="DPV rule type")
    
    # Core DPV Properties
    hasProcessing: List[str] = Field(..., description="Processing operations")
    hasPurpose: List[str] = Field(..., description="Purposes for processing") 
    hasPersonalData: List[str] = Field(..., description="Personal data categories")
    hasDataController: Optional[str] = Field(None, description="Data controller")
    hasDataProcessor: Optional[str] = Field(None, description="Data processor")
    hasLegalBasis: Optional[str] = Field(None, description="Legal basis for processing")
    hasTechnicalMeasure: List[str] = Field(default_factory=list, description="Technical measures")
    hasOrganisationalMeasure: List[str] = Field(default_factory=list, description="Organisational measures")
    
    # Location and Context
    hasLocation: List[str] = Field(default_factory=list, description="Processing locations/countries")
    hasRecipient: List[str] = Field(default_factory=list, description="Data recipients")
    hasStorageCondition: Optional[str] = Field(None, description="Storage conditions")
    hasDataSource: Optional[str] = Field(None, description="Data source")
    
    # Metadata
    source_legislation: str = Field(..., description="Source legislation")
    source_article: str = Field(..., description="Source article/section")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class ODRLPolicy(BaseModel):
    """ODRL Policy structure."""
    context: str = Field(default="http://www.w3.org/ns/odrl.jsonld", description="JSON-LD context")
    type: str = Field(default="Policy", description="ODRL policy type")
    uid: str = Field(..., description="Unique policy identifier")
    
    permission: List[Dict[str, Any]] = Field(default_factory=list, description="Permissions")
    prohibition: List[Dict[str, Any]] = Field(default_factory=list, description="Prohibitions") 
    obligation: List[Dict[str, Any]] = Field(default_factory=list, description="Obligations")
    
    # Metadata
    profile: Optional[str] = Field(None, description="ODRL profile")
    inheritFrom: Optional[str] = Field(None, description="Inherited policy")
    conflict: Optional[str] = Field(None, description="Conflict resolution strategy")

class ODRLRule(BaseModel):
    """Individual ODRL rule (permission, prohibition, obligation)."""
    target: str = Field(..., description="Target asset")
    action: Union[str, List[str]] = Field(..., description="Action(s)")
    assigner: Optional[str] = Field(None, description="Party granting the rule")
    assignee: Optional[str] = Field(None, description="Party receiving the rule")
    constraint: List[Dict[str, Any]] = Field(default_factory=list, description="Constraints")
    duty: List[Dict[str, Any]] = Field(default_factory=list, description="Duties")
    
class ODRLConstraint(BaseModel):
    """ODRL constraint structure."""
    leftOperand: str = Field(..., description="Left operand")
    operator: str = Field(..., description="Comparison operator")
    rightOperand: Any = Field(..., description="Right operand value")
    dataType: Optional[str] = Field(None, description="Data type")
    unit: Optional[str] = Field(None, description="Unit of measurement")

class IntegratedRule(BaseModel):
    """Unified rule that combines DPV, ODRL, and ODRE elements."""
    
    # Core Identification
    id: str = Field(..., description="Unique rule identifier")
    type: str = Field(default="odre:EnforceablePolicy", description="Unified rule type")
    
    # DPV Properties
    dpv_hasProcessing: List[str] = Field(default_factory=list, description="DPV: Processing operations")
    dpv_hasPurpose: List[str] = Field(default_factory=list, description="DPV: Purposes for processing") 
    dpv_hasPersonalData: List[str] = Field(default_factory=list, description="DPV: Personal data categories")
    dpv_hasDataController: Optional[str] = Field(None, description="DPV: Data controller")
    dpv_hasDataProcessor: Optional[str] = Field(None, description="DPV: Data processor")
    dpv_hasLegalBasis: Optional[str] = Field(None, description="DPV: Legal basis for processing")
    dpv_hasTechnicalMeasure: List[str] = Field(default_factory=list, description="DPV: Technical measures")
    dpv_hasOrganisationalMeasure: List[str] = Field(default_factory=list, description="DPV: Organisational measures")
    dpv_hasLocation: List[str] = Field(default_factory=list, description="DPV: Processing locations/countries")
    dpv_hasRecipient: List[str] = Field(default_factory=list, description="DPV: Data recipients")
    
    # ODRL Properties
    odrl_permission: List[Dict[str, Any]] = Field(default_factory=list, description="ODRL: Permissions")
    odrl_prohibition: List[Dict[str, Any]] = Field(default_factory=list, description="ODRL: Prohibitions") 
    odrl_obligation: List[Dict[str, Any]] = Field(default_factory=list, description="ODRL: Obligations")
    odrl_profile: Optional[str] = Field(None, description="ODRL: Profile")
    odrl_conflict: Optional[str] = Field(None, description="ODRL: Conflict resolution strategy")
    
    # ODRE Properties (Enforcement Framework)
    odre_enforceable: bool = Field(default=True, description="ODRE: Enforceable flag")
    odre_enforcement_mode: str = Field(default="real_time", description="ODRE: Enforcement mode")
    odre_monitoring_required: bool = Field(default=True, description="ODRE: Monitoring requirement")
    odre_compliance_check: bool = Field(default=True, description="ODRE: Compliance checking")
    odre_temporal_enforcement: bool = Field(default=False, description="ODRE: Temporal enforcement")
    
    # Metadata
    source_legislation: str = Field(..., description="Source legislation")
    source_article: str = Field(..., description="Source article/section")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class RuleChangeEvent(BaseModel):
    """Event model for rule changes."""
    event_type: str = Field(..., description="Type of change event")
    rule_id: str = Field(..., description="ID of the affected rule")
    old_rule: Optional[LegislationRule] = Field(None, description="Previous rule state")
    new_rule: Optional[LegislationRule] = Field(None, description="New rule state")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(..., description="Source of the change")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional change metadata")

class ProcessingStatus(str, Enum):
    """Status of processing operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExtractionJob(BaseModel):
    """Job model for extraction tasks."""
    job_id: str = Field(..., description="Unique job identifier")
    source_file: str = Field(..., description="Source file being processed")
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    error_message: Optional[str] = Field(None)
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    extracted_rules_count: int = Field(default=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)