"""
Trace Audit Module

This module provides audit capabilities for trace records,
enabling verification of trace integrity and compliance checking.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import asdict

from policy_as_code.tracing.errors import AuditError, IntegrityError
from policy_as_code.trace_schema import TraceRecord, TraceEvent, TraceStatus


class TraceAuditor:
    """Audits trace records for integrity and compliance"""

    def __init__(self):
        self.audit_rules: List[Dict[str, Any]] = []
        self.integrity_checks: List[str] = []

    async def audit_trace(self, trace: TraceRecord) -> Dict[str, Any]:
        """Perform comprehensive audit of a trace record"""
        audit_result = {
            "trace_id": trace.trace_id,
            "audit_timestamp": datetime.utcnow(),
            "passed": True,
            "issues": [],
            "warnings": [],
            "recommendations": [],
        }

        try:
            # Integrity checks
            integrity_result = await self._check_integrity(trace)
            audit_result["integrity"] = integrity_result

            if not integrity_result["passed"]:
                audit_result["passed"] = False
                audit_result["issues"].extend(integrity_result["issues"])

            # Compliance checks
            compliance_result = await self._check_compliance(trace)
            audit_result["compliance"] = compliance_result

            if not compliance_result["passed"]:
                audit_result["passed"] = False
                audit_result["issues"].extend(compliance_result["issues"])

            # Performance checks
            performance_result = await self._check_performance(trace)
            audit_result["performance"] = performance_result

            if performance_result["warnings"]:
                audit_result["warnings"].extend(performance_result["warnings"])

            # Security checks
            security_result = await self._check_security(trace)
            audit_result["security"] = security_result

            if not security_result["passed"]:
                audit_result["passed"] = False
                audit_result["issues"].extend(security_result["issues"])

            return audit_result

        except Exception as e:
            raise AuditError(f"Audit failed: {e}")

    async def _check_integrity(self, trace: TraceRecord) -> Dict[str, Any]:
        """Check trace integrity"""
        result = {"passed": True, "issues": [], "checks_performed": []}

        try:
            # Check trace ID format
            if not trace.trace_id or len(trace.trace_id) < 10:
                result["issues"].append("Invalid trace ID format")
                result["passed"] = False
            result["checks_performed"].append("trace_id_format")

            # Check timestamp consistency
            if trace.end_time and trace.start_time > trace.end_time:
                result["issues"].append("End time before start time")
                result["passed"] = False
            result["checks_performed"].append("timestamp_consistency")

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
            result["checks_performed"].append("duration_consistency")

            # Check event ordering
            if trace.events:
                for i, event in enumerate(trace.events):
                    if i > 0 and event.timestamp < trace.events[i - 1].timestamp:
                        result["issues"].append(f"Event {i} timestamp out of order")
                        result["passed"] = False
                result["checks_performed"].append("event_ordering")

            return result

        except Exception as e:
            raise IntegrityError(f"Integrity check failed: {e}")

    async def _check_compliance(self, trace: TraceRecord) -> Dict[str, Any]:
        """Check trace compliance with policies"""
        result = {"passed": True, "issues": [], "policies_checked": []}

        try:
            # Check data retention policy
            if trace.start_time < datetime.utcnow() - timedelta(days=365):
                result["issues"].append("Trace exceeds data retention policy")
                result["passed"] = False
            result["policies_checked"].append("data_retention")

            # Check sensitive data handling
            if trace.input_data:
                sensitive_fields = ["password", "ssn", "credit_card", "token"]
                for field in sensitive_fields:
                    if field in json.dumps(trace.input_data).lower():
                        result["issues"].append(f"Sensitive data detected: {field}")
                        result["passed"] = False
            result["policies_checked"].append("sensitive_data")

            # Check audit trail completeness
            if trace.status == TraceStatus.COMPLETED and not trace.output_data:
                result["issues"].append("Missing output data for completed trace")
                result["passed"] = False
            result["policies_checked"].append("audit_trail")

            return result

        except Exception as e:
            raise AuditError(f"Compliance check failed: {e}")

    async def _check_performance(self, trace: TraceRecord) -> Dict[str, Any]:
        """Check trace performance metrics"""
        result = {"passed": True, "warnings": [], "metrics_checked": []}

        try:
            # Check execution time
            if trace.duration_ms:
                if trace.duration_ms > 30000:  # 30 seconds
                    result["warnings"].append("Long execution time detected")
                result["metrics_checked"].append("execution_time")

            # Check performance metrics
            if trace.performance_metrics:
                if trace.performance_metrics.get("memory_usage", 0) > 1000:  # 1GB
                    result["warnings"].append("High memory usage detected")
                result["metrics_checked"].append("memory_usage")

            return result

        except Exception as e:
            raise AuditError(f"Performance check failed: {e}")

    async def _check_security(self, trace: TraceRecord) -> Dict[str, Any]:
        """Check trace security"""
        result = {"passed": True, "issues": [], "security_checks": []}

        try:
            # Check for suspicious patterns
            if trace.events:
                error_events = [
                    e for e in trace.events if e.status == TraceStatus.FAILED
                ]
                if len(error_events) > 5:
                    result["issues"].append("Excessive error events detected")
                    result["passed"] = False
            result["security_checks"].append("error_patterns")

            # Check metadata integrity
            if trace.metadata and trace.metadata.trace_id != trace.trace_id:
                result["issues"].append("Metadata trace ID mismatch")
                result["passed"] = False
            result["security_checks"].append("metadata_integrity")

            return result

        except Exception as e:
            raise AuditError(f"Security check failed: {e}")

    async def generate_audit_report(self, traces: List[TraceRecord]) -> Dict[str, Any]:
        """Generate comprehensive audit report for multiple traces"""
        report = {
            "report_timestamp": datetime.utcnow(),
            "total_traces": len(traces),
            "passed_audits": 0,
            "failed_audits": 0,
            "common_issues": {},
            "recommendations": [],
        }

        for trace in traces:
            audit_result = await self.audit_trace(trace)
            if audit_result["passed"]:
                report["passed_audits"] += 1
            else:
                report["failed_audits"] += 1

                # Track common issues
                for issue in audit_result["issues"]:
                    report["common_issues"][issue] = (
                        report["common_issues"].get(issue, 0) + 1
                    )

        # Generate recommendations based on common issues
        if report["common_issues"].get("Duration mismatch with timestamps", 0) > 0:
            report["recommendations"].append("Review timestamp calculation logic")

        if report["common_issues"].get("Sensitive data detected", 0) > 0:
            report["recommendations"].append("Implement data sanitization")

        return report


# Export main class
__all__ = ["TraceAuditor"]
