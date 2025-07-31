"""
Simple REST API for Decision Layer
"""

import json
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .core import DecisionEngine


class DecisionRequest(BaseModel):
    """Request model for decision execution"""

    input_data: Dict[str, Any] = Field(..., description="Input data for the decision")
    version: Optional[str] = Field(None, description="Specific version to use")
    enable_validation: bool = Field(True, description="Enable input validation")


class DecisionResponse(BaseModel):
    """Response model for decision execution"""

    result: Dict[str, Any] = Field(..., description="Decision result")
    function_id: str = Field(..., description="Function ID")
    version: str = Field(..., description="Version used")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class DeployRequest(BaseModel):
    """Request model for function deployment"""

    function_code: str = Field(..., description="Python function code")
    version: str = Field(..., description="Function version")


class FunctionInfo(BaseModel):
    """Model for function information"""

    function_id: str = Field(..., description="Function ID")
    versions: list[str] = Field(..., description="Available versions")
    latest_version: str = Field(..., description="Latest version")


class APIError(BaseModel):
    """Error response model"""

    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Error details")


class DecisionLayerAPI:
    """REST API for Decision Layer"""

    def __init__(
        self, engine: DecisionEngine, host: str = "localhost", port: int = 8000
    ):
        self.engine = engine
        self.host = host
        self.port = port
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="Decision Layer API",
            description="REST API for Decision Layer - Elegant decision management",
            version="2.0.0",
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

        # Add routes
        self._add_routes(app)

        return app

    def _add_routes(self, app: FastAPI):
        """Add API routes"""

        @app.get("/")
        async def root():
            """API root endpoint"""
            return {
                "message": "Decision Layer API",
                "version": "2.0.0",
                "docs": "/docs",
                "health": "/health",
            }

        @app.get("/health")
        async def health_check():
            """Enhanced health check endpoint"""
            from datetime import datetime

            health = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0.0",
                "components": {},
            }

            # Check storage
            try:
                functions = await self.engine.list_functions()
                health["components"]["storage"] = {
                    "status": "healthy",
                    "functions_count": len(functions),
                }
            except Exception as e:
                health["components"]["storage"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                health["status"] = "degraded"

            # Check plugins
            try:
                plugin_status = {}
                for plugin_type, plugins in self.engine.plugins.items():
                    plugin_status[plugin_type] = {
                        "count": len(plugins),
                        "plugins": [p.name for p in plugins],
                    }
                health["components"]["plugins"] = {
                    "status": "healthy",
                    "details": plugin_status,
                }
            except Exception as e:
                health["components"]["plugins"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                health["status"] = "degraded"

            # Check security
            try:
                security_config = self.engine.security_manager.config
                health["components"]["security"] = {
                    "status": "healthy",
                    "rate_limiting": security_config.enable_rate_limiting,
                    "input_sanitization": security_config.enable_input_sanitization,
                    "trace_sanitization": security_config.enable_trace_sanitization,
                }
            except Exception as e:
                health["components"]["security"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                health["status"] = "degraded"

            return health

        @app.get("/functions", response_model=list[FunctionInfo])
        async def list_functions():
            """List all available functions"""
            try:
                functions = await self.engine.list_functions()
                result = []

                for function_id in functions:
                    versions = await self.engine.list_versions(function_id)
                    latest_version = versions[-1] if versions else "none"

                    result.append(
                        FunctionInfo(
                            function_id=function_id,
                            versions=versions,
                            latest_version=latest_version,
                        )
                    )

                return result
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to list functions: {str(e)}"
                )

        @app.get("/functions/{function_id}/versions")
        async def get_function_versions(function_id: str):
            """Get versions for a specific function"""
            try:
                versions = await self.engine.list_versions(function_id)
                return {
                    "function_id": function_id,
                    "versions": versions,
                    "latest": versions[-1] if versions else None,
                }
            except Exception as e:
                raise HTTPException(
                    status_code=404, detail=f"Function not found: {str(e)}"
                )

        @app.post("/functions/{function_id}/deploy")
        async def deploy_function(function_id: str, request: DeployRequest):
            """Deploy a new function version"""
            try:
                await self.engine.deploy_function(
                    function_id, request.version, request.function_code
                )
                return {
                    "message": "Function deployed successfully",
                    "function_id": function_id,
                    "version": request.version,
                }
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Deployment failed: {str(e)}"
                )

        @app.post("/functions/{function_id}/execute", response_model=DecisionResponse)
        async def execute_function(function_id: str, request: DecisionRequest):
            """Execute a decision function"""
            try:
                import time

                start_time = time.time()

                result = await self.engine.execute(
                    function_id, request.input_data, request.version
                )

                execution_time = (time.time() - start_time) * 1000

                return DecisionResponse(
                    result=result,
                    function_id=function_id,
                    version=request.version or "latest",
                    execution_time_ms=round(execution_time, 2),
                )
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Execution failed: {str(e)}"
                )

        @app.post("/functions/{function_id}/test")
        async def test_function(function_id: str, request: DecisionRequest):
            """Test a decision function with sample data"""
            try:
                # Use provided input or default test data
                test_input = request.input_data or {
                    "amount": 500,
                    "customer_score": 750,
                }

                result = await self.engine.execute(
                    function_id, test_input, request.version
                )

                return {
                    "function_id": function_id,
                    "version": request.version or "latest",
                    "test_input": test_input,
                    "result": result,
                    "status": "success",
                }
            except Exception as e:
                return {
                    "function_id": function_id,
                    "version": request.version or "latest",
                    "test_input": request.input_data,
                    "error": str(e),
                    "status": "error",
                }

        @app.get("/traces/{function_id}")
        async def get_traces(function_id: str, date: Optional[str] = None):
            """Get traces for a function"""
            try:
                from datetime import datetime

                if date is None:
                    date = datetime.now().strftime("%Y%m%d")

                trace_file = f"./traces/{function_id}_{date}.jsonl"

                traces = []
                try:
                    with open(trace_file, "r") as f:
                        for line in f:
                            traces.append(json.loads(line.strip()))
                except FileNotFoundError:
                    return {"function_id": function_id, "date": date, "traces": []}

                return {
                    "function_id": function_id,
                    "date": date,
                    "traces": traces,
                    "count": len(traces),
                }
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to get traces: {str(e)}"
                )

        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            """Global exception handler"""
            return JSONResponse(
                status_code=500,
                content=APIError(
                    error="Internal server error", details=str(exc)
                ).dict(),
            )

    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """Run the API server"""
        host = host or self.host
        port = port or self.port

        uvicorn.run(self.app, host=host, port=port, log_level="info")


def create_api(
    engine: DecisionEngine, host: str = "localhost", port: int = 8000
) -> DecisionLayerAPI:
    """Create a Decision Layer API instance"""
    return DecisionLayerAPI(engine, host, port)


if __name__ == "__main__":
    # Example usage
    engine = DecisionEngine()
    api = create_api(engine)
    api.run()
