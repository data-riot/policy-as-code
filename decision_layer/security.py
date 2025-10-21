"""
Basic security features for Decision Layer
"""

import hashlib
import hmac

# datetime imports removed as they're not used
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SecurityConfig:
    """Security configuration"""

    enable_auth: bool = False
    enable_rate_limiting: bool = False
    enable_input_sanitization: bool = True
    enable_trace_sanitization: bool = True
    max_input_size: int = 1024 * 1024  # 1MB
    rate_limit_requests: int = 100  # requests per minute
    rate_limit_window: int = 60  # seconds
    sanitize_fields: Optional[List[str]] = None

    def __post_init__(self):
        if self.sanitize_fields is None:
            self.sanitize_fields = [
                "password",
                "token",
                "secret",
                "key",
                "ssn",
                "credit_card",
                "card_number",
                "cvv",
                "pin",
            ]


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}  # client_id -> list of timestamps

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed"""
        now = time.time()

        if client_id not in self.requests:
            self.requests[client_id] = []

        # Remove old requests outside window
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] if now - ts < self.window_seconds
        ]

        # Check if under limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False

        # Add current request
        self.requests[client_id].append(now)
        return True

    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client"""
        now = time.time()

        if client_id not in self.requests:
            return self.max_requests

        # Remove old requests
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] if now - ts < self.window_seconds
        ]

        return max(0, self.max_requests - len(self.requests[client_id]))


class InputSanitizer:
    """Sanitize sensitive input data"""

    def __init__(self, sanitize_fields: List[str]):
        self.sanitize_fields = sanitize_fields

    def sanitize_data(self, data: Any) -> Any:
        """Recursively sanitize data"""
        if isinstance(data, dict):
            return {k: self.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return self.sanitize_string(data)
        else:
            return data

    def sanitize_string(self, value: str) -> str:
        """Sanitize a string value"""
        # Check if field name contains sensitive keywords
        if any(field in value.lower() for field in self.sanitize_fields):
            return "[SANITIZED]"
        return value

    def sanitize_trace(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize trace data"""
        sanitized = trace_data.copy()

        # Sanitize input
        if "input" in sanitized:
            sanitized["input"] = self.sanitize_data(sanitized["input"])

        # Sanitize output
        if "output" in sanitized:
            sanitized["output"] = self.sanitize_data(sanitized["output"])

        return sanitized


class SecurityManager:
    """Main security manager"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.rate_limiter = (
            RateLimiter(config.rate_limit_requests, config.rate_limit_window)
            if config.enable_rate_limiting
            else None
        )
        self.input_sanitizer = (
            InputSanitizer(config.sanitize_fields or [])
            if config.enable_input_sanitization
            else None
        )

    def validate_input_size(self, data: Dict[str, Any]) -> bool:
        """Validate input data size"""
        data_size = len(json.dumps(data))
        return data_size <= self.config.max_input_size

    def check_rate_limit(self, client_id: str) -> bool:
        """Check rate limit for client"""
        if not self.config.enable_rate_limiting or self.rate_limiter is None:
            return True
        return self.rate_limiter.is_allowed(client_id)

    def get_rate_limit_info(self, client_id: str) -> Dict[str, Any]:
        """Get rate limit information for client"""
        if not self.config.enable_rate_limiting or self.rate_limiter is None:
            return {"enabled": False}

        return {
            "enabled": True,
            "remaining": self.rate_limiter.get_remaining(client_id),
            "limit": self.config.rate_limit_requests,
            "window": self.config.rate_limit_window,
        }

    def sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data"""
        if not self.config.enable_input_sanitization or self.input_sanitizer is None:
            return data
        return self.input_sanitizer.sanitize_data(data)

    def sanitize_trace(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize trace data"""
        if not self.config.enable_trace_sanitization or self.input_sanitizer is None:
            return trace_data
        return self.input_sanitizer.sanitize_trace(trace_data)

    def validate_function_code(self, function_code: str) -> bool:
        """Basic validation of function code"""
        # Check for potentially dangerous imports
        dangerous_imports = [
            "os",
            "subprocess",
            "sys",
            "importlib",
            "eval",
            "exec",
            "open",
            "file",
        ]

        code_lower = function_code.lower()
        for dangerous in dangerous_imports:
            if f"import {dangerous}" in code_lower or f"from {dangerous}" in code_lower:
                return False

        # Check for eval/exec usage
        if "eval(" in code_lower or "exec(" in code_lower:
            return False

        return True


def create_security_manager(config: Optional[SecurityConfig] = None) -> SecurityManager:
    """Create a security manager with default or custom config"""
    if config is None:
        config = SecurityConfig()
    return SecurityManager(config)


def generate_client_id() -> str:
    """Generate a unique client ID"""
    return secrets.token_urlsafe(16)


def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for storage"""
    return hashlib.sha256(data.encode()).hexdigest()


def verify_signature(data: str, signature: str, secret: str) -> bool:
    """Verify HMAC signature"""
    expected_signature = hmac.new(
        secret.encode(), data.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


def create_signature(data: str, secret: str) -> str:
    """Create HMAC signature for data"""
    return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()
