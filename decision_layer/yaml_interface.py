"""
YAML-based Decision Interface for Data Governance

This module provides a simple YAML-based interface for defining decision logic
without requiring Python programming knowledge.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from .core import DecisionFunction, DecisionContext
from .schemas import DecisionSchema, SchemaField, FieldType
from .errors import ValidationError


class YAMLDecisionParser:
    """Parser for YAML-based decision definitions"""

    def __init__(self):
        self.supported_operators = {
            "equals": lambda x, y: x == y,
            "not_equals": lambda x, y: x != y,
            "greater_than": lambda x, y: x > y,
            "less_than": lambda x, y: x < y,
            "greater_equal": lambda x, y: x >= y,
            "less_equal": lambda x, y: x <= y,
            "in": lambda x, y: x in y,
            "not_in": lambda x, y: x not in y,
            "contains": lambda x, y: y in x if isinstance(x, str) else x in y,
            "starts_with": lambda x, y: str(x).startswith(str(y)),
            "ends_with": lambda x, y: str(x).endswith(str(y)),
            "is_empty": lambda x: not x or (isinstance(x, str) and not x.strip()),
            "is_not_empty": lambda x: x and (not isinstance(x, str) or x.strip()),
        }

    def parse_condition(
        self, condition: Dict[str, Any], input_data: Dict[str, Any]
    ) -> bool:
        """Parse and evaluate a condition"""
        if "field" not in condition or "operator" not in condition:
            raise ValidationError("Condition must have 'field' and 'operator'")

        field = condition["field"]
        operator = condition["operator"]
        value = condition.get("value")

        if operator not in self.supported_operators:
            raise ValidationError(f"Unsupported operator: {operator}")

        field_value = input_data.get(field)

        if operator in ["is_empty", "is_not_empty"]:
            return self.supported_operators[operator](field_value)
        else:
            if "value" not in condition:
                raise ValidationError(f"Operator '{operator}' requires a 'value'")

            # Handle None values gracefully
            if field_value is None:
                if operator in ["equals", "is_empty"]:
                    return value is None
                elif operator in ["not_equals", "is_not_empty"]:
                    return value is not None
                else:
                    return False  # None values fail other comparisons

            return self.supported_operators[operator](field_value, value)

    def parse_rule(self, rule: Dict[str, Any], input_data: Dict[str, Any]) -> bool:
        """Parse and evaluate a rule (can have multiple conditions with AND/OR logic)"""
        if "conditions" not in rule:
            raise ValidationError("Rule must have 'conditions'")

        conditions = rule["conditions"]
        logic = rule.get("logic", "AND")  # Default to AND

        if not isinstance(conditions, list):
            conditions = [conditions]

        results = [self.parse_condition(cond, input_data) for cond in conditions]

        if logic.upper() == "AND":
            return all(results)
        elif logic.upper() == "OR":
            return any(results)
        else:
            raise ValidationError(f"Unsupported logic: {logic}")

    def evaluate_rules(
        self, rules: List[Dict[str, Any]], input_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Evaluate a list of rules and return the first matching result"""
        for rule in rules:
            if self.parse_rule(rule, input_data):
                return rule.get("result", {})
        return None

    def create_decision_function(self, yaml_content: str) -> DecisionFunction:
        """Create a DecisionFunction from YAML content"""
        try:
            config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML: {e}")

        if "name" not in config:
            raise ValidationError("Decision must have a 'name'")

        if "rules" not in config:
            raise ValidationError("Decision must have 'rules'")

        def decision_function(
            input_data: Dict[str, Any], context: DecisionContext
        ) -> Dict[str, Any]:
            """Generated decision function from YAML"""
            try:
                result = self.evaluate_rules(config["rules"], input_data)
                if result is None:
                    # Return default result if no rules match
                    return config.get(
                        "default_result",
                        {"approved": False, "reason": "No matching rules found"},
                    )
                return result
            except Exception as e:
                return {
                    "error": True,
                    "message": str(e),
                    "approved": False,
                    "reason": f"Decision evaluation failed: {e}",
                }

        return decision_function

    def create_schema_from_yaml(self, yaml_content: str) -> DecisionSchema:
        """Create a DecisionSchema from YAML content"""
        try:
            config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML: {e}")

        if "input_fields" not in config:
            raise ValidationError("Decision must have 'input_fields'")

        fields = []
        for field_name, field_config in config["input_fields"].items():
            field_type = field_config.get("type", "string")
            required = field_config.get("required", False)
            description = field_config.get("description", "")

            fields.append(
                SchemaField(
                    name=field_name,
                    field_type=FieldType(field_type),
                    required=required,
                    description=description,
                )
            )

        return DecisionSchema(fields=fields)


