import pytest
from datetime import datetime
from dataclasses import dataclass
from decision_layer.executor import DecisionExecutor, resolve_field, serialize_for_json
from decision_layer.registry import DecisionRegistry
from decision_layer.trace_sink import FileSink, TraceSink
import tempfile
import os
import json
from typing import Dict, Any

from decision_layer.schemas import DecisionSchema, SchemaField, FieldType

@dataclass
class TestCustomer:
    id: str
    signup_date: datetime
    status: str

@dataclass
class TestOrder:
    id: str
    customer: TestCustomer
    order_date: datetime
    delivery_date: datetime
    issue: str

    @property
    def is_late(self):
        return self.issue == "late"

class MockTraceSink(TraceSink):
    def __init__(self):
        self.traces = []
    
    def emit(self, trace):
        self.traces.append(trace)

def create_test_schema() -> DecisionSchema:
    """Create a basic test schema for testing"""
    input_schema = {
        "id": SchemaField(name="id", type=FieldType.STRING, required=True),
        "customer": SchemaField(name="customer", type=FieldType.OBJECT, required=True),
        "order_date": SchemaField(name="order_date", type=FieldType.DATETIME, required=True),
        "delivery_date": SchemaField(name="delivery_date", type=FieldType.DATETIME, required=True),
        "issue": SchemaField(name="issue", type=FieldType.STRING, required=True)
    }
    
    output_schema = {
        "result": SchemaField(name="result", type=FieldType.STRING, required=True),
        "value": SchemaField(name="value", type=FieldType.INTEGER, required=False)
    }
    
    return DecisionSchema(
        input_schema=input_schema,
        output_schema=output_schema,
        version="v1.0",
        function_id="test_decision"
    )

def test_resolve_field_simple():
    """Test resolve_field with simple attribute access"""
    customer = TestCustomer(id="123", signup_date=datetime(2023, 1, 1), status="gold")
    assert resolve_field(customer, "id") == "123"
    assert resolve_field(customer, "status") == "gold"

def test_resolve_field_property():
    """Test resolve_field with property access"""
    customer = TestCustomer(id="123", signup_date=datetime(2023, 1, 1), status="gold")
    order = TestOrder(
        id="A1",
        customer=customer,
        order_date=datetime(2024, 6, 1),
        delivery_date=datetime(2024, 6, 5),
        issue="late"
    )
    assert resolve_field(order, "is_late") == True

def test_resolve_field_nested():
    """Test resolve_field with nested attribute access"""
    customer = TestCustomer(id="123", signup_date=datetime(2023, 1, 1), status="gold")
    order = TestOrder(
        id="A1",
        customer=customer,
        order_date=datetime(2024, 6, 1),
        delivery_date=datetime(2024, 6, 5),
        issue="late"
    )
    assert resolve_field(order, "customer.id") == "123"
    assert resolve_field(order, "customer.status") == "gold"

def test_resolve_field_missing():
    """Test resolve_field with missing field"""
    customer = TestCustomer(id="123", signup_date=datetime(2023, 1, 1), status="gold")
    with pytest.raises(AttributeError):
        resolve_field(customer, "nonexistent")

def test_serialize_for_json_dataclass():
    """Test serialize_for_json with dataclass"""
    customer = TestCustomer(id="123", signup_date=datetime(2023, 1, 1), status="gold")
    result = serialize_for_json(customer)
    assert result["id"] == "123"
    assert result["status"] == "gold"
    assert result["signup_date"] == "2023-01-01T00:00:00"

def test_serialize_for_json_datetime():
    """Test serialize_for_json with datetime"""
    dt = datetime(2023, 1, 1, 12, 30, 45)
    result = serialize_for_json(dt)
    assert result == "2023-01-01T12:30:45"

