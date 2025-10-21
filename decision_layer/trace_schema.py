"""
Formal Trace Schema with Versioning
Production-grade trace schema with required fields, types, and versioning
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from .errors import DecisionLayerError


class TraceSchemaVersion(str, Enum):
    """Trace schema versions"""

    V1_0 = "1.0"  # Initial production schema
    V1_1 = "1.1"  # Added feature store lookups
    V1_2 = "1.2"  # Added PII handling
    CURRENT = V1_2


class TraceStatus(str, Enum):
    """Trace execution status"""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    VALIDATION_ERROR = "validation_error"
    EXTERNAL_ERROR = "external_error"


class DeterministicTimeSource(str, Enum):
    """Sources of deterministic time"""

    FIXED = "fixed"  # Fixed timestamp for testing
    UTC_NORMALIZED = "utc_normalized"  # UTC with clock skew handling
    FEATURE_STORE = "feature_store"  # Time from feature store
    EXTERNAL_API = "external_api"  # Time from external API


@dataclass(frozen=True)
class DeterministicTime:
    """Deterministic time with source tracking"""

    timestamp: datetime
    source: DeterministicTimeSource
    timezone: str = "UTC"
    clock_skew_ms: Optional[int] = None
    normalized_timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Normalize timestamp to UTC"""
        if self.normalized_timestamp is None:
            if self.timestamp.tzinfo is None:
                # Assume UTC if no timezone info
                normalized = self.timestamp.replace(tzinfo=timezone.utc)
            else:
                normalized = self.timestamp.astimezone(timezone.utc)
            object.__setattr__(self, "normalized_timestamp", normalized)


@dataclass(frozen=True)
class FeatureLookup:
    """Point-in-time feature lookup"""

    feature_name: str
    entity_id: str
    lookup_time: datetime
    value: Any
    feature_version: str
    ttl_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "feature_name": self.feature_name,
            "entity_id": self.entity_id,
            "lookup_time": self.lookup_time.isoformat(),
            "value": self.value,
            "feature_version": self.feature_version,
            "ttl_seconds": self.ttl_seconds,
        }


@dataclass(frozen=True)
class TraceMetadata:
    """Immutable trace metadata"""

    trace_id: UUID
    schema_version: TraceSchemaVersion
    function_id: str
    function_version: str
    execution_id: str
    parent_trace_id: Optional[UUID] = None
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trace_id": str(self.trace_id),
            "schema_version": self.schema_version.value,
            "function_id": self.function_id,
            "function_version": self.function_version,
            "execution_id": self.execution_id,
            "parent_trace_id": (
                str(self.parent_trace_id) if self.parent_trace_id else None
            ),
            "correlation_id": self.correlation_id,
        }


@dataclass(frozen=True)
class TraceInput:
    """Structured trace input"""

    raw_input: Dict[str, Any]
    validated_input: Dict[str, Any]
    input_hash: str
    validation_errors: List[str] = field(default_factory=list)
    pii_fields: List[str] = field(default_factory=list)
    redacted_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "raw_input": self.raw_input,
            "validated_input": self.validated_input,
            "input_hash": self.input_hash,
            "validation_errors": self.validation_errors,
            "pii_fields": self.pii_fields,
            "redacted_fields": self.redacted_fields,
        }


@dataclass(frozen=True)
class TraceOutput:
    """Structured trace output"""

    result: Dict[str, Any]
    output_hash: str
    confidence_score: Optional[float] = None
    decision_path: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    memory_usage_mb: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "result": self.result,
            "output_hash": self.output_hash,
            "confidence_score": self.confidence_score,
            "decision_path": self.decision_path,
            "execution_time_ms": self.execution_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
        }


