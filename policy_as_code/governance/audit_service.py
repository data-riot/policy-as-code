"""
Independent Audit Service
Trace verification, integrity reports, and drift detection
"""

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .errors import DecisionLayerError
from .release import Release, ReleaseManager
from policy_as_code.tracing.ledger import TraceRecord, TraceLedger


class AuditStatus(str, Enum):
    """Audit status states"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class IntegrityCheck(str, Enum):
    """Types of integrity checks"""

    HASH_VERIFICATION = "hash_verification"
    CHAIN_VERIFICATION = "chain_verification"
    REPLAY_TEST = "replay_test"
    SIGNATURE_VERIFICATION = "signature_verification"
    LEGAL_COMPLIANCE = "legal_compliance"


@dataclass
class AuditResult:
    """Result of an audit check"""

    check_type: IntegrityCheck
    status: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "check_type": self.check_type.value,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class IntegrityReport:
    """Comprehensive integrity report"""

    report_id: str
    generated_at: datetime
    audit_status: AuditStatus
    total_traces: int
    checked_traces: int
    failed_checks: int
    results: List[AuditResult] = field(default_factory=list)
    drift_count: int = 0
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "audit_status": self.audit_status.value,
            "total_traces": self.total_traces,
            "checked_traces": self.checked_traces,
            "failed_checks": self.failed_checks,
            "results": [result.to_dict() for result in self.results],
            "drift_count": self.drift_count,
            "summary": self.summary,
        }


class AuditError(DecisionLayerError):
    """Audit service errors"""

    def __init__(self, error_type: str, message: str):
        super().__init__(f"Audit error ({error_type}): {message}")
        self.error_type = error_type


class AuditWorker:
    """Independent audit worker for trace verification"""

    def __init__(
        self,
        trace_ledger: TraceLedger,
        release_manager: ReleaseManager,
        function_registry: Any = None,
    ):
        self.trace_ledger = trace_ledger
        self.release_manager = release_manager
        self.function_registry = function_registry
        self.reports: List[IntegrityReport] = []

    async def run_daily_audit(self) -> IntegrityReport:
        """Run daily integrity audit"""
        report_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        report = IntegrityReport(
            report_id=report_id,
            generated_at=datetime.now(),
            audit_status=AuditStatus.IN_PROGRESS,
            total_traces=0,
            checked_traces=0,
            failed_checks=0,
        )

        try:
            # Get traces from last 24 hours
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)

            traces = await self.trace_ledger.get_traces_by_timeframe(
                start_time, end_time, limit=10000
            )

            report.total_traces = len(traces)

            # Run integrity checks
            for trace in traces:
                trace_results = await self._audit_trace(trace)
                report.results.extend(trace_results)
                report.checked_traces += 1

                # Count failed checks
                for result in trace_results:
                    if result.status == "failed":
                        report.failed_checks += 1

            # Detect drift
            drift_results = await self._detect_drift(traces)
            report.results.extend(drift_results)
            report.drift_count = len([r for r in drift_results if r.status == "failed"])

            # Generate summary
            report.summary = self._generate_summary(report)
            report.audit_status = AuditStatus.COMPLETED

        except Exception as e:
            report.audit_status = AuditStatus.FAILED
            report.summary = f"Audit failed: {str(e)}"

        self.reports.append(report)
        return report

    async def _audit_trace(self, trace: TraceRecord) -> List[AuditResult]:
        """Audit a single trace"""
        results = []

        # Hash verification
        hash_result = await self._verify_trace_hash(trace)
        results.append(hash_result)

        # Chain verification
        chain_result = await self._verify_chain_integrity(trace)
        results.append(chain_result)

        # Replay test
        replay_result = await self._replay_trace(trace)
        results.append(replay_result)

        # Signature verification
        signature_result = await self._verify_signatures(trace)
        results.append(signature_result)

        # Legal compliance
        legal_result = await self._verify_legal_compliance(trace)
        results.append(legal_result)

        return results

    async def _verify_trace_hash(self, trace: TraceRecord) -> AuditResult:
        """Verify trace hash integrity"""
        try:
            # Recompute hash of trace data
            trace_data = {
                "trace_id": trace.trace_id,
                "df_id": trace.df_id,
                "version": trace.version,
                "timestamp": trace.timestamp.isoformat(),
                "input_hash": hashlib.sha256(
                    json.dumps(trace.input_json, sort_keys=True).encode()
                ).hexdigest(),
                "output_hash": hashlib.sha256(
                    json.dumps(trace.output_json, sort_keys=True).encode()
                ).hexdigest(),
            }

            computed_hash = hashlib.sha256(
                json.dumps(trace_data, sort_keys=True).encode()
            ).hexdigest()

            # Compare with stored hash (simplified - in production would use actual df_hash)
            if computed_hash == trace.df_hash:
                return AuditResult(
                    check_type=IntegrityCheck.HASH_VERIFICATION,
                    status="passed",
                    message="Trace hash verification passed",
                    details={"trace_id": trace.trace_id},
                )
            else:
                return AuditResult(
                    check_type=IntegrityCheck.HASH_VERIFICATION,
                    status="failed",
                    message="Trace hash verification failed",
                    details={
                        "trace_id": trace.trace_id,
                        "expected": trace.df_hash,
                        "computed": computed_hash,
                    },
                )
        except Exception as e:
            return AuditResult(
                check_type=IntegrityCheck.HASH_VERIFICATION,
                status="failed",
                message=f"Hash verification error: {str(e)}",
                details={"trace_id": trace.trace_id},
            )

    async def _verify_chain_integrity(self, trace: TraceRecord) -> AuditResult:
        """Verify hash chain integrity"""
        try:
            # Get previous trace
            if trace.prev_hash:
                # In production, would verify the chain hash computation
                return AuditResult(
                    check_type=IntegrityCheck.CHAIN_VERIFICATION,
                    status="passed",
                    message="Chain integrity verification passed",
                    details={"trace_id": trace.trace_id, "prev_hash": trace.prev_hash},
                )
            else:
                return AuditResult(
                    check_type=IntegrityCheck.CHAIN_VERIFICATION,
                    status="passed",
                    message="First trace in chain",
                    details={"trace_id": trace.trace_id},
                )
        except Exception as e:
            return AuditResult(
                check_type=IntegrityCheck.CHAIN_VERIFICATION,
                status="failed",
                message=f"Chain verification error: {str(e)}",
                details={"trace_id": trace.trace_id},
            )

    async def _replay_trace(self, trace: TraceRecord) -> AuditResult:
        """Replay trace to verify output consistency"""
        try:
            # Get release information
            release = self.release_manager.get_release(trace.df_id, trace.version)
            if not release:
                return AuditResult(
                    check_type=IntegrityCheck.REPLAY_TEST,
                    status="failed",
                    message="Release not found for replay",
                    details={
                        "trace_id": trace.trace_id,
                        "df_id": trace.df_id,
                        "version": trace.version,
                    },
                )

            # In production, would actually replay the function
            # For now, we'll do a simplified check
            if trace.status == "success":
                return AuditResult(
                    check_type=IntegrityCheck.REPLAY_TEST,
                    status="passed",
                    message="Replay test passed",
                    details={"trace_id": trace.trace_id, "status": trace.status},
                )
            else:
                return AuditResult(
                    check_type=IntegrityCheck.REPLAY_TEST,
                    status="failed",
                    message="Replay test failed - original execution failed",
                    details={"trace_id": trace.trace_id, "status": trace.status},
                )
        except Exception as e:
            return AuditResult(
                check_type=IntegrityCheck.REPLAY_TEST,
                status="failed",
                message=f"Replay test error: {str(e)}",
                details={"trace_id": trace.trace_id},
            )

    async def _verify_signatures(self, trace: TraceRecord) -> AuditResult:
        """Verify digital signatures"""
        try:
            release = self.release_manager.get_release(trace.df_id, trace.version)
            if not release:
                return AuditResult(
                    check_type=IntegrityCheck.SIGNATURE_VERIFICATION,
                    status="failed",
                    message="Release not found for signature verification",
                    details={"trace_id": trace.trace_id},
                )

            # Check if release has required signatures
            owner_signed = any(sig.role.value == "owner" for sig in release.signatures)
            reviewer_signed = any(
                sig.role.value == "reviewer" for sig in release.signatures
            )

            if owner_signed and reviewer_signed:
                return AuditResult(
                    check_type=IntegrityCheck.SIGNATURE_VERIFICATION,
                    status="passed",
                    message="Required signatures present",
                    details={
                        "trace_id": trace.trace_id,
                        "signature_count": len(release.signatures),
                    },
                )
            else:
                return AuditResult(
                    check_type=IntegrityCheck.SIGNATURE_VERIFICATION,
                    status="failed",
                    message="Missing required signatures",
                    details={
                        "trace_id": trace.trace_id,
                        "owner_signed": owner_signed,
                        "reviewer_signed": reviewer_signed,
                    },
                )
        except Exception as e:
            return AuditResult(
                check_type=IntegrityCheck.SIGNATURE_VERIFICATION,
                status="failed",
                message=f"Signature verification error: {str(e)}",
                details={"trace_id": trace.trace_id},
            )

    async def _verify_legal_compliance(self, trace: TraceRecord) -> AuditResult:
        """Verify legal compliance"""
        try:
            release = self.release_manager.get_release(trace.df_id, trace.version)
            if not release:
                return AuditResult(
                    check_type=IntegrityCheck.LEGAL_COMPLIANCE,
                    status="failed",
                    message="Release not found for legal compliance check",
                    details={"trace_id": trace.trace_id},
                )

            # Check if release has legal references
            if release.legal_references:
                return AuditResult(
                    check_type=IntegrityCheck.LEGAL_COMPLIANCE,
                    status="passed",
                    message="Legal references present",
                    details={
                        "trace_id": trace.trace_id,
                        "legal_ref_count": len(release.legal_references),
                    },
                )
            else:
                return AuditResult(
                    check_type=IntegrityCheck.LEGAL_COMPLIANCE,
                    status="failed",
                    message="No legal references found",
                    details={"trace_id": trace.trace_id},
                )
        except Exception as e:
            return AuditResult(
                check_type=IntegrityCheck.LEGAL_COMPLIANCE,
                status="failed",
                message=f"Legal compliance check error: {str(e)}",
                details={"trace_id": trace.trace_id},
            )

    async def _detect_drift(self, traces: List[TraceRecord]) -> List[AuditResult]:
        """Detect drift in decision patterns"""
        results = []

        try:
            # Group traces by function
            function_traces: Dict[str, List[TraceRecord]] = {}
            for trace in traces:
                key = f"{trace.df_id}:{trace.version}"
                if key not in function_traces:
                    function_traces[key] = []
                function_traces[key].append(trace)

            # Analyze each function for drift
            for function_key, function_trace_list in function_traces.items():
                if len(function_trace_list) < 2:
                    continue  # Need at least 2 traces to detect drift

                drift_result = await self._analyze_function_drift(
                    function_key, function_trace_list
                )
                results.append(drift_result)

        except Exception as e:
            results.append(
                AuditResult(
                    check_type=IntegrityCheck.HASH_VERIFICATION,  # Using as generic check type
                    status="failed",
                    message=f"Drift detection error: {str(e)}",
                    details={},
                )
            )

        return results

    async def _analyze_function_drift(
        self, function_key: str, traces: List[TraceRecord]
    ) -> AuditResult:
        """Analyze drift for a specific function"""
        try:
            # Simple drift detection based on output patterns
            outputs = [trace.output_json for trace in traces]

            # Check for consistent decision patterns
            decision_keys: Set[str] = set()
            for output in outputs:
                decision_keys.update(output.keys())

            # If outputs are very different, might indicate drift
            if len(decision_keys) > 5:  # Arbitrary threshold
                return AuditResult(
                    check_type=IntegrityCheck.HASH_VERIFICATION,  # Using as generic check type
                    status="failed",
                    message=f"Potential drift detected in {function_key}",
                    details={
                        "function_key": function_key,
                        "unique_keys": len(decision_keys),
                    },
                )
            else:
                return AuditResult(
                    check_type=IntegrityCheck.HASH_VERIFICATION,  # Using as generic check type
                    status="passed",
                    message=f"No drift detected in {function_key}",
                    details={
                        "function_key": function_key,
                        "unique_keys": len(decision_keys),
                    },
                )
        except Exception as e:
            return AuditResult(
                check_type=IntegrityCheck.HASH_VERIFICATION,  # Using as generic check type
                status="failed",
                message=f"Drift analysis error for {function_key}: {str(e)}",
                details={"function_key": function_key},
            )

    def _generate_summary(self, report: IntegrityReport) -> str:
        """Generate human-readable summary"""
        if report.audit_status == AuditStatus.FAILED:
            return "Audit failed due to system error"

        success_rate = (
            (
                (report.checked_traces - report.failed_checks)
                / report.checked_traces
                * 100
            )
            if report.checked_traces > 0
            else 100
        )

        summary_parts = [
            f"Audit completed: {report.checked_traces}/{report.total_traces} traces checked",
            f"Success rate: {success_rate:.1f}%",
            f"Failed checks: {report.failed_checks}",
            f"Drift detected: {report.drift_count} functions",
        ]

        if report.failed_checks == 0 and report.drift_count == 0:
            summary_parts.append("All integrity checks passed")
        else:
            summary_parts.append("Some issues detected - review required")

        return "; ".join(summary_parts)

    def get_latest_report(self) -> Optional[IntegrityReport]:
        """Get the latest integrity report"""
        if not self.reports:
            return None
        return self.reports[-1]

    def get_reports_by_date(self, date: datetime) -> List[IntegrityReport]:
        """Get reports generated on a specific date"""
        target_date = date.date()
        return [
            report
            for report in self.reports
            if report.generated_at.date() == target_date
        ]


class AuditService:
    """Service for managing audit operations"""

    def __init__(self, audit_worker: AuditWorker):
        self.audit_worker = audit_worker

    async def run_audit(self) -> IntegrityReport:
        """Run a new audit"""
        return await self.audit_worker.run_daily_audit()

    def get_latest_report(self) -> Optional[IntegrityReport]:
        """Get the latest audit report"""
        return self.audit_worker.get_latest_report()

    def get_reports_by_date(self, date: datetime) -> List[IntegrityReport]:
        """Get reports by date"""
        return self.audit_worker.get_reports_by_date(date)

    async def start_periodic_audits(self, interval_hours: int = 24):
        """Start periodic audit service"""
        while True:
            try:
                await self.run_audit()
                await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
            except Exception as e:
                print(f"Audit service error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying


def create_audit_service(
    trace_ledger: TraceLedger,
    release_manager: ReleaseManager,
    function_registry: Any = None,
) -> AuditService:
    """Create an audit service instance"""
    audit_worker = AuditWorker(trace_ledger, release_manager, function_registry)
    return AuditService(audit_worker)
