import pytest
from datetime import datetime
from dataclasses import dataclass
from decision_layer.executor import DecisionExecutor, resolve_field, serialize_for_json
from decision_layer.registry import DecisionRegistry
from decision_layer.trace_sink import TraceSink, FileSink
from decision_layer.dsl_loader import load_yaml_policy
import tempfile
import os

@dataclass
class EmptyObject:
    pass

@dataclass
class NestedObject:
    inner: EmptyObject

class TestTraceSink(TraceSink):
    def emit(self, trace):
        pass

def test_resolve_field_empty_path():
    """Test resolve_field with empty path"""
    obj = EmptyObject()
    result = resolve_field(obj, "")
    assert result == obj

def test_resolve_field_callable_attribute():
    """Test resolve_field with callable attributes that aren't properties"""
    @dataclass
    class TestObj:
        def method(self):
            return "method_result"
    
    obj = TestObj()
    result = resolve_field(obj, "method")
    assert result == "method_result"

def test_serialize_for_json_empty_dataclass():
    """Test serialize_for_json with empty dataclass"""
    obj = EmptyObject()
    result = serialize_for_json(obj)
    assert result == {}

def test_serialize_for_json_none_values():
    """Test serialize_for_json with None values"""
    @dataclass
    class TestObj:
        value: str = None
    
    obj = TestObj()
    result = serialize_for_json(obj)
    assert result["value"] is None

def test_serialize_for_json_list_with_dataclasses():
    """Test serialize_for_json with list containing dataclasses"""
    @dataclass
    class Item:
        id: str
    
    items = [Item("1"), Item("2")]
    result = serialize_for_json(items)
    assert len(result) == 2
    assert result[0]["id"] == "1"
    assert result[1]["id"] == "2"

def test_serialize_for_json_dict_with_dataclasses():
    """Test serialize_for_json with dict containing dataclasses"""
    @dataclass
    class Item:
        id: str
    
    data = {"item1": Item("1"), "item2": Item("2")}
    result = serialize_for_json(data)
    assert result["item1"]["id"] == "1"
    assert result["item2"]["id"] == "2"

def test_executor_with_none_sink():
    """Test executor with None trace sink"""
    registry = DecisionRegistry()
    executor = DecisionExecutor(registry, None, caller="test")
    
    def test_decision(obj):
        return {"result": "success"}
    
    registry.register("test_decision", "v1.0", test_decision)
    
    @dataclass
    class TestInput:
        value: str
    
    input_obj = TestInput("test")
    
    # Should not raise an error
    result = executor.run("test_decision", "v1.0", input_obj)
    assert result["result"] == "success"

def test_file_sink_directory_creation():
    """Test FileSink creates directory if it doesn't exist"""
    with tempfile.TemporaryDirectory() as temp_dir:
        trace_file = os.path.join(temp_dir, "subdir", "trace.jsonl")
        sink = FileSink(trace_file)
        
        trace = {"test": "data"}
        sink.emit(trace)
        
        assert os.path.exists(trace_file)
        with open(trace_file, 'r') as f:
            content = f.read()
            assert "test" in content

def test_file_sink_multiple_writes():
    """Test FileSink handles multiple writes correctly"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_file = f.name
    
    try:
        sink = FileSink(temp_file)
        
        trace1 = {"id": 1, "data": "first"}
        trace2 = {"id": 2, "data": "second"}
        
        sink.emit(trace1)
        sink.emit(trace2)
        
        with open(temp_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
            assert "first" in lines[0]
            assert "second" in lines[1]
    
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def test_registry_get_nonexistent():
    """Test registry get with nonexistent function"""
    registry = DecisionRegistry()
    result = registry.get("nonexistent", "v1.0")
    assert result is None

def test_registry_register_overwrite():
    """Test registry can overwrite existing functions"""
    registry = DecisionRegistry()
    
    def func1(obj):
        return {"version": "1"}
    
    def func2(obj):
        return {"version": "2"}
    
    registry.register("test", "v1.0", func1)
    registry.register("test", "v1.0", func2)  # Overwrite
    
    result = registry.get("test", "v1.0")
    assert result is func2

def test_dsl_loader_with_complex_rules():
    """Test DSL loader with more complex rule conditions"""
    yaml_content = """
function: test_policy
version: v1.0
rules:
  - id: rule1
    if: { field: "customer.status", operator: "==", value: "gold" }
    then: { result: "gold_customer" }
  - id: rule2
    if: { field: "issue", operator: "==", value: "damaged" }
    then: { result: "damaged_item" }
default:
  result: "default_case"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name
    
    try:
        policy_fn = load_yaml_policy(yaml_path)
        
        @dataclass
        class Customer:
            status: str
        
        @dataclass
        class TestInput:
            customer: Customer
            issue: str
        
        # Test gold customer
        input1 = TestInput(Customer("gold"), "none")
        result1 = policy_fn(input1)
        assert result1["result"] == "gold_customer"
        
        # Test damaged item
        input2 = TestInput(Customer("silver"), "damaged")
        result2 = policy_fn(input2)
        assert result2["result"] == "damaged_item"
        
        # Test default case
        input3 = TestInput(Customer("silver"), "none")
        result3 = policy_fn(input3)
        assert result3["result"] == "default_case"
    
    finally:
        if os.path.exists(yaml_path):
            os.unlink(yaml_path)

def test_executor_error_handling():
    """Test executor handles decision function errors gracefully"""
    registry = DecisionRegistry()
    sink = TestTraceSink()
    executor = DecisionExecutor(registry, sink, caller="test")
    
    def failing_decision(obj):
        raise ValueError("Decision function failed")
    
    registry.register("failing_decision", "v1.0", failing_decision)
    
    @dataclass
    class TestInput:
        value: str
    
    input_obj = TestInput("test")
    
    with pytest.raises(ValueError, match="Decision function failed"):
        executor.run("failing_decision", "v1.0", input_obj)

def test_resolve_field_deep_nesting():
    """Test resolve_field with deeply nested objects"""
    @dataclass
    class Level3:
        value: str
    
    @dataclass
    class Level2:
        level3: Level3
    
    @dataclass
    class Level1:
        level2: Level2
    
    obj = Level1(Level2(Level3("deep_value")))
    
    result = resolve_field(obj, "level2.level3.value")
    assert result == "deep_value"

def test_serialize_for_json_complex_nested():
    """Test serialize_for_json with complex nested structures"""
    @dataclass
    class NestedItem:
        id: str
        tags: list
    
    @dataclass
    class ComplexObject:
        items: list
        metadata: dict
        timestamp: datetime
    
    items = [NestedItem("1", ["tag1", "tag2"]), NestedItem("2", ["tag3"])]
    metadata = {"version": "1.0", "author": "test"}
    timestamp = datetime(2023, 1, 1, 12, 0, 0)
    
    obj = ComplexObject(items, metadata, timestamp)
    result = serialize_for_json(obj)
    
    assert len(result["items"]) == 2
    assert result["items"][0]["id"] == "1"
    assert result["items"][0]["tags"] == ["tag1", "tag2"]
    assert result["metadata"]["version"] == "1.0"
    assert result["timestamp"] == "2023-01-01T12:00:00" 