"""
Enhanced Decision Engine Implementation
Complete the core DecisionEngine with production-ready features
"""

import asyncio
import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass

from .errors import DecisionLayerError, ExecutionError, FunctionNotFoundError
from .security import SecurityConfig, SecurityManager
from .storage import StorageBackend, create_storage_backend
from .types import DecisionContext, DecisionResult
from ..tracing.enhanced_ledger import ImmutableTraceLedger
from ..monitoring.performance_monitor import PerformanceMonitor


class DecisionFunction(Protocol):
    """Protocol for decision functions"""

    def __call__(
        self, input_data: Dict[str, Any], context: DecisionContext
    ) -> Dict[str, Any]:
        ...


class DecisionRegistry:
    """Registry for decision functions"""

    def __init__(self):
        self._functions: Dict[str, DecisionFunction] = {}
        self._versions: Dict[str, List[str]] = {}

    def register(self, function_id: str, version: str, func: DecisionFunction):
        """Register a decision function"""
        full_id = f"{function_id}:{version}"
        self._functions[full_id] = func

        if function_id not in self._versions:
            self._versions[function_id] = []
        self._versions[function_id].append(version)

    def get_function(self, function_id: str, version: str) -> DecisionFunction:
        """Get a decision function by ID and version"""
        full_id = f"{function_id}:{version}"
        if full_id not in self._functions:
            raise FunctionNotFoundError(f"Function {full_id} not found")
        return self._functions[full_id]

    def list_functions(self) -> List[str]:
        """List all registered function IDs"""
        return list(self._versions.keys())


