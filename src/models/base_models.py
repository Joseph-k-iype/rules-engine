"""
Base data models for the legislation rules converter.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .enums import (
    DataDomain, DataRole, DataCategory, ConditionOperator, 
    DocumentLevel, ProcessingPurpose, LegalBasis
)


class RuleAction(BaseModel):
    """Action that can be taken based on a rule - inferred from legislation."""
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Unique action identifier")
    action_type: str = Field(..., description="Type of action inferred from legislation")
    title: str = Field(..., description="Action title in simple English")
    description: str = Field(..., description="What must be done in simple English")
    priority: str = Field(..., description="Action priority based on legislative language")

    # Implementation details
    data_specific_steps: List[str] = Field(..., description="Specific steps for data handling")
    responsible_role: Optional[str] = Field(None, description="Who is responsible for this action")

    # Compliance context
    legislative_requirement: str = Field(..., description="Specific legislative requirement")
    data_impact: str = Field(..., description="How this affects data processing")
    verification_method: List[str] = Field(default_factory=list, description="How to verify completion")

    # Optional timeline
    timeline: Optional[str] = Field(None, description="Timeline if specified in legislation")

    # Metadata
    derived_from_text: str = Field(..., description="Legislative text this action was derived from")
    applicable_countries: List[str] = Field(default_factory=list, description="Countries where action applies")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in action relevance")


class UserAction(BaseModel):
    """Specific user action inferred from legislation."""
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Unique user action identifier")
    action_type: str = Field(..., description="Type of data action user must perform")
    title: str = Field(..., description="Clear action title in simple English")
    description: str = Field(..., description="What the user must do in simple English")
    priority: str = Field(..., description="Priority level based on legislative context")

    # User-specific implementation details
    user_data_steps: List[str] = Field(..., description="Concrete steps for user data handling")
    affected_data_categories: List[str] = Field(default_factory=list, description="Data categories affected")
    user_role_context: Optional[str] = Field(None, description="User's role when performing this action")

    # Legislative basis
    legislative_requirement: str = Field(..., description="Specific legal requirement")
    compliance_outcome: str = Field(..., description="What compliance outcome this achieves")
    user_verification_steps: List[str] = Field(default_factory=list, description="How user can verify completion")

    # Implementation guidance for users
    timeline: Optional[str] = Field(None, description="Timeline if specified in legislation")

    # Metadata
    derived_from_text: str = Field(..., description="Legislative text this action was derived from")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in action inference")


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
    document_level: DocumentLevel = Field(..., description="Document level this condition was extracted from")
    chunk_reference: Optional[str] = Field(None, description="Reference to source chunk if document was chunked")

    @field_validator('data_domain', mode='before')
    @classmethod
    def validate_data_domain(cls, v):
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
        return []

    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
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

    @field_validator('operator', mode='before')
    @classmethod
    def validate_operator(cls, v):
        if isinstance(v, str):
            try:
                return ConditionOperator(v)
            except ValueError:
                return ConditionOperator.EQUAL
        elif isinstance(v, ConditionOperator):
            return v
        return ConditionOperator.EQUAL

    @field_validator('document_level', mode='before')
    @classmethod
    def validate_document_level(cls, v):
        if isinstance(v, str):
            try:
                return DocumentLevel(v)
            except ValueError:
                return DocumentLevel.LEVEL_1
        elif isinstance(v, DocumentLevel):
            return v
        return DocumentLevel.LEVEL_1


class RuleEvent(BaseModel):
    """Event triggered when rule conditions are met."""
    type: str = Field(..., description="Type of event/action")
    params: Dict[str, Any] = Field(default_factory=dict, description="Event parameters")


class CountryMetadata(BaseModel):
    """Updated metadata for country configurations."""
    model_config = ConfigDict(validate_assignment=True)

    country: List[str] = Field(..., description="List of applicable countries")
    adequacy_country: List[str] = Field(default_factory=list, description="List of adequacy countries")
    file_level_1: Optional[str] = Field(None, description="Level 1 document (actual legislation)")
    file_level_2: Optional[str] = Field(None, description="Level 2 document (regulator guidance)")
    file_level_3: Optional[str] = Field(None, description="Level 3 document (additional guidance)")

    @field_validator('country', mode='after')
    @classmethod
    def validate_country_not_empty(cls, v):
        if not v:
            raise ValueError("At least one country must be specified")
        return v


class DocumentChunk:
    """Represents a chunk of a document."""
    def __init__(self, content: str, chunk_index: int, total_chunks: int, start_pos: int, end_pos: int):
        self.content = content
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.chunk_id = f"chunk_{chunk_index}_{total_chunks}"


class IntegratedRule(BaseModel):
    """Unified rule that combines DPV, ODRL, and ODRE elements."""

    id: str = Field(..., description="Unique rule identifier")
    type: str = Field(default="odre:EnforceablePolicy", description="Unified rule type")

    # DPV Properties - Updated for v2.1
    dpv_hasProcessing: List[str] = Field(default_factory=list, description="DPV: Processing operations")
    dpv_hasPurpose: List[str] = Field(default_factory=list, description="DPV: Purposes for processing") 
    dpv_hasPersonalData: List[str] = Field(default_factory=list, description="DPV: Personal data categories")
    dpv_hasDataController: Optional[str] = Field(None, description="DPV: Data controller")
    dpv_hasDataProcessor: Optional[str] = Field(None, description="DPV: Data processor")
    dpv_hasLegalBasis: Optional[str] = Field(None, description="DPV: Legal basis for processing")
    dpv_hasLocation: List[str] = Field(default_factory=list, description="DPV: Processing locations/countries")

    # DPV Actions - Dynamically inferred
    dpv_hasRuleAction: List[str] = Field(default_factory=list, description="DPV: Rule actions inferred from legislation")
    dpv_hasUserAction: List[str] = Field(default_factory=list, description="DPV: User actions inferred from legislation")

    # ODRL Properties
    odrl_permission: List[Dict[str, Any]] = Field(default_factory=list, description="ODRL: Permissions")
    odrl_prohibition: List[Dict[str, Any]] = Field(default_factory=list, description="ODRL: Prohibitions") 
    odrl_obligation: List[Dict[str, Any]] = Field(default_factory=list, description="ODRL: Obligations")

    # ODRE Properties
    odre_enforceable: bool = Field(default=True, description="ODRE: Enforceable flag")
    odre_enforcement_mode: str = Field(default="dual_action_based", description="ODRE: Enforcement mode")
    odre_action_inference: bool = Field(default=True, description="ODRE: Action inference enabled")
    odre_user_action_inference: bool = Field(default=True, description="ODRE: User action inference enabled")

    # Processing metadata
    source_document_levels: List[str] = Field(default_factory=list, description="Document levels processed")
    chunk_references: List[str] = Field(default_factory=list, description="Chunk references if document was chunked")

    # Metadata
    source_legislation: str = Field(..., description="Source legislation")
    source_article: str = Field(..., description="Source article/section")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(..., ge=0.0, le=1.0)