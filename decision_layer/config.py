"""
Configuration validation for Decision Layer
"""

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator


class StorageConfig(BaseModel):
    """Storage configuration"""

    backend: str = Field(default="file", description="Storage backend type")
    path: Optional[str] = Field(
        default="./functions", description="Storage path for file backend"
    )
    connection_string: Optional[str] = Field(
        default=None, description="Database connection string"
    )

    @validator("backend")
    def validate_backend(cls, v):
        if v not in ["file", "postgresql"]:
            raise ValueError('Storage backend must be "file" or "postgresql"')
        return v

    @validator("connection_string")
    def validate_connection_string(cls, v, values):
        if values.get("backend") == "postgresql" and not v:
            raise ValueError("Connection string is required for PostgreSQL backend")
        return v


class SecurityConfig(BaseModel):
    """Security configuration"""

    enable_auth: bool = Field(
        default=False, description="Enable API key authentication"
    )
    api_key: Optional[str] = Field(
        default=None, description="API key for authentication"
    )
    enable_rate_limiting: bool = Field(
        default=False, description="Enable rate limiting"
    )
    enable_input_sanitization: bool = Field(
        default=True, description="Enable input sanitization"
    )
    enable_trace_sanitization: bool = Field(
        default=True, description="Enable trace sanitization"
    )
    max_input_size: int = Field(
        default=1024 * 1024, description="Maximum input size in bytes"
    )
    rate_limit_requests: int = Field(
        default=100, description="Rate limit requests per window"
    )
    rate_limit_window: int = Field(
        default=60, description="Rate limit window in seconds"
    )


class PluginConfig(BaseModel):
    """Plugin configuration"""

    enabled: bool = Field(default=True, description="Enable plugin")
    path: Optional[str] = Field(default=None, description="Plugin-specific path")


class PluginsConfig(BaseModel):
    """Plugins configuration"""

    validation: PluginConfig = Field(default_factory=PluginConfig)
    tracing: PluginConfig = Field(default_factory=PluginConfig)
    caching: PluginConfig = Field(default_factory=PluginConfig)


class APIConfig(BaseModel):
    """API configuration"""

    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    enable_docs: bool = Field(default=True, description="Enable API documentation")
    enable_cors: bool = Field(default=True, description="Enable CORS")


class DecisionLayerConfig(BaseModel):
    """Main configuration for Decision Layer"""

    storage: StorageConfig = Field(default_factory=StorageConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    plugins: PluginsConfig = Field(default_factory=PluginsConfig)
    api: APIConfig = Field(default_factory=APIConfig)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "DecisionLayerConfig":
        """Create config from dictionary"""
        return cls(**config_dict)

    @classmethod
    def from_file(cls, config_path: str) -> "DecisionLayerConfig":
        """Load config from file"""
        import yaml

        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_file, "r") as f:
            config_dict = yaml.safe_load(f) or {}

        return cls.from_dict(config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return self.dict()

    def validate(self) -> None:
        """Validate configuration"""
        # Additional validation logic can be added here
        pass


def load_config(config_path: Optional[str] = None) -> DecisionLayerConfig:
    """Load configuration with fallbacks"""
    if config_path:
        try:
            return DecisionLayerConfig.from_file(config_path)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")

    # Try default config locations
    default_paths = [
        "config.yaml",
        "config.yml",
        "decision-layer.yaml",
        "decision-layer.yml",
    ]

    for path in default_paths:
        try:
            return DecisionLayerConfig.from_file(path)
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"Warning: Failed to load config from {path}: {e}")

    # Return default config
    return DecisionLayerConfig()
