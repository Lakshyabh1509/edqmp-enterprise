"""
Pydantic Schemas for Alerting
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class AlertChannel(str, Enum):
    """Alert delivery channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"
    TEAMS = "teams"


class AlertType(str, Enum):
    """Types of alerts"""
    QUALITY_FAILURE = "quality_failure"
    PIPELINE_FAILURE = "pipeline_failure"
    SLA_BREACH = "sla_breach"
    ANOMALY = "anomaly"


class AlertStatus(str, Enum):
    """Alert delivery status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


# =============================================================================
# Alert Configuration Schemas
# =============================================================================

class ThresholdConfig(BaseModel):
    """When to trigger alerts"""
    trigger_on_status: List[str] = Field(default=["failed", "error"])
    min_score_threshold: float = Field(default=0.95, ge=0, le=1)
    consecutive_failures: int = Field(default=1, ge=1)


class EmailChannelConfig(BaseModel):
    """Email-specific configuration"""
    recipients: List[str]
    cc: List[str] = Field(default_factory=list)
    subject_prefix: str = "[EDQMP Alert]"
    include_details: bool = True


class SlackChannelConfig(BaseModel):
    """Slack-specific configuration"""
    channel: str = "#data-quality-alerts"
    mention_users: List[str] = Field(default_factory=list)
    mention_on_critical: bool = True


class WebhookChannelConfig(BaseModel):
    """Webhook-specific configuration"""
    url: str
    method: str = "POST"
    headers: Dict[str, str] = Field(default_factory=dict)
    include_full_payload: bool = True


class AlertConfigBase(BaseModel):
    """Base schema for alert configurations"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rule_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    channel: AlertChannel
    channel_config: Dict[str, Any]
    threshold_config: ThresholdConfig = Field(default_factory=ThresholdConfig)
    cooldown_minutes: int = Field(default=60, ge=0)
    is_active: bool = True


class AlertConfigCreate(AlertConfigBase):
    """Schema for creating an alert config"""
    pass


class AlertConfigUpdate(BaseModel):
    """Schema for updating an alert config"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rule_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    channel: Optional[AlertChannel] = None
    channel_config: Optional[Dict[str, Any]] = None
    threshold_config: Optional[ThresholdConfig] = None
    cooldown_minutes: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class AlertConfig(AlertConfigBase):
    """Schema for alert config response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    # Joined data
    rule_name: Optional[str] = None
    source_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Alert History Schemas
# =============================================================================

class AlertHistoryBase(BaseModel):
    """Base schema for alert history"""
    config_id: UUID
    validation_result_id: Optional[UUID] = None
    pipeline_run_id: Optional[UUID] = None
    alert_type: AlertType
    status: AlertStatus = AlertStatus.PENDING
    recipients: List[str] = Field(default_factory=list)
    message: Optional[str] = None
    response: Dict[str, Any] = Field(default_factory=dict)


class AlertHistoryCreate(AlertHistoryBase):
    """Schema for creating alert history"""
    pass


class AlertHistory(AlertHistoryBase):
    """Schema for alert history response"""
    id: UUID
    sent_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[UUID] = None
    
    # Joined data
    config_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class AlertHistoryList(BaseModel):
    """Paginated list of alert history"""
    items: List[AlertHistory]
    total: int
    page: int
    page_size: int


# =============================================================================
# Alert Action Schemas
# =============================================================================

class AcknowledgeRequest(BaseModel):
    """Request to acknowledge an alert"""
    alert_id: UUID
    notes: Optional[str] = None


class ResolveRequest(BaseModel):
    """Request to resolve an alert"""
    alert_id: UUID
    resolution_notes: Optional[str] = None


class TestAlertRequest(BaseModel):
    """Request to send a test alert"""
    config_id: UUID
    test_message: str = "This is a test alert from EDQMP"


class AlertStats(BaseModel):
    """Alert statistics"""
    total_alerts: int
    sent_count: int
    failed_count: int
    acknowledged_count: int
    resolved_count: int
    avg_response_time_minutes: Optional[float] = None
    by_channel: Dict[str, int] = Field(default_factory=dict)
    by_type: Dict[str, int] = Field(default_factory=dict)
