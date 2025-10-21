"""
Point-in-Time Feature Store
Production-grade feature lookups with replay consistency and temporal integrity
"""

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from .errors import DecisionLayerError
from .time_semantics import DeterministicTimestamp, TimeSource


class FeatureType(str, Enum):
    """Types of features"""
    
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    TEXT = "text"
    EMBEDDING = "embedding"
    JSON = "json"


class FeatureSource(str, Enum):
    """Sources of features"""
    
    DATABASE = "database"
    API = "api"
    CACHE = "cache"
    COMPUTED = "computed"
    EXTERNAL = "external"


@dataclass(frozen=True)
class FeatureDefinition:
    """Definition of a feature"""
    
    name: str
    feature_type: FeatureType
    source: FeatureSource
    description: str
    version: str
    ttl_seconds: Optional[int] = None
    required: bool = True
    default_value: Any = None
    validation_schema: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "feature_type": self.feature_type.value,
            "source": self.source.value,
            "description": self.description,
            "version": self.version,
            "ttl_seconds": self.ttl_seconds,
            "required": self.required,
            "default_value": self.default_value,
            "validation_schema": self.validation_schema,
        }


@dataclass(frozen=True)
class FeatureValue:
    """A feature value with metadata"""
    
    feature_name: str
    entity_id: str
    value: Any
    feature_type: FeatureType
    timestamp: datetime
    feature_version: str
    source: FeatureSource
    ttl_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self, current_time: datetime) -> bool:
        """Check if feature value is expired"""
        if self.ttl_seconds is None:
            return False
        
        age = (current_time - self.timestamp).total_seconds()
        return age > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "feature_name": self.feature_name,
            "entity_id": self.entity_id,
            "value": self.value,
            "feature_type": self.feature_type.value,
            "timestamp": self.timestamp.isoformat(),
            "feature_version": self.feature_version,
            "source": self.source.value,
            "ttl_seconds": self.ttl_seconds,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class FeatureLookupRequest:
    """Request for feature lookup"""
    
    feature_name: str
    entity_id: str
    lookup_time: datetime
    feature_version: Optional[str] = None
    fallback_to_latest: bool = True
    max_age_seconds: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "feature_name": self.feature_name,
            "entity_id": self.entity_id,
            "lookup_time": self.lookup_time.isoformat(),
            "feature_version": self.feature_version,
            "fallback_to_latest": self.fallback_to_latest,
            "max_age_seconds": self.max_age_seconds,
        }


@dataclass(frozen=True)
class FeatureLookupResult:
    """Result of feature lookup"""
    
    request: FeatureLookupRequest
    value: Optional[FeatureValue]
    lookup_timestamp: datetime
    cache_hit: bool = False
    fallback_used: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "request": self.request.to_dict(),
            "value": self.value.to_dict() if self.value else None,
            "lookup_timestamp": self.lookup_timestamp.isoformat(),
            "cache_hit": self.cache_hit,
            "fallback_used": self.fallback_used,
            "error": self.error,
        }


class FeatureStoreError(DecisionLayerError):
    """Feature store specific errors"""
    
    def __init__(self, error_type: str, message: str):
        super().__init__(f"Feature store error ({error_type}): {message}")
        self.error_type = error_type


class FeatureStoreBackend:
    """Abstract backend for feature store"""
    
    async def get_feature(
        self, 
        feature_name: str, 
        entity_id: str, 
        lookup_time: datetime,
        feature_version: Optional[str] = None
    ) -> Optional[FeatureValue]:
        """Get feature value at specific time"""
        raise NotImplementedError
    
    async def put_feature(self, feature_value: FeatureValue) -> None:
        """Store feature value"""
        raise NotImplementedError
    
    async def list_features(self, entity_id: str) -> List[FeatureValue]:
        """List all features for an entity"""
        raise NotImplementedError
    
    async def delete_feature(self, feature_name: str, entity_id: str) -> None:
        """Delete feature value"""
        raise NotImplementedError


