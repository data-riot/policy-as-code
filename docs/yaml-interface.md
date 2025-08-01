# YAML Decision Interface

The YAML Decision Interface allows data governance teams to define business decision logic using simple YAML files instead of writing Python code. This makes it easy for business analysts and data governance professionals to create, maintain, and version control decision rules.

## Overview

Instead of writing Python functions, you can define decision logic in YAML format with:
- **Input field definitions** with types and validation
- **Business rules** with conditions and results
- **Metadata** for tracking and compliance

## Quick Start

### 1. Create a YAML Decision File

```yaml
name: "loan_approval_decision"
description: "Loan approval decision based on customer profile"

input_fields:
  amount:
    type: "number"
    required: true
    description: "Requested loan amount"

  customer_score:
    type: "number"
    required: true
    description: "Customer credit score"

rules:
  - name: "high_risk_rejection"
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

default_result:
  approved: false
  reason: "Decision criteria not met"
```

### 2. Load and Use the Decision

```python
from decision_layer import load_decision_from_yaml

# Load the decision function
decision_function = load_decision_from_yaml("loan_approval.yaml")

# Test with input data
input_data = {
    "amount": 15000,
    "customer_score": 550
}

result = decision_function(input_data, context)
print(result)
# Output: {"approved": false, "reason": "Amount too high for credit score"}
```

## YAML Structure

### Required Fields

- **`name`**: Unique identifier for the decision
- **`rules`**: List of business rules to evaluate

### Optional Fields

- **`description`**: Human-readable description
- **`input_fields`**: Field definitions for validation
- **`default_result`**: Result when no rules match
- **`metadata`**: Additional information (version, author, etc.)

## Input Fields

Define the expected input data structure:

```yaml
input_fields:
  field_name:
    type: "string|number|boolean"
    required: true|false
    description: "Field description"
    default: "default_value"  # Optional
```

### Supported Types

- **`string`**: Text values
- **`number`**: Numeric values (integers and floats)
- **`boolean`**: True/false values

## Business Rules

Rules are evaluated in order. The first matching rule determines the result.

### Rule Structure

```yaml
rules:
  - name: "rule_name"
    description: "Rule description"
    conditions:
      - field: "field_name"
        operator: "operator_name"
        value: "comparison_value"
    logic: "AND|OR"  # Default: AND
    result:
      # Your result data here
      approved: true
      reason: "Approval reason"
```

### Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `equals` | Field equals value | `customer_tier: "premium"` |
| `not_equals` | Field not equals value | `status: "rejected"` |
| `greater_than` | Field greater than value | `amount: 10000` |
| `less_than` | Field less than value | `score: 600` |
| `greater_equal` | Field greater than or equal | `age: 18` |
| `less_equal` | Field less than or equal | `amount: 5000` |
| `in` | Field in list | `region: ["US", "CA"]` |
| `not_in` | Field not in list | `status: ["pending"]` |
| `contains` | Field contains substring | `description: "urgent"` |
| `starts_with` | Field starts with | `email: "admin@"` |
| `ends_with` | Field ends with | `file: ".pdf"` |
| `is_empty` | Field is empty/null | `notes: null` |
| `is_not_empty` | Field is not empty | `phone: "required"` |

### Multiple Conditions

Use multiple conditions with AND/OR logic:

```yaml
conditions:
  - field: "amount"
    operator: "greater_than"
    value: 10000
  - field: "customer_score"
    operator: "less_than"
    value: 600
logic: "AND"  # Both conditions must be true
```

## Examples

### Loan Approval Decision

