# CLI Reference

The Decision Layer provides a comprehensive command-line interface for managing decision functions, executing decisions, and viewing traces.

## Installation

The CLI is automatically installed when you install the Decision Layer package:

```bash
pip install -e .
```

## Basic Usage

```bash
# Get help
decision-layer --help

# Get help for a specific command
decision-layer execute --help
```

## Commands Overview

### Core Commands

- `init` - Initialize the Decision Layer system
- `deploy` - Deploy a decision function
- `execute` - Execute a decision function
- `list` - List all functions
- `traces` - View execution traces
- `info` - Get function information
- `test` - Test a function with validation

### Management Commands

- `clear` - Clear traces and cache
- `config` - Manage configuration
- `status` - Check system status

## Command Reference

### Initialize System

```bash
decision-layer init
```

**Description**: Initialize the Decision Layer system by creating necessary directories and configuration files.

**Creates**:
- `registry/` - Function registry storage
- `traces/` - Execution traces
- `config/` - Configuration files
- `data/` - Runtime data

**Example**:
```bash
$ decision-layer init
✅ Initialized Decision Layer system
Created directories: registry, traces, config, data
Created default configuration: config.yaml
```

### Deploy Function

```bash
decision-layer deploy <function_id> <version> <function_file>
```

**Description**: Deploy a new version of a decision function.

**Arguments**:
- `function_id` - Unique identifier for the function
- `version` - Version string (e.g., "1.0", "v2.1")
- `function_file` - Path to the Python file containing the function

**Options**:
- `--schema` - Path to schema file (JSON)
- `--metadata` - Path to metadata file (JSON)
- `--force` - Overwrite existing version

**Example**:
```bash
# Deploy a simple function
$ decision-layer deploy loan_approval 1.0 loan_approval.py

# Deploy with schema and metadata
$ decision-layer deploy loan_approval 2.0 loan_approval.py \
  --schema loan_approval_schema.json \
  --metadata loan_approval_metadata.json

✅ Deployed loan_approval version 1.0
```

### Execute Function

```bash
decision-layer execute <function_id> <input_file> [options]
```

**Description**: Execute a decision function with input data.

**Arguments**:
- `function_id` - Function identifier
- `input_file` - JSON file containing input data

**Options**:
- `--version` - Specific version to use (defaults to latest)
- `--output` - Output file path (defaults to stdout)
- `--validate` - Enable input validation (default: true)
- `--trace` - Enable detailed tracing

**Example**:
```bash
# Execute with default settings
$ decision-layer execute loan_approval test_input.json

# Execute specific version
$ decision-layer execute loan_approval test_input.json --version 1.0

# Save output to file
$ decision-layer execute loan_approval test_input.json --output result.json

# With detailed tracing
$ decision-layer execute loan_approval test_input.json --trace
```

**Input File Format** (`test_input.json`):
```json
{
  "credit_score": 750,
  "income": 75000,
  "age": 30,
  "requested_amount": 25000
}
```

**Output**:
```json
{
  "approved": true,
  "reason": "All criteria met",
  "risk_level": "low",
  "approved_amount": 25000
}
```

### List Functions

```bash
decision-layer list [options]
```

**Description**: List all available decision functions.

**Options**:
- `--detailed` - Show detailed information
- `--format` - Output format (table, json, yaml)
- `--filter` - Filter by tags or author

**Example**:
```bash
# Basic listing
$ decision-layer list
┌─────────────────┬─────────────┬─────────────┬─────────────┐
│ Function ID     │ Versions    │ Latest      │ Status      │
├─────────────────┼─────────────┼─────────────┼─────────────┤
│ loan_approval   │ 1.0, 1.1    │ 1.1         │ approved    │
│ insurance_claim │ 1.0         │ 1.0         │ draft       │
└─────────────────┴─────────────┴─────────────┴─────────────┘

# Detailed listing
$ decision-layer list --detailed --format json
[
  {
    "function_id": "loan_approval",
    "versions": ["1.0", "1.1"],
    "latest_version": "1.1",
    "status": "approved",
    "author": "finance-team",
    "description": "Loan approval decision function",
    "tags": ["loan", "approval", "finance"]
  }
]
```

### View Traces

```bash
decision-layer traces <function_id> [options]
```

**Description**: View execution traces for a function.

**Arguments**:
- `function_id` - Function identifier

**Options**:
- `--date` - Date in YYYYMMDD format (defaults to today)
- `--limit` - Maximum number of traces to show
- `--format` - Output format (table, json, yaml)
- `--filter` - Filter by status (success, error)

**Example**:
```bash
# View today's traces
$ decision-layer traces loan_approval

# View specific date
$ decision-layer traces loan_approval --date 20250127

# View with limit
$ decision-layer traces loan_approval --limit 10

# JSON format
$ decision-layer traces loan_approval --format json
```

