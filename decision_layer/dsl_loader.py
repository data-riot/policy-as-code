import yaml
from typing import Dict, Any, Callable
from .executor import resolve_field
from .schemas import DecisionSchema, SchemaField, FieldType

def load_yaml_policy(path: str) -> Callable:
    """Load a YAML policy and return a decision function"""
    with open(path) as f:
        data = yaml.safe_load(f)

    rules = data.get("rules", [])
    default = data.get("default", {})
    function_id = data.get("function", "unknown")
    version = data.get("version", "v1.0")

    def decision_fn(obj):
        for rule in rules:
            cond = rule["if"]
            actual_value = resolve_field(obj, cond["field"])
            if actual_value == cond["value"]:
                result = rule["then"].copy()
                result["rule_id"] = rule["id"]
                return result
        return default

    return decision_fn

def load_yaml_policy_with_schema(path: str) -> tuple[Callable, DecisionSchema]:
    """
    Load a YAML policy with schema definition and return both the function and schema.
    
    Expected YAML format:
    function: refund_policy
    version: v3.2
    description: "Determine refund amount for customer orders"
    
    input_schema:
      id:
        type: string
        required: true
        description: "Order ID"
      issue:
        type: string
        required: true
        enum: ["late", "damaged", "wrong_item", "none"]
        description: "Issue type"
      customer:
        type: object
        required: true
        properties:
          id:
            type: string
          status:
            type: string
            enum: ["bronze", "silver", "gold"]
    
    output_schema:
      refund:
        type: integer
        required: true
        min_value: 0
        max_value: 1000
        description: "Refund amount in cents"
      reason:
        type: string
        required: true
        description: "Reason for refund decision"
      rule_id:
        type: string
        required: false
        description: "ID of the rule that matched"
    
    rules:
      - id: late
        if: { field: "is_late", operator: "==", value: true }
        then: { refund: 100, reason: "Late delivery" }
    
    default:
      refund: 0
      reason: "Not eligible"
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    # Extract schema information
    function_id = data.get("function", "unknown")
    version = data.get("version", "v1.0")
    description = data.get("description", "")
    
    # Parse input schema
    input_schema = _parse_schema_fields(data.get("input_schema", {}))
    
    # Parse output schema
    output_schema = _parse_schema_fields(data.get("output_schema", {}))
    
    # Create decision schema
    schema = DecisionSchema(
        input_schema=input_schema,
        output_schema=output_schema,
        version=version,
        function_id=function_id,
        description=description
    )
    
    # Create decision function
    rules = data.get("rules", [])
    default = data.get("default", {})
    
    def decision_fn(obj):
        for rule in rules:
            cond = rule["if"]
            actual_value = resolve_field(obj, cond["field"])
            if actual_value == cond["value"]:
                result = rule["then"].copy()
                result["rule_id"] = rule["id"]
                return result
        return default
    
    return decision_fn, schema

def _parse_schema_fields(schema_data: Dict[str, Any]) -> Dict[str, SchemaField]:
    """Parse schema fields from YAML data"""
    fields = {}
    
    for field_name, field_data in schema_data.items():
        if isinstance(field_data, dict):
            # Complex field definition
            field_type = _parse_field_type(field_data.get("type", "string"))
            
            field = SchemaField(
                name=field_name,
                type=field_type,
                required=field_data.get("required", True),
                description=field_data.get("description"),
                default=field_data.get("default"),
                enum_values=field_data.get("enum"),
                min_value=field_data.get("min_value"),
                max_value=field_data.get("max_value"),
                pattern=field_data.get("pattern")
            )
        else:
            # Simple field definition - just type
            field_type = _parse_field_type(field_data)
            field = SchemaField(
                name=field_name,
                type=field_type,
                required=True
            )
        
        fields[field_name] = field
    
    return fields

def _parse_field_type(type_str: str) -> FieldType:
    """Parse field type string to FieldType enum"""
    type_mapping = {
        "string": FieldType.STRING,
        "integer": FieldType.INTEGER,
        "int": FieldType.INTEGER,
        "float": FieldType.FLOAT,
        "number": FieldType.FLOAT,
        "boolean": FieldType.BOOLEAN,
        "bool": FieldType.BOOLEAN,
        "datetime": FieldType.DATETIME,
        "date": FieldType.DATETIME,
        "object": FieldType.OBJECT,
        "array": FieldType.ARRAY,
        "list": FieldType.ARRAY
    }
    
    return type_mapping.get(type_str.lower(), FieldType.STRING)

def create_schema_from_example(input_example: Dict[str, Any], 
                             output_example: Dict[str, Any],
                             function_id: str = "unknown",
                             version: str = "v1.0") -> DecisionSchema:
    """
    Create a schema by inferring types from example data.
    This is useful for backward compatibility with existing policies.
    """
    input_schema = {}
    for field_name, value in input_example.items():
        field_type = _infer_type_from_value(value)
        input_schema[field_name] = SchemaField(
            name=field_name,
            type=field_type,
            required=True
        )
    
    output_schema = {}
    for field_name, value in output_example.items():
        field_type = _infer_type_from_value(value)
        output_schema[field_name] = SchemaField(
            name=field_name,
            type=field_type,
            required=True
        )
    
    return DecisionSchema(
        input_schema=input_schema,
        output_schema=output_schema,
        version=version,
        function_id=function_id
    )

def _infer_type_from_value(value: Any) -> FieldType:
    """Infer FieldType from a Python value"""
    if isinstance(value, str):
        return FieldType.STRING
    elif isinstance(value, int):
        return FieldType.INTEGER
    elif isinstance(value, float):
        return FieldType.FLOAT
    elif isinstance(value, bool):
        return FieldType.BOOLEAN
    elif isinstance(value, dict):
        return FieldType.OBJECT
    elif isinstance(value, (list, tuple)):
        return FieldType.ARRAY
    else:
        return FieldType.STRING