#!/usr/bin/env python3
"""
Simple API Server for Policy as Code
Provides REST API for decision function execution
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import importlib.util
import traceback
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("❌ FastAPI not installed. Install with: pip install fastapi uvicorn")
    print("   Or install production dependencies: pip install -e .[production]")
    sys.exit(1)


# Pydantic models
class DecisionRequest(BaseModel):
    function_id: str = Field(..., description="ID of the decision function")
    input_data: Dict[str, Any] = Field(..., description="Input data for the decision")
    version: Optional[str] = Field(
        None, description="Function version (default: latest)"
    )


class DecisionResponse(BaseModel):
    function_id: str
    version: str
    result: Dict[str, Any]
    execution_time_ms: float
    timestamp: str


class FunctionInfo(BaseModel):
    function_id: str
    version: str
    function_name: str
    file_path: str
    deployed_at: str


class HealthResponse(BaseModel):
    status: str
    version: str
    functions_count: int
    uptime: str


# Global variables
app = FastAPI(
    title="Policy as Code API",
    description="REST API for executing decision functions",
    version="2.0.0",
)

start_time = datetime.now()


def load_function_from_registry(
    function_id: str, version: Optional[str] = None
) -> tuple:
    """Load a function from the registry"""
    registry_dir = Path("registry")
    if not registry_dir.exists():
        raise HTTPException(
            status_code=404,
            detail="Registry not found. Run 'policy-as-code init' first.",
        )

    # Look for function files
    pattern = (
        f"{function_id}_*.json" if not version else f"{function_id}_{version}.json"
    )
    registry_files = list(registry_dir.glob(pattern))

    if not registry_files:
        available_functions = []
        for file in registry_dir.glob("*.json"):
            func_name = file.stem.split("_")[0]
            if func_name not in available_functions:
                available_functions.append(func_name)

        raise HTTPException(
            status_code=404,
            detail=f"Function {function_id} not found. Available functions: {available_functions}",
        )

    # Use latest version if not specified
    if not version:
        registry_file = max(registry_files, key=lambda f: f.stat().st_mtime)
    else:
        registry_file = registry_dir / f"{function_id}_{version}.json"
        if not registry_file.exists():
            raise HTTPException(status_code=404, detail=f"Version {version} not found.")

    # Load registry entry
    with open(registry_file, "r") as f:
        registry_entry = json.load(f)

    # Load function module
    func_path = Path(registry_entry["file_path"])
    spec = importlib.util.spec_from_file_location(function_id, func_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    func = getattr(module, registry_entry["function_name"])
    return func, registry_entry


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Policy as Code API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    registry_dir = Path("registry")
    functions_count = (
        len(list(registry_dir.glob("*.json"))) if registry_dir.exists() else 0
    )

    uptime = str(datetime.now() - start_time)

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        functions_count=functions_count,
        uptime=uptime,
    )


@app.post("/execute", response_model=DecisionResponse)
async def execute_decision(request: DecisionRequest):
    """Execute a decision function"""
    start_time_exec = datetime.now()

    try:
        # Load function
        func, registry_entry = load_function_from_registry(
            request.function_id, request.version
        )

        # Execute function
        result = func(request.input_data)

        # Calculate execution time
        execution_time = (datetime.now() - start_time_exec).total_seconds() * 1000

        return DecisionResponse(
            function_id=request.function_id,
            version=registry_entry["version"],
            result=result,
            execution_time_ms=execution_time,
            timestamp=datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@app.get("/functions", response_model=list[FunctionInfo])
async def list_functions():
    """List all deployed functions"""
    registry_dir = Path("registry")
    if not registry_dir.exists():
        return []

    functions = []
    registry_files = list(registry_dir.glob("*.json"))

    for file in registry_files:
        with open(file, "r") as f:
            entry = json.load(f)

        functions.append(
            FunctionInfo(
                function_id=entry["function_id"],
                version=entry["version"],
                function_name=entry["function_name"],
                file_path=entry["file_path"],
                deployed_at=entry["deployed_at"],
            )
        )

    return functions


@app.get("/functions/{function_id}", response_model=FunctionInfo)
async def get_function_info(function_id: str, version: Optional[str] = None):
    """Get information about a specific function"""
    try:
        _, registry_entry = load_function_from_registry(function_id, version)

        return FunctionInfo(
            function_id=registry_entry["function_id"],
            version=registry_entry["version"],
            function_name=registry_entry["function_name"],
            file_path=registry_entry["file_path"],
            deployed_at=registry_entry["deployed_at"],
        )
    except HTTPException:
        raise


@app.get("/functions/{function_id}/versions", response_model=list[str])
async def get_function_versions(function_id: str):
    """Get all versions of a function"""
    registry_dir = Path("registry")
    if not registry_dir.exists():
        raise HTTPException(status_code=404, detail="Registry not found")

    pattern = f"{function_id}_*.json"
    registry_files = list(registry_dir.glob(pattern))

    if not registry_files:
        raise HTTPException(status_code=404, detail=f"Function {function_id} not found")

    versions = []
    for file in registry_files:
        with open(file, "r") as f:
            entry = json.load(f)
        versions.append(entry["version"])

    return sorted(versions)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url),
        },
    )


def main():
    """Main function to run the API server"""
    import argparse

    parser = argparse.ArgumentParser(description="Policy as Code API Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print("🚀 Starting Policy as Code API Server")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Docs: http://{args.host}:{args.port}/docs")
    print(f"   Health: http://{args.host}:{args.port}/health")
    print("   Press Ctrl+C to stop")

    uvicorn.run(
        "policy_as_code.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info",
    )


if __name__ == "__main__":
    main()
