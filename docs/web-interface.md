# Web Interface Guide

The Decision Layer provides a modern, interactive web interface built with Streamlit for managing decision functions, viewing traces, and testing decisions visually.

## Quick Start

### Launch the Web Interface

```bash
# Start the web interface
python run_ui.py

# Or run directly with Streamlit
streamlit run streamlit_app.py
```

### Access the Interface

Open your browser and navigate to:
```
http://localhost:8501
```

## Interface Overview

The web interface is organized into several main sections:

### 🏠 Dashboard

The dashboard provides an overview of your Decision Layer system:

- **System Status** - Health indicators and uptime
- **Function Summary** - Total functions, versions, and status
- **Recent Activity** - Latest executions and traces
- **Performance Metrics** - Execution times and error rates
- **Quick Actions** - Common tasks and shortcuts

### 📝 Function Management

#### Function List

View all deployed decision functions with:
- Function ID and description
- Available versions
- Current status (Draft, Review, Approved, etc.)
- Last modified date
- Quick action buttons

#### Function Editor

Create and edit decision functions with:
- **Code Editor** - Syntax-highlighted Python editor
- **Schema Builder** - Visual schema creation tool
- **Metadata Editor** - Function metadata and tags
- **Live Preview** - Real-time function testing
- **Version Control** - Version management and comparison

#### Function Deployment

Deploy functions with:
- **Validation** - Automatic schema and code validation
- **Testing** - Built-in test runner
- **Metadata** - Rich metadata and documentation
- **Governance** - Approval workflow integration

### 🔍 Trace Viewer

#### Trace List

Browse execution traces with:
- **Filtering** - Filter by function, date, status
- **Search** - Search through trace data
- **Sorting** - Sort by timestamp, duration, status
- **Pagination** - Navigate large trace sets

#### Trace Details

View detailed trace information:
- **Input/Output** - Complete input and output data
- **Execution Details** - Timing, performance metrics
- **Error Information** - Detailed error messages
- **Context** - Execution context and metadata

#### Trace Analysis

Analyze trace patterns with:
- **Performance Charts** - Execution time trends
- **Error Analysis** - Error patterns and frequency
- **Usage Statistics** - Function usage metrics
- **Trend Analysis** - Historical performance trends

### 🧪 Test Runner

#### Test Interface

Test decision functions with:
- **Input Builder** - Visual input data creation
- **Schema Validation** - Real-time input validation
- **Output Display** - Formatted output presentation
- **Comparison** - Compare multiple versions

#### Batch Testing

Run multiple test cases:
- **Test Case Management** - Create and organize test cases
- **Batch Execution** - Run multiple tests at once
- **Result Analysis** - Compare expected vs actual results
- **Report Generation** - Generate test reports

### 🔧 Configuration

#### System Settings

Configure the system with:
- **Storage Settings** - Backend configuration
- **Security Settings** - Authentication and authorization
- **Performance Settings** - Rate limiting and caching
- **Integration Settings** - LLM, Ontology, and KG providers

#### User Preferences

Customize the interface:
- **Theme Selection** - Light/dark mode
- **Layout Options** - Customize dashboard layout
- **Notification Settings** - Configure alerts and notifications
- **Export Settings** - Default export formats

## Detailed Features

### Function Editor

#### Code Editor Features

```python
# Example function in the editor
from typing import Dict, Any
from decision_layer import DecisionContext

def decision_function(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    """
    Loan approval decision function
    
    Approves loans for users with:
    - Credit score >= 700
    - Income >= $50,000
    - Age >= 18
    """
    
    credit_score = input_data.get('credit_score', 0)
    income = input_data.get('income', 0)
    age = input_data.get('age', 0)
    
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
    
    return {
        "approved": True,
        "reason": "All criteria met",
        "risk_level": "low",
        "approved_amount": min(input_data.get('requested_amount', 0), 100000)
    }
```

**Features**:
- **Syntax Highlighting** - Python syntax highlighting
- **Auto-completion** - Intelligent code completion
- **Error Detection** - Real-time error checking
- **Code Formatting** - Automatic code formatting
- **Version History** - Track code changes