**Output**:
```
┌─────────────────────────────────────┬─────────────────────┬─────────┬─────────────┐
│ Trace ID                            │ Timestamp           │ Status  │ Duration    │
├─────────────────────────────────────┼─────────────────────┼─────────┼─────────────┤
│ 550e8400-e29b-41d4-a716-446655440000│ 2025-01-27 10:00:00 │ success │ 12.5ms      │
│ 550e8400-e29b-41d4-a716-446655440001│ 2025-01-27 10:01:00 │ error   │ 8.2ms       │
└─────────────────────────────────────┴─────────────────────┴─────────┴─────────────┘
```

### Function Information

```bash
decision-layer info <function_id> [options]
```

**Description**: Get detailed information about a function.

**Arguments**:
- `function_id` - Function identifier

**Options**:
- `--version` - Specific version (defaults to latest)
- `--format` - Output format (table, json, yaml)

**Example**:
```bash
$ decision-layer info loan_approval --version 1.1
Function: loan_approval
Version: 1.1
Status: approved
Author: finance-team
Created: 2025-01-27 10:00:00
Description: Loan approval decision function

Input Schema:
- credit_score (integer, required): Credit score (300-850)
- income (float, required): Annual income in USD
- age (integer, required): Applicant age (18-100)

Output Schema:
- approved (boolean, required): Whether the loan is approved
- reason (string, required): Reason for approval or denial
- risk_level (enum, required): Risk assessment level

Tags: loan, approval, finance
Policy References: POL-001, POL-002
Compliance: SOX, GDPR
```

### Test Function

```bash
decision-layer test <function_id> <test_file> [options]
```

**Description**: Test a function with validation and multiple test cases.

**Arguments**:
- `function_id` - Function identifier
- `test_file` - JSON file containing test cases

**Options**:
- `--version` - Specific version to test
- `--output` - Output file for results
- `--validate` - Enable schema validation
- `--verbose` - Show detailed test results

**Test File Format** (`test_cases.json`):
```json
{
  "test_cases": [
    {
      "name": "Valid Application",
      "input": {
        "credit_score": 750,
        "income": 75000,
        "age": 30
      },
      "expected": {
        "approved": true
      }
    },
    {
      "name": "Low Credit Score",
      "input": {
        "credit_score": 650,
        "income": 75000,
        "age": 30
      },
      "expected": {
        "approved": false,
        "reason": "Credit score below minimum requirement"
      }
    }
  ]
}
```

**Example**:
```bash
$ decision-layer test loan_approval test_cases.json --verbose
Running 2 test cases...

✅ Valid Application: PASSED
Input: {"credit_score": 750, "income": 75000, "age": 30}
Expected: {"approved": true}
Actual: {"approved": true, "reason": "All criteria met", "risk_level": "low"}

✅ Low Credit Score: PASSED
Input: {"credit_score": 650, "income": 75000, "age": 30}
Expected: {"approved": false, "reason": "Credit score below minimum requirement"}
Actual: {"approved": false, "reason": "Credit score below minimum requirement (700)", "risk_level": "high"}

Test Results: 2/2 PASSED
```

### Clear Data

```bash
decision-layer clear [options]
```

**Description**: Clear traces, cache, and temporary data.

**Options**:
- `--function-id` - Clear data for specific function only
- `--all` - Clear all data (traces, cache, registry)
- `--traces` - Clear traces only
- `--cache` - Clear cache only
- `--confirm` - Skip confirmation prompt

**Example**:
```bash
# Clear all traces
$ decision-layer clear --traces
Cleared 150 trace files

# Clear specific function
$ decision-layer clear --function-id loan_approval
Cleared traces for loan_approval: 25 files

# Clear everything
$ decision-layer clear --all --confirm
Cleared all data: traces, cache, registry
```

### Configuration

```bash
decision-layer config [options]
```

**Description**: Manage configuration settings.

**Subcommands**:
- `show` - Show current configuration
- `set` - Set configuration value
- `get` - Get configuration value
- `reset` - Reset to defaults

**Example**:
```bash
# Show configuration
$ decision-layer config show
Storage Backend: file
Trace Directory: ./traces
Max Input Size: 1048576
Rate Limit: 100 requests/minute

# Set configuration
$ decision-layer config set storage.backend postgresql
$ decision-layer config set storage.connection_string "postgresql://user:pass@localhost/db"

# Get specific value
$ decision-layer config get storage.backend
postgresql
```

### System Status

```bash
decision-layer status [options]
```

**Description**: Check system status and health.

