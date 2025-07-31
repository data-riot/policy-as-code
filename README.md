# Decision Layer - Elegant Decision Management

> Treat decision logic like software with version control, testing, and observability

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 What is Decision Layer?

Decision Layer is an **elegant, minimal, and extensible** decision engine that treats decision logic as software. It provides:

- **🔄 Version Control** - Immutable decision function versions
- **🧪 Testing** - Built-in testing and validation
- **📊 Observability** - Structured tracing and monitoring
- **🔌 Plugins** - Extensible plugin architecture
- **⚡ Performance** - Async execution with caching
- **🛠️ Developer Experience** - Simple CLI and Python APIs

## 🚀 Quick Start

### Option 1: Web UI (Recommended)

The easiest way to get started is with the **Streamlit web interface**:

```bash
# Clone and install
git clone https://github.com/decision-layer/decision-layer.git
cd decision-layer
pip install -r requirements.txt

# Launch the web UI
python run_ui.py

# Open http://localhost:8501 in your browser
```

The web interface provides:
- 📊 **Dashboard** with metrics and charts
- 📦 **Function Management** with visual editor
- 🚀 **Deploy Functions** with templates
- 📈 **Execution Traces** with filtering
- ⚙️ **Settings** and configuration

### Option 2: Local Development (CLI)

```bash
# Clone the repository
git clone https://github.com/decision-layer/decision-layer.git
cd decision-layer

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Option 2: Web UI (Streamlit)

```bash
# Clone the repository
git clone https://github.com/decision-layer/decision-layer.git
cd decision-layer

# Install dependencies
pip install -r requirements.txt

# Run the web interface
python run_ui.py
# Or directly: streamlit run streamlit_app.py

# Open http://localhost:8501 in your browser
```

### Option 3: Docker (Production Ready)

```bash
# Clone the repository
git clone https://github.com/decision-layer/decision-layer.git
cd decision-layer

# Set up environment
cp env.example .env
# Edit .env with your API key and database password

# Start with Docker Compose
docker-compose up -d
```

### Initialize

```bash
# Initialize the decision layer
decision-layer init
```

This creates the necessary directories and a default configuration file.

### API Usage (Docker)

When running with Docker, you can use the REST API:

```bash
# Deploy a decision function
curl -X POST "http://localhost:8000/functions/refund_policy/deploy" \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "v1.0",
    "function_code": "from decision_layer import DecisionContext; def decision_function(input_data, context): return {\"approved\": True}"
  }'

# Execute a decision
curl -X POST "http://localhost:8000/functions/refund_policy/execute" \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"amount": 500, "issue": "damaged"}'

# Check health
curl "http://localhost:8000/health"
```

### Create Your First Decision Function

```python
# decisions/my_policy.py
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """My first decision function"""
    
    # Extract input
    amount = input_data.get('amount', 0)
    
    # Decision logic
    if amount > 1000:
        result = {"approved": False, "reason": "Amount too high"}
    else:
        result = {"approved": True, "reason": "Amount within limits"}
    
    return result
```

### Deploy and Execute

```bash
# Deploy the function
decision-layer deploy my_policy decisions/my_policy.py --version v1.0

# Test the function
decision-layer test my_policy

# Execute with custom input
echo '{"amount": 500}' > input.json
decision-layer execute my_policy input.json
```

## 🖥️ Web Interface

The Decision Layer includes a **beautiful, interactive web interface** built with Streamlit that makes decision management effortless:

### 📊 Dashboard
- **Real-time metrics** showing function count, execution volume, and success rates
- **Interactive charts** displaying execution trends and performance
- **Recent activity feed** with live updates
- **System health monitoring** with component status

### 📦 Function Management
- **Visual function browser** with version history
- **Inline function editor** with syntax highlighting
- **Live testing** with JSON input/output preview
- **One-click deployment** with validation

### 🚀 Function Deployment
- **Template library** with common decision patterns
- **Code validation** with real-time feedback
- **Test before deploy** workflow
- **Version management** with rollback capability

### 📈 Execution Traces
- **Filterable trace viewer** by function, date, and status
- **Performance analytics** with response time tracking
- **Error tracking** with detailed error messages
- **Export capabilities** for analysis

### ⚙️ Settings & Configuration
- **System configuration** viewer
- **Health check** diagnostics
- **Security settings** management
- **Plugin configuration** interface

## 📖 Core Concepts

### Decision Functions

Decision functions are pure Python functions that take input data and return structured output:

```python
def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    # Your decision logic here
    return {"result": "decision_made"}
```

### Version Control

Every decision function is versioned immutably:

```bash
# Deploy multiple versions
decision-layer deploy my_policy decisions/my_policy.py --version v1.0
decision-layer deploy my_policy decisions/my_policy.py --version v1.1

