"""
Strict Pydantic models for Policy as Code Platform
Enforces comprehensive validation with detailed error reporting
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    Field,
    validator,
    root_validator,
    constr,
    conint,
    confloat,
    EmailStr,
    HttpUrl,
    ValidationError as PydanticValidationError,
    ConfigDict,
)


# Strict configuration for Pydantic models
STRICT_CONFIG = ConfigDict(
    # Strict mode - no extra fields allowed
    extra="forbid",
    # Validate assignment - validate on field assignment
    validate_assignment=True,
    # Use enum values
    use_enum_values=True,
    # Validate default values
    validate_default=True,
    # Forbid mutation
    frozen=True,
    # Strict string validation
    str_strip_whitespace=True,
    # Validate JSON schema
    json_schema_extra={"examples": []},
)


# ============================================================================
# CORE IDENTIFIER MODELS
# ============================================================================


class PersonIdType(str, Enum):
    """Valid person ID types"""

    HETU = "hetu"
    VTJ = "vtj"
    PASSPORT = "passport"
    OTHER = "other"


class PersonId(BaseModel):
    """Strict person identifier validation"""

    model_config = STRICT_CONFIG

    id: constr(
        pattern=r"^(\d{6}[+-A]\d{3}[0-9A-Z]|VTJ_\d+|PASSPORT_[A-Z0-9]+|OTHER_[A-Z0-9]+)$"
    ) = Field(
        ..., description="Person identifier (HETU, VTJ, Passport, or Other format)"
    )
    type: PersonIdType = Field(..., description="Type of identifier")
    verified: bool = Field(default=False, description="Whether ID is verified")
    verification_date: Optional[datetime] = Field(
        None, description="Date of verification"
    )

    @validator("id")
    def validate_id_format(cls, v, values):
        """Validate ID format matches type"""
        if "type" in values:
            id_type = values["type"]
            if id_type == PersonIdType.HETU and not v.startswith(
                ("VTJ_", "PASSPORT_", "OTHER_")
            ):
                import re

                if not re.match(r"^\d{6}[+-A]\d{3}[0-9A-Z]$", v):
                    raise ValueError("Invalid HETU format")
            elif id_type == PersonIdType.VTJ and not v.startswith("VTJ_"):
                raise ValueError("VTJ ID must start with VTJ_")
            elif id_type == PersonIdType.PASSPORT and not v.startswith("PASSPORT_"):
                raise ValueError("Passport ID must start with PASSPORT_")
            elif id_type == PersonIdType.OTHER and not v.startswith("OTHER_"):
                raise ValueError("Other ID must start with OTHER_")
        return v


# ============================================================================
# INCOME MODELS
# ============================================================================


class IncomeSource(str, Enum):
    """Income data sources"""

    VERO = "vero"
    KELA = "kela"
    MANUAL = "manual"
    EXTERNAL_API = "external_api"


class Income(BaseModel):
    """Strict income validation"""

    model_config = STRICT_CONFIG

    monthly_net_eur: confloat(ge=0, le=1000000) = Field(
        ..., description="Monthly net income in euros (0-1,000,000)"
    )
    source: IncomeSource = Field(..., description="Income data source")
    verification_status: Literal["verified", "pending", "failed"] = Field(
        default="pending", description="Income verification status"
    )
    verification_date: Optional[datetime] = Field(
        None, description="Date of verification"
    )
    tax_year: conint(ge=2020, le=2030) = Field(
        default=datetime.now().year, description="Tax year for income data"
    )
    currency: Literal["EUR"] = Field(default="EUR", description="Currency code")

    @validator("verification_date")
    def validate_verification_date(cls, v, values):
        """Validate verification date is not in future"""
        if v:
            now = datetime.now()
            # Handle timezone-aware datetimes
            if v.tzinfo is not None and now.tzinfo is None:
                now = now.replace(tzinfo=v.tzinfo)
            elif v.tzinfo is None and now.tzinfo is not None:
                v = v.replace(tzinfo=now.tzinfo)
            if v > now:
                raise ValueError("Verification date cannot be in the future")
        return v


# ============================================================================
# RESIDENCE MODELS
# ============================================================================


class ResidenceStatus(str, Enum):
    """Legal residence status"""

    CITIZEN = "citizen"
    PERMANENT_RESIDENT = "permanent_resident"
    TEMPORARY_RESIDENT = "temporary_resident"
    REFUGEE = "refugee"
    OTHER = "other"


class Residence(BaseModel):
    """Strict residence validation"""

    model_config = STRICT_CONFIG

    municipality_code: constr(pattern=r"^\d{3}$") = Field(
        ..., description="VTJ municipality code (3 digits)"
    )
    residence_status: ResidenceStatus = Field(..., description="Legal residence status")
    address: Optional[str] = Field(None, max_length=500, description="Full address")
    postal_code: Optional[constr(pattern=r"^\d{5}$")] = Field(
        None, description="Postal code (5 digits)"
    )
    country_code: Literal["FI"] = Field(default="FI", description="Country code")
    valid_from: Optional[datetime] = Field(
        None, description="Residence valid from date"
    )
    valid_to: Optional[datetime] = Field(None, description="Residence valid to date")

    @validator("valid_to")
    def validate_valid_to(cls, v, values):
        """Validate valid_to is after valid_from"""
        if v and "valid_from" in values and values["valid_from"]:
            valid_from = values["valid_from"]
            # Handle timezone-aware datetimes
            if v.tzinfo is not None and valid_from.tzinfo is None:
                valid_from = valid_from.replace(tzinfo=v.tzinfo)
            elif v.tzinfo is None and valid_from.tzinfo is not None:
                v = v.replace(tzinfo=valid_from.tzinfo)
            if v <= valid_from:
                raise ValueError("valid_to must be after valid_from")
        return v


# ============================================================================
# FAMILY MODELS
# ============================================================================


class RelationshipType(str, Enum):
    """Family relationship types"""

    CHILD = "child"
    SPOUSE = "spouse"
    PARENT = "parent"
    SIBLING = "sibling"
    OTHER = "other"


class CareResponsibility(str, Enum):
    """Care responsibility types"""

    CHILD_CARE = "child_care"
    ELDERLY_CARE = "elderly_care"
    DISABLED_CARE = "disabled_care"
    NONE = "none"


class Dependent(BaseModel):
    """Strict dependent person validation"""

    model_config = STRICT_CONFIG

    id: str = Field(
        ..., min_length=1, max_length=100, description="Dependent person ID"
    )
    relationship: RelationshipType = Field(
        ..., description="Relationship to main person"
    )
    age: conint(ge=0, le=150) = Field(..., description="Age in years")
    is_dependent: bool = Field(default=True, description="Whether person is dependent")
    care_level: Literal["none", "partial", "full"] = Field(
        default="none", description="Level of care required"
    )


class Family(BaseModel):
    """Strict family information validation"""

    model_config = STRICT_CONFIG

    dependents: List[Dependent] = Field(
        default_factory=list, max_items=20, description="Dependent persons"
    )
    care_responsibilities: List[CareResponsibility] = Field(
        default_factory=list, max_items=10, description="Care responsibilities"
    )
    household_size: conint(ge=1, le=20) = Field(..., description="Total household size")

    @validator("household_size")
    def validate_household_size(cls, v, values):
        """Validate household size matches dependents + 1"""
        if "dependents" in values:
            min_size = len(values["dependents"]) + 1  # +1 for main person
            if v < min_size:
                raise ValueError(f"household_size must be at least {min_size}")
        return v


# ============================================================================
# ECONOMIC ACTIVITY MODELS
# ============================================================================


class EmploymentStatus(str, Enum):
    """Employment status"""

    EMPLOYED = "employed"
    UNEMPLOYED = "unemployed"
    STUDENT = "student"
    RETIRED = "retired"
    DISABLED = "disabled"
    OTHER = "other"


class WorkCapacity(str, Enum):
    """Work capacity levels"""

    FULL = "full"
    PARTIAL = "partial"
    LIMITED = "limited"
    NONE = "none"


class WorkBarrier(str, Enum):
    """Barriers to work"""

    HEALTH = "health"
    CARE_RESPONSIBILITIES = "care_responsibilities"
    EDUCATION = "education"
    LANGUAGE = "language"
    TRANSPORTATION = "transportation"
    DISCRIMINATION = "discrimination"
    OTHER = "other"


class EconomicActivity(BaseModel):
    """Strict economic activity validation"""

    model_config = STRICT_CONFIG

    employment_status: EmploymentStatus = Field(
        ..., description="Current employment status"
    )
    work_capacity: WorkCapacity = Field(..., description="Work capacity level")
    barriers_to_work: List[WorkBarrier] = Field(
        default_factory=list, max_items=10, description="Barriers to work"
    )
    employer_name: Optional[str] = Field(
        None, max_length=200, description="Employer name"
    )
    job_title: Optional[str] = Field(None, max_length=100, description="Job title")
    work_hours_per_week: Optional[conint(ge=0, le=168)] = Field(
        None, description="Work hours per week"
    )


# ============================================================================
# ELIGIBILITY INPUT/OUTPUT MODELS
# ============================================================================


class EligibilityInput(BaseModel):
    """Strict eligibility input validation"""

    model_config = STRICT_CONFIG

    person_id: PersonId = Field(..., description="Person identifier")
    income: Income = Field(..., description="Income information")
    residence: Residence = Field(..., description="Residence information")
    family: Optional[Family] = Field(None, description="Family information")
    economic_activity: Optional[EconomicActivity] = Field(
        None, description="Economic activity information"
    )
    application_date: datetime = Field(
        default_factory=datetime.now, description="Application submission date"
    )
    application_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique application identifier",
    )

    @validator("application_date")
    def validate_application_date(cls, v):
        """Validate application date is not in future"""
        if v > datetime.now():
            raise ValueError("Application date cannot be in the future")
        return v


class DecisionOutcome(str, Enum):
    """Decision outcomes"""

    APPROVED = "APPROVED"
    DENIED = "DENIED"
    CONDITIONAL_APPROVAL = "CONDITIONAL_APPROVAL"
    DEFERRED = "DEFERRED"
    REQUIRES_APPEAL = "REQUIRES_APPEAL"


class ConditionType(str, Enum):
    """Condition types for conditional approval"""

    DOCUMENTATION = "documentation"
    VERIFICATION = "verification"
    TIME_LIMIT = "time_limit"
    REVIEW = "review"


class Condition(BaseModel):
    """Strict condition validation"""

    model_config = STRICT_CONFIG

    type: ConditionType = Field(..., description="Type of condition")
    description: str = Field(
        ..., min_length=10, max_length=1000, description="Condition description"
    )
    deadline: Optional[datetime] = Field(None, description="Condition deadline")
    is_met: bool = Field(default=False, description="Whether condition is met")

    @validator("deadline")
    def validate_deadline(cls, v):
        """Validate deadline is in future"""
        if v and v <= datetime.now():
            raise ValueError("Deadline must be in the future")
        return v


class LegalBasis(BaseModel):
    """Strict legal basis validation"""

    model_config = STRICT_CONFIG

    law_reference: HttpUrl = Field(..., description="ELI URI to legal basis")
    section: str = Field(
        ..., min_length=1, max_length=100, description="Specific section or article"
    )
    description: str = Field(
        ..., min_length=10, max_length=500, description="Human-readable legal basis"
    )
    effective_date: Optional[datetime] = Field(
        None, description="When law became effective"
    )
    expiry_date: Optional[datetime] = Field(None, description="When law expires")

    @validator("expiry_date")
    def validate_expiry_date(cls, v, values):
        """Validate expiry date is after effective date"""
        if v and "effective_date" in values and values["effective_date"]:
            effective_date = values["effective_date"]
            # Handle timezone-aware datetimes
            if v.tzinfo is not None and effective_date.tzinfo is None:
                effective_date = effective_date.replace(tzinfo=v.tzinfo)
            elif v.tzinfo is None and effective_date.tzinfo is not None:
                v = v.replace(tzinfo=effective_date.tzinfo)
            if v <= effective_date:
                raise ValueError("expiry_date must be after effective_date")
        return v


class EligibilityOutput(BaseModel):
    """Strict eligibility output validation"""

    model_config = STRICT_CONFIG

    decision: DecisionOutcome = Field(..., description="Primary decision outcome")
    basis: Dict[str, Any] = Field(..., description="Decision basis information")
    conditions: List[Condition] = Field(
        default_factory=list,
        max_items=20,
        description="Conditions for conditional approval",
    )
    legal_basis: List[LegalBasis] = Field(
        ..., min_items=1, max_items=10, description="Legal basis for the decision"
    )
    reasoning: List[str] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="Step-by-step reasoning for the decision",
    )
    confidence_score: confloat(ge=0.0, le=1.0) = Field(
        ..., description="Confidence score for the decision (0-1)"
    )
    next_review_date: Optional[datetime] = Field(
        None, description="Date for next review if applicable"
    )
    appeal_deadline: Optional[datetime] = Field(
        None, description="Appeal deadline if applicable"
    )
    appeal_info: Optional[Dict[str, Any]] = Field(
        None, description="Appeal information for denied decisions"
    )
    trace_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Trace identifier for audit"
    )

    @validator("next_review_date", "appeal_deadline")
    def validate_future_dates(cls, v):
        """Validate dates are in future"""
        if v:
            now = datetime.now()
            # Handle timezone-aware datetimes
            if v.tzinfo is not None and now.tzinfo is None:
                now = now.replace(tzinfo=v.tzinfo)
            elif v.tzinfo is None and now.tzinfo is not None:
                v = v.replace(tzinfo=now.tzinfo)
            if v <= now:
                raise ValueError("Date must be in the future")
        return v


# ============================================================================
# DECISION CONTEXT MODELS
# ============================================================================


class DecisionContext(BaseModel):
    """Strict decision context validation"""

    model_config = STRICT_CONFIG

    function_id: str = Field(
        ..., min_length=1, max_length=100, description="Decision function ID"
    )
    version: str = Field(
        ..., pattern=r"^\d+\.\d+\.\d+$", description="Function version (semantic)"
    )
    input_hash: str = Field(
        ..., pattern=r"^[a-f0-9]{64}$", description="SHA-256 input hash"
    )
    timestamp: datetime = Field(..., description="Decision execution timestamp")
    trace_id: str = Field(..., description="Trace identifier")
    client_id: Optional[str] = Field(
        None, max_length=100, description="Client identifier"
    )
    request_id: Optional[str] = Field(
        None, max_length=100, description="Request identifier"
    )

    @validator("timestamp")
    def validate_timestamp(cls, v):
        """Validate timestamp is not in future"""
        now = datetime.now()
        # Handle timezone-aware datetimes
        if v.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=v.tzinfo)
        elif v.tzinfo is None and now.tzinfo is not None:
            v = v.replace(tzinfo=now.tzinfo)
        if v > now:
            raise ValueError("Timestamp cannot be in the future")
        return v


class DecisionResult(BaseModel):
    """Strict decision result validation"""

    model_config = STRICT_CONFIG

    trace_id: str = Field(..., description="Trace identifier")
    function_id: str = Field(
        ..., min_length=1, max_length=100, description="Function ID"
    )
    version: str = Field(
        ..., pattern=r"^\d+\.\d+\.\d+$", description="Function version"
    )
    result: Dict[str, Any] = Field(..., description="Decision result data")
    execution_time_ms: conint(ge=0, le=300000) = Field(
        ..., description="Execution time in milliseconds (max 5 minutes)"
    )
    timestamp: datetime = Field(..., description="Result timestamp")
    success: bool = Field(..., description="Whether execution was successful")
    error_message: Optional[str] = Field(
        None, max_length=2000, description="Error message if failed"
    )
    input_hash: str = Field(
        ..., pattern=r"^[a-f0-9]{64}$", description="SHA-256 input hash"
    )
    output_hash: str = Field(
        ..., pattern=r"^[a-f0-9]{64}$", description="SHA-256 output hash"
    )

    @validator("error_message")
    def validate_error_message(cls, v, values):
        """Validate error message is present when success is False"""
        if "success" in values and not values["success"] and not v:
            raise ValueError("error_message is required when success is False")
        return v


# ============================================================================
# TRACE LEDGER MODELS
# ============================================================================


class TraceStatus(str, Enum):
    """Trace status values"""

    OK = "OK"
    ERROR = "ERROR"
    PENDING = "PENDING"


class TraceRecord(BaseModel):
    """Strict trace record validation"""

    model_config = STRICT_CONFIG

    trace_id: str = Field(..., description="Unique trace identifier")
    df_id: str = Field(
        ..., min_length=1, max_length=100, description="Decision function ID"
    )
    version: str = Field(
        ..., pattern=r"^\d+\.\d+\.\d+$", description="Function version"
    )
    df_hash: str = Field(
        ..., pattern=r"^sha256:[a-f0-9]{64}$", description="Function hash"
    )
    ts: datetime = Field(..., description="Timestamp")
    caller_id: str = Field(
        ..., pattern=r"^xroad:FI/ORG/[A-Za-z0-9_-]+$", description="X-Road caller ID"
    )
    cert_thumbprint: str = Field(
        ..., pattern=r"^[a-f0-9]{40}$", description="Certificate thumbprint"
    )
    request_nonce: str = Field(
        ..., min_length=16, max_length=64, description="Request nonce"
    )
    input_ref: str = Field(
        ..., pattern=r"^s3://[a-z0-9.-]+/.*$", description="S3 input reference"
    )
    output: Dict[str, Any] = Field(..., description="Decision output")
    prev_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$", description="Previous hash")
    chain_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$", description="Chain hash")
    status: TraceStatus = Field(..., description="Trace status")
    signature: Optional[str] = Field(
        None, pattern=r"^[A-Za-z0-9+/=]+$", description="Digital signature"
    )

    @validator("ts")
    def validate_timestamp(cls, v):
        """Validate timestamp is not in future"""
        now = datetime.now()
        # Handle timezone-aware datetimes
        if v.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=v.tzinfo)
        elif v.tzinfo is None and now.tzinfo is not None:
            v = v.replace(tzinfo=now.tzinfo)
        if v > now:
            raise ValueError("Timestamp cannot be in the future")
        return v


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================


class ValidationResult(BaseModel):
    """Validation result with detailed error information"""

    model_config = STRICT_CONFIG

    is_valid: bool = Field(..., description="Whether validation passed")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Detailed validation errors"
    )
    warnings: List[Dict[str, Any]] = Field(
        default_factory=list, description="Validation warnings"
    )
    validated_data: Optional[Dict[str, Any]] = Field(
        None, description="Validated and cleaned data"
    )


def validate_eligibility_input(data: Dict[str, Any]) -> ValidationResult:
    """Validate eligibility input with detailed error reporting"""
    try:
        validated = EligibilityInput(**data)
        return ValidationResult(is_valid=True, validated_data=validated.dict())
    except PydanticValidationError as e:
        errors = []
        for error in e.errors():
            errors.append(
                {
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                    "input": error.get("input"),
                }
            )
        return ValidationResult(is_valid=False, errors=errors)


def validate_eligibility_output(data: Dict[str, Any]) -> ValidationResult:
    """Validate eligibility output with detailed error reporting"""
    try:
        validated = EligibilityOutput(**data)
        return ValidationResult(is_valid=True, validated_data=validated.dict())
    except PydanticValidationError as e:
        errors = []
        for error in e.errors():
            errors.append(
                {
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                    "input": error.get("input"),
                }
            )
        return ValidationResult(is_valid=False, errors=errors)


def validate_decision_context(data: Dict[str, Any]) -> ValidationResult:
    """Validate decision context with detailed error reporting"""
    try:
        validated = DecisionContext(**data)
        return ValidationResult(is_valid=True, validated_data=validated.dict())
    except PydanticValidationError as e:
        errors = []
        for error in e.errors():
            errors.append(
                {
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                    "input": error.get("input"),
                }
            )
        return ValidationResult(is_valid=False, errors=errors)


def validate_trace_record(data: Dict[str, Any]) -> ValidationResult:
    """Validate trace record with detailed error reporting"""
    try:
        validated = TraceRecord(**data)
        return ValidationResult(is_valid=True, validated_data=validated.dict())
    except PydanticValidationError as e:
        errors = []
        for error in e.errors():
            errors.append(
                {
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                    "input": error.get("input"),
                }
            )
        return ValidationResult(is_valid=False, errors=errors)
