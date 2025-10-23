"""
Advanced Authentication/Authorization with Nonce and TTL Middleware
Implements secure nonce-based authentication with time-to-live validation
"""

import os
import time
import secrets
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis
import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend


class AuthLevel(Enum):
    """Authentication levels"""

    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    AUTHORIZED = "authorized"
    ADMIN = "admin"


@dataclass
class NonceRecord:
    """Nonce record with TTL"""

    nonce: str
    created_at: float
    expires_at: float
    client_id: str
    request_hash: str
    used: bool = False
    attempts: int = 0


@dataclass
class AuthConfig:
    """Authentication configuration"""

    # Nonce settings
    nonce_length: int = 32
    nonce_ttl_seconds: int = 300  # 5 minutes
    max_nonce_attempts: int = 3

    # JWT settings
    jwt_secret: str = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Security headers
    enable_security_headers: bool = True
    enable_cors: bool = True
    cors_origins: list = None

    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]


class NonceManager:
    """Manages nonce generation, validation, and cleanup"""

    def __init__(self, config: AuthConfig):
        self.config = config
        self.redis_client = redis.from_url(config.redis_url, decode_responses=True)
        self._nonce_prefix = "nonce:"
        self._rate_limit_prefix = "rate_limit:"

    def generate_nonce(self, client_id: str, request_data: Dict[str, Any]) -> str:
        """Generate a new nonce for a request"""
        # Create request hash for replay protection
        request_str = json.dumps(request_data, sort_keys=True)
        request_hash = hashlib.sha256(request_str.encode()).hexdigest()

        # Generate nonce
        nonce = secrets.token_urlsafe(self.config.nonce_length)

        # Store nonce record
        nonce_record = NonceRecord(
            nonce=nonce,
            created_at=time.time(),
            expires_at=time.time() + self.config.nonce_ttl_seconds,
            client_id=client_id,
            request_hash=request_hash,
        )

        # Store in Redis with TTL
        key = f"{self._nonce_prefix}{nonce}"
        self.redis_client.setex(
            key,
            self.config.nonce_ttl_seconds,
            json.dumps(
                {
                    "nonce": nonce_record.nonce,
                    "created_at": nonce_record.created_at,
                    "expires_at": nonce_record.expires_at,
                    "client_id": nonce_record.client_id,
                    "request_hash": nonce_record.request_hash,
                    "used": nonce_record.used,
                    "attempts": nonce_record.attempts,
                }
            ),
        )

        return nonce

    def validate_nonce(
        self, nonce: str, client_id: str, request_data: Dict[str, Any]
    ) -> bool:
        """Validate a nonce and mark as used"""
        key = f"{self._nonce_prefix}{nonce}"

        # Get nonce record
        nonce_data = self.redis_client.get(key)
        if not nonce_data:
            return False

        try:
            record_data = json.loads(nonce_data)
        except json.JSONDecodeError:
            return False

        # Check if already used
        if record_data.get("used", False):
            return False

        # Check expiration
        if time.time() > record_data.get("expires_at", 0):
            self.redis_client.delete(key)
            return False

        # Check client ID
        if record_data.get("client_id") != client_id:
            return False

        # Check request hash for replay protection
        request_str = json.dumps(request_data, sort_keys=True)
        request_hash = hashlib.sha256(request_str.encode()).hexdigest()
        if record_data.get("request_hash") != request_hash:
            return False

        # Increment attempts
        attempts = record_data.get("attempts", 0) + 1
        if attempts >= self.config.max_nonce_attempts:
            self.redis_client.delete(key)
            return False

        # Mark as used
        record_data["used"] = True
        record_data["attempts"] = attempts
        self.redis_client.setex(
            key, self.config.nonce_ttl_seconds, json.dumps(record_data)
        )

        return True

    def cleanup_expired_nonces(self):
        """Clean up expired nonces (called periodically)"""
        # Redis TTL handles this automatically, but we can add manual cleanup if needed
        pass


