"""
EDQMP Alerts API Routes
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.core import get_supabase, get_current_user
from app.schemas import (
    AlertConfig, AlertConfigCreate, AlertConfigUpdate,
    AlertHistory, AlertHistoryList, AlertStats,
    AcknowledgeRequest, ResolveRequest, TestAlertRequest
)
from app.engines import get_alert_dispatcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["Alerting"])


@router.get("/configs", response_model=List[AlertConfig])
async def list_alert_configs(
    is_active: Optional[bool] = None,
    channel: Optional[str] = None,
    supabase: Client = Depends(get_supabase)
):
    """List all alert configurations"""
    query = supabase.table("alert_configs").select("*")
    if is_active is not None:
        query = query.eq("is_active", is_active)
    if channel:
        query = query.eq("channel", channel)
    response = query.order("created_at", desc=True).execute()
    return [AlertConfig(**c) for c in response.data]


@router.post("/configs", response_model=AlertConfig, status_code=201)
async def create_alert_config(
    config: AlertConfigCreate,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Create a new alert configuration"""
    data = config.model_dump()
    data["created_by"] = user.get("id")
    data["channel"] = data["channel"].value
    if data.get("rule_id"):
        data["rule_id"] = str(data["rule_id"])
    if data.get("source_id"):
        data["source_id"] = str(data["source_id"])
    response = supabase.table("alert_configs").insert(data).execute()
    return AlertConfig(**response.data[0])


@router.get("/history", response_model=AlertHistoryList)
async def list_alert_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supabase: Client = Depends(get_supabase)
):
    """List alert history"""
    offset = (page - 1) * page_size
    response = supabase.table("alert_history").select("*", count="exact").order("sent_at", desc=True).range(offset, offset + page_size - 1).execute()
    return AlertHistoryList(items=[AlertHistory(**h) for h in response.data], total=response.count or 0, page=page, page_size=page_size)


@router.post("/acknowledge", response_model=AlertHistory)
async def acknowledge_alert(
    request: AcknowledgeRequest,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Acknowledge an alert"""
    data = {"status": "acknowledged", "acknowledged_at": datetime.utcnow().isoformat(), "acknowledged_by": user.get("id")}
    response = supabase.table("alert_history").update(data).eq("id", str(request.alert_id)).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertHistory(**response.data[0])


@router.get("/stats", response_model=AlertStats)
async def get_alert_stats(supabase: Client = Depends(get_supabase)):
    """Get alert statistics"""
    response = supabase.table("alert_history").select("*").execute()
    alerts = response.data
    sent = sum(1 for a in alerts if a.get("status") == "sent")
    failed = sum(1 for a in alerts if a.get("status") == "failed")
    acknowledged = sum(1 for a in alerts if a.get("status") == "acknowledged")
    return AlertStats(total_alerts=len(alerts), sent_count=sent, failed_count=failed, acknowledged_count=acknowledged, resolved_count=0)