class InMemoryFeatureStore(FeatureStoreBackend):
    """In-memory feature store for testing"""
    
    def __init__(self):
        self.features: Dict[str, List[FeatureValue]] = {}  # entity_id -> features
        self.definitions: Dict[str, FeatureDefinition] = {}
    
    async def get_feature(
        self, 
        feature_name: str, 
        entity_id: str, 
        lookup_time: datetime,
        feature_version: Optional[str] = None
    ) -> Optional[FeatureValue]:
        """Get feature value at specific time"""
        entity_features = self.features.get(entity_id, [])
        
        # Filter by feature name
        matching_features = [f for f in entity_features if f.feature_name == feature_name]
        
        # Filter by version if specified
        if feature_version:
            matching_features = [f for f in matching_features if f.feature_version == feature_version]
        
        # Find the most recent feature before or at lookup_time
        valid_features = [f for f in matching_features if f.timestamp <= lookup_time]
        
        if not valid_features:
            return None
        
        # Sort by timestamp descending and return the most recent
        valid_features.sort(key=lambda f: f.timestamp, reverse=True)
        return valid_features[0]
    
    async def put_feature(self, feature_value: FeatureValue) -> None:
        """Store feature value"""
        entity_id = feature_value.entity_id
        
        if entity_id not in self.features:
            self.features[entity_id] = []
        
        # Remove existing feature with same name and version
        self.features[entity_id] = [
            f for f in self.features[entity_id] 
            if not (f.feature_name == feature_value.feature_name and f.feature_version == feature_value.feature_version)
        ]
        
        # Add new feature
        self.features[entity_id].append(feature_value)
    
    async def list_features(self, entity_id: str) -> List[FeatureValue]:
        """List all features for an entity"""
        return self.features.get(entity_id, [])
    
    async def delete_feature(self, feature_name: str, entity_id: str) -> None:
        """Delete feature value"""
        if entity_id in self.features:
            self.features[entity_id] = [
                f for f in self.features[entity_id] 
                if f.feature_name != feature_name
            ]
    
    def register_feature_definition(self, definition: FeatureDefinition) -> None:
        """Register a feature definition"""
        self.definitions[definition.name] = definition


