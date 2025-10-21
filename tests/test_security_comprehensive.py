"""
Comprehensive test suite for security components
"""

import pytest
import jwt
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from policy_as_code.security.auth import AuthenticationService, JWTAuthProvider
from policy_as_code.security.caller_auth import CallerAuthenticationService
from policy_as_code.security.kms import KMSService, KMSConfig
from policy_as_code.security.replay import ReplayProtector, NonceGenerator


class TestJWTAuthProvider:
    """Test JWT authentication provider"""

    @pytest.fixture
    def jwt_provider(self):
        """Create a test JWT provider"""
        return JWTAuthProvider(secret_key="test_secret")

    def test_generate_token(self, jwt_provider):
        """Test generating a JWT token"""
        user_id = "test_user"
        token = jwt_provider.generate_token(user_id)

        assert token is not None
        assert isinstance(token, str)

        # Verify token can be decoded
        decoded = jwt.decode(token, "test_secret", algorithms=["HS256"])
        assert decoded["user_id"] == user_id

    def test_validate_token(self, jwt_provider):
        """Test validating a JWT token"""
        user_id = "test_user"
        token = jwt_provider.generate_token(user_id)

        # Valid token
        result = jwt_provider.validate_token(token)
        assert result is not None
        assert result["user_id"] == user_id

        # Invalid token
        invalid_token = "invalid_token"
        result = jwt_provider.validate_token(invalid_token)
        assert result is None

    def test_token_expiration(self, jwt_provider):
        """Test token expiration"""
        # Create expired token
        expired_payload = {
            "user_id": "test_user",
            "exp": datetime.utcnow() - timedelta(hours=1),
        }
        expired_token = jwt.encode(expired_payload, "test_secret", algorithm="HS256")

        result = jwt_provider.validate_token(expired_token)
        assert result is None


class TestAuthenticationService:
    """Test authentication service"""

    @pytest.fixture
    def auth_service(self):
        """Create a test authentication service"""
        return AuthenticationService()

    @pytest.mark.asyncio
    async def test_authenticate_user(self, auth_service):
        """Test user authentication"""
        with patch.object(
            auth_service.jwt_provider,
            "validate_token",
            return_value={"user_id": "test_user"},
        ):
            result = await auth_service.authenticate("valid_token")

            assert result is not None
            assert result["user_id"] == "test_user"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_token(self, auth_service):
        """Test authentication with invalid token"""
        with patch.object(
            auth_service.jwt_provider, "validate_token", return_value=None
        ):
            result = await auth_service.authenticate("invalid_token")

            assert result is None

    @pytest.mark.asyncio
    async def test_authorize_user(self, auth_service):
        """Test user authorization"""
        user_context = {"user_id": "test_user", "roles": ["admin"]}

        # Authorized user
        result = await auth_service.authorize(user_context, "admin")
        assert result is True

        # Unauthorized user
        result = await auth_service.authorize(user_context, "super_admin")
        assert result is False


class TestCallerAuthenticationService:
    """Test caller authentication service"""

    @pytest.fixture
    def caller_auth(self):
        """Create a test caller authentication service"""
        return CallerAuthenticationService()

    @pytest.mark.asyncio
    async def test_authenticate_caller(self, caller_auth):
        """Test caller authentication"""
        caller_id = "test_caller"
        api_key = "valid_api_key"

        with patch.object(caller_auth, "_validate_api_key", return_value=True):
            result = await caller_auth.authenticate_caller(caller_id, api_key)

            assert result is not None
            assert result["caller_id"] == caller_id

    @pytest.mark.asyncio
    async def test_authenticate_invalid_caller(self, caller_auth):
        """Test authentication with invalid caller"""
        caller_id = "invalid_caller"
        api_key = "invalid_api_key"

        with patch.object(caller_auth, "_validate_api_key", return_value=False):
            result = await caller_auth.authenticate_caller(caller_id, api_key)

            assert result is None


class TestKMSService:
    """Test KMS service"""

    @pytest.fixture
    def kms_service(self):
        """Create a test KMS service"""
        config = KMSConfig(
            provider="mock", endpoint="http://localhost:8080", key_id="test_key"
        )
        return KMSService(config)

    @pytest.mark.asyncio
    async def test_encrypt_data(self, kms_service):
        """Test data encryption"""
        plaintext = "sensitive_data"

        with patch.object(kms_service, "_encrypt", return_value="encrypted_data"):
            result = await kms_service.encrypt(plaintext)

            assert result == "encrypted_data"

    @pytest.mark.asyncio
    async def test_decrypt_data(self, kms_service):
        """Test data decryption"""
        ciphertext = "encrypted_data"

        with patch.object(kms_service, "_decrypt", return_value="sensitive_data"):
            result = await kms_service.decrypt(ciphertext)

            assert result == "sensitive_data"

    @pytest.mark.asyncio
    async def test_generate_key(self, kms_service):
        """Test key generation"""
        with patch.object(kms_service, "_generate_key", return_value="new_key_id"):
            result = await kms_service.generate_key()

            assert result == "new_key_id"


