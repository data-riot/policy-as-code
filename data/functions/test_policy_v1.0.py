from typing import Any, Dict

from decision_layer_v2 import DecisionContext


def decision_function(
    input_data: Dict[str, Any], context: DecisionContext
) -> Dict[str, Any]:
    """Test decision function"""
    amount = input_data.get("amount", 0)

    if amount > 1000:
        return {"approved": False, "reason": "Amount too high"}
    else:
        return {"approved": True, "reason": "Amount within limits"}
