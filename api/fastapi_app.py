from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json
import os
from datetime import datetime

from decision_layer.entities import Order, Customer
from decision_layer.dsl_loader import load_yaml_policy_with_schema, create_schema_from_example
from decision_layer.executor import DecisionExecutor
from decision_layer.registry import DecisionRegistry
from decision_layer.trace_sink import FileSink
from decision_layer.shadow_runner import ShadowRunner

# Pydantic models for API input validation
class CustomerInput(BaseModel):
    id: str = Field(..., description="Customer ID")
    signup_date: str = Field(..., description="ISO format date string")
    status: str = Field(..., description="Customer status")

class OrderInput(BaseModel):
    id: str = Field(..., description="Order ID")
    customer: CustomerInput = Field(..., description="Customer information")
    order_date: str = Field(..., description="ISO format date string")
    delivery_date: str = Field(..., description="ISO format date string")
    issue: str = Field(..., description="Issue type")

class DecisionRequest(BaseModel):
    input: OrderInput = Field(..., description="Input data")
    version: Optional[str] = Field(None, description="Specific version to use")
    enable_validation: bool = Field(True, description="Enable schema validation")

class DecisionResponse(BaseModel):
    output: Dict[str, Any] = Field(..., description="Decision output")
    function_id: str = Field(..., description="Function ID")
    version: str = Field(..., description="Version used")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    invocation_id: str = Field(..., description="Unique invocation ID")

class ShadowRequest(BaseModel):
    input: OrderInput = Field(..., description="Input data")
    current_version: str = Field(..., description="Current version")
    shadow_version: str = Field(..., description="Shadow version to test")

class ShadowResponse(BaseModel):
    has_differences: bool = Field(..., description="Whether outputs differ")
    current_output: Dict[str, Any] = Field(..., description="Current version output")
    shadow_output: Dict[str, Any] = Field(..., description="Shadow version output")
    diff_summary: Dict[str, Any] = Field(..., description="Difference summary")

class FunctionInfo(BaseModel):
    function_id: str = Field(..., description="Function ID")
    version: str = Field(..., description="Version")
    description: Optional[str] = Field(None, description="Description")
    author: Optional[str] = Field(None, description="Author")
    tags: List[str] = Field(default_factory=list, description="Tags")

app = FastAPI(
    title="Decision Layer API", 
    version="2.0.0",
    description="Decision layer with schema validation and shadow running"
)

# Global setup
registry = DecisionRegistry()
trace_sink = FileSink("traces/api_trace_log.jsonl")
executor = DecisionExecutor(registry, trace_sink, caller="api")
shadow_runner = ShadowRunner(registry, trace_sink, caller="api-shadow")

# Load and register policies
def load_policies():
    """Load policies from the policies directory"""
    policy_dir = "policies"
    if not os.path.exists(policy_dir):
        return
    
    for filename in os.listdir(policy_dir):
        if filename.endswith(('.yaml', '.yml')):
            policy_path = os.path.join(policy_dir, filename)
            try:
                policy_fn, schema = load_yaml_policy_with_schema(policy_path)
                function_id = filename.replace('.yaml', '').replace('.yml', '')
                
                if schema:
                    registry.register(
                        function_id=function_id,
                        version=schema.version,
                        logic=policy_fn,
                        schema=schema,
                        description=schema.description
                    )
                else:
                    # Create basic schema for backward compatibility
                    basic_schema = create_schema_from_example(
                        input_example={"id": "test", "issue": "test"},
                        output_example={"refund": 0, "reason": "test"},
                        function_id=function_id,
                        version="v1.0"
                    )
                    registry.register(
                        function_id=function_id,
                        version="v1.0",
                        logic=policy_fn,
                        schema=basic_schema
                    )
            except Exception as e:
                print(f"Warning: Could not load {filename}: {e}")

# Load policies on startup
load_policies()

