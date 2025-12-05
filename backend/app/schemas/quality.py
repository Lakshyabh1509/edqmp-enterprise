"""
Pydantic Schemas for Data Quality
Request/Response models for quality rules and validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class RuleType(str, Enum):
    """Types of validation rules"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    UNIQUENESS = "uniqueness"
    ANOMALY = "anomaly"
    CUSTOM = "custom"


class Severity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ValidationStatus(str, Enum):
    """Validation result status"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


# =============================================================================
# Quality Rules Schemas
# =============================================================================

class QualityRuleBase(BaseModel):
    """Base schema for quality rules"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: RuleType
    config: Dict[str, Any] = Field(default_factory=dict)
    severity: Severity = Severity.WARNING
    is_active: bool = True
    tags: List[str] = Field(default_factory=list)


class QualityRuleCreate(QualityRuleBase):
    """Schema for creating a new rule"""
    pass


class QualityRuleUpdate(BaseModel):
    """Schema for updating a rule"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: Optional[RuleType] = None
    config: Optional[Dict[str, Any]] = None
    severity: Optional[Severity] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class QualityRule(QualityRuleBase):
    """Schema for rule response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class QualityRuleList(BaseModel):
    """Paginated list of rules"""
    items: List[QualityRule]
    total: int
    page: int
    page_size: int


# =============================================================================
# Data Source Schemas
# =============================================================================

class SourceType(str, Enum):
    """Types of data sources"""
    DATABASE = "database"
    API = "api"
    FILE = "file"
    STREAM = "stream"
    WAREHOUSE = "warehouse"


class SLAConfig(BaseModel):
    """SLA configuration for a data source"""
    max_latency_ms: int = Field(default=300000, ge=0)
    min_freshness_hours: float = Field(default=24, ge=0)
    expected_records_min: int = Field(default=0, ge=0)


class DataSourceBase(BaseModel):
    """Base schema for data sources"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_type: SourceType
    connection_config: Dict[str, Any] = Field(default_factory=dict)
    schema_info: Dict[str, Any] = Field(default_factory=dict)
    sla_config: SLAConfig = Field(default_factory=SLAConfig)
    schedule_cron: Optional[str] = None
    is_active: bool = True
    tags: List[str] = Field(default_factory=list)


class DataSourceCreate(DataSourceBase):
    """Schema for creating a data source"""
    pass


class DataSourceUpdate(BaseModel):
    """Schema for updating a data source"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    source_type: Optional[SourceType] = None
    connection_config: Optional[Dict[str, Any]] = None
    schema_info: Optional[Dict[str, Any]] = None
    sla_config: Optional[SLAConfig] = None
    schedule_cron: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class DataSource(DataSourceBase):
    """Schema for data source response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Validation Schemas
# =============================================================================

class ValidationRequest(BaseModel):
    """Request to run validation"""
    source_id: UUID
    rule_ids: Optional[List[UUID]] = None  # If None, run all active rules
    data: Optional[Dict[str, Any]] = None  # Inline data for testing
    options: Dict[str, Any] = Field(default_factory=dict)


class ColumnResult(BaseModel):
    """Validation result for a single column"""
    column: str
    score: float
    passed: bool
    records_checked: int
    records_failed: int
    sample_failures: List[Any] = Field(default_factory=list)


class ValidationResultBase(BaseModel):
    """Base schema for validation results"""
    status: ValidationStatus
    score: Optional[float] = Field(None, ge=0, le=1)
    threshold: Optional[float] = Field(None, ge=0, le=1)
    records_checked: int = 0
    records_passed: int = 0
    records_failed: int = 0
    details: Dict[str, Any] = Field(default_factory=dict)
    sample_failures: List[Any] = Field(default_factory=list)
    duration_ms: Optional[int] = None


class ValidationResultCreate(ValidationResultBase):
    """Schema for creating a validation result"""
    rule_id: UUID
    source_id: UUID
    run_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(ValidationResultBase):
    """Schema for validation result response"""
    id: UUID
    rule_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    execution_time: datetime
    run_id: Optional[UUID] = None
    
    # Joined data (optional)
    rule_name: Optional[str] = None
    source_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ValidationRun(BaseModel):
    """Complete validation run with multiple results"""
    run_id: UUID
    source_id: UUID
    source_name: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_rules: int
    passed_rules: int
    failed_rules: int
    warning_rules: int
    overall_score: float
    results: List[ValidationResult]


class ValidationSummary(BaseModel):
    """Summary of validation results for dashboard"""
    source_id: UUID
    source_name: str
    total_validations: int
    passed_count: int
    failed_count: int
    warning_count: int
    avg_score: float
    last_validation: Optional[datetime] = None


# =============================================================================
# Validation Rule Configuration Schemas
# =============================================================================

class CompletenessConfig(BaseModel):
    """Config for completeness validation"""
    columns: List[str]
    threshold: float = Field(default=0.95, ge=0, le=1)
    treat_empty_as_null: bool = True


class AccuracyConfig(BaseModel):
    """Config for accuracy/format validation"""
    column: str
    pattern: str  # Regex pattern
    threshold: float = Field(default=1.0, ge=0, le=1)
    case_sensitive: bool = False


class ConsistencyConfig(BaseModel):
    """Config for cross-field consistency"""
    rules: List[Dict[str, Any]]  # Expression-based rules
    threshold: float = Field(default=1.0, ge=0, le=1)


class TimelinessConfig(BaseModel):
    """Config for data freshness validation"""
    timestamp_column: str
    max_age_hours: float = Field(default=24, gt=0)
    timezone: str = "UTC"


class UniquenessConfig(BaseModel):
    """Config for uniqueness validation"""
    columns: List[str]
    threshold: float = Field(default=1.0, ge=0, le=1)


class AnomalyConfig(BaseModel):
    """Config for anomaly detection"""
    column: str
    method: str = "zscore"  # zscore, iqr, isolation_forest
    z_threshold: float = Field(default=3.0, gt=0)
    contamination: float = Field(default=0.1, gt=0, lt=0.5)  # For isolation forest
