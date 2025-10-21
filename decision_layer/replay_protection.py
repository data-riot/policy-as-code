"""
Replay Protection with Nonce + TTL
Prevents replay attacks using cryptographic nonces and time-based validation

PRODUCTION STATUS: ⚠️ PARTIAL IMPLEMENTATION
- Nonce generation and validation implemented
- TTL validation implemented
- Request signing framework implemented

MISSING PRODUCTION FEATURES:
- Distributed nonce storage (currently in-memory)
- Nonce persistence across restarts
- Performance optimization and caching
- Nonce cleanup automation
- Clock skew handling
- Request signing implementation
- Integration with existing API endpoints
- Audit logging for replay attempts
- Rate limiting integration
- Multi-region nonce synchronization
- Nonce collision detection
- Performance monitoring and metrics
"""

import hashlib
import hmac
import json
import time
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum

from .errors import DecisionLayerError


class NonceType(str, Enum):
    """Types of nonces"""

    CRYPTOGRAPHIC = "cryptographic"  # Random bytes
    TIMESTAMP = "timestamp"  # Timestamp-based
    COUNTER = "counter"  # Sequential counter
    HYBRID = "hybrid"  # Combination of above


@dataclass
class NonceConfig:
    """Nonce configuration"""

    nonce_type: NonceType = NonceType.HYBRID
    ttl_seconds: int = 300  # 5 minutes
    max_clock_skew_seconds: int = 30
    nonce_length_bytes: int = 16
    max_nonce_age_seconds: int = 3600  # 1 hour
    cleanup_interval_seconds: int = 60


@dataclass
class NonceRecord:
    """Nonce record for tracking"""

    nonce: str
    caller_id: str
    request_id: Optional[str]
    created_at: datetime
    expires_at: datetime
    used_at: Optional[datetime] = None
    request_hash: Optional[str] = None


class NonceGenerator:
    """Cryptographic nonce generator"""

    def __init__(self, config: NonceConfig):
        self.config = config
        self._counter = 0
        self._last_timestamp = 0

    def generate_nonce(self, caller_id: str, request_id: Optional[str] = None) -> str:
        """Generate nonce based on configured type"""

        if self.config.nonce_type == NonceType.CRYPTOGRAPHIC:
            return self._generate_cryptographic_nonce()
        elif self.config.nonce_type == NonceType.TIMESTAMP:
            return self._generate_timestamp_nonce()
        elif self.config.nonce_type == NonceType.COUNTER:
            return self._generate_counter_nonce()
        elif self.config.nonce_type == NonceType.HYBRID:
            return self._generate_hybrid_nonce(caller_id, request_id)
        else:
            raise DecisionLayerError(
                "unsupported_nonce_type",
                f"Unsupported nonce type: {self.config.nonce_type}",
            )

    def _generate_cryptographic_nonce(self) -> str:
        """Generate random cryptographic nonce"""
        import secrets

        nonce_bytes = secrets.token_bytes(self.config.nonce_length_bytes)
        return nonce_bytes.hex()

    def _generate_timestamp_nonce(self) -> str:
        """Generate timestamp-based nonce"""
        timestamp = int(time.time() * 1000)  # milliseconds
        nonce_bytes = timestamp.to_bytes(8, "big")
        return nonce_bytes.hex()

    def _generate_counter_nonce(self) -> str:
        """Generate counter-based nonce"""
        self._counter += 1
        counter_bytes = self._counter.to_bytes(8, "big")
        return counter_bytes.hex()

    def _generate_hybrid_nonce(
        self, caller_id: str, request_id: Optional[str] = None
    ) -> str:
        """Generate hybrid nonce combining multiple sources"""
        timestamp = int(time.time() * 1000)
        self._counter += 1

        # Combine timestamp, counter, caller_id, and random bytes
        timestamp_bytes = timestamp.to_bytes(8, "big")
        counter_bytes = self._counter.to_bytes(4, "big")
        caller_bytes = caller_id.encode("utf-8")[:8].ljust(8, b"\x00")

        import secrets

        random_bytes = secrets.token_bytes(4)

        # Combine all components
        combined = timestamp_bytes + counter_bytes + caller_bytes + random_bytes

        # Hash to get fixed-length nonce
        nonce_hash = hashlib.sha256(combined).digest()[: self.config.nonce_length_bytes]
        return nonce_hash.hex()


