"""
Ingress Security and Rate Limiting
Comprehensive ingress protection with security headers, rate limiting, and DDoS protection
"""

import os
import time
import json
import hashlib
import ipaddress
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque

from fastapi import FastAPI, Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis
from pydantic import BaseModel


class SecurityLevel(Enum):
    """Security levels for different environments"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class SecurityConfig:
    """Security configuration for ingress"""

    # Environment
    environment: SecurityLevel = SecurityLevel.PRODUCTION

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    burst_limit: int = 200

    # DDoS protection
    ddos_protection_enabled: bool = True
    ddos_threshold: int = 50  # requests per second
    ddos_window: int = 10  # seconds
    ddos_block_duration: int = 300  # 5 minutes

    # IP whitelist/blacklist
    ip_whitelist: Optional[Set[str]] = None
    ip_blacklist: Optional[Set[str]] = None

    # Security headers
    enable_security_headers: bool = True
    enable_cors: bool = True
    cors_origins: List[str] = None
    cors_methods: List[str] = None
    cors_headers: List[str] = None

    # Content Security Policy
    csp_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

    # HSTS
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True

    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = (
                ["*"] if self.environment == SecurityLevel.DEVELOPMENT else []
            )
        if self.cors_methods is None:
            self.cors_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        if self.cors_headers is None:
            self.cors_headers = ["*"]


class RateLimiter:
    """Advanced rate limiter with sliding window and burst protection"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.redis_client = redis.from_url(config.redis_url, decode_responses=True)

        # In-memory fallback for when Redis is unavailable
        self.memory_store: Dict[str, deque] = defaultdict(lambda: deque())
        self.memory_cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()

    def is_allowed(
        self, client_id: str, endpoint: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed with sliding window"""
        now = time.time()
        key = f"rate_limit:{client_id}:{endpoint or 'global'}"

        try:
            # Try Redis first
            return self._check_redis_rate_limit(key, now)
        except Exception:
            # Fallback to memory
            return self._check_memory_rate_limit(client_id, endpoint, now)

    def _check_redis_rate_limit(
        self, key: str, now: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis"""
        window_start = now - self.config.rate_limit_window

        # Use Redis sorted set for sliding window
        pipe = self.redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # Remove old entries
        pipe.zcard(key)  # Count current entries
        pipe.zadd(key, {str(now): now})  # Add current request
        pipe.expire(key, self.config.rate_limit_window)  # Set expiry

        results = pipe.execute()
        current_count = results[1]

        # Check burst limit
        burst_key = f"burst:{key}"
        burst_count = self.redis_client.incr(burst_key)
        if burst_count == 1:
            self.redis_client.expire(burst_key, 1)  # 1 second window for burst

        is_allowed = (
            current_count < self.config.rate_limit_requests
            and burst_count <= self.config.burst_limit
        )

        remaining = max(0, self.config.rate_limit_requests - current_count - 1)

        return is_allowed, {
            "limit": self.config.rate_limit_requests,
            "remaining": remaining,
            "reset_time": now + self.config.rate_limit_window,
            "burst_remaining": max(0, self.config.burst_limit - burst_count),
        }

    def _check_memory_rate_limit(
        self, client_id: str, endpoint: str, now: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using in-memory store"""
        key = f"{client_id}:{endpoint or 'global'}"
        requests = self.memory_store[key]

        # Clean old requests
        window_start = now - self.config.rate_limit_window
        while requests and requests[0] < window_start:
            requests.popleft()

        # Check limits
        current_count = len(requests)
        is_allowed = current_count < self.config.rate_limit_requests

        if is_allowed:
            requests.append(now)

        remaining = max(0, self.config.rate_limit_requests - current_count - 1)

        # Cleanup old entries periodically
        if now - self.last_cleanup > self.memory_cleanup_interval:
            self._cleanup_memory_store(now)
            self.last_cleanup = now

        return is_allowed, {
            "limit": self.config.rate_limit_requests,
            "remaining": remaining,
            "reset_time": now + self.config.rate_limit_window,
        }

    def _cleanup_memory_store(self, now: float):
        """Clean up old entries from memory store"""
        cutoff = now - self.config.rate_limit_window
        keys_to_remove = []

        for key, requests in self.memory_store.items():
            # Remove old requests
            while requests and requests[0] < cutoff:
                requests.popleft()

            # Remove empty entries
            if not requests:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.memory_store[key]


class DDoSProtection:
    """DDoS protection with IP-based blocking"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.redis_client = redis.from_url(config.redis_url, decode_responses=True)

        # In-memory tracking
        self.ip_requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.blocked_ips: Set[str] = set()

    def check_ddos(self, client_ip: str) -> Tuple[bool, Optional[str]]:
        """Check for DDoS attack from IP"""
        if not self.config.ddos_protection_enabled:
            return True, None

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            return False, "IP blocked due to DDoS activity"

        now = time.time()

        try:
            # Try Redis first
            return self._check_redis_ddos(client_ip, now)
        except Exception:
            # Fallback to memory
            return self._check_memory_ddos(client_ip, now)

    def _check_redis_ddos(
        self, client_ip: str, now: float
    ) -> Tuple[bool, Optional[str]]:
        """Check DDoS using Redis"""
        key = f"ddos:{client_ip}"
        window_start = now - self.config.ddos_window

        # Count requests in window
        pipe = self.redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, self.config.ddos_window)

        results = pipe.execute()
        request_count = results[1]

        if request_count > self.config.ddos_threshold:
            # Block IP
            block_key = f"blocked_ip:{client_ip}"
            self.redis_client.setex(
                block_key, self.config.ddos_block_duration, "blocked"
            )
            self.blocked_ips.add(client_ip)

            return (
                False,
                f"DDoS detected: {request_count} requests in {self.config.ddos_window}s",
            )

        return True, None

    def _check_memory_ddos(
        self, client_ip: str, now: float
    ) -> Tuple[bool, Optional[str]]:
        """Check DDoS using in-memory tracking"""
        requests = self.ip_requests[client_ip]
        window_start = now - self.config.ddos_window

        # Remove old requests
        while requests and requests[0] < window_start:
            requests.popleft()

        # Add current request
        requests.append(now)

        if len(requests) > self.config.ddos_threshold:
            self.blocked_ips.add(client_ip)
            return (
                False,
                f"DDoS detected: {len(requests)} requests in {self.config.ddos_window}s",
            )

        return True, None


class IPFilter:
    """IP whitelist/blacklist filter"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.whitelist = (
            self._parse_ip_list(config.ip_whitelist) if config.ip_whitelist else None
        )
        self.blacklist = (
            self._parse_ip_list(config.ip_blacklist) if config.ip_blacklist else None
        )

    def _parse_ip_list(self, ip_list: Set[str]) -> List[ipaddress.IPv4Network]:
        """Parse IP list into network objects"""
        networks = []
        for ip_str in ip_list:
            try:
                if "/" in ip_str:
                    networks.append(ipaddress.IPv4Network(ip_str))
                else:
                    networks.append(ipaddress.IPv4Network(f"{ip_str}/32"))
            except ValueError:
                continue
        return networks

    def is_allowed(self, client_ip: str) -> Tuple[bool, Optional[str]]:
        """Check if IP is allowed"""
        try:
            ip = ipaddress.IPv4Address(client_ip)
        except ValueError:
            return False, "Invalid IP address"

        # Check blacklist first
        if self.blacklist:
            for network in self.blacklist:
                if ip in network:
                    return False, "IP in blacklist"

        # Check whitelist
        if self.whitelist:
            for network in self.whitelist:
                if ip in network:
                    return True, None
            return False, "IP not in whitelist"

        return True, None


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Comprehensive security headers middleware"""

    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if self.config.enable_security_headers:
            # Basic security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

            # HSTS
            if self.config.environment == SecurityLevel.PRODUCTION:
                hsts_value = f"max-age={self.config.hsts_max_age}"
                if self.config.hsts_include_subdomains:
                    hsts_value += "; includeSubDomains"
                response.headers["Strict-Transport-Security"] = hsts_value

            # Content Security Policy
            response.headers["Content-Security-Policy"] = self.config.csp_policy

            # CORS headers
            if self.config.enable_cors:
                origin = request.headers.get("origin")
                if origin and (
                    origin in self.config.cors_origins
                    or "*" in self.config.cors_origins
                ):
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Access-Control-Allow-Methods"] = ", ".join(
                        self.config.cors_methods
                    )
                    response.headers["Access-Control-Allow-Headers"] = ", ".join(
                        self.config.cors_headers
                    )
                    response.headers["Access-Control-Allow-Credentials"] = "true"

            # Remove server header
            response.headers.pop("server", None)

            # Add custom security header
            response.headers["X-Policy-As-Code-Version"] = "1.0.0"

        return response


