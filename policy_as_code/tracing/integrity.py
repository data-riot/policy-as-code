"""
Trace Integrity Module

This module provides integrity checking capabilities for trace records,
ensuring data consistency and detecting tampering or corruption.
"""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import asdict

from policy_as_code.tracing.errors import IntegrityError
from policy_as_code.trace_schema import TraceRecord, TraceEvent


class TraceIntegrityChecker:
    """Checks trace integrity and detects tampering"""

    def __init__(self):
        self.integrity_algorithms = ["sha256", "md5", "crc32"]
        self.checksum_cache: Dict[str, str] = {}

    async def verify_trace_integrity(self, trace: TraceRecord) -> Dict[str, Any]:
        """Verify the integrity of a trace record"""
        integrity_result: Dict[str, Any] = {
            "trace_id": trace.trace_id,
            "verification_timestamp": datetime.utcnow(),
            "passed": True,
            "checks_performed": [],
            "issues": [],
            "checksums": {},
        }

        try:
            # Calculate checksums
            checksums = await self._calculate_checksums(trace)
            integrity_result["checksums"] = checksums

            # Verify timestamp integrity
            timestamp_result = await self._verify_timestamps(trace)
            integrity_result["checks_performed"].append("timestamp_verification")
            if not timestamp_result["passed"]:
                integrity_result["passed"] = False
                integrity_result["issues"].extend(timestamp_result["issues"])

            # Verify event integrity
            event_result = await self._verify_events(trace)
            integrity_result["checks_performed"].append("event_verification")
            if not event_result["passed"]:
                integrity_result["passed"] = False
                integrity_result["issues"].extend(event_result["issues"])

            # Verify data consistency
            consistency_result = await self._verify_data_consistency(trace)
            integrity_result["checks_performed"].append("data_consistency")
            if not consistency_result["passed"]:
                integrity_result["passed"] = False
                integrity_result["issues"].extend(consistency_result["issues"])

            # Verify metadata integrity
            metadata_result = await self._verify_metadata(trace)
            integrity_result["checks_performed"].append("metadata_verification")
            if not metadata_result["passed"]:
                integrity_result["passed"] = False
                integrity_result["issues"].extend(metadata_result["issues"])

            return integrity_result

        except Exception as e:
            raise IntegrityError(f"Integrity verification failed: {e}")

    async def _calculate_checksums(self, trace: TraceRecord) -> Dict[str, str]:
        """Calculate checksums for trace data"""
        checksums = {}

        try:
            # Serialize trace data for checksum calculation
            trace_data = json.dumps(asdict(trace), sort_keys=True, default=str)

            # Calculate different types of checksums
            checksums["sha256"] = hashlib.sha256(trace_data.encode()).hexdigest()
            checksums["md5"] = hashlib.md5(trace_data.encode()).hexdigest()

            # Calculate CRC32 (simplified)
            import zlib

            checksums["crc32"] = hex(zlib.crc32(trace_data.encode()) & 0xFFFFFFFF)

            return checksums

        except Exception as e:
            raise IntegrityError(f"Checksum calculation failed: {e}")

    async def _verify_timestamps(self, trace: TraceRecord) -> Dict[str, Any]:
        """Verify timestamp integrity"""
        result: Dict[str, Any] = {"passed": True, "issues": []}

        try:
            # Check if start time is valid
            if not trace.start_time:
                result["issues"].append("Missing start time")
                result["passed"] = False

            # Check if end time is after start time
            if (
                trace.end_time
                and trace.start_time
                and trace.end_time < trace.start_time
            ):
                result["issues"].append("End time before start time")
                result["passed"] = False

            # Check if timestamps are reasonable (not in the future)
            now = datetime.utcnow()
            if trace.start_time and trace.start_time > now:
                result["issues"].append("Start time in the future")
                result["passed"] = False

            if trace.end_time and trace.end_time > now:
                result["issues"].append("End time in the future")
                result["passed"] = False

            # Check duration consistency
            if trace.duration_ms and trace.start_time and trace.end_time:
                calculated_duration = int(
                    (trace.end_time - trace.start_time).total_seconds() * 1000
                )
                if (
                    abs(trace.duration_ms - calculated_duration) > 1000
                ):  # 1 second tolerance
                    result["issues"].append("Duration mismatch with timestamps")
                    result["passed"] = False

            return result

        except Exception as e:
            raise IntegrityError(f"Timestamp verification failed: {e}")

    async def _verify_events(self, trace: TraceRecord) -> Dict[str, Any]:
        """Verify event integrity"""
        result: Dict[str, Any] = {"passed": True, "issues": []}

        try:
            if not trace.events:
                return result

            # Check event ordering
            for i, event in enumerate(trace.events):
                if i > 0 and event.timestamp < trace.events[i - 1].timestamp:
                    result["issues"].append(f"Event {i} timestamp out of order")
                    result["passed"] = False

                # Check event data integrity
                if not event.event_id:
                    result["issues"].append(f"Event {i} missing event ID")
                    result["passed"] = False

                if not event.event_type:
                    result["issues"].append(f"Event {i} missing event type")
                    result["passed"] = False

            return result

        except Exception as e:
            raise IntegrityError(f"Event verification failed: {e}")

    async def _verify_data_consistency(self, trace: TraceRecord) -> Dict[str, Any]:
        """Verify data consistency"""
        result: Dict[str, Any] = {"passed": True, "issues": []}

        try:
            # Check JSON serializability
            try:
                json.dumps(trace.input_data) if trace.input_data else None
                json.dumps(trace.output_data) if trace.output_data else None
                json.dumps(trace.error_data) if trace.error_data else None
            except (TypeError, ValueError) as e:
                result["issues"].append(f"Data serialization error: {e}")
                result["passed"] = False

            # Check for circular references
            if trace.input_data:
                self._check_circular_refs(trace.input_data, "input_data", result)

            if trace.output_data:
                self._check_circular_refs(trace.output_data, "output_data", result)

            return result

        except Exception as e:
            raise IntegrityError(f"Data consistency verification failed: {e}")

    def _check_circular_refs(self, data: Any, path: str, result: Dict[str, Any]):
        """Check for circular references in data"""
        try:
            json.dumps(data)
        except (TypeError, ValueError):
            result["issues"].append(f"Circular reference detected in {path}")
            result["passed"] = False

    async def _verify_metadata(self, trace: TraceRecord) -> Dict[str, Any]:
        """Verify metadata integrity"""
        result: Dict[str, Any] = {"passed": True, "issues": []}

        try:
            if not trace.metadata:
                return result

            # Check metadata trace ID consistency
            if trace.metadata.trace_id != trace.trace_id:
                result["issues"].append("Metadata trace ID mismatch")
                result["passed"] = False

            # Check metadata timestamp consistency
            if trace.metadata.trace_id and trace.start_time:
                # Metadata should be consistent with trace timing
                pass

            return result

        except Exception as e:
            raise IntegrityError(f"Metadata verification failed: {e}")

    async def detect_tampering(self, trace: TraceRecord, stored_checksum: str) -> bool:
        """Detect if trace has been tampered with"""
        try:
            current_checksums = await self._calculate_checksums(trace)
            current_checksum = current_checksums.get("sha256")

            return current_checksum != stored_checksum

        except Exception as e:
            raise IntegrityError(f"Tampering detection failed: {e}")

    async def generate_integrity_report(
        self, traces: List[TraceRecord]
    ) -> Dict[str, Any]:
        """Generate integrity report for multiple traces"""
        report = {
            "report_timestamp": datetime.utcnow(),
            "total_traces": len(traces),
            "passed_integrity": 0,
            "failed_integrity": 0,
            "common_issues": {},
            "integrity_score": 0.0,
        }

        for trace in traces:
            integrity_result = await self.verify_trace_integrity(trace)
            if integrity_result["passed"]:
                report["passed_integrity"] += 1
            else:
                report["failed_integrity"] += 1

                # Track common issues
                for issue in integrity_result["issues"]:
                    report["common_issues"][issue] = (
                        report["common_issues"].get(issue, 0) + 1
                    )

        # Calculate integrity score
        if report["total_traces"] > 0:
            report["integrity_score"] = (
                report["passed_integrity"] / report["total_traces"]
            )

        return report


# Export main class
__all__ = ["TraceIntegrityChecker"]
