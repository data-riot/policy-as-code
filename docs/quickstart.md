# Quick Start Tutorial

This tutorial will get you up and running with Decision Layer in minutes. You'll learn how to create your first decision function, deploy it, and execute decisions.

## Prerequisites

- Python 3.8+ installed
- Basic Python knowledge
- Git (for cloning the repository)

## Step 1: Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/data-riot/decision-layer.git
cd decision-layer

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Verify Installation

```bash
# Test the installation
python -c "import decision_layer; print('✅ Decision Layer installed successfully!')"

# Check the CLI
decision-layer --help
```

## Step 2: Initialize the System

```bash
# Initialize the system (creates necessary directories)
decision-layer init
```

This creates:
- `registry/` - Function registry storage
- `traces/` - Execution traces
- `config/` - Configuration files
- `data/` - Runtime data

## Step 3: Create Your First Decision Function

Let's create a simple loan approval decision function.

### Create the Function File

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

### Create the Schema

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

## Step 4: Deploy the Function

### Using the CLI

```bash
# Deploy the function
decision-layer deploy loan_approval 1.0 loan_approval.py

# Verify deployment
decision-layer list
```

### Using Python

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

## Step 5: Execute Your First Decision

### Create Test Data

Create a file called `test_input.json`:

```json
{
  "credit_score": 750,
  "income": 75000,
  "age": 30,
  "requested_amount": 25000
}
```

### Execute the Decision

#### Using the CLI

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

#### Using Python

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

## Step 6: View Traces

```bash
# View execution traces
decision-layer traces loan_approval

# View traces for a specific date
decision-layer traces loan_approval --date 20250127
```

## Step 7: Test Different Scenarios

Let's test some edge cases:

### Test Case 1: Low Credit Score

```json
{
  "credit_score": 650,
  "income": 75000,
  "age": 30,
  "requested_amount": 25000
}
```

Expected result: `{"approved": false, "reason": "Credit score below minimum requirement (700)"}`

### Test Case 2: Young Applicant

```json
{
  "credit_score": 750,
  "income": 75000,
  "age": 17,
  "requested_amount": 25000
}
```

Expected result: `{"approved": false, "reason": "Applicant must be 18 or older"}`

### Test Case 3: High Income, Low Credit

```json
{
  "credit_score": 720,
  "income": 120000,
  "age": 35,
  "requested_amount": 50000
}
```

Expected result: `{"approved": true, "reason": "All criteria met"}`

## Step 8: Use the Web Interface

```bash
# Start the web interface
python run_ui.py

# Open http://localhost:8501 in your browser
```

The web interface provides:
- **Dashboard** - Overview of your decision functions
- **Function Editor** - Visual editor for decision functions
- **Trace Viewer** - Interactive trace analysis
- **Test Runner** - Easy testing interface

## Step 9: Explore Cross-Domain Features

### Natural Language Query

```python
from decision_layer import create_unified_interface

async def test_natural_language():
    # Create unified interface
    interface = create_unified_interface()
    
    # Ask a natural language question
    response = await interface.process_query(
        "What decision functions do we have for loan approval?",
        include_cross_domain=True
    )
    
    print(f"Query: {response.query}")
    print(f"Response: {response.primary_response}")
    if response.llm_explanation:
        print(f"LLM Explanation: {response.llm_explanation}")

# Run the query
asyncio.run(test_natural_language())
```

### LLM-Generated Function

```python
from decision_layer.llm_integration import LLMIntegration, create_llm_provider

async def generate_function_with_llm():
    # Create LLM integration
    llm_provider = create_llm_provider("mock", {})
    registry = FunctionRegistry("./registry")
    llm_integration = LLMIntegration(registry, llm_provider)
    
    # Generate function from natural language
    artifact = await llm_integration.generate_decision_function(
        policy_description="Approve insurance claims for amounts under $1000 with valid documentation",
        function_id="insurance_claim_llm",
        version="1.0"
    )
    
    print(f"✅ Generated function: {artifact.function_id} v{artifact.version}")

# Run the generation
asyncio.run(generate_function_with_llm())
```

## Step 10: Next Steps

Congratulations! You've successfully:

1. ✅ **Installed Decision Layer**
2. ✅ **Created your first decision function**
3. ✅ **Deployed and executed decisions**
4. ✅ **Viewed execution traces**
5. ✅ **Tested different scenarios**
6. ✅ **Explored the web interface**
7. ✅ **Used cross-domain features**

### What to Explore Next

1. **Read the [Architecture Documentation](architecture.md)** to understand the system design
2. **Check out the [Examples](../examples/)** for more complex use cases
3. **Explore the [API Documentation](api.md)** for programmatic access
4. **Review the [CLI Reference](cli.md)** for all available commands
5. **Learn about [Configuration](configuration.md)** for advanced setup

### Advanced Topics

- **Shadow Testing** - Test new versions safely
- **Cross-Domain Integration** - LLM, Ontology, and Knowledge Graph features
- **Plugin Development** - Create custom plugins
- **Production Deployment** - Deploy to production environments
- **Monitoring and Observability** - Set up comprehensive monitoring

## Troubleshooting

### Common Issues

**Problem**: `ModuleNotFoundError: No module named 'decision_layer'`
**Solution**: Make sure you ran `pip install -e .` in the project directory

**Problem**: `Permission denied` when creating directories
**Solution**: Check file permissions and ensure you have write access

**Problem**: Port 8501 already in use
**Solution**: Change the port in the web interface or stop conflicting services

**Problem**: Function not found
**Solution**: Make sure you deployed the function first with `decision-layer deploy`

### Getting Help

- **Documentation**: Check the [docs/](docs/) directory
- **Examples**: Review the [examples/](../examples/) directory
- **Issues**: Report bugs on [GitHub Issues](https://github.com/data-riot/decision-layer/issues)
- **Discussions**: Join the [GitHub Discussions](https://github.com/data-riot/decision-layer/issues)

You're now ready to build sophisticated decision management systems with Decision Layer! 🚀 