"""
Pydantic Schemas for Pipeline Monitoring
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PipelineStatus(str, Enum):
    """Pipeline run status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


# =============================================================================
# Pipeline Run Schemas
# =============================================================================

class PipelineRunBase(BaseModel):
    """Base schema for pipeline runs"""
    source_id: UUID
    external_run_id: Optional[str] = None
    pipeline_name: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: PipelineStatus = PipelineStatus.PENDING
    records_processed: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_deleted: int = 0
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineRunCreate(BaseModel):
    """Schema for creating a pipeline run"""
    source_id: UUID
    external_run_id: Optional[str] = None
    pipeline_name: Optional[str] = None
    started_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineRunUpdate(BaseModel):
    """Schema for updating a pipeline run"""
    ended_at: Optional[datetime] = None
    status: Optional[PipelineStatus] = None
    records_processed: Optional[int] = None
    records_inserted: Optional[int] = None
    records_updated: Optional[int] = None
    records_deleted: Optional[int] = None
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PipelineRun(PipelineRunBase):
    """Schema for pipeline run response"""
    id: UUID
    created_at: datetime
    
    # Joined data
    source_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class PipelineRunList(BaseModel):
    """Paginated list of pipeline runs"""
    items: List[PipelineRun]
    total: int
    page: int
    page_size: int


# =============================================================================
# Pipeline Health Schemas
# =============================================================================

class PipelineHealthSummary(BaseModel):
    """Health summary for a pipeline/source"""
    source_id: UUID
    source_name: str
    total_runs: int
    success_count: int
    failed_count: int
    success_rate: float
    avg_latency_ms: Optional[float] = None
    max_latency_ms: Optional[int] = None
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    sla_compliant: bool = True
    health_status: str = "healthy"  # healthy, warning, critical


class PipelineMetrics(BaseModel):
    """Aggregated pipeline metrics"""
    period: str  # hourly, daily, weekly
    timestamp: datetime
    total_runs: int
    success_count: int
    failed_count: int
    avg_latency_ms: float
    total_records: int
    error_rate: float


class PipelineTrend(BaseModel):
    """Pipeline performance trend data"""
    source_id: UUID
    source_name: str
    period: str
    data_points: List[PipelineMetrics]


# =============================================================================
# SLA Schemas
# =============================================================================

class SLABreachEvent(BaseModel):
    """SLA breach event"""
    id: UUID
    source_id: UUID
    source_name: str
    pipeline_run_id: UUID
    breach_type: str  # latency, freshness, availability
    expected_value: float
    actual_value: float
    breach_time: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class SLAStatus(BaseModel):
    """Current SLA status for a source"""
    source_id: UUID
    source_name: str
    latency_sla_met: bool
    freshness_sla_met: bool
    availability_sla_met: bool
    overall_compliant: bool
    current_latency_ms: Optional[int] = None
    last_data_time: Optional[datetime] = None
    uptime_percentage: float = 100.0
    recent_breaches: List[SLABreachEvent] = Field(default_factory=list)


# =============================================================================
# Lineage Schemas
# =============================================================================

class LineageNode(BaseModel):
    """Node in data lineage graph"""
    id: str
    name: str
    type: str  # source, transformation, destination
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LineageEdge(BaseModel):
    """Edge in data lineage graph"""
    source: str
    target: str
    relationship: str  # derives_from, feeds_into, transforms
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DataLineage(BaseModel):
    """Complete data lineage graph"""
    nodes: List[LineageNode]
    edges: List[LineageEdge]
    root_sources: List[str]
    leaf_destinations: List[str]
