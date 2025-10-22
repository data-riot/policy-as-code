"""
REST API Implementation for Policy as Code Platform
FastAPI-based API with OpenAPI 3.0 documentation
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID
import json
import hashlib
import time
import logging

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    BackgroundTasks,
    WebSocket,
    Request,
    Header,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from policy_as_code.core.enhanced_engine import DecisionEngine
from policy_as_code.core.types import DecisionContext, DecisionResult
from policy_as_code.core.security import SecurityConfig, SecurityManager
from policy_as_code.api.graphql_api import create_graphql_router
from policy_as_code.api.websocket_api import WebSocketHandler
from policy_as_code.security.kms_integration import KMSManager, create_kms_manager
from policy_as_code.validation.eli_validator import (
    ELIValidator,
    ELIValidationStatus,
    validate_decision_function_eli,
)
from policy_as_code.audit.audit_replay_api import (
    create_audit_replay_api,
    AuditReplayAPI,
)

# Configure logging
logger = logging.getLogger(__name__)


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


class ReleaseRequest(BaseModel):
    """Request model for releasing a decision function"""

    df_id: str = Field(..., description="Decision function ID")
    version: str = Field(..., description="Version to release")
    effective_from: datetime = Field(
        ..., description="When the release becomes effective"
    )
    sunset_date: Optional[datetime] = Field(
        None, description="When the release expires"
    )
    change_summary: str = Field(..., description="Summary of changes")
    signatures: List[Dict[str, str]] = Field(..., description="Required signatures")


class ReleaseResponse(BaseModel):
    """Response model for release operations"""

    release_id: str
    df_id: str
    version: str
    status: str
    effective_from: datetime
    sunset_date: Optional[datetime]
    created_at: datetime


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

# Initialize KMS manager (configure based on environment)
kms_config = {
    "provider": "local",  # Change to "aws" or "gcp" in production
    "region": "eu-west-1",  # For AWS
    "project_id": "policy-as-code",  # For GCP
}
kms_manager = create_kms_manager(kms_config["provider"], kms_config)

# Initialize Audit Replay API
audit_replay_api = create_audit_replay_api(
    decision_engine, decision_engine.trace_ledger
)

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
    x_road_client: str = Header(
        ..., alias="X-ROAD-CLIENT", description="X-Road client identifier"
    ),
    x_request_nonce: str = Header(
        ..., alias="X-REQUEST-NONCE", description="Request nonce for replay protection"
    ),
    current_user: dict = Depends(get_current_user),
):
    """Execute a decision function with X-Road integration and idempotency"""
    try:
        # Validate X-Road client format
        if not x_road_client.startswith("xroad:FI/ORG/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid X-ROAD-CLIENT format. Expected: xroad:FI/ORG/...",
            )

        # Check idempotency
        idempotency_key = get_idempotency_key(request, x_road_client)
        if idempotency_key in idempotency_cache:
            cached_result = idempotency_cache[idempotency_key]
            # Check if cache entry is still valid (5 minutes TTL)
            if time.time() - cached_result["timestamp"] < 300:
                return cached_result["response"]

        # Create decision context
        input_hash = hashlib.sha256(
            json.dumps(request.input_data, sort_keys=True).encode()
        ).hexdigest()
        context = DecisionContext(
            function_id=request.function_id,
            version=request.version,
            input_hash=input_hash,
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

        # Create response
        response = DecisionResponse(
            trace_id=result.trace_id,
            function_id=result.function_id,
            version=result.version,
            result=result.result,
            execution_time_ms=result.execution_time_ms,
            timestamp=result.timestamp,
            success=result.success,
            error_message=result.error_message,
        )

        # Cache for idempotency
        idempotency_cache[idempotency_key] = {
            "response": response,
            "timestamp": time.time(),
        }

        # Schedule background tasks
        background_tasks.add_task(
            log_decision_execution, result, current_user, x_road_client, x_request_nonce
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_idempotency_key(request: DecisionRequest, x_road_client: str) -> str:
    """Generate idempotency key from request"""
    key_data = f"{x_road_client}:{request.function_id}:{request.version}:{hashlib.sha256(str(request.input_data).encode()).hexdigest()}"
    return hashlib.sha256(key_data.encode()).hexdigest()


# Global idempotency cache (in production, use Redis)
idempotency_cache: Dict[str, Dict[str, Any]] = {}


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


# Registry API endpoints
@app.post("/registry/df")
async def register_decision_function(
    spec: Dict[str, Any], current_user: dict = Depends(get_current_user)
):
    """Register a new decision function with ELI validation"""
    try:
        # Validate required fields
        required_fields = ["id", "version", "status", "law_reference", "owner"]
        for field in required_fields:
            if field not in spec:
                raise HTTPException(
                    status_code=400, detail=f"Missing required field: {field}"
                )

        # Validate ELI reference
        law_reference = spec.get("law_reference", {})
        eli_uri = law_reference.get("eli")

        if not eli_uri:
            raise HTTPException(
                status_code=400, detail="Decision function must have law_reference.eli"
            )

        # Comprehensive ELI validation
        try:
            eli_results = await validate_decision_function_eli(spec)

            # Check if any ELI validation failed
            invalid_results = [
                result
                for result in eli_results.values()
                if result.status != ELIValidationStatus.VALID
            ]

            if invalid_results:
                error_details = []
                for result in invalid_results:
                    error_details.append(f"{result.eli_uri}: {result.error_message}")

                raise HTTPException(
                    status_code=400,
                    detail=f"ELI validation failed: {'; '.join(error_details)}",
                )

            # Log successful ELI validation for audit
            logger.info(f"ELI validation passed for {spec['id']} v{spec['version']}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"ELI validation error for {spec['id']}: {e}")
            raise HTTPException(
                status_code=500, detail=f"ELI validation service error: {str(e)}"
            )

        # Store the decision function specification
        await decision_engine.storage_backend.store_function_spec(
            spec["id"], spec["version"], spec
        )

        return {"message": "Decision function registered", "spec": spec}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/registry/df/{df_id}")
async def get_decision_function_versions(
    df_id: str, current_user: dict = Depends(get_current_user)
):
    """Get all versions of a decision function"""
    try:
        versions = decision_engine.registry._versions.get(df_id, [])
        if not versions:
            raise HTTPException(
                status_code=404, detail=f"Decision function {df_id} not found"
            )

        return {
            "df_id": df_id,
            "versions": versions,
            "latest": versions[-1] if versions else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")


@app.get("/registry/df/{df_id}/{version}")
async def get_decision_function_spec(
    df_id: str, version: str, current_user: dict = Depends(get_current_user)
):
    """Get specific version of decision function specification"""
    try:
        # Load DecisionFunctionSpec from storage
        spec_data = await decision_engine.storage_backend.retrieve_function_spec(
            df_id, version
        )
        if not spec_data:
            raise HTTPException(
                status_code=404, detail=f"Version {version} of {df_id} not found"
            )

        return spec_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get spec: {str(e)}")


@app.post("/registry/releases", response_model=ReleaseResponse)
async def create_release(
    release_request: ReleaseRequest, current_user: dict = Depends(get_current_user)
):
    """Create a new release for a decision function"""
    try:
        # Validate ELI reference exists
        spec_data = await decision_engine.storage_backend.retrieve_function_spec(
            release_request.df_id, release_request.version
        )
        if not spec_data:
            raise HTTPException(
                status_code=404,
                detail=f"Decision function {release_request.df_id} v{release_request.version} not found",
            )

        # Validate law_reference.eli exists
        law_reference = spec_data.get("law_reference", {})
        eli_uri = law_reference.get("eli")

        if not eli_uri:
            raise HTTPException(
                status_code=400, detail="Decision function must have law_reference.eli"
            )

        # Comprehensive ELI validation
        try:
            eli_results = await validate_decision_function_eli(spec_data)

            # Check if any ELI validation failed
            invalid_results = [
                result
                for result in eli_results.values()
                if result.status != ELIValidationStatus.VALID
            ]

            if invalid_results:
                error_details = []
                for result in invalid_results:
                    error_details.append(f"{result.eli_uri}: {result.error_message}")

                raise HTTPException(
                    status_code=400,
                    detail=f"ELI validation failed: {'; '.join(error_details)}",
                )

            # Log successful ELI validation for audit
            logger.info(
                f"ELI validation passed for {release_request.df_id} v{release_request.version}"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"ELI validation error for {release_request.df_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"ELI validation service error: {str(e)}"
            )

        # Validate signatures (minimum 2)
        if len(release_request.signatures) < 2:
            raise HTTPException(
                status_code=400, detail="At least 2 signatures required"
            )

        # Validate signatures using KMS
        validation_results = await kms_manager.validate_signatures(spec_data)
        invalid_signatures = [
            kid for kid, valid in validation_results.items() if not valid
        ]

        if invalid_signatures:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid signatures for keys: {', '.join(invalid_signatures)}",
            )

        # Create release record
        release_id = f"{release_request.df_id}_{release_request.version}_{int(release_request.effective_from.timestamp())}"

        release_data = {
            "release_id": release_id,
            "df_id": release_request.df_id,
            "version": release_request.version,
            "status": "PENDING",
            "effective_from": release_request.effective_from,
            "sunset_date": release_request.sunset_date,
            "change_summary": release_request.change_summary,
            "signatures": release_request.signatures,
            "created_at": datetime.utcnow(),
            "created_by": current_user.get("user_id", "unknown"),
        }

        # Store release
        decision_engine.storage_backend.store_release(release_data)

        return ReleaseResponse(
            release_id=release_id,
            df_id=release_request.df_id,
            version=release_request.version,
            status="PENDING",
            effective_from=release_request.effective_from,
            sunset_date=release_request.sunset_date,
            created_at=release_data["created_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create release: {str(e)}"
        )


@app.get("/registry/releases")
async def list_releases(
    df_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """List releases with optional filtering"""
    try:
        releases = await decision_engine.storage_backend.get_releases(df_id, status)
        return {"releases": releases, "total": len(releases)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list releases: {str(e)}"
        )


@app.post("/registry/releases/{release_id}/activate")
async def activate_release(
    release_id: str, current_user: dict = Depends(get_current_user)
):
    """Activate a pending release"""
    try:
        # Get release data
        release_data = await decision_engine.storage_backend.get_release(release_id)
        if not release_data:
            raise HTTPException(
                status_code=404, detail=f"Release {release_id} not found"
            )

        if release_data["status"] != "PENDING":
            raise HTTPException(
                status_code=400, detail=f"Release {release_id} is not pending"
            )

        # Update status to ACTIVE
        release_data["status"] = "ACTIVE"
        release_data["activated_at"] = datetime.utcnow()
        release_data["activated_by"] = current_user.get("user_id", "unknown")

        await decision_engine.storage_backend.update_release(release_id, release_data)

        return {"message": f"Release {release_id} activated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to activate release: {str(e)}"
        )


@app.post("/registry/releases/{release_id}/sunset")
async def sunset_release(
    release_id: str, current_user: dict = Depends(get_current_user)
):
    """Sunset an active release"""
    try:
        # Get release data
        release_data = await decision_engine.storage_backend.get_release(release_id)
        if not release_data:
            raise HTTPException(
                status_code=404, detail=f"Release {release_id} not found"
            )

        if release_data["status"] != "ACTIVE":
            raise HTTPException(
                status_code=400, detail=f"Release {release_id} is not active"
            )

        # Update status to SUNSET
        release_data["status"] = "SUNSET"
        release_data["sunset_at"] = datetime.utcnow()
        release_data["sunset_by"] = current_user.get("user_id", "unknown")

        await decision_engine.storage_backend.update_release(release_id, release_data)

        return {"message": f"Release {release_id} sunset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to sunset release: {str(e)}"
        )


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


@app.get("/kms/keys")
async def list_kms_keys(current_user: dict = Depends(get_current_user)):
    """List all KMS keys"""
    try:
        keys = await kms_manager.client.list_keys()
        return {
            "keys": [
                {
                    "key_id": k.key_id,
                    "provider": k.provider.value,
                    "algorithm": k.algorithm,
                    "created_at": k.created_at.isoformat(),
                }
                for k in keys
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list KMS keys: {str(e)}"
        )


@app.post("/kms/keys")
async def create_kms_key(
    key_id: str,
    description: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Create a new KMS signing key"""
    try:
        key_info = await kms_manager.create_signing_key(key_id, description)
        return {
            "key_id": key_info.key_id,
            "provider": key_info.provider.value,
            "algorithm": key_info.algorithm,
            "public_key": key_info.public_key,
            "created_at": key_info.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create KMS key: {str(e)}"
        )


