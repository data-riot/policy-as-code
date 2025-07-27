# 🧠 decision-layer

Treat business logic like code.

---

## 👀 Why

Most companies still make decisions like it's 2005:
- `if` statements scattered across services
- Decision logic in a Notion doc
- Rules buried in dashboards
- No way to test, version, or trace any of it

---

## ✅ What this is

A minimal decision engine that gives you:

- 🧪 Testable decisions
- 🔁 Versioned logic
- 📜 Logged traces
- 🧠 DSL you can read and change
- 🔒 Schema validation
- 👻 Shadow running for safe testing
- 📊 Regression analysis
- 🏷️ Function tagging and search

---

## ✨ Try it now

### Basic Usage

```bash
git clone https://github.com/data-riot/decision-layer
cd decision-layer

# Install dependencies
pip install -r requirements.txt

# For development (includes testing tools)
pip install -r requirements-dev.txt

# Run a basic decision
python -m decision_layer.cli run \
  --policy policies/refund_policy.yaml \
  --input tests/data/sample_order.json
```

### Usage with Schema Validation

```bash
# Run with schema validation
python -m decision_layer.cli run \
  --policy policies/refund_policy.yaml \
  --input tests/data/sample_order.json \
  --use-schema \
  --function-id refund_policy \
  --description "Refund policy with validation" \
  --author "team-finance" \
  --tags "refund,finance,validation"
```

### Shadow Testing

```bash
# Test logic against current version
python -m decision_layer.cli shadow \
  --current-policy policies/refund_policy.yaml \
  --shadow-policy policies/refund_policy.yaml \
  --inputs tests/data/test_inputs.json \
  --mode simulation \
  --use-schema
```

### Function Management

```bash
# List all registered functions
python -m decision_layer.cli list --policy-dir policies

# Validate input against schema
python -m decision_layer.cli validate \
  --policy policies/refund_policy.yaml \
  --input tests/data/sample_order.json
```

---

## 🧠 Define a policy

### Basic Policy (Backward Compatible)

```yaml
# refund_policy.yaml
function: refund_policy
version: v3.2
rules:
  - id: late
    if: { field: "is_late", operator: "==", value: true }
    then: { refund: 100, reason: "Late delivery" }

  - id: damaged
    if: { field: "issue", operator: "==", value: "damaged" }
    then: { refund: 50, reason: "Damaged item" }

default:
  refund: 0
  reason: "Not eligible"
```

### Policy with Schema Validation

```yaml
# refund_policy.yaml
function: refund_policy
version: v3.2
description: "Determine refund amount for customer orders with comprehensive validation"

input_schema:
  id:
    type: string
    required: true
    description: "Order ID"
    pattern: "^[A-Z0-9]+$"
  
  issue:
    type: string
    required: true
    enum: ["late", "damaged", "wrong_item", "none"]
    description: "Issue type"
  
  customer:
    type: object
    required: true
    description: "Customer information"
    properties:
      id:
        type: string
        required: true
      status:
        type: string
        required: true
        enum: ["bronze", "silver", "gold", "platinum"]

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

rules:
  - id: late_delivery
    if: { field: "issue", operator: "==", value: "late" }
    then: 
      refund: 100
      reason: "Late delivery"

default:
  refund: 0
  reason: "Not eligible for refund"
```

---

## 🔍 Output trace format

```json
{
  "invocation_id": "550e8400-e29b-41d4-a716-446655440000",
  "function_id": "refund_policy",
  "version": "v3.2",
  "input": { "id": "A1", "customer": { "id": "123", "signup_date": "2023-01-01T00:00:00", "status": "gold" }, "order_date": "2024-06-01T00:00:00", "delivery_date": "2024-06-05T00:00:00", "issue": "late" },
  "output": { "refund": 100, "reason": "Late delivery" },
  "input_hash": "0x4f...",
  "output_hash": "0xe9...",
  "timestamp": "2025-07-27T14:23:51Z",
  "caller": "cli",
  "execution_time_ms": 12.5,
  "status": "success",
  "schema_validated": true
}
```

---

## 🚀 API Usage

### Start the API Server

```bash
uvicorn api.fastapi_app:app --reload
```

### API Endpoints

```bash
# List all functions
curl http://localhost:8000/functions

# Get function schema
curl http://localhost:8000/functions/refund_policy/schema

# Execute decision
curl -X POST http://localhost:8000/decide/refund_policy \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "id": "A1",
      "customer": {
        "id": "123",
        "signup_date": "2023-01-01T00:00:00",
        "status": "gold"
      },
      "order_date": "2024-06-01T00:00:00",
      "delivery_date": "2024-06-05T00:00:00",
      "issue": "late"
    },
    "version": "v3.2",
    "enable_validation": true
  }'

# Shadow testing
curl -X POST http://localhost:8000/shadow/refund_policy \
  -H "Content-Type: application/json" \
  -d '{
    "input": { ... },
    "current_version": "v3.2",
    "shadow_version": "v3.2"
  }'

# Validate input
curl -X POST http://localhost:8000/validate/refund_policy \
  -H "Content-Type: application/json" \
  -d '{
    "input": { ... },
    "version": "v3.2"
  }'
```