#### Schema Builder

Create schemas visually:

**Input Schema**:
```json
{
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
  }
}
```

**Output Schema**:
```json
{
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
  }
}
```

### Trace Viewer

#### Trace List View

```
┌─────────────────────────────────────┬─────────────────────┬─────────┬─────────────┬─────────────┐
│ Function ID                         │ Timestamp           │ Status  │ Duration    │ Input Hash  │
├─────────────────────────────────────┼─────────────────────┼─────────┼─────────────┼─────────────┤
│ loan_approval                       │ 2025-01-27 10:00:00 │ success │ 12.5ms      │ 0x4f...     │
│ loan_approval                       │ 2025-01-27 10:01:00 │ error   │ 8.2ms       │ 0xe9...     │
│ insurance_claim                     │ 2025-01-27 10:02:00 │ success │ 15.1ms      │ 0xa1...     │
└─────────────────────────────────────┴─────────────────────┴─────────┴─────────────┴─────────────┘
```

#### Trace Detail View

**Input Data**:
```json
{
  "credit_score": 750,
  "income": 75000,
  "age": 30,
  "requested_amount": 25000
}
```

**Output Data**:
```json
{
  "approved": true,
  "reason": "All criteria met",
  "risk_level": "low",
  "approved_amount": 25000
}
```

**Execution Details**:
- **Function**: `loan_approval` v1.1
- **Execution Time**: 12.5ms
- **Status**: Success
- **Input Hash**: `0x4f...`
- **Output Hash**: `0xe9...`
- **Timestamp**: 2025-01-27T10:00:00Z

### Test Runner

#### Single Test Interface

**Input Builder**:
```json
{
  "credit_score": 750,
  "income": 75000,
  "age": 30,
  "requested_amount": 25000
}
```

**Output Display**:
```json
{
  "approved": true,
  "reason": "All criteria met",
  "risk_level": "low",
  "approved_amount": 25000
}
```

**Test Results**:
- ✅ **Validation**: Input schema validation passed
- ✅ **Execution**: Function executed successfully
- ✅ **Output**: Output schema validation passed
- ⏱️ **Performance**: 12.5ms execution time

#### Batch Test Interface

**Test Cases**:
```json
[
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
      "approved": false
    }
  }
]
```

**Batch Results**:
```
Test Results: 2/2 PASSED

✅ Valid Application: PASSED
   Input: {"credit_score": 750, "income": 75000, "age": 30}
   Expected: {"approved": true}
   Actual: {"approved": true, "reason": "All criteria met", "risk_level": "low"}

✅ Low Credit Score: PASSED
   Input: {"credit_score": 650, "income": 75000, "age": 30}
   Expected: {"approved": false}
   Actual: {"approved": false, "reason": "Credit score below minimum requirement", "risk_level": "high"}
```

### Cross-Domain Features

#### Natural Language Query

**Query Interface**:
```
What are the risk factors for user 123?
```

**Response Display**:
```
Query: What are the risk factors for user 123?

Primary Response:
- Risk Score: 0.3
- Risk Factors: ["new_account", "high_transaction_volume"]

Ontology Context:
- Entity Type: User
- Properties: {"account_age": 30, "transaction_count": 45}

Knowledge Graph Context:
- Related Entities: ["account_456", "transaction_789"]
- Risk Indicators: ["suspicious_pattern", "unusual_amount"]

LLM Explanation:
User 123 shows moderate risk due to being a new account holder with high transaction volume.
```

#### LLM Function Generation

**Policy Description**:
```
Approve insurance claims for amounts under $1000 with valid documentation
```

**Generated Function**:
```python
def decision_function(input_data, context):
    """
    Auto-generated insurance claim approval function
    """
    amount = input_data.get('amount', 0)
    documentation = input_data.get('documentation', False)
    
    if amount > 1000:
        return {
            "approved": False,
            "reason": "Amount exceeds $1000 limit"
        }
    
    if not documentation:
        return {
            "approved": False,
            "reason": "Valid documentation required"
        }
    
    return {
        "approved": True,
        "reason": "Claim approved",
        "approved_amount": amount
    }
```

## Advanced Features

