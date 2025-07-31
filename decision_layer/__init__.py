"""
Decision Layer - Elegant decision management

A minimal, composable, and extensible decision engine that treats decision logic
as software with version control, testing, and observability.
"""

from .api import DecisionLayerAPI, DecisionRequest, DecisionResponse, create_api
from .auth import APIKeyAuth, create_auth_middleware, require_auth
from .config import DecisionLayerConfig, load_config
from .core import (
    CachingPlugin,
    DecisionContext,
    DecisionEngine,
    DecisionFunction,
    DecisionPlugin,
    TracingPlugin,
    ValidationPlugin,
)
from .errors import (
    ConfigurationError,
    DecisionLayerError,
    DeploymentError,
    ExecutionError,
    FunctionNotFoundError,
    PluginError,
    StorageError,
    ValidationError,
    VersionNotFoundError,
)
from .security import InputSanitizer, RateLimiter, SecurityConfig, SecurityManager
from .storage import (
    FileStorage,
    PostgreSQLStorage,
    StorageBackend,
    create_storage_backend,
)

__version__ = "2.0.0"
__author__ = "Decision Layer Team"

__all__ = [
    "DecisionEngine",
    "DecisionContext",
    "DecisionFunction",
    "DecisionPlugin",
    "StorageBackend",
    "FileStorage",
    "ValidationPlugin",
    "TracingPlugin",
    "CachingPlugin",
]