class PostgreSQLFeatureStore(FeatureStoreBackend):
    """PostgreSQL-based feature store"""
    
    def __init__(self, connection_string: str, table_name: str = "feature_store"):
        self.connection_string = connection_string
        self.table_name = table_name
        self.pool = None
    
    async def initialize(self) -> None:
        """Initialize the database connection pool"""
        import asyncpg
        self.pool = await asyncpg.create_pool(self.connection_string)
        
        async with self.pool.acquire() as conn:
            await self._create_table(conn)
    
    async def _create_table(self, conn) -> None:
        """Create the feature store table"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            feature_name VARCHAR(255) NOT NULL,
            entity_id VARCHAR(255) NOT NULL,
            value JSONB NOT NULL,
            feature_type VARCHAR(50) NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            feature_version VARCHAR(50) NOT NULL,
            source VARCHAR(50) NOT NULL,
            ttl_seconds INTEGER,
            metadata JSONB DEFAULT '{{}}',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (feature_name, entity_id, feature_version, timestamp)
        );
        
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_entity_time 
        ON {self.table_name}(entity_id, timestamp DESC);
        
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_feature_time 
        ON {self.table_name}(feature_name, timestamp DESC);
        
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_lookup 
        ON {self.table_name}(feature_name, entity_id, timestamp DESC);
        """
        
        await conn.execute(create_table_sql)
    
    async def get_feature(
        self, 
        feature_name: str, 
        entity_id: str, 
        lookup_time: datetime,
        feature_version: Optional[str] = None
    ) -> Optional[FeatureValue]:
        """Get feature value at specific time"""
        if not self.pool:
            raise FeatureStoreError("not_initialized", "Feature store not initialized")
        
        async with self.pool.acquire() as conn:
            if feature_version:
                query_sql = f"""
                SELECT * FROM {self.table_name} 
                WHERE feature_name = $1 AND entity_id = $2 AND timestamp <= $3 AND feature_version = $4
                ORDER BY timestamp DESC 
                LIMIT 1
                """
                result = await conn.fetchrow(query_sql, feature_name, entity_id, lookup_time, feature_version)
            else:
                query_sql = f"""
                SELECT * FROM {self.table_name} 
                WHERE feature_name = $1 AND entity_id = $2 AND timestamp <= $3
                ORDER BY timestamp DESC 
                LIMIT 1
                """
                result = await conn.fetchrow(query_sql, feature_name, entity_id, lookup_time)
            
            if not result:
                return None
            
            return FeatureValue(
                feature_name=result['feature_name'],
                entity_id=result['entity_id'],
                value=result['value'],
                feature_type=FeatureType(result['feature_type']),
                timestamp=result['timestamp'],
                feature_version=result['feature_version'],
                source=FeatureSource(result['source']),
                ttl_seconds=result['ttl_seconds'],
                metadata=result['metadata'],
            )
    
    async def put_feature(self, feature_value: FeatureValue) -> None:
        """Store feature value"""
        if not self.pool:
            raise FeatureStoreError("not_initialized", "Feature store not initialized")
        
        async with self.pool.acquire() as conn:
            insert_sql = f"""
            INSERT INTO {self.table_name} (
                feature_name, entity_id, value, feature_type, timestamp, 
                feature_version, source, ttl_seconds, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (feature_name, entity_id, feature_version, timestamp) 
            DO UPDATE SET 
                value = EXCLUDED.value,
                feature_type = EXCLUDED.feature_type,
                source = EXCLUDED.source,
                ttl_seconds = EXCLUDED.ttl_seconds,
                metadata = EXCLUDED.metadata
            """
            
            await conn.execute(
                insert_sql,
                feature_value.feature_name,
                feature_value.entity_id,
                json.dumps(feature_value.value),
                feature_value.feature_type.value,
                feature_value.timestamp,
                feature_value.feature_version,
                feature_value.source.value,
                feature_value.ttl_seconds,
                json.dumps(feature_value.metadata),
            )
    
    async def list_features(self, entity_id: str) -> List[FeatureValue]:
        """List all features for an entity"""
        if not self.pool:
            raise FeatureStoreError("not_initialized", "Feature store not initialized")
        
        async with self.pool.acquire() as conn:
            query_sql = f"""
            SELECT * FROM {self.table_name} 
            WHERE entity_id = $1 
            ORDER BY timestamp DESC
            """
            
            results = await conn.fetch(query_sql, entity_id)
            
            return [
                FeatureValue(
                    feature_name=row['feature_name'],
                    entity_id=row['entity_id'],
                    value=row['value'],
                    feature_type=FeatureType(row['feature_type']),
                    timestamp=row['timestamp'],
                    feature_version=row['feature_version'],
                    source=FeatureSource(row['source']),
                    ttl_seconds=row['ttl_seconds'],
                    metadata=row['metadata'],
                )
                for row in results
            ]
    
    async def delete_feature(self, feature_name: str, entity_id: str) -> None:
        """Delete feature value"""
        if not self.pool:
            raise FeatureStoreError("not_initialized", "Feature store not initialized")
        
        async with self.pool.acquire() as conn:
            delete_sql = f"""
            DELETE FROM {self.table_name} 
            WHERE feature_name = $1 AND entity_id = $2
            """
            
            await conn.execute(delete_sql, feature_name, entity_id)
    
    async def close(self) -> None:
        """Close the database pool"""
        if self.pool:
            await self.pool.close()


