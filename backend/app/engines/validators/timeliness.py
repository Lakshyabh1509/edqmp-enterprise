"""
Timeliness Validator
Checks data freshness and temporal validity
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time
import logging

import pandas as pd
from dateutil import parser as date_parser
import pytz

from app.engines.validators.base import (
    BaseValidator, 
    ValidationResult, 
    ValidatorRegistry
)

logger = logging.getLogger(__name__)


@ValidatorRegistry.register("timeliness")
class TimelinessValidator(BaseValidator):
    """
    Validates data timeliness (freshness) based on timestamp columns.
    
    Configuration options:
        timestamp_column: Column containing timestamps
        max_age_hours: Maximum allowed age in hours
        timezone: Timezone for comparison (default: UTC)
        reference_time: Reference time for comparison (default: now)
        check_future: Whether to flag future timestamps (default: True)
        max_future_hours: Maximum allowed hours in future (default: 1)
    
    Example config:
        {
            "timestamp_column": "updated_at",
            "max_age_hours": 24,
            "timezone": "UTC",
            "check_future": true
        }
    """
    
    validator_type = "timeliness"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.timestamp_column = config.get("timestamp_column")
        self.max_age_hours = config.get("max_age_hours", 24)
        self.timezone = config.get("timezone", "UTC")
        self.reference_time = config.get("reference_time")  # ISO format string or None
        self.check_future = config.get("check_future", True)
        self.max_future_hours = config.get("max_future_hours", 1)
    
    def _get_reference_time(self) -> datetime:
        """Get the reference time for comparison"""
        if self.reference_time:
            ref = date_parser.parse(self.reference_time)
        else:
            ref = datetime.utcnow()
        
        # Ensure timezone aware
        tz = pytz.timezone(self.timezone)
        if ref.tzinfo is None:
            ref = tz.localize(ref)
        else:
            ref = ref.astimezone(tz)
        
        return ref
    
    def _parse_timestamps(self, series: pd.Series) -> pd.Series:
        """Parse timestamp column to datetime"""
        if pd.api.types.is_datetime64_any_dtype(series):
            return pd.to_datetime(series, utc=True)
        
        # Try parsing string timestamps
        try:
            return pd.to_datetime(series, utc=True, errors='coerce')
        except Exception:
            # Fall back to dateutil parser
            def safe_parse(x):
                if pd.isna(x):
                    return pd.NaT
                try:
                    return date_parser.parse(str(x))
                except:
                    return pd.NaT
            
            return series.apply(safe_parse)
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Check data timeliness.
        
        Returns a ValidationResult with:
        - Score: Percentage of records within freshness threshold
        - Details: Age statistics and outliers
        - Sample failures: Stale/future records
        """
        start_time = time.time()
        
        try:
            if not self.timestamp_column:
                return ValidationResult(
                    status="error",
                    score=0.0,
                    threshold=self.threshold,
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    error_message="No timestamp_column specified"
                )
            
            if self.timestamp_column not in df.columns:
                return ValidationResult(
                    status="error",
                    score=0.0,
                    threshold=self.threshold,
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    error_message=f"Column '{self.timestamp_column}' not found"
                )
            
            total_records = len(df)
            reference_time = self._get_reference_time()
            
            # Parse timestamps
            timestamps = self._parse_timestamps(df[self.timestamp_column])
            
            # Handle timezone
            if timestamps.dt.tz is None:
                tz = pytz.timezone(self.timezone)
                timestamps = timestamps.dt.tz_localize(tz)
            
            # Calculate age in hours
            age_delta = reference_time - timestamps
            age_hours = age_delta.dt.total_seconds() / 3600
            
            # Determine valid records
            # Too old: age > max_age_hours
            too_old_mask = age_hours > self.max_age_hours
            
            # Future data (optional check)
            if self.check_future:
                too_future_mask = age_hours < -self.max_future_hours
            else:
                too_future_mask = pd.Series([False] * total_records, index=df.index)
            
            # Null timestamps are considered failures
            null_mask = timestamps.isna()
            
            # Combined failure mask
            fail_mask = too_old_mask | too_future_mask | null_mask
            
            records_passed = (~fail_mask).sum()
            records_failed = fail_mask.sum()
            score = self.calculate_score(records_passed, total_records)
            
            # Calculate statistics
            valid_ages = age_hours[~timestamps.isna()]
            stats = {
                "min_age_hours": round(float(valid_ages.min()), 2) if len(valid_ages) > 0 else None,
                "max_age_hours": round(float(valid_ages.max()), 2) if len(valid_ages) > 0 else None,
                "avg_age_hours": round(float(valid_ages.mean()), 2) if len(valid_ages) > 0 else None,
                "median_age_hours": round(float(valid_ages.median()), 2) if len(valid_ages) > 0 else None,
            }
            
            # Get sample failures
            sample_failures = self.sample_failed_records(df, fail_mask)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return ValidationResult(
                status=self.determine_status(score),
                score=round(score, 4),
                threshold=self.threshold,
                records_checked=total_records,
                records_passed=int(records_passed),
                records_failed=int(records_failed),
                details={
                    "timestamp_column": self.timestamp_column,
                    "reference_time": reference_time.isoformat(),
                    "max_age_hours": self.max_age_hours,
                    "check_future": self.check_future,
                    "too_old_count": int(too_old_mask.sum()),
                    "too_future_count": int(too_future_mask.sum()),
                    "null_count": int(null_mask.sum()),
                    "statistics": stats
                },
                sample_failures=sample_failures,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.exception(f"Timeliness validation failed: {e}")
            return ValidationResult(
                status="error",
                score=0.0,
                threshold=self.threshold,
                records_checked=len(df) if df is not None else 0,
                records_passed=0,
                records_failed=0,
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000)
            )
    
    def validate_config(self) -> List[str]:
        """Validate configuration"""
        errors = super().validate_config()
        
        if not self.config.get("timestamp_column"):
            errors.append("timestamp_column is required")
        
        max_age = self.config.get("max_age_hours")
        if max_age is not None and (not isinstance(max_age, (int, float)) or max_age <= 0):
            errors.append("max_age_hours must be a positive number")
        
        tz = self.config.get("timezone", "UTC")
        try:
            pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            errors.append(f"Unknown timezone: {tz}")
        
        return errors
