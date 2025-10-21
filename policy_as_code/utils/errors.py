"""
Custom exception classes for Decision Layer
"""

from typing import Any, Dict, Optional


class DecisionLayerError(Exception):
    """Base exception for Decision Layer"""

    def __init__(
        self, message: str, error_code: str = "UNKNOWN", details: Optional[Dict] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(DecisionLayerError):
    """Raised when input validation fails"""

    def __init__(self, field: str, message: str):
        super().__init__(message, "VALIDATION_ERROR", {"field": field})


class ExecutionError(DecisionLayerError):
    """Raised when decision execution fails"""

    def __init__(self, function_id: str, version: str, original_error: Exception):
        super().__init__(
            f"Execution failed for {function_id} v{version}: {str(original_error)}",
            "EXECUTION_ERROR",
            {
                "function_id": function_id,
                "version": version,
                "original_error": str(original_error),
            },
        )


class DeploymentError(DecisionLayerError):
    """Raised when function deployment fails"""

    def __init__(self, function_id: str, version: str, reason: str):
        super().__init__(
            f"Deployment failed for {function_id} v{version}: {reason}",
            "DEPLOYMENT_ERROR",
            {"function_id": function_id, "version": version, "reason": reason},
        )


class FunctionNotFoundError(DecisionLayerError):
    """Raised when a function is not found"""

    def __init__(self, function_id: str, version: Optional[str] = None):
        version_info = f" v{version}" if version else ""
        super().__init__(
            f"Function {function_id}{version_info} not found",
            "FUNCTION_NOT_FOUND",
            {"function_id": function_id, "version": version},
        )


class StorageError(DecisionLayerError):
    """Raised when storage operations fail"""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            f"Storage operation '{operation}' failed: {reason}",
            "STORAGE_ERROR",
            {"operation": operation, "reason": reason},
        )


class RegistryError(DecisionLayerError):
    """Raised when registry operations fail"""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            f"Registry operation '{operation}' failed: {reason}",
            "REGISTRY_ERROR",
            {"operation": operation, "reason": reason},
        )


class ShadowExecutionError(DecisionLayerError):
    """Raised when shadow execution fails"""

    def __init__(self, function_id: str, version: str, reason: str):
        super().__init__(
            f"Shadow execution failed for {function_id} v{version}: {reason}",
            "SHADOW_EXECUTION_ERROR",
            {"function_id": function_id, "version": version, "reason": reason},
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