class IngressSecurityMiddleware(BaseHTTPMiddleware):
    """Main ingress security middleware"""

    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.rate_limiter = RateLimiter(config)
        self.ddos_protection = DDoSProtection(config)
        self.ip_filter = IPFilter(config)

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = self._get_client_ip(request)

        # IP filtering
        ip_allowed, ip_message = self.ip_filter.is_allowed(client_ip)
        if not ip_allowed:
            return JSONResponse(
                content={"error": f"Access denied: {ip_message}"}, status_code=403
            )

        # DDoS protection
        ddos_allowed, ddos_message = self.ddos_protection.check_ddos(client_ip)
        if not ddos_allowed:
            return JSONResponse(
                content={"error": f"DDoS protection: {ddos_message}"}, status_code=429
            )

        # Rate limiting
        if self.config.rate_limit_enabled:
            client_id = self._get_client_id(request)
            endpoint = request.url.path

            rate_allowed, rate_info = self.rate_limiter.is_allowed(client_id, endpoint)
            if not rate_allowed:
                return JSONResponse(
                    content={"error": "Rate limit exceeded"},
                    status_code=429,
                    headers={
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_info["remaining"]),
                        "X-RateLimit-Reset": str(int(rate_info["reset_time"])),
                    },
                )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        if self.config.rate_limit_enabled:
            client_id = self._get_client_id(request)
            endpoint = request.url.path
            _, rate_info = self.rate_limiter.is_allowed(client_id, endpoint)

            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(int(rate_info["reset_time"]))

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct connection
        if request.client:
            return request.client.host

        return "127.0.0.1"

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get from custom header first
        client_id = request.headers.get("X-Client-ID")
        if client_id:
            return client_id

        # Fallback to IP
        return self._get_client_ip(request)


