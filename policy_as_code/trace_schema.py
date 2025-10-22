"""
Trace Schema Module

This module defines the schema and data structures for trace records,
providing type definitions and validation for trace data.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class TraceSchemaVersion(str, Enum):
    """Trace schema version enumeration"""

    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"


class TraceStatus(str, Enum):
    """Trace status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TraceType(str, Enum):
    """Trace type enumeration"""

    DECISION = "decision"
    AUDIT = "audit"
    WORKFLOW = "workflow"
    API_CALL = "api_call"
    SYSTEM_EVENT = "system_event"


@dataclass
class TraceMetadata:
    """Metadata for trace records"""

    trace_id: str
    parent_trace_id: Optional[str] = None
    function_id: Optional[str] = None
    version: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


@dataclass
class TraceEvent:
    """A single event within a trace"""

    event_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    duration_ms: Optional[int] = None
    status: Optional[TraceStatus] = None
    error_message: Optional[str] = None


@dataclass
class TraceRecord:
    """Complete trace record"""

    trace_id: str
    trace_type: TraceType
    status: TraceStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    metadata: Optional[TraceMetadata] = None
    events: Optional[List[TraceEvent]] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_data: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, float]] = None


@dataclass
class TraceQuery:
    """Query parameters for trace retrieval"""

    trace_id: Optional[str] = None
    function_id: Optional[str] = None
    user_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    trace_type: Optional[TraceType] = None
    status: Optional[TraceStatus] = None
    limit: int = 100
    offset: int = 0


@dataclass
class TraceSummary:
    """Summary statistics for traces"""

    total_traces: int
    completed_traces: int
    failed_traces: int
    average_duration_ms: float
    success_rate: float
    time_range: Dict[str, datetime]


class TraceSchemaValidator:
    """Validates trace data against schema"""

    @staticmethod
    def validate_trace_record(trace: TraceRecord) -> bool:
        """Validate a trace record"""
        if not trace.trace_id:
            return False
        if not trace.trace_type:
            return False
        if not trace.status:
            return False
        if not trace.start_time:
            return False
        return True

    @staticmethod
    def validate_trace_event(event: TraceEvent) -> bool:
        """Validate a trace event"""
        if not event.event_id:
            return False
        if not event.event_type:
            return False
        if not event.timestamp:
            return False
        return True


# Export main classes and functions
__all__ = [
    "TraceSchemaVersion",
    "TraceStatus",
    "TraceType",
    "TraceMetadata",
    "TraceEvent",
    "TraceRecord",
    "TraceQuery",
    "TraceSummary",
    "TraceSchemaValidator",
]
