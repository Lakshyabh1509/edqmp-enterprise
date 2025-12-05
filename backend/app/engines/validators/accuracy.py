"""
Accuracy Validator
Validates data format and patterns using regex
"""

import re
from typing import Dict, Any, List
import time
import logging

import pandas as pd

from app.engines.validators.base import (
    BaseValidator, 
    ValidationResult, 
    ValidatorRegistry
)

logger = logging.getLogger(__name__)


@ValidatorRegistry.register("accuracy")
class AccuracyValidator(BaseValidator):
    """
    Validates data accuracy by checking values against patterns or formats.
    
    Configuration options:
        column: Column to validate
        pattern: Regex pattern to match
        threshold: Minimum required match rate (default: 1.0)
        case_sensitive: Whether pattern matching is case-sensitive (default: False)
        allow_null: Whether null values are allowed (default: True)
    
    Example config:
        {
            "column": "account_number",
            "pattern": "^[A-Z]{2}[0-9]{10}$",
            "threshold": 1.0,
            "case_sensitive": false
        }
    """
    
    validator_type = "accuracy"
    
    # Common predefined patterns
    PATTERNS = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "phone_us": r"^\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$",
        "ssn": r"^\d{3}-\d{2}-\d{4}$",
        "zip_us": r"^\d{5}(-\d{4})?$",
        "date_iso": r"^\d{4}-\d{2}-\d{2}$",
        "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        "isin": r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$",  # International Securities ID
        "cusip": r"^[0-9A-Z]{9}$",  # US/Canada securities
        "swift": r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$",  # Bank codes
        "iban": r"^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$",
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.column = config.get("column")
        self.pattern = self._resolve_pattern(config.get("pattern", ""))
        self.case_sensitive = config.get("case_sensitive", False)
        self.allow_null = config.get("allow_null", True)
        
        # Compile regex
        flags = 0 if self.case_sensitive else re.IGNORECASE
        try:
            self._regex = re.compile(self.pattern, flags)
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            self._regex = None
    
    def _resolve_pattern(self, pattern: str) -> str:
        """Resolve pattern name to actual regex if using predefined patterns"""
        if pattern.startswith("@"):
            pattern_name = pattern[1:]
            return self.PATTERNS.get(pattern_name, pattern)
        return pattern
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Check data accuracy against pattern.
        
        Returns a ValidationResult with:
        - Score: Percentage of values matching the pattern
        - Details: Match/mismatch counts
        - Sample failures: Records that don't match
        """
        start_time = time.time()
        
        try:
            # Validate configuration
            if not self.column:
                return ValidationResult(
                    status="error",
                    score=0.0,
                    threshold=self.threshold,
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    error_message="No column specified in configuration"
                )
            
            if self.column not in df.columns:
                return ValidationResult(
                    status="error",
                    score=0.0,
                    threshold=self.threshold,
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    error_message=f"Column '{self.column}' not found in data"
                )
            
            if self._regex is None:
                return ValidationResult(
                    status="error",
                    score=0.0,
                    threshold=self.threshold,
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    error_message=f"Invalid regex pattern: {self.pattern}"
                )
            
            series = df[self.column].astype(str)
            total_records = len(df)
            
            # Handle null values
            null_mask = df[self.column].isna()
            null_count = null_mask.sum()
            
            # Apply pattern matching (only to non-null values)
            match_mask = series.str.match(self._regex, na=False)
            
            # Determine pass/fail per record
            if self.allow_null:
                passed_mask = match_mask | null_mask
            else:
                passed_mask = match_mask & ~null_mask
            
            records_passed = passed_mask.sum()
            records_failed = (~passed_mask).sum()
            
            # Calculate score
            score = self.calculate_score(records_passed, total_records)
            
            # Get sample failures
            sample_failures = self.sample_failed_records(df, ~passed_mask)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return ValidationResult(
                status=self.determine_status(score),
                score=round(score, 4),
                threshold=self.threshold,
                records_checked=total_records,
                records_passed=int(records_passed),
                records_failed=int(records_failed),
                details={
                    "column": self.column,
                    "pattern": self.pattern,
                    "case_sensitive": self.case_sensitive,
                    "allow_null": self.allow_null,
                    "null_count": int(null_count),
                    "match_count": int(match_mask.sum()),
                    "mismatch_count": int((~match_mask & ~null_mask).sum())
                },
                sample_failures=sample_failures,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.exception(f"Accuracy validation failed: {e}")
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
        
        if not self.config.get("column"):
            errors.append("column is required")
        
        if not self.config.get("pattern"):
            errors.append("pattern is required")
        
        if self._regex is None:
            errors.append(f"Invalid regex pattern: {self.config.get('pattern')}")
        
        return errors