@app.get("/kms/keys/{key_id}")
async def get_kms_key(key_id: str, current_user: dict = Depends(get_current_user)):
    """Get KMS key information"""
    try:
        key_info = await kms_manager.get_key_info(key_id)
        return {
            "key_id": key_info.key_id,
            "provider": key_info.provider.value,
            "algorithm": key_info.algorithm,
            "public_key": key_info.public_key,
            "created_at": key_info.created_at.isoformat(),
            "description": key_info.description,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"KMS key not found: {str(e)}")


@app.get("/kms/public-keys")
async def get_public_keys(current_user: dict = Depends(get_current_user)):
    """Get all public keys for verification"""
    try:
        public_keys = await kms_manager.publish_public_keys()
        return {"public_keys": public_keys}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get public keys: {str(e)}"
        )


@app.post("/validation/eli")
async def validate_eli_reference(
    eli_uri: str, current_user: dict = Depends(get_current_user)
):
    """Validate a single ELI reference"""
    try:
        from policy_as_code.validation.eli_validator import (
            validate_eli_reference as validate_single_eli,
        )

        result = await validate_single_eli(eli_uri)

        return {
            "eli_uri": result.eli_uri,
            "status": result.status.value,
            "law_year": result.law_year,
            "law_number": result.law_number,
            "section": result.section,
            "law_title": result.law_title,
            "effective_date": (
                result.effective_date.isoformat() if result.effective_date else None
            ),
            "expiry_date": (
                result.expiry_date.isoformat() if result.expiry_date else None
            ),
            "error_message": result.error_message,
            "validated_at": result.validated_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ELI validation failed: {str(e)}")


@app.post("/validation/eli/batch")
async def validate_eli_references_batch(
    eli_uris: List[str], current_user: dict = Depends(get_current_user)
):
    """Validate multiple ELI references"""
    try:
        results = {}
        async with ELIValidator() as validator:
            for eli_uri in eli_uris:
                result = await validator.validate_eli(eli_uri)
                results[eli_uri] = {
                    "status": result.status.value,
                    "law_year": result.law_year,
                    "law_number": result.law_number,
                    "section": result.section,
                    "law_title": result.law_title,
                    "effective_date": (
                        result.effective_date.isoformat()
                        if result.effective_date
                        else None
                    ),
                    "expiry_date": (
                        result.expiry_date.isoformat() if result.expiry_date else None
                    ),
                    "error_message": result.error_message,
                    "validated_at": result.validated_at.isoformat(),
                }

        # Get validation summary
        summary = validator.get_validation_summary(
            {uri: result for uri, result in results.items()}
        )

        return {"results": results, "summary": summary}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Batch ELI validation failed: {str(e)}"
        )


