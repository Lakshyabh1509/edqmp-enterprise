"""
Financial Impact Logic
Calculates potential financial loss from data quality issues
"""

def calculate_financial_impact(validation_result: dict, context: str = "trade") -> dict:
    """
    Calculate estimated financial impact of data quality failures.
    
    Args:
        validation_result: The result dictionary from a validator
        context: Business context (trade, kyc, payments)
        
    Returns:
        Dictionary with impact metrics
    """
    failed_count = validation_result.get("records_failed", 0)
    
    if failed_count == 0:
        return {"estimated_loss": 0.0, "risk_level": "none"}
        
    # Logic for different contexts
    if context == "trade":
        # Avg trade size assumption
        avg_trade_value = 15000.0 
        # Probability that a failed trade results in a break/loss
        failure_probability = 0.05 
        # Cost to fix manually
        manual_fix_cost = 45.0 
        
        operational_cost = failed_count * manual_fix_cost
        risk_exposure = failed_count * avg_trade_value * failure_probability
        
        return {
            "estimated_loss": round(operational_cost + risk_exposure, 2),
            "operational_cost": operational_cost,
            "risk_exposure": risk_exposure,
            "currency": "USD",
            "risk_level": "critical" if risk_exposure > 50000 else "warning"
        }
        
    elif context == "kyc":
        # Regulatory fine risk per violation
        fine_risk = 500.0
        manual_review_cost = 120.0
        
        return {
            "estimated_loss": round(failed_count * (fine_risk + manual_review_cost), 2),
            "risk_level": "critical"
        }
        
    return {"estimated_loss": 0.0, "risk_level": "unknown"}
