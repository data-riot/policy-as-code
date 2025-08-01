from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """Refund policy decision function"""

    amount = input_data.get('amount', 0)
    issue = input_data.get('issue', '')
    customer_tier = input_data.get('customer_tier', 'standard')

    # Decision logic
    if amount > 1000:
        return {"approved": False, "reason": "Amount exceeds limit"}

    if issue == "damaged":
        if customer_tier == "premium":
            return {"approved": True, "reason": "Premium customer damaged item policy"}
        else:
            return {"approved": True, "reason": "Standard damaged item policy"}

    if issue == "wrong_item":
        return {"approved": True, "reason": "Wrong item policy"}

    return {"approved": False, "reason": "Issue not covered by policy"}