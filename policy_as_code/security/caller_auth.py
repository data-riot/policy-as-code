"""
JWT + mTLS Authentication for Callers
Enhanced authentication with JWT tokens and mutual TLS for government-grade security

PRODUCTION STATUS: ⚠️ PARTIAL IMPLEMENTATION
- JWT verification framework implemented
- mTLS certificate validation framework implemented
- Hybrid authentication logic implemented

MISSING PRODUCTION FEATURES:
- Actual JWT token validation (currently mock)
- Real mTLS certificate validation
- Certificate transparency monitoring
- JWT token blacklisting and revocation
- Certificate revocation list (CRL) checking
- Online Certificate Status Protocol (OCSP)
- Performance optimization and caching
- Multi-tenant authentication
- Audit logging for all auth operations
- Integration with existing auth systems
- Certificate lifecycle management
- Identity federation support
- Rate limiting and brute force protection
"""

import jwt
import hashlib
import ssl
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum

from .errors import DecisionLayerError


class AuthMethod(str, Enum):
    """Authentication methods"""

    JWT = "jwt"
    MTLS = "mtls"
    HYBRID = "hybrid"  # Both JWT and mTLS required


@dataclass
class JWTAuthConfig:
    """JWT authentication configuration"""

    issuer: str
    audience: str
    public_key_url: str
    algorithm: str = "RS256"
    leeway_seconds: int = 30
    cache_ttl_seconds: int = 300


@dataclass
class MTLSConfig:
    """mTLS configuration"""

    ca_cert_path: str
    client_cert_required: bool = True
    verify_hostname: bool = True
    min_tls_version: str = "TLSv1.2"
    cipher_suites: List[str] = field(
        default_factory=lambda: [
            "ECDHE-RSA-AES256-GCM-SHA384",
            "ECDHE-RSA-AES128-GCM-SHA256",
        ]
    )


@dataclass
class CallerIdentity:
    """Caller identity information"""

    caller_id: str
    subject: str
    issuer: str
    certificate_hash: Optional[str] = None
    certificate_cn: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    authenticated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    expires_at: Optional[datetime] = None


class JWTAuthenticator:
    """JWT token authenticator"""

    def __init__(self, config: JWTAuthConfig):
        self.config = config
        self._public_keys_cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, datetime] = {}

    def _get_public_key(self, key_id: str) -> str:
        """Get public key for JWT verification

        PRODUCTION NOTES:
        - Currently uses mock JWKS endpoint
        - MISSING: Actual JWKS endpoint implementation
        - MISSING: Certificate pinning and validation
        - MISSING: Key rotation handling
        - MISSING: Performance optimization
        """
        cache_key = f"{self.config.public_key_url}:{key_id}"

        # Check cache
        if cache_key in self._public_keys_cache:
            if datetime.now(timezone.utc) < self._cache_expiry[cache_key]:
                return self._public_keys_cache[cache_key]

        # PSEUDOCODE: Mock JWKS endpoint - NOT production ready
        try:
            # MISSING PRODUCTION LOGIC:
            # 1. Actual JWKS endpoint with proper SSL/TLS
            # 2. Certificate pinning for security
            # 3. Key rotation and versioning
            # 4. Performance optimization and caching
            # 5. Error handling and retry logic
            # 6. Audit logging for key requests
            # 7. Rate limiting and DDoS protection
            import requests

            response = requests.get(self.config.public_key_url)
            jwks = response.json()

            # Find the key
            for key in jwks.get("keys", []):
                if key.get("kid") == key_id:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                    self._public_keys_cache[cache_key] = public_key
                    self._cache_expiry[cache_key] = datetime.now(
                        timezone.utc
                    ) + timedelta(seconds=self.config.cache_ttl_seconds)
                    return public_key

            raise DecisionLayerError(
                "jwt_key_not_found", f"Public key {key_id} not found in JWKS"
            )

        except Exception as e:
            raise DecisionLayerError(
                "jwt_key_fetch_failed", f"Failed to fetch public key: {str(e)}"
            )

    def verify_token(self, token: str) -> CallerIdentity:
        """Verify JWT token and extract caller identity"""
        try:
            # Decode header to get key ID
            header = jwt.get_unverified_header(token)
            key_id = header.get("kid")

            if not key_id:
                raise DecisionLayerError(
                    "jwt_no_key_id", "JWT token missing key ID in header"
                )

            # Get public key
            public_key = self._get_public_key(key_id)

            # Verify and decode token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[self.config.algorithm],
                audience=self.config.audience,
                issuer=self.config.issuer,
                leeway=self.config.leeway_seconds,
            )

            # Extract caller identity
            caller_id = payload.get("sub")
            if not caller_id:
                raise DecisionLayerError("jwt_no_subject", "JWT token missing subject")

            # Check expiration
            exp = payload.get("exp")
            if exp:
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                if datetime.now(timezone.utc) > expires_at:
                    raise DecisionLayerError("jwt_expired", "JWT token has expired")
            else:
                expires_at = None

            return CallerIdentity(
                caller_id=caller_id,
                subject=payload.get("sub", ""),
                issuer=payload.get("iss", ""),
                roles=payload.get("roles", []),
                capabilities=payload.get("capabilities", []),
                expires_at=expires_at,
            )

        except jwt.ExpiredSignatureError:
            raise DecisionLayerError("jwt_expired", "JWT token has expired")
        except jwt.InvalidTokenError as e:
            raise DecisionLayerError("jwt_invalid", f"Invalid JWT token: {str(e)}")
        except Exception as e:
            raise DecisionLayerError(
                "jwt_verification_failed", f"JWT verification failed: {str(e)}"
            )


