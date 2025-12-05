"""
Uniqueness Validator
Detects duplicate records
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


@ValidatorRegistry.register("uniqueness")
class UniquenessValidator(BaseValidator):
    """
    Validates data uniqueness by detecting duplicate records.
    
    Configuration options:
        columns: Columns to check for uniqueness (composite key if multiple)
        threshold: Minimum required uniqueness rate (default: 1.0)
        keep: Which duplicates to consider as valid - 'first', 'last', False (default: 'first')
        ignore_null: Whether to ignore null values in uniqueness check (default: True)
    
    Example config:
        {
            "columns": ["customer_id", "document_number"],
            "threshold": 1.0,
            "keep": "first"
        }
    """
    
    validator_type = "uniqueness"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.columns = config.get("columns", [])
        self.keep = config.get("keep", "first")
        self.ignore_null = config.get("ignore_null", True)
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Check data uniqueness.
        
        Returns a ValidationResult with:
        - Score: Percentage of unique records
        - Details: Duplicate counts and groups
        - Sample failures: Duplicate records
        """
        start_time = time.time()
        
        try:
            if not self.columns:
                return ValidationResult(
                    status="error",
                    score=0.0,
                    threshold=self.threshold,
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    error_message="No columns specified for uniqueness check"
                )
            
            # Validate columns exist
            missing_cols = [c for c in self.columns if c not in df.columns]
            if missing_cols:
                return ValidationResult(
                    status="error",
                    score=0.0,
                    threshold=self.threshold,
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    error_message=f"Columns not found: {missing_cols}"
                )
            
            total_records = len(df)
            
            # Create subset for uniqueness check
            check_df = df[self.columns].copy()
            
            # Handle null values
            if self.ignore_null:
                # Rows with any null in key columns are not considered duplicates
                null_mask = check_df.isna().any(axis=1)
                null_count = null_mask.sum()
                check_subset = check_df[~null_mask]
            else:
                null_count = 0
                check_subset = check_df
            
            # Find duplicates
            # keep='first' means first occurrence is not marked as duplicate
            # keep=False means all occurrences of duplicates are marked
            duplicate_mask_subset = check_subset.duplicated(keep=self.keep)
            
            # Map back to original DataFrame
            duplicate_mask = pd.Series([False] * total_records, index=df.index)
            duplicate_mask.loc[check_subset.index] = duplicate_mask_subset
            
            duplicate_count = duplicate_mask.sum()
            unique_count = total_records - duplicate_count
            
            score = self.calculate_score(unique_count, total_records)
            
            # Get duplicate groups for analysis
            duplicate_groups = []
            if duplicate_count > 0:
                # Find all records involved in duplicates (including first occurrences)
                all_duplicate_mask = check_subset.duplicated(keep=False)
                duplicate_records = check_subset[all_duplicate_mask]
                
                # Group by the key columns and count
                group_counts = duplicate_records.groupby(
                    list(self.columns), 
                    dropna=False
                ).size().reset_index(name='count')
                
                # Get top duplicate groups
                top_groups = group_counts.nlargest(10, 'count')
                for _, row in top_groups.iterrows():
                    group = {col: row[col] for col in self.columns}
                    group['duplicate_count'] = int(row['count'])
                    duplicate_groups.append(group)
            
            # Get sample of duplicate records
            sample_failures = self.sample_failed_records(df, duplicate_mask)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return ValidationResult(
                status=self.determine_status(score),
                score=round(score, 4),
                threshold=self.threshold,
                records_checked=total_records,
                records_passed=int(unique_count),
                records_failed=int(duplicate_count),
                details={
                    "columns": self.columns,
                    "keep": self.keep,
                    "ignore_null": self.ignore_null,
                    "null_count": int(null_count),
                    "unique_count": int(unique_count),
                    "duplicate_count": int(duplicate_count),
                    "duplicate_groups": duplicate_groups
                },
                sample_failures=sample_failures,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.exception(f"Uniqueness validation failed: {e}")
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
        if not columns:
            errors.append("columns is required")
        elif not isinstance(columns, list):
            errors.append("columns must be a list")
        
        keep = self.config.get("keep", "first")
        if keep not in ["first", "last", False]:
            errors.append("keep must be 'first', 'last', or false")
        
        return errors
