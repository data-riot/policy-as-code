"""
Production-grade REST API for Decision Layer
Integrated with governance features: ledger, legal refs, signatures, explanations, audit
"""

import uuid
import datetime
import json

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .core import DecisionEngine
from .trace_ledger import TraceLedger, create_trace_record
from .release import ReleaseManager, SignerRole, create_release_manager
from .explain import create_explanation_api
from .audit_service import create_audit_service
from typing import Dict, Any, Optional, List


class DecisionRequest(BaseModel):
    """Request model for decision execution"""

    input_data: Dict[str, Any] = Field(..., description="Input data for the decision")
    version: Optional[str] = Field(None, description="Specific version to use")
    enable_validation: bool = Field(True, description="Enable input validation")
    client_id: Optional[str] = Field(None, description="Client identifier for tracing")


class LegalReferenceRequest(BaseModel):
    """Request model for legal reference validation"""

    system: str = Field(..., description="Legal system (finlex, eurlex, custom)")
    act_id: str = Field(..., description="Act/regulation identifier")
    section: Optional[str] = Field(None, description="Section number")
    subsection: Optional[str] = Field(None, description="Subsection number")
    title: Optional[str] = Field(None, description="Human-readable title")
    description: Optional[str] = Field(None, description="Description")


class SignatureRequest(BaseModel):
    """Request model for digital signatures"""

    signer_id: str = Field(..., description="Signer identifier")
    role: str = Field(..., description="Signer role (owner, reviewer)")
    comment: Optional[str] = Field(None, description="Signature comment")


class ReleaseRequest(BaseModel):
    """Request model for release creation"""

    legal_references: List[Dict[str, Any]] = Field(..., description="Legal references")
    change_summary: Optional[str] = Field(None, description="Summary of changes")
    risk_assessment: Optional[str] = Field(None, description="Risk assessment")
    compliance_checklist: Optional[List[str]] = Field(
        None, description="Compliance checklist"
    )
    release_notes: Optional[str] = Field(None, description="Release notes")


class DecisionResponse(BaseModel):
    """Response model for decision execution"""

    result: Dict[str, Any] = Field(..., description="Decision result")
    function_id: str = Field(..., description="Function ID")
    version: str = Field(..., description="Version used")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    trace_id: str = Field(..., description="Trace ID for audit")
    legal_basis: List[Dict[str, Any]] = Field(
        default_factory=list, description="Legal references"
    )


class ExplanationResponse(BaseModel):
    """Response model for decision explanations"""

    trace_id: str = Field(..., description="Trace ID")
    decision: str = Field(..., description="Human-readable decision")
    legal_basis: List[Dict[str, Any]] = Field(..., description="Legal references")
    decision_path: List[str] = Field(..., description="Decision reasoning path")
    confidence_score: Optional[float] = Field(None, description="Confidence score")
    redacted_fields: List[str] = Field(
        default_factory=list, description="Redacted fields"
    )


class AuditReportResponse(BaseModel):
    """Response model for audit reports"""

    report_id: str = Field(..., description="Report ID")
    generated_at: str = Field(..., description="Generation timestamp")
    audit_status: str = Field(..., description="Audit status")
    total_traces: int = Field(..., description="Total traces checked")
    failed_checks: int = Field(..., description="Number of failed checks")
    drift_count: int = Field(..., description="Number of drift detections")
    summary: str = Field(..., description="Audit summary")


# Agentic AI Request/Response Models


class AgenticDecisionRequest(BaseModel):
    """Request model for agentic decision making"""

    function_id: str = Field(..., description="Decision function ID")
    input_data: Dict[str, Any] = Field(..., description="Input data for the decision")
    citizen_id: Optional[str] = Field(None, description="Citizen identifier")
    service_type: Optional[str] = Field(None, description="Type of service")
    urgency_level: str = Field(
        "normal", description="Urgency level (low, normal, high, critical)"
    )
    reasoning_mode: str = Field(
        "autonomous", description="Reasoning mode (autonomous, assisted, explanatory)"
    )
    legal_framework: Optional[str] = Field(None, description="Legal framework to apply")


class ConversationRequest(BaseModel):
    """Request model for conversational interface"""

    message: str = Field(..., description="Citizen message")
    session_id: str = Field(..., description="Session identifier")
    citizen_id: Optional[str] = Field(None, description="Citizen identifier")
    channel: str = Field("web_chat", description="Communication channel")
    language: str = Field("en", description="Language preference")


class WorkflowRequest(BaseModel):
    """Request model for workflow orchestration"""

    workflow_definition: Dict[str, Any] = Field(..., description="Workflow definition")
    initial_context: Optional[Dict[str, Any]] = Field(
        None, description="Initial context data"
    )