@app.post("/kms/sign")
async def sign_data(
    key_id: str, data: Dict[str, Any], current_user: dict = Depends(get_current_user)
):
    """Sign data with KMS key"""
    try:
        signature_result = await kms_manager.client.sign(
            key_id, json.dumps(data, sort_keys=True).encode()
        )
        return {
            "signature": signature_result.signature,
            "key_id": signature_result.key_id,
            "algorithm": signature_result.algorithm,
            "timestamp": signature_result.timestamp.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sign data: {str(e)}")


@app.post("/kms/verify")
async def verify_signature(
    key_id: str,
    data: Dict[str, Any],
    signature: str,
    current_user: dict = Depends(get_current_user),
):
    """Verify signature with KMS key"""
    try:
        is_valid = await kms_manager.client.verify(
            key_id, json.dumps(data, sort_keys=True).encode(), signature
        )
        return {"valid": is_valid, "key_id": key_id}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to verify signature: {str(e)}"
        )


@app.get("/performance/alerts")
async def get_active_alerts(current_user: dict = Depends(get_current_user)):
    """Get active performance alerts"""
    try:
        alerts = await decision_engine.get_active_alerts()
        return {"alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Audit Replay API endpoints
@app.post("/audit/replay")
async def run_audit_replay(
    from_date: str,
    to_date: str,
    df_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Run audit replay for specified time range

    Args:
        from_date: Start date in ISO format (e.g., "2024-01-01T00:00:00Z")
        to_date: End date in ISO format (e.g., "2024-01-31T23:59:59Z")
        df_id: Optional specific decision function to audit

    Returns:
        Audit replay results with drift detection
    """
    try:
        # Parse dates
        from_dt = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        to_dt = datetime.fromisoformat(to_date.replace("Z", "+00:00"))

        # Validate date range
        if from_dt >= to_dt:
            raise HTTPException(
                status_code=400, detail="from_date must be before to_date"
            )

        # Check date range is reasonable (max 1 year)
        if (to_dt - from_dt).days > 365:
            raise HTTPException(
                status_code=400, detail="Date range cannot exceed 1 year"
            )

        # Run audit replay
        result = await audit_replay_api.run_audit_replay(from_dt, to_dt, df_id)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Audit replay error: {e}")
        raise HTTPException(status_code=500, detail=f"Audit replay failed: {str(e)}")


@app.get("/audit/report/latest")
async def get_latest_audit_report(current_user: dict = Depends(get_current_user)):
    """
    Get the latest audit report for public consumption

    Returns:
        Latest audit report with public summary
    """
    try:
        report = await audit_replay_api.get_latest_report()
        return report
    except Exception as e:
        logger.error(f"Error getting latest audit report: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get latest audit report: {str(e)}"
        )


@app.get("/audit/report/{report_id}")
async def get_audit_report(
    report_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get specific audit report by ID

    Args:
        report_id: Audit report identifier

    Returns:
        Audit report details
    """
    try:
        report = await audit_replay_api.get_report(report_id)

        if not report:
            raise HTTPException(
                status_code=404, detail=f"Audit report {report_id} not found"
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit report {report_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get audit report: {str(e)}"
        )


@app.get("/audit/drift/{report_id}")
async def get_drift_report(
    report_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get detailed drift report for auditors

    Args:
        report_id: Audit report identifier

    Returns:
        Detailed drift analysis with timeline and recommendations
    """
    try:
        report = await audit_replay_api.get_report(report_id)

        if not report:
            raise HTTPException(
                status_code=404, detail=f"Audit report {report_id} not found"
            )

        # Return detailed drift information for auditors
        return {
            "report_id": report_id,
            "audit_period": report["audit_period"],
            "drift_summary": report["drift_summary"],
            "chain_analysis": report["chain_analysis"],
            "coverage_analysis": report["coverage_analysis"],
            "security_metrics": report["security_metrics"],
            "recommendations": report["recommendations"],
            "compliance_score": report["compliance_score"],
            "generated_at": report["generated_at"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drift report {report_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get drift report: {str(e)}"
        )


@app.get("/audit/summary")
async def get_audit_summary(current_user: dict = Depends(get_current_user)):
    """
    Get audit summary for public consumption

    Returns:
        Public audit summary with key metrics
    """
    try:
        latest_report = await audit_replay_api.get_latest_report()

        if "error" in latest_report:
            return {
                "status": "no_data",
                "message": "No audit data available",
                "recommendation": "Run audit replay to generate first report",
            }

        # Extract key metrics for public summary
        return {
            "status": "available",
            "last_audit": latest_report["generated_at"],
            "audit_period": latest_report["audit_period"],
            "system_health": latest_report["summary"]["system_health"],
            "compliance_score": latest_report["compliance_score"],
            "chain_integrity": latest_report["chain_ok"],
            "coverage": latest_report["coverage_percentage"],
            "drift_percentage": latest_report["drift_percentage"],
            "security_status": latest_report["security_metrics"]["security_status"],
            "key_recommendations": latest_report["recommendations"][
                :3
            ],  # Top 3 recommendations
        }

    except Exception as e:
        logger.error(f"Error getting audit summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get audit summary: {str(e)}"
        )


@app.post("/audit/run")
async def trigger_audit(
    audit_type: str = "incremental",
    df_id: Optional[str] = None,
    days_back: int = 7,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger new audit (for auditors)

    Args:
        audit_type: Type of audit ("incremental", "full")
        df_id: Optional specific decision function to audit
        days_back: Number of days to audit back from now

    Returns:
        Audit trigger confirmation
    """
    try:
        # Calculate date range
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=days_back)

        # Run audit replay
        result = await audit_replay_api.run_audit_replay(from_date, to_date, df_id)

        return {
            "message": "Audit triggered successfully",
            "audit_id": result.get("audit_id"),
            "status": result.get("status"),
            "audit_period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
            "estimated_completion": result.get("completed_at"),
            "report_url": (
                f"/audit/report/{result.get('audit_id')}"
                if result.get("audit_id")
                else None
            ),
        }

    except Exception as e:
        logger.error(f"Error triggering audit: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger audit: {str(e)}"
        )


# Background tasks
async def log_decision_execution(
    result: DecisionResult, user: dict, x_road_client: str, x_request_nonce: str
):
    """Background task to log decision execution with X-Road metadata"""
    try:
        # Create trace entry with X-Road metadata
        trace_entry = {
            "trace_id": result.trace_id,
            "df_id": result.function_id,
            "version": result.version,
            "df_hash": f"sha256:{hashlib.sha256(f'{result.function_id}:{result.version}'.encode()).hexdigest()}",
            "ts": datetime.utcnow().isoformat() + "Z",
            "caller_id": x_road_client,
            "cert_thumbprint": "placeholder_thumbprint",  # Will be filled by mTLS middleware
            "request_nonce": x_request_nonce,
            "input_ref": f"s3://policy-as-code/inputs/redacted-{result.trace_id}.json",  # PII redacted
            "output": result.result,
            "prev_hash": "placeholder_prev_hash",  # Will be filled by ledger
            "chain_hash": "placeholder_chain_hash",  # Will be filled by ledger
            "status": "OK" if result.success else "ERROR",
        }

        # Append to trace ledger
        await decision_engine.trace_ledger.append_decision_execution(context, result)

        print(f"Decision executed: {result.trace_id} by X-Road client {x_road_client}")

    except Exception as e:
        print(f"Failed to log decision execution: {e}")


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
