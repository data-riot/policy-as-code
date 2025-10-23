"""
Secure Policy as Code API Application
Comprehensive FastAPI application with full authentication, monitoring, and security
"""

import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from policy_as_code.core.enhanced_engine import DecisionEngine
from policy_as_code.core.security import SecurityConfig as CoreSecurityConfig
from policy_as_code.api.graphql_api import create_graphql_router
from policy_as_code.api.enhanced_rest import app as rest_app
from policy_as_code.security.nonce_auth import (
    NonceAuthMiddleware,
    AuthConfig,
    create_auth_config,
    get_current_user,
    get_client_id,
    generate_client_credentials,
)
from policy_as_code.security.ingress_security import (
    apply_security_middleware,
    create_security_config,
    SecurityConfigBuilder,
)
from policy_as_code.monitoring.metrics_logs_health import (
    create_monitoring_app,
    MetricsCollector,
    StructuredLogger,
    HealthAPI,
)


class SecurePolicyAPI:
    """Secure Policy as Code API with comprehensive security"""

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.app = FastAPI(
            title="Policy as Code API",
            description="Secure Policy as Code decision platform with comprehensive security",
            version="1.0.0",
            docs_url="/docs" if environment != "production" else None,
            redoc_url="/redoc" if environment != "production" else None,
        )

        # Initialize components
        self.decision_engine = DecisionEngine(CoreSecurityConfig())
        self.auth_config = create_auth_config()
        self.security_config = self._create_security_config()

        # Initialize monitoring
        (
            self.metrics_collector,
            self.logger,
            self.health_checker,
            self.health_api,
        ) = create_monitoring_app(self.app, self.security_config.redis_url)

        # Setup application
        self._setup_middleware()
        self._setup_routes()
        self._setup_security()

    def _create_security_config(self):
        """Create security configuration based on environment"""
        builder = SecurityConfigBuilder()

        if self.environment == "development":
            return builder.for_development().build()
        elif self.environment == "staging":
            return builder.for_staging().build()
        else:
            return builder.for_production().build()

    def _setup_middleware(self):
        """Setup all middleware"""
        # Apply ingress security middleware
        apply_security_middleware(self.app, self.security_config)

        # Add nonce authentication middleware
        self.app.add_middleware(NonceAuthMiddleware, config=self.auth_config)

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.security_config.cors_origins,
            allow_credentials=True,
            allow_methods=self.security_config.cors_methods,
            allow_headers=self.security_config.cors_headers,
        )

    def _setup_routes(self):
        """Setup API routes"""

        # Health endpoints
        @self.app.get("/health")
        async def health():
            """Comprehensive health check"""
            return await self.health_api.health_check()

        @self.app.get("/healthz")
        async def healthz():
            """Kubernetes-style health check"""
            return await self.health_api.healthz()

        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint"""
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            from fastapi.responses import Response

            return Response(
                generate_latest(self.metrics_collector.registry),
                media_type=CONTENT_TYPE_LATEST,
            )

        # Root endpoint
        @self.app.get("/")
        async def root():
            """API information"""
            return {
                "name": "Policy as Code API",
                "version": "1.0.0",
                "environment": self.environment,
                "security": "enabled",
                "endpoints": {
                    "health": "/health",
                    "healthz": "/healthz",
                    "metrics": "/metrics",
                    "graphql": "/graphql",
                    "docs": "/docs" if self.environment != "production" else "disabled",
                },
            }

        # GraphQL endpoint
        graphql_router = create_graphql_router(self.decision_engine, self.auth_config)
        self.app.include_router(graphql_router)

        # Include REST API routes
        self.app.include_router(rest_app.router, prefix="/api/v1")

        # Security endpoints
        @self.app.post("/auth/generate-credentials")
        async def generate_credentials(
            client_id: str,
            roles: list = ["user"],
            current_user: dict = Depends(get_current_user),
        ):
            """Generate client credentials (admin only)"""
            if "admin" not in current_user.get("roles", []):
                raise HTTPException(status_code=403, detail="Admin access required")

            credentials = generate_client_credentials(client_id, roles)
            self.logger.log_auth_event("credential_generation", client_id, "success")

            return credentials

        @self.app.get("/auth/validate")
        async def validate_auth(current_user: dict = Depends(get_current_user)):
            """Validate current authentication"""
            return {
                "valid": True,
                "user": current_user,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _setup_security(self):
        """Setup additional security features"""

        # Request logging middleware
        @self.app.middleware("http")
        async def security_logging_middleware(request: Request, call_next):
            start_time = time.time()

            # Process request
            response = await call_next(request)

            # Log security events
            duration = time.time() - start_time
            client_ip = request.client.host if request.client else "unknown"
            user = getattr(request.state, "user", None)

            # Log authentication events
            if hasattr(request.state, "user") and request.state.user:
                self.logger.log_auth_event(
                    "request",
                    user.get("client_id", "unknown"),
                    "success",
                    {
                        "endpoint": request.url.path,
                        "method": request.method,
                        "duration_ms": duration * 1000,
                        "client_ip": client_ip,
                    },
                )

            # Record metrics
            self.metrics_collector.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration,
            )

            return response

        # Error handling
        @self.app.exception_handler(HTTPException)
        async def security_error_handler(request: Request, exc: HTTPException):
            # Log security events
            client_ip = request.client.host if request.client else "unknown"

            if exc.status_code == 401:
                self.logger.log_security_event(
                    "authentication_failure",
                    "medium",
                    {
                        "client_ip": client_ip,
                        "endpoint": request.url.path,
                        "error": exc.detail,
                    },
                )
            elif exc.status_code == 403:
                self.logger.log_security_event(
                    "authorization_failure",
                    "medium",
                    {
                        "client_ip": client_ip,
                        "endpoint": request.url.path,
                        "error": exc.detail,
                    },
                )
            elif exc.status_code == 429:
                self.logger.log_security_event(
                    "rate_limit_exceeded",
                    "low",
                    {
                        "client_ip": client_ip,
                        "endpoint": request.url.path,
                        "error": exc.detail,
                    },
                )

            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.detail,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    def register_use_cases(self):
        """Register example use cases"""
        try:
            from examples.demos import (
                healthcare_eligibility,
                social_benefits_allocation,
                immigration_visa_processing,
            )

            # Register healthcare eligibility
            self.decision_engine.register_function(
                "healthcare_eligibility",
                "1.0.0",
                healthcare_eligibility.decision_function,
            )

            # Register social benefits allocation
            self.decision_engine.register_function(
                "social_benefits_allocation",
                "1.0.0",
                social_benefits_allocation.decision_function,
            )

            # Register immigration visa processing
            self.decision_engine.register_function(
                "immigration_visa_processing",
                "1.0.0",
                immigration_visa_processing.decision_function,
            )

            self.logger.logger.info("Use cases registered successfully")

        except ImportError as e:
            self.logger.logger.warning(f"Could not register use cases: {e}")

    def get_app(self) -> FastAPI:
        """Get the FastAPI application"""
        return self.app


def create_secure_api(environment: str = "production") -> FastAPI:
    """Create a secure Policy as Code API"""
    api = SecurePolicyAPI(environment)
    api.register_use_cases()
    return api.get_app()


# Create the application
app = create_secure_api(os.getenv("ENVIRONMENT", "production"))


if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    environment = os.getenv("ENVIRONMENT", "production")

    # Run the application
    uvicorn.run(
        "policy_as_code.api.secure_api:app",
        host=host,
        port=port,
        reload=environment == "development",
        log_level="info" if environment == "production" else "debug",
    )
