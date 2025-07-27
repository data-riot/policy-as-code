from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
from enum import Enum

class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    OBJECT = "object"
    ARRAY = "array"

@dataclass
class SchemaField:
    name: str
    type: FieldType
    required: bool = True
    description: Optional[str] = None
    default: Optional[Any] = None
    enum_values: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None

@dataclass
class DecisionSchema:
    input_schema: Dict[str, SchemaField]
    output_schema: Dict[str, SchemaField]
    version: str
    function_id: str
    description: Optional[str] = None

class ValidationError(Exception):
    """Custom validation error for schema validation"""
    pass

class SchemaValidator:
    """Validates inputs and outputs against declared schemas"""
    
    def __init__(self, schema: DecisionSchema):
        self.schema = schema
    
    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """Validate input against the declared input schema"""
        if isinstance(input_data, dict):
            data = input_data
        elif hasattr(input_data, '__dict__'):
            data = input_data.__dict__
        else:
            raise ValueError("Input must be a dict or object with __dict__")
        
        validated = {}
        errors = []
        
        # Check required fields
        for field_name, field_spec in self.schema.input_schema.items():
            if field_name not in data:
                if field_spec.required:
                    errors.append(f"Required field '{field_name}' is missing")
                elif field_spec.default is not None:
                    validated[field_name] = field_spec.default
                continue
            
            value = data[field_name]
            
            # Type validation
            try:
                validated_value = self._validate_field_type(value, field_spec)
                validated[field_name] = validated_value
            except ValueError as e:
                errors.append(f"Field '{field_name}': {str(e)}")
        
        if errors:
            raise ValidationError(f"Input validation failed: {'; '.join(errors)}")
        
        return validated
    
    def validate_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output against the declared output schema"""
        validated = {}
        errors = []
        
        for field_name, field_spec in self.schema.output_schema.items():
            if field_name not in output_data:
                if field_spec.required:
                    errors.append(f"Required output field '{field_name}' is missing")
                elif field_spec.default is not None:
                    validated[field_name] = field_spec.default
                continue
            
            value = output_data[field_name]
            
            try:
                validated_value = self._validate_field_type(value, field_spec)
                validated[field_name] = validated_value
            except ValueError as e:
                errors.append(f"Output field '{field_name}': {str(e)}")
        
        if errors:
            raise ValidationError(f"Output validation failed: {'; '.join(errors)}")
        
        return validated
    
    def _validate_field_type(self, value: Any, field_spec: SchemaField) -> Any:
        """Validate a single field against its type specification"""
        if value is None and not field_spec.required:
            return field_spec.default
        
        if field_spec.enum_values and value not in field_spec.enum_values:
            raise ValueError(f"Value '{value}' not in allowed values: {field_spec.enum_values}")
        
        if field_spec.type == FieldType.STRING:
            if not isinstance(value, str):
                raise ValueError(f"Expected string, got {type(value).__name__}")
            if field_spec.pattern and not re.match(field_spec.pattern, value):
                raise ValueError(f"String does not match pattern: {field_spec.pattern}")
        
        elif field_spec.type == FieldType.INTEGER:
            try:
                int_value = int(value)
                if field_spec.min_value is not None and int_value < field_spec.min_value:
                    raise ValueError(f"Value {int_value} is less than minimum {field_spec.min_value}")
                if field_spec.max_value is not None and int_value > field_spec.max_value:
                    raise ValueError(f"Value {int_value} is greater than maximum {field_spec.max_value}")
                return int_value
            except (ValueError, TypeError):
                raise ValueError(f"Expected integer, got {type(value).__name__}")
        
        elif field_spec.type == FieldType.FLOAT:
            try:
                float_value = float(value)
                if field_spec.min_value is not None and float_value < field_spec.min_value:
                    raise ValueError(f"Value {float_value} is less than minimum {field_spec.min_value}")
                if field_spec.max_value is not None and float_value > field_spec.max_value:
                    raise ValueError(f"Value {float_value} is greater than maximum {field_spec.max_value}")
                return float_value
            except (ValueError, TypeError):
                raise ValueError(f"Expected float, got {type(value).__name__}")
        
        elif field_spec.type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValueError(f"Expected boolean, got {type(value).__name__}")
        
        elif field_spec.type == FieldType.DATETIME:
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value)
                except ValueError:
                    raise ValueError(f"Invalid datetime format: {value}")
            elif not isinstance(value, datetime):
                raise ValueError(f"Expected datetime, got {type(value).__name__}")
        
        elif field_spec.type == FieldType.OBJECT:
            # Handle both dict and objects with __dict__
            if isinstance(value, dict):
                return value
            elif hasattr(value, '__dict__'):
                return value.__dict__
            else:
                raise ValueError(f"Expected object, got {type(value).__name__}")
        
        elif field_spec.type == FieldType.ARRAY:
            if not isinstance(value, (list, tuple)):
                raise ValueError(f"Expected array, got {type(value).__name__}")
        
        return value 