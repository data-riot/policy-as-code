import pytest
from decision_layer.executor import DecisionExecutor
from decision_layer.registry import DecisionRegistry
from decision_layer.trace_sink import FileSink
from decision_layer.dsl_loader import load_yaml_policy
from decision_layer.entities import Order, Customer
from datetime import datetime
import os

@pytest.fixture
def setup_executor(tmp_path):
    registry = DecisionRegistry()
    sink = FileSink(tmp_path / "trace.jsonl")
    executor = DecisionExecutor(registry, sink, caller="unit-test")

    policy_path = os.path.join(os.path.dirname(__file__), "../policies/refund_policy.yaml")
    fn = load_yaml_policy(policy_path)
    registry.register("refund_policy", "v3.2", fn)

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