class ReplayProtector:
    """Replay attack protection using nonces and TTL

    PRODUCTION STATUS: ⚠️ PARTIAL IMPLEMENTATION
    - Basic nonce validation implemented
    - In-memory storage only (not production-ready)

    MISSING PRODUCTION FEATURES:
    - Distributed storage (Redis/Database)
    - Nonce persistence across restarts
    - Performance optimization
    - Cleanup automation
    - Clock skew handling
    - Request signing
    - Integration with API endpoints
    """

    def __init__(self, config: NonceConfig):
        self.config = config
        self.nonce_generator = NonceGenerator(config)
        # PSEUDOCODE: In-memory storage - NOT production ready
        self._nonce_cache: Dict[str, NonceRecord] = {}
        self._last_cleanup = datetime.now(timezone.utc)

        # MISSING PRODUCTION LOGIC:
        # 1. Redis/Database connection for distributed storage
        # 2. Nonce cleanup background task
        # 3. Performance monitoring and metrics
        # 4. Clock skew detection and handling
        # 5. Request signing implementation
        # 6. Integration with API middleware

    def generate_nonce(self, caller_id: str, request_id: Optional[str] = None) -> str:
        """Generate nonce for request"""
        nonce = self.nonce_generator.generate_nonce(caller_id, request_id)

        # Store nonce record
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.config.ttl_seconds)

        self._nonce_cache[nonce] = NonceRecord(
            nonce=nonce,
            caller_id=caller_id,
            request_id=request_id,
            created_at=now,
            expires_at=expires_at,
        )

        return nonce

    def validate_nonce(
        self, nonce: str, caller_id: str, request_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Validate nonce and prevent replay attacks"""

        # Cleanup expired nonces
        self._cleanup_expired_nonces()

        # Check if nonce exists
        if nonce not in self._nonce_cache:
            raise DecisionLayerError(
                "invalid_nonce", f"Nonce {nonce} not found or expired"
            )

        nonce_record = self._nonce_cache[nonce]

        # Check if nonce has already been used
        if nonce_record.used_at is not None:
            raise DecisionLayerError(
                "nonce_replay", f"Nonce {nonce} has already been used"
            )

        # Check caller ID match
        if nonce_record.caller_id != caller_id:
            raise DecisionLayerError(
                "nonce_caller_mismatch",
                f"Nonce {nonce} caller mismatch: expected {nonce_record.caller_id}, got {caller_id}",
            )

        # Check expiration
        now = datetime.now(timezone.utc)
        if now > nonce_record.expires_at:
            raise DecisionLayerError("nonce_expired", f"Nonce {nonce} has expired")

        # Check clock skew
        age_seconds = (now - nonce_record.created_at).total_seconds()
        if age_seconds > self.config.max_nonce_age_seconds:
            raise DecisionLayerError(
                "nonce_too_old", f"Nonce {nonce} is too old: {age_seconds} seconds"
            )

        # Validate request data if provided
        if request_data:
            request_hash = self._calculate_request_hash(request_data)
            if nonce_record.request_hash and nonce_record.request_hash != request_hash:
                raise DecisionLayerError(
                    "request_data_mismatch",
                    f"Request data does not match nonce {nonce}",
                )
            nonce_record.request_hash = request_hash

        # Mark nonce as used
        nonce_record.used_at = now

        return True

    def _calculate_request_hash(self, request_data: Dict[str, Any]) -> str:
        """Calculate hash of request data"""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(request_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(sorted_data.encode("utf-8")).hexdigest()

    def _cleanup_expired_nonces(self) -> None:
        """Clean up expired nonces"""
        now = datetime.now(timezone.utc)

        # Only cleanup if enough time has passed
        if (
            now - self._last_cleanup
        ).total_seconds() < self.config.cleanup_interval_seconds:
            return

        expired_nonces = []
        for nonce, record in self._nonce_cache.items():
            if now > record.expires_at + timedelta(
                seconds=self.config.max_nonce_age_seconds
            ):
                expired_nonces.append(nonce)

        for nonce in expired_nonces:
            del self._nonce_cache[nonce]

        self._last_cleanup = now

    def get_nonce_stats(self) -> Dict[str, Any]:
        """Get nonce statistics"""
        now = datetime.now(timezone.utc)

        total_nonces = len(self._nonce_cache)
        used_nonces = sum(
            1 for record in self._nonce_cache.values() if record.used_at is not None
        )
        expired_nonces = sum(
            1 for record in self._nonce_cache.values() if now > record.expires_at
        )

        return {
            "total_nonces": total_nonces,
            "used_nonces": used_nonces,
            "expired_nonces": expired_nonces,
            "active_nonces": total_nonces - used_nonces - expired_nonces,
            "last_cleanup": self._last_cleanup.isoformat(),
        }


class RequestSigner:
    """Request signing for additional replay protection"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode("utf-8")

    def sign_request(
        self,
        nonce: str,
        caller_id: str,
        request_data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> str:
        """Sign request with HMAC"""

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Create message to sign
        message_parts = [
            nonce,
            caller_id,
            timestamp.isoformat(),
            json.dumps(request_data, sort_keys=True, separators=(",", ":")),
        ]

        message = "|".join(message_parts)

        # Create HMAC signature
        signature = hmac.new(
            self.secret_key, message.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return signature

    def verify_request_signature(
        self,
        nonce: str,
        caller_id: str,
        request_data: Dict[str, Any],
        timestamp: datetime,
        signature: str,
    ) -> bool:
        """Verify request signature"""

        expected_signature = self.sign_request(
            nonce, caller_id, request_data, timestamp
        )

        # Use constant-time comparison
        return hmac.compare_digest(expected_signature, signature)


class ReplayProtectionManager:
    """Centralized replay protection manager"""

    def __init__(self, nonce_config: NonceConfig, secret_key: Optional[str] = None):
        self.nonce_config = nonce_config
        self.replay_protector = ReplayProtector(nonce_config)
        self.request_signer = RequestSigner(secret_key) if secret_key else None

    def create_protected_request(
        self,
        caller_id: str,
        request_data: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create request with replay protection"""

        # Generate nonce
        nonce = self.replay_protector.generate_nonce(caller_id, request_id)

        # Create timestamp
        timestamp = datetime.now(timezone.utc)

        # Sign request if signer is available
        signature = None
        if self.request_signer:
            signature = self.request_signer.sign_request(
                nonce, caller_id, request_data, timestamp
            )

        return {
            "nonce": nonce,
            "timestamp": timestamp.isoformat(),
            "signature": signature,
            "request_data": request_data,
        }

    def validate_protected_request(
        self,
        caller_id: str,
        nonce: str,
        request_data: Dict[str, Any],
        timestamp_str: str,
        signature: Optional[str] = None,
    ) -> bool:
        """Validate protected request"""

        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            raise DecisionLayerError(
                "invalid_timestamp", f"Invalid timestamp format: {timestamp_str}"
            )

        # Check timestamp freshness
        now = datetime.now(timezone.utc)
        age_seconds = (now - timestamp).total_seconds()

        if age_seconds > self.nonce_config.ttl_seconds:
            raise DecisionLayerError(
                "request_too_old", f"Request timestamp too old: {age_seconds} seconds"
            )

        # Check clock skew
        if abs(age_seconds) > self.nonce_config.max_clock_skew_seconds:
            raise DecisionLayerError(
                "clock_skew_too_large",
                f"Clock skew too large: {abs(age_seconds)} seconds",
            )

        # Validate nonce
        self.replay_protector.validate_nonce(nonce, caller_id, request_data)

        # Verify signature if provided
        if signature and self.request_signer:
            if not self.request_signer.verify_request_signature(
                nonce, caller_id, request_data, timestamp, signature
            ):
                raise DecisionLayerError(
                    "invalid_signature", "Request signature verification failed"
                )

        return True

    def get_protection_stats(self) -> Dict[str, Any]:
        """Get replay protection statistics"""
        nonce_stats = self.replay_protector.get_nonce_stats()

        return {
            "nonce_stats": nonce_stats,
            "config": {
                "nonce_type": self.nonce_config.nonce_type.value,
                "ttl_seconds": self.nonce_config.ttl_seconds,
                "max_clock_skew_seconds": self.nonce_config.max_clock_skew_seconds,
                "signing_enabled": self.request_signer is not None,
            },
        }


# Global replay protection manager
_replay_protection_manager: Optional[ReplayProtectionManager] = None


def configure_replay_protection(
    nonce_config: NonceConfig, secret_key: Optional[str] = None
) -> None:
    """Configure replay protection"""
    global _replay_protection_manager
    _replay_protection_manager = ReplayProtectionManager(nonce_config, secret_key)


def get_replay_protection_manager() -> ReplayProtectionManager:
    """Get replay protection manager instance"""
    global _replay_protection_manager
    if _replay_protection_manager is None:
        raise DecisionLayerError(
            "replay_protection_not_configured",
            "Replay protection not configured. Call configure_replay_protection() first.",
        )
    return _replay_protection_manager


def create_protected_request(
    caller_id: str, request_data: Dict[str, Any], request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create request with replay protection"""
    manager = get_replay_protection_manager()
    return manager.create_protected_request(caller_id, request_data, request_id)


def validate_protected_request(
    caller_id: str,
    nonce: str,
    request_data: Dict[str, Any],
    timestamp_str: str,
    signature: Optional[str] = None,
) -> bool:
    """Validate protected request"""
    manager = get_replay_protection_manager()
    return manager.validate_protected_request(
        caller_id, nonce, request_data, timestamp_str, signature
    )


def get_replay_protection_stats() -> Dict[str, Any]:
    """Get replay protection statistics"""
    manager = get_replay_protection_manager()
    return manager.get_protection_stats()