class MTLSVerifier:
    """mTLS certificate verifier"""

    def __init__(self, config: MTLSConfig):
        self.config = config
        self._certificate_cache: Dict[str, CallerIdentity] = {}

    def verify_certificate(
        self, cert_der: bytes, cert_chain: List[bytes]
    ) -> CallerIdentity:
        """Verify client certificate and extract identity

        PRODUCTION NOTES:
        - Currently performs basic certificate parsing
        - MISSING: Actual certificate chain validation
        - MISSING: CRL and OCSP checking
        - MISSING: Certificate transparency monitoring
        - MISSING: Certificate pinning validation
        """
        try:
            import cryptography.x509
            from cryptography.hazmat.primitives import hashes, serialization

            # Parse certificate
            cert = cryptography.x509.load_der_x509_certificate(cert_der)

            # PSEUDOCODE: Basic certificate chain verification - NOT production ready
            self._verify_certificate_chain(cert, cert_chain)

            # Extract identity information
            subject = cert.subject
            cn = None
            for name in subject:
                if name.oid == cryptography.x509.NameOID.COMMON_NAME:
                    cn_value = name.value
                    # Ensure cn is a string
                    cn = (
                        cn_value.decode()
                        if isinstance(cn_value, bytes)
                        else str(cn_value)
                    )
                    break

            if not cn:
                raise DecisionLayerError(
                    "mtls_no_cn", "Client certificate missing Common Name"
                )

            # Calculate certificate hash
            cert_hash = hashlib.sha256(cert_der).hexdigest()

            # Check certificate validity
            now = datetime.now(timezone.utc)
            if cert.not_valid_before.replace(tzinfo=timezone.utc) > now:
                raise DecisionLayerError(
                    "mtls_cert_not_yet_valid", "Client certificate not yet valid"
                )

            if cert.not_valid_after.replace(tzinfo=timezone.utc) < now:
                raise DecisionLayerError(
                    "mtls_cert_expired", "Client certificate has expired"
                )

            # MISSING PRODUCTION LOGIC:
            # 1. Certificate Revocation List (CRL) checking
            # 2. Online Certificate Status Protocol (OCSP) validation
            # 3. Certificate Transparency log verification
            # 4. Certificate pinning validation
            # 5. Intermediate certificate validation
            # 6. Root CA trust validation
            # 7. Certificate policy validation
            # 8. Key usage and extended key usage validation

            # Extract roles and capabilities from certificate extensions
            roles = []
            capabilities = []

            try:
                # PSEUDOCODE: Custom extensions parsing - NOT production ready
                # Look for custom extensions (would be defined in certificate)
                for ext in cert.extensions:
                    if (
                        ext.oid.dotted_string == "1.3.6.1.4.1.12345.1.1"
                    ):  # Custom roles extension
                        roles = ext.value.value.decode().split(",")
                    elif (
                        ext.oid.dotted_string == "1.3.6.1.4.1.12345.1.2"
                    ):  # Custom capabilities extension
                        capabilities = ext.value.value.decode().split(",")
            except:
                pass  # Extensions are optional

            return CallerIdentity(
                caller_id=cn,
                subject=cn,
                issuer=cert.issuer.rfc4514_string(),
                certificate_hash=cert_hash,
                certificate_cn=cn,
                roles=roles,
                capabilities=capabilities,
            )

        except Exception as e:
            raise DecisionLayerError(
                "mtls_verification_failed", f"mTLS verification failed: {str(e)}"
            )

    def _verify_certificate_chain(self, cert: Any, cert_chain: List[bytes]) -> None:
        """Verify certificate chain against CA"""
        try:
            import cryptography.x509
            from cryptography.hazmat.primitives import hashes

            # Load CA certificate
            with open(self.config.ca_cert_path, "rb") as f:
                ca_cert = cryptography.x509.load_pem_x509_certificate(f.read())

            # Verify certificate against CA
            ca_public_key = ca_cert.public_key()

            # This is a simplified verification - in production, you'd use proper chain validation
            # including intermediate certificates, CRL checking, etc.

        except Exception as e:
            raise DecisionLayerError(
                "mtls_chain_verification_failed",
                f"Certificate chain verification failed: {str(e)}",
            )


