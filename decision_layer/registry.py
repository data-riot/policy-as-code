from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from .schemas import DecisionSchema, SchemaValidator

@dataclass
class DecisionFunction:
    """Represents a versioned decision function with metadata"""
    function_id: str
    version: str
    logic: Callable
    schema: DecisionSchema
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: datetime = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def full_id(self) -> str:
        """Get the full identifier including version"""
        return f"{self.function_id}.{self.version}"
    
    def get_hash(self) -> str:
        """Generate a content hash for the function"""
        # This is a simplified hash - in production you'd want to hash the actual logic
        content = f"{self.function_id}:{self.version}:{self.description}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

class DecisionRegistry:
    """Registry with schema support and versioning"""
    
    def __init__(self):
        self._functions: Dict[str, DecisionFunction] = {}
        self._latest_versions: Dict[str, str] = {}
    
    def register(self, 
                function_id: str, 
                version: str, 
                logic: Callable, 
                schema: DecisionSchema,
                description: Optional[str] = None,
                author: Optional[str] = None,
                tags: Optional[List[str]] = None,
                metadata: Optional[Dict[str, Any]] = None) -> DecisionFunction:
        """
        Register a decision function with schema validation
        """
        full_id = f"{function_id}.{version}"
        
        if full_id in self._functions:
            raise ValueError(f"Function {full_id} already registered")
        
        # Create the decision function
        decision_fn = DecisionFunction(
            function_id=function_id,
            version=version,
            logic=logic,
            schema=schema,
            description=description,
            author=author,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Store the function
        self._functions[full_id] = decision_fn
        
        # Update latest version if this is newer
        if function_id not in self._latest_versions or self._is_newer_version(version, self._latest_versions[function_id]):
            self._latest_versions[function_id] = version
        
        return decision_fn
    
    def get(self, function_id: str, version: Optional[str] = None) -> Optional[DecisionFunction]:
        """
        Get a decision function by ID and optional version.
        If no version specified, returns the latest version.
        """
        if version is None:
            version = self._latest_versions.get(function_id)
            if version is None:
                return None
        
        full_id = f"{function_id}.{version}"
        return self._functions.get(full_id)
    
    def get_latest(self, function_id: str) -> Optional[DecisionFunction]:
        """Get the latest version of a function"""
        latest_version = self._latest_versions.get(function_id)
        if latest_version is None:
            return None
        return self.get(function_id, latest_version)
    
    def list_functions(self) -> List[str]:
        """List all function IDs"""
        return list(self._latest_versions.keys())
    
    def list_versions(self, function_id: str) -> List[str]:
        """List all versions of a function"""
        versions = []
        for full_id in self._functions.keys():
            if full_id.startswith(f"{function_id}."):
                version = full_id.split(".", 1)[1]
                versions.append(version)
        return sorted(versions, key=lambda v: self._version_key(v))
    
    def get_schema(self, function_id: str, version: Optional[str] = None) -> Optional[DecisionSchema]:
        """Get the schema for a function"""
        func = self.get(function_id, version)
        return func.schema if func else None
    
    def validate_input(self, function_id: str, version: Optional[str] = None, input_data: Any = None) -> Dict[str, Any]:
        """Validate input against function schema"""
        func = self.get(function_id, version)
        if func is None:
            raise ValueError(f"Function {function_id} version {version} not found")
        
        validator = SchemaValidator(func.schema)
        return validator.validate_input(input_data)
    
    def validate_output(self, function_id: str, version: Optional[str] = None, output_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate output against function schema"""
        func = self.get(function_id, version)
        if func is None:
            raise ValueError(f"Function {function_id} version {version} not found")
        
        validator = SchemaValidator(func.schema)
        return validator.validate_output(output_data)
    
    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """Compare two version strings to determine which is newer"""
        return self._version_key(version1) > self._version_key(version2)
    
    def _version_key(self, version: str) -> tuple:
        """Convert version string to comparable tuple"""
        # Handle semantic versioning (v1.2.3) and simple versions (v3.2)
        if version.startswith('v'):
            version = version[1:]
        
        parts = version.split('.')
        # Convert to integers, handling non-numeric parts
        version_parts = []
        for part in parts:
            try:
                version_parts.append(int(part))
            except ValueError:
                version_parts.append(part)
        
        return tuple(version_parts)
    
    def search(self, tags: Optional[List[str]] = None, author: Optional[str] = None) -> List[DecisionFunction]:
        """Search functions by tags or author"""
        results = []
        
        for func in self._functions.values():
            if tags and not any(tag in func.tags for tag in tags):
                continue
            if author and func.author != author:
                continue
            results.append(func)
        
        return results
    
    def export_metadata(self) -> Dict[str, Any]:
        """Export registry metadata for backup or analysis"""
        metadata = {
            "functions": {},
            "latest_versions": self._latest_versions,
            "exported_at": datetime.utcnow().isoformat()
        }
        
        for full_id, func in self._functions.items():
            metadata["functions"][full_id] = {
                "function_id": func.function_id,
                "version": func.version,
                "description": func.description,
                "author": func.author,
                "created_at": func.created_at.isoformat(),
                "tags": func.tags,
                "metadata": func.metadata,
                "hash": func.get_hash()
            }
        
        return metadata