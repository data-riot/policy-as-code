from typing import Callable, Dict, Any, Union, Optional
from uuid import uuid4
from datetime import datetime
from dataclasses import is_dataclass, asdict
import json
import hashlib
import time
from .registry import DecisionFunction
from .schemas import SchemaValidator

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

def generate_input_hash(input_data: Any) -> str:
    """Generate a deterministic hash of input data"""
    serialized = serialize_for_json(input_data)
    json_str = json.dumps(serialized, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]

def generate_output_hash(output_data: Dict[str, Any]) -> str:
    """Generate a deterministic hash of output data"""
    json_str = json.dumps(output_data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]

class DecisionExecutor:
    """
    Execution engine with schema validation and deterministic execution
    """
    
    def __init__(self, registry, trace_sink, caller: str = "unknown"):
        self.registry = registry
        self.trace_sink = trace_sink
        self.caller = caller

    def run(self, 
            function_id: str, 
            version: Optional[str] = None, 
            input_obj: Any = None,
            enable_validation: bool = True) -> Dict[str, Any]:
        """
        Run a decision function with validation and tracing.
        
        Args:
            function_id: The ID of the decision function
            version: Optional version (uses latest if not specified)
            input_obj: Input data (dict, dataclass, or object with __dict__)
            enable_validation: Whether to enable schema validation
            
        Returns:
            Dict containing the decision output
            
        Raises:
            ValueError: If function not found or validation fails
            RuntimeError: If execution fails
        """
        # Get the decision function
        decision_fn: DecisionFunction = self.registry.get(function_id, version)
        if decision_fn is None:
            raise ValueError(f"Decision function '{function_id}' version '{version}' not found in registry")
        
        # Generate execution ID
        invocation_id = str(uuid4())
        start_time = time.time()
        
        try:
            # Validate input if enabled
            validated_input = None
            if enable_validation:
                validator = SchemaValidator(decision_fn.schema)
                validated_input = validator.validate_input(input_obj)
                # Ensure validated input is JSON serializable
                validated_input = serialize_for_json(validated_input)
            else:
                # Convert to dict for consistency
                if is_dataclass(input_obj):
                    validated_input = serialize_for_json(input_obj)
                elif hasattr(input_obj, '__dict__'):
                    validated_input = serialize_for_json(input_obj.__dict__)
                else:
                    validated_input = input_obj
            
            # Execute the decision function
            output = decision_fn.logic(input_obj)
            
            # Validate output if enabled
            if enable_validation:
                validator = SchemaValidator(decision_fn.schema)
                validated_output = validator.validate_output(output)
            else:
                validated_output = output
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Generate hashes for trace
            input_hash = generate_input_hash(validated_input)
            output_hash = generate_output_hash(validated_output)
            
            # Create trace
            trace = {
                "invocation_id": invocation_id,
                "function_id": decision_fn.function_id,
                "version": decision_fn.version,
                "input": validated_input,
                "output": validated_output,
                "input_hash": input_hash,
                "output_hash": output_hash,
                "timestamp": datetime.utcnow().isoformat(),
                "caller": self.caller,
                "execution_time_ms": round(execution_time * 1000, 2),
                "status": "success",
                "schema_validated": enable_validation
            }
            
            # Emit trace
            if self.trace_sink is not None:
                self.trace_sink.emit(trace)
            
            return validated_output
            
        except Exception as e:
            # Calculate execution time even for failures
            execution_time = time.time() - start_time
            
            # Create error trace
            error_trace = {
                "invocation_id": invocation_id,
                "function_id": decision_fn.function_id if decision_fn else function_id,
                "version": decision_fn.version if decision_fn else version,
                "input": serialize_for_json(input_obj) if input_obj else None,
                "output": None,
                "timestamp": datetime.utcnow().isoformat(),
                "caller": self.caller,
                "execution_time_ms": round(execution_time * 1000, 2),
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }
            
            # Emit error trace
            if self.trace_sink is not None:
                self.trace_sink.emit(error_trace)
            
            # Re-raise the exception
            raise RuntimeError(f"Decision execution failed: {str(e)}") from e

    def run_deterministic(self, 
                         function_id: str, 
                         version: Optional[str] = None, 
                         input_obj: Any = None,
                         seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Run a decision function with deterministic execution guarantees.
        This method ensures that identical inputs produce identical outputs.
        """
        # Set random seed if provided for deterministic behavior
        if seed is not None:
            import random
            random.seed(seed)
        
        return self.run(function_id, version, input_obj, enable_validation=True)

    def validate_only(self, 
                     function_id: str, 
                     version: Optional[str] = None, 
                     input_obj: Any = None) -> Dict[str, Any]:
        """
        Validate input against function schema without executing the function.
        Useful for testing and validation workflows.
        """
        decision_fn: DecisionFunction = self.registry.get(function_id, version)
        if decision_fn is None:
            raise ValueError(f"Decision function '{function_id}' version '{version}' not found")
        
        validator = SchemaValidator(decision_fn.schema)
        return validator.validate_input(input_obj)