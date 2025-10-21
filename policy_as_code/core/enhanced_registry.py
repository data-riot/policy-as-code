"""
Enhanced Registry with Legal IRI Enforcement
Enforces legal references at registry level for all decision functions

PRODUCTION STATUS: ✅ IMPLEMENTED
- Legal IRI validation at registry level
- Deny-by-default with explicit allow lists
- Legal compliance caching

MISSING PRODUCTION FEATURES:
- Database persistence (currently in-memory only)
- Distributed registry synchronization
- Legal reference freshness checking
- Automated legal reference updates from Finlex/EUR-Lex APIs
- Registry backup and disaster recovery
- Multi-tenant registry isolation
- Registry versioning and migration support
- Performance optimization for large registries (1000+ functions)
- Registry replication across regions
- Legal reference conflict resolution
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .errors import DecisionLayerError
from .legal_refs import (
    LawReference,
    validate_legal_references_in_metadata,
    LegalReferenceError,
)


@dataclass
class DecisionFunctionSpec:
    """Enhanced decision function specification with legal compliance"""

    function_id: str
    version: str
    function_type: str  # "python", "dsl", "hybrid"
    legal_references: List[LawReference]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    metadata: Dict[str, Any]
    explain: Optional[Dict[str, Any]] = None
    security: Optional[Dict[str, Any]] = None
    function_code: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tests: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Validate legal references after initialization"""
        self._validate_legal_references()
        self._validate_explain_policy()

    def _validate_legal_references(self) -> None:
        """Enforce legal IRI validation at registry level

        PRODUCTION NOTES:
        - Currently validates IRI format only
        - MISSING: Actual HTTP validation against Finlex/EUR-Lex endpoints
        - MISSING: Legal reference freshness checking (laws change over time)
        - MISSING: Cross-reference validation (ensuring referenced sections exist)
        - MISSING: Legal hierarchy validation (acts, sections, subsections)
        - MISSING: Jurisdiction-specific validation rules
        """
        if not self.legal_references:
            raise DecisionLayerError(
                "missing_legal_references",
                f"Decision function {self.function_id} must have at least one legal reference",
            )

        for ref in self.legal_references:
            # PSEUDOCODE: This only validates format, not actual legal content
            # Convert LawReference to dict for validation
            ref_dict = {"policy_references": [ref]}
            try:
                validate_legal_references_in_metadata(ref_dict)
            except LegalReferenceError:
                raise DecisionLayerError(
                    "invalid_legal_reference",
                    f"Invalid legal URI: {ref.uri}. Must be valid Finlex or EUR-Lex reference",
                )

            # MISSING PRODUCTION LOGIC:
            # 1. HTTP GET request to validate IRI exists
            # 2. Check if legal reference is still in force
            # 3. Validate section/subsection exists in the referenced law
            # 4. Check for legal reference conflicts or contradictions
            # 5. Cache validation results with TTL
            # 6. Handle network failures gracefully

    def _validate_explain_policy(self) -> None:
        """Validate explanation and redaction policy"""
        if self.explain:
            # Ensure deny-by-default with explicit allow list
            if "allow_fields" not in self.explain:
                raise DecisionLayerError(
                    "missing_explain_policy",
                    f"Decision function {self.function_id} must specify allow_fields for explanation policy",
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "function_id": self.function_id,
            "version": self.version,
            "function_type": self.function_type,
            "legal_references": [ref.to_dict() for ref in self.legal_references],
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "metadata": self.metadata,
            "explain": self.explain,
            "security": self.security,
            "function_code": self.function_code,
            "dependencies": self.dependencies,
            "tests": self.tests,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionFunctionSpec":
        """Create from dictionary"""
        legal_refs = [
            LawReference.from_dict(ref) for ref in data.get("legal_references", [])
        ]

        return cls(
            function_id=data["function_id"],
            version=data["version"],
            function_type=data["function_type"],
            legal_references=legal_refs,
            input_schema=data["input_schema"],
            output_schema=data["output_schema"],
            metadata=data["metadata"],
            explain=data.get("explain"),
            security=data.get("security"),
            function_code=data.get("function_code"),
            dependencies=data.get("dependencies", []),
            tests=data.get("tests", []),
        )


class EnhancedRegistry:
    """Registry with mandatory legal compliance enforcement

    PRODUCTION STATUS: ⚠️ PARTIAL IMPLEMENTATION
    - Legal compliance validation implemented
    - In-memory storage only (not production-ready)

    MISSING PRODUCTION FEATURES:
    - Database persistence (PostgreSQL/MySQL)
    - Distributed caching (Redis)
    - Registry replication and synchronization
    - Performance optimization for large datasets
    - Backup and disaster recovery
    - Multi-tenant isolation
    - Registry versioning and migration
    - Legal reference monitoring and updates
    - Compliance reporting and analytics
    """

    def __init__(self):
        # PSEUDOCODE: In-memory storage - NOT production ready
        self.functions: Dict[str, Dict[str, DecisionFunctionSpec]] = {}
        self.active_versions: Dict[str, str] = {}
        self._legal_compliance_cache: Dict[str, bool] = {}

        # MISSING PRODUCTION LOGIC:
        # 1. Database connection and initialization
        # 2. Cache configuration (Redis/Memcached)
        # 3. Registry replication setup
        # 4. Performance monitoring
        # 5. Backup scheduling
        # 6. Multi-tenant configuration

    def register_function(self, spec: DecisionFunctionSpec) -> None:
        """Register decision function with legal compliance validation"""
        # Legal IRI enforcement happens in DecisionFunctionSpec.__post_init__

        if spec.function_id not in self.functions:
            self.functions[spec.function_id] = {}

        # Store the specification
        self.functions[spec.function_id][spec.version] = spec

        # Cache legal compliance status
        self._legal_compliance_cache[f"{spec.function_id}:{spec.version}"] = True

        print(
            f"✅ Registered {spec.function_id} v{spec.version} with {len(spec.legal_references)} legal references"
        )

    def get_function(
        self, function_id: str, version: Optional[str] = None
    ) -> Optional[DecisionFunctionSpec]:
        """Get decision function specification"""
        if function_id not in self.functions:
            return None

        if version:
            return self.functions[function_id].get(version)
        else:
            # Return latest version
            latest_version = self.active_versions.get(function_id)
            if latest_version:
                return self.functions[function_id].get(latest_version)
            return None

    def validate_legal_compliance(self, function_id: str, version: str) -> bool:
        """Validate legal compliance for a function version"""
        cache_key = f"{function_id}:{version}"

        if cache_key in self._legal_compliance_cache:
            return self._legal_compliance_cache[cache_key]

        spec = self.get_function(function_id, version)
        if not spec:
            return False

        try:
            # Re-validate legal references
            for ref in spec.legal_references:
                ref_dict = {"policy_references": [ref]}
                try:
                    validate_legal_references_in_metadata(ref_dict)
                except LegalReferenceError:
                    self._legal_compliance_cache[cache_key] = False
                    return False

            self._legal_compliance_cache[cache_key] = True
            return True

        except Exception:
            self._legal_compliance_cache[cache_key] = False
            return False

    def get_legal_references(
        self, function_id: str, version: Optional[str] = None
    ) -> List[LawReference]:
        """Get legal references for a function"""
        spec = self.get_function(function_id, version)
        if not spec:
            return []
        return spec.legal_references

    def get_explain_policy(
        self, function_id: str, version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get explanation policy for a function"""
        spec = self.get_function(function_id, version)
        if not spec:
            return None
        return spec.explain

    def list_functions(self) -> List[Dict[str, Any]]:
        """List all registered functions with compliance status"""
        result = []

        for function_id, versions in self.functions.items():
            for version, spec in versions.items():
                compliance_status = self.validate_legal_compliance(function_id, version)

                result.append(
                    {
                        "function_id": function_id,
                        "version": version,
                        "legal_references_count": len(spec.legal_references),
                        "legal_compliance": compliance_status,
                        "metadata": spec.metadata,
                        "registered_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

        return result

    def enforce_legal_compliance(self) -> Dict[str, Any]:
        """Enforce legal compliance across all functions"""
        non_compliant = []
        compliant = []

        for function_id, versions in self.functions.items():
            for version, spec in versions.items():
                if self.validate_legal_compliance(function_id, version):
                    compliant.append(f"{function_id}:{version}")
                else:
                    non_compliant.append(
                        {
                            "function_id": function_id,
                            "version": version,
                            "issue": "Invalid legal references",
                        }
                    )

        return {
            "compliant_count": len(compliant),
            "non_compliant_count": len(non_compliant),
            "compliant_functions": compliant,
            "non_compliant_functions": non_compliant,
            "enforcement_timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global registry instance
_enhanced_registry: Optional[EnhancedRegistry] = None


def get_enhanced_registry() -> EnhancedRegistry:
    """Get global enhanced registry instance"""
    global _enhanced_registry
    if _enhanced_registry is None:
        _enhanced_registry = EnhancedRegistry()
    return _enhanced_registry


def register_function_with_legal_compliance(spec_data: Dict[str, Any]) -> None:
    """Register function with mandatory legal compliance"""
    try:
        spec = DecisionFunctionSpec.from_dict(spec_data)
        registry = get_enhanced_registry()
        registry.register_function(spec)
    except DecisionLayerError as e:
        raise e
    except Exception as e:
        raise DecisionLayerError(
            "registration_failed", f"Failed to register function: {str(e)}"
        )


def validate_function_legal_compliance(function_id: str, version: str) -> bool:
    """Validate legal compliance for a specific function version"""
    registry = get_enhanced_registry()
    return registry.validate_legal_compliance(function_id, version)


def get_function_legal_references(
    function_id: str, version: Optional[str] = None
) -> List[LawReference]:
    """Get legal references for a function"""
    registry = get_enhanced_registry()
    return registry.get_legal_references(function_id, version)


def enforce_all_legal_compliance() -> Dict[str, Any]:
    """Enforce legal compliance across all registered functions"""
    registry = get_enhanced_registry()
    return registry.enforce_legal_compliance()
