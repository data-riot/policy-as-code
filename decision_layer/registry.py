"""
Function registry for managing decision functions
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .errors import RegistryError
from .schemas import create_schema_from_dict


class FunctionStatus(Enum):
    """Status of a decision function"""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class FunctionMetadata:
    """Rich metadata for decision functions"""

    function_id: str
    version: str
    title: str
    created_at: datetime
    updated_at: datetime
    status: FunctionStatus
    content_hash: str
    description: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    policy_references: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    change_log: List[Dict[str, Any]] = field(default_factory=list)
    approval_history: List[Dict[str, Any]] = field(default_factory=list)
    usage_metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.policy_references is None:
            self.policy_references = []
        if self.compliance_requirements is None:
            self.compliance_requirements = []
        if self.dependencies is None:
            self.dependencies = []
        if self.change_log is None:
            self.change_log = []
        if self.approval_history is None:
            self.approval_history = []
        if self.usage_metrics is None:
            self.usage_metrics = {}


@dataclass
class FunctionArtifact:
    """Complete function artifact with code, schema, and metadata"""

    function_id: str
    version: str
    logic_code: str
    schema: Any  # DecisionSchema
    metadata: FunctionMetadata
    content_hash: str


class FunctionRegistry:
    """Central registry for managing decision functions"""

    def __init__(self, storage_backend=None):
        self.storage_backend = storage_backend
        self.functions: Dict[str, Dict[str, FunctionMetadata]] = {}

    def deploy_function(
        self,
        function_id: str,
        version: str,
        function_code: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Deploy a new version of a decision function"""
        try:
            # Validate schemas
            create_schema_from_dict(input_schema)
            create_schema_from_dict(output_schema)

            # Generate content hash
            content = (
                f"{function_code}{json.dumps(input_schema)}{json.dumps(output_schema)}"
            )
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Create metadata
            now = datetime.now(timezone.utc)
            function_metadata = FunctionMetadata(
                function_id=function_id,
                version=version,
                title=metadata.get("title", function_id) if metadata else function_id,
                created_at=now,
                updated_at=now,
                status=FunctionStatus.DRAFT,
                content_hash=content_hash,
                description=metadata.get("description") if metadata else None,
                author=metadata.get("author") if metadata else None,
                tags=metadata.get("tags", []) if metadata else [],
                policy_references=(
                    metadata.get("policy_references", []) if metadata else []
                ),
                compliance_requirements=(
                    metadata.get("compliance_requirements", []) if metadata else []
                ),
                dependencies=metadata.get("dependencies", []) if metadata else [],
            )

            # Store function
            if function_id not in self.functions:
                self.functions[function_id] = {}

            self.functions[function_id][version] = function_metadata

            # Store in backend if available
            if self.storage_backend:
                self.storage_backend.store_function(
                    function_id,
                    version,
                    function_code,
                    input_schema,
                    output_schema,
                    function_metadata,
                )

        except Exception as e:
            raise RegistryError("deploy_function", str(e))

    def get_function(
        self, function_id: str, version: Optional[str] = None
    ) -> FunctionArtifact:
        """Get function artifact"""
        if function_id not in self.functions:
            raise RegistryError("get_function", f"Function {function_id} not found")

        if version is None:
            version = self.get_latest_version(function_id)

        if version not in self.functions[function_id]:
            raise RegistryError(
                "get_function", f"Version {version} not found for {function_id}"
            )

        metadata = self.functions[function_id][version]

        # For now, return a mock artifact since we don't store code/schema
        # In a real implementation, these would be retrieved from storage
        return FunctionArtifact(
            function_id=function_id,
            version=version,
            logic_code="# Mock code - would be retrieved from storage",
            schema=None,  # Mock schema - would be retrieved from storage
            metadata=metadata,
            content_hash=metadata.content_hash,
        )

    def get_latest_version(self, function_id: str) -> str:
        """Get the latest version of a function"""
        if function_id not in self.functions:
            raise RegistryError("get_function", f"Function {function_id} not found")

        versions = list(self.functions[function_id].keys())
        if not versions:
            raise RegistryError(
                "get_function", f"No versions found for function {function_id}"
            )

        # Simple version comparison - in production, use proper semver
        return max(versions)

    def register_function(
        self,
        function_id: str,
        version: str,
        logic_code: str,
        schema: Any,
        metadata: Dict[str, Any],
        status: str = "draft",
    ) -> FunctionArtifact:
        """Register a new function and return FunctionArtifact"""
        # Create metadata
        now = datetime.now(timezone.utc)
        content_hash = hashlib.sha256(logic_code.encode()).hexdigest()

        function_metadata = FunctionMetadata(
            function_id=function_id,
            version=version,
            title=metadata.get("title", function_id),
            created_at=now,
            updated_at=now,
            status=FunctionStatus(status.upper()),
            content_hash=content_hash,
            description=metadata.get("description"),
            author=metadata.get("author"),
            tags=metadata.get("tags", []),
            policy_references=metadata.get("policy_references", []),
            compliance_requirements=metadata.get("compliance_requirements", []),
            dependencies=metadata.get("dependencies", []),
        )

        # Store in registry
        if function_id not in self.functions:
            self.functions[function_id] = {}
        self.functions[function_id][version] = function_metadata

        # Create and return artifact
        return FunctionArtifact(
            function_id=function_id,
            version=version,
            logic_code=logic_code,
            schema=schema,
            metadata=function_metadata,
            content_hash=content_hash,
        )

    def list_functions(
        self, status: Optional[FunctionStatus] = None
    ) -> List[Dict[str, Any]]:
        """List all functions with optional status filter"""
        result = []
        for function_id, versions in self.functions.items():
            for version, metadata in versions.items():
                if status is None or metadata.status == status:
                    result.append(
                        {
                            "function_id": function_id,
                            "version": version,
                            "title": metadata.title,
                            "status": metadata.status.value,
                            "created_at": metadata.created_at.isoformat(),
                            "author": metadata.author,
                            "description": metadata.description,
                        }
                    )
        return result

    def update_status(
        self, function_id: str, version: str, status: FunctionStatus
    ) -> None:
        """Update function status"""
        try:
            metadata = self.get_function(function_id, version)
            metadata.status = status
            metadata.updated_at = datetime.now(timezone.utc)

            # Add to approval history
            metadata.approval_history.append(
                {
                    "status": status.value,
                    "timestamp": metadata.updated_at.isoformat(),
                    "updated_by": "system",  # Would be user in real implementation
                }
            )

        except Exception as e:
            raise RegistryError("update_status", str(e))

    def get_function_info(self, function_id: str) -> Dict[str, Any]:
        """Get detailed information about a function"""
        if function_id not in self.functions:
            raise RegistryError(
                "get_function_info", f"Function {function_id} not found"
            )

        versions = self.functions[function_id]
        version_info = []
        for version, metadata in versions.items():
            version_info.append(
                {
                    "version": version,
                    "title": metadata.title,
                    "status": metadata.status.value,
                    "created_at": metadata.created_at.isoformat(),
                    "updated_at": metadata.updated_at.isoformat(),
                    "author": metadata.author,
                    "description": metadata.description,
                    "tags": metadata.tags,
                    "policy_references": metadata.policy_references,
                    "compliance_requirements": metadata.compliance_requirements,
                    "content_hash": metadata.content_hash,
                }
            )

        return {
            "function_id": function_id,
            "versions": version_info,
            "total_versions": len(versions),
        }

    def delete_function(self, function_id: str, version: str) -> None:
        """Delete a function version"""
        try:
            if (
                function_id not in self.functions
                or version not in self.functions[function_id]
            ):
                raise RegistryError(
                    "delete_function", f"Function {function_id} v{version} not found"
                )

            del self.functions[function_id][version]

            # Remove function entirely if no versions left
            if not self.functions[function_id]:
                del self.functions[function_id]

        except Exception as e:
            raise RegistryError("delete_function", str(e))
