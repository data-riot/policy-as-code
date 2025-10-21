# AI Assistant Development Guide

This document helps AI assistants understand and work effectively with this decision layer codebase.

## 🏗️ Architecture Overview

### Core Components
- **`policy_as_code/core/`** - Decision engine, context, and registry
- **`policy_as_code/api/`** - REST API, agentic endpoints, and audit
- **`policy_as_code/ai/`** - LLM integration, workflow, and monitoring
- **`policy_as_code/security/`** - Authentication, KMS, and replay protection
- **`policy_as_code/governance/`** - Audit service, release management, legal refs
- **`policy_as_code/tracing/`** - Immutable trace ledger and schema

### Key Patterns

#### Decision Functions
```python
def decision_name(context: DecisionContext) -> DecisionResult:
    """Decision function following the decision layer pattern."""
    try:
        # Extract input data
        input_data = context.get('key', default_value)

        # Implement decision logic
        # ... decision logic ...

        # Return result
        return DecisionResult(
            decision='outcome',
            confidence=0.95,
            reasoning='explanation',
            metadata={}
        )
    except Exception as e:
        raise DecisionError(f"Failed to process decision: {e}")
```

#### API Endpoints
```python
@app.post('/endpoint')
async def endpoint_name(request_data: RequestModel):
    """API endpoint following the decision layer pattern."""
    try:
        # Create decision context
        context = DecisionContext({
            'key': request_data.field,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Process decision
        result = await decision_function(context)

        # Return response
        return ResponseModel(success=True, result=result)
    except DecisionError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## 🧪 Testing Patterns

### Test Structure
```python
def test_function_name():
    """Test function following arrange-act-assert pattern."""
    # Arrange
    context = DecisionContext({'key': 'value'})

    # Act
    result = decision_function(context)

    # Assert
    assert result.decision == 'expected'
    assert result.confidence > 0.8
```

## 🔧 Development Workflow

### Quality Gates
1. **Format**: Black (88 chars)
2. **Lint**: Flake8
3. **Type**: MyPy
4. **Test**: Pytest
5. **Security**: Bandit

### Pre-commit Hooks
- Automatic formatting
- Linting
- Type checking
- Test execution

## 📚 Key Files for AI Understanding

### Architecture
- `docs/architecture/architecture.md` - Overall architecture
- `docs/architecture/governance.md` - Governance patterns
- `docs/architecture/security.md` - Security model

### API Reference
- `docs/reference/openapi.json` - API specification
- `docs/reference/api.md` - API documentation

### Examples
- `examples/policies/approval_decision.yaml` - Policy example
- `examples/demos/comprehensive_demo.py` - Demo implementation

### Configuration
- `pyproject.toml` - Project configuration
- `requirements.txt` - Dependencies
- `requirements-dev.txt` - Development dependencies

## 🎯 AI Assistant Best Practices

### Code Generation
1. Use the provided snippets (`ai_decision_func`, `ai_api_endpoint`)
2. Follow the decision layer patterns
3. Include proper error handling
4. Add comprehensive docstrings
5. Use type hints

### Testing
1. Write tests for all new functionality
2. Use arrange-act-assert pattern
3. Test both success and error cases
4. Mock external dependencies

### Quality
1. Ensure code passes all quality gates
2. Use consistent naming conventions
3. Follow the established architecture
4. Document complex logic

## 🚀 Quick Commands

### VS Code Tasks
- `AI Codebase Analysis` - Validate imports and modules
- `AI Decision Function Test` - Test decision layer components
- `AI Architecture Validation` - Check architecture structure
- `Run All Quality Checks` - Complete quality pipeline

### Debugging
- `Python: Decision Layer API` - Debug API server
- `Python: Run Tests` - Debug test execution
- `Python: Current File` - Debug any file

## 📝 Notes for AI Assistants

- This is a production-grade governance platform
- Focus on maintainability and testability
- Follow the established patterns
- Consider security implications
- Maintain audit trails
- Use structured logging
