from typing import Callable, Dict, Any, Union
from uuid import uuid4
from datetime import datetime
from dataclasses import is_dataclass, asdict
import json

def serialize_for_json(obj: Any) -> Any:
    """
    Recursively serialize objects for JSON output.
    Handles dataclasses, datetime objects, and nested structures.
    """
    if is_dataclass(obj):
        return {field: serialize_for_json(getattr(obj, field)) 
                for field in obj.__dataclass_fields__}
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    else:
        return obj

def resolve_field(obj: Any, field_path: str) -> Any:
    """
    Resolve a field value from an object using dot notation.
    Supports both dataclass attributes and properties.
    """
    if not field_path:
        return obj
    
    parts = field_path.split('.')
    current = obj
    
    for part in parts:
        if hasattr(current, part):
            current = getattr(current, part)
            # If it's a property, we need to call it
            if hasattr(current, '__call__') and not isinstance(current, type):
                current = current()
        else:
            raise AttributeError(f"Field '{field_path}' not found on object")
    
    return current

class DecisionExecutor:
    def __init__(self, registry, trace_sink, caller: str = "unknown"):
        self.registry = registry
        self.trace_sink = trace_sink
        self.caller = caller

    def run(self, name: str, version: str, input_obj: Any) -> Dict[str, Any]:
        """
        Run a decision function by name and version.
        Logs input/output and metadata to trace sink.
        """
        if not (is_dataclass(input_obj) or hasattr(input_obj, '__dict__')):
            raise TypeError("Input must be a dataclass or object with attributes.")

        decision_fn: Callable = self.registry.get(name, version)
        if decision_fn is None:
            raise ValueError(f"Decision function '{name}' version '{version}' not found in registry")
        
        # Convert dataclass to dict for serialization
        if is_dataclass(input_obj):
            input_data = serialize_for_json(input_obj)
        else:
            input_data = serialize_for_json(input_obj.__dict__)
        
        output = decision_fn(input_obj)

        trace = {
            "input": input_data,
            "output": output,
            "decision_id": name,
            "version": version,
            "invocation_id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "caller": self.caller,
            "status": "success"
        }

        if self.trace_sink is not None:
            self.trace_sink.emit(trace)
        return output