# Installation & Quick Start Guide

This comprehensive guide covers installation options and gets you up and running with Decision Layer in minutes.

## Prerequisites

- **Python 3.8+** - The framework requires Python 3.8 or higher
- **Git** - For cloning the repository
- **pip** - Python package installer
- **Basic Python knowledge** - For creating decision functions

## Installation Options

### Option 1: Quick Install (Recommended for Beginners)

For most users, this is the fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Verify installation
python -c "import decision_layer; print('✅ Decision Layer installed successfully!')"
```

### Option 2: Virtual Environment (Recommended for Development)

For development or to avoid conflicts with other Python packages:

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Option 3: Docker Installation

For containerized deployment:

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t decision-layer .
docker run -p 8000:8000 -p 8501:8501 decision-layer
```

### Option 4: Production Installation

For production environments:

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Copy environment configuration
cp env.example .env

# Edit configuration (see Configuration section below)
nano .env

# Install production dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Initialize the system
decision-layer init
```

## Quick Start Tutorial

### Step 1: Initialize the System

```bash
# Initialize the system (creates necessary directories)
decision-layer init
```

This creates:
- `registry/` - Function registry storage
- `traces/` - Execution traces
- `config/` - Configuration files
- `data/` - Runtime data

### Step 2: Create Your First Decision Function

Let's create a simple loan approval decision function.

#### Create the Function File

Create a file called `loan_approval.py`:

```python
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """
    Simple loan approval decision function

    Approves loans for users with:
    - Credit score >= 700
    - Income >= $50,000
    - Age >= 18
    """

    # Extract input data
    credit_score = input_data.get('credit_score', 0)
    income = input_data.get('income', 0)
    age = input_data.get('age', 0)

    # Decision logic
    if age < 18:
        return {
            "approved": False,
            "reason": "Applicant must be 18 or older",
            "risk_level": "high"
        }

    if credit_score < 700:
        return {
            "approved": False,
            "reason": "Credit score below minimum requirement (700)",
            "risk_level": "high"
        }

    if income < 50000:
        return {
            "approved": False,
            "reason": "Income below minimum requirement ($50,000)",
            "risk_level": "medium"
        }

    # All criteria met
    return {
        "approved": True,
        "reason": "All criteria met",
        "risk_level": "low",
        "approved_amount": min(input_data.get('requested_amount', 0), 100000)
    }
```

#### Create the Schema

Create a file called `loan_approval_schema.json`:

```json
{
  "input_schema": {
    "credit_score": {
      "type": "integer",
      "required": true,
      "min_value": 300,
      "max_value": 850,
      "description": "Credit score (300-850)"
    },
    "income": {
      "type": "float",
      "required": true,
      "min_value": 0,
      "description": "Annual income in USD"
    },
    "age": {
      "type": "integer",
      "required": true,
      "min_value": 18,
      "max_value": 100,
      "description": "Applicant age"
    },
    "requested_amount": {
      "type": "float",
      "required": false,
      "default": 0,
      "min_value": 0,
      "description": "Requested loan amount"
    }
  },
  "output_schema": {
    "approved": {
      "type": "boolean",
      "required": true,
      "description": "Whether the loan is approved"
    },
    "reason": {
      "type": "string",
      "required": true,
      "description": "Reason for approval or denial"
    },
    "risk_level": {
      "type": "enum",
      "enum": ["low", "medium", "high"],
      "required": true,
      "description": "Risk assessment level"
    },
    "approved_amount": {
      "type": "float",
      "required": false,
      "description": "Amount approved (if approved)"
    }
  },
  "version": "1.0",
  "function_id": "loan_approval",
  "description": "Simple loan approval decision function"
}
```

### Step 3: Deploy the Function

#### Using the CLI

```bash
# Deploy the function
decision-layer deploy loan_approval 1.0 loan_approval.py

# Verify deployment
decision-layer list
```

#### Using Python

```python
import asyncio
from decision_layer import DecisionEngine
from decision_layer.schemas import create_schema_from_dict
import json

async def deploy_function():
    # Load the schema
    with open('loan_approval_schema.json', 'r') as f:
        schema_dict = json.load(f)

    schema = create_schema_from_dict(schema_dict)

    # Load the function code
    with open('loan_approval.py', 'r') as f:
        function_code = f.read()

    # Create engine and deploy
    engine = DecisionEngine()
    await engine.deploy_function(
        function_id="loan_approval",
        version="1.0",
        function_code=function_code
    )

    print("✅ Function deployed successfully!")

# Run the deployment
asyncio.run(deploy_function())
```

### Step 4: Execute Your First Decision

#### Create Test Data

Create a file called `test_input.json`:

```json
{
  "credit_score": 750,
  "income": 75000,
  "age": 30,
  "requested_amount": 25000
}
```

#### Execute the Decision

##### Using the CLI

```bash
# Execute the decision
decision-layer execute loan_approval test_input.json