@dataclass(frozen=True)
class TraceContext:
    """Execution context for trace"""

    deterministic_time: DeterministicTime
    feature_lookups: List[FeatureLookup] = field(default_factory=list)
    external_calls: List[Dict[str, Any]] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    client_info: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "deterministic_time": {
                "timestamp": self.deterministic_time.timestamp.isoformat(),
                "source": self.deterministic_time.source.value,
                "timezone": self.deterministic_time.timezone,
                "clock_skew_ms": self.deterministic_time.clock_skew_ms,
                "normalized_timestamp": self.deterministic_time.normalized_timestamp.isoformat(),
            },
            "feature_lookups": [lookup.to_dict() for lookup in self.feature_lookups],
            "external_calls": self.external_calls,
            "environment_variables": self.environment_variables,
            "client_info": self.client_info,
        }


@dataclass(frozen=True)
class ProductionTrace:
    """Production-grade trace with formal schema"""

    # Core metadata
    metadata: TraceMetadata

    # Execution data
    input_data: TraceInput
    output_data: TraceOutput
    context: TraceContext

    # Status and timing
    status: TraceStatus
    started_at: datetime
    completed_at: datetime

    # Governance
    legal_references: List[str] = field(default_factory=list)
    audit_hash: str = ""
    chain_hash: str = ""
    signer: str = "system"

    # Versioning
    trace_schema_version: TraceSchemaVersion = TraceSchemaVersion.CURRENT

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "metadata": self.metadata.to_dict(),
            "input_data": self.input_data.to_dict(),
            "output_data": self.output_data.to_dict(),
            "context": self.context.to_dict(),
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "legal_references": self.legal_references,
            "audit_hash": self.audit_hash,
            "chain_hash": self.chain_hash,
            "signer": self.signer,
            "trace_schema_version": self.trace_schema_version.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductionTrace":
        """Create from dictionary"""
        # Parse metadata
        metadata = TraceMetadata(
            trace_id=UUID(data["metadata"]["trace_id"]),
            schema_version=TraceSchemaVersion(data["metadata"]["schema_version"]),
            function_id=data["metadata"]["function_id"],
            function_version=data["metadata"]["function_version"],
            execution_id=data["metadata"]["execution_id"],
            parent_trace_id=(
                UUID(data["metadata"]["parent_trace_id"])
                if data["metadata"].get("parent_trace_id")
                else None
            ),
            correlation_id=data["metadata"].get("correlation_id"),
        )

        # Parse input data
        input_data = TraceInput(
            raw_input=data["input_data"]["raw_input"],
            validated_input=data["input_data"]["validated_input"],
            input_hash=data["input_data"]["input_hash"],
            validation_errors=data["input_data"].get("validation_errors", []),
            pii_fields=data["input_data"].get("pii_fields", []),
            redacted_fields=data["input_data"].get("redacted_fields", []),
        )

        # Parse output data
        output_data = TraceOutput(
            result=data["output_data"]["result"],
            output_hash=data["output_data"]["output_hash"],
            confidence_score=data["output_data"].get("confidence_score"),
            decision_path=data["output_data"].get("decision_path", []),
            execution_time_ms=data["output_data"].get("execution_time_ms", 0.0),
            memory_usage_mb=data["output_data"].get("memory_usage_mb"),
        )

        # Parse context
        deterministic_time = DeterministicTime(
            timestamp=datetime.fromisoformat(
                data["context"]["deterministic_time"]["timestamp"]
            ),
            source=DeterministicTimeSource(
                data["context"]["deterministic_time"]["source"]
            ),
            timezone=data["context"]["deterministic_time"]["timezone"],
            clock_skew_ms=data["context"]["deterministic_time"].get("clock_skew_ms"),
            normalized_timestamp=datetime.fromisoformat(
                data["context"]["deterministic_time"]["normalized_timestamp"]
            ),
        )

        feature_lookups = [
            FeatureLookup(
                feature_name=lookup["feature_name"],
                entity_id=lookup["entity_id"],
                lookup_time=datetime.fromisoformat(lookup["lookup_time"]),
                value=lookup["value"],
                feature_version=lookup["feature_version"],
                ttl_seconds=lookup.get("ttl_seconds"),
            )
            for lookup in data["context"].get("feature_lookups", [])
        ]

        context = TraceContext(
            deterministic_time=deterministic_time,
            feature_lookups=feature_lookups,
            external_calls=data["context"].get("external_calls", []),
            environment_variables=data["context"].get("environment_variables", {}),
            client_info=data["context"].get("client_info"),
        )

        return cls(
            metadata=metadata,
            input_data=input_data,
            output_data=output_data,
            context=context,
            status=TraceStatus(data["status"]),
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]),
            legal_references=data.get("legal_references", []),
            audit_hash=data.get("audit_hash", ""),
            chain_hash=data.get("chain_hash", ""),
            signer=data.get("signer", "system"),
            trace_schema_version=TraceSchemaVersion(
                data.get("trace_schema_version", TraceSchemaVersion.CURRENT.value)
            ),
        )


