"""
Example refund policy decision function

This demonstrates a simple, elegant decision function that determines
refund amounts based on issue type and customer tier.
"""

from typing import Dict, Any
from decision_layer_v2 import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """
    Refund policy decision function
    
    Determines refund amount based on:
    - Issue type (late, damaged, wrong_item, none)
    - Customer tier (bronze, silver, gold, platinum)
    - Order amount (for percentage-based refunds)
    """
    
    # Extract input data
    issue = input_data.get('issue', 'none')
    customer = input_data.get('customer', {})
    customer_tier = customer.get('tier', 'bronze')
    order_amount = input_data.get('order_amount', 0)
    
    # Base refund amounts by issue type
    base_refunds = {
        'late': 100,
        'damaged': 50,
        'wrong_item': 75,
        'none': 0
    }
    
    # Get base refund
    base_refund = base_refunds.get(issue, 0)
    
    # Apply tier multipliers
    tier_multipliers = {
        'bronze': 1.0,
        'silver': 1.1,
        'gold': 1.2,
        'platinum': 1.5
    }
    
    multiplier = tier_multipliers.get(customer_tier, 1.0)
    
    # Calculate final refund
    final_refund = int(base_refund * multiplier)
    
    # Ensure refund doesn't exceed order amount
    final_refund = min(final_refund, order_amount)
    
    # Generate reason
    if final_refund > 0:
        reason = f"{issue} issue with {customer_tier} tier (multiplier: {multiplier})"
    else:
        reason = "No refund applicable"
    
    return {
        'refund_amount': final_refund,
        'reason': reason,
        'issue_type': issue,
        'customer_tier': customer_tier,
        'tier_multiplier': multiplier,
        'base_refund': base_refund,
        'order_amount': order_amount,
        'decision_function': context.function_id,
        'version': context.version
    } 