# Expected output:
# {
#   "approved": true,
#   "reason": "All criteria met",
#   "risk_level": "low",
#   "approved_amount": 25000
# }
```

##### Using Python

```python
import asyncio
import json
from decision_layer import DecisionEngine

async def execute_decision():
    # Load test data
    with open('test_input.json', 'r') as f:
        input_data = json.load(f)

    # Create engine and execute
    engine = DecisionEngine()
    result = await engine.execute(
        function_id="loan_approval",
        input_data=input_data,
        version="1.0"
    )

    print("Decision Result:")
    print(json.dumps(result, indent=2))

# Run the execution
asyncio.run(execute_decision())
```

### Step 5: View Traces

```bash
# View execution traces
decision-layer traces loan_approval

# View traces for a specific date
decision-layer traces loan_approval --date 20250127
```

## Configuration

### Environment Variables

Copy `env.example` to `.env` and configure the following variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/decision_layer

# Security
DECISION_LAYER_API_KEY=your-secret-api-key
SECRET_KEY=your-secret-key

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/decision_layer.log

# Storage
STORAGE_BACKEND=file  # or postgresql
STORAGE_PATH=./data

# Cross-Domain Integration
LLM_PROVIDER=mock  # or openai, anthropic
ONTOLOGY_PROVIDER=mock  # or owl, neo4j
KG_PROVIDER=mock  # or neo4j, amazon_neptune
```

### Configuration File

The main configuration is in `config.yaml`:

```yaml
# Core Configuration
core:
  storage_backend: file
  trace_dir: ./traces
  max_input_size: 1048576  # 1MB

# Plugin Configuration
plugins:
  validation:
    enabled: true
  tracing:
    enabled: true
    path: ./traces
  caching:
    enabled: true

# Security Configuration
security:
  enable_rate_limiting: true
  enable_input_sanitization: true
  enable_trace_sanitization: true
  max_input_size: 1048576
  rate_limit_requests: 100
  rate_limit_window: 60

# Cross-Domain Integration
integrations:
  llm:
    provider: mock
    config: {}
  ontology:
    provider: mock
    config: {}
  knowledge_graph:
    provider: mock
    config: {}
```

## Verification

After installation, verify that everything is working:

### 1. Check Installation

```bash
# Test package import
python -c "import decision_layer; print('✅ Decision Layer imported successfully')"

# Check version
python -c "import decision_layer; print(f'Version: {decision_layer.__version__}')"

# Check the CLI
decision-layer --help
```

### 2. Test API Interface

```bash
# Start the API server
python run_api.py

# Test API health
curl http://localhost:8000/health

# Open http://localhost:8000/docs for API documentation
```

## Development Setup

For developers who want to contribute to the project:

### 1. Install Development Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 2. Development Tools

The project includes several development tools:

- **Black**: Code formatting (includes import sorting)
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

### 3. Run Development Tools

```bash
# Format code
black decision_layer tests

# Sort imports
black decision_layer tests

# Lint code
flake8 decision_layer tests

# Type check
mypy decision_layer

# Run tests
pytest tests/
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'decision_layer'`

**Solution**: Make sure you've installed the package in development mode:
```bash
pip install -e .
```

#### 2. Permission Errors

**Problem**: Permission denied when creating directories

**Solution**: Check file permissions and ensure you have write access to the installation directory.

#### 3. Port Conflicts

**Problem**: Port 8000 or 8501 already in use

**Solution**: Change ports in configuration or stop conflicting services:
```bash
# Find processes using ports
lsof -i :8000
lsof -i :8501

# Kill processes if needed
kill -9 <PID>
```

#### 4. Database Connection Issues

**Problem**: Cannot connect to PostgreSQL

**Solution**:
- Ensure PostgreSQL is running
- Check connection string in `.env`
- Verify database exists and user has permissions

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: Look in `logs/` directory for error messages
2. **Review configuration**: Ensure all settings in `config.yaml` and `.env` are correct
3. **Search issues**: Check existing GitHub issues for similar problems
4. **Create issue**: Open a new GitHub issue with detailed error information

## Next Steps

After successful installation and quick start:

1. **Read the [Architecture Documentation](architecture.md)** to understand the system design
2. **Explore the [Examples](../examples/)** to see working implementations
3. **Check the [API Documentation](api.md)** for programmatic access
4. **Review the [CLI Reference](cli.md)** for all available commands
5. **Learn about [Configuration](configuration.md)** for advanced setup

## Support

For additional support:

- **Documentation**: Check the [docs/](docs/) directory
- **Examples**: Review the [examples/](../examples/) directory
- **Issues**: Report bugs on [GitHub Issues](https://github.com/data-riot/decision-layer/issues)
- **Discussions**: Join the [GitHub Discussions](https://github.com/data-riot/decision-layer/issues)

You're now ready to build sophisticated decision management systems with Decision Layer! 🚀