---

## 💡 Use cases

- **Refunds**: Automated refund decisions with customer tier bonuses
- **Risk holds**: Transaction risk assessment with configurable thresholds
- **Support escalation**: Customer service routing based on issue type and customer value
- **Account flags**: Fraud detection and account suspension logic
- **Access control**: Permission management with role-based rules
- **Pricing**: Dynamic pricing based on customer segments and market conditions

---

## 🧱 Project structure

```
decision_layer/
  cli.py              # CLI with multiple commands
  executor.py         # Execution engine
  registry.py         # Function registry
  trace_sink.py       # Trace logging infrastructure
  schemas.py          # Schema validation system
  shadow_runner.py    # Shadow testing
  dsl_loader.py       # YAML policy loader
  entities.py         # Domain entities

api/
  fastapi_app.py      # REST API

policies/
  refund_policy.yaml  # Sample policy

tests/
  test_features.py    # Test suite
  data/
    sample_order.json # Sample test input
    test_inputs.json  # Test inputs for shadow testing
```

---

## 🔧 CLI Commands

### `run` - Execute a decision
```bash
python -m decision_layer.cli run \
  --policy <policy-file> \
  --input <input-file> \
  [--output <output-file>] \
  [--version <version>] \
  [--function-id <id>] \
  [--description <desc>] \
  [--author <author>] \
  [--tags <tags>] \
  [--trace <trace-file>] \
  [--use-schema]
```

### `shadow` - Shadow testing
```bash
python -m decision_layer.cli shadow \
  --current-policy <current-policy> \
  --shadow-policy <shadow-policy> \
  --inputs <input-files...> \
  [--current-version <version>] \
  [--shadow-version <version>] \
  [--mode simulation|mirror] \
  [--trace <trace-file>] \
  [--report <report-file>] \
  [--use-schema]
```

### `list` - List functions
```bash
python -m decision_layer.cli list \
  [--policy-dir <directory>] \
  [--use-schema]
```

### `validate` - Validate input
```bash
python -m decision_layer.cli validate \
  --policy <policy-file> \
  --input <input-file>
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_features.py

# Run with coverage
pytest --cov=decision_layer
```

---

## 🔒 Schema Validation

The decision layer supports comprehensive schema validation:

- **Input validation**: Ensures all required fields are present and have correct types
- **Output validation**: Validates decision outputs against declared schemas
- **Type constraints**: Supports strings, integers, floats, booleans, dates, objects, and arrays
- **Value constraints**: Min/max values, enums, patterns, and custom validation
- **Backward compatibility**: Existing policies work without schema definitions

---

## 👻 Shadow Running

Shadow running allows safe testing of decision logic:

- **Simulation mode**: Test logic against historical inputs
- **Mirror mode**: Run both versions in parallel on live traffic
- **Regression analysis**: Categorize differences as critical, warning, or improvement
- **Diff reporting**: Detailed analysis of what changed and why

---

## 📊 Version Management

- **Immutable versions**: Each function version is stored immutably
- **Semantic versioning**: Support for semantic versioning (v1.2.3) and simple versions (v3.2)
- **Latest tracking**: Automatic tracking of latest stable versions
- **Version comparison**: Built-in version comparison and ordering
- **Rollback support**: Easy rollback to any previous version

---

## 🏷️ Function Metadata

Functions can be tagged and searched:

- **Tags**: Categorize functions (e.g., "refund", "finance", "validation")
- **Authors**: Track who created each function
- **Descriptions**: Document function purpose and behavior
- **Search**: Find functions by tags, authors, or other criteria

---

## ⚠️ Migration Guide

### From v1.x to v2.x

1. **Existing policies continue to work** without changes
2. **Add schema definitions** to existing policies for validation
3. **Use CLI commands** for advanced features
4. **Update API calls** to use endpoint structure

### Example Migration

```yaml
# Old format (still works)
function: refund_policy
version: v3.2
rules: [...]

# Current format (recommended)
function: refund_policy
version: v3.2
description: "Refund policy"
input_schema: [...]
output_schema: [...]
rules: [...]
```

---

## 🪪 License

MIT

---

## 🔗 Roadmap

- [x] Schema validation
- [x] Shadow running
- [x] CLI
- [x] Function metadata
- [x] Regression analysis
- [ ] Web UI for browsing decisions
- [ ] Policy composition (multi-function chains)
- [ ] Template support for regional variations
- [ ] LLM integration for logic generation
- [ ] Counterfactual analysis tools

---

## 🙋‍♂️ Questions?

Open an issue, submit a policy or fork it into your stack.
