"""
Core data structures for Policy as Code Platform
Separated to avoid circular imports
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Callable


@dataclass(frozen=True)
class DecisionContext:
    """Immutable decision execution context"""

    function_id: str
    version: str
    input_hash: str
    timestamp: datetime
    trace_id: str


@dataclass
class DecisionResult:
    """Result of a decision execution"""

    trace_id: str
    function_id: str
    version: str
    result: Dict[str, Any]
    execution_time_ms: int
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


@dataclass
class DecisionInput:
    """Input data for decision execution"""

    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DecisionOutput:
    """Output data from decision execution"""

    result: Dict[str, Any]
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Type alias for decision functions
DecisionFunction = Callable[[DecisionInput], DecisionOutput]
