# Decision Layer

A Python framework for managing decision logic as versioned, testable functions with structured observability.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Decision Layer provides a structured approach to managing business decision logic. It treats decisions as software artifacts that can be versioned, tested, and monitored. This can help teams maintain consistency, track changes, and ensure reliability in decision-making systems.

### Key Features

- **Version Control** - Track changes to decision logic over time
- **Testing Framework** - Validate decision functions with test cases
- **Observability** - Monitor decision execution with structured traces
- **Plugin Architecture** - Extend functionality with custom plugins
- **Async Execution** - Handle concurrent decision requests efficiently
- **Multiple Interfaces** - CLI, REST API, and web interface

## Getting Started

### Quick Start

The fastest way to get started with Decision Layer:

```bash
# Clone and install
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer
pip install -r requirements.txt

# Launch the web interface
python run_ui.py

# Open http://localhost:8501 in your browser
```

The web interface includes:
- Dashboard with execution metrics
- Visual function editor
- Template library for common patterns
- Trace viewer and analytics
- Configuration management

### Command Line Interface

For developers who prefer command-line tools:

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Docker Deployment

For production environments:

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Set up environment
cp env.example .env
# Edit .env with your configuration

# Start with Docker Compose
docker-compose up -d
```

### Initial Setup

```bash
# Initialize the system
decision-layer init
```

This creates the necessary directories and a default configuration file.

## 📚 Documentation

For comprehensive documentation, see the [docs/](docs/) directory:

- **[Architecture Overview](docs/architecture.md)** - System architecture and design principles
- **[Installation Guide](docs/installation.md)** - Detailed installation instructions
- **[API Reference](docs/api.md)** - REST API documentation
- **[CLI Reference](docs/cli.md)** - Command-line interface documentation
- **[Examples](../examples/)** - Working examples and demos

## Core Concepts

### Decision Functions

Decision functions are Python functions that take structured input and return structured output. They represent a single decision point in your business logic.

```python
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """Example decision function for refund approval"""

    amount = input_data.get('amount', 0)
    customer_tier = input_data.get('customer', {}).get('tier', 'standard')

    # Decision logic
    if amount > 1000 and customer_tier == 'standard':
        return {"approved": False, "reason": "Amount exceeds limit for standard tier"}
    elif amount > 2000:
        return {"approved": False, "reason": "Amount exceeds maximum limit"}
    else:
        return {"approved": True, "reason": "Approved within limits"}
```

### Version Management

Each decision function can have multiple versions, allowing you to track changes and roll back if needed:

```bash
# Deploy multiple versions
decision-layer deploy refund_policy decisions/refund_policy.py --version v1.0
decision-layer deploy refund_policy decisions/refund_policy.py --version v1.1

# Execute specific version
decision-layer execute refund_policy input.json --version v1.0
```

### Plugin System

The framework uses plugins to add functionality:

- **Validation Plugin** - Ensures input data meets expected schemas
- **Tracing Plugin** - Records execution details for monitoring
- **Caching Plugin** - Improves performance by caching results

## Usage Examples

### Creating a Decision Function

```python
# decisions/approval_policy.py
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """Approval decision based on amount and customer history"""

    amount = input_data.get('amount', 0)
    customer_score = input_data.get('customer_score', 0)

    # Decision logic
    if customer_score >= 800:
        max_amount = 5000
    elif customer_score >= 600:
        max_amount = 2000
    else:
        max_amount = 500

    approved = amount <= max_amount

    return {
        "approved": approved,
        "max_amount": max_amount,
        "reason": f"Customer score {customer_score} allows max {max_amount}"
    }
```

### Deploying and Testing

```bash
# Deploy the function
decision-layer deploy approval_policy decisions/approval_policy.py --version v1.0

# Test with default data
decision-layer test approval_policy

# Test with custom input
echo '{"amount": 1500, "customer_score": 750}' > input.json
decision-layer execute approval_policy input.json
```

### API Usage

When running with Docker, you can use the REST API:

```bash
# Deploy a decision function
curl -X POST "http://localhost:8000/functions/approval_policy/deploy" \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "v1.0",
    "function_code": "def decision_function(input_data, context): return {\"approved\": True}"
  }'

