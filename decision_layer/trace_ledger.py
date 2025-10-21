"""
Immutable Trace Ledger Interface
Production-grade append-only ledger with hash chaining and signer identity
"""

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .errors import DecisionLayerError


@dataclass(frozen=True)
class TraceRecord:
    """Immutable trace record with hash chaining"""
    
    trace_id: str
    df_id: str
    version: str
    df_hash: str
    timestamp: datetime
    caller: str
    status: str
    input_json: Dict[str, Any]
    output_json: Dict[str, Any]
    prev_hash: Optional[str]
    chain_hash: str
    signer: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "trace_id": self.trace_id,
            "df_id": self.df_id,
            "version": self.version,
            "df_hash": self.df_hash,
            "timestamp": self.timestamp.isoformat(),
            "caller": self.caller,
            "status": self.status,
            "input_json": self.input_json,
            "output_json": self.output_json,
            "prev_hash": self.prev_hash,
            "chain_hash": self.chain_hash,
            "signer": self.signer,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceRecord":
        """Create from dictionary"""
        return cls(
            trace_id=data["trace_id"],
            df_id=data["df_id"],
            version=data["version"],
            df_hash=data["df_hash"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            caller=data["caller"],
            status=data["status"],
            input_json=data["input_json"],
            output_json=data["output_json"],
            prev_hash=data.get("prev_hash"),
            chain_hash=data["chain_hash"],
            signer=data["signer"],
        )


class TraceWriter(ABC):
    """Abstract interface for trace writing"""
    
    @abstractmethod
    async def write_trace(self, record: TraceRecord) -> None:
        """Write a trace record to the ledger"""
        pass
    
    @abstractmethod
    async def get_latest_hash(self) -> Optional[str]:
        """Get the hash of the latest record for chaining"""
        pass
    
    @abstractmethod
    async def verify_chain(self) -> bool:
        """Verify the integrity of the hash chain"""
        pass


class TraceReader(ABC):
    """Abstract interface for trace reading"""
    
    @abstractmethod
    async def get_trace(self, trace_id: str) -> Optional[TraceRecord]:
        """Get a specific trace by ID"""
        pass
    
    @abstractmethod
    async def get_traces_by_function(
        self, df_id: str, version: Optional[str] = None, limit: int = 100
    ) -> List[TraceRecord]:
        """Get traces for a specific function"""
        pass
    
    @abstractmethod
    async def get_traces_by_timeframe(
        self, start_time: datetime, end_time: datetime, limit: int = 1000
    ) -> List[TraceRecord]:
        """Get traces within a time range"""
        pass


class TraceLedger(TraceWriter, TraceReader):
    """Main trace ledger interface"""
    
    def __init__(self, writer: TraceWriter, reader: TraceReader):
        self.writer = writer
        self.reader = reader
    
    async def write_trace(self, record: TraceRecord) -> None:
        """Write trace using the writer backend"""
        await self.writer.write_trace(record)
    
    async def get_latest_hash(self) -> Optional[str]:
        """Get latest hash from writer"""
        return await self.writer.get_latest_hash()
    
    async def verify_chain(self) -> bool:
        """Verify chain integrity"""
        return await self.writer.verify_chain()
    
    async def get_trace(self, trace_id: str) -> Optional[TraceRecord]:
        """Get trace using reader backend"""
        return await self.reader.get_trace(trace_id)
    
    async def get_traces_by_function(
        self, df_id: str, version: Optional[str] = None, limit: int = 100
    ) -> List[TraceRecord]:
        """Get traces by function using reader backend"""
        return await self.reader.get_traces_by_function(df_id, version, limit)
    
    async def get_traces_by_timeframe(
        self, start_time: datetime, end_time: datetime, limit: int = 1000
    ) -> List[TraceRecord]:
        """Get traces by timeframe using reader backend"""
        return await self.reader.get_traces_by_timeframe(start_time, end_time, limit)


def compute_chain_hash(record: TraceRecord, prev_hash: Optional[str]) -> str:
    """Compute the chain hash for a record"""
    # Create hash of current record
    record_data = json.dumps({
        "trace_id": record.trace_id,
        "df_id": record.df_id,
        "version": record.version,
        "df_hash": record.df_hash,
        "timestamp": record.timestamp.isoformat(),
        "caller": record.caller,
        "status": record.status,
        "input_hash": hashlib.sha256(json.dumps(record.input_json, sort_keys=True).encode()).hexdigest(),
        "output_hash": hashlib.sha256(json.dumps(record.output_json, sort_keys=True).encode()).hexdigest(),
        "signer": record.signer,
    }, sort_keys=True, separators=(",", ":"))
    
    current_hash = hashlib.sha256(record_data.encode()).hexdigest()
    
    # Chain with previous hash
    if prev_hash:
        chain_input = f"{prev_hash}{current_hash}"
    else:
        chain_input = current_hash
    
    return hashlib.sha256(chain_input.encode()).hexdigest()


def create_trace_record(
    trace_id: str,
    df_id: str,
    version: str,
    df_hash: str,
    timestamp: datetime,
    caller: str,
    status: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    signer: str,
    prev_hash: Optional[str] = None,
) -> TraceRecord:
    """Create a trace record with computed chain hash"""
    
    record = TraceRecord(
        trace_id=trace_id,
        df_id=df_id,
        version=version,
        df_hash=df_hash,
        timestamp=timestamp,
        caller=caller,
        status=status,
        input_json=input_data,
        output_json=output_data,
        prev_hash=prev_hash,
        chain_hash="",  # Will be computed
        signer=signer,
    )
    
    # Compute chain hash
    chain_hash = compute_chain_hash(record, prev_hash)
    
    # Return new record with computed hash
    return TraceRecord(
        trace_id=record.trace_id,
        df_id=record.df_id,
        version=record.version,
        df_hash=record.df_hash,
        timestamp=record.timestamp,
        caller=record.caller,
        status=record.status,
        input_json=record.input_json,
        output_json=record.output_json,
        prev_hash=record.prev_hash,
        chain_hash=chain_hash,
        signer=record.signer,
    )


class LedgerError(DecisionLayerError):
    """Ledger-specific errors"""
    
    def __init__(self, operation: str, message: str):
        super().__init__(f"Ledger {operation} failed: {message}")
        self.operation = operation
