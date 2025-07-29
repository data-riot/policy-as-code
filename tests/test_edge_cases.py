import pytest
import tempfile
import os
import json
from dataclasses import dataclass
from decision_layer.executor import DecisionExecutor, resolve_field
from decision_layer.registry import DecisionRegistry
from decision_layer.trace_sink import FileSink
from decision_layer.dsl_loader import load_yaml_policy
from decision_layer.entities import Order, Customer
from datetime import datetime, timezone

@dataclass
class SimpleTestObject:
    field1: str = "value1"
    field2: int = 42

def test_resolve_field_success():
    """Test successful field resolution"""
    obj = SimpleTestObject()
    assert resolve_field(obj, "field1") == "value1"
    assert resolve_field(obj, "field2") == 42

def test_resolve_field_missing_attribute():
    """Test field resolution with missing attribute"""
    obj = SimpleTestObject()
    with pytest.raises(ValueError, match="Field 'nonexistent' not found"):
        resolve_field(obj, "nonexistent")

def test_decision_executor_with_none_trace_sink():
    """Test executor works correctly with None trace sink"""
    registry = DecisionRegistry()
    executor = DecisionExecutor(registry, None, caller="test")
    
    def simple_policy(obj):
        return {"result": "test"}
    
    registry.register("test_policy", "v1.0", simple_policy)
    
    result = executor.run("test_policy", "v1.0", SimpleTestObject())
    assert result == {"result": "test"}

def test_decision_executor_with_trace_sink(tmp_path):
    """Test executor works correctly with trace sink"""
    trace_file = tmp_path / "test_trace.jsonl"
    registry = DecisionRegistry()
    sink = FileSink(str(trace_file))
    executor = DecisionExecutor(registry, sink, caller="test")
    
    def simple_policy(obj):
        return {"result": "test", "rule_id": "test_rule"}
    
    registry.register("test_policy", "v1.0", simple_policy)
    
    result = executor.run("test_policy", "v1.0", SimpleTestObject())
    assert result == {"result": "test", "rule_id": "test_rule"}
    
    # Verify trace was written
    assert trace_file.exists()
    with open(trace_file) as f:
        trace_data = json.loads(f.read().strip())
        assert trace_data["output"] == {"result": "test", "rule_id": "test_rule"}
        assert trace_data["version"] == "v1.0"
        assert trace_data["caller"] == "test"
        assert "timestamp" in trace_data

def test_registry_get_missing_policy():
    """Test registry returns None for missing policy"""
    registry = DecisionRegistry()
    result = registry.get("nonexistent", "v1.0")
    assert result is None

def test_yaml_policy_with_default_fallback(tmp_path):
    """Test YAML policy falls back to default when no rules match"""
    policy_file = tmp_path / "test_policy.yaml"
    policy_content = """
function: test_policy
version: v1.0
rules:
  - id: test_rule
    if: { field: "field1", operator: "==", value: "nomatch" }
    then: { result: "matched" }
default:
  result: "default"
"""
    with open(policy_file, 'w') as f:
        f.write(policy_content)
    
    policy_fn = load_yaml_policy(str(policy_file))
    obj = SimpleTestObject()
    result = policy_fn(obj)
    
    assert result == {"result": "default"}

def test_yaml_policy_with_rule_match(tmp_path):
    """Test YAML policy returns rule result when condition matches"""
    policy_file = tmp_path / "test_policy.yaml"
    policy_content = """
function: test_policy
version: v1.0
rules:
  - id: test_rule
    if: { field: "field1", operator: "==", value: "value1" }
    then: { result: "matched" }
default:
  result: "default"
"""
    with open(policy_file, 'w') as f:
        f.write(policy_content)
    
    policy_fn = load_yaml_policy(str(policy_file))
    obj = SimpleTestObject()
    result = policy_fn(obj)
    
    assert result == {"result": "matched", "rule_id": "test_rule"}

def test_yaml_policy_multiple_rules_first_match(tmp_path):
    """Test YAML policy returns first matching rule"""
    policy_file = tmp_path / "test_policy.yaml"
    policy_content = """
function: test_policy
version: v1.0
rules:
  - id: rule1
    if: { field: "field1", operator: "==", value: "value1" }
    then: { result: "first" }
  - id: rule2
    if: { field: "field1", operator: "==", value: "value1" }
    then: { result: "second" }
default:
  result: "default"
"""
    with open(policy_file, 'w') as f:
        f.write(policy_content)
    
    policy_fn = load_yaml_policy(str(policy_file))
    obj = SimpleTestObject()
    result = policy_fn(obj)
    
    # Should match first rule
    assert result == {"result": "first", "rule_id": "rule1"}

def test_refund_policy_damaged_case():
    """Test refund policy with damaged item case"""
    customer = Customer(id="123", signup_date=datetime(2023,1,1), status="gold")
    order = Order(
        id="A1",
        customer=customer,
        order_date=datetime(2024,6,1),
        delivery_date=datetime(2024,6,5),
        issue="damaged"  # This should trigger damaged rule
    )
    
    policy_fn = load_yaml_policy("policies/refund_policy.yaml")
    result = policy_fn(order)
    
    assert result["refund"] == 50
    assert result["reason"] == "Damaged item"
    assert result["rule_id"] == "damaged"

def test_refund_policy_no_refund_case():
    """Test refund policy when no refund is eligible"""
    customer = Customer(id="123", signup_date=datetime(2023,1,1), status="gold")
    order = Order(
        id="A1",
        customer=customer,
        order_date=datetime(2024,6,1),
        delivery_date=datetime(2024,6,5),
        issue="other"  # This should not match any rule
    )
    
    policy_fn = load_yaml_policy("policies/refund_policy.yaml")
    result = policy_fn(order)
    
    assert result["refund"] == 0
    assert result["reason"] == "Not eligible"

def test_order_is_late_property():
    """Test Order.is_late property"""
    customer = Customer(id="123", signup_date=datetime(2023,1,1), status="gold")
    
    # Test late order
    late_order = Order(
        id="A1",
        customer=customer,
        order_date=datetime(2024,6,1),
        delivery_date=datetime(2024,6,5),
        issue="late"
    )
    assert late_order.is_late == True
    
    # Test non-late order
    normal_order = Order(
        id="A2",
        customer=customer,
        order_date=datetime(2024,6,1),
        delivery_date=datetime(2024,6,5),
        issue="damaged"
    )
    assert normal_order.is_late == False