def convert_to_dataclass(input_data: OrderInput) -> Order:
    """Convert Pydantic model to dataclass"""
    customer = Customer(
        id=input_data.customer.id,
        signup_date=datetime.fromisoformat(input_data.customer.signup_date),
        status=input_data.customer.status
    )
    return Order(
        id=input_data.id,
        customer=customer,
        order_date=datetime.fromisoformat(input_data.order_date),
        delivery_date=datetime.fromisoformat(input_data.delivery_date),
        issue=input_data.issue
    )

@app.get("/")
def root():
    """API root endpoint"""
    return {
        "message": "Decision Layer API",
        "version": "2.0.0",
        "features": [
            "Schema validation",
            "Shadow running",
            "Version management",
            "Structured tracing"
        ]
    }

@app.get("/functions", response_model=List[FunctionInfo])
def list_functions():
    """List all registered decision functions"""
    functions = []
    for function_id in registry.list_functions():
        latest = registry.get_latest(function_id)
        if latest:
            functions.append(FunctionInfo(
                function_id=function_id,
                version=latest.version,
                description=latest.description,
                author=latest.author,
                tags=latest.tags
            ))
    return functions

@app.get("/functions/{function_id}/versions")
def list_versions(function_id: str):
    """List all versions of a function"""
    versions = registry.list_versions(function_id)
    return {
        "function_id": function_id,
        "versions": versions,
        "latest": registry._latest_versions.get(function_id)
    }

@app.get("/functions/{function_id}/schema")
def get_schema(function_id: str, version: Optional[str] = None):
    """Get schema for a function"""
    schema = registry.get_schema(function_id, version)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema not found for {function_id}")
    
    return {
        "function_id": function_id,
        "version": schema.version,
        "input_schema": {
            name: {
                "type": field.type.value,
                "required": field.required,
                "description": field.description,
                "default": field.default,
                "enum_values": field.enum_values,
                "min_value": field.min_value,
                "max_value": field.max_value,
                "pattern": field.pattern
            }
            for name, field in schema.input_schema.items()
        },
        "output_schema": {
            name: {
                "type": field.type.value,
                "required": field.required,
                "description": field.description,
                "default": field.default,
                "enum_values": field.enum_values,
                "min_value": field.min_value,
                "max_value": field.max_value,
                "pattern": field.pattern
            }
            for name, field in schema.output_schema.items()
        }
    }

@app.post("/decide/{function_id}", response_model=DecisionResponse)
def decide(function_id: str, request: DecisionRequest):
    """Execute a decision function"""
    try:
        order = convert_to_dataclass(request.input)
        
        result = executor.run(
            function_id=function_id,
            version=request.version,
            input_obj=order,
            enable_validation=request.enable_validation
        )
        
        # Get function info for response
        func = registry.get(function_id, request.version)
        version_used = func.version if func else request.version or "unknown"
        
        return DecisionResponse(
            output=result,
            function_id=function_id,
            version=version_used,
            execution_time_ms=0,  # Would be available from executor
            invocation_id="generated"  # Would be available from executor
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/shadow/{function_id}", response_model=ShadowResponse)
def shadow_decide(function_id: str, request: ShadowRequest):
    """Run shadow analysis for a decision function"""
    try:
        order = convert_to_dataclass(request.input)
        
        result = shadow_runner.run_mirror(
            function_id=function_id,
            current_version=request.current_version,
            shadow_version=request.shadow_version,
            input_data=order
        )
        
        return ShadowResponse(
            has_differences=result.has_differences,
            current_output=result.current_output,
            shadow_output=result.shadow_output,
            diff_summary=result.diff_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/validate/{function_id}")
def validate_input(function_id: str, request: DecisionRequest):
    """Validate input against function schema without executing"""
    try:
        order = convert_to_dataclass(request.input)
        
        validated = executor.validate_only(
            function_id=function_id,
            version=request.version,
            input_obj=order
        )
        
        return {
            "valid": True,
            "validated_input": validated,
            "function_id": function_id,
            "version": request.version
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "function_id": function_id,
            "version": request.version
        }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "functions_registered": len(registry.list_functions())
    }