"""
Completeness Validator
Checks for missing/null values in data
"""

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


@ValidatorRegistry.register("completeness")
class CompletenessValidator(BaseValidator):
    """
    Validates data completeness by checking for null/missing values.
    
    Configuration options:
        columns: List of columns to check (default: all columns)
        threshold: Minimum required completeness score (default: 0.95)
        treat_empty_as_null: Whether to treat empty strings as nulls (default: True)
        treat_whitespace_as_null: Whether to treat whitespace-only strings as nulls (default: False)
    
    Example config:
        {
            "columns": ["trade_id", "symbol", "quantity", "price"],
            "threshold": 0.99,
            "treat_empty_as_null": True
        }
    """
    
    validator_type = "completeness"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.columns = config.get("columns", None)  # None = all columns
        self.treat_empty_as_null = config.get("treat_empty_as_null", True)
        self.treat_whitespace_as_null = config.get("treat_whitespace_as_null", False)
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Check completeness of specified columns.
        
        Returns a ValidationResult with:
        - Overall score: Average completeness across all columns
        - Column-level details: Completeness score per column
        - Sample failures: Records with null values
        """
        start_time = time.time()
        
        try:
            # Determine columns to check
            columns_to_check = self.columns or df.columns.tolist()
            
            # Filter to columns that exist in the DataFrame
            available_columns = [c for c in columns_to_check if c in df.columns]
            missing_columns = [c for c in columns_to_check if c not in df.columns]
            
            if not available_columns:
                return ValidationResult(
                    status="error",
                    score=0.0,
                    threshold=self.threshold,
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    error_message=f"No matching columns found. Missing: {missing_columns}"
                )
            
            total_records = len(df)
            column_results = {}
            total_non_null = 0
            total_cells = 0
            
            # Check each column
            for col in available_columns:
                series = df[col]
                
                # Create null mask
                null_mask = series.isna()
                
                # Optionally treat empty strings as null
                if self.treat_empty_as_null and series.dtype == object:
                    null_mask = null_mask | (series == "")
                
                # Optionally treat whitespace-only as null
                if self.treat_whitespace_as_null and series.dtype == object:
                    null_mask = null_mask | (series.str.strip() == "")
                
                non_null_count = (~null_mask).sum()
                col_score = self.calculate_score(non_null_count, total_records)
                
                column_results[col] = {
                    "score": round(col_score, 4),
                    "non_null": int(non_null_count),
                    "null_count": int(null_mask.sum()),
                    "total": total_records,
                    "passed": col_score >= self.threshold
                }
                
                total_non_null += non_null_count
                total_cells += total_records
            
            # Calculate overall score (average across columns)
            overall_score = total_non_null / total_cells if total_cells > 0 else 1.0
            
            # Get sample of failed records (any row with a null in checked columns)
            any_null_mask = df[available_columns].isna().any(axis=1)
            if self.treat_empty_as_null:
                for col in available_columns:
                    if df[col].dtype == object:
                        any_null_mask = any_null_mask | (df[col] == "")
            
            sample_failures = self.sample_failed_records(df, any_null_mask)
            
            # Calculate counts
            records_passed = (~any_null_mask).sum()
            records_failed = any_null_mask.sum()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return ValidationResult(
                status=self.determine_status(overall_score),
                score=round(overall_score, 4),
                threshold=self.threshold,
                records_checked=total_records,
                records_passed=int(records_passed),
                records_failed=int(records_failed),
                details={
                    "columns_checked": available_columns,
                    "missing_columns": missing_columns,
                    "column_results": column_results,
                    "treat_empty_as_null": self.treat_empty_as_null
                },
                sample_failures=sample_failures,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.exception(f"Completeness validation failed: {e}")
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
        
        columns = self.config.get("columns")
        if columns is not None and not isinstance(columns, list):
            errors.append("columns must be a list")
        
        return errors
