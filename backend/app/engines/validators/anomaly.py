"""
Anomaly Detection Validator
Detects statistical outliers using various methods
"""

from typing import Dict, Any, List, Optional
import time
import logging

import pandas as pd
import numpy as np

# scipy is optional - only used for some statistical methods
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    stats = None

from app.engines.validators.base import (
    BaseValidator, 
    ValidationResult, 
    ValidatorRegistry
)

logger = logging.getLogger(__name__)


@ValidatorRegistry.register("anomaly")
class AnomalyValidator(BaseValidator):
    """
    Detects anomalies/outliers in numerical data using statistical methods.
    
    Configuration options:
        column: Column to check for anomalies
        method: Detection method - 'zscore', 'iqr', 'isolation_forest' (default: 'zscore')
        z_threshold: Z-score threshold for outliers (default: 3.0)
        iqr_multiplier: IQR multiplier for outlier bounds (default: 1.5)
        contamination: Expected proportion of outliers for isolation forest (default: 0.1)
        direction: 'both', 'high', 'low' - which direction to flag (default: 'both')
    
    Example config:
        {
            "column": "price",
            "method": "zscore",
            "z_threshold": 3.0,
            "direction": "both"
        }
    """
    
    validator_type = "anomaly"
    
    METHODS = ["zscore", "iqr", "isolation_forest", "mad"]
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.column = config.get("column")
        self.method = config.get("method", "zscore")
        self.z_threshold = config.get("z_threshold", 3.0)
        self.iqr_multiplier = config.get("iqr_multiplier", 1.5)
        self.contamination = config.get("contamination", 0.1)
        self.direction = config.get("direction", "both")
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Detect anomalies in the data.
        
        Returns a ValidationResult with:
        - Score: Percentage of non-anomalous records
        - Details: Statistical info and thresholds used
        - Sample failures: Anomalous records
        """
        start_time = time.time()
        
        try:
            if not self.column:
                return ValidationResult(
                    status="error",
                    score=0.0,
                    threshold=self.threshold,
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    error_message="No column specified"
                )
            
            if self.column not in df.columns:
                return ValidationResult(
                    status="error",
                    score=0.0,
                    threshold=self.threshold,
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    error_message=f"Column '{self.column}' not found"
                )
            
            series = pd.to_numeric(df[self.column], errors='coerce')
            total_records = len(df)
            
            # Handle null values
            null_mask = series.isna()
            valid_series = series[~null_mask]
            
            if len(valid_series) == 0:
                return ValidationResult(
                    status="warning",
                    score=1.0,
                    threshold=self.threshold,
                    records_checked=total_records,
                    records_passed=total_records,
                    records_failed=0,
                    details={"message": "No valid numeric values to analyze"}
                )
            
            # Detect anomalies based on method
            if self.method == "zscore":
                anomaly_mask, stats_info = self._detect_zscore(valid_series)
            elif self.method == "iqr":
                anomaly_mask, stats_info = self._detect_iqr(valid_series)
            elif self.method == "mad":
                anomaly_mask, stats_info = self._detect_mad(valid_series)
            elif self.method == "isolation_forest":
                anomaly_mask, stats_info = self._detect_isolation_forest(valid_series)
            else:
                return ValidationResult(
                    status="error",
                    score=0.0,
                    threshold=self.threshold,
                    records_checked=0,
                    records_passed=0,
                    records_failed=0,
                    error_message=f"Unknown method: {self.method}"
                )
            
            # Map back to original index
            full_anomaly_mask = pd.Series([False] * total_records, index=df.index)
            full_anomaly_mask.loc[valid_series.index] = anomaly_mask
            
            anomaly_count = full_anomaly_mask.sum()
            normal_count = total_records - anomaly_count - null_mask.sum()
            
            # Score is percentage of non-anomalous records
            score = self.calculate_score(normal_count, total_records - null_mask.sum())
            
            # Get sample anomalies
            sample_failures = self.sample_failed_records(df, full_anomaly_mask)
            
            # Calculate additional statistics
            stats_info.update({
                "column": self.column,
                "method": self.method,
                "direction": self.direction,
                "null_count": int(null_mask.sum()),
                "anomaly_count": int(anomaly_count),
                "normal_count": int(normal_count),
                "mean": round(float(valid_series.mean()), 4),
                "std": round(float(valid_series.std()), 4),
                "min": round(float(valid_series.min()), 4),
                "max": round(float(valid_series.max()), 4),
                "median": round(float(valid_series.median()), 4),
            })
            
            # Add anomaly values summary
            if anomaly_count > 0:
                anomaly_values = valid_series[anomaly_mask]
                stats_info["anomaly_values"] = {
                    "min": round(float(anomaly_values.min()), 4),
                    "max": round(float(anomaly_values.max()), 4),
                    "mean": round(float(anomaly_values.mean()), 4)
                }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return ValidationResult(
                status=self.determine_status(score),
                score=round(score, 4),
                threshold=self.threshold,
                records_checked=total_records,
                records_passed=int(normal_count + null_mask.sum()),
                records_failed=int(anomaly_count),
                details=stats_info,
                sample_failures=sample_failures,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.exception(f"Anomaly detection failed: {e}")
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
    
    def _detect_zscore(self, series: pd.Series) -> tuple:
        """Detect anomalies using Z-score method"""
        mean = series.mean()
        std = series.std()
        
        if std == 0:
            return pd.Series([False] * len(series), index=series.index), {
                "z_threshold": self.z_threshold,
                "message": "Standard deviation is 0, no anomalies detected"
            }
        
        z_scores = (series - mean) / std
        
        if self.direction == "both":
            anomaly_mask = np.abs(z_scores) > self.z_threshold
        elif self.direction == "high":
            anomaly_mask = z_scores > self.z_threshold
        else:  # low
            anomaly_mask = z_scores < -self.z_threshold
        
        return anomaly_mask, {
            "z_threshold": self.z_threshold,
            "upper_bound": round(mean + self.z_threshold * std, 4),
            "lower_bound": round(mean - self.z_threshold * std, 4)
        }
    
    def _detect_iqr(self, series: pd.Series) -> tuple:
        """Detect anomalies using Interquartile Range method"""
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - self.iqr_multiplier * iqr
        upper_bound = q3 + self.iqr_multiplier * iqr
        
        if self.direction == "both":
            anomaly_mask = (series < lower_bound) | (series > upper_bound)
        elif self.direction == "high":
            anomaly_mask = series > upper_bound
        else:  # low
            anomaly_mask = series < lower_bound
        
        return anomaly_mask, {
            "iqr_multiplier": self.iqr_multiplier,
            "q1": round(float(q1), 4),
            "q3": round(float(q3), 4),
            "iqr": round(float(iqr), 4),
            "lower_bound": round(float(lower_bound), 4),
            "upper_bound": round(float(upper_bound), 4)
        }
    
    def _detect_mad(self, series: pd.Series) -> tuple:
        """Detect anomalies using Median Absolute Deviation"""
        median = series.median()
        mad = np.median(np.abs(series - median))
        
        if mad == 0:
            return pd.Series([False] * len(series), index=series.index), {
                "message": "MAD is 0, no anomalies detected"
            }
        
        # Modified Z-score using MAD
        modified_z = 0.6745 * (series - median) / mad
        
        if self.direction == "both":
            anomaly_mask = np.abs(modified_z) > self.z_threshold
        elif self.direction == "high":
            anomaly_mask = modified_z > self.z_threshold
        else:
            anomaly_mask = modified_z < -self.z_threshold
        
        return anomaly_mask, {
            "method": "mad",
            "z_threshold": self.z_threshold,
            "median": round(float(median), 4),
            "mad": round(float(mad), 4)
        }
    
    def _detect_isolation_forest(self, series: pd.Series) -> tuple:
        """Detect anomalies using Isolation Forest"""
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            logger.warning("scikit-learn not available, falling back to zscore")
            return self._detect_zscore(series)
        
        # Reshape for sklearn
        X = series.values.reshape(-1, 1)
        
        clf = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        predictions = clf.fit_predict(X)
        
        # -1 = anomaly, 1 = normal
        anomaly_mask = pd.Series(predictions == -1, index=series.index)
        
        return anomaly_mask, {
            "contamination": self.contamination,
            "method": "isolation_forest"
        }
    
    def validate_config(self) -> List[str]:
        """Validate configuration"""
        errors = super().validate_config()
        
        if not self.config.get("column"):
            errors.append("column is required")
        
        method = self.config.get("method", "zscore")
        if method not in self.METHODS:
            errors.append(f"method must be one of: {self.METHODS}")
        
        direction = self.config.get("direction", "both")
        if direction not in ["both", "high", "low"]:
            errors.append("direction must be 'both', 'high', or 'low'")
        
        z_threshold = self.config.get("z_threshold", 3.0)
        if not isinstance(z_threshold, (int, float)) or z_threshold <= 0:
            errors.append("z_threshold must be a positive number")
        
        return errors
