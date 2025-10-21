"""
Core components for the Decision Layer framework
"""

import asyncio
import hashlib
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from .errors import (
    DecisionLayerError,
    DeploymentError,
    ExecutionError,
    FunctionNotFoundError,
    ValidationError,
)
from .security import SecurityConfig, SecurityManager
from .storage import StorageBackend, create_storage_backend


@dataclass(frozen=True)
class DecisionContext:
    """Immutable decision execution context"""

    function_id: str
    version: str
    input_hash: str
    timestamp: datetime
    trace_id: str


class DecisionFunction(Protocol):
    """Protocol for decision functions - elegant abstraction"""

    def __call__(
        self, input_data: Dict[str, Any], context: DecisionContext
    ) -> Dict[str, Any]:
        ...


class DecisionPlugin(ABC):
    """Base class for decision plugins"""

    @abstractmethod
    async def process(
        self, data: Dict[str, Any], context: DecisionContext
    ) -> Dict[str, Any]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


# Storage backends moved to separate module


class ValidationPlugin(DecisionPlugin):
    """Schema validation plugin"""

    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        self.schema = schema

    async def process(
        self, data: Dict[str, Any], context: DecisionContext
    ) -> Dict[str, Any]:
        """Validate input data against schema"""
        if self.schema:
            # Simple validation - in production you'd want more sophisticated validation
            for field, field_spec in self.schema.get("input", {}).items():
                if field_spec.get("required", False) and field not in data:
                    raise ValueError(f"Required field '{field}' is missing")
        return data

    @property
    def name(self) -> str:
        return "validation"


class TracingPlugin(DecisionPlugin):
    """Structured tracing plugin"""

    def __init__(self, trace_dir: str = "./traces"):
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(exist_ok=True)

    async def process(
        self, data: Dict[str, Any], context: DecisionContext
    ) -> Dict[str, Any]:
        """Add trace metadata to data"""
        data["_trace"] = {
            "trace_id": context.trace_id,
            "timestamp": context.timestamp.isoformat(),
            "function_id": context.function_id,
            "version": context.version,
            "input_hash": context.input_hash,
        }
        return data

    async def store_trace(
        self,
        context: DecisionContext,
        input_data: Dict[str, Any],
        result: Dict[str, Any],
        status: str,
    ):
        """Store trace to file"""
        trace_data = {
            "trace_id": context.trace_id,
            "function_id": context.function_id,
            "version": context.version,
            "input_hash": context.input_hash,
            "timestamp": context.timestamp.isoformat(),
            "input": input_data,
            "output": result,
            "status": status,
        }

        trace_file = (
            self.trace_dir
            / f"{context.function_id}_{context.timestamp.strftime('%Y%m%d')}.jsonl"
        )
        with open(trace_file, "a") as f:
            f.write(json.dumps(trace_data) + "\n")

    @property
    def name(self) -> str:
        return "tracing"


class CachingPlugin(DecisionPlugin):
    """Simple in-memory caching plugin"""

    def __init__(self):
        self.cache = {}

    async def process(
        self, data: Dict[str, Any], context: DecisionContext
    ) -> Dict[str, Any]:
        """Check cache for existing result"""
        cache_key = f"{context.function_id}:{context.version}:{context.input_hash}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        return data

    async def cache_result(self, context: DecisionContext, result: Dict[str, Any]):
        """Cache the result"""
        cache_key = f"{context.function_id}:{context.version}:{context.input_hash}"
        self.cache[cache_key] = result

    @property
    def name(self) -> str:
        return "caching"