# Execute specific version
decision-layer execute my_policy input.json --version v1.0
```

### Plugins

The system uses a plugin architecture for extensibility:

- **Validation Plugin** - Schema validation
- **Tracing Plugin** - Structured logging
- **Caching Plugin** - Performance optimization

## 🛠️ CLI Commands

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

### Examples

```bash
# Deploy a refund policy
decision-layer deploy refund_policy examples/refund_policy.py --version v1.0

# Test with default data
decision-layer test refund_policy

# Execute with custom input
echo '{"issue": "late", "customer": {"tier": "gold"}, "order_amount": 1000}' > input.json
decision-layer execute refund_policy input.json

# View today's traces
decision-layer traces refund_policy

# List all functions
decision-layer list
```

## 🔧 Configuration

The system uses a YAML configuration file (`config.yaml`):

```yaml
storage:
  backend: "file"  # file, postgres, redis
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

## 📊 Observability

### Traces

Every decision execution generates a structured trace:

```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "function_id": "refund_policy",
  "version": "v1.0",
  "input_hash": "0x4f...",
  "timestamp": "2025-01-27T14:23:51Z",
  "input": {"issue": "late", "customer": {"tier": "gold"}},
  "output": {"refund_amount": 120, "reason": "late issue with gold tier"},
  "status": "success"
}
```

### Viewing Traces

```bash
# View traces for today
decision-layer traces refund_policy

# View traces for specific date
decision-layer traces refund_policy --date 20250127
```

## 🔌 Plugin System

### Creating Custom Plugins

```python
from decision_layer import DecisionPlugin, DecisionContext
from typing import Dict, Any

class MyCustomPlugin(DecisionPlugin):
    async def process(self, data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        # Your plugin logic here
        data["processed_by"] = "my_plugin"
        return data
    
    @property
    def name(self) -> str:
        return "my_custom_plugin"
```

### Built-in Plugins

#### Validation Plugin

Validates input data against schemas:

```python
# Schema definition
schema = {
    "input": {
        "amount": {"required": True, "type": "number"},
        "customer_id": {"required": True, "type": "string"}
    }
}

# Plugin automatically validates inputs
```

#### Tracing Plugin

Adds structured tracing to all executions:

```python
# Automatically adds trace metadata
data["_trace"] = {
    "trace_id": "uuid",
    "timestamp": "iso_timestamp",
    "function_id": "function_name",
    "version": "version"
}
```

#### Caching Plugin

Caches results for performance:

```python
# Automatically caches results by input hash
# Subsequent identical inputs return cached results
```

## 🧪 Testing

### Built-in Testing

```bash
# Test with default data
decision-layer test my_policy

# Test with custom data
echo '{"amount": 500}' > test_data.json
decision-layer test my_policy --test-data test_data.json
```

### Test Data

Create test data files for comprehensive testing:

```json
{
  "test_case_1": {
    "amount": 500,
    "expected": {"approved": true}
  },
  "test_case_2": {
    "amount": 1500,
    "expected": {"approved": false}
  }
}
```

## 🚀 Production Deployment

### File Storage (Development)

```yaml
storage:
  backend: "file"
  path: "./data"
```

### PostgreSQL Storage (Production)

```yaml
storage:
  backend: "postgres"
  connection_string: "postgresql://user:pass@localhost/decisions"
```

### Redis Caching (Production)

```yaml
plugins:
  caching:
    enabled: true
    backend: "redis"
    url: "redis://localhost:6379"
    ttl: 300
```

## 📈 Performance

### Caching

The caching plugin automatically caches results:

```bash
# First execution (cache miss)
decision-layer execute my_policy input.json
# Execution time: 150ms

# Second execution with same input (cache hit)
decision-layer execute my_policy input.json
# Execution time: 5ms
```

### Async Execution

All operations are async for better performance:

```python
import asyncio
from decision_layer import DecisionEngine

async def main():
    engine = DecisionEngine()
    result = await engine.execute("my_policy", {"amount": 500})
    print(result)

asyncio.run(main())
```

## 🔒 Security

### Input Validation

All inputs are validated by default:

```python
# Invalid input raises validation error
try:
    result = await engine.execute("my_policy", {"invalid": "data"})
except ValueError as e:
    print(f"Validation error: {e}")
```

### Trace Sanitization

Sensitive data can be sanitized in traces:

```python
# Configure trace sanitization
config = {
    "plugins": {
        "tracing": {
            "enabled": True,
            "sanitize_fields": ["password", "ssn", "credit_card"]
        }
    }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/decision-layer/decision-layer.git
cd decision-layer
pip install -e .

# Run tests
python -m pytest tests/

# Run linting
python -m flake8 decision_layer/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.decisionlayer.com](https://docs.decisionlayer.com)
- **Issues**: [GitHub Issues](https://github.com/decision-layer/decision-layer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/decision-layer/decision-layer/discussions)

## 🎉 Acknowledgments

- Inspired by the need for better decision logic management
- Built with modern Python async/await patterns
- Designed for developer productivity and system reliability 