"""
Enumeration classes for the legislation rules converter with decision-making capabilities.
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


class DecisionType(str, Enum):
    """Decision types for rule-based outcomes."""
    YES = "yes"           # Action is allowed unconditionally
    NO = "no"            # Action is prohibited/forbidden
    MAYBE = "maybe"      # Action is allowed conditionally (requires additional steps)
    UNKNOWN = "unknown"  # Decision cannot be determined from available information


class DecisionContext(str, Enum):
    """Context for decision-making."""
    DATA_TRANSFER = "data_transfer"
    DATA_PROCESSING = "data_processing"
    DATA_STORAGE = "data_storage"
    DATA_COLLECTION = "data_collection"
    DATA_SHARING = "data_sharing"
    DATA_DELETION = "data_deletion"
    CONSENT_MANAGEMENT = "consent_management"
    RIGHTS_EXERCISE = "rights_exercise"
    COMPLIANCE_VERIFICATION = "compliance_verification"


class RequiredActionType(str, Enum):
    """Types of actions required for conditional decisions."""
    DATA_MASKING = "data_masking"
    DATA_ENCRYPTION = "data_encryption"
    DATA_ANONYMIZATION = "data_anonymization"
    CONSENT_OBTAINMENT = "consent_obtainment"
    CONSENT_VERIFICATION = "consent_verification"
    LEGAL_BASIS_ESTABLISHMENT = "legal_basis_establishment"
    ADEQUACY_VERIFICATION = "adequacy_verification"
    SAFEGUARDS_IMPLEMENTATION = "safeguards_implementation"
    DOCUMENTATION_COMPLETION = "documentation_completion"
    AUDIT_COMPLETION = "audit_completion"
    APPROVAL_OBTAINMENT = "approval_obtainment"
    NOTIFICATION_COMPLETION = "notification_completion"
    IMPACT_ASSESSMENT = "impact_assessment"
    SECURITY_MEASURES = "security_measures"
    ACCESS_CONTROLS = "access_controls"