class TestReplayProtector:
    """Test replay protection"""

    @pytest.fixture
    def replay_protector(self):
        """Create a test replay protector"""
        return ReplayProtector()

    @pytest.fixture
    def nonce_generator(self):
        """Create a test nonce generator"""
        return NonceGenerator()

    def test_generate_nonce(self, nonce_generator):
        """Test nonce generation"""
        nonce = nonce_generator.generate_nonce()

        assert nonce is not None
        assert isinstance(nonce, str)
        assert len(nonce) > 0

    def test_nonce_uniqueness(self, nonce_generator):
        """Test nonce uniqueness"""
        nonces = set()
        for _ in range(100):
            nonce = nonce_generator.generate_nonce()
            nonces.add(nonce)

        # All nonces should be unique
        assert len(nonces) == 100

    @pytest.mark.asyncio
    async def test_validate_request(self, replay_protector):
        """Test request validation"""
        request_id = "test_request"
        nonce = "test_nonce"
        timestamp = datetime.utcnow()

        # Valid request
        result = await replay_protector.validate_request(request_id, nonce, timestamp)
        assert result is True

        # Replay attack (same request_id and nonce)
        result = await replay_protector.validate_request(request_id, nonce, timestamp)
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_expired_nonces(self, replay_protector):
        """Test cleanup of expired nonces"""
        # Add some expired nonces
        old_timestamp = datetime.utcnow() - timedelta(hours=2)
        await replay_protector.validate_request(
            "old_request", "old_nonce", old_timestamp
        )

        # Cleanup expired nonces
        await replay_protector.cleanup_expired_nonces()

        # Should be able to reuse the old nonce
        result = await replay_protector.validate_request(
            "new_request", "old_nonce", datetime.utcnow()
        )
        assert result is True


class TestSecurityIntegration:
    """Test security integration scenarios"""

    @pytest.fixture
    def auth_service(self):
        """Create authentication service for integration tests"""
        return AuthenticationService()

    @pytest.fixture
    def kms_service(self):
        """Create KMS service for integration tests"""
        config = KMSConfig(
            provider="mock", endpoint="http://localhost:8080", key_id="test_key"
        )
        return KMSService(config)

    @pytest.mark.asyncio
    async def test_secure_decision_execution(self, auth_service, kms_service):
        """Test secure decision execution workflow"""
        # Authenticate user
        token = "valid_token"
        with patch.object(
            auth_service.jwt_provider,
            "validate_token",
            return_value={"user_id": "test_user"},
        ):
            user_context = await auth_service.authenticate(token)
            assert user_context is not None

        # Encrypt sensitive data
        sensitive_data = "credit_score:750"
        with patch.object(
            kms_service, "_encrypt", return_value="encrypted_credit_score"
        ):
            encrypted_data = await kms_service.encrypt(sensitive_data)
            assert encrypted_data == "encrypted_credit_score"

        # Decrypt data for processing
        with patch.object(kms_service, "_decrypt", return_value="credit_score:750"):
            decrypted_data = await kms_service.decrypt(encrypted_data)
            assert decrypted_data == sensitive_data

    @pytest.mark.asyncio
    async def test_replay_attack_prevention(self):
        """Test replay attack prevention"""
        replay_protector = ReplayProtector()

        # First request
        request_id = "loan_request_123"
        nonce = "unique_nonce_456"
        timestamp = datetime.utcnow()

        result1 = await replay_protector.validate_request(request_id, nonce, timestamp)
        assert result1 is True

        # Replay attack attempt
        result2 = await replay_protector.validate_request(request_id, nonce, timestamp)
        assert result2 is False

        # Different request with same nonce should be allowed
        result3 = await replay_protector.validate_request(
            "different_request", nonce, timestamp
        )
        assert result3 is True


class TestSecurityPerformance:
    """Test security performance"""

    @pytest.fixture
    def auth_service(self):
        """Create authentication service for performance tests"""
        return AuthenticationService()

    def test_jwt_performance(self, auth_service):
        """Test JWT token generation and validation performance"""
        import time

        # Test token generation performance
        start_time = time.time()
        for _ in range(1000):
            auth_service.jwt_provider.generate_token("test_user")
        generation_time = time.time() - start_time

        # Should be fast (less than 1 second for 1000 tokens)
        assert generation_time < 1.0

        # Test token validation performance
        token = auth_service.jwt_provider.generate_token("test_user")
        start_time = time.time()
        for _ in range(1000):
            auth_service.jwt_provider.validate_token(token)
        validation_time = time.time() - start_time

        # Should be fast (less than 1 second for 1000 validations)
        assert validation_time < 1.0