def test_serialize_for_json_nested():
    """Test serialize_for_json with nested structures"""
    customer = TestCustomer(id="123", signup_date=datetime(2023, 1, 1), status="gold")
    order = TestOrder(
        id="A1",
        customer=customer,
        order_date=datetime(2024, 6, 1),
        delivery_date=datetime(2024, 6, 5),
        issue="late"
    )
    result = serialize_for_json(order)
    assert result["id"] == "A1"
    assert result["customer"]["id"] == "123"
    assert result["order_date"] == "2024-06-01T00:00:00"

def test_executor_initialization():
    """Test DecisionExecutor initialization"""
    registry = DecisionRegistry()
    sink = MockTraceSink()
    executor = DecisionExecutor(registry, sink, caller="test")
    
    assert executor.registry == registry
    assert executor.trace_sink == sink
    assert executor.caller == "test"

def test_executor_run_success():
    """Test successful execution of a decision function"""
    registry = DecisionRegistry()
    sink = MockTraceSink()
    executor = DecisionExecutor(registry, sink, caller="test")
    
    # Register a simple decision function
    def test_decision(obj):
        return {"result": "success", "value": 42}
    
    schema = create_test_schema()
    registry.register("test_decision", "v1.0", test_decision, schema)
    
    # Create test input that matches the schema
    @dataclass
    class TestInput:
        value: str
    
    input_obj = TestInput("test")
    result = executor.run("test_decision", "v1.0", input_obj, enable_validation=False)
    
    assert result["result"] == "success"
    assert result["value"] == 42
    
    # Check that trace was emitted
    assert len(sink.traces) == 1
    trace = sink.traces[0]
    assert trace["function_id"] == "test_decision"
    assert trace["version"] == "v1.0"
    assert trace["caller"] == "test"
    assert trace["status"] == "success"
    assert "invocation_id" in trace
    assert "timestamp" in trace

def test_executor_run_missing_function():
    """Test error when decision function is not found"""
    registry = DecisionRegistry()
    sink = MockTraceSink()
    executor = DecisionExecutor(registry, sink, caller="test")
    
    customer = TestCustomer(id="123", signup_date=datetime(2023, 1, 1), status="gold")
    
    with pytest.raises(ValueError, match="Decision function 'missing' version 'v1.0' not found"):
        executor.run("missing", "v1.0", customer)

def test_executor_run_invalid_input():
    """Test error when input is not a dataclass or object with attributes"""
    registry = DecisionRegistry()
    sink = MockTraceSink()
    executor = DecisionExecutor(registry, sink, caller="test")
    
    # Register a function that expects an object with attributes
    def test_decision(obj):
        # This will fail when trying to access attributes on a string
        return {"result": obj.some_attribute}
    
    schema = create_test_schema()
    registry.register("test", "v1.0", test_decision, schema)
    
    # Test with invalid input (string instead of object)
    # The function will fail when trying to access attributes on the string
    with pytest.raises(RuntimeError, match="Decision execution failed"):
        executor.run("test", "v1.0", "not an object", enable_validation=False)

def test_executor_with_file_sink():
    """Test executor with FileSink for actual file writing"""
    registry = DecisionRegistry()
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_file = f.name
    
    try:
        sink = FileSink(temp_file)
        executor = DecisionExecutor(registry, sink, caller="test")
        
        def test_decision(obj):
            return {"result": "success"}
        
        schema = create_test_schema()
        registry.register("test_decision", "v1.0", test_decision, schema)
        
        # Create test input that matches the schema
        @dataclass
        class TestInput:
            value: str
        
        input_obj = TestInput("test")
        result = executor.run("test_decision", "v1.0", input_obj, enable_validation=False)
        
        assert result["result"] == "success"
        
        # Check that file was written
        assert os.path.exists(temp_file)
        with open(temp_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            
            trace = json.loads(lines[0])
            assert trace["function_id"] == "test_decision"
            assert trace["version"] == "v1.0"
            assert trace["caller"] == "test"
            assert trace["status"] == "success"
    
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file) 