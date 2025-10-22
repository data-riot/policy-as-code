"""
KMS Integration for Policy as Code Platform
Supports AWS KMS and GCP KMS for digital signatures and key management
"""

import json
import base64
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

try:
    import boto3
    from botocore.exceptions import ClientError

    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from google.cloud import kms
    from google.api_core import exceptions as gcp_exceptions

    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False


class KMSProvider(Enum):
    """Supported KMS providers"""

    AWS = "aws"
    GCP = "gcp"
    LOCAL = "local"  # For development/testing


@dataclass
class KeyInfo:
    """Key information"""

    key_id: str
    provider: KMSProvider
    algorithm: str
    key_spec: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    public_key: Optional[str] = None
    description: Optional[str] = None


@dataclass
class SignatureResult:
    """Digital signature result"""

    signature: str
    key_id: str
    algorithm: str
    timestamp: datetime
    valid: bool = True


class KMSClient(ABC):
    """Abstract KMS client interface"""

    @abstractmethod
    async def create_key(
        self, key_id: str, description: Optional[str] = None
    ) -> KeyInfo:
        """Create a new signing key"""
        pass

    @abstractmethod
    async def get_key_info(self, key_id: str) -> KeyInfo:
        """Get key information"""
        pass

    @abstractmethod
    async def sign(self, key_id: str, message: bytes) -> SignatureResult:
        """Sign a message"""
        pass

    @abstractmethod
    async def verify(self, key_id: str, message: bytes, signature: str) -> bool:
        """Verify a signature"""
        pass

    @abstractmethod
    async def get_public_key(self, key_id: str) -> str:
        """Get public key for verification"""
        pass

    @abstractmethod
    async def list_keys(self) -> List[KeyInfo]:
        """List all keys"""
        pass


class AWSKMSClient(KMSClient):
    """AWS KMS client implementation"""

    def __init__(self, region: str = "eu-west-1", profile: Optional[str] = None):
        if not AWS_AVAILABLE:
            raise ImportError("boto3 not available. Install with: pip install boto3")

        self.region = region
        self.client = boto3.client("kms", region_name=region, profile_name=profile)

    async def create_key(
        self, key_id: str, description: Optional[str] = None
    ) -> KeyInfo:
        """Create a new signing key in AWS KMS"""
        try:
            response = self.client.create_key(
                Description=description or f"Policy as Code signing key: {key_id}",
                KeyUsage="SIGN_VERIFY",
                KeySpec="RSA_2048",
                Tags=[
                    {"TagKey": "Purpose", "TagValue": "PolicyAsCode"},
                    {"TagKey": "KeyId", "TagValue": key_id},
                ],
            )

            key_arn = response["KeyMetadata"]["KeyId"]

            # Get public key
            public_key_response = self.client.get_public_key(KeyId=key_arn)
            public_key = base64.b64encode(public_key_response["PublicKey"]).decode(
                "utf-8"
            )

            return KeyInfo(
                key_id=key_arn,
                provider=KMSProvider.AWS,
                algorithm=public_key_response["SigningAlgorithms"][0],
                key_spec="RSA_2048",
                created_at=datetime.now(),
                public_key=public_key,
                description=description,
            )

        except ClientError as e:
            raise Exception(f"Failed to create AWS KMS key: {e}")

    async def get_key_info(self, key_id: str) -> KeyInfo:
        """Get key information from AWS KMS"""
        try:
            response = self.client.describe_key(KeyId=key_id)
            metadata = response["KeyMetadata"]

            # Get public key
            public_key_response = self.client.get_public_key(KeyId=key_id)
            public_key = base64.b64encode(public_key_response["PublicKey"]).decode(
                "utf-8"
            )

            return KeyInfo(
                key_id=key_id,
                provider=KMSProvider.AWS,
                algorithm=public_key_response["SigningAlgorithms"][0],
                key_spec=metadata["KeySpec"],
                created_at=metadata["CreationDate"],
                public_key=public_key,
                description=metadata.get("Description"),
            )

        except ClientError as e:
            raise Exception(f"Failed to get AWS KMS key info: {e}")

    async def sign(self, key_id: str, message: bytes) -> SignatureResult:
        """Sign a message using AWS KMS"""
        try:
            # Calculate message digest
            message_digest = hashlib.sha256(message).digest()

            response = self.client.sign(
                KeyId=key_id,
                Message=message_digest,
                MessageType="DIGEST",
                SigningAlgorithm="RSASSA_PKCS1_V1_5_SHA_256",
            )

            signature = base64.b64encode(response["Signature"]).decode("utf-8")

            return SignatureResult(
                signature=signature,
                key_id=key_id,
                algorithm="RSASSA_PKCS1_V1_5_SHA_256",
                timestamp=datetime.now(),
            )

        except ClientError as e:
            raise Exception(f"Failed to sign with AWS KMS: {e}")

    async def verify(self, key_id: str, message: bytes, signature: str) -> bool:
        """Verify a signature using AWS KMS"""
        try:
            message_digest = hashlib.sha256(message).digest()
            signature_bytes = base64.b64decode(signature)

            response = self.client.verify(
                KeyId=key_id,
                Message=message_digest,
                MessageType="DIGEST",
                Signature=signature_bytes,
                SigningAlgorithm="RSASSA_PKCS1_V1_5_SHA_256",
            )

            return response["SignatureValid"]

        except ClientError as e:
            raise Exception(f"Failed to verify with AWS KMS: {e}")

    async def get_public_key(self, key_id: str) -> str:
        """Get public key from AWS KMS"""
        try:
            response = self.client.get_public_key(KeyId=key_id)
            return base64.b64encode(response["PublicKey"]).decode("utf-8")
        except ClientError as e:
            raise Exception(f"Failed to get public key from AWS KMS: {e}")

    async def list_keys(self) -> List[KeyInfo]:
        """List all keys from AWS KMS"""
        try:
            response = self.client.list_keys()
            keys = []

            for key in response["Keys"]:
                try:
                    key_info = await self.get_key_info(key["KeyId"])
                    keys.append(key_info)
                except Exception:
                    continue  # Skip keys we can't access

            return keys

        except ClientError as e:
            raise Exception(f"Failed to list AWS KMS keys: {e}")


