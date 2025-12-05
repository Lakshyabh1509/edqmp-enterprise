"""
Consistency Validator
Validates cross-field relationships and business rules
"""

from typing import Dict, Any, List, Callable
import time
import logging

import pandas as pd
import numpy as np

from app.engines.validators.base import (
    BaseValidator, 
    ValidationResult, 
    ValidatorRegistry
)

logger = logging.getLogger(__name__)


@ValidatorRegistry.register("consistency")
class ConsistencyValidator(BaseValidator):
    """
    Validates data consistency through cross-field rules.
    
    Configuration options:
        rules: List of consistency rules to apply
        threshold: Minimum required compliance rate (default: 1.0)
        fail_on_first: Stop on first rule failure (default: False)
    
    Rule format:
        {
            "name": "rule_name",
            "type": "comparison|expression|lookup",
            "config": { rule-specific configuration }
        }
    
    Rule types:
        - comparison: Compare two columns (e.g., start_date <= end_date)
        - expression: Custom pandas expression
        - lookup: Check value exists in reference set
    
    Example config:
        {
            "rules": [
                {
                    "name": "date_order",
                    "type": "comparison",
                    "config": {
                        "left": "start_date",
                        "operator": "<=",
                        "right": "end_date"
                    }
                },
                {
                    "name": "positive_amount",
                    "type": "expression",
                    "config": {
                        "expression": "quantity > 0 and price > 0"
                    }
                }
            ],
            "threshold": 0.99
        }
    """
    
    validator_type = "consistency"
    
    # Supported comparison operators
    OPERATORS = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rules = config.get("rules", [])
        self.fail_on_first = config.get("fail_on_first", False)
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Check data consistency against defined rules.
        
        Returns a ValidationResult with:
        - Score: Percentage of records passing all rules
        - Details: Per-rule results
        - Sample failures: Records that violate rules
        """
        start_time = time.time()
        
        try:
            if not self.rules:
                return ValidationResult(
                    status="passed",
                    score=1.0,
                    threshold=self.threshold,
                    records_checked=len(df),
                    records_passed=len(df),
                    records_failed=0,
                    details={"message": "No rules configured"}
                )
            
            total_records = len(df)
            rule_results = {}
            combined_pass_mask = pd.Series([True] * total_records, index=df.index)
            
            for rule in self.rules:
                rule_name = rule.get("name", "unnamed_rule")
                rule_type = rule.get("type", "expression")
                rule_config = rule.get("config", {})
                
                try:
                    if rule_type == "comparison":
                        pass_mask = self._evaluate_comparison(df, rule_config)
                    elif rule_type == "expression":
                        pass_mask = self._evaluate_expression(df, rule_config)
                    elif rule_type == "lookup":
                        pass_mask = self._evaluate_lookup(df, rule_config)
                    else:
                        logger.warning(f"Unknown rule type: {rule_type}")
                        pass_mask = pd.Series([True] * total_records, index=df.index)
                    
                    passed = pass_mask.sum()
                    failed = (~pass_mask).sum()
                    
                    rule_results[rule_name] = {
                        "type": rule_type,
                        "passed": int(passed),
                        "failed": int(failed),
                        "score": round(self.calculate_score(passed, total_records), 4),
                        "status": "passed" if passed == total_records else "failed"
                    }
                    
                    combined_pass_mask = combined_pass_mask & pass_mask
                    
                    if self.fail_on_first and failed > 0:
                        break
                        
                except Exception as e:
                    logger.error(f"Rule '{rule_name}' evaluation failed: {e}")
                    rule_results[rule_name] = {
                        "type": rule_type,
                        "error": str(e),
                        "status": "error"
                    }
            
            # Calculate overall results
            records_passed = combined_pass_mask.sum()
            records_failed = (~combined_pass_mask).sum()
            score = self.calculate_score(records_passed, total_records)
            
            # Get sample failures
            sample_failures = self.sample_failed_records(df, ~combined_pass_mask)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return ValidationResult(
                status=self.determine_status(score),
                score=round(score, 4),
                threshold=self.threshold,
                records_checked=total_records,
                records_passed=int(records_passed),
                records_failed=int(records_failed),
                details={
                    "rules_evaluated": len(self.rules),
                    "rule_results": rule_results
                },
                sample_failures=sample_failures,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.exception(f"Consistency validation failed: {e}")
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
    
    def _evaluate_comparison(
        self, 
        df: pd.DataFrame, 
        config: Dict[str, Any]
    ) -> pd.Series:
        """Evaluate a comparison rule"""
        left_col = config.get("left")
        operator = config.get("operator", "==")
        right = config.get("right")
        
        if left_col not in df.columns:
            raise ValueError(f"Column '{left_col}' not found")
        
        left_values = df[left_col]
        
        # Right can be a column name or a literal value
        if isinstance(right, str) and right in df.columns:
            right_values = df[right]
        else:
            right_values = right
        
        op_func = self.OPERATORS.get(operator)
        if op_func is None:
            raise ValueError(f"Unknown operator: {operator}")
        
        # Handle nulls - null comparisons return False
        result = op_func(left_values, right_values)
        if isinstance(result, pd.Series):
            result = result.fillna(False)
        
        return result
    
    def _evaluate_expression(
        self, 
        df: pd.DataFrame, 
        config: Dict[str, Any]
    ) -> pd.Series:
        """Evaluate a pandas expression rule"""
        expression = config.get("expression", "True")
        
        # Use pandas eval for safe expression evaluation
        try:
            result = df.eval(expression, engine='python')
            if isinstance(result, bool):
                return pd.Series([result] * len(df), index=df.index)
            return result.fillna(False)
        except Exception as e:
            raise ValueError(f"Expression evaluation failed: {e}")
    
    def _evaluate_lookup(
        self, 
        df: pd.DataFrame, 
        config: Dict[str, Any]
    ) -> pd.Series:
        """Evaluate a lookup rule (value in reference set)"""
        column = config.get("column")
        values = config.get("values", [])
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")
        
        return df[column].isin(values)
    
    def validate_config(self) -> List[str]:
        """Validate configuration"""
        errors = super().validate_config()
        
        rules = self.config.get("rules", [])
        if not isinstance(rules, list):
            errors.append("rules must be a list")
        else:
            for i, rule in enumerate(rules):
                if not isinstance(rule, dict):
                    errors.append(f"Rule {i} must be a dictionary")
                elif "type" not in rule:
                    errors.append(f"Rule {i} missing 'type' field")
        
        return errors