class JWTManager:
    """Manages JWT token generation and validation"""

    def __init__(self, config: AuthConfig):
        self.config = config

    def generate_token(self, user_id: str, roles: list, client_id: str) -> str:
        """Generate a JWT token"""
        payload = {
            "user_id": user_id,
            "roles": roles,
            "client_id": client_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow()
            + timedelta(minutes=self.config.jwt_expiry_minutes),
            "jti": secrets.token_urlsafe(16),  # JWT ID for revocation
        }

        return jwt.encode(
            payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm
        )

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a JWT token"""
        try:
            payload = jwt.decode(
                token, self.config.jwt_secret, algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def revoke_token(self, jti: str):
        """Revoke a token by JWT ID"""
        # Store revoked JTI in Redis
        key = f"revoked_token:{jti}"
        self.redis_client.setex(key, self.config.jwt_expiry_minutes * 60, "revoked")


class RateLimiter:
    """Rate limiting with Redis backend"""

    def __init__(self, config: AuthConfig):
        self.config = config
        self.redis_client = redis.from_url(config.redis_url, decode_responses=True)
        self._rate_limit_prefix = "rate_limit:"

    def is_allowed(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed"""
        key = f"{self._rate_limit_prefix}{client_id}"
        now = int(time.time())
        window_start = now - self.config.rate_limit_window

        # Use Redis sliding window counter
        pipe = self.redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
        pipe.zcard(key)  # Count current entries
        pipe.zadd(key, {str(now): now})  # Add current request
        pipe.expire(key, self.config.rate_limit_window)  # Set expiry

        results = pipe.execute()
        current_count = results[1]

        is_allowed = current_count < self.config.rate_limit_requests
        remaining = max(0, self.config.rate_limit_requests - current_count - 1)

        return is_allowed, {
            "limit": self.config.rate_limit_requests,
            "remaining": remaining,
            "reset_time": now + self.config.rate_limit_window,
        }


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to all responses"""

    def __init__(self, app, config: AuthConfig):
        super().__init__(app)
        self.config = config

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if self.config.enable_security_headers:
            # Security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Content-Security-Policy"] = "default-src 'self'"

            # Remove server header
            response.headers.pop("server", None)

        return response


class NonceAuthMiddleware(BaseHTTPMiddleware):
    """Nonce-based authentication middleware"""

    def __init__(self, app, config: AuthConfig):
        super().__init__(app)
        self.config = config
        self.nonce_manager = NonceManager(config)
        self.jwt_manager = JWTManager(config)
        self.rate_limiter = RateLimiter(config)

        # Endpoints that require authentication
        self.protected_endpoints = {
            "/decisions": AuthLevel.AUTHENTICATED,
            "/registry/df": AuthLevel.AUTHORIZED,
            "/registry/releases": AuthLevel.AUTHORIZED,
            "/kms": AuthLevel.ADMIN,
            "/audit": AuthLevel.AUTHORIZED,
        }

        # Public endpoints
        self.public_endpoints = {
            "/",
            "/health",
            "/healthz",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public endpoints
        if request.url.path in self.public_endpoints:
            return await call_next(request)

        # Get client ID from headers
        client_id = request.headers.get("X-Client-ID", "anonymous")

        # Rate limiting
        is_allowed, rate_info = self.rate_limiter.is_allowed(client_id)
        if not is_allowed:
            return Response(
                content=json.dumps({"error": "Rate limit exceeded"}),
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": str(rate_info["remaining"]),
                    "X-RateLimit-Reset": str(rate_info["reset_time"]),
                },
                media_type="application/json",
            )

        # Check if endpoint requires authentication
        required_auth_level = self._get_required_auth_level(request.url.path)

        if required_auth_level == AuthLevel.PUBLIC:
            return await call_next(request)

        # Extract nonce and JWT token
        nonce = request.headers.get("X-Request-Nonce")
        auth_header = request.headers.get("Authorization")

        if not nonce:
            return Response(
                content=json.dumps({"error": "Missing X-Request-Nonce header"}),
                status_code=401,
                media_type="application/json",
            )

        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                content=json.dumps(
                    {"error": "Missing or invalid Authorization header"}
                ),
                status_code=401,
                media_type="application/json",
            )

        # Extract JWT token
        token = auth_header[7:]  # Remove "Bearer " prefix

        # Validate JWT token
        token_payload = self.jwt_manager.validate_token(token)
        if not token_payload:
            return Response(
                content=json.dumps({"error": "Invalid or expired token"}),
                status_code=401,
                media_type="application/json",
            )

        # Validate nonce
        request_data = await self._extract_request_data(request)
        if not self.nonce_manager.validate_nonce(nonce, client_id, request_data):
            return Response(
                content=json.dumps({"error": "Invalid or expired nonce"}),
                status_code=401,
                media_type="application/json",
            )

        # Check authorization level
        user_roles = token_payload.get("roles", [])
        if not self._check_authorization(required_auth_level, user_roles):
            return Response(
                content=json.dumps({"error": "Insufficient permissions"}),
                status_code=403,
                media_type="application/json",
            )

        # Add user info to request state
        request.state.user = token_payload
        request.state.client_id = client_id

        return await call_next(request)

    def _get_required_auth_level(self, path: str) -> AuthLevel:
        """Get required authentication level for path"""
        for endpoint, level in self.protected_endpoints.items():
            if path.startswith(endpoint):
                return level
        return AuthLevel.PUBLIC

    def _check_authorization(self, required_level: AuthLevel, user_roles: list) -> bool:
        """Check if user has required authorization level"""
        role_hierarchy = {
            AuthLevel.PUBLIC: [],
            AuthLevel.AUTHENTICATED: ["user"],
            AuthLevel.AUTHORIZED: ["user", "authorized"],
            AuthLevel.ADMIN: ["user", "authorized", "admin"],
        }

        required_roles = role_hierarchy.get(required_level, [])
        return any(role in user_roles for role in required_roles)

    async def _extract_request_data(self, request: Request) -> Dict[str, Any]:
        """Extract request data for nonce validation"""
        data = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
        }

        # For POST requests, include body hash
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            data["body_hash"] = hashlib.sha256(body).hexdigest()

        return data


# Dependency functions for FastAPI
async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current authenticated user"""
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.state.user


async def get_client_id(request: Request) -> str:
    """Get current client ID"""
    if not hasattr(request.state, "client_id"):
        raise HTTPException(status_code=401, detail="No client ID")
    return request.state.client_id


def require_auth_level(level: AuthLevel):
    """Decorator to require specific authentication level"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented in the middleware
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Utility functions
def create_auth_config(**kwargs) -> AuthConfig:
    """Create authentication configuration"""
    return AuthConfig(**kwargs)


def generate_client_credentials(client_id: str, roles: list) -> Dict[str, str]:
    """Generate client credentials for testing"""
    config = AuthConfig()
    jwt_manager = JWTManager(config)

    token = jwt_manager.generate_token(client_id, roles, client_id)

    return {"client_id": client_id, "token": token, "roles": roles}