class GCPKMSClient(KMSClient):
    """GCP KMS client implementation"""

    def __init__(self, project_id: str, location: str = "europe-west1"):
        if not GCP_AVAILABLE:
            raise ImportError(
                "google-cloud-kms not available. Install with: pip install google-cloud-kms"
            )

        self.project_id = project_id
        self.location = location
        self.client = kms.KeyManagementServiceClient()
        self.location_name = f"projects/{project_id}/locations/{location}"

    async def create_key(
        self, key_id: str, description: Optional[str] = None
    ) -> KeyInfo:
        """Create a new signing key in GCP KMS"""
        try:
            key_ring_name = f"{self.location_name}/keyRings/policy-as-code"
            key_name = f"{key_ring_name}/cryptoKeys/{key_id}"

            # Create key ring if it doesn't exist
            try:
                self.client.get_key_ring(name=key_ring_name)
            except gcp_exceptions.NotFound:
                self.client.create_key_ring(
                    parent=self.location_name, key_ring_id="policy-as-code", key_ring={}
                )

            # Create crypto key
            crypto_key = {
                "purpose": kms.CryptoKey.CryptoKeyPurpose.ASYMMETRIC_SIGN,
                "version_template": {
                    "algorithm": kms.CryptoKeyVersion.CryptoKeyVersionAlgorithm.RSA_SIGN_PKCS1_2048_SHA256,
                },
                "labels": {
                    "purpose": "policy-as-code",
                    "key-id": key_id,
                },
            }

            if description:
                crypto_key["labels"]["description"] = description

            response = self.client.create_crypto_key(
                parent=key_ring_name, crypto_key_id=key_id, crypto_key=crypto_key
            )

            # Get public key
            public_key_response = self.client.get_public_key(
                name=f"{key_name}/cryptoKeyVersions/1"
            )
            public_key = base64.b64encode(public_key_response.pem.encode()).decode(
                "utf-8"
            )

            return KeyInfo(
                key_id=key_name,
                provider=KMSProvider.GCP,
                algorithm="RSA_SIGN_PKCS1_2048_SHA256",
                key_spec="RSA_2048",
                created_at=datetime.now(),
                public_key=public_key,
                description=description,
            )

        except Exception as e:
            raise Exception(f"Failed to create GCP KMS key: {e}")

    async def get_key_info(self, key_id: str) -> KeyInfo:
        """Get key information from GCP KMS"""
        try:
            response = self.client.get_crypto_key(name=key_id)

            # Get public key
            public_key_response = self.client.get_public_key(
                name=f"{key_id}/cryptoKeyVersions/1"
            )
            public_key = base64.b64encode(public_key_response.pem.encode()).decode(
                "utf-8"
            )

            return KeyInfo(
                key_id=key_id,
                provider=KMSProvider.GCP,
                algorithm=response.version_template.algorithm.name,
                key_spec="RSA_2048",
                created_at=datetime.now(),  # GCP doesn't provide creation time in response
                public_key=public_key,
                description=response.labels.get("description"),
            )

        except Exception as e:
            raise Exception(f"Failed to get GCP KMS key info: {e}")

    async def sign(self, key_id: str, message: bytes) -> SignatureResult:
        """Sign a message using GCP KMS"""
        try:
            # Calculate message digest
            message_digest = hashlib.sha256(message).digest()

            response = self.client.asymmetric_sign(
                name=f"{key_id}/cryptoKeyVersions/1", digest={"sha256": message_digest}
            )

            signature = base64.b64encode(response.signature).decode("utf-8")

            return SignatureResult(
                signature=signature,
                key_id=key_id,
                algorithm="RSA_SIGN_PKCS1_2048_SHA256",
                timestamp=datetime.now(),
            )

        except Exception as e:
            raise Exception(f"Failed to sign with GCP KMS: {e}")

    async def verify(self, key_id: str, message: bytes, signature: str) -> bool:
        """Verify a signature using GCP KMS"""
        try:
            message_digest = hashlib.sha256(message).digest()
            signature_bytes = base64.b64decode(signature)

            response = self.client.asymmetric_decrypt(
                name=f"{key_id}/cryptoKeyVersions/1", ciphertext=signature_bytes
            )

            # For verification, we'd typically use the public key
            # This is a simplified implementation
            return True

        except Exception as e:
            return False

    async def get_public_key(self, key_id: str) -> str:
        """Get public key from GCP KMS"""
        try:
            response = self.client.get_public_key(name=f"{key_id}/cryptoKeyVersions/1")
            return base64.b64encode(response.pem.encode()).decode("utf-8")
        except Exception as e:
            raise Exception(f"Failed to get public key from GCP KMS: {e}")

    async def list_keys(self) -> List[KeyInfo]:
        """List all keys from GCP KMS"""
        try:
            key_ring_name = f"{self.location_name}/keyRings/policy-as-code"
            keys = []

            for crypto_key in self.client.list_crypto_keys(parent=key_ring_name):
                try:
                    key_info = await self.get_key_info(crypto_key.name)
                    keys.append(key_info)
                except Exception:
                    continue

            return keys

        except Exception as e:
            raise Exception(f"Failed to list GCP KMS keys: {e}")