class DecisionEngine:
    """Core decision execution engine"""

    def __init__(self, security_config: Optional[SecurityConfig] = None):
        self.registry = DecisionRegistry()
        self.security_manager = SecurityManager(security_config or SecurityConfig())
        # Initialize with file storage by default
        self.storage_backend = create_storage_backend("file", {"path": "./functions"})
        self.trace_ledger = ImmutableTraceLedger(self.storage_backend)
        self.performance_monitor = PerformanceMonitor()
        self._execution_cache: Dict[str, DecisionResult] = {}

    def register_function(self, function_id: str, version: str, func: DecisionFunction):
        """Register a decision function"""
        self.registry.register(function_id, version, func)
        # Note: Trace ledger entry will be added asynchronously

    async def execute_decision(
        self,
        function_id: str,
        version: str,
        input_data: Dict[str, Any],
        context: Optional[DecisionContext] = None,
    ) -> DecisionResult:
        """Execute a decision function"""
        start_time = datetime.now()

        try:
            # Security check
            if not self.security_manager.is_function_allowed(function_id):
                raise ExecutionError(
                    f"Function {function_id} not allowed by security policy"
                )

            # Create context if not provided
            if context is None:
                input_hash = self._hash_input(input_data)
                context = DecisionContext(
                    function_id=function_id,
                    version=version,
                    input_hash=input_hash,
                    timestamp=start_time,
                    trace_id=str(uuid.uuid4()),
                )

            # Check cache
            cache_key = f"{function_id}:{version}:{context.input_hash}"
            if cache_key in self._execution_cache:
                cached_result = self._execution_cache[cache_key]
                # Update timestamp for cached result
                cached_result.timestamp = start_time
                return cached_result

            # Get and execute function
            decision_function = self.registry.get_function(function_id, version)

            # Execute with monitoring
            result_data = await self._execute_with_monitoring(
                decision_function, input_data, context
            )

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Create result
            result = DecisionResult(
                trace_id=context.trace_id,
                function_id=function_id,
                version=version,
                result=result_data,
                execution_time_ms=int(execution_time),
                timestamp=start_time,
                success=True,
            )

            # Cache result
            self._execution_cache[cache_key] = result

            # Store in persistent storage
            await self.storage_backend.store_decision(context, result_data)

            # Add to immutable trace ledger
            await self.trace_ledger.append_decision_execution(context, result)

            # Record performance metrics
            self.performance_monitor.record_decision_execution(
                function_id,
                result.execution_time_ms,
                result.success,
                result.error_message,
            )

            # Audit log
            self.security_manager.audit_log(
                function_id,
                "decision_executed",
                {"trace_id": context.trace_id, "success": True},
            )

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            result = DecisionResult(
                trace_id=context.trace_id if context else str(uuid.uuid4()),
                function_id=function_id,
                version=version,
                result={},
                execution_time_ms=int(execution_time),
                timestamp=start_time,
                success=False,
                error_message=str(e),
            )

            # Audit log error
            self.security_manager.audit_log(
                function_id,
                "decision_failed",
                {"trace_id": result.trace_id, "error": str(e)},
            )

            raise ExecutionError(f"Decision execution failed: {e}") from e

    async def _execute_with_monitoring(
        self,
        func: DecisionFunction,
        input_data: Dict[str, Any],
        context: DecisionContext,
    ) -> Dict[str, Any]:
        """Execute function with monitoring and error handling"""
        try:
            # Run in executor to prevent blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, func, input_data, context)

            # Validate result
            if not isinstance(result, dict):
                raise ExecutionError("Decision function must return a dictionary")

            return result

        except Exception as e:
            raise ExecutionError(f"Function execution error: {e}") from e

    def _hash_input(self, input_data: Dict[str, Any]) -> str:
        """Create hash of input data for caching"""
        input_str = json.dumps(input_data, sort_keys=True)
        return hashlib.sha256(input_str.encode()).hexdigest()

    async def get_decision_history(
        self, function_id: str, limit: int = 100, offset: int = 0
    ) -> List[DecisionResult]:
        """Get decision history for a function"""
        try:
            history_data = await self.storage_backend.get_decision_history(
                function_id, limit, offset
            )

            # Convert storage data to DecisionResult objects
            results = []
            for data in history_data:
                result = DecisionResult(
                    trace_id=data["trace_id"],
                    function_id=data["function_id"],
                    version=data["version"],
                    result=data["result"],
                    execution_time_ms=data["result"].get("execution_time_ms", 0),
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    success=data["result"].get("success", False),
                    error_message=data["result"].get("error_message"),
                )
                results.append(result)

            return results
        except Exception as e:
            raise ExecutionError(f"Failed to get decision history: {e}")

    async def get_decisions_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 100
    ) -> List[DecisionResult]:
        """Get decisions within a date range"""
        try:
            history_data = await self.storage_backend.get_decisions_by_date_range(
                start_date, end_date, limit
            )

            # Convert storage data to DecisionResult objects
            results = []
            for data in history_data:
                result = DecisionResult(
                    trace_id=data["trace_id"],
                    function_id=data["function_id"],
                    version=data["version"],
                    result=data["result"],
                    execution_time_ms=data["result"].get("execution_time_ms", 0),
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    success=data["result"].get("success", False),
                    error_message=data["result"].get("error_message"),
                )
                results.append(result)

            return results
        except Exception as e:
            raise ExecutionError(f"Failed to get decisions by date range: {e}")

    async def cleanup_old_decisions(self, retention_days: int) -> int:
        """Clean up decisions older than retention_days"""
        try:
            deleted_count = await self.storage_backend.cleanup_old_decisions(
                retention_days
            )

            # Also clean up cache
            cache_keys_to_remove = []
            for key, result in self._execution_cache.items():
                if (datetime.now() - result.timestamp).days > retention_days:
                    cache_keys_to_remove.append(key)

            for key in cache_keys_to_remove:
                del self._execution_cache[key]

            return deleted_count
        except Exception as e:
            raise ExecutionError(f"Failed to cleanup old decisions: {e}")

    async def get_decision_stats(self, function_id: str) -> Dict[str, Any]:
        """Get decision statistics for a function"""
        try:
            return await self.storage_backend.get_decision_stats(function_id)
        except Exception as e:
            raise ExecutionError(f"Failed to get decision stats: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the decision engine"""
        ledger_stats = self.trace_ledger.get_ledger_stats()
        performance_summary = self.performance_monitor.get_performance_summary()

        return {
            "status": "healthy",
            "registered_functions": len(self.registry.list_functions()),
            "cache_size": len(self._execution_cache),
            "trace_ledger": ledger_stats,
            "performance": performance_summary,
            "timestamp": datetime.now().isoformat(),
        }

    async def verify_trace_integrity(self) -> Dict[str, Any]:
        """Verify the integrity of the trace ledger"""
        return self.trace_ledger.verify_integrity()

    async def get_trace_entries(
        self, function_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trace entries, optionally filtered by function"""
        if function_id:
            entries = self.trace_ledger.get_entries_by_function(function_id)
        else:
            entries = self.trace_ledger.get_latest_entries(limit)

        return [
            {
                "entry_id": entry.entry_id,
                "entry_type": entry.entry_type.value,
                "timestamp": entry.timestamp.isoformat(),
                "function_id": entry.data.get("function_id"),
                "hash": entry.hash,
                "previous_hash": entry.previous_hash,
                "signature": entry.signature,
            }
            for entry in entries
        ]

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return self.performance_monitor.get_performance_summary()

    async def get_function_performance(self, function_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific function"""
        return self.performance_monitor.get_metrics_for_function(function_id)

    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active performance alerts"""
        alerts = self.performance_monitor.get_active_alerts()
        return [
            {
                "rule_name": alert.rule_name,
                "metric_name": alert.metric_name,
                "value": alert.value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp.isoformat(),
                "message": alert.message,
                "severity": alert.severity,
            }
            for alert in alerts
        ]

    def add_alert_callback(self, callback):
        """Add alert notification callback"""
        self.performance_monitor.add_alert_callback(callback)

    async def start_monitoring(self, interval_seconds: int = 60):
        """Start performance monitoring"""
        await self.performance_monitor.start_monitoring(interval_seconds)

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.performance_monitor.stop_monitoring()
