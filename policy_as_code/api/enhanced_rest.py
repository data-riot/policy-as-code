"""
REST API Implementation for Policy as Code Platform
FastAPI-based API with OpenAPI 3.0 documentation
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from policy_as_code.core.enhanced_engine import DecisionEngine
from policy_as_code.core.types import DecisionContext, DecisionResult
from policy_as_code.core.security import SecurityConfig, SecurityManager
from policy_as_code.api.graphql_api import create_graphql_router
from policy_as_code.api.websocket_api import WebSocketHandler


# Pydantic models for API
class DecisionRequest(BaseModel):
    """Request model for decision execution"""

    function_id: str = Field(..., description="ID of the decision function")
    version: str = Field(
        default="latest", description="Version of the decision function"
    )
    input_data: Dict[str, Any] = Field(..., description="Input data for the decision")
    trace_id: Optional[str] = Field(
        None, description="Optional trace ID for correlation"
    )


class DecisionResponse(BaseModel):
    """Response model for decision execution"""

    trace_id: str
    function_id: str
    version: str
    result: Dict[str, Any]
    execution_time_ms: int
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float


class FunctionInfo(BaseModel):
    """Information about a registered function"""

    function_id: str
    versions: List[str]
    description: Optional[str] = None


# Initialize FastAPI app
app = FastAPI(
    title="Policy as Code API",
    description="REST API for Policy as Code decision platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global decision engine instance
decision_engine = DecisionEngine(SecurityConfig())

# WebSocket handler
websocket_handler = WebSocketHandler(decision_engine)

# Add GraphQL router
graphql_router = create_graphql_router(decision_engine)
app.include_router(graphql_router)


# Dependency for authentication
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Dependency for user authentication"""
    # Implement proper authentication logic
    # For now, just return a mock user
    return {"user_id": "demo_user", "roles": ["admin"]}


# API Endpoints


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Policy as Code API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    health_data = await decision_engine.health_check()
    return HealthResponse(
        status=health_data["status"],
        timestamp=datetime.now(),
        version="1.0.0",
        uptime_seconds=0.0,  # Implement uptime tracking
    )


@app.post("/decisions", response_model=DecisionResponse)
async def execute_decision(
    request: DecisionRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Execute a decision function"""
    try:
        # Create decision context
        context = DecisionContext(
            function_id=request.function_id,
            version=request.version,
            result=request.input_data,
            timestamp=datetime.now(),
            trace_id=request.trace_id or str(UUID()),
        )

        # Execute decision
        result = await decision_engine.execute_decision(
            function_id=request.function_id,
            version=request.version,
            input_data=request.input_data,
            context=context,
        )

        # Schedule background tasks
        background_tasks.add_task(log_decision_execution, result, current_user)

        return DecisionResponse(
            trace_id=result.trace_id,
            function_id=result.function_id,
            version=result.version,
            result=result.result,
            execution_time_ms=result.execution_time_ms,
            timestamp=result.timestamp,
            success=result.success,
            error_message=result.error_message,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/decisions/{trace_id}", response_model=DecisionResponse)
async def get_decision(trace_id: str, current_user: dict = Depends(get_current_user)):
    """Get a decision result by trace ID"""
    try:
        # This would query the storage backend
        # For now, return a mock response
        raise HTTPException(status_code=501, detail="Not implemented yet")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/functions", response_model=List[FunctionInfo])
async def list_functions(current_user: dict = Depends(get_current_user)):
    """List all registered decision functions"""
    try:
        function_ids = decision_engine.registry.list_functions()
        functions = []

        for func_id in function_ids:
            versions = decision_engine.registry._versions.get(func_id, [])
            functions.append(
                FunctionInfo(
                    function_id=func_id,
                    versions=versions,
                    description=f"Decision function for {func_id}",
                )
            )

        return functions

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/functions/{function_id}/history")
async def get_function_history(
    function_id: str, limit: int = 100, current_user: dict = Depends(get_current_user)
):
    """Get decision history for a specific function"""
    try:
        history = await decision_engine.get_decision_history(function_id, limit)
        return {"function_id": function_id, "history": history}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/functions/{function_id}/register")
async def register_function(
    function_id: str,
    version: str,
    function_code: str,
    current_user: dict = Depends(get_current_user),
):
    """Register a new decision function"""
    try:
        # This would compile and register the function code
        # For now, return a mock response
        raise HTTPException(
            status_code=501, detail="Function registration not implemented yet"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/functions/{function_id}/stats")
async def get_function_stats(
    function_id: str, current_user: dict = Depends(get_current_user)
):
    """Get decision statistics for a function"""
    try:
        stats = await decision_engine.get_decision_stats(function_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trace/integrity")
async def verify_trace_integrity(current_user: dict = Depends(get_current_user)):
    """Verify trace ledger integrity"""
    try:
        integrity = await decision_engine.verify_trace_integrity()
        return integrity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trace/entries")
async def get_trace_entries(
    function_id: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    """Get trace entries"""
    try:
        entries = await decision_engine.get_trace_entries(function_id, limit)
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cleanup/decisions")
async def cleanup_old_decisions(
    retention_days: int = 30, current_user: dict = Depends(get_current_user)
):
    """Clean up decisions older than retention_days"""
    try:
        deleted_count = await decision_engine.cleanup_old_decisions(retention_days)
        return {"deleted_count": deleted_count, "retention_days": retention_days}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_handler.handle_websocket(websocket)


@app.get("/performance/summary")
async def get_performance_summary(current_user: dict = Depends(get_current_user)):
    """Get comprehensive performance summary"""
    try:
        summary = await decision_engine.get_performance_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance/function/{function_id}")
async def get_function_performance(
    function_id: str, current_user: dict = Depends(get_current_user)
):
    """Get performance metrics for a specific function"""
    try:
        performance = await decision_engine.get_function_performance(function_id)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance/alerts")
async def get_active_alerts(current_user: dict = Depends(get_current_user)):
    """Get active performance alerts"""
    try:
        alerts = await decision_engine.get_active_alerts()
        return {"alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Background tasks
async def log_decision_execution(result: DecisionResult, user: dict):
    """Background task to log decision execution"""
    # Implement logging logic
    print(f"Decision executed: {result.trace_id} by user {user['user_id']}")


# Register existing use cases
def register_use_cases():
    """Register the existing use case functions"""
    from examples.demos import (
        healthcare_eligibility,
        social_benefits_allocation,
        immigration_visa_processing,
    )

    # Register healthcare eligibility
    decision_engine.register_function(
        "healthcare_eligibility", "1.0.0", healthcare_eligibility.decision_function
    )

    # Register social benefits allocation
    decision_engine.register_function(
        "social_benefits_allocation",
        "1.0.0",
        social_benefits_allocation.decision_function,
    )

    # Register immigration visa processing
    decision_engine.register_function(
        "immigration_visa_processing",
        "1.0.0",
        immigration_visa_processing.decision_function,
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the API on startup"""
    register_use_cases()
    print("Policy as Code API started successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Policy as Code API shutting down")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