### Dashboard Customization

#### Widget Configuration

Customize dashboard widgets:
- **Add/Remove Widgets** - Configure which widgets to display
- **Widget Layout** - Arrange widgets in custom layouts
- **Widget Settings** - Configure widget-specific settings
- **Auto-refresh** - Set refresh intervals for real-time data

#### Performance Monitoring

Monitor system performance:
- **Execution Metrics** - Average execution times
- **Error Rates** - Error frequency and patterns
- **Throughput** - Requests per second
- **Resource Usage** - CPU, memory, and storage usage

### Export and Reporting

#### Data Export

Export data in various formats:
- **JSON Export** - Export traces and functions as JSON
- **CSV Export** - Export trace data as CSV
- **PDF Reports** - Generate PDF reports
- **Excel Export** - Export to Excel format

#### Report Generation

Generate comprehensive reports:
- **Function Reports** - Function usage and performance
- **Trace Reports** - Execution analysis and trends
- **Error Reports** - Error analysis and recommendations
- **Compliance Reports** - Audit and compliance documentation

### Integration Features

#### API Integration

Connect to external systems:
- **Webhook Support** - Send notifications to external systems
- **API Keys** - Manage API access and authentication
- **Rate Limiting** - Configure API rate limits
- **Monitoring** - Monitor API usage and performance

#### External Tools

Integrate with external tools:
- **Git Integration** - Version control integration
- **CI/CD Integration** - Continuous integration support
- **Monitoring Tools** - Prometheus, Grafana integration
- **Logging Tools** - Centralized logging integration

## Configuration

### Interface Settings

Configure the web interface:

```yaml
# Web interface configuration
web:
  title: "Decision Layer"
  theme: "light"  # light, dark, auto
  layout: "wide"  # wide, centered
  sidebar_state: "expanded"  # expanded, collapsed, auto
  
  # Dashboard settings
  dashboard:
    auto_refresh: 30  # seconds
    default_widgets: ["status", "functions", "recent_traces"]
    
  # Editor settings
  editor:
    theme: "monokai"  # editor theme
    font_size: 14
    line_numbers: true
    auto_complete: true
    
  # Trace viewer settings
  traces:
    page_size: 50
    default_sort: "timestamp"
    show_input_output: true
```

### Security Settings

Configure security features:

```yaml
# Security configuration
security:
  enable_auth: true
  session_timeout: 3600  # seconds
  max_login_attempts: 5
  password_policy:
    min_length: 8
    require_special_chars: true
    require_numbers: true
    
  # API security
  api:
    enable_rate_limiting: true
    rate_limit: 100  # requests per minute
    enable_cors: true
    allowed_origins: ["http://localhost:3000"]
```

## Troubleshooting

### Common Issues

#### Interface Not Loading

**Problem**: Web interface doesn't load or shows errors

**Solutions**:
1. Check if Streamlit is running: `ps aux | grep streamlit`
2. Verify port availability: `lsof -i :8501`
3. Check logs: `tail -f logs/streamlit.log`
4. Restart the interface: `pkill streamlit && python run_ui.py`

#### Performance Issues

**Problem**: Interface is slow or unresponsive

**Solutions**:
1. Check system resources: `htop` or `top`
2. Reduce trace data size: Clear old traces
3. Optimize queries: Use filters and pagination
4. Increase system resources: More RAM, CPU

#### Authentication Issues

**Problem**: Can't log in or access features

**Solutions**:
1. Check authentication configuration
2. Verify API keys and tokens
3. Clear browser cache and cookies
4. Check user permissions and roles

### Getting Help

- **Interface Logs**: Check `logs/streamlit.log` for detailed error information
- **Browser Console**: Open browser developer tools for client-side errors
- **System Logs**: Check system logs for server-side issues
- **Documentation**: Review this guide and other documentation
- **Support**: Report issues on GitHub or contact support

## Next Steps

- **Read the [API Reference](api.md)** for programmatic access
- **Check the [CLI Reference](cli.md)** for command-line usage
- **Explore the [Examples](../examples/)** for working code samples
- **Review the [Architecture Documentation](architecture.md)** for system design 