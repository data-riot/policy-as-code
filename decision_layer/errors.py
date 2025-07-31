"""
Enhanced error handling for Decision Layer
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class DecisionLayerError(Exception):
    """Base exception for Decision Layer errors"""

    message: str
    error_code: str
    details: Optional[Dict[str, Any]] = None

    def __str__(self):
        return f"{self.error_code}: {self.message}"


class FunctionNotFoundError(DecisionLayerError):
    """Raised when a function is not found"""

    def __init__(self, function_id: str, version: Optional[str] = None):
        super().__init__(
            message=f"Function '{function_id}' not found",
            error_code="FUNCTION_NOT_FOUND",
            details={"function_id": function_id, "version": version},
        )


class VersionNotFoundError(DecisionLayerError):
    """Raised when a specific version is not found"""

    def __init__(self, function_id: str, version: str):
        super().__init__(
            message=f"Version '{version}' not found for function '{function_id}'",
            error_code="VERSION_NOT_FOUND",
            details={"function_id": function_id, "version": version},
        )


class ValidationError(DecisionLayerError):
    """Raised when input validation fails"""

    def __init__(self, field: str, message: str, value: Any = None):
        super().__init__(
            message=f"Validation error for field '{field}': {message}",
            error_code="VALIDATION_ERROR",
            details={"field": field, "message": message, "value": value},
        )


class ExecutionError(DecisionLayerError):
    """Raised when function execution fails"""

    def __init__(self, function_id: str, version: str, original_error: Exception):
        super().__init__(
            message=f"Execution failed for function '{function_id}' version '{version}': {str(original_error)}",
            error_code="EXECUTION_ERROR",
            details={
                "function_id": function_id,
                "version": version,
                "original_error": str(original_error),
                "error_type": type(original_error).__name__,
            },
        )


class DeploymentError(DecisionLayerError):
    """Raised when function deployment fails"""

    def __init__(self, function_id: str, version: str, reason: str):
        super().__init__(
            message=f"Deployment failed for function '{function_id}' version '{version}': {reason}",
            error_code="DEPLOYMENT_ERROR",
            details={"function_id": function_id, "version": version, "reason": reason},
        )


class StorageError(DecisionLayerError):
    """Raised when storage operations fail"""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Storage operation '{operation}' failed: {reason}",
            error_code="STORAGE_ERROR",
            details={"operation": operation, "reason": reason},
        )


class PluginError(DecisionLayerError):
    """Raised when plugin operations fail"""

    def __init__(self, plugin_name: str, operation: str, reason: str):
        super().__init__(
            message=f"Plugin '{plugin_name}' operation '{operation}' failed: {reason}",
            error_code="PLUGIN_ERROR",
            details={
                "plugin_name": plugin_name,
                "operation": operation,
                "reason": reason,
            },
        )


class ConfigurationError(DecisionLayerError):
    """Raised when configuration is invalid"""

    def __init__(self, config_key: str, reason: str):
        super().__init__(
            message=f"Configuration error for '{config_key}': {reason}",
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key, "reason": reason},
        )


def handle_decision_error(func):
    """Decorator to handle and convert exceptions to DecisionLayerError"""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DecisionLayerError:
            # Re-raise DecisionLayerError as-is
            raise
        except FileNotFoundError as e:
            # Convert file not found to appropriate error
            if "function" in str(e).lower():
                raise FunctionNotFoundError("unknown", "unknown")
            else:
                raise StorageError("read", str(e))
        except ValueError as e:
            # Convert ValueError to ValidationError
            raise ValidationError("input", str(e))
        except Exception as e:
            # Convert other exceptions to ExecutionError
            raise ExecutionError("unknown", "unknown", e)

    return wrapper


def create_error_response(error: DecisionLayerError) -> Dict[str, Any]:
    """Create a standardized error response"""
    return {
        "error": {
            "code": error.error_code,
            "message": error.message,
            "details": error.details or {},
        }
    }


def is_decision_error(exception: Exception) -> bool:
    """Check if an exception is a DecisionLayerError"""
    return isinstance(exception, DecisionLayerError)


def get_error_code(exception: Exception) -> str:
    """Get error code from exception"""
    if isinstance(exception, DecisionLayerError):
        return exception.error_code
    return "UNKNOWN_ERROR"
