from executor import DecisionExecutor
from registry import DecisionRegistry
from trace_sink import FileSink
from dsl_loader import load_yaml_policy
from entities import Order, Customer
from datetime import datetime

def test_refund():
    registry = DecisionRegistry()
    sink = FileSink("demo_trace.jsonl")
    executor = DecisionExecutor(registry, sink, caller="unit-test")

    fn = load_yaml_policy("refund_policy.yaml")
    registry.register("refund_policy", "v3.2", fn)

    customer = Customer(id="123", signup_date=datetime(2023,1,1), status="gold")
    order = Order(id="A1", customer=customer, order_date=datetime(2024,6,1), delivery_date=datetime(2024,6,5), issue="late")

    result = executor.run("refund_policy", "v3.2", order)
    assert result["refund"] == 100