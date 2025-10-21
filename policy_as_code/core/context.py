import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    OBJECT = "object"
    ARRAY = "array"
    ENUM = "enum"


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
    custom_validator: Optional[Callable[[Any], bool]] = None
    nested_schema: Optional[Dict[str, "SchemaField"]] = None


@dataclass
class DecisionSchema:
    input_schema: Dict[str, SchemaField]
    output_schema: Dict[str, SchemaField]
    version: str
    function_id: str
    description: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    policy_references: Optional[List[str]] = None
    compliance_requirements: Optional[List[str]] = None


class ValidationError(Exception):
    """Custom validation error for schema validation"""

    def __init__(
        self,
        message: str,
        field_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.field_path = field_path
        self.details = details or {}
        super().__init__(self.message)


class SchemaValidator:
    """Validates inputs and outputs against declared schemas"""

    def __init__(self, schema: DecisionSchema):
        self.schema = schema

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """Validate input against the declared input schema"""
        if isinstance(input_data, dict):
            data = input_data
        elif hasattr(input_data, "__dict__"):
            data = input_data.__dict__
        else:
            raise ValidationError("Input must be a dict or object with __dict__")

        validated = {}
        errors = []

        # Check required fields
        for field_name, field_spec in self.schema.input_schema.items():
            if field_name not in data:
                if field_spec.required:
                    errors.append(
                        ValidationError(
                            f"Required field '{field_name}' is missing",
                            field_path=field_name,
                        )
                    )
                elif field_spec.default is not None:
                    validated[field_name] = field_spec.default
                continue

            value = data[field_name]

            # Type validation
            try:
                validated_value = self._validate_field_type(
                    value, field_spec, field_name
                )
                validated[field_name] = validated_value
            except ValidationError as e:
                errors.append(e)

        if errors:
            # Aggregate all validation errors
            error_messages = [
                f"{e.field_path}: {e.message}" if e.field_path else e.message
                for e in errors
            ]
            raise ValidationError(
                f"Input validation failed: {'; '.join(error_messages)}",
                details={"errors": errors},
            )

        return validated

    def validate_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output against the declared output schema"""
        validated = {}
        errors = []

        for field_name, field_spec in self.schema.output_schema.items():
            if field_name not in output_data:
                if field_spec.required:
                    errors.append(
                        ValidationError(
                            f"Required output field '{field_name}' is missing",
                            field_path=field_name,
                        )
                    )
                elif field_spec.default is not None:
                    validated[field_name] = field_spec.default
                continue

            value = output_data[field_name]

            # Type validation
            try:
                validated_value = self._validate_field_type(
                    value, field_spec, field_name
                )
                validated[field_name] = validated_value
            except ValidationError as e:
                errors.append(e)

        if errors:
            error_messages = [
                f"{e.field_path}: {e.message}" if e.field_path else e.message
                for e in errors
            ]
            raise ValidationError(
                f"Output validation failed: {'; '.join(error_messages)}",
                details={"errors": errors},
            )

        return validated

    def _validate_field_type(
        self, value: Any, field_spec: SchemaField, field_path: str
    ) -> Any:
        """Validate a single field against its type specification"""

        # Handle None values
        if value is None:
            if field_spec.required:
                raise ValidationError("Field cannot be null", field_path=field_path)
            return field_spec.default

        # Type-specific validation
        if field_spec.type == FieldType.STRING:
            if not isinstance(value, str):
                raise ValidationError(
                    f"Expected string, got {type(value).__name__}",
                    field_path=field_path,
                )

            # Pattern validation
            if field_spec.pattern and not re.match(field_spec.pattern, value):
                raise ValidationError(
                    f"String does not match pattern: {field_spec.pattern}",
                    field_path=field_path,
                )

            # Length validation
            if field_spec.min_value is not None and len(value) < field_spec.min_value:
                raise ValidationError(
                    f"String too short (min: {field_spec.min_value})",
                    field_path=field_path,
                )
            if field_spec.max_value is not None and len(value) > field_spec.max_value:
                raise ValidationError(
                    f"String too long (max: {field_spec.max_value})",
                    field_path=field_path,
                )

        elif field_spec.type == FieldType.INTEGER:
            try:
                int_value = int(value)
                if (
                    field_spec.min_value is not None
                    and int_value < field_spec.min_value
                ):
                    raise ValidationError(
                        f"Value too small (min: {field_spec.min_value})",
                        field_path=field_path,
                    )
                if (
                    field_spec.max_value is not None
                    and int_value > field_spec.max_value
                ):
                    raise ValidationError(
                        f"Value too large (max: {field_spec.max_value})",
                        field_path=field_path,
                    )
                return int_value
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Expected integer, got {type(value).__name__}",
                    field_path=field_path,
                )

        elif field_spec.type == FieldType.FLOAT:
            try:
                float_value = float(value)
                if (
                    field_spec.min_value is not None
                    and float_value < field_spec.min_value
                ):
                    raise ValidationError(
                        f"Value too small (min: {field_spec.min_value})",
                        field_path=field_path,
                    )
                if (
                    field_spec.max_value is not None
                    and float_value > field_spec.max_value
                ):
                    raise ValidationError(
                        f"Value too large (max: {field_spec.max_value})",
                        field_path=field_path,
                    )
                return float_value
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Expected float, got {type(value).__name__}", field_path=field_path
                )

        elif field_spec.type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValidationError(
                    f"Expected boolean, got {type(value).__name__}",
                    field_path=field_path,
                )

        elif field_spec.type == FieldType.DATETIME:
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    raise ValidationError(
                        "Invalid datetime format", field_path=field_path
                    )
            elif not isinstance(value, datetime):
                raise ValidationError(
                    f"Expected datetime, got {type(value).__name__}",
                    field_path=field_path,
                )

        elif field_spec.type == FieldType.ENUM:
            if field_spec.enum_values and value not in field_spec.enum_values:
                raise ValidationError(
                    f"Value must be one of {field_spec.enum_values}",
                    field_path=field_path,
                )

        elif field_spec.type == FieldType.OBJECT:
            if not isinstance(value, dict):
                raise ValidationError(
                    f"Expected object, got {type(value).__name__}",
                    field_path=field_path,
                )

            # Validate nested schema if provided
            if field_spec.nested_schema:
                nested_validator = SchemaValidator(
                    DecisionSchema(
                        input_schema=field_spec.nested_schema,
                        output_schema={},
                        version=self.schema.version,
                        function_id=self.schema.function_id,
                    )
                )
                return nested_validator.validate_input(value)

        elif field_spec.type == FieldType.ARRAY:
            if not isinstance(value, list):
                raise ValidationError(
                    f"Expected array, got {type(value).__name__}", field_path=field_path
                )

            # Array length validation
            if field_spec.min_value is not None and len(value) < field_spec.min_value:
                raise ValidationError(
                    f"Array too short (min: {field_spec.min_value})",
                    field_path=field_path,
                )
            if field_spec.max_value is not None and len(value) > field_spec.max_value:
                raise ValidationError(
                    f"Array too long (max: {field_spec.max_value})",
                    field_path=field_path,
                )

        # Custom validation
        if field_spec.custom_validator and not field_spec.custom_validator(value):
            raise ValidationError("Custom validation failed", field_path=field_path)

        return value


def create_schema_from_dict(schema_dict: Dict[str, Any]) -> DecisionSchema:
    """Create a DecisionSchema from a dictionary definition"""

    def parse_field(field_name: str, field_def: Dict[str, Any]) -> SchemaField:
        return SchemaField(
            name=field_name,
            type=FieldType(field_def.get("type", "string")),
            required=field_def.get("required", True),
            description=field_def.get("description"),
            default=field_def.get("default"),
            enum_values=field_def.get("enum"),
            min_value=field_def.get("min"),
            max_value=field_def.get("max"),
            pattern=field_def.get("pattern"),
            nested_schema=field_def.get("nested_schema"),
        )

    input_schema = {
        name: parse_field(name, field_def)
        for name, field_def in schema_dict.get("input", {}).items()
    }

    output_schema = {
        name: parse_field(name, field_def)
        for name, field_def in schema_dict.get("output", {}).items()
    }

    return DecisionSchema(
        input_schema=input_schema,
        output_schema=output_schema,
        version=schema_dict.get("version", "1.0"),
        function_id=schema_dict.get("function_id", "unknown"),
        description=schema_dict.get("description"),
        author=schema_dict.get("author"),
        tags=schema_dict.get("tags", []),
        policy_references=schema_dict.get("policy_references", []),
        compliance_requirements=schema_dict.get("compliance_requirements", []),
    )