class DecisionEngine:
    """Elegant, minimal decision engine"""

    def __init__(
        self, storage_backend: str = "file", config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        self.storage = self._create_storage(storage_backend)
        self.plugins = {"pre_execute": [], "post_execute": []}
        self._load_default_plugins()

        # Initialize security manager
        security_config = SecurityConfig(
            enable_rate_limiting=self.config.get("security", {}).get(
                "enable_rate_limiting", False
            ),
            enable_input_sanitization=self.config.get("security", {}).get(
                "enable_input_sanitization", True
            ),
            enable_trace_sanitization=self.config.get("security", {}).get(
                "enable_trace_sanitization", True
            ),
        )
        self.security_manager = SecurityManager(security_config)

    def _create_storage(self, backend: str) -> StorageBackend:
        """Create storage backend"""
        storage_config = self.config.get("storage", {})
        return create_storage_backend(backend, storage_config)

    def _load_default_plugins(self):
        """Load default plugins"""
        # Add validation plugin if enabled
        if self.config.get("plugins", {}).get("validation", {}).get("enabled", True):
            validation_plugin = ValidationPlugin()
            self.plugins["pre_execute"].append(validation_plugin)

        # Add tracing plugin if enabled
        if self.config.get("plugins", {}).get("tracing", {}).get("enabled", True):
            trace_dir = (
                self.config.get("plugins", {})
                .get("tracing", {})
                .get("path", "./traces")
            )
            tracing_plugin = TracingPlugin(trace_dir)
            self.plugins["pre_execute"].append(tracing_plugin)
            self._tracing_plugin = tracing_plugin  # Store reference for trace storage

        # Add caching plugin if enabled
        if self.config.get("plugins", {}).get("caching", {}).get("enabled", True):
            caching_plugin = CachingPlugin()
            self.plugins["post_execute"].append(caching_plugin)
            self._caching_plugin = caching_plugin  # Store reference for cache storage

    def _hash_input(self, input_data: Dict[str, Any]) -> str:
        """Generate hash of input data"""
        json_str = json.dumps(input_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]

    def _generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        return str(uuid.uuid4())

    async def execute(
        self,
        function_id: str,
        input_data: Dict[str, Any],
        version: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute decision with elegant error handling"""

        # Security checks
        if not self.security_manager.validate_input_size(input_data):
            raise ValidationError("input", "Input data too large")

        if client_id and not self.security_manager.check_rate_limit(client_id):
            raise ValidationError("rate_limit", "Rate limit exceeded")

        # Sanitize input
        sanitized_input = self.security_manager.sanitize_input(input_data)

        # Use latest version if not specified
        if version is None:
            versions = await self.storage.list_versions(function_id)
            if not versions:
                raise FunctionNotFoundError(function_id, version)
            version = versions[-1]  # Latest version

        # Create context
        context = DecisionContext(
            function_id=function_id,
            version=version,
            input_hash=self._hash_input(sanitized_input),
            timestamp=datetime.utcnow(),
            trace_id=self._generate_trace_id(),
        )

        try:
            # Load function
            function = await self.storage.load_function_object(function_id, version)

            # Execute with plugins
            result = await self._execute_with_plugins(
                function, sanitized_input, context
            )

            # Store trace
            if hasattr(self, "_tracing_plugin"):
                trace_data = {"input": sanitized_input, "output": result}
                sanitized_trace = self.security_manager.sanitize_trace(trace_data)
                await self._tracing_plugin.store_trace(
                    context,
                    sanitized_trace["input"],
                    sanitized_trace["output"],
                    "success",
                )

            # Cache result
            if hasattr(self, "_caching_plugin"):
                await self._caching_plugin.cache_result(context, result)

            return result

        except DecisionLayerError:
            # Re-raise DecisionLayerError as-is
            raise
        except Exception as e:
            # Store error trace
            if hasattr(self, "_tracing_plugin"):
                error_trace = {"input": sanitized_input, "output": {"error": str(e)}}
                sanitized_error_trace = self.security_manager.sanitize_trace(
                    error_trace
                )
                await self._tracing_plugin.store_trace(
                    context,
                    sanitized_error_trace["input"],
                    sanitized_error_trace["output"],
                    "error",
                )

            # Convert to ExecutionError
            raise ExecutionError(function_id, version, e)

    async def _execute_with_plugins(
        self,
        function: DecisionFunction,
        input_data: Dict[str, Any],
        context: DecisionContext,
    ) -> Dict[str, Any]:
        """Execute with plugin pipeline"""

        # Pre-execution plugins
        processed_input = input_data
        for plugin in self.plugins["pre_execute"]:
            processed_input = await plugin.process(processed_input, context)

        # Execute (handle both sync and async functions)
        if asyncio.iscoroutinefunction(function):
            result = await function(processed_input, context)
        else:
            result = function(processed_input, context)

        # Post-execution plugins
        processed_result = result
        for plugin in self.plugins["post_execute"]:
            processed_result = await plugin.process(processed_result, context)

        return processed_result

    async def deploy_function(self, function_id: str, version: str, function_code: str):
        """Deploy a new function version"""
        # Security validation
        if not self.security_manager.validate_function_code(function_code):
            raise DeploymentError(
                function_id, version, "Function code contains dangerous operations"
            )

        await self.storage.save_function(function_id, version, function_code)

    async def list_functions(self) -> List[str]:
        """List all available functions"""
        return await self.storage.list_functions()

    async def list_versions(self, function_id: str) -> List[str]:
        """List all versions of a function"""
        return await self.storage.list_versions(function_id)