class HybridAuthenticator:
    """Hybrid authenticator requiring both JWT and mTLS"""

    def __init__(self, jwt_config: JWTAuthConfig, mtls_config: MTLSConfig):
        self.jwt_authenticator = JWTAuthenticator(jwt_config)
        self.mtls_verifier = MTLSVerifier(mtls_config)

    def authenticate(
        self, jwt_token: str, client_cert: bytes, cert_chain: List[bytes]
    ) -> CallerIdentity:
        """Authenticate using both JWT and mTLS"""

        # Verify JWT token
        jwt_identity = self.jwt_authenticator.verify_token(jwt_token)

        # Verify mTLS certificate
        mtls_identity = self.mtls_verifier.verify_certificate(client_cert, cert_chain)

        # Ensure identities match
        if jwt_identity.caller_id != mtls_identity.caller_id:
            raise DecisionLayerError(
                "identity_mismatch",
                f"JWT subject {jwt_identity.caller_id} does not match certificate CN {mtls_identity.caller_id}",
            )

        # Combine capabilities from both sources
        combined_roles = list(set(jwt_identity.roles + mtls_identity.roles))
        combined_capabilities = list(
            set(jwt_identity.capabilities + mtls_identity.capabilities)
        )

        return CallerIdentity(
            caller_id=jwt_identity.caller_id,
            subject=jwt_identity.subject,
            issuer=jwt_identity.issuer,
            certificate_hash=mtls_identity.certificate_hash,
            certificate_cn=mtls_identity.certificate_cn,
            roles=combined_roles,
            capabilities=combined_capabilities,
            expires_at=jwt_identity.expires_at,
        )


