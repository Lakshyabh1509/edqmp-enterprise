"""
EDQMP Pipeline Monitoring API Routes
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.core import get_supabase, get_current_user
from app.schemas import (
    PipelineRun, PipelineRunCreate, PipelineRunUpdate, PipelineRunList,
    PipelineHealthSummary, PipelineMetrics, SLAStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipelines", tags=["Pipeline Monitoring"])


# =============================================================================
# Pipeline Runs
# =============================================================================

@router.post("/runs", response_model=PipelineRun, status_code=status.HTTP_201_CREATED)
async def start_pipeline_run(
    run: PipelineRunCreate,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Record the start of a pipeline run"""
    try:
        data = run.model_dump()
        data["started_at"] = data.get("started_at") or datetime.utcnow().isoformat()
        data["status"] = "running"
        data["source_id"] = str(data["source_id"])
        
        response = supabase.table("pipeline_runs").insert(data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create pipeline run")
        
        return PipelineRun(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/runs/{run_id}", response_model=PipelineRun)
async def update_pipeline_run(
    run_id: UUID,
    update: PipelineRunUpdate,
    supabase: Client = Depends(get_supabase)
):
    """Update a pipeline run (e.g., when it completes)"""
    try:
        data = {k: v for k, v in update.model_dump().items() if v is not None}
        
        if "status" in data:
            data["status"] = data["status"].value if hasattr(data["status"], "value") else data["status"]
        
        # Calculate latency if ended_at is provided
        if "ended_at" in data:
            run_response = supabase.table("pipeline_runs").select("started_at").eq("id", str(run_id)).execute()
            if run_response.data:
                started_at = datetime.fromisoformat(run_response.data[0]["started_at"].replace("Z", "+00:00"))
                ended_at = data["ended_at"]
                if isinstance(ended_at, str):
                    ended_at = datetime.fromisoformat(ended_at.replace("Z", "+00:00"))
                data["latency_ms"] = int((ended_at - started_at).total_seconds() * 1000)
        
        response = supabase.table("pipeline_runs").update(data).eq("id", str(run_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Pipeline run not found")
        
        return PipelineRun(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs", response_model=PipelineRunList)
async def list_pipeline_runs(
    source_id: Optional[UUID] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    supabase: Client = Depends(get_supabase)
):
    """List pipeline runs with filtering and pagination"""
    try:
        query = supabase.table("pipeline_runs").select("*", count="exact")
        
        if source_id:
            query = query.eq("source_id", str(source_id))
        if status:
            query = query.eq("status", status)
        
        offset = (page - 1) * page_size
        query = query.order("started_at", desc=True).range(offset, offset + page_size - 1)
        
        response = query.execute()
        
        return PipelineRunList(
            items=[PipelineRun(**r) for r in response.data],
            total=response.count or 0,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.exception(f"Failed to list runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}", response_model=PipelineRun)
async def get_pipeline_run(
    run_id: UUID,
    supabase: Client = Depends(get_supabase)
):
    """Get a specific pipeline run"""
    try:
        response = supabase.table("pipeline_runs").select("*").eq("id", str(run_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Pipeline run not found")
        
        return PipelineRun(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Pipeline Health
# =============================================================================

@router.get("/health", response_model=List[PipelineHealthSummary])
async def get_pipeline_health(
    supabase: Client = Depends(get_supabase)
):
    """Get health summary for all pipelines"""
    try:
        # Get from view
        response = supabase.table("v_pipeline_health").select("*").execute()
        
        summaries = []
        for r in response.data:
            total = r.get("total_runs", 0) or 0
            success = r.get("success_count", 0) or 0
            failed = r.get("failed_count", 0) or 0
            
            success_rate = success / total if total > 0 else 1.0
            
            # Determine health status
            if success_rate >= 0.99:
                health_status = "healthy"
            elif success_rate >= 0.95:
                health_status = "warning"
            else:
                health_status = "critical"
            
            summaries.append(PipelineHealthSummary(
                source_id=r["source_id"],
                source_name=r["source_name"],
                total_runs=total,
                success_count=success,
                failed_count=failed,
                success_rate=round(success_rate, 4),
                avg_latency_ms=float(r.get("avg_latency_ms") or 0),
                last_run=r.get("last_run"),
                health_status=health_status
            ))
        
        return summaries
    except Exception as e:
        logger.exception(f"Failed to get health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{source_id}", response_model=PipelineHealthSummary)
async def get_source_health(
    source_id: UUID,
    supabase: Client = Depends(get_supabase)
):
    """Get health summary for a specific data source"""
    try:
        # Get source info
        source_response = supabase.table("data_sources").select("*").eq("id", str(source_id)).execute()
        
        if not source_response.data:
            raise HTTPException(status_code=404, detail="Data source not found")
        
        source = source_response.data[0]
        
        # Get run statistics for last 24 hours
        since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        runs_response = supabase.table("pipeline_runs").select("*").eq("source_id", str(source_id)).gte("started_at", since).execute()
        
        runs = runs_response.data
        total = len(runs)
        success = sum(1 for r in runs if r.get("status") == "success")
        failed = sum(1 for r in runs if r.get("status") == "failed")
        
        latencies = [r.get("latency_ms") for r in runs if r.get("latency_ms")]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0
        
        success_rate = success / total if total > 0 else 1.0
        
        # Check SLA compliance
        sla_config = source.get("sla_config", {})
        sla_compliant = avg_latency <= sla_config.get("max_latency_ms", float("inf"))
        
        if success_rate >= 0.99 and sla_compliant:
            health_status = "healthy"
        elif success_rate >= 0.95:
            health_status = "warning"
        else:
            health_status = "critical"
        
        last_run = max((r.get("ended_at") for r in runs if r.get("ended_at")), default=None)
        last_success = max(
            (r.get("ended_at") for r in runs if r.get("status") == "success" and r.get("ended_at")),
            default=None
        )
        
        return PipelineHealthSummary(
            source_id=source_id,
            source_name=source["name"],
            total_runs=total,
            success_count=success,
            failed_count=failed,
            success_rate=round(success_rate, 4),
            avg_latency_ms=round(avg_latency, 0),
            max_latency_ms=max_latency,
            last_run=last_run,
            last_success=last_success,
            sla_compliant=sla_compliant,
            health_status=health_status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get source health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SLA Monitoring
# =============================================================================

@router.get("/sla/{source_id}", response_model=SLAStatus)
async def get_sla_status(
    source_id: UUID,
    supabase: Client = Depends(get_supabase)
):
    """Get SLA compliance status for a data source"""
    try:
        # Get source with SLA config
        source_response = supabase.table("data_sources").select("*").eq("id", str(source_id)).execute()
        
        if not source_response.data:
            raise HTTPException(status_code=404, detail="Data source not found")
        
        source = source_response.data[0]
        sla_config = source.get("sla_config", {})
        
        # Get recent runs
        runs_response = supabase.table("pipeline_runs").select("*").eq("source_id", str(source_id)).order("started_at", desc=True).limit(100).execute()
        
        runs = runs_response.data
        
        # Calculate SLA metrics
        latencies = [r.get("latency_ms") for r in runs if r.get("latency_ms")]
        current_latency = latencies[0] if latencies else None
        
        max_latency = sla_config.get("max_latency_ms", 300000)
        latency_sla_met = current_latency is None or current_latency <= max_latency
        
        # Freshness check
        last_success = next((r for r in runs if r.get("status") == "success"), None)
        if last_success and last_success.get("ended_at"):
            last_time = datetime.fromisoformat(last_success["ended_at"].replace("Z", "+00:00"))
            hours_since = (datetime.utcnow().replace(tzinfo=last_time.tzinfo) - last_time).total_seconds() / 3600
            freshness_sla_met = hours_since <= sla_config.get("min_freshness_hours", 24)
        else:
            freshness_sla_met = True
            last_time = None
        
        # Availability (success rate)
        total = len(runs)
        success = sum(1 for r in runs if r.get("status") == "success")
        uptime = (success / total * 100) if total > 0 else 100.0
        availability_sla_met = uptime >= 99.0
        
        return SLAStatus(
            source_id=source_id,
            source_name=source["name"],
            latency_sla_met=latency_sla_met,
            freshness_sla_met=freshness_sla_met,
            availability_sla_met=availability_sla_met,
            overall_compliant=all([latency_sla_met, freshness_sla_met, availability_sla_met]),
            current_latency_ms=current_latency,
            last_data_time=last_time,
            uptime_percentage=round(uptime, 2)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get SLA status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Metrics
# =============================================================================

@router.get("/metrics/{source_id}", response_model=List[PipelineMetrics])
async def get_pipeline_metrics(
    source_id: UUID,
    period: str = Query("daily", enum=["hourly", "daily", "weekly"]),
    days: int = Query(7, ge=1, le=90),
    supabase: Client = Depends(get_supabase)
):
    """Get aggregated pipeline metrics over time"""
    try:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        runs_response = supabase.table("pipeline_runs").select("*").eq("source_id", str(source_id)).gte("started_at", since).order("started_at").execute()
        
        runs = runs_response.data
        
        if not runs:
            return []
        
        # Group by period
        import pandas as pd
        df = pd.DataFrame(runs)
        df["started_at"] = pd.to_datetime(df["started_at"])
        
        if period == "hourly":
            df["period"] = df["started_at"].dt.floor("H")
        elif period == "daily":
            df["period"] = df["started_at"].dt.floor("D")
        else:  # weekly
            df["period"] = df["started_at"].dt.to_period("W").dt.start_time
        
        metrics = []
        for period_start, group in df.groupby("period"):
            total = len(group)
            success = (group["status"] == "success").sum()
            failed = (group["status"] == "failed").sum()
            avg_latency = group["latency_ms"].mean() if "latency_ms" in group else 0
            total_records = group["records_processed"].sum() if "records_processed" in group else 0
            
            metrics.append(PipelineMetrics(
                period=period,
                timestamp=period_start,
                total_runs=int(total),
                success_count=int(success),
                failed_count=int(failed),
                avg_latency_ms=float(avg_latency or 0),
                total_records=int(total_records or 0),
                error_rate=round(failed / total if total > 0 else 0, 4)
            ))
        
        return metrics
    except Exception as e:
        logger.exception(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