class PointInTimeFeatureStore:
    """Production-grade point-in-time feature store"""
    
    def __init__(self, backend: FeatureStoreBackend):
        self.backend = backend
        self.cache: Dict[str, FeatureValue] = {}
        self.definitions: Dict[str, FeatureDefinition] = {}
        self.lookup_history: List[FeatureLookupResult] = []
    
    def register_feature_definition(self, definition: FeatureDefinition) -> None:
        """Register a feature definition"""
        self.definitions[definition.name] = definition
    
    async def lookup_feature(
        self, 
        request: FeatureLookupRequest,
        deterministic_time: DeterministicTimestamp
    ) -> FeatureLookupResult:
        """Lookup feature with point-in-time consistency"""
        
        # Check cache first
        cache_key = f"{request.feature_name}:{request.entity_id}:{request.lookup_time.isoformat()}"
        if cache_key in self.cache:
            cached_value = self.cache[cache_key]
            if not cached_value.is_expired(deterministic_time.normalized_utc):
                result = FeatureLookupResult(
                    request=request,
                    value=cached_value,
                    lookup_timestamp=deterministic_time.normalized_utc,
                    cache_hit=True,
                )
                self.lookup_history.append(result)
                return result
        
        # Lookup from backend
        try:
            feature_value = await self.backend.get_feature(
                request.feature_name,
                request.entity_id,
                request.lookup_time,
                request.feature_version
            )
            
            # Handle fallback to latest if no value found
            if not feature_value and request.fallback_to_latest:
                feature_value = await self.backend.get_feature(
                    request.feature_name,
                    request.entity_id,
                    deterministic_time.normalized_utc,  # Use current time
                    request.feature_version
                )
            
            # Validate feature value
            if feature_value:
                validation_error = self._validate_feature_value(feature_value, request)
                if validation_error:
                    result = FeatureLookupResult(
                        request=request,
                        value=None,
                        lookup_timestamp=deterministic_time.normalized_utc,
                        error=validation_error,
                    )
                else:
                    # Cache the result
                    self.cache[cache_key] = feature_value
                    
                    result = FeatureLookupResult(
                        request=request,
                        value=feature_value,
                        lookup_timestamp=deterministic_time.normalized_utc,
                        fallback_used=not feature_value.timestamp <= request.lookup_time,
                    )
            else:
                result = FeatureLookupResult(
                    request=request,
                    value=None,
                    lookup_timestamp=deterministic_time.normalized_utc,
                    error="Feature not found",
                )
            
        except Exception as e:
            result = FeatureLookupResult(
                request=request,
                value=None,
                lookup_timestamp=deterministic_time.normalized_utc,
                error=f"Lookup failed: {str(e)}",
            )
        
        self.lookup_history.append(result)
        return result
    
    async def lookup_multiple_features(
        self, 
        requests: List[FeatureLookupRequest],
        deterministic_time: DeterministicTimestamp
    ) -> List[FeatureLookupResult]:
        """Lookup multiple features in parallel"""
        tasks = [self.lookup_feature(req, deterministic_time) for req in requests]
        return await asyncio.gather(*tasks)
    
    def _validate_feature_value(self, feature_value: FeatureValue, request: FeatureLookupRequest) -> Optional[str]:
        """Validate feature value against definition"""
        definition = self.definitions.get(feature_value.feature_name)
        if not definition:
            return None  # No definition to validate against
        
        # Check if value is expired
        if feature_value.is_expired(request.lookup_time):
            return "Feature value expired"
        
        # Check max age if specified
        if request.max_age_seconds:
            age = (request.lookup_time - feature_value.timestamp).total_seconds()
            if age > request.max_age_seconds:
                return f"Feature value too old: {age}s > {request.max_age_seconds}s"
        
        # Type validation
        if not self._validate_feature_type(feature_value.value, definition.feature_type):
            return f"Feature value type mismatch: expected {definition.feature_type.value}"
        
        return None
    
    def _validate_feature_type(self, value: Any, expected_type: FeatureType) -> bool:
        """Validate feature value type"""
        if expected_type == FeatureType.NUMERICAL:
            return isinstance(value, (int, float))
        elif expected_type == FeatureType.CATEGORICAL:
            return isinstance(value, str)
        elif expected_type == FeatureType.BOOLEAN:
            return isinstance(value, bool)
        elif expected_type == FeatureType.TEXT:
            return isinstance(value, str)
        elif expected_type == FeatureType.JSON:
            return isinstance(value, (dict, list))
        else:
            return True  # Unknown type, allow any value
    
    async def store_feature(self, feature_value: FeatureValue) -> None:
        """Store a feature value"""
        await self.backend.put_feature(feature_value)
        
        # Update cache
        cache_key = f"{feature_value.feature_name}:{feature_value.entity_id}:{feature_value.timestamp.isoformat()}"
        self.cache[cache_key] = feature_value
    
    def get_lookup_history(self) -> List[FeatureLookupResult]:
        """Get lookup history for audit"""
        return self.lookup_history.copy()
    
    def clear_cache(self) -> None:
        """Clear feature cache"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.cache),
            "lookup_history_size": len(self.lookup_history),
            "cache_hit_rate": len([r for r in self.lookup_history if r.cache_hit]) / max(len(self.lookup_history), 1),
        }


def create_in_memory_feature_store() -> PointInTimeFeatureStore:
    """Create an in-memory feature store for testing"""
    backend = InMemoryFeatureStore()
    return PointInTimeFeatureStore(backend)


def create_postgresql_feature_store(connection_string: str) -> PointInTimeFeatureStore:
    """Create a PostgreSQL-based feature store"""
    backend = PostgreSQLFeatureStore(connection_string)
    return PointInTimeFeatureStore(backend)
