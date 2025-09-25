"""
Data models for the legislation rules converter.
Enhanced with combined actions structure and decision-making capabilities.
"""

from .enums import (
    DataDomain, DataRole, DataCategory, ConditionOperator, 
    DocumentLevel, ProcessingPurpose, LegalBasis,
    DecisionOutcome, DecisionType, DecisionContext
)
from .base_models import (
    RuleAction, UserAction, CombinedAction, RuleCondition, RuleEvent, 
    CountryMetadata, DocumentChunk, IntegratedRule, RuleDecision
)
from .rules import LegislationRule, ExtractionResult

__all__ = [
    # Enums
    "DataDomain",
    "DataRole", 
    "DataCategory",
    "ConditionOperator",
    "DocumentLevel",
    "ProcessingPurpose",
    "LegalBasis",
    # Decision Enums
    "DecisionOutcome",
    "DecisionType", 
    "DecisionContext",
    # Base Models
    "RuleAction",
    "UserAction",
    "CombinedAction",  # New combined action class
    "RuleCondition",
    "RuleEvent",
    "CountryMetadata",
    "DocumentChunk",
    "IntegratedRule",
    # Decision Models
    "RuleDecision",
    # Rules
    "LegislationRule",
    "ExtractionResult"
]