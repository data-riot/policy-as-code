# User Interfaces Guide

This guide covers all the ways to interact with Decision Layer, including the API, CLI, YAML interface, and planned web interface.

## API Interface

The REST API provides programmatic access to all Decision Layer functionality.

### Base URL
```
http://localhost:8000
```

### Key Endpoints

- **Health Check**: `GET /health`
- **Function Management**: `POST /functions/deploy`, `GET /functions/list`
- **Decision Execution**: `POST /decisions/execute`
- **Trace Management**: `GET /traces/{function_id}`
- **Documentation**: `GET /docs` (Interactive OpenAPI docs)

### Example Usage

```bash
# Health check
curl http://localhost:8000/health

# Deploy a function
curl -X POST http://localhost:8000/functions/deploy \
  -H "Content-Type: application/json" \
  -d '{"function_id": "loan_approval", "version": "1.0", "code": "..."}'

# Execute a decision
curl -X POST http://localhost:8000/decisions/execute \
  -H "Content-Type: application/json" \
  -d '{"function_id": "loan_approval", "input_data": {...}}'
```

## CLI Interface

The command-line interface provides easy access to all functionality.

### Installation
```bash
# Install the CLI
pip install -e .

# Verify installation
decision-layer --help
```

### Key Commands

```bash
# Initialize the system
decision-layer init

# Deploy a function
decision-layer deploy <function_id> <version> <file_path>

# Execute a decision
decision-layer execute <function_id> <input_file>

# List functions
decision-layer list

# View traces
decision-layer traces <function_id>

# Get help
decision-layer --help
```

### Example Workflow

```bash
# 1. Initialize
decision-layer init

# 2. Deploy function
decision-layer deploy loan_approval 1.0 loan_approval.py

# 3. Execute decision
decision-layer execute loan_approval test_input.json

# 4. View traces
decision-layer traces loan_approval
```

## YAML Decision Interface

The YAML Decision Interface allows business users to define decision logic using simple YAML files instead of writing Python code.

### Overview

Instead of writing Python functions, you can define decision logic in YAML format with:
- **Input field definitions** with types and validation
- **Business rules** with conditions and results
- **Metadata** for tracking and compliance

### Quick Start

#### 1. Create a YAML Decision File

```yaml
name: "loan_approval_decision"
description: "Loan approval decision based on customer profile"

input_fields:
  credit_score:
    type: integer
    required: true
    min_value: 300
    max_value: 850
    description: "Customer credit score"

  income:
    type: float
    required: true
    min_value: 0
    description: "Annual income in USD"

  age:
    type: integer
    required: true
    min_value: 18
    max_value: 100
    description: "Customer age"

rules:
  - name: "age_check"
    condition: "age < 18"
    result:
      approved: false
      reason: "Applicant must be 18 or older"
      risk_level: "high"

  - name: "credit_score_check"
    condition: "credit_score < 700"
    result:
      approved: false
      reason: "Credit score below minimum requirement (700)"
      risk_level: "high"

  - name: "income_check"
    condition: "income < 50000"
    result:
      approved: false
      reason: "Income below minimum requirement ($50,000)"
      risk_level: "medium"

  - name: "approve_loan"
    condition: "age >= 18 and credit_score >= 700 and income >= 50000"
    result:
      approved: true
      reason: "All criteria met"
      risk_level: "low"
      approved_amount: "min(requested_amount, 100000)"

output_fields:
  approved:
    type: boolean
    required: true
    description: "Whether the loan is approved"

  reason:
    type: string
    required: true
    description: "Reason for approval or denial"

  risk_level:
    type: enum
    enum: ["low", "medium", "high"]
    required: true
    description: "Risk assessment level"

  approved_amount:
    type: float
    required: false
    description: "Amount approved (if approved)"

metadata:
  version: "1.0"
  author: "Data Governance Team"
  last_updated: "2025-01-27"
  legal_references:
    - "https://finlex.fi/fi/laki/alkup/1999/19990544#L7"
```

#### 2. Deploy the YAML Decision

```bash
# Deploy using CLI
decision-layer deploy-yaml loan_approval_decision.yaml

# Or using Python
python -c "
from decision_layer.yaml_interface import YAMLDecisionProcessor
processor = YAMLDecisionProcessor()
processor.deploy_yaml_decision('loan_approval_decision.yaml')
"
```

#### 3. Execute the Decision

```bash
# Execute using CLI
decision-layer execute loan_approval_decision test_input.json

# Or using Python
python -c "
from decision_layer.yaml_interface import YAMLDecisionProcessor
import json

processor = YAMLDecisionProcessor()
with open('test_input.json', 'r') as f:
    input_data = json.load(f)

result = processor.execute_yaml_decision('loan_approval_decision', input_data)
print(json.dumps(result, indent=2))
"
```

### YAML Schema Reference

