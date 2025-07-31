# API Reference

The Decision Layer provides a comprehensive REST API for programmatic access to all functionality. The API is built with FastAPI and provides automatic OpenAPI documentation.

## Quick Start

### Start the API Server

```bash
# Start the API server
python run_api.py

# Or using uvicorn directly
uvicorn decision_layer.api:app --host 0.0.0.0 --port 8000
```

### Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Authentication

The API supports multiple authentication methods:

### API Key Authentication

```bash
# Set API key in environment
export DECISION_LAYER_API_KEY=your-secret-key

# Use in requests
curl -H "X-API-Key: your-secret-key" http://localhost:8000/health
```

### Bearer Token Authentication

```bash
# Use Bearer token
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/health
```

## Base URL

All API endpoints are relative to the base URL:

```
http://localhost:8000
```

## Endpoints

### Health Check

#### GET /health

Check the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:00:00Z",
  "version": "2.0.0"
}
```

### Root

#### GET /

Get API information.

**Response:**
```json
{
  "message": "Decision Layer API",
  "version": "2.0.0",
  "docs": "/docs"
}
```

### Functions

#### GET /functions

List all available decision functions.

**Response:**
```json
[
  {
    "function_id": "loan_approval",
    "versions": ["1.0", "1.1", "2.0"],
    "latest_version": "2.0"
  },
  {
    "function_id": "insurance_claim",
    "versions": ["1.0"],
    "latest_version": "1.0"
  }
]
```

#### GET /functions/{function_id}/versions

Get all versions of a specific function.

**Parameters:**
- `function_id` (string, required): The function identifier

**Response:**
```json
{
  "function_id": "loan_approval",
  "versions": ["1.0", "1.1", "2.0"],
  "latest_version": "2.0"
}
```

#### POST /functions/{function_id}/deploy

Deploy a new version of a decision function.

**Parameters:**
- `function_id` (string, required): The function identifier

**Request Body:**
```json
{
  "function_code": "def decision_function(input_data, context):\n    return {'approved': True}",
  "version": "2.0"
}
```

**Response:**
```json
{
  "message": "Function deployed successfully",
  "function_id": "loan_approval",
  "version": "2.0"
}
```

#### POST /functions/{function_id}/execute

Execute a decision function.

**Parameters:**
- `function_id` (string, required): The function identifier

**Request Body:**
```json
{
  "input_data": {
    "credit_score": 750,
    "income": 75000,
    "age": 30
  },
  "version": "2.0",
  "enable_validation": true
}
```

**Response:**
```json
{
  "result": {
    "approved": true,
    "reason": "All criteria met",
    "risk_level": "low"
  },
  "function_id": "loan_approval",
  "version": "2.0",
  "execution_time_ms": 12.5
}
```

#### POST /functions/{function_id}/test

Test a decision function with validation.

**Parameters:**
- `function_id` (string, required): The function identifier

**Request Body:**
```json
{
  "input_data": {
    "credit_score": 650,
    "income": 45000,
    "age": 25
  },
  "version": "2.0"
}
```

**Response:**
```json
{
  "result": {
    "approved": false,
    "reason": "Credit score below minimum requirement",
    "risk_level": "high"
  },
  "validation_passed": true,
  "execution_time_ms": 8.2
}
```

### Traces

#### GET /traces/{function_id}

Get execution traces for a function.

**Parameters:**
- `function_id` (string, required): The function identifier
- `date` (string, optional): Date in YYYYMMDD format (defaults to today)

**Response:**
```json
{
  "function_id": "loan_approval",
  "date": "20250127",
  "traces": [
    {
      "trace_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2025-01-27T10:00:00Z",
      "input_hash": "0x4f...",
      "output_hash": "0xe9...",
      "status": "success",
      "execution_time_ms": 12.5
    }
  ],
  "total_traces": 1
}
```

### Cross-Domain Integration

#### POST /cross-domain/query

Process a natural language query with cross-domain enrichment.

**Request Body:**
```json
{
  "query": "What are the risk factors for user 123?",
  "context": {
    "user_id": "123",
    "time_range": {
      "start": "2025-01-01",
      "end": "2025-01-27"
    }
  },
  "include_cross_domain": true,
  "format": "natural"
}
```

**Response:**
```json
{
  "query": "What are the risk factors for user 123?",
  "intent": {
    "intent_type": "risk_analysis",
    "entities": ["user_123"],
    "confidence": 0.95
  },
  "primary_response": {
    "risk_score": 0.3,
    "risk_factors": ["new_account", "high_transaction_volume"]
  },
  "ontology_context": {
    "entity_type": "User",
    "properties": {
      "account_age": 30,
      "transaction_count": 45
    }
  },
  "knowledge_graph_context": {
    "related_entities": ["account_456", "transaction_789"],
    "risk_indicators": ["suspicious_pattern", "unusual_amount"]
  },
  "llm_explanation": "User 123 shows moderate risk due to being a new account holder with high transaction volume.",
  "format": "natural"
}
```

#### POST /cross-domain/explain

Explain a decision function for different audiences.

**Request Body:**
```json
{
  "function_id": "loan_approval",
  "version": "2.0",
  "audience": "user",
  "format": "natural",
  "include_context": true
}
```

**Response:**
```json
{
  "function_id": "loan_approval",
  "version": "2.0",
  "explanation": "This decision function evaluates loan applications based on credit score, income, and age. It approves loans for applicants who meet all criteria.",
  "audience": "user",
  "format": "natural",
  "context": {
    "policy_references": ["POL-001", "POL-002"],
    "compliance_requirements": ["SOX", "GDPR"]
  }
}
```

#### POST /cross-domain/generate

Generate a decision function from natural language description.

**Request Body:**
```json
{
  "policy_description": "Approve insurance claims for amounts under $1000 with valid documentation",
  "function_id": "insurance_claim_auto",
  "version": "1.0",
  "metadata": {
    "author": "llm-system",
    "tags": ["insurance", "claims", "auto-generated"]
  }
}
```

**Response:**
```json
{
  "function_id": "insurance_claim_auto",
  "version": "1.0",
  "artifact": {
    "logic_code": "def decision_function(input_data, context):\n    # Generated logic...",
    "schema": {
      "input_schema": {...},
      "output_schema": {...}
    },
    "metadata": {
      "title": "Insurance Claim Approval",
      "description": "Auto-generated from policy description",
      "author": "llm-system"
    }
  },
  "generation_metadata": {
    "model_used": "gpt-4",
    "confidence": 0.92,
    "generation_time_ms": 1500
  }
}
```

### Shadow Testing

#### POST /shadow/simulation

Run shadow simulation to test new versions against historical data.

**Request Body:**
```json
{
  "function_id": "loan_approval",
  "current_version": "1.0",
  "shadow_version": "2.0",
  "inputs": [
    {
      "credit_score": 750,
      "income": 75000,
      "age": 30
    },
    {
      "credit_score": 650,
      "income": 45000,
      "age": 25
    }
  ]
}
```

**Response:**
```json
{
  "function_id": "loan_approval",
  "current_version": "1.0",
  "shadow_version": "2.0",
  "total_tests": 2,
  "identical_results": 1,
  "different_results": 1,
  "errors": 0,
  "regressions": [],
  "improvements": [
    {
      "input_hash": "0x4f...",
      "diff_summary": {
        "changed_fields": ["approved"],
        "current_value": false,
        "shadow_value": true
      }
    }
  ],
  "confidence": {
    "identical_ratio": 0.5,
    "regression_ratio": 0.0,
    "improvement_ratio": 0.5
  }
}
```

#### POST /shadow/mirror

Run shadow mirroring on live traffic.

**Request Body:**
```json
{
  "function_id": "loan_approval",
  "current_version": "1.0",
  "shadow_version": "2.0",
  "input_data": {
    "credit_score": 750,
    "income": 75000,
    "age": 30
  }
}
```

**Response:**
```json
{
  "input_hash": "0x4f...",
  "current_output": {
    "approved": true,
    "reason": "All criteria met"
  },
  "shadow_output": {
    "approved": true,
    "reason": "All criteria met",
    "confidence": 0.95
  },
  "current_version": "1.0",
  "shadow_version": "2.0",
  "execution_time_ms": 15.2,
  "has_differences": false,
  "diff_summary": {
    "status": "identical"
  }
}
```

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "details": {
      "field": "credit_score",
      "issue": "Value must be between 300 and 850"
    }
  }
}
```

