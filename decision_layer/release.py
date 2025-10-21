"""
Release Management with Digital Signatures
Change control with separation of duties and release gates
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .errors import DecisionLayerError
from .legal_refs import LawReference, LegalReferenceValidator


class ReleaseStatus(str, Enum):
    """Release status states"""

    DRAFT = "draft"
    PENDING_OWNER_SIGNATURE = "pending_owner_signature"
    PENDING_REVIEWER_SIGNATURE = "pending_reviewer_signature"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class SignerRole(str, Enum):
    """Signer roles for separation of duties"""

    OWNER = "owner"  # Function owner/developer
    REVIEWER = "reviewer"  # Independent reviewer
    AUDITOR = "auditor"  # External auditor (optional)


@dataclass(frozen=True)
class DigitalSignature:
    """Digital signature for release approval"""

    signer_id: str
    role: SignerRole
    signature_hash: str
    timestamp: datetime
    comment: Optional[str] = None
    public_key_fingerprint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "signer_id": self.signer_id,
            "role": self.role.value,
            "signature_hash": self.signature_hash,
            "timestamp": self.timestamp.isoformat(),
            "comment": self.comment,
            "public_key_fingerprint": self.public_key_fingerprint,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DigitalSignature":
        """Create from dictionary"""
        return cls(
            signer_id=data["signer_id"],
            role=SignerRole(data["role"]),
            signature_hash=data["signature_hash"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            comment=data.get("comment"),
            public_key_fingerprint=data.get("public_key_fingerprint"),
        )


@dataclass
class Release:
    """Release with digital signatures and legal references"""

    function_id: str
    version: str
    status: ReleaseStatus
    created_at: datetime
    updated_at: datetime
    legal_references: List[LawReference] = field(default_factory=list)
    signatures: List[DigitalSignature] = field(default_factory=list)
    change_summary: Optional[str] = None
    risk_assessment: Optional[str] = None
    compliance_checklist: List[str] = field(default_factory=list)
    release_notes: Optional[str] = None

    def add_signature(self, signature: DigitalSignature) -> None:
        """Add a signature to the release"""
        # Check if signer already signed
        for existing_sig in self.signatures:
            if (
                existing_sig.signer_id == signature.signer_id
                and existing_sig.role == signature.role
            ):
                raise ReleaseError(
                    "duplicate_signature",
                    f"Signer {signature.signer_id} already signed as {signature.role.value}",
                )

        self.signatures.append(signature)
        self.updated_at = datetime.now(timezone.utc)

        # Update status based on signatures
        self._update_status()

    def _update_status(self) -> None:
        """Update release status based on signatures"""
        owner_signed = any(sig.role == SignerRole.OWNER for sig in self.signatures)
        reviewer_signed = any(
            sig.role == SignerRole.REVIEWER for sig in self.signatures
        )

        if not owner_signed:
            self.status = ReleaseStatus.PENDING_OWNER_SIGNATURE
        elif not reviewer_signed:
            self.status = ReleaseStatus.PENDING_REVIEWER_SIGNATURE
        else:
            self.status = ReleaseStatus.APPROVED

    def can_activate(self) -> bool:
        """Check if release can be activated"""
        return (
            self.status == ReleaseStatus.APPROVED
            and len(self.legal_references) > 0
            and any(sig.role == SignerRole.OWNER for sig in self.signatures)
            and any(sig.role == SignerRole.REVIEWER for sig in self.signatures)
        )

    def activate(self) -> None:
        """Activate the release"""
        if not self.can_activate():
            raise ReleaseError(
                "activation_failed",
                "Release cannot be activated: missing signatures or legal references",
            )

        self.status = ReleaseStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "function_id": self.function_id,
            "version": self.version,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "legal_references": [ref.to_dict() for ref in self.legal_references],
            "signatures": [sig.to_dict() for sig in self.signatures],
            "change_summary": self.change_summary,
            "risk_assessment": self.risk_assessment,
            "compliance_checklist": self.compliance_checklist,
            "release_notes": self.release_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Release":
        """Create from dictionary"""
        legal_refs = [
            LawReference.from_dict(ref) for ref in data.get("legal_references", [])
        ]
        signatures = [
            DigitalSignature.from_dict(sig) for sig in data.get("signatures", [])
        ]

        return cls(
            function_id=data["function_id"],
            version=data["version"],
            status=ReleaseStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            legal_references=legal_refs,
            signatures=signatures,
            change_summary=data.get("change_summary"),
            risk_assessment=data.get("risk_assessment"),
            compliance_checklist=data.get("compliance_checklist", []),
            release_notes=data.get("release_notes"),
        )


class ReleaseError(DecisionLayerError):
    """Release management errors"""

    def __init__(self, error_type: str, message: str):
        super().__init__(f"Release error ({error_type}): {message}")
        self.error_type = error_type


class SignatureValidator:
    """Validator for digital signatures"""

    @staticmethod
    def create_signature(
        signer_id: str,
        role: SignerRole,
        content_hash: str,
        private_key: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> DigitalSignature:
        """Create a digital signature"""
        # In production, this would use proper cryptographic signing
        # For now, we'll create a hash-based signature
        signature_data = f"{signer_id}:{role.value}:{content_hash}:{datetime.now(timezone.utc).isoformat()}"
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()

        return DigitalSignature(
            signer_id=signer_id,
            role=role,
            signature_hash=signature_hash,
            timestamp=datetime.now(timezone.utc),
            comment=comment,
            public_key_fingerprint=f"key_{signer_id}_{hashlib.sha256(signer_id.encode()).hexdigest()[:8]}",
        )

    @staticmethod
    def verify_signature(signature: DigitalSignature, content_hash: str) -> bool:
        """Verify a digital signature"""
        # In production, this would verify the actual cryptographic signature
        # For now, we'll do a basic validation
        return len(signature.signature_hash) == 64  # SHA256 hex length

    @staticmethod
    def validate_signature_requirements(release: Release) -> List[str]:
        """Validate signature requirements for a release"""
        errors = []

        # Check for owner signature
        owner_signed = any(sig.role == SignerRole.OWNER for sig in release.signatures)
        if not owner_signed:
            errors.append("Missing owner signature")

        # Check for reviewer signature
        reviewer_signed = any(
            sig.role == SignerRole.REVIEWER for sig in release.signatures
        )
        if not reviewer_signed:
            errors.append("Missing reviewer signature")

        # Check for separation of duties
        signers = {sig.signer_id for sig in release.signatures}
        if len(signers) < 2:
            errors.append(
                "Separation of duties requires at least two different signers"
            )

        return errors


class ReleaseManager:
    """Manager for release lifecycle"""

    def __init__(self):
        self.releases: Dict[
            str, Dict[str, Release]
        ] = {}  # function_id -> version -> Release

    def create_release(
        self,
        function_id: str,
        version: str,
        legal_references: List[LawReference],
        change_summary: Optional[str] = None,
        risk_assessment: Optional[str] = None,
        compliance_checklist: Optional[List[str]] = None,
        release_notes: Optional[str] = None,
    ) -> Release:
        """Create a new release"""
        if function_id in self.releases and version in self.releases[function_id]:
            raise ReleaseError(
                "duplicate_release", f"Release {function_id} v{version} already exists"
            )

        # Validate legal references
        validated_refs = LegalReferenceValidator.validate_reference_list(
            legal_references
        )

        release = Release(
            function_id=function_id,
            version=version,
            status=ReleaseStatus.DRAFT,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            legal_references=validated_refs,
            change_summary=change_summary,
            risk_assessment=risk_assessment,
            compliance_checklist=compliance_checklist or [],
            release_notes=release_notes,
        )

        if function_id not in self.releases:
            self.releases[function_id] = {}

        self.releases[function_id][version] = release
        return release

    def get_release(self, function_id: str, version: str) -> Optional[Release]:
        """Get a release"""
        return self.releases.get(function_id, {}).get(version)

    def list_releases(self, function_id: Optional[str] = None) -> List[Release]:
        """List releases"""
        releases = []
        for fid, versions in self.releases.items():
            if function_id and fid != function_id:
                continue
            releases.extend(versions.values())
        return releases

    def sign_release(
        self,
        function_id: str,
        version: str,
        signer_id: str,
        role: SignerRole,
        comment: Optional[str] = None,
    ) -> Release:
        """Sign a release"""
        release = self.get_release(function_id, version)
        if not release:
            raise ReleaseError(
                "release_not_found", f"Release {function_id} v{version} not found"
            )

        # Create content hash for signing
        content_hash = self._compute_release_hash(release)

        # Create signature
        signature = SignatureValidator.create_signature(
            signer_id=signer_id, role=role, content_hash=content_hash, comment=comment
        )

        # Add signature to release
        release.add_signature(signature)

        return release

    def activate_release(self, function_id: str, version: str) -> Release:
        """Activate a release"""
        release = self.get_release(function_id, version)
        if not release:
            raise ReleaseError(
                "release_not_found", f"Release {function_id} v{version} not found"
            )

        # Validate signature requirements
        errors = SignatureValidator.validate_signature_requirements(release)
        if errors:
            raise ReleaseError(
                "activation_failed", f"Cannot activate release: {'; '.join(errors)}"
            )

        release.activate()
        return release

    def _compute_release_hash(self, release: Release) -> str:
        """Compute hash of release content for signing"""
        content = {
            "function_id": release.function_id,
            "version": release.version,
            "legal_references": [ref.to_dict() for ref in release.legal_references],
            "change_summary": release.change_summary,
            "risk_assessment": release.risk_assessment,
            "compliance_checklist": release.compliance_checklist,
        }

        content_str = json.dumps(content, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content_str.encode()).hexdigest()

    def get_active_releases(self) -> List[Release]:
        """Get all active releases"""
        active_releases = []
        for function_id, versions in self.releases.items():
            for version, release in versions.items():
                if release.status == ReleaseStatus.ACTIVE:
                    active_releases.append(release)
        return active_releases

    def can_execute_function(self, function_id: str, version: str) -> bool:
        """Check if a function version can be executed (is active)"""
        release = self.get_release(function_id, version)
        return release is not None and release.status == ReleaseStatus.ACTIVE


def create_release_manager() -> ReleaseManager:
    """Create a release manager instance"""
    return ReleaseManager()