class TraceSchemaValidator:
    """Validator for trace schema compliance"""

    def __init__(
        self, required_version: TraceSchemaVersion = TraceSchemaVersion.CURRENT
    ):
        self.required_version = required_version

    def validate_trace(self, trace: ProductionTrace) -> List[str]:
        """Validate trace against schema"""
        errors = []

        # Check schema version compatibility
        if trace.trace_schema_version != self.required_version:
            errors.append(
                f"Schema version mismatch: {trace.trace_schema_version} != {self.required_version}"
            )

        # Check required fields
        if not trace.metadata.trace_id:
            errors.append("Missing trace_id")

        if not trace.metadata.function_id:
            errors.append("Missing function_id")

        if not trace.metadata.function_version:
            errors.append("Missing function_version")

        if not trace.input_data.input_hash:
            errors.append("Missing input_hash")

        if not trace.output_data.output_hash:
            errors.append("Missing output_hash")

        # Check deterministic time
        if not trace.context.deterministic_time.normalized_timestamp:
            errors.append("Missing normalized timestamp")

        # Check execution timing
        if trace.completed_at <= trace.started_at:
            errors.append("Invalid execution timing: completed_at <= started_at")

        return errors

    def validate_schema_evolution(
        self, old_trace: ProductionTrace, new_trace: ProductionTrace
    ) -> List[str]:
        """Validate schema evolution compatibility"""
        errors = []

        # Check if schema evolution is backward compatible
        if (
            old_trace.trace_schema_version == TraceSchemaVersion.V1_0
            and new_trace.trace_schema_version == TraceSchemaVersion.V1_2
        ):
            # V1.2 should be backward compatible with V1.0
            pass
        elif (
            old_trace.trace_schema_version == TraceSchemaVersion.V1_1
            and new_trace.trace_schema_version == TraceSchemaVersion.V1_2
        ):
            # V1.2 should be backward compatible with V1.1
            pass
        else:
            errors.append(
                f"Incompatible schema evolution: {old_trace.trace_schema_version} -> {new_trace.trace_schema_version}"
            )

        return errors