class SecurityConfigBuilder:
    """Builder for security configuration"""

    def __init__(self):
        self.config = SecurityConfig()

    def for_development(self):
        """Configure for development environment"""
        self.config.environment = SecurityLevel.DEVELOPMENT
        self.config.rate_limit_requests = 1000
        self.config.ddos_protection_enabled = False
        self.config.enable_security_headers = False
        self.config.cors_origins = ["*"]
        return self

    def for_staging(self):
        """Configure for staging environment"""
        self.config.environment = SecurityLevel.STAGING
        self.config.rate_limit_requests = 500
        self.config.ddos_protection_enabled = True
        self.config.ddos_threshold = 100
        return self

    def for_production(self):
        """Configure for production environment"""
        self.config.environment = SecurityLevel.PRODUCTION
        self.config.rate_limit_requests = 100
        self.config.ddos_protection_enabled = True
        self.config.ddos_threshold = 50
        self.config.enable_security_headers = True
        self.config.cors_origins = []  # Must be explicitly configured
        return self

    def with_rate_limits(self, requests: int, window: int = 60, burst: int = None):
        """Configure rate limits"""
        self.config.rate_limit_requests = requests
        self.config.rate_limit_window = window
        if burst:
            self.config.burst_limit = burst
        return self

    def with_ddos_protection(
        self, threshold: int, window: int = 10, block_duration: int = 300
    ):
        """Configure DDoS protection"""
        self.config.ddos_protection_enabled = True
        self.config.ddos_threshold = threshold
        self.config.ddos_window = window
        self.config.ddos_block_duration = block_duration
        return self

    def with_ip_whitelist(self, ips: List[str]):
        """Configure IP whitelist"""
        self.config.ip_whitelist = set(ips)
        return self

    def with_ip_blacklist(self, ips: List[str]):
        """Configure IP blacklist"""
        self.config.ip_blacklist = set(ips)
        return self

    def with_cors(
        self, origins: List[str], methods: List[str] = None, headers: List[str] = None
    ):
        """Configure CORS"""
        self.config.enable_cors = True
        self.config.cors_origins = origins
        if methods:
            self.config.cors_methods = methods
        if headers:
            self.config.cors_headers = headers
        return self

    def with_csp(self, policy: str):
        """Configure Content Security Policy"""
        self.config.csp_policy = policy
        return self

    def build(self) -> SecurityConfig:
        """Build the security configuration"""
        return self.config


# Utility functions
def create_security_config(environment: str = "production") -> SecurityConfig:
    """Create security configuration for environment"""
    builder = SecurityConfigBuilder()

    if environment.lower() == "development":
        return builder.for_development().build()
    elif environment.lower() == "staging":
        return builder.for_staging().build()
    else:
        return builder.for_production().build()


def apply_security_middleware(app: FastAPI, config: SecurityConfig):
    """Apply all security middleware to FastAPI app"""

    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware, config=config)

    # Add ingress security middleware
    app.add_middleware(IngressSecurityMiddleware, config=config)

    return app
