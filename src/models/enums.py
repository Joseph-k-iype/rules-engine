"""
Enumeration classes for the legislation rules converter.
Enhanced with decision-making capabilities.
"""
from enum import Enum


class DataDomain(str, Enum):
    """Data domains as per privacy regulations."""
    DATA_TRANSFER = "data_transfer"
    DATA_USAGE = "data_usage" 
    DATA_STORAGE = "data_storage"
    DATA_COLLECTION = "data_collection"
    DATA_DELETION = "data_deletion"


class DataRole(str, Enum):
    """Roles in data processing - Updated without supervisory_authority."""
    CONTROLLER = "controller"
    PROCESSOR = "processor"
    JOINT_CONTROLLER = "joint_controller"
    DATA_SUBJECT = "data_subject"


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


class DocumentLevel(str, Enum):
    """Document processing levels."""
    LEVEL_1 = "level_1"  # Actual legislation
    LEVEL_2 = "level_2"  # Regulator guidance
    LEVEL_3 = "level_3"  # Additional guidance


class ProcessingPurpose(str, Enum):
    """GDPR-compliant processing purposes."""
    CONSENT = "consent"
    CONTRACTUAL_NECESSITY = "contractual_necessity"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class LegalBasis(str, Enum):
    """GDPR-compliant legal basis."""
    CONSENT = "consent"
    CONTRACTUAL_OBLIGATION = "contractual_obligation"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_INTEREST_OFFICIAL_AUTHORITY = "public_interest_official_authority"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class DecisionOutcome(str, Enum):
    """Decision outcomes for rule evaluation."""
    YES = "yes"
    NO = "no"
    MAYBE = "maybe"


class DecisionType(str, Enum):
    """Types of decisions that can be made."""
    DATA_TRANSFER = "data_transfer"
    DATA_PROCESSING = "data_processing"
    DATA_COLLECTION = "data_collection"
    DATA_STORAGE = "data_storage"
    DATA_DELETION = "data_deletion"
    CONSENT_REQUIREMENT = "consent_requirement"
    ACCESS_PERMISSION = "access_permission"
    SHARING_PERMISSION = "sharing_permission"
    COMPLIANCE_STATUS = "compliance_status"


class DecisionContext(str, Enum):
    """Context in which decisions are made."""
    CROSS_BORDER_TRANSFER = "cross_border_transfer"
    INTERNAL_PROCESSING = "internal_processing"
    THIRD_PARTY_SHARING = "third_party_sharing"
    DATA_SUBJECT_REQUEST = "data_subject_request"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    SECURITY_ASSESSMENT = "security_assessment"