# Execute a decision
curl -X POST "http://localhost:8000/functions/approval_policy/execute" \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"amount": 1500, "customer_score": 750}'
```

## CLI Reference

### Core Commands

```bash
# Initialize the system
decision-layer init

# Deploy a function
decision-layer deploy <function_id> <file> --version <version>

# Execute a function
decision-layer execute <function_id> <input_file> [--version <version>]

# Test a function
decision-layer test <function_id> [--version <version>]

# List functions
decision-layer list

# View traces
decision-layer traces <function_id> [--date <YYYYMMDD>]

# Show function info
decision-layer info <function_id> [--version <version>]

# Clear traces
decision-layer clear [--function-id <id>] [--all]
```

## Configuration

The system uses a YAML configuration file (`config.yaml`):

```yaml
storage:
  backend: "file"  # file, postgresql
  path: "./data"

plugins:
  validation:
    enabled: true
    strict: false

  tracing:
    enabled: true
    path: "./traces"

  caching:
    enabled: true
    ttl: 300

api:
  host: "0.0.0.0"
  port: 8000
  cors: true
```

## Observability

### Execution Traces

Every decision execution generates a structured trace for monitoring and debugging:

```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "function_id": "approval_policy",
  "version": "v1.0",
  "input_hash": "0x4f...",
  "timestamp": "2025-01-27T14:23:51Z",
  "input": {"amount": 1500, "customer_score": 750},
  "output": {"approved": true, "max_amount": 2000},
  "status": "success"
}
```

### Viewing Traces

```bash
# View traces for today
decision-layer traces approval_policy

# View traces for specific date
decision-layer traces approval_policy --date 20250127
```

## Plugin Development

### Creating Custom Plugins

```python
from decision_layer import DecisionPlugin, DecisionContext
from typing import Dict, Any

class LoggingPlugin(DecisionPlugin):
    async def process(self, data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        # Add logging information
        data["logged_at"] = context.timestamp.isoformat()
        data["function_version"] = context.version
        return data

    @property
    def name(self) -> str:
        return "logging_plugin"
```

## Testing

### Built-in Testing

```bash
# Test with default data
decision-layer test approval_policy

# Test with custom data
echo '{"amount": 500, "customer_score": 800}' > test_data.json
decision-layer test approval_policy --test-data test_data.json
```

### Test Data Format

Create test data files for comprehensive testing:

```json
{
  "test_case_1": {
    "input": {"amount": 500, "customer_score": 800},
    "expected": {"approved": true}
  },
  "test_case_2": {
    "input": {"amount": 3000, "customer_score": 600},
    "expected": {"approved": false}
  }
}
```

## Deployment Options

### Development (File Storage)

```yaml
storage:
  backend: "file"
  path: "./data"
```

### Production (PostgreSQL)

```yaml
storage:
  backend: "postgresql"
  connection_string: "postgresql://user:pass@localhost/decisions"
```

## Performance Considerations

### Caching

The caching plugin can improve performance for repeated decisions:

```bash
# First execution (cache miss)
decision-layer execute approval_policy input.json
# Execution time: 150ms

# Second execution with same input (cache hit)
decision-layer execute approval_policy input.json
# Execution time: 5ms
```

### Async Execution

All operations are async for better concurrency:

```python
import asyncio
from decision_layer import DecisionEngine

async def main():
    engine = DecisionEngine()
    result = await engine.execute("approval_policy", {"amount": 500})
    print(result)

asyncio.run(main())
```

## Security

### Input Validation

All inputs are validated by default:

```python
# Invalid input raises validation error
try:
    result = await engine.execute("approval_policy", {"invalid": "data"})
except ValueError as e:
    print(f"Validation error: {e}")
```

### Trace Sanitization

Sensitive data can be sanitized in traces:

```yaml
plugins:
  tracing:
    enabled: true
    sanitize_fields: ["password", "ssn", "credit_card"]
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer
pip install -e .

# Run tests
python -m pytest tests/

# Run linting
python -m flake8 decision_layer/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