### Common Error Codes

- `VALIDATION_ERROR` - Input validation failed
- `FUNCTION_NOT_FOUND` - Function or version not found
- `EXECUTION_ERROR` - Function execution failed
- `DEPLOYMENT_ERROR` - Function deployment failed
- `STORAGE_ERROR` - Storage operation failed
- `AUTHENTICATION_ERROR` - Authentication failed
- `RATE_LIMIT_ERROR` - Rate limit exceeded

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default**: 100 requests per minute per client
- **Configurable**: Can be adjusted in configuration
- **Headers**: Rate limit information included in response headers

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1643270400
```

## Pagination

For endpoints that return lists, pagination is supported:

### Query Parameters

- `page` (integer, optional): Page number (default: 1)
- `size` (integer, optional): Page size (default: 20, max: 100)

### Response Format

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 150,
    "pages": 8
  }
}
```

## SDK Examples

### Python SDK

```python
import requests

# Base configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your-secret-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Execute a decision
def execute_decision(function_id, input_data, version=None):
    url = f"{BASE_URL}/functions/{function_id}/execute"
    payload = {
        "input_data": input_data,
        "version": version
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()

# Example usage
result = execute_decision(
    function_id="loan_approval",
    input_data={
        "credit_score": 750,
        "income": 75000,
        "age": 30
    },
    version="2.0"
)

print(f"Decision: {result['result']}")
```