# Schema evolution utilities
def migrate_trace_to_current_version(trace_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate trace data to current schema version"""
    current_version = trace_data.get(
        "trace_schema_version", TraceSchemaVersion.V1_0.value
    )

    if current_version == TraceSchemaVersion.V1_0.value:
        # Add feature lookups field
        if "context" not in trace_data:
            trace_data["context"] = {}
        if "feature_lookups" not in trace_data["context"]:
            trace_data["context"]["feature_lookups"] = []

        # Add PII handling fields
        if "input_data" not in trace_data:
            trace_data["input_data"] = {}
        if "pii_fields" not in trace_data["input_data"]:
            trace_data["input_data"]["pii_fields"] = []
        if "redacted_fields" not in trace_data["input_data"]:
            trace_data["input_data"]["redacted_fields"] = []

        trace_data["trace_schema_version"] = TraceSchemaVersion.V1_2.value

    elif current_version == TraceSchemaVersion.V1_1.value:
        # Add PII handling fields
        if "input_data" not in trace_data:
            trace_data["input_data"] = {}
        if "pii_fields" not in trace_data["input_data"]:
            trace_data["input_data"]["pii_fields"] = []
        if "redacted_fields" not in trace_data["input_data"]:
            trace_data["input_data"]["redacted_fields"] = []

        trace_data["trace_schema_version"] = TraceSchemaVersion.V1_2.value

    return trace_data


# BigQuery DDL for decision_logs table
BIGQUERY_DDL = """
CREATE TABLE IF NOT EXISTS `project.dataset.decision_logs` (
  -- Core identifiers
  trace_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  function_id STRING NOT NULL,
  function_version STRING NOT NULL,
  execution_id STRING NOT NULL,
  parent_trace_id STRING,
  correlation_id STRING,
  
  -- Execution timing
  started_at TIMESTAMP NOT NULL,
  completed_at TIMESTAMP NOT NULL,
  execution_time_ms FLOAT64 NOT NULL,
  
  -- Status and results
  status STRING NOT NULL,
  confidence_score FLOAT64,
  memory_usage_mb FLOAT64,
  
  -- Input/Output hashes for integrity
  input_hash STRING NOT NULL,
  output_hash STRING NOT NULL,
  
  -- Deterministic time tracking
  deterministic_timestamp TIMESTAMP NOT NULL,
  time_source STRING NOT NULL,
  clock_skew_ms INT64,
  
  -- Feature lookups (repeated)
  feature_lookups ARRAY<STRUCT<
    feature_name STRING,
    entity_id STRING,
    lookup_time TIMESTAMP,
    feature_version STRING,
    ttl_seconds INT64
  >>,
  
  -- Legal and governance
  legal_references ARRAY<STRING>,
  audit_hash STRING,
  chain_hash STRING,
  signer STRING,
  
  -- Raw data (JSON)
  input_data JSON,
  output_data JSON,
  context_data JSON,
  
  -- Partitioning and clustering
  _partition_date DATE GENERATED ALWAYS AS (DATE(started_at)),
  _inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY _partition_date
CLUSTER BY function_id, function_version, status
OPTIONS (
  description = "Production decision traces with governance features",
  partition_expiration_days = 2555,  -- 7 years retention
  require_partition_filter = true
);
"""

# Canonical queries for operational monitoring
CANONICAL_QUERIES = {
    "daily_decision_summary": """
SELECT 
  function_id,
  function_version,
  status,
  COUNT(*) as decision_count,
  AVG(execution_time_ms) as avg_execution_time_ms,
  AVG(confidence_score) as avg_confidence_score,
  DATE(started_at) as decision_date
FROM `project.dataset.decision_logs`
WHERE _partition_date = CURRENT_DATE()
GROUP BY function_id, function_version, status, decision_date
ORDER BY decision_date DESC, decision_count DESC
""",
    "error_rate_by_function": """
SELECT 
  function_id,
  function_version,
  COUNT(*) as total_decisions,
  SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END) as error_count,
  SAFE_DIVIDE(SUM(CASE WHEN status != 'success' THEN 1 ELSE 0 END), COUNT(*)) as error_rate
FROM `project.dataset.decision_logs`
WHERE _partition_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY function_id, function_version
HAVING total_decisions > 100  -- Only functions with significant volume
ORDER BY error_rate DESC
""",
    "feature_lookup_performance": """
SELECT 
  feature_name,
  COUNT(*) as lookup_count,
  AVG(TIMESTAMP_DIFF(lookup_time, deterministic_timestamp, MILLISECOND)) as avg_lookup_latency_ms,
  COUNT(DISTINCT entity_id) as unique_entities
FROM `project.dataset.decision_logs`,
UNNEST(feature_lookups) as lookup
WHERE _partition_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY feature_name
ORDER BY lookup_count DESC
""",
}
