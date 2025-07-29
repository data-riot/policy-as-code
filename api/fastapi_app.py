from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from decision_layer.entities import Order, Customer
from decision_layer.dsl_loader import load_yaml_policy
from decision_layer.executor import DecisionExecutor
from decision_layer.registry import DecisionRegistry
from decision_layer.trace_sink import FileSink
from datetime import datetime
import os

# Pydantic models for API input validation
class CustomerInput(BaseModel):
    id: str
    signup_date: str  # ISO format string
    status: str

class OrderInput(BaseModel):
    id: str
    customer: CustomerInput
    order_date: str  # ISO format string
    delivery_date: str  # ISO format string
    issue: str

app = FastAPI(title="Decision Cortex API", version="1.0")

# Setup
registry = DecisionRegistry()
trace_sink = FileSink("traces/api_trace_log.jsonl")
executor = DecisionExecutor(registry, trace_sink, caller="api")

# Register policies
POLICY_NAME = "refund_policy"
POLICY_VERSION = "v3.2"
POLICY_PATH = "policies/refund_policy.yaml"

if not os.path.exists(POLICY_PATH):
    raise FileNotFoundError(f"{POLICY_PATH} not found")

fn = load_yaml_policy(POLICY_PATH)
registry.register(POLICY_NAME, POLICY_VERSION, fn)

def convert_to_dataclass(input_data: OrderInput) -> Order:
    """Convert Pydantic model to dataclass"""
    customer = Customer(
        id=input_data.customer.id,
        signup_date=datetime.fromisoformat(input_data.customer.signup_date),
        status=input_data.customer.status
    )
    return Order(
        id=input_data.id,
        customer=customer,
        order_date=datetime.fromisoformat(input_data.order_date),
        delivery_date=datetime.fromisoformat(input_data.delivery_date),
        issue=input_data.issue
    )

@app.post("/decide/{policy_name}/{version}")
def decide(policy_name: str, version: str, input_data: OrderInput) -> Dict[str, Any]:
    try:
        order = convert_to_dataclass(input_data)
        result = executor.run(policy_name, version, order)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))