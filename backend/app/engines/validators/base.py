"""
Base Validator Class
Abstract base for all data quality validators
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check"""
    status: str  # passed, failed, warning, error
    score: float  # 0.0 to 1.0
    threshold: float
    records_checked: int
    records_passed: int
    records_failed: int
    details: Dict[str, Any] = field(default_factory=dict)
    sample_failures: List[Any] = field(default_factory=list)
    duration_ms: int = 0
    error_message: Optional[str] = None
    
    @property
    def passed(self) -> bool:
        return self.status == "passed"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "score": self.score,
            "threshold": self.threshold,
            "records_checked": self.records_checked,
            "records_passed": self.records_passed,
            "records_failed": self.records_failed,
            "details": self.details,
            "sample_failures": self.sample_failures,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message
        }


class BaseValidator(ABC):
    """
    Abstract base class for all data quality validators.
    
    Each validator implements a specific type of quality check:
    - Completeness: Check for missing/null values
    - Accuracy: Validate data format and patterns
    - Consistency: Cross-field validation rules
    - Timeliness: Data freshness checks
    - Uniqueness: Duplicate detection
    - Anomaly: Statistical outlier detection
    """
    
    # Validator type identifier
    validator_type: str = "base"
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize validator with configuration.
        
        Args:
            config: Validator configuration dictionary
        """
        self.config = config
        self.threshold = config.get("threshold", 0.95)
        self.max_sample_failures = config.get("max_sample_failures", 100)
    
    @abstractmethod
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Execute validation on the provided DataFrame.
        
        Args:
            df: pandas DataFrame to validate
            
        Returns:
            ValidationResult with status, score, and details
        """
        pass
    
    def calculate_score(self, passed: int, total: int) -> float:
        """Calculate quality score (0.0 to 1.0)"""
        if total == 0:
            return 1.0  # No records to check = pass
        return passed / total
    
    def determine_status(self, score: float) -> str:
        """Determine validation status based on score vs threshold"""
        if score >= self.threshold:
            return "passed"
        elif score >= self.threshold * 0.8:  # Within 20% of threshold
            return "warning"
        else:
            return "failed"
    
    def sample_failed_records(
        self, 
        df: pd.DataFrame, 
        mask: pd.Series,
        max_samples: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get a sample of failed records for debugging.
        
        Args:
            df: Full DataFrame
            mask: Boolean mask where True = failed
            max_samples: Maximum number of samples to return
            
        Returns:
            List of failed records as dictionaries
        """
        max_samples = max_samples or self.max_sample_failures
        failed_df = df[mask].head(max_samples)
        
        # Convert to list of dicts, handling NaN values
        samples = []
        for _, row in failed_df.iterrows():
            record = {}
            for col, val in row.items():
                if pd.isna(val):
                    record[col] = None
                elif isinstance(val, (pd.Timestamp, datetime)):
                    record[col] = val.isoformat()
                else:
                    record[col] = val
            samples.append(record)
        
        return samples
    
    def validate_config(self) -> List[str]:
        """
        Validate the configuration for this validator.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check threshold
        threshold = self.config.get("threshold")
        if threshold is not None:
            if not isinstance(threshold, (int, float)):
                errors.append("threshold must be a number")
            elif not 0 <= threshold <= 1:
                errors.append("threshold must be between 0 and 1")
        
        return errors
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(threshold={self.threshold})"


class ValidatorRegistry:
    """Registry for validator classes"""
    
    _validators: Dict[str, type] = {}
    
    @classmethod
    def register(cls, validator_type: str):
        """Decorator to register a validator class"""
        def decorator(validator_class: type):
            cls._validators[validator_type] = validator_class
            return validator_class
        return decorator
    
    @classmethod
    def get(cls, validator_type: str) -> Optional[type]:
        """Get validator class by type"""
        return cls._validators.get(validator_type)
    
    @classmethod
    def create(cls, validator_type: str, config: Dict[str, Any]) -> BaseValidator:
        """Create a validator instance by type"""
        validator_class = cls.get(validator_type)
        if validator_class is None:
            raise ValueError(f"Unknown validator type: {validator_type}")
        return validator_class(config)
    
    @classmethod
    def list_types(cls) -> List[str]:
        """List all registered validator types"""
        return list(cls._validators.keys())


# Convenience function
def create_validator(validator_type: str, config: Dict[str, Any]) -> BaseValidator:
    """Create a validator instance by type"""
    return ValidatorRegistry.create(validator_type, config)