#### Input Fields
```yaml
input_fields:
  field_name:
    type: string|integer|float|boolean|enum|array
    required: true|false
    min_value: number
    max_value: number
    min_length: number
    max_length: number
    pattern: "regex_pattern"
    enum: ["value1", "value2"]
    default: default_value
    description: "Field description"
```

#### Rules
```yaml
rules:
  - name: "rule_name"
    condition: "python_expression"
    result:
      field_name: value_or_expression
```

#### Output Fields
```yaml
output_fields:
  field_name:
    type: string|integer|float|boolean|enum|array
    required: true|false
    description: "Field description"
```

### Advanced Features

#### Complex Conditions
```yaml
rules:
  - name: "complex_approval"
    condition: |
      age >= 18 and
      credit_score >= 700 and
      income >= 50000 and
      (employment_years >= 2 or income >= 100000)
    result:
      approved: true
      reason: "Complex criteria met"
```

#### Dynamic Values
```yaml
rules:
  - name: "approve_with_amount"
    condition: "approved == true"
    result:
      approved_amount: "min(requested_amount, income * 0.3)"
```

#### Multiple Outputs
```yaml
rules:
  - name: "comprehensive_decision"
    condition: "credit_score >= 750"
    result:
      approved: true
      interest_rate: 3.5
      term_years: 30
      special_offers: ["low_rate", "no_fee"]
```

## Web Interface (Planned)

> **⚠️ Not Implemented**: The web interface is planned but not yet implemented. This document describes the intended functionality.

The Decision Layer is planned to provide a modern, interactive web interface for managing decision functions, viewing traces, and testing decisions visually.

### Planned Features

#### Interface Components
```
http://localhost:8501
```

#### Dashboard
- System overview and health status
- Recent decision executions
- Performance metrics
- Quick access to common functions

#### Function Management
- Visual function editor
- Schema validation
- Version control
- Deployment management

#### Decision Testing
- Interactive test interface
- Input validation
- Real-time execution
- Result visualization

#### Trace Viewer
- Execution history
- Performance analytics
- Error tracking
- Audit trails

#### Configuration
- System settings
- Security configuration
- Integration setup
- User management

### Planned Architecture

The web interface will be built using:
- **Streamlit** for the main interface
- **FastAPI** for the backend API
- **React** for advanced components
- **D3.js** for data visualization

## Interface Comparison

| Feature | API | CLI | YAML | Web (Planned) |
|---------|-----|-----|------|----------------|
| **Programmatic Access** | ✅ | ✅ | ✅ | ❌ |
| **Business User Friendly** | ❌ | ❌ | ✅ | ✅ |
| **Visual Interface** | ❌ | ❌ | ❌ | ✅ |
| **Version Control** | ✅ | ✅ | ✅ | ✅ |
| **Real-time Testing** | ✅ | ✅ | ✅ | ✅ |
| **Batch Processing** | ✅ | ✅ | ✅ | ❌ |
| **Integration Ready** | ✅ | ✅ | ✅ | ✅ |

## Best Practices

### Choosing the Right Interface

- **API**: Use for integrations, automation, and programmatic access
- **CLI**: Use for development, testing, and automation scripts
- **YAML**: Use for business users and non-technical stakeholders
- **Web**: Use for interactive management and visualization (when available)

### Interface-Specific Tips

#### API Interface
- Always check the `/health` endpoint before making requests
- Use proper HTTP status codes for error handling
- Implement retry logic for production use
- Cache function schemas to reduce API calls

#### CLI Interface
- Use shell scripts to automate common workflows
- Pipe output to files for logging and analysis
- Use `--help` to discover new features
- Combine with other command-line tools

#### YAML Interface
- Keep rules simple and readable
- Use descriptive field names
- Add comprehensive metadata
- Test with various input scenarios
- Version control your YAML files

## Troubleshooting

### Common Issues

#### API Interface
- **Connection refused**: Ensure the API server is running (`python run_api.py`)
- **Authentication errors**: Check API key configuration
- **Timeout errors**: Increase timeout settings for large functions

#### CLI Interface
- **Command not found**: Ensure `pip install -e .` was run
- **Permission errors**: Check file permissions and user access
- **Function not found**: Verify function deployment

#### YAML Interface
- **Parse errors**: Validate YAML syntax
- **Schema errors**: Check field definitions and types
- **Execution errors**: Verify rule conditions and expressions

### Getting Help

- **API Documentation**: Visit `http://localhost:8000/docs`
- **CLI Help**: Run `decision-layer --help`
- **YAML Examples**: Check the `examples/` directory
- **Issues**: Report problems on GitHub Issues

## Next Steps

1. **Start with CLI**: Get familiar with basic operations
2. **Try YAML**: Create business-friendly decision rules
3. **Use API**: Integrate with your applications
4. **Plan for Web**: Prepare for the upcoming web interface

Choose the interface that best fits your use case and technical requirements! 🚀