**Options**:
- `--detailed` - Show detailed status information
- `--format` - Output format (table, json, yaml)

**Example**:
```bash
$ decision-layer status
System Status: HEALTHY
Version: 2.0.0
Uptime: 2h 15m 30s

Components:
✅ Registry: Connected
✅ Storage: File backend (./registry)
✅ Traces: 150 files
✅ Cache: 25 entries

Functions: 5 deployed
Traces: 1,250 total executions
Errors: 0 in last 24h
```

## Advanced Usage

### Batch Processing

```bash
# Execute multiple inputs
for input_file in inputs/*.json; do
    decision-layer execute loan_approval "$input_file" --output "results/$(basename "$input_file")"
done

# Process with parallel execution
find inputs/ -name "*.json" | xargs -P 4 -I {} decision-layer execute loan_approval {}
```

### Scripting

```bash
#!/bin/bash
# deploy_and_test.sh

FUNCTION_ID="loan_approval"
VERSION="2.0"

echo "Deploying $FUNCTION_ID version $VERSION..."
decision-layer deploy "$FUNCTION_ID" "$VERSION" "$FUNCTION_ID.py"

echo "Running tests..."
decision-layer test "$FUNCTION_ID" test_cases.json --output test_results.json

echo "Checking status..."
decision-layer status

echo "Done!"
```

### Integration with CI/CD

```yaml
# .github/workflows/test.yml
name: Test Decision Functions

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -e .
    
    - name: Initialize system
      run: decision-layer init
    
    - name: Deploy functions
      run: |
        decision-layer deploy loan_approval 1.0 examples/loan_approval.py
        decision-layer deploy insurance_claim 1.0 examples/insurance_claim.py
    
    - name: Run tests
      run: |
        decision-layer test loan_approval tests/loan_approval_tests.json
        decision-layer test insurance_claim tests/insurance_claim_tests.json
    
    - name: Check status
      run: decision-layer status
```

## Configuration

### Environment Variables

```bash
# Storage configuration
DECISION_LAYER_STORAGE_BACKEND=file
DECISION_LAYER_STORAGE_PATH=./registry

# Trace configuration
DECISION_LAYER_TRACE_DIR=./traces
DECISION_LAYER_TRACE_LEVEL=INFO

# Security
DECISION_LAYER_API_KEY=your-secret-key
DECISION_LAYER_ENABLE_AUTH=true

# Performance
DECISION_LAYER_MAX_INPUT_SIZE=1048576
DECISION_LAYER_RATE_LIMIT=100
```

### Configuration File

The CLI uses `config.yaml` for configuration:

```yaml
# Core configuration
core:
  storage_backend: file
  trace_dir: ./traces
  max_input_size: 1048576

# CLI configuration
cli:
  default_format: table
  enable_colors: true
  verbose_output: false

# Security
security:
  enable_auth: false
  api_key: null

# Performance
performance:
  rate_limit: 100
  cache_size: 1000
```

## Error Handling

### Common Errors

**Function Not Found**:
```bash
$ decision-layer execute unknown_function test.json
Error: Function 'unknown_function' not found
```

**Invalid Input**:
```bash
$ decision-layer execute loan_approval invalid.json
Error: Input validation failed
Field 'credit_score': Value must be between 300 and 850
```

**Version Not Found**:
```bash
$ decision-layer execute loan_approval test.json --version 999.0
Error: Version '999.0' not found for function 'loan_approval'
```

### Debug Mode

Enable debug mode for detailed error information:

```bash
# Set debug environment variable
export DECISION_LAYER_DEBUG=true

# Or use debug flag
decision-layer execute loan_approval test.json --debug
```

## Output Formats

### Table Format (Default)

```bash
$ decision-layer list
┌─────────────────┬─────────────┬─────────────┬─────────────┐
│ Function ID     │ Versions    │ Latest      │ Status      │
├─────────────────┼─────────────┼─────────────┼─────────────┤
│ loan_approval   │ 1.0, 1.1    │ 1.1         │ approved    │
└─────────────────┴─────────────┴─────────────┴─────────────┘
```

### JSON Format

```bash
$ decision-layer list --format json
[
  {
    "function_id": "loan_approval",
    "versions": ["1.0", "1.1"],
    "latest_version": "1.1",
    "status": "approved"
  }
]
```

### YAML Format

```bash
$ decision-layer list --format yaml
- function_id: loan_approval
  versions: [1.0, 1.1]
  latest_version: "1.1"
  status: approved
```

## Next Steps

- **Read the [API Reference](api.md)** for programmatic access
- **Check the [Web Interface Guide](web-interface.md)** for visual tools
- **Explore the [Examples](../examples/)** for working code samples
- **Review the [Architecture Documentation](architecture.md)** for system design 