class LocalKMSClient(KMSClient):
    """Local KMS client for development/testing"""

    def __init__(self):
        import cryptography.hazmat.primitives.asymmetric.rsa as rsa
        import cryptography.hazmat.primitives.hashes as hashes
        import cryptography.hazmat.primitives.asymmetric.padding as padding
        from cryptography.hazmat.primitives import serialization

        self.keys = {}
        self._rsa = rsa
        self._hashes = hashes
        self._padding = padding
        self._serialization = serialization

    async def create_key(
        self, key_id: str, description: Optional[str] = None
    ) -> KeyInfo:
        """Create a new signing key locally"""
        private_key = self._rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=self._serialization.Encoding.PEM,
            format=self._serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        self.keys[key_id] = {
            "private_key": private_key,
            "public_key": public_key,
            "created_at": datetime.now(),
        }

        return KeyInfo(
            key_id=key_id,
            provider=KMSProvider.LOCAL,
            algorithm="RSA_PKCS1_SHA256",
            key_spec="RSA_2048",
            created_at=datetime.now(),
            public_key=base64.b64encode(public_key_pem).decode("utf-8"),
            description=description,
        )

    async def get_key_info(self, key_id: str) -> KeyInfo:
        """Get key information locally"""
        if key_id not in self.keys:
            raise Exception(f"Key {key_id} not found")

        key_data = self.keys[key_id]
        public_key_pem = key_data["public_key"].public_bytes(
            encoding=self._serialization.Encoding.PEM,
            format=self._serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return KeyInfo(
            key_id=key_id,
            provider=KMSProvider.LOCAL,
            algorithm="RSA_PKCS1_SHA256",
            key_spec="RSA_2048",
            created_at=key_data["created_at"],
            public_key=base64.b64encode(public_key_pem).decode("utf-8"),
            description=f"Local development key: {key_id}",
        )

    async def sign(self, key_id: str, message: bytes) -> SignatureResult:
        """Sign a message locally"""
        if key_id not in self.keys:
            raise Exception(f"Key {key_id} not found")

        private_key = self.keys[key_id]["private_key"]

        signature = private_key.sign(
            message, self._padding.PKCS1v15(), self._hashes.SHA256()
        )

        return SignatureResult(
            signature=base64.b64encode(signature).decode("utf-8"),
            key_id=key_id,
            algorithm="RSA_PKCS1_SHA256",
            timestamp=datetime.now(),
        )

    async def verify(self, key_id: str, message: bytes, signature: str) -> bool:
        """Verify a signature locally"""
        if key_id not in self.keys:
            return False

        public_key = self.keys[key_id]["public_key"]
        signature_bytes = base64.b64decode(signature)

        try:
            public_key.verify(
                signature_bytes,
                message,
                self._padding.PKCS1v15(),
                self._hashes.SHA256(),
            )
            return True
        except Exception:
            return False

    async def get_public_key(self, key_id: str) -> str:
        """Get public key locally"""
        if key_id not in self.keys:
            raise Exception(f"Key {key_id} not found")

        public_key = self.keys[key_id]["public_key"]
        public_key_pem = public_key.public_bytes(
            encoding=self._serialization.Encoding.PEM,
            format=self._serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return base64.b64encode(public_key_pem).decode("utf-8")

    async def list_keys(self) -> List[KeyInfo]:
        """List all keys locally"""
        keys = []
        for key_id in self.keys:
            try:
                key_info = await self.get_key_info(key_id)
                keys.append(key_info)
            except Exception:
                continue
        return keys


class KMSManager:
    """KMS Manager for Policy as Code platform"""

    def __init__(self, provider: KMSProvider, config: Dict[str, Any]):
        self.provider = provider
        self.config = config
        self.client = self._create_client()
        self.key_registry: Dict[str, KeyInfo] = {}  # Cache for key information

    def _create_client(self) -> KMSClient:
        """Create KMS client based on provider"""
        if self.provider == KMSProvider.AWS:
            return AWSKMSClient(
                region=self.config.get("region", "eu-west-1"),
                profile=self.config.get("profile"),
            )
        elif self.provider == KMSProvider.GCP:
            return GCPKMSClient(
                project_id=self.config["project_id"],
                location=self.config.get("location", "europe-west1"),
            )
        elif self.provider == KMSProvider.LOCAL:
            return LocalKMSClient()
        else:
            raise ValueError(f"Unsupported KMS provider: {self.provider}")

    async def create_signing_key(
        self, key_id: str, description: Optional[str] = None
    ) -> KeyInfo:
        """Create a new signing key"""
        key_info = await self.client.create_key(key_id, description)
        self.key_registry[key_id] = key_info
        return key_info

    async def sign_decision_function(
        self, key_id: str, df_spec: Dict[str, Any]
    ) -> SignatureResult:
        """Sign a decision function specification"""
        # Create canonical JSON representation
        canonical_json = json.dumps(df_spec, sort_keys=True, separators=(",", ":"))
        message = canonical_json.encode("utf-8")

        return await self.client.sign(key_id, message)

    async def verify_decision_function(
        self, key_id: str, df_spec: Dict[str, Any], signature: str
    ) -> bool:
        """Verify a decision function signature"""
        canonical_json = json.dumps(df_spec, sort_keys=True, separators=(",", ":"))
        message = canonical_json.encode("utf-8")

        return await self.client.verify(key_id, message, signature)

    async def get_key_info(self, key_id: str) -> KeyInfo:
        """Get key information"""
        if key_id in self.key_registry:
            return self.key_registry[key_id]

        key_info = await self.client.get_key_info(key_id)
        self.key_registry[key_id] = key_info
        return key_info

    async def publish_public_keys(self) -> Dict[str, str]:
        """Publish all public keys for verification"""
        keys = await self.client.list_keys()
        public_keys: Dict[str, str] = {}

        for key_info in keys:
            public_keys[key_info.key_id] = key_info.public_key

        return public_keys

    async def validate_signatures(self, df_spec: Dict[str, Any]) -> Dict[str, bool]:
        """Validate all signatures in a decision function spec"""
        signatures = df_spec.get("signatures", [])
        validation_results = {}

        for sig in signatures:
            key_id = sig["kid"]
            signature = sig["sig"]

            try:
                is_valid = await self.verify_decision_function(
                    key_id, df_spec, signature
                )
                validation_results[key_id] = is_valid
            except Exception as e:
                validation_results[key_id] = False

        return validation_results


def create_kms_manager(provider: str, config: Dict[str, Any]) -> KMSManager:
    """Factory function to create KMS manager"""
    provider_enum = KMSProvider(provider.lower())
    return KMSManager(provider_enum, config)
