import pytest
from decision_layer.executor import DecisionExecutor
from decision_layer.registry import DecisionRegistry
from decision_layer.trace_sink import FileSink
from decision_layer.dsl_loader import load_yaml_policy_with_schema
from decision_layer.entities import Order, Customer
from decision_layer.schemas import DecisionSchema, SchemaField, FieldType
from datetime import datetime
import os

def create_refund_schema() -> DecisionSchema:
    """Create a schema for the refund policy"""
    input_schema = {
        "id": SchemaField(name="id", type=FieldType.STRING, required=True),
        "customer": SchemaField(name="customer", type=FieldType.OBJECT, required=True),
        "order_date": SchemaField(name="order_date", type=FieldType.DATETIME, required=True),
        "delivery_date": SchemaField(name="delivery_date", type=FieldType.DATETIME, required=True),
        "issue": SchemaField(name="issue", type=FieldType.STRING, required=True)
    }
    
    output_schema = {
        "refund": SchemaField(name="refund", type=FieldType.INTEGER, required=True),
        "reason": SchemaField(name="reason", type=FieldType.STRING, required=True),
        "rule_id": SchemaField(name="rule_id", type=FieldType.STRING, required=False),
        "customer_tier_multiplier": SchemaField(name="customer_tier_multiplier", type=FieldType.FLOAT, required=False)
    }
    
    return DecisionSchema(
        input_schema=input_schema,
        output_schema=output_schema,
        version="v3.2",
        function_id="refund_policy"
    )

@pytest.fixture
def setup_executor(tmp_path):
    registry = DecisionRegistry()
    sink = FileSink(tmp_path / "trace.jsonl")
    executor = DecisionExecutor(registry, sink, caller="unit-test")

    policy_path = os.path.join(os.path.dirname(__file__), "../policies/refund_policy.yaml")
    fn, schema = load_yaml_policy_with_schema(policy_path)
    
    if schema is None:
        schema = create_refund_schema()
    
    registry.register("refund_policy", "v3.2", fn, schema)

    return executor

def test_refund_full_amount(setup_executor):
    customer = Customer(id="123", signup_date=datetime(2023,1,1), status="gold")
    order = Order(
        id="A1",
        customer=customer,
        order_date=datetime(2024,6,1),
        delivery_date=datetime(2024,6,5),
        issue="late"  # this triggers is_late = True via @property
    )

    result = setup_executor.run("refund_policy", "v3.2", order)
    assert result["refund"] == 100, f"Expected 100, got {result['refund']}"