### JavaScript/Node.js SDK

```javascript
const axios = require('axios');

// Base configuration
const BASE_URL = 'http://localhost:8000';
const API_KEY = 'your-secret-key';

const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
});

// Execute a decision
async function executeDecision(functionId, inputData, version = null) {
    try {
        const response = await api.post(`/functions/${functionId}/execute`, {
            input_data: inputData,
            version: version
        });
        
        return response.data;
    } catch (error) {
        console.error('API Error:', error.response?.data || error.message);
        throw error;
    }
}

// Example usage
executeDecision('loan_approval', {
    credit_score: 750,
    income: 75000,
    age: 30
}, '2.0')
.then(result => {
    console.log('Decision:', result.result);
})
.catch(error => {
    console.error('Failed to execute decision:', error);
});
```

### cURL Examples

```bash
# Execute a decision
curl -X POST "http://localhost:8000/functions/loan_approval/execute" \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "credit_score": 750,
      "income": 75000,
      "age": 30
    },
    "version": "2.0"
  }'

# List all functions
curl -X GET "http://localhost:8000/functions" \
  -H "X-API-Key: your-secret-key"

# Get traces
curl -X GET "http://localhost:8000/traces/loan_approval?date=20250127" \
  -H "X-API-Key: your-secret-key"
```

## WebSocket Support

For real-time updates, the API supports WebSocket connections:

```python
import websockets
import json

async def connect_websocket():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Subscribe to function updates
        await websocket.send(json.dumps({
            "action": "subscribe",
            "channel": "function_updates"
        }))
        
        # Listen for updates
        async for message in websocket:
            data = json.loads(message)
            print(f"Update: {data}")
```

## Monitoring and Observability

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

### Logging

The API logs all requests and responses for monitoring and debugging:

- **Access logs**: HTTP requests and responses
- **Error logs**: Detailed error information
- **Performance logs**: Execution time and resource usage
- **Audit logs**: Security and compliance events

## Configuration

API configuration can be customized through environment variables:

```bash
# Server configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Security
DECISION_LAYER_API_KEY=your-secret-key
ENABLE_AUTH=true

# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/api.log
```

## Next Steps

- **Explore the [CLI Reference](cli.md)** for command-line usage
- **Check the [Web Interface Guide](web-interface.md)** for visual tools
- **Review the [Architecture Documentation](architecture.md)** for system design
- **See the [Examples](../examples/)** for working code samples 