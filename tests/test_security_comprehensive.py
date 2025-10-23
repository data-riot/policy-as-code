"""
Comprehensive Security Test Suite
Tests authentication, authorization, rate limiting, DDoS protection, and monitoring
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi.testclient import TestClient
from fastapi import FastAPI

from policy_as_code.api.secure_api import create_secure_api
from policy_as_code.security.nonce_auth import (
    NonceManager,
    JWTManager,
    AuthConfig,
    generate_client_credentials,
)
from policy_as_code.security.ingress_security import (
    RateLimiter,
    DDoSProtection,
    SecurityConfig,
    SecurityConfigBuilder,
)
from policy_as_code.monitoring.metrics_logs_health import (
    MetricsCollector,
    StructuredLogger,
    HealthChecker,
)


class TestNonceAuthentication:
    """Test nonce-based authentication"""

    def setup_method(self):
        """Setup test environment"""
        self.auth_config = AuthConfig(
            nonce_ttl_seconds=60,
            jwt_expiry_minutes=5,
            redis_url="redis://localhost:6379",
        )
        self.nonce_manager = NonceManager(self.auth_config)
        self.jwt_manager = JWTManager(self.auth_config)

    def test_nonce_generation(self):
        """Test nonce generation"""
        client_id = "test_client"
        request_data = {"test": "data"}

        nonce = self.nonce_manager.generate_nonce(client_id, request_data)

        assert nonce is not None
        assert len(nonce) == self.auth_config.nonce_length

    def test_nonce_validation(self):
        """Test nonce validation"""
        client_id = "test_client"
        request_data = {"test": "data"}

        # Generate nonce
        nonce = self.nonce_manager.generate_nonce(client_id, request_data)

        # Validate nonce
        is_valid = self.nonce_manager.validate_nonce(nonce, client_id, request_data)
        assert is_valid is True

        # Try to reuse nonce (should fail)
        is_valid = self.nonce_manager.validate_nonce(nonce, client_id, request_data)
        assert is_valid is False

    def test_nonce_expiration(self):
        """Test nonce expiration"""
        client_id = "test_client"
        request_data = {"test": "data"}

        # Generate nonce with short TTL
        self.auth_config.nonce_ttl_seconds = 1
        nonce = self.nonce_manager.generate_nonce(client_id, request_data)

        # Wait for expiration
        time.sleep(2)

        # Try to validate expired nonce
        is_valid = self.nonce_manager.validate_nonce(nonce, client_id, request_data)
        assert is_valid is False

    def test_jwt_generation_and_validation(self):
        """Test JWT token generation and validation"""
        user_id = "test_user"
        roles = ["user", "admin"]
        client_id = "test_client"

        # Generate token
        token = self.jwt_manager.generate_token(user_id, roles, client_id)
        assert token is not None

        # Validate token
        payload = self.jwt_manager.validate_token(token)
        assert payload is not None
        assert payload["user_id"] == user_id
        assert payload["roles"] == roles
        assert payload["client_id"] == client_id

    def test_jwt_expiration(self):
        """Test JWT token expiration"""
        user_id = "test_user"
        roles = ["user"]
        client_id = "test_client"

        # Generate token with short expiry
        self.auth_config.jwt_expiry_minutes = 1
        token = self.jwt_manager.generate_token(user_id, roles, client_id)

        # Wait for expiration
        time.sleep(70)

        # Try to validate expired token
        payload = self.jwt_manager.validate_token(token)
        assert payload is None


class TestRateLimiting:
    """Test rate limiting functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.security_config = SecurityConfig(
            rate_limit_requests=5,
            rate_limit_window=60,
            burst_limit=10,
            redis_url="redis://localhost:6379",
        )
        self.rate_limiter = RateLimiter(self.security_config)

    def test_rate_limiting_allows_requests(self):
        """Test that rate limiter allows requests within limits"""
        client_id = "test_client"

        # Make requests within limit
        for i in range(5):
            is_allowed, info = self.rate_limiter.is_allowed(client_id)
            assert is_allowed is True
            assert info["remaining"] >= 0

    def test_rate_limiting_blocks_excess_requests(self):
        """Test that rate limiter blocks excess requests"""
        client_id = "test_client"

        # Make requests up to limit
        for i in range(5):
            is_allowed, info = self.rate_limiter.is_allowed(client_id)
            assert is_allowed is True

        # Next request should be blocked
        is_allowed, info = self.rate_limiter.is_allowed(client_id)
        assert is_allowed is False
        assert info["remaining"] == 0

    def test_burst_protection(self):
        """Test burst protection"""
        client_id = "test_client"

        # Make burst requests
        for i in range(10):
            is_allowed, info = self.rate_limiter.is_allowed(client_id)
            assert is_allowed is True

        # Next request should be blocked by burst limit
        is_allowed, info = self.rate_limiter.is_allowed(client_id)
        assert is_allowed is False