class PerformanceMetricsRequest(BaseModel):
    """Request model for performance metrics"""

    agent_id: str = Field(..., description="Agent identifier")
    metric_type: str = Field(..., description="Type of metric")
    value: float = Field(..., description="Metric value")
    context: Optional[Dict[str, Any]] = Field(None, description="Context data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AgenticDecisionResponse(BaseModel):
    """Response model for agentic decisions"""

    decision: Dict[str, Any] = Field(..., description="Decision result")
    confidence: float = Field(..., description="Confidence score")
    reasoning_steps: List[str] = Field(..., description="Reasoning steps")
    legal_basis: List[str] = Field(..., description="Legal basis")
    alternatives_considered: List[str] = Field(
        ..., description="Alternatives considered"
    )
    risk_assessment: Dict[str, Any] = Field(..., description="Risk assessment")
    trace_id: str = Field(..., description="Trace identifier")


class ConversationResponse(BaseModel):
    """Response model for conversational interface"""

    message: str = Field(..., description="Agent response message")
    actions: List[Dict[str, Any]] = Field(..., description="Actions to take")
    next_steps: List[str] = Field(..., description="Next steps")
    requires_human: bool = Field(..., description="Whether human assistance is needed")
    confidence: float = Field(..., description="Confidence score")
    trace_id: str = Field(..., description="Trace identifier")


class WorkflowResponse(BaseModel):
    """Response model for workflow orchestration"""

    execution_id: str = Field(..., description="Workflow execution ID")
    status: str = Field(..., description="Execution status")
    started_at: str = Field(..., description="Start timestamp")
    progress: Dict[str, Any] = Field(..., description="Progress information")


class PerformanceReportResponse(BaseModel):
    """Response model for performance reports"""

    agent_id: str = Field(..., description="Agent identifier")
    performance_score: float = Field(..., description="Overall performance score")
    effectiveness_metrics: Dict[str, Any] = Field(
        ..., description="Effectiveness metrics"
    )
    trend_analysis: Dict[str, str] = Field(..., description="Trend analysis")
    recommendations: List[str] = Field(..., description="Recommendations")
    data_points: int = Field(..., description="Number of data points")


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
    """Production-grade REST API for Decision Layer with governance features"""

    def __init__(
        self,
        engine: DecisionEngine,
        trace_ledger: Optional[TraceLedger] = None,
        release_manager: Optional[ReleaseManager] = None,
        host: str = "localhost",
        port: int = 8000,
    ):
        self.engine = engine
        self.trace_ledger = trace_ledger
        self.release_manager = release_manager or create_release_manager()
        self.host = host
        self.port = port

        # Initialize governance services
        if self.trace_ledger:
            self.explanation_api = create_explanation_api(
                self.release_manager, self.trace_ledger
            )
            self.audit_service = create_audit_service(
                self.trace_ledger, self.release_manager
            )
        else:
            self.explanation_api = None
            self.audit_service = None

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
            """Execute a decision function with governance features"""
            try:
                import time

                start_time = time.time()

                # Check if function can be executed (is active)
                if self.release_manager:
                    version = request.version or "latest"
                    if not self.release_manager.can_execute_function(
                        function_id, version
                    ):
                        raise HTTPException(
                            status_code=403,
                            detail=f"Function {function_id} v{version} is not active",
                        )

                result = await self.engine.execute(
                    function_id, request.input_data, request.version, request.client_id
                )

                execution_time = (time.time() - start_time) * 1000

                # Get legal basis if available
                legal_basis = []
                if self.release_manager:
                    release = self.release_manager.get_release(
                        function_id, request.version or "latest"
                    )
                    if release:
                        legal_basis = [
                            ref.to_dict() for ref in release.legal_references
                        ]

                # Write to trace ledger if available
                trace_id = "unknown"
                if self.trace_ledger:
                    # Generate trace record
                    trace_record = create_trace_record(
                        trace_id=str(uuid.uuid4()),
                        df_id=function_id,
                        version=request.version or "latest",
                        df_hash="mock_hash",  # Would be actual function hash
                        timestamp=datetime.now(),
                        caller=request.client_id or "anonymous",
                        status="success",
                        input_data=request.input_data,
                        output_data=result,
                        signer="system",
                        prev_hash=await self.trace_ledger.get_latest_hash(),
                    )
                    await self.trace_ledger.write_trace(trace_record)
                    trace_id = trace_record.trace_id

                return DecisionResponse(
                    result=result,
                    function_id=function_id,
                    version=request.version or "latest",
                    execution_time_ms=round(execution_time, 2),
                    trace_id=trace_id,
                    legal_basis=legal_basis,
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

        # Governance endpoints
        @app.get("/explain/{trace_id}", response_model=ExplanationResponse)
        async def explain_decision(trace_id: str, redact_sensitive: bool = True):
            """Get human-readable explanation for a decision trace"""
            if not self.explanation_api:
                raise HTTPException(
                    status_code=503, detail="Explanation service not available"
                )

            try:
                explanation = await self.explanation_api.get_explanation(
                    trace_id, redact_sensitive
                )
                return ExplanationResponse(
                    trace_id=explanation.trace_id,
                    decision=explanation.decision,
                    legal_basis=explanation.legal_basis,
                    decision_path=explanation.decision_path,
                    confidence_score=explanation.confidence_score,
                    redacted_fields=explanation.redacted_fields,
                )
            except Exception as e:
                raise HTTPException(
                    status_code=404, detail=f"Explanation not found: {str(e)}"
                )

        @app.get("/audit/report/latest", response_model=AuditReportResponse)
        async def get_latest_audit_report():
            """Get the latest audit report"""
            if not self.audit_service:
                raise HTTPException(
                    status_code=503, detail="Audit service not available"
                )

            report = self.audit_service.get_latest_report()
            if not report:
                raise HTTPException(
                    status_code=404, detail="No audit reports available"
                )

            return AuditReportResponse(
                report_id=report.report_id,
                generated_at=report.generated_at.isoformat(),
                audit_status=report.audit_status.value,
                total_traces=report.total_traces,
                failed_checks=report.failed_checks,
                drift_count=report.drift_count,
                summary=report.summary,
            )

        @app.post("/audit/run")
        async def run_audit():
            """Run a new audit"""
            if not self.audit_service:
                raise HTTPException(
                    status_code=503, detail="Audit service not available"
                )

            try:
                report = await self.audit_service.run_audit()
                return {"message": "Audit completed", "report_id": report.report_id}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")

        # Legal reference endpoints
        @app.post("/legal/validate")
        async def validate_legal_reference(request: LegalReferenceRequest):
            """Validate a legal reference"""
            try:
                from .legal_refs import create_legal_reference

                ref = create_legal_reference(
                    system=request.system,
                    act_id=request.act_id,
                    section=request.section,
                    subsection=request.subsection,
                    title=request.title,
                    description=request.description,
                )
                return {"valid": True, "reference": ref.to_dict()}
            except Exception as e:
                return {"valid": False, "error": str(e)}

        # Release management endpoints
        @app.post("/registry/{function_id}/{version}/release")
        async def create_release(
            function_id: str, version: str, request: ReleaseRequest
        ):
            """Create a new release"""
            try:
                # Validate legal references
                legal_refs = []
                for ref_data in request.legal_references:
                    from .legal_refs import LawReference

                    legal_refs.append(LawReference.from_dict(ref_data))

                release = self.release_manager.create_release(
                    function_id=function_id,
                    version=version,
                    legal_references=legal_refs,
                    change_summary=request.change_summary,
                    risk_assessment=request.risk_assessment,
                    compliance_checklist=request.compliance_checklist,
                    release_notes=request.release_notes,
                )

                return {"message": "Release created", "release": release.to_dict()}
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Release creation failed: {str(e)}"
                )

        @app.post("/registry/{function_id}/{version}/sign")
        async def sign_release(
            function_id: str, version: str, request: SignatureRequest
        ):
            """Sign a release"""
            try:
                role = SignerRole(request.role)
                release = self.release_manager.sign_release(
                    function_id=function_id,
                    version=version,
                    signer_id=request.signer_id,
                    role=role,
                    comment=request.comment,
                )

                return {"message": "Release signed", "release": release.to_dict()}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Signing failed: {str(e)}")

        @app.post("/registry/{function_id}/{version}/activate")
        async def activate_release(function_id: str, version: str):
            """Activate a release"""
            try:
                release = self.release_manager.activate_release(function_id, version)
                return {"message": "Release activated", "release": release.to_dict()}
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Activation failed: {str(e)}"
                )

        @app.get("/registry/{function_id}/{version}/release")
        async def get_release(function_id: str, version: str):
            """Get release information"""
            release = self.release_manager.get_release(function_id, version)
            if not release:
                raise HTTPException(
                    status_code=404,
                    detail=f"Release {function_id} v{version} not found",
                )

            return release.to_dict()

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
    engine: DecisionEngine,
    trace_ledger: Optional[TraceLedger] = None,
    release_manager: Optional[ReleaseManager] = None,
    host: str = "localhost",
    port: int = 8000,
) -> DecisionLayerAPI:
    """Create a Decision Layer API instance with governance features"""
    return DecisionLayerAPI(engine, trace_ledger, release_manager, host, port)


if __name__ == "__main__":
    # Example usage
    engine = DecisionEngine()
    api = create_api(engine)
    api.run()
