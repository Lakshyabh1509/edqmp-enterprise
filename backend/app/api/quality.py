"""
EDQMP Quality API Routes
Endpoints for data quality rules and validation
"""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from supabase import Client
import pandas as pd

from app.core import get_supabase, get_current_user, get_current_user_optional
from app.schemas import (
    QualityRule, QualityRuleCreate, QualityRuleUpdate, QualityRuleList,
    DataSource, DataSourceCreate, DataSourceUpdate,
    ValidationRequest, ValidationResult as ValidationResultSchema, 
    ValidationRun, ValidationSummary
)
from app.engines import create_validator, ValidationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quality", tags=["Data Quality"])


# =============================================================================
# Quality Rules CRUD
# =============================================================================

@router.get("/rules", response_model=QualityRuleList)
async def list_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    rule_type: Optional[str] = None,
    severity: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user_optional)
):
    """List all quality rules with pagination and filtering"""
    try:
        query = supabase.table("quality_rules").select("*", count="exact")
        
        # Apply filters
        if rule_type:
            query = query.eq("rule_type", rule_type)
        if severity:
            query = query.eq("severity", severity)
        if is_active is not None:
            query = query.eq("is_active", is_active)
        if search:
            query = query.ilike("name", f"%{search}%")
        
        # Pagination
        offset = (page - 1) * page_size
        query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)
        
        response = query.execute()
        
        return QualityRuleList(
            items=[QualityRule(**r) for r in response.data],
            total=response.count or 0,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.exception(f"Failed to list rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}", response_model=QualityRule)
async def get_rule(
    rule_id: UUID,
    supabase: Client = Depends(get_supabase)
):
    """Get a specific quality rule by ID"""
    try:
        response = supabase.table("quality_rules").select("*").eq("id", str(rule_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        return QualityRule(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules", response_model=QualityRule, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule: QualityRuleCreate,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Create a new quality rule"""
    try:
        data = rule.model_dump()
        data["created_by"] = user.get("id")
        data["rule_type"] = data["rule_type"].value
        data["severity"] = data["severity"].value
        
        response = supabase.table("quality_rules").insert(data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create rule")
        
        return QualityRule(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}", response_model=QualityRule)
async def update_rule(
    rule_id: UUID,
    rule: QualityRuleUpdate,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Update an existing quality rule"""
    try:
        # Only include non-None values
        data = {k: v for k, v in rule.model_dump().items() if v is not None}
        
        if "rule_type" in data:
            data["rule_type"] = data["rule_type"].value
        if "severity" in data:
            data["severity"] = data["severity"].value
        
        response = supabase.table("quality_rules").update(data).eq("id", str(rule_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        return QualityRule(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: UUID,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Delete a quality rule"""
    try:
        response = supabase.table("quality_rules").delete().eq("id", str(rule_id)).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Rule not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Validation Execution
# =============================================================================

@router.post("/validate", response_model=ValidationRun)
async def run_validation(
    request: ValidationRequest,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """
    Run data quality validation on a data source.
    
    If rule_ids is provided, only those rules are executed.
    Otherwise, all active rules mapped to the source are executed.
    """
    run_id = uuid4()
    started_at = datetime.utcnow()
    results = []
    
    try:
        # Get data source
        source_response = supabase.table("data_sources").select("*").eq("id", str(request.source_id)).execute()
        
        if not source_response.data:
            raise HTTPException(status_code=404, detail="Data source not found")
        
        source = source_response.data[0]
        
        # Get rules to execute
        if request.rule_ids:
            rules_response = supabase.table("quality_rules").select("*").in_("id", [str(r) for r in request.rule_ids]).execute()
        else:
            # Get all active rules (in a real implementation, would filter by source mapping)
            rules_response = supabase.table("quality_rules").select("*").eq("is_active", True).execute()
        
        rules = rules_response.data
        
        if not rules:
            raise HTTPException(status_code=400, detail="No rules found to execute")
        
        # Get or generate sample data
        # In production, this would fetch from the actual data source
        if request.data:
            df = pd.DataFrame(request.data)
        else:
            # Generate sample data for testing
            df = _generate_sample_data(source)
        
        # Execute each rule
        for rule in rules:
            try:
                validator = create_validator(rule["rule_type"], rule["config"])
                result = validator.validate(df)
                
                # Store result
                result_data = {
                    "rule_id": rule["id"],
                    "source_id": str(request.source_id),
                    "status": result.status,
                    "score": result.score,
                    "threshold": result.threshold,
                    "records_checked": result.records_checked,
                    "records_passed": result.records_passed,
                    "records_failed": result.records_failed,
                    "details": result.details,
                    "sample_failures": result.sample_failures[:10],  # Limit stored samples
                    "duration_ms": result.duration_ms,
                    "run_id": str(run_id),
                    "metadata": request.options
                }
                
                insert_response = supabase.table("validation_results").insert(result_data).execute()
                
                if insert_response.data:
                    result_record = insert_response.data[0]
                    results.append(ValidationResultSchema(
                        id=result_record["id"],
                        rule_id=rule["id"],
                        source_id=request.source_id,
                        execution_time=result_record["execution_time"],
                        status=result.status,
                        score=result.score,
                        threshold=result.threshold,
                        records_checked=result.records_checked,
                        records_passed=result.records_passed,
                        records_failed=result.records_failed,
                        details=result.details,
                        sample_failures=result.sample_failures[:10],
                        duration_ms=result.duration_ms,
                        run_id=run_id,
                        rule_name=rule["name"]
                    ))
                    
            except Exception as e:
                logger.error(f"Rule {rule['name']} failed: {e}")
                # Create error result
                results.append(ValidationResultSchema(
                    id=uuid4(),
                    rule_id=rule["id"],
                    source_id=request.source_id,
                    execution_time=datetime.utcnow(),
                    status="error",
                    score=0.0,
                    threshold=rule["config"].get("threshold", 0.95),
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    details={"error": str(e)},
                    rule_name=rule["name"]
                ))
        
        # Calculate summary
        passed_count = sum(1 for r in results if r.status == "passed")
        failed_count = sum(1 for r in results if r.status == "failed")
        warning_count = sum(1 for r in results if r.status == "warning")
        overall_score = sum(r.score or 0 for r in results) / len(results) if results else 0
        
        return ValidationRun(
            run_id=run_id,
            source_id=request.source_id,
            source_name=source["name"],
            started_at=started_at,
            ended_at=datetime.utcnow(),
            total_rules=len(results),
            passed_rules=passed_count,
            failed_rules=failed_count,
            warning_rules=warning_count,
            overall_score=overall_score,
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Validation run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results", response_model=List[ValidationResultSchema])
async def list_validation_results(
    source_id: Optional[UUID] = None,
    rule_id: Optional[UUID] = None,
    status: Optional[str] = None,
    run_id: Optional[UUID] = None,
    limit: int = Query(50, ge=1, le=200),
    supabase: Client = Depends(get_supabase)
):
    """List recent validation results with optional filtering"""
    try:
        query = supabase.table("validation_results").select("*")
        
        if source_id:
            query = query.eq("source_id", str(source_id))
        if rule_id:
            query = query.eq("rule_id", str(rule_id))
        if status:
            query = query.eq("status", status)
        if run_id:
            query = query.eq("run_id", str(run_id))
        
        query = query.order("execution_time", desc=True).limit(limit)
        
        response = query.execute()
        
        return [ValidationResultSchema(**r) for r in response.data]
    except Exception as e:
        logger.exception(f"Failed to list results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=List[ValidationSummary])
async def get_quality_summary(
    supabase: Client = Depends(get_supabase)
):
    """Get quality summary per data source"""
    try:
        # Use the view if available, otherwise aggregate manually
        response = supabase.table("v_quality_summary").select("*").execute()
        
        if response.data:
            return [ValidationSummary(
                source_id=r["source_id"],
                source_name=r["source_name"],
                total_validations=r["total_validations"] or 0,
                passed_count=r["passed_count"] or 0,
                failed_count=r["failed_count"] or 0,
                warning_count=r["warning_count"] or 0,
                avg_score=float(r["avg_score"] or 0),
                last_validation=r["last_validation"]
            ) for r in response.data]
        
        return []
    except Exception as e:
        logger.exception(f"Failed to get summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Data Sources CRUD
# =============================================================================

@router.get("/sources", response_model=List[DataSource])
async def list_data_sources(
    is_active: Optional[bool] = None,
    source_type: Optional[str] = None,
    supabase: Client = Depends(get_supabase)
):
    """List all data sources"""
    try:
        query = supabase.table("data_sources").select("*")
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        if source_type:
            query = query.eq("source_type", source_type)
        
        query = query.order("created_at", desc=True)
        
        response = query.execute()
        
        return [DataSource(**s) for s in response.data]
    except Exception as e:
        logger.exception(f"Failed to list sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources", response_model=DataSource, status_code=status.HTTP_201_CREATED)
async def create_data_source(
    source: DataSourceCreate,
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """Create a new data source"""
    try:
        data = source.model_dump()
        data["created_by"] = user.get("id")
        data["source_type"] = data["source_type"].value
        data["sla_config"] = data["sla_config"].model_dump() if hasattr(data["sla_config"], "model_dump") else data["sla_config"]
        
        response = supabase.table("data_sources").insert(data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create data source")
        
        return DataSource(**response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Helper Functions
# =============================================================================

def _generate_sample_data(source: dict) -> pd.DataFrame:
    """Generate sample data for testing when no data is provided"""
    import random
    from datetime import timedelta
    
    # Generate 100 sample records
    n = 100
    now = datetime.utcnow()
    
# ============================================
# System Management
# ============================================

@router.delete("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_system_data(
    confirm: bool = Query(..., description="Must be true to confirm deletion"),
    supabase: Client = Depends(get_supabase),
    user: dict = Depends(get_current_user)
):
    """
    HARD RESET: Delete all rules, sources, and results.
    Used to clear sample data and start fresh.
    """
    if not confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")
        
    try:
        # Delete in order of dependencies
        supabase.table("validation_results").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("pipeline_runs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("alert_history").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("quality_rules").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("data_sources").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
    except Exception as e:
        logger.exception(f"System reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
