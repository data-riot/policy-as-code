"""
Example risk assessment decision function

This demonstrates a decision function that assesses transaction risk
based on multiple factors and returns a risk score and recommendation.
"""

from typing import Dict, Any
from decision_layer_v2 import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """
    Risk assessment decision function
    
    Assesses transaction risk based on:
    - Transaction amount
    - Customer history
    - Location
    - Time of day
    - Device type
    """
    
    # Extract input data
    amount = input_data.get('amount', 0)
    customer_history = input_data.get('customer_history', {})
    location = input_data.get('location', {})
    time_of_day = input_data.get('time_of_day', 'day')
    device_type = input_data.get('device_type', 'desktop')
    
    # Initialize risk score
    risk_score = 0
    risk_factors = []
    
    # Amount-based risk
    if amount > 10000:
        risk_score += 30
        risk_factors.append("high_amount")
    elif amount > 5000:
        risk_score += 15
        risk_factors.append("medium_amount")
    
    # Customer history risk
    previous_fraud = customer_history.get('previous_fraud', False)
    account_age_days = customer_history.get('account_age_days', 0)
    transaction_count = customer_history.get('transaction_count', 0)
    
    if previous_fraud:
        risk_score += 40
        risk_factors.append("previous_fraud")
    
    if account_age_days < 30:
        risk_score += 20
        risk_factors.append("new_account")
    
    if transaction_count < 5:
        risk_score += 10
        risk_factors.append("low_transaction_count")
    
    # Location-based risk
    country = location.get('country', 'unknown')
    high_risk_countries = ['XX', 'YY', 'ZZ']  # Example high-risk countries
    
    if country in high_risk_countries:
        risk_score += 25
        risk_factors.append("high_risk_country")
    
    # Time-based risk
    if time_of_day == 'night':
        risk_score += 10
        risk_factors.append("night_transaction")
    
    # Device-based risk
    if device_type == 'mobile':
        risk_score += 5
        risk_factors.append("mobile_device")
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = "high"
        recommendation = "block"
    elif risk_score >= 40:
        risk_level = "medium"
        recommendation = "review"
    else:
        risk_level = "low"
        recommendation = "approve"
    
    return {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'recommendation': recommendation,
        'risk_factors': risk_factors,
        'amount': amount,
        'customer_history': {
            'previous_fraud': previous_fraud,
            'account_age_days': account_age_days,
            'transaction_count': transaction_count
        },
        'location': location,
        'time_of_day': time_of_day,
        'device_type': device_type,
        'decision_function': context.function_id,
        'version': context.version
    } 