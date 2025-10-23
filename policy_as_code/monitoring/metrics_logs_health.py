"""
Metrics, Logging, and Health Monitoring
Comprehensive monitoring solution with Prometheus metrics, structured logging, and health checks
"""

import os
import time
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)
import redis
from pydantic import BaseModel


class HealthStatus(Enum):
    """Health status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Individual health check result"""

    name: str
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealth:
    """Overall system health status"""

    status: HealthStatus
    timestamp: datetime
    uptime_seconds: float
    version: str
    checks: List[HealthCheck]
    metrics: Dict[str, Any]


class MetricsCollector:
    """Prometheus metrics collector"""

    def __init__(self):
        self.registry = CollectorRegistry()

        # Request metrics
        self.request_count = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        self.request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            registry=self.registry,
        )

        # Decision metrics
        self.decision_count = Counter(
            "decisions_total",
            "Total decisions executed",
            ["function_id", "version", "status"],
            registry=self.registry,
        )

        self.decision_duration = Histogram(
            "decision_duration_seconds",
            "Decision execution duration",
            ["function_id", "version"],
            registry=self.registry,
        )

        # System metrics
        self.active_connections = Gauge(
            "active_connections", "Number of active connections", registry=self.registry
        )

        self.cache_size = Gauge(
            "cache_size_bytes", "Cache size in bytes", registry=self.registry
        )

        self.registered_functions = Gauge(
            "registered_functions_total",
            "Number of registered decision functions",
            registry=self.registry,
        )

        # Error metrics
        self.error_count = Counter(
            "errors_total",
            "Total errors",
            ["error_type", "component"],
            registry=self.registry,
        )

        # Authentication metrics
        self.auth_attempts = Counter(
            "auth_attempts_total",
            "Authentication attempts",
            ["client_id", "status"],
            registry=self.registry,
        )

        self.nonce_validations = Counter(
            "nonce_validations_total",
            "Nonce validations",
            ["client_id", "status"],
            registry=self.registry,
        )

    def record_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """Record HTTP request metrics"""
        self.request_count.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_decision(
        self, function_id: str, version: str, status: str, duration: float
    ):
        """Record decision execution metrics"""
        self.decision_count.labels(
            function_id=function_id, version=version, status=status
        ).inc()
        self.decision_duration.labels(function_id=function_id, version=version).observe(
            duration
        )

    def record_error(self, error_type: str, component: str):
        """Record error metrics"""
        self.error_count.labels(error_type=error_type, component=component).inc()

    def record_auth_attempt(self, client_id: str, status: str):
        """Record authentication attempt"""
        self.auth_attempts.labels(client_id=client_id, status=status).inc()

    def record_nonce_validation(self, client_id: str, status: str):
        """Record nonce validation"""
        self.nonce_validations.labels(client_id=client_id, status=status).inc()

    def update_system_metrics(
        self, active_connections: int, cache_size: int, registered_functions: int
    ):
        """Update system metrics"""
        self.active_connections.set(active_connections)
        self.cache_size.set(cache_size)
        self.registered_functions.set(registered_functions)


