"""
Immutable Trace Ledger with Cryptographic Hash Chaining
Provides blockchain-like immutability for decision traces
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from policy_as_code.core.types import DecisionContext, DecisionResult


class TraceEntryType(Enum):
    """Types of trace entries"""

    DECISION_EXECUTION = "decision_execution"
    FUNCTION_REGISTRATION = "function_registration"
    POLICY_UPDATE = "policy_update"
    SECURITY_EVENT = "security_event"
    SYSTEM_EVENT = "system_event"


@dataclass(frozen=True)
class TraceEntry:
    """Immutable trace entry"""

    entry_id: str
    entry_type: TraceEntryType
    timestamp: datetime
    data: Dict[str, Any]
    previous_hash: Optional[str]
    hash: str
    signature: Optional[str] = None


class ImmutableTraceLedger:
    """Immutable trace ledger with cryptographic hash chaining"""

    def __init__(self, storage_backend=None):
        self.storage_backend = storage_backend
        self._entries: List[TraceEntry] = []
        self._last_hash: Optional[str] = None
        self._genesis_hash = self._create_genesis_hash()

    def _create_genesis_hash(self) -> str:
        """Create the genesis hash for the ledger"""
        genesis_data = {
            "type": "genesis",
            "timestamp": datetime.now().isoformat(),
            "description": "Policy as Code Trace Ledger Genesis Block",
        }
        return self._hash_data(genesis_data)

    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Create SHA-256 hash of data"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _create_entry_hash(
        self, entry_data: Dict[str, Any], previous_hash: Optional[str]
    ) -> str:
        """Create hash for a trace entry"""
        hash_data = {
            "entry_data": entry_data,
            "previous_hash": previous_hash,
            "timestamp": entry_data.get("timestamp"),
        }
        return self._hash_data(hash_data)

    async def append_decision_execution(
        self,
        context: DecisionContext,
        result: DecisionResult,
        signature: Optional[str] = None,
    ) -> str:
        """Append a decision execution to the ledger"""
        entry_data = {
            "entry_type": TraceEntryType.DECISION_EXECUTION.value,
            "timestamp": datetime.now().isoformat(),
            "function_id": context.function_id,
            "version": context.version,
            "trace_id": context.trace_id,
            "input_hash": context.input_hash,
            "execution_time_ms": result.execution_time_ms,
            "success": result.success,
            "error_message": result.error_message,
            "result_summary": self._create_result_summary(result.result),
        }

        return await self._append_entry(entry_data, signature)

    async def append_function_registration(
        self, function_id: str, version: str, signature: Optional[str] = None
    ) -> str:
        """Append a function registration to the ledger"""
        entry_data = {
            "entry_type": TraceEntryType.FUNCTION_REGISTRATION.value,
            "timestamp": datetime.now().isoformat(),
            "function_id": function_id,
            "version": version,
            "action": "registered",
        }

        return await self._append_entry(entry_data, signature)

    async def append_policy_update(
        self,
        function_id: str,
        old_version: str,
        new_version: str,
        signature: Optional[str] = None,
    ) -> str:
        """Append a policy update to the ledger"""
        entry_data = {
            "entry_type": TraceEntryType.POLICY_UPDATE.value,
            "timestamp": datetime.now().isoformat(),
            "function_id": function_id,
            "old_version": old_version,
            "new_version": new_version,
            "action": "updated",
        }

        return await self._append_entry(entry_data, signature)

    async def append_security_event(
        self, event_type: str, details: Dict[str, Any], signature: Optional[str] = None
    ) -> str:
        """Append a security event to the ledger"""
        entry_data = {
            "entry_type": TraceEntryType.SECURITY_EVENT.value,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
        }

        return await self._append_entry(entry_data, signature)

    async def _append_entry(
        self, entry_data: Dict[str, Any], signature: Optional[str] = None
    ) -> str:
        """Append an entry to the ledger"""
        entry_id = f"entry_{len(self._entries)}_{int(datetime.now().timestamp())}"

        # Create hash with previous hash
        entry_hash = self._create_entry_hash(entry_data, self._last_hash)

        # Create trace entry
        entry = TraceEntry(
            entry_id=entry_id,
            entry_type=TraceEntryType(entry_data["entry_type"]),
            timestamp=datetime.fromisoformat(entry_data["timestamp"]),
            data=entry_data,
            previous_hash=self._last_hash,
            hash=entry_hash,
            signature=signature,
        )

        # Add to ledger
        self._entries.append(entry)
        self._last_hash = entry_hash

        # Store in persistent storage if available
        if self.storage_backend:
            await self._store_entry(entry)

        return entry_id

    async def _store_entry(self, entry: TraceEntry):
        """Store trace entry in persistent storage"""
        try:
            # Store as JSON in decisions directory
            if hasattr(self.storage_backend, "base_path"):
                ledger_dir = self.storage_backend.base_path / "ledger"
                ledger_dir.mkdir(exist_ok=True)

                file_path = ledger_dir / f"{entry.entry_id}.json"
                with open(file_path, "w") as f:
                    json.dump(asdict(entry), f, default=str)
        except Exception as e:
            print(f"Warning: Failed to store trace entry: {e}")

    def _create_result_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the decision result for tracing"""
        return {
            "eligible": result.get("eligible"),
            "recommendation": result.get("recommendation"),
            "warnings_count": len(result.get("warnings", [])),
            "requirements_count": len(result.get("requirements", [])),
            "compliance_status": result.get("eu_ai_act_compliance", {}).get("status"),
            "has_legal_refs": bool(result.get("legal_references", [])),
            "has_international_obligations": bool(
                result.get("international_law_obligations", [])
            ),
        }

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify the integrity of the entire ledger"""
        verification_result = {
            "is_valid": True,
            "total_entries": len(self._entries),
            "errors": [],
            "genesis_hash": self._genesis_hash,
            "last_hash": self._last_hash,
        }

        if not self._entries:
            return verification_result

        # Verify hash chain
        previous_hash = None
        for i, entry in enumerate(self._entries):
            # Check if previous hash matches
            if entry.previous_hash != previous_hash:
                verification_result["is_valid"] = False
                verification_result["errors"].append(
                    f"Hash mismatch at entry {i}: expected {previous_hash}, got {entry.previous_hash}"
                )

            # Verify entry hash
            expected_hash = self._create_entry_hash(entry.data, entry.previous_hash)
            if entry.hash != expected_hash:
                verification_result["is_valid"] = False
                verification_result["errors"].append(
                    f"Invalid hash at entry {i}: expected {expected_hash}, got {entry.hash}"
                )

            previous_hash = entry.hash

        return verification_result

    def get_entries_by_type(self, entry_type: TraceEntryType) -> List[TraceEntry]:
        """Get all entries of a specific type"""
        return [entry for entry in self._entries if entry.entry_type == entry_type]

    def get_entries_by_function(self, function_id: str) -> List[TraceEntry]:
        """Get all entries for a specific function"""
        return [
            entry
            for entry in self._entries
            if entry.data.get("function_id") == function_id
        ]

    def get_entries_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[TraceEntry]:
        """Get entries within a date range"""
        return [
            entry
            for entry in self._entries
            if start_date <= entry.timestamp <= end_date
        ]

    def get_latest_entries(self, limit: int = 100) -> List[TraceEntry]:
        """Get the latest entries"""
        return self._entries[-limit:] if self._entries else []

    def get_entry_by_id(self, entry_id: str) -> Optional[TraceEntry]:
        """Get a specific entry by ID"""
        for entry in self._entries:
            if entry.entry_id == entry_id:
                return entry
        return None

    async def load_from_storage(self):
        """Load trace entries from persistent storage"""
        if not self.storage_backend or not hasattr(self.storage_backend, "base_path"):
            return

        try:
            ledger_dir = self.storage_backend.base_path / "ledger"
            if not ledger_dir.exists():
                return

            # Load all entries
            for file_path in ledger_dir.glob("*.json"):
                with open(file_path, "r") as f:
                    entry_data = json.load(f)

                    # Convert back to TraceEntry
                    entry = TraceEntry(
                        entry_id=entry_data["entry_id"],
                        entry_type=TraceEntryType(entry_data["entry_type"]),
                        timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                        data=entry_data["data"],
                        previous_hash=entry_data["previous_hash"],
                        hash=entry_data["hash"],
                        signature=entry_data.get("signature"),
                    )

                    self._entries.append(entry)

            # Sort by timestamp and rebuild hash chain
            self._entries.sort(key=lambda x: x.timestamp)
            self._rebuild_hash_chain()

        except Exception as e:
            print(f"Warning: Failed to load trace entries: {e}")

    def _rebuild_hash_chain(self):
        """Rebuild the hash chain after loading from storage"""
        if not self._entries:
            return

        self._last_hash = None
        for entry in self._entries:
            if entry.previous_hash != self._last_hash:
                # Hash chain is broken, need to recalculate
                expected_hash = self._create_entry_hash(entry.data, self._last_hash)
                if entry.hash != expected_hash:
                    print(
                        f"Warning: Hash chain integrity issue at entry {entry.entry_id}"
                    )

            self._last_hash = entry.hash

    def get_ledger_stats(self) -> Dict[str, Any]:
        """Get statistics about the ledger"""
        if not self._entries:
            return {
                "total_entries": 0,
                "entry_types": {},
                "first_entry": None,
                "last_entry": None,
                "is_valid": True,
            }

        # Count entries by type
        entry_types = {}
        for entry in self._entries:
            entry_type = entry.entry_type.value
            entry_types[entry_type] = entry_types.get(entry_type, 0) + 1

        verification = self.verify_integrity()

        return {
            "total_entries": len(self._entries),
            "entry_types": entry_types,
            "first_entry": self._entries[0].timestamp.isoformat(),
            "last_entry": self._entries[-1].timestamp.isoformat(),
            "is_valid": verification["is_valid"],
            "genesis_hash": self._genesis_hash,
            "last_hash": self._last_hash,
        }