def load_decision_from_yaml(yaml_path: Union[str, Path]) -> DecisionFunction:
    """Load a decision function from a YAML file"""
    yaml_path = Path(yaml_path)
    if not yaml_path.exists():
        raise ValidationError(f"YAML file not found: {yaml_path}")

    with open(yaml_path, "r") as f:
        yaml_content = f.read()

    parser = YAMLDecisionParser()
    return parser.create_decision_function(yaml_content)


def create_yaml_template() -> str:
    """Create a template YAML file for decision definitions"""
    return """# Decision Layer YAML Template
# This template shows how to define decision logic without writing Python code

name: "approval_decision"
description: "Example approval decision based on amount and customer score"

# Define input fields and their types
input_fields:
  amount:
    type: "number"
    required: true
    description: "Requested amount"

  customer_score:
    type: "number"
    required: true
    description: "Customer credit score"

  customer_tier:
    type: "string"
    required: false
    description: "Customer tier (standard, premium, vip)"
    default: "standard"

  location:
    type: "string"
    required: false
    description: "Customer location"

# Define decision rules (evaluated in order)
rules:
  # Rule 1: High amount with low score
  - name: "high_amount_low_score"
    description: "Reject high amounts for low credit scores"
    conditions:
      - field: "amount"
        operator: "greater_than"
        value: 10000
      - field: "customer_score"
        operator: "less_than"
        value: 600
    logic: "AND"
    result:
      approved: false
      reason: "Amount too high for credit score"
      max_allowed: 5000

  # Rule 2: Standard tier limits
  - name: "standard_tier_limits"
    description: "Apply limits for standard tier customers"
    conditions:
      - field: "customer_tier"
        operator: "equals"
        value: "standard"
      - field: "amount"
        operator: "greater_than"
        value: 5000
    logic: "AND"
    result:
      approved: false
      reason: "Amount exceeds standard tier limit"
      max_allowed: 5000

  # Rule 3: Premium tier with good score
  - name: "premium_good_score"
    description: "Approve premium customers with good scores"
    conditions:
      - field: "customer_tier"
        operator: "equals"
        value: "premium"
      - field: "customer_score"
        operator: "greater_equal"
        value: 700
    logic: "AND"
    result:
      approved: true
      reason: "Premium customer with good credit score"
      limit: 25000

  # Rule 4: VIP customers
  - name: "vip_customers"
    description: "Approve VIP customers with higher limits"
    conditions:
      - field: "customer_tier"
        operator: "equals"
        value: "vip"
    result:
      approved: true
      reason: "VIP customer approved"
      limit: 50000

# Default result if no rules match
default_result:
  approved: false
  reason: "Decision criteria not met"
  limit: 0

# Metadata
metadata:
  version: "1.0"
  author: "Data Governance Team"
  created_date: "2025-08-01"
  tags: ["approval", "credit", "risk"]
"""


def validate_yaml_decision(yaml_content: str) -> Dict[str, Any]:
    """Validate a YAML decision definition and return validation results"""
    validation_result = {"valid": True, "errors": [], "warnings": [], "info": {}}

    try:
        config = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        validation_result["valid"] = False
        validation_result["errors"].append(f"YAML syntax error: {e}")
        return validation_result

    # Check required fields
    required_fields = ["name", "rules"]
    for field in required_fields:
        if field not in config:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Missing required field: {field}")

    # Validate rules
    if "rules" in config:
        parser = YAMLDecisionParser()
        for i, rule in enumerate(config["rules"]):
            try:
                if "conditions" not in rule:
                    validation_result["errors"].append(
                        f"Rule {i+1}: Missing 'conditions'"
                    )
                else:
                    conditions = rule["conditions"]
                    if not isinstance(conditions, list):
                        conditions = [conditions]

                    for j, condition in enumerate(conditions):
                        if "field" not in condition:
                            validation_result["errors"].append(
                                f"Rule {i+1}, Condition {j+1}: Missing 'field'"
                            )
                        if "operator" not in condition:
                            validation_result["errors"].append(
                                f"Rule {i+1}, Condition {j+1}: Missing 'operator'"
                            )
                        elif condition["operator"] not in parser.supported_operators:
                            validation_result["warnings"].append(
                                f"Rule {i+1}, Condition {j+1}: Unknown operator '{condition['operator']}'"
                            )
            except Exception as e:
                validation_result["errors"].append(f"Rule {i+1}: {e}")

    # Check for common issues
    if "input_fields" in config:
        validation_result["info"]["input_fields"] = list(config["input_fields"].keys())

    if "rules" in config:
        validation_result["info"]["rule_count"] = len(config["rules"])

    return validation_result