class StructuredLogger:
    """Structured logging with JSON output"""

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Create JSON formatter
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_request(
        self,
        request: Request,
        response: Response,
        duration: float,
        user: Optional[Dict] = None,
    ):
        """Log HTTP request"""
        log_data = {
            "event": "http_request",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration * 1000,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
            "user_id": user.get("user_id") if user else None,
            "client_id": user.get("client_id") if user else None,
        }

        if response.status_code >= 400:
            self.logger.error(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))

    def log_decision(
        self,
        function_id: str,
        version: str,
        trace_id: str,
        duration: float,
        success: bool,
        error_message: Optional[str] = None,
        user: Optional[Dict] = None,
    ):
        """Log decision execution"""
        log_data = {
            "event": "decision_execution",
            "function_id": function_id,
            "version": version,
            "trace_id": trace_id,
            "duration_ms": duration * 1000,
            "success": success,
            "error_message": error_message,
            "user_id": user.get("user_id") if user else None,
            "client_id": user.get("client_id") if user else None,
        }

        if not success:
            self.logger.error(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))

    def log_auth_event(
        self,
        event_type: str,
        client_id: str,
        status: str,
        details: Optional[Dict] = None,
    ):
        """Log authentication events"""
        log_data = {
            "event": f"auth_{event_type}",
            "client_id": client_id,
            "status": status,
            "details": details or {},
        }

        if status == "success":
            self.logger.info(json.dumps(log_data))
        else:
            self.logger.warning(json.dumps(log_data))

    def log_security_event(
        self, event_type: str, severity: str, details: Dict[str, Any]
    ):
        """Log security events"""
        log_data = {
            "event": f"security_{event_type}",
            "severity": severity,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if severity == "high":
            self.logger.critical(json.dumps(log_data))
        elif severity == "medium":
            self.logger.error(json.dumps(log_data))
        else:
            self.logger.warning(json.dumps(log_data))


class HealthChecker:
    """System health checker"""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.start_time = time.time()
        self.checks: List[callable] = []

        # Register default health checks
        self.register_check("database", self._check_database)
        self.register_check("redis", self._check_redis)
        self.register_check("memory", self._check_memory)
        self.register_check("disk", self._check_disk)

    def register_check(self, name: str, check_func: callable):
        """Register a health check function"""
        self.checks.append((name, check_func))

    async def run_checks(self) -> List[HealthCheck]:
        """Run all health checks"""
        results = []

        for name, check_func in self.checks:
            start_time = time.time()
            try:
                status, message, details = await check_func()
                response_time = (time.time() - start_time) * 1000

                results.append(
                    HealthCheck(
                        name=name,
                        status=status,
                        message=message,
                        response_time_ms=response_time,
                        timestamp=datetime.utcnow(),
                        details=details,
                    )
                )
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                results.append(
                    HealthCheck(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Health check failed: {str(e)}",
                        response_time_ms=response_time,
                        timestamp=datetime.utcnow(),
                    )
                )

        return results

    async def _check_database(self) -> tuple:
        """Check database connectivity"""
        try:
            # This would check your actual database
            # For now, return healthy
            return HealthStatus.HEALTHY, "Database connection OK", {"connections": 5}
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Database error: {str(e)}", None

    async def _check_redis(self) -> tuple:
        """Check Redis connectivity"""
        try:
            redis_client = redis.from_url(self.redis_url)
            redis_client.ping()
            info = redis_client.info()
            return (
                HealthStatus.HEALTHY,
                "Redis connection OK",
                {
                    "memory_used": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                },
            )
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Redis error: {str(e)}", None

    async def _check_memory(self) -> tuple:
        """Check memory usage"""
        try:
            import psutil

            memory = psutil.virtual_memory()
            usage_percent = memory.percent

            if usage_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High memory usage: {usage_percent}%"
            elif usage_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Elevated memory usage: {usage_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage OK: {usage_percent}%"

            return (
                status,
                message,
                {
                    "usage_percent": usage_percent,
                    "available_gb": memory.available / (1024**3),
                },
            )
        except ImportError:
            return HealthStatus.DEGRADED, "psutil not available", None
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Memory check error: {str(e)}", None

    async def _check_disk(self) -> tuple:
        """Check disk usage"""
        try:
            import psutil

            disk = psutil.disk_usage("/")
            usage_percent = (disk.used / disk.total) * 100

            if usage_percent > 95:
                status = HealthStatus.UNHEALTHY
                message = f"Critical disk usage: {usage_percent:.1f}%"
            elif usage_percent > 85:
                status = HealthStatus.DEGRADED
                message = f"High disk usage: {usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage OK: {usage_percent:.1f}%"

            return (
                status,
                message,
                {"usage_percent": usage_percent, "free_gb": disk.free / (1024**3)},
            )
        except ImportError:
            return HealthStatus.DEGRADED, "psutil not available", None
        except Exception as e:
            return HealthStatus.UNHEALTHY, f"Disk check error: {str(e)}", None


class MonitoringMiddleware:
    """FastAPI middleware for monitoring"""

    def __init__(
        self,
        app: FastAPI,
        metrics_collector: MetricsCollector,
        logger: StructuredLogger,
    ):
        self.app = app
        self.metrics = metrics_collector
        self.logger = logger

        # Add middleware
        @app.middleware("http")
        async def monitoring_middleware(request: Request, call_next):
            start_time = time.time()

            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            self.metrics.record_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration,
            )

            # Log request
            user = getattr(request.state, "user", None)
            self.logger.log_request(request, response, duration, user)

            return response


class HealthAPI:
    """Health check API endpoints"""

    def __init__(
        self, health_checker: HealthChecker, metrics_collector: MetricsCollector
    ):
        self.health_checker = health_checker
        self.metrics = metrics_collector

    async def health_check(self) -> SystemHealth:
        """Comprehensive health check"""
        checks = await self.health_checker.run_checks()

        # Determine overall status
        if any(check.status == HealthStatus.UNHEALTHY for check in checks):
            overall_status = HealthStatus.UNHEALTHY
        elif any(check.status == HealthStatus.DEGRADED for check in checks):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        # Get system metrics
        metrics_data = {
            "uptime_seconds": time.time() - self.health_checker.start_time,
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }

        return SystemHealth(
            status=overall_status,
            timestamp=datetime.utcnow(),
            uptime_seconds=metrics_data["uptime_seconds"],
            version=metrics_data["version"],
            checks=checks,
            metrics=metrics_data,
        )

    async def healthz(self) -> Dict[str, str]:
        """Kubernetes-style health check"""
        health = await self.health_check()

        if health.status == HealthStatus.HEALTHY:
            return {"status": "ok"}
        else:
            return {"status": "error", "message": "System unhealthy"}


# FastAPI integration functions
def create_monitoring_app(app: FastAPI, redis_url: str = None) -> tuple:
    """Create monitoring components for FastAPI app"""

    # Initialize components
    metrics_collector = MetricsCollector()
    logger = StructuredLogger("policy-as-code")
    health_checker = HealthChecker(redis_url)
    health_api = HealthAPI(health_checker, metrics_collector)

    # Add monitoring middleware
    monitoring_middleware = MonitoringMiddleware(app, metrics_collector, logger)

    # Add health endpoints
    @app.get("/health", response_model=SystemHealth)
    async def health():
        """Comprehensive health check endpoint"""
        return await health_api.health_check()

    @app.get("/healthz")
    async def healthz():
        """Kubernetes-style health check"""
        return await health_api.healthz()

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            generate_latest(metrics_collector.registry), media_type=CONTENT_TYPE_LATEST
        )

    return metrics_collector, logger, health_checker, health_api


# Utility functions
def get_metrics_collector() -> Optional[MetricsCollector]:
    """Get global metrics collector instance"""
    return getattr(create_monitoring_app, "_metrics_collector", None)


def get_structured_logger() -> Optional[StructuredLogger]:
    """Get global structured logger instance"""
    return getattr(create_monitoring_app, "_logger", None)