```yaml
name: "loan_approval"
description: "Automated loan approval decision"

input_fields:
  amount:
    type: "number"
    required: true
    description: "Requested loan amount"

  customer_score:
    type: "number"
    required: true
    description: "Credit score (300-850)"

  customer_tier:
    type: "string"
    required: false
    default: "standard"
    description: "Customer tier"

rules:
  # Reject low credit scores
  - name: "minimum_score"
    conditions:
      - field: "customer_score"
        operator: "less_than"
        value: 500
    result:
      approved: false
      reason: "Credit score too low"
      max_amount: 0

  # Premium customers get higher limits
  - name: "premium_customers"
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
      reason: "Premium customer approved"
      max_amount: 50000

  # Standard tier limits
  - name: "standard_limits"
    conditions:
      - field: "customer_tier"
        operator: "equals"
        value: "standard"
      - field: "amount"
        operator: "less_equal"
        value: 10000
    logic: "AND"
    result:
      approved: true
      reason: "Standard tier approved"
      max_amount: 10000

default_result:
  approved: false
  reason: "Decision criteria not met"
  max_amount: 0
```

### Risk Assessment Decision

```yaml
name: "risk_assessment"
description: "Customer risk assessment"

input_fields:
  transaction_amount:
    type: "number"
    required: true
    description: "Transaction amount"

  customer_age:
    type: "number"
    required: true
    description: "Customer age"

  location:
    type: "string"
    required: false
    description: "Transaction location"

rules:
  # High-risk locations
  - name: "high_risk_locations"
    conditions:
      - field: "location"
        operator: "in"
        value: ["restricted_region_1", "restricted_region_2"]
    result:
      risk_level: "high"
      action: "block"
      reason: "High-risk location"

  # Large amounts for young customers
  - name: "large_amount_young_customer"
    conditions:
      - field: "transaction_amount"
        operator: "greater_than"
        value: 5000
      - field: "customer_age"
        operator: "less_than"
        value: 25
    logic: "AND"
    result:
      risk_level: "medium"
      action: "review"
      reason: "Large amount for young customer"

  # Normal transactions
  - name: "normal_transaction"
    conditions:
      - field: "transaction_amount"
        operator: "less_equal"
        value: 1000
    result:
      risk_level: "low"
      action: "approve"
      reason: "Normal transaction amount"

default_result:
  risk_level: "medium"
  action: "review"
  reason: "Requires manual review"
```

## Validation

Validate your YAML decision files:

```python
from decision_layer import validate_yaml_decision

with open("decision.yaml", "r") as f:
    yaml_content = f.read()

validation = validate_yaml_decision(yaml_content)

if validation['valid']:
    print("✅ YAML is valid")
else:
    print("❌ Validation errors:")
    for error in validation['errors']:
        print(f"   - {error}")
```

## Best Practices

### 1. Rule Order
- Place the most restrictive rules first
- Use specific conditions before general ones
- Always have a `default_result`

### 2. Field Definitions
- Define all expected input fields
- Use descriptive field names
- Set appropriate required/optional flags

### 3. Rule Naming
- Use descriptive rule names
- Include rule descriptions
- Group related rules together

### 4. Testing
- Test with various input combinations
- Include edge cases (null values, boundaries)
- Validate rule logic thoroughly

### 5. Documentation
- Add comprehensive descriptions
- Include business context
- Document rule dependencies

## Integration with Decision Layer

YAML decisions integrate seamlessly with the Decision Layer framework:

```python
from decision_layer import (
    load_decision_from_yaml,
    DecisionEngine,
    create_decision_engine
)

# Load YAML decision
decision_function = load_decision_from_yaml("business_rules.yaml")

# Use with Decision Engine
engine = create_decision_engine()
result = await engine.execute("yaml_decision", input_data)
```

## Benefits for Data Governance Teams

1. **No Programming Required**: Define rules in business-friendly YAML
2. **Version Control**: Track changes to business rules over time
3. **Audit Trail**: Maintain compliance and audit requirements
4. **Collaboration**: Business and technical teams can work together
5. **Testing**: Easy to test and validate rule changes
6. **Documentation**: Self-documenting rule definitions

## Migration from Python Functions

To migrate existing Python decision functions to YAML:

1. **Analyze the function**: Identify conditions and logic
2. **Map to YAML structure**: Convert to rules and conditions
3. **Test thoroughly**: Ensure same behavior
4. **Deploy gradually**: Use shadow testing to compare results

This approach makes decision logic accessible to data governance professionals while maintaining the power and flexibility of the Decision Layer framework.