class TestDDoSProtection:
    """Test DDoS protection functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.security_config = SecurityConfig(
            ddos_protection_enabled=True,
            ddos_threshold=5,
            ddos_window=10,
            ddos_block_duration=60,
            redis_url="redis://localhost:6379",
        )
        self.ddos_protection = DDoSProtection(self.security_config)

    def test_ddos_protection_allows_normal_traffic(self):
        """Test that DDoS protection allows normal traffic"""
        client_ip = "192.168.1.1"

        # Make normal requests
        for i in range(3):
            is_allowed, message = self.ddos_protection.check_ddos(client_ip)
            assert is_allowed is True
            assert message is None

    def test_ddos_protection_blocks_attack(self):
        """Test that DDoS protection blocks attack traffic"""
        client_ip = "192.168.1.2"

        # Make requests exceeding threshold
        for i in range(6):
            is_allowed, message = self.ddos_protection.check_ddos(client_ip)
            if i < 5:
                assert is_allowed is True
            else:
                assert is_allowed is False
                assert "DDoS detected" in message


class TestMonitoring:
    """Test monitoring and metrics functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.metrics_collector = MetricsCollector()
        self.logger = StructuredLogger("test")
        self.health_checker = HealthChecker()

    def test_metrics_collection(self):
        """Test metrics collection"""
        # Record some metrics
        self.metrics_collector.record_request("GET", "/test", 200, 0.1)
        self.metrics_collector.record_decision("test_func", "1.0.0", "success", 0.05)
        self.metrics_collector.record_error("test_error", "test_component")

        # Verify metrics were recorded
        assert self.metrics_collector.request_count._value.sum() > 0
        assert self.metrics_collector.decision_count._value.sum() > 0
        assert self.metrics_collector.error_count._value.sum() > 0

    def test_health_checks(self):
        """Test health check functionality"""

        async def run_health_checks():
            checks = await self.health_checker.run_checks()
            assert len(checks) > 0

            for check in checks:
                assert check.name is not None
                assert check.status is not None
                assert check.message is not None
                assert check.response_time_ms >= 0

        asyncio.run(run_health_checks())


class TestSecureAPI:
    """Test the complete secure API"""

    def setup_method(self):
        """Setup test environment"""
        self.app = create_secure_api("development")
        self.client = TestClient(self.app)

    def test_health_endpoints(self):
        """Test health check endpoints"""
        # Test /health endpoint
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

        # Test /healthz endpoint
        response = self.client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = self.client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Policy as Code API"
        assert data["security"] == "enabled"

    def test_authentication_required(self):
        """Test that authentication is required for protected endpoints"""
        # Try to access protected endpoint without auth
        response = self.client.post(
            "/api/v1/decisions", json={"function_id": "test", "input_data": {}}
        )
        assert response.status_code == 401

    def test_rate_limiting_headers(self):
        """Test that rate limiting headers are present"""
        response = self.client.get("/")
        assert response.status_code == 200

        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_security_headers(self):
        """Test that security headers are present"""
        response = self.client.get("/")
        assert response.status_code == 200

        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers


class TestClientCredentials:
    """Test client credential generation"""

    def test_generate_credentials(self):
        """Test client credential generation"""
        client_id = "test_client"
        roles = ["user", "admin"]

        credentials = generate_client_credentials(client_id, roles)

        assert "client_id" in credentials
        assert "token" in credentials
        assert "roles" in credentials
        assert credentials["client_id"] == client_id
        assert credentials["roles"] == roles
        assert credentials["token"] is not None


class TestSecurityConfig:
    """Test security configuration"""

    def test_development_config(self):
        """Test development security configuration"""
        config = SecurityConfigBuilder().for_development().build()

        assert config.environment.value == "development"
        assert config.rate_limit_requests == 1000
        assert config.ddos_protection_enabled is False
        assert config.enable_security_headers is False

    def test_production_config(self):
        """Test production security configuration"""
        config = SecurityConfigBuilder().for_production().build()

        assert config.environment.value == "production"
        assert config.rate_limit_requests == 100
        assert config.ddos_protection_enabled is True
        assert config.enable_security_headers is True

    def test_custom_config(self):
        """Test custom security configuration"""
        config = (
            SecurityConfigBuilder()
            .for_production()
            .with_rate_limits(200, 120, 300)
            .with_ddos_protection(100, 20, 600)
            .with_ip_whitelist(["192.168.1.0/24"])
            .build()
        )

        assert config.rate_limit_requests == 200
        assert config.rate_limit_window == 120
        assert config.burst_limit == 300
        assert config.ddos_threshold == 100
        assert config.ddos_window == 20
        assert config.ddos_block_duration == 600
        assert "192.168.1.0/24" in config.ip_whitelist


# Integration tests
class TestIntegration:
    """Integration tests for the complete system"""

    def setup_method(self):
        """Setup test environment"""
        self.app = create_secure_api("development")
        self.client = TestClient(self.app)

    def test_complete_workflow(self):
        """Test complete workflow with authentication"""
        # Generate credentials
        credentials = generate_client_credentials("test_client", ["user"])

        # Create request data
        request_data = {"test": "data"}

        # Generate nonce (this would normally be done by the client)
        from policy_as_code.security.nonce_auth import NonceManager, AuthConfig

        auth_config = AuthConfig()
        nonce_manager = NonceManager(auth_config)
        nonce = nonce_manager.generate_nonce("test_client", request_data)

        # Make authenticated request
        headers = {
            "Authorization": f"Bearer {credentials['token']}",
            "X-Request-Nonce": nonce,
            "X-Client-ID": "test_client",
        }

        response = self.client.get("/", headers=headers)
        assert response.status_code == 200

        # Verify rate limiting headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_error_handling(self):
        """Test error handling and logging"""
        # Test 404
        response = self.client.get("/nonexistent")
        assert response.status_code == 404

        # Test 401
        response = self.client.post("/api/v1/decisions", json={})
        assert response.status_code == 401

        # Test 403 (would need proper setup)
        # This would require setting up proper authorization


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