class CallerAuthManager:
    """Centralized caller authentication manager"""

    def __init__(
        self,
        auth_method: AuthMethod,
        jwt_config: Optional[JWTAuthConfig] = None,
        mtls_config: Optional[MTLSConfig] = None,
    ):
        self.auth_method = auth_method
        self.authenticator: Optional[
            Union[JWTAuthenticator, MTLSVerifier, HybridAuthenticator]
        ] = None

        if auth_method == AuthMethod.JWT:
            if not jwt_config:
                raise DecisionLayerError(
                    "jwt_config_required", "JWT config required for JWT authentication"
                )
            self.authenticator = JWTAuthenticator(jwt_config)

        elif auth_method == AuthMethod.MTLS:
            if not mtls_config:
                raise DecisionLayerError(
                    "mtls_config_required",
                    "mTLS config required for mTLS authentication",
                )
            self.authenticator = MTLSVerifier(mtls_config)

        elif auth_method == AuthMethod.HYBRID:
            if not jwt_config or not mtls_config:
                raise DecisionLayerError(
                    "hybrid_config_required",
                    "Both JWT and mTLS config required for hybrid authentication",
                )
            self.authenticator = HybridAuthenticator(jwt_config, mtls_config)

    def authenticate_caller(self, **kwargs) -> CallerIdentity:
        """Authenticate caller based on configured method"""

        if self.auth_method == AuthMethod.JWT:
            jwt_token = kwargs.get("jwt_token")
            if not jwt_token:
                raise DecisionLayerError("jwt_token_required", "JWT token required")
            if not isinstance(self.authenticator, JWTAuthenticator):
                raise DecisionLayerError(
                    "invalid_authenticator", "JWT authenticator required"
                )
            return self.authenticator.verify_token(jwt_token)

        elif self.auth_method == AuthMethod.MTLS:
            client_cert = kwargs.get("client_cert")
            cert_chain = kwargs.get("cert_chain", [])
            if not client_cert:
                raise DecisionLayerError(
                    "client_cert_required", "Client certificate required"
                )
            if not isinstance(self.authenticator, MTLSVerifier):
                raise DecisionLayerError(
                    "invalid_authenticator", "mTLS authenticator required"
                )
            return self.authenticator.verify_certificate(client_cert, cert_chain)

        elif self.auth_method == AuthMethod.HYBRID:
            jwt_token = kwargs.get("jwt_token")
            client_cert = kwargs.get("client_cert")
            cert_chain = kwargs.get("cert_chain", [])
            if not jwt_token or not client_cert:
                raise DecisionLayerError(
                    "hybrid_auth_required",
                    "Both JWT token and client certificate required",
                )
            if not isinstance(self.authenticator, HybridAuthenticator):
                raise DecisionLayerError(
                    "invalid_authenticator", "Hybrid authenticator required"
                )
            return self.authenticator.authenticate(jwt_token, client_cert, cert_chain)

        else:
            raise DecisionLayerError(
                "unsupported_auth_method",
                f"Unsupported auth method: {self.auth_method}",
            )


# Global authentication manager
_auth_manager: Optional[CallerAuthManager] = None


def configure_caller_auth(
    auth_method: AuthMethod,
    jwt_config: Optional[JWTAuthConfig] = None,
    mtls_config: Optional[MTLSConfig] = None,
) -> None:
    """Configure caller authentication"""
    global _auth_manager
    _auth_manager = CallerAuthManager(auth_method, jwt_config, mtls_config)


def get_auth_manager() -> CallerAuthManager:
    """Get authentication manager instance"""
    global _auth_manager
    if _auth_manager is None:
        raise DecisionLayerError(
            "auth_not_configured",
            "Authentication not configured. Call configure_caller_auth() first.",
        )
    return _auth_manager


def authenticate_caller(**kwargs) -> CallerIdentity:
    """Authenticate caller"""
    manager = get_auth_manager()
    return manager.authenticate_caller(**kwargs)


def create_caller_context(identity: CallerIdentity) -> Dict[str, Any]:
    """Create caller context for trace records"""
    return {
        "caller_id": identity.caller_id,
        "subject": identity.subject,
        "issuer": identity.issuer,
        "certificate_hash": identity.certificate_hash,
        "certificate_cn": identity.certificate_cn,
        "roles": identity.roles,
        "capabilities": identity.capabilities,
        "authenticated_at": identity.authenticated_at.isoformat(),
        "expires_at": identity.expires_at.isoformat() if identity.expires_at else None,
    }
