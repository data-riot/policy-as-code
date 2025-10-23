"""
GraphQL API for Policy as Code Platform
Provides flexible querying capabilities for decision data with comprehensive security
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info
from fastapi import FastAPI, Request, Depends
from starlette.middleware.base import BaseHTTPMiddleware

from policy_as_code.core.enhanced_engine import DecisionEngine
from policy_as_code.core.types import DecisionContext, DecisionResult
from policy_as_code.tracing.enhanced_ledger import (
    TraceEntryType as LedgerTraceEntryType,
)
from policy_as_code.security.nonce_auth import (
    NonceAuthMiddleware,
    AuthConfig,
    create_auth_config,
    get_current_user,
    get_client_id,
)
from policy_as_code.security.ingress_security import (
    apply_security_middleware,
    create_security_config,
)
from policy_as_code.monitoring.metrics_logs_health import (
    create_monitoring_app,
    MetricsCollector,
    StructuredLogger,
)


@strawberry.type
class DecisionResultType:
    """GraphQL type for decision results"""

    trace_id: str
    function_id: str
    version: str
    execution_time_ms: int
    timestamp: str
    success: bool
    error_message: Optional[str] = None


@strawberry.type
class DecisionStatsType:
    """GraphQL type for decision statistics"""

    total_decisions: int
    success_rate: float
    avg_execution_time: float
    first_decision: Optional[str] = None
    last_decision: Optional[str] = None


@strawberry.type
class TraceEntryType:
    """GraphQL type for trace entries"""

    entry_id: str
    entry_type: str
    timestamp: str
    function_id: Optional[str] = None
    hash: str
    previous_hash: Optional[str] = None
    signature: Optional[str] = None


@strawberry.type
class TraceIntegrityType:
    """GraphQL type for trace integrity verification"""

    is_valid: bool
    total_entries: int
    errors: List[str]
    genesis_hash: str
    last_hash: Optional[str] = None


@strawberry.type
class FunctionInfoType:
    """GraphQL type for function information"""

    function_id: str
    versions: List[str]
    description: Optional[str] = None


@strawberry.type
class HealthStatusType:
    """GraphQL type for health status"""

    status: str
    registered_functions: int
    cache_size: int
    trace_ledger_total_entries: int
    trace_ledger_is_valid: bool
    timestamp: str


@strawberry.input
class DecisionRequestInput:
    """GraphQL input for decision requests"""

    function_id: str
    version: str = "latest"
    input_data: strawberry.scalars.JSON
    trace_id: Optional[str] = None


@strawberry.input
class DateRangeInput:
    """GraphQL input for date range queries"""

    start_date: str
    end_date: str


class GraphQLContext:
    """GraphQL context with decision engine and security"""

    def __init__(
        self,
        decision_engine: DecisionEngine,
        user: Dict[str, Any] = None,
        client_id: str = None,
    ):
        self.decision_engine = decision_engine
        self.user = user or {}
        self.client_id = client_id or "anonymous"


@strawberry.type
class Query:
    """GraphQL query root"""

    @strawberry.field
    async def health(self, info: Info) -> HealthStatusType:
        """Get system health status"""
        health_data = await info.context.decision_engine.health_check()
        ledger_stats = health_data.get("trace_ledger", {})

        return HealthStatusType(
            status=health_data["status"],
            registered_functions=health_data["registered_functions"],
            cache_size=health_data["cache_size"],
            trace_ledger_total_entries=ledger_stats.get("total_entries", 0),
            trace_ledger_is_valid=ledger_stats.get("is_valid", True),
            timestamp=health_data["timestamp"],
        )

    @strawberry.field
    async def functions(self, info: Info) -> List[FunctionInfoType]:
        """Get all registered functions"""
        function_ids = info.context.decision_engine.registry.list_functions()
        functions = []

        for func_id in function_ids:
            versions = info.context.decision_engine.registry._versions.get(func_id, [])
            functions.append(
                FunctionInfoType(
                    function_id=func_id,
                    versions=versions,
                    description=f"Decision function for {func_id}",
                )
            )

        return functions

    @strawberry.field
    async def decision_history(
        self, info: Info, function_id: str, limit: int = 100, offset: int = 0
    ) -> List[DecisionResultType]:
        """Get decision history for a function"""
        history = await info.context.decision_engine.get_decision_history(
            function_id, limit, offset
        )

        return [
            DecisionResultType(
                trace_id=result.trace_id,
                function_id=result.function_id,
                version=result.version,
                execution_time_ms=result.execution_time_ms,
                timestamp=result.timestamp.isoformat(),
                success=result.success,
                error_message=result.error_message,
            )
            for result in history
        ]

    @strawberry.field
    async def decisions_by_date_range(
        self, info: Info, date_range: DateRangeInput, limit: int = 100
    ) -> List[DecisionResultType]:
        """Get decisions within a date range"""
        start_date = datetime.fromisoformat(date_range.start_date)
        end_date = datetime.fromisoformat(date_range.end_date)

        decisions = await info.context.decision_engine.get_decisions_by_date_range(
            start_date, end_date, limit
        )

        return [
            DecisionResultType(
                trace_id=result.trace_id,
                function_id=result.function_id,
                version=result.version,
                execution_time_ms=result.execution_time_ms,
                timestamp=result.timestamp.isoformat(),
                success=result.success,
                error_message=result.error_message,
            )
            for result in decisions
        ]

    @strawberry.field
    async def decision_stats(self, info: Info, function_id: str) -> DecisionStatsType:
        """Get decision statistics for a function"""
        stats = await info.context.decision_engine.get_decision_stats(function_id)

        return DecisionStatsType(
            total_decisions=stats["total_decisions"],
            success_rate=stats["success_rate"],
            avg_execution_time=stats["avg_execution_time"],
            first_decision=stats.get("first_decision"),
            last_decision=stats.get("last_decision"),
        )

    @strawberry.field
    async def trace_entries(
        self, info: Info, function_id: Optional[str] = None, limit: int = 100
    ) -> List[TraceEntryType]:
        """Get trace entries"""
        entries = await info.context.decision_engine.get_trace_entries(
            function_id, limit
        )

        return [
            TraceEntryType(
                entry_id=entry["entry_id"],
                entry_type=entry["entry_type"],
                timestamp=entry["timestamp"],
                function_id=entry.get("function_id"),
                hash=entry["hash"],
                previous_hash=entry.get("previous_hash"),
                signature=entry.get("signature"),
            )
            for entry in entries
        ]

    @strawberry.field
    async def trace_integrity(self, info: Info) -> TraceIntegrityType:
        """Verify trace ledger integrity"""
        integrity = await info.context.decision_engine.verify_trace_integrity()

        return TraceIntegrityType(
            is_valid=integrity["is_valid"],
            total_entries=integrity["total_entries"],
            errors=integrity["errors"],
            genesis_hash=integrity["genesis_hash"],
            last_hash=integrity.get("last_hash"),
        )


@strawberry.type
class Mutation:
    """GraphQL mutation root"""

    @strawberry.field
    async def execute_decision(
        self, info: Info, request: DecisionRequestInput
    ) -> DecisionResultType:
        """Execute a decision function"""
        # Create decision context
        context = DecisionContext(
            function_id=request.function_id,
            version=request.version,
            input_hash="",  # Will be calculated by engine
            timestamp=datetime.now(),
            trace_id=request.trace_id or "",
        )

        # Execute decision
        result = await info.context.decision_engine.execute_decision(
            function_id=request.function_id,
            version=request.version,
            input_data=request.input_data,
            context=context,
        )

        return DecisionResultType(
            trace_id=result.trace_id,
            function_id=result.function_id,
            version=result.version,
            execution_time_ms=result.execution_time_ms,
            timestamp=result.timestamp.isoformat(),
            success=result.success,
            error_message=result.error_message,
        )

    @strawberry.field
    async def cleanup_old_decisions(self, info: Info, retention_days: int) -> int:
        """Clean up decisions older than retention_days"""
        return await info.context.decision_engine.cleanup_old_decisions(retention_days)


# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)


def create_graphql_router(
    decision_engine: DecisionEngine, auth_config: AuthConfig = None
) -> GraphQLRouter:
    """Create GraphQL router with decision engine context and security"""

    async def get_context(request: Request):
        # Extract user and client info from request state (set by middleware)
        user = getattr(request.state, "user", None)
        client_id = getattr(request.state, "client_id", "anonymous")

        return GraphQLContext(decision_engine, user, client_id)

    return GraphQLRouter(schema, context_getter=get_context, path="/graphql")
