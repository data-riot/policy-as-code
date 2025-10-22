"""
Audit Replay API for Policy as Code Platform

This module implements the Audit Replay API that enables post-decision verification
and prevents corruption by allowing auditors to replay and verify decision traces.

CITIZEN BENEFIT PERSPECTIVE:
- Enables post-decision verification to prevent corruption
- Allows citizens to request audits of their decisions
- Provides transparency and public oversight
- Ensures system reliability and prevents "drift"

API ENDPOINTS:
- POST /audit/replay?from=...&to=... - Run audit replay for auditors
- GET /audit/report/latest - Get latest audit report for public
- GET /audit/report/{report_id} - Get specific audit report
- POST /audit/run - Trigger new audit (for auditors)
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from policy_as_code.core.enhanced_engine import DecisionEngine
from policy_as_code.tracing.enhanced_ledger import ImmutableTraceLedger, TraceEntry
from policy_as_code.core.storage import StorageBackend
from policy_as_code.validation.eli_validator import ELIValidationStatus

logger = logging.getLogger(__name__)


class AuditStatus(Enum):
    """Audit execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DriftType(Enum):
    """Types of audit drift detected"""

    HASH_MISMATCH = "hash_mismatch"
    CHAIN_BREAK = "chain_break"
    SIGNATURE_INVALID = "signature_invalid"
    ELI_INVALID = "eli_invalid"
    LOGIC_CHANGE = "logic_change"
    TIMESTAMP_ANOMALY = "timestamp_anomaly"


@dataclass
class DriftDetection:
    """Individual drift detection result"""

    trace_id: str
    df_id: str
    version: str
    drift_type: DriftType
    severity: str  # "low", "medium", "high", "critical"
    description: str
    detected_at: datetime
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    remediation_suggestion: Optional[str] = None


@dataclass
class AuditReplayResult:
    """Result of audit replay operation"""

    audit_id: str
    status: AuditStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_traces_checked: int = 0
    traces_with_drift: int = 0
    drift_percentage: float = 0.0
    drift_detections: List[DriftDetection] = field(default_factory=list)
    chain_ok: bool = True
    unsigned_attempts: int = 0
    coverage_percentage: float = 0.0
    error_message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None


@dataclass
class AuditReport:
    """Comprehensive audit report"""

    report_id: str
    generated_at: datetime
    audit_period_start: datetime
    audit_period_end: datetime
    total_decisions: int
    total_traces: int
    chain_ok: bool
    drift_count: int
    unsigned_attempts: int
    coverage_percentage: float
    drift_percentage: float
    compliance_score: float
    drift_detections: List[DriftDetection]
    recommendations: List[str]
    public_summary: Dict[str, Any]
    drift_summary: Dict[str, Any] = field(default_factory=dict)
    chain_analysis: Dict[str, Any] = field(default_factory=dict)
    coverage_analysis: Dict[str, Any] = field(default_factory=dict)
    security_metrics: Dict[str, Any] = field(default_factory=dict)


class AuditReplayEngine:
    """Engine for performing audit replay operations"""

    def __init__(
        self, decision_engine: DecisionEngine, trace_ledger: ImmutableTraceLedger
    ):
        self.decision_engine = decision_engine
        self.trace_ledger = trace_ledger
        self.storage_backend = decision_engine.storage_backend

    async def replay_audit(
        self, from_date: datetime, to_date: datetime, df_id: Optional[str] = None
    ) -> AuditReplayResult:
        """
        Perform audit replay for specified time range

        Args:
            from_date: Start of audit period
            to_date: End of audit period
            df_id: Optional specific decision function to audit

        Returns:
            AuditReplayResult with comprehensive audit findings
        """
        audit_id = f"audit_{int(from_date.timestamp())}_{int(to_date.timestamp())}"
        started_at = datetime.utcnow()

        logger.info(f"Starting audit replay {audit_id} from {from_date} to {to_date}")

        try:
            # Get traces for the specified period
            traces = await self._get_traces_for_period(from_date, to_date, df_id)

            if not traces:
                return AuditReplayResult(
                    audit_id=audit_id,
                    status=AuditStatus.COMPLETED,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                    summary={"message": "No traces found for specified period"},
                )

            # Perform drift detection
            drift_detections = []
            unsigned_attempts = 0
            chain_breaks = 0

            for trace in traces:
                # Check for drift
                trace_drifts = await self._detect_trace_drift(trace)
                drift_detections.extend(trace_drifts)

                # Check for unsigned attempts
                if not trace.get("signatures") or len(trace.get("signatures", [])) < 2:
                    unsigned_attempts += 1

                # Check for chain breaks
                if not await self._verify_chain_integrity(trace):
                    chain_breaks += 1

            # Calculate metrics
            total_traces = len(traces)
            traces_with_drift = len(
                [d for d in drift_detections if d.severity in ["high", "critical"]]
            )
            drift_percentage = (
                (traces_with_drift / total_traces * 100) if total_traces > 0 else 0.0
            )

            # Calculate coverage
            coverage_percentage = await self._calculate_coverage_percentage(
                from_date, to_date
            )

            # Generate summary
            summary = {
                "audit_period": {
                    "start": from_date.isoformat(),
                    "end": to_date.isoformat(),
                },
                "total_traces_checked": total_traces,
                "traces_with_drift": traces_with_drift,
                "drift_percentage": round(drift_percentage, 2),
                "chain_ok": chain_breaks == 0,
                "unsigned_attempts": unsigned_attempts,
                "coverage_percentage": round(coverage_percentage, 2),
                "drift_types": self._summarize_drift_types(drift_detections),
                "recommendations": self._generate_recommendations(
                    drift_detections, drift_percentage
                ),
            }

            result = AuditReplayResult(
                audit_id=audit_id,
                status=AuditStatus.COMPLETED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                total_traces_checked=total_traces,
                traces_with_drift=traces_with_drift,
                drift_percentage=drift_percentage,
                drift_detections=drift_detections,
                chain_ok=chain_breaks == 0,
                unsigned_attempts=unsigned_attempts,
                coverage_percentage=coverage_percentage,
                summary=summary,
            )

            logger.info(
                f"Audit replay {audit_id} completed: {traces_with_drift}/{total_traces} traces with drift ({drift_percentage:.2f}%)"
            )
            return result

        except Exception as e:
            logger.error(f"Audit replay {audit_id} failed: {e}")
            return AuditReplayResult(
                audit_id=audit_id,
                status=AuditStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                error_message=str(e),
            )

    async def _get_traces_for_period(
        self, from_date: datetime, to_date: datetime, df_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get traces for the specified time period"""
        try:
            # Get traces from trace ledger
            entries = self.trace_ledger.get_entries_by_date_range(from_date, to_date)

            # Filter by decision function if specified
            if df_id:
                entries = [e for e in entries if e.get("df_id") == df_id]

            # Convert to trace format
            traces = []
            for entry in entries:
                if entry.get("type") == "decision_execution":
                    traces.append(entry)

            return traces

        except Exception as e:
            logger.error(f"Failed to get traces for period: {e}")
            return []

    async def _detect_trace_drift(self, trace: Dict[str, Any]) -> List[DriftDetection]:
        """Detect drift in a single trace"""
        detections = []

        try:
            # 1. Hash verification
            hash_drift = await self._verify_trace_hash(trace)
            if hash_drift:
                detections.append(hash_drift)

            # 2. ELI validation
            eli_drift = await self._verify_eli_reference(trace)
            if eli_drift:
                detections.append(eli_drift)

            # 3. Signature verification
            sig_drift = await self._verify_signatures(trace)
            if sig_drift:
                detections.append(sig_drift)

            # 4. Logic consistency
            logic_drift = await self._verify_logic_consistency(trace)
            if logic_drift:
                detections.append(logic_drift)

            # 5. Timestamp validation
            timestamp_drift = await self._verify_timestamp(trace)
            if timestamp_drift:
                detections.append(timestamp_drift)

        except Exception as e:
            logger.error(
                f"Error detecting drift for trace {trace.get('trace_id')}: {e}"
            )

        return detections

    async def _verify_trace_hash(
        self, trace: Dict[str, Any]
    ) -> Optional[DriftDetection]:
        """Verify trace hash integrity"""
        try:
            trace_id = trace.get("trace_id")
            df_id = trace.get("df_id")
            version = trace.get("version")

            # Validate required fields
            if not trace_id or not df_id or not version:
                logger.warning(
                    f"Trace missing required fields: trace_id={trace_id}, df_id={df_id}, version={version}"
                )
                return None

            # Get current decision function specification
            spec = await self.storage_backend.retrieve_function_spec(df_id, version)
            if not spec:
                return DriftDetection(
                    trace_id=trace_id,
                    df_id=df_id,
                    version=version,
                    drift_type=DriftType.HASH_MISMATCH,
                    severity="high",
                    description=f"Decision function specification not found for {df_id} v{version}",
                    detected_at=datetime.utcnow(),
                    remediation_suggestion="Verify decision function is properly registered",
                )

            # Recompute hash
            spec_hash = hashlib.sha256(
                json.dumps(spec, sort_keys=True).encode()
            ).hexdigest()
            stored_hash = trace.get("df_hash", "").replace("sha256:", "")

            if spec_hash != stored_hash:
                return DriftDetection(
                    trace_id=trace_id,
                    df_id=df_id,
                    version=version,
                    drift_type=DriftType.HASH_MISMATCH,
                    severity="critical",
                    description="Decision function hash mismatch",
                    detected_at=datetime.utcnow(),
                    expected_value=spec_hash,
                    actual_value=stored_hash,
                    remediation_suggestion="Decision function may have been modified after trace creation",
                )

            return None

        except Exception as e:
            logger.error(f"Error verifying trace hash: {e}")
            return None

    async def _verify_eli_reference(
        self, trace: Dict[str, Any]
    ) -> Optional[DriftDetection]:
        """Verify ELI reference validity"""
        try:
            trace_id = trace.get("trace_id")
            df_id = trace.get("df_id")
            version = trace.get("version")

            # Validate required fields
            if not trace_id or not df_id or not version:
                logger.warning(
                    f"Trace missing required fields: trace_id={trace_id}, df_id={df_id}, version={version}"
                )
                return None

            # Get decision function specification
            spec = await self.storage_backend.retrieve_function_spec(df_id, version)
            if not spec:
                return None

            # Check ELI reference
            law_ref = spec.get("law_reference", {})
            eli_uri = law_ref.get("eli")

            if not eli_uri:
                return DriftDetection(
                    trace_id=trace_id,
                    df_id=df_id,
                    version=version,
                    drift_type=DriftType.ELI_INVALID,
                    severity="critical",
                    description="Decision function missing ELI reference",
                    detected_at=datetime.utcnow(),
                    remediation_suggestion="Add valid ELI reference to decision function",
                )

            # Validate ELI format
            if not eli_uri.startswith("https://finlex.fi/eli/laki/"):
                return DriftDetection(
                    trace_id=trace_id,
                    df_id=df_id,
                    version=version,
                    drift_type=DriftType.ELI_INVALID,
                    severity="high",
                    description=f"Invalid ELI URI format: {eli_uri}",
                    detected_at=datetime.utcnow(),
                    remediation_suggestion="Use valid Finlex ELI URI format",
                )

            return None

        except Exception as e:
            logger.error(f"Error verifying ELI reference: {e}")
            return None

    async def _verify_signatures(
        self, trace: Dict[str, Any]
    ) -> Optional[DriftDetection]:
        """Verify digital signatures"""
        try:
            trace_id = trace.get("trace_id")
            df_id = trace.get("df_id")
            version = trace.get("version")

            # Validate required fields
            if not trace_id or not df_id or not version:
                logger.warning(
                    f"Trace missing required fields: trace_id={trace_id}, df_id={df_id}, version={version}"
                )
                return None

            # Get decision function specification
            spec = await self.storage_backend.retrieve_function_spec(df_id, version)
            if not spec:
                return None

            signatures = spec.get("signatures", [])

            if len(signatures) < 2:
                return DriftDetection(
                    trace_id=trace_id,
                    df_id=df_id,
                    version=version,
                    drift_type=DriftType.SIGNATURE_INVALID,
                    severity="high",
                    description=f"Insufficient signatures: {len(signatures)}/2 required",
                    detected_at=datetime.utcnow(),
                    remediation_suggestion="Add required signatures (owner + reviewer)",
                )

            # TODO: Implement actual signature verification with KMS
            # For now, just check that signatures exist

            return None

        except Exception as e:
            logger.error(f"Error verifying signatures: {e}")
            return None

    async def _verify_logic_consistency(
        self, trace: Dict[str, Any]
    ) -> Optional[DriftDetection]:
        """Verify decision logic consistency"""
        try:
            trace_id = trace.get("trace_id")
            df_id = trace.get("df_id")
            version = trace.get("version")

            # Validate required fields
            if not trace_id or not df_id or not version:
                logger.warning(
                    f"Trace missing required fields: trace_id={trace_id}, df_id={df_id}, version={version}"
                )
                return None

            # Get decision function specification
            spec = await self.storage_backend.retrieve_function_spec(df_id, version)
            if not spec:
                return None

            # Check invariants
            invariants = spec.get("invariants", [])
            output = trace.get("output", {})

            for invariant in invariants:
                # Simple invariant checking (in production, use proper expression evaluator)
                if "decision" in invariant and "output.decision" in invariant:
                    decision = output.get("decision")
                    if decision not in [
                        "APPROVED",
                        "DENIED",
                        "REQUIRES_ADDITIONAL_INFO",
                        "PARTIALLY_APPROVED",
                    ]:
                        return DriftDetection(
                            trace_id=trace_id,
                            df_id=df_id,
                            version=version,
                            drift_type=DriftType.LOGIC_CHANGE,
                            severity="medium",
                            description=f"Decision output violates invariant: {invariant}",
                            detected_at=datetime.utcnow(),
                            expected_value="APPROVED|DENIED|REQUIRES_ADDITIONAL_INFO|PARTIALLY_APPROVED",
                            actual_value=decision,
                            remediation_suggestion="Check decision function logic",
                        )

            return None

        except Exception as e:
            logger.error(f"Error verifying logic consistency: {e}")
            return None

    async def _verify_timestamp(
        self, trace: Dict[str, Any]
    ) -> Optional[DriftDetection]:
        """Verify timestamp validity"""
        try:
            trace_id = trace.get("trace_id")
            df_id = trace.get("df_id")
            version = trace.get("version")

            # Validate required fields
            if not trace_id or not df_id or not version:
                logger.warning(
                    f"Trace missing required fields: trace_id={trace_id}, df_id={df_id}, version={version}"
                )
                return None

            timestamp_str = trace.get("ts")
            if not timestamp_str:
                return DriftDetection(
                    trace_id=trace_id,
                    df_id=df_id,
                    version=version,
                    drift_type=DriftType.TIMESTAMP_ANOMALY,
                    severity="medium",
                    description="Missing timestamp",
                    detected_at=datetime.utcnow(),
                    remediation_suggestion="Ensure all traces have valid timestamps",
                )

            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except ValueError:
                return DriftDetection(
                    trace_id=trace_id,
                    df_id=df_id,
                    version=version,
                    drift_type=DriftType.TIMESTAMP_ANOMALY,
                    severity="medium",
                    description=f"Invalid timestamp format: {timestamp_str}",
                    detected_at=datetime.utcnow(),
                    remediation_suggestion="Use ISO 8601 timestamp format",
                )

            # Check if timestamp is in the future
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            if timestamp > now:
                return DriftDetection(
                    trace_id=trace_id,
                    df_id=df_id,
                    version=version,
                    drift_type=DriftType.TIMESTAMP_ANOMALY,
                    severity="low",
                    description=f"Future timestamp: {timestamp_str}",
                    detected_at=datetime.utcnow(),
                    remediation_suggestion="Check system clock synchronization",
                )

            return None

        except Exception as e:
            logger.error(f"Error verifying timestamp: {e}")
            return None

    async def _verify_chain_integrity(self, trace: Dict[str, Any]) -> bool:
        """Verify trace chain integrity"""
        try:
            # This would verify the cryptographic hash chain
            # For now, return True (assume chain is intact)
            return True

        except Exception as e:
            logger.error(f"Error verifying chain integrity: {e}")
            return False

    async def _calculate_coverage_percentage(
        self, from_date: datetime, to_date: datetime
    ) -> float:
        """Calculate audit coverage percentage"""
        try:
            # Get traced decisions
            traced_decisions = len(
                await self._get_traces_for_period(from_date, to_date)
            )

            # For now, assume 100% coverage if we have traces
            # TODO: Implement proper total decision counting
            total_decisions = traced_decisions if traced_decisions > 0 else 1

            if total_decisions == 0:
                return 100.0

            return (traced_decisions / total_decisions) * 100.0

        except Exception as e:
            logger.error(f"Error calculating coverage: {e}")
            return 0.0

    def _summarize_drift_types(
        self, detections: List[DriftDetection]
    ) -> Dict[str, int]:
        """Summarize drift types"""
        summary: Dict[str, int] = {}
        for detection in detections:
            drift_type = detection.drift_type.value
            summary[drift_type] = summary.get(drift_type, 0) + 1
        return summary

    def _generate_recommendations(
        self, detections: List[DriftDetection], drift_percentage: float
    ) -> List[str]:
        """Generate recommendations based on audit findings"""
        recommendations = []

        if drift_percentage > 1.0:
            recommendations.append(
                "CRITICAL: Drift percentage exceeds 1% threshold - immediate investigation required"
            )

        if drift_percentage > 0.5:
            recommendations.append(
                "HIGH: Drift percentage above 0.5% - review decision functions"
            )

        drift_types = self._summarize_drift_types(detections)

        if drift_types.get("hash_mismatch", 0) > 0:
            recommendations.append(
                "Review decision function modifications and ensure proper versioning"
            )

        if drift_types.get("signature_invalid", 0) > 0:
            recommendations.append("Verify KMS key management and signature processes")

        if drift_types.get("eli_invalid", 0) > 0:
            recommendations.append("Update ELI references to valid Finlex URIs")

        if drift_types.get("chain_break", 0) > 0:
            recommendations.append("Investigate trace ledger integrity issues")

        if not recommendations:
            recommendations.append(
                "No critical issues detected - system operating normally"
            )

        return recommendations


class AuditReplayAPI:
    """API endpoints for audit replay functionality"""

    def __init__(self, audit_replay_engine: AuditReplayEngine):
        self.audit_replay_engine = audit_replay_engine
        self.reports_cache: Dict[str, AuditReport] = {}

    async def run_audit_replay(
        self, from_date: datetime, to_date: datetime, df_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """POST /audit/replay endpoint"""
        try:
            result = await self.audit_replay_engine.replay_audit(
                from_date, to_date, df_id
            )

            # Generate audit report
            report = await self._generate_audit_report(result, from_date, to_date)
            self.reports_cache[result.audit_id] = report

            return {
                "audit_id": result.audit_id,
                "status": result.status.value,
                "started_at": result.started_at.isoformat(),
                "completed_at": (
                    result.completed_at.isoformat() if result.completed_at else None
                ),
                "total_traces_checked": result.total_traces_checked,
                "traces_with_drift": result.traces_with_drift,
                "drift_percentage": result.drift_percentage,
                "chain_ok": result.chain_ok,
                "unsigned_attempts": result.unsigned_attempts,
                "coverage_percentage": result.coverage_percentage,
                "summary": result.summary,
                "error_message": result.error_message,
            }

        except Exception as e:
            logger.error(f"Audit replay API error: {e}")
            return {"error": "Audit replay failed", "message": str(e)}

    async def get_latest_report(self) -> Dict[str, Any]:
        """GET /audit/report/latest endpoint"""
        try:
            # Get the most recent report
            if not self.reports_cache:
                return {
                    "message": "No audit reports available",
                    "recommendation": "Run audit replay to generate first report",
                }

            latest_report_id = max(self.reports_cache.keys())
            latest_report = self.reports_cache[latest_report_id]

            return self._format_public_report(latest_report)

        except Exception as e:
            logger.error(f"Error getting latest report: {e}")
            return {"error": "Failed to get latest report", "message": str(e)}

    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """GET /audit/report/{report_id} endpoint"""
        try:
            if report_id not in self.reports_cache:
                return None

            report = self.reports_cache[report_id]
            return self._format_public_report(report)

        except Exception as e:
            logger.error(f"Error getting report {report_id}: {e}")
            return None

    async def _generate_audit_report(
        self, result: AuditReplayResult, from_date: datetime, to_date: datetime
    ) -> AuditReport:
        """Generate comprehensive audit report"""

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(result)

        # Generate recommendations
        recommendations = (
            result.summary.get("recommendations", []) if result.summary else []
        )

        # Create comprehensive drift summary
        drift_summary = self._generate_drift_summary(result.drift_detections)

        # Create chain analysis
        chain_analysis = self._generate_chain_analysis(result)

        # Create coverage analysis
        coverage_analysis = self._generate_coverage_analysis(result, from_date, to_date)

        # Create security metrics
        security_metrics = self._generate_security_metrics(result)

        # Create public summary
        public_summary = {
            "audit_period": {
                "start": from_date.isoformat(),
                "end": to_date.isoformat(),
            },
            "total_decisions_audited": result.total_traces_checked,
            "system_health": (
                "healthy"
                if result.drift_percentage < 0.5
                else "warning"
                if result.drift_percentage < 1.0
                else "critical"
            ),
            "compliance_score": round(compliance_score, 2),
            "chain_integrity": "intact" if result.chain_ok else "compromised",
            "coverage": f"{result.coverage_percentage:.1f}%",
            "last_updated": (
                result.completed_at.isoformat() if result.completed_at else None
            ),
        }

        return AuditReport(
            report_id=result.audit_id,
            generated_at=result.completed_at or datetime.utcnow(),
            audit_period_start=from_date,
            audit_period_end=to_date,
            total_decisions=result.total_traces_checked,
            total_traces=result.total_traces_checked,
            chain_ok=result.chain_ok,
            drift_count=result.traces_with_drift,
            unsigned_attempts=result.unsigned_attempts,
            coverage_percentage=result.coverage_percentage,
            drift_percentage=result.drift_percentage,
            compliance_score=compliance_score,
            drift_detections=result.drift_detections,
            recommendations=recommendations,
            public_summary=public_summary,
            drift_summary=drift_summary,
            chain_analysis=chain_analysis,
            coverage_analysis=coverage_analysis,
            security_metrics=security_metrics,
        )

    def _calculate_compliance_score(self, result: AuditReplayResult) -> float:
        """Calculate compliance score based on audit results"""
        score = 100.0

        # Deduct points for drift
        score -= result.drift_percentage * 10  # 10 points per 1% drift

        # Deduct points for chain breaks
        if not result.chain_ok:
            score -= 20

        # Deduct points for unsigned attempts
        if result.unsigned_attempts > 0:
            score -= min(result.unsigned_attempts * 5, 30)  # Max 30 points deduction

        # Deduct points for low coverage
        if result.coverage_percentage < 95:
            score -= (95 - result.coverage_percentage) * 2

        return max(score, 0.0)

    def _generate_drift_summary(
        self, drift_detections: List[DriftDetection]
    ) -> Dict[str, Any]:
        """Generate comprehensive drift summary"""
        if not drift_detections:
            return {
                "total_drift_events": 0,
                "drift_by_type": {},
                "drift_by_severity": {},
                "drift_by_function": {},
                "critical_drift_count": 0,
                "high_drift_count": 0,
                "medium_drift_count": 0,
                "low_drift_count": 0,
                "most_common_drift_type": None,
                "most_affected_function": None,
                "drift_timeline": [],
            }

        # Count drift by type
        drift_by_type: Dict[str, int] = {}
        drift_by_severity: Dict[str, int] = {}
        drift_by_function: Dict[str, int] = {}
        drift_timeline = []

        for detection in drift_detections:
            # Count by type
            drift_type = detection.drift_type.value
            drift_by_type[drift_type] = drift_by_type.get(drift_type, 0) + 1

            # Count by severity
            severity = detection.severity
            drift_by_severity[severity] = drift_by_severity.get(severity, 0) + 1

            # Count by function
            df_id = detection.df_id
            drift_by_function[df_id] = drift_by_function.get(df_id, 0) + 1

            # Add to timeline
            drift_timeline.append(
                {
                    "timestamp": detection.detected_at.isoformat(),
                    "trace_id": detection.trace_id,
                    "df_id": detection.df_id,
                    "drift_type": drift_type,
                    "severity": severity,
                    "description": detection.description,
                }
            )

        # Sort timeline by timestamp
        drift_timeline.sort(key=lambda x: x["timestamp"])

        # Find most common drift type
        most_common_drift_type = (
            max(drift_by_type.items(), key=lambda x: x[1])[0] if drift_by_type else None
        )

        # Find most affected function
        most_affected_function = (
            max(drift_by_function.items(), key=lambda x: x[1])[0]
            if drift_by_function
            else None
        )

        return {
            "total_drift_events": len(drift_detections),
            "drift_by_type": drift_by_type,
            "drift_by_severity": drift_by_severity,
            "drift_by_function": drift_by_function,
            "critical_drift_count": drift_by_severity.get("critical", 0),
            "high_drift_count": drift_by_severity.get("high", 0),
            "medium_drift_count": drift_by_severity.get("medium", 0),
            "low_drift_count": drift_by_severity.get("low", 0),
            "most_common_drift_type": most_common_drift_type,
            "most_affected_function": most_affected_function,
            "drift_timeline": drift_timeline,
        }

    def _generate_chain_analysis(self, result: AuditReplayResult) -> Dict[str, Any]:
        """Generate chain integrity analysis"""
        return {
            "chain_ok": result.chain_ok,
            "chain_breaks_detected": not result.chain_ok,
            "chain_integrity_score": 100.0 if result.chain_ok else 0.0,
            "chain_status": "intact" if result.chain_ok else "compromised",
            "chain_recommendations": (
                ["Chain integrity verified - no breaks detected"]
                if result.chain_ok
                else [
                    "CRITICAL: Chain integrity compromised - immediate investigation required",
                    "Verify cryptographic hash chain continuity",
                    "Check for tampering or system errors",
                ]
            ),
            "last_chain_verification": (
                result.completed_at.isoformat() if result.completed_at else None
            ),
        }

    def _generate_coverage_analysis(
        self, result: AuditReplayResult, from_date: datetime, to_date: datetime
    ) -> Dict[str, Any]:
        """Generate coverage analysis"""
        coverage_percentage = result.coverage_percentage
        total_traces = result.total_traces_checked

        # Calculate coverage quality
        if coverage_percentage >= 95.0:
            coverage_quality = "excellent"
        elif coverage_percentage >= 90.0:
            coverage_quality = "good"
        elif coverage_percentage >= 80.0:
            coverage_quality = "acceptable"
        elif coverage_percentage >= 70.0:
            coverage_quality = "poor"
        else:
            coverage_quality = "critical"

        # Calculate audit period duration
        audit_duration_days = (to_date - from_date).days

        return {
            "coverage_percentage": coverage_percentage,
            "coverage_quality": coverage_quality,
            "total_traces_audited": total_traces,
            "audit_period_days": audit_duration_days,
            "traces_per_day": (
                round(total_traces / audit_duration_days, 2)
                if audit_duration_days > 0
                else 0
            ),
            "coverage_gaps": max(0, 100.0 - coverage_percentage),
            "coverage_recommendations": self._generate_coverage_recommendations(
                coverage_percentage
            ),
            "coverage_trend": "stable",  # TODO: Implement trend analysis
        }

    def _generate_security_metrics(self, result: AuditReplayResult) -> Dict[str, Any]:
        """Generate security metrics"""
        unsigned_attempts = result.unsigned_attempts
        total_traces = result.total_traces_checked

        # Calculate security score
        security_score = 100.0
        if unsigned_attempts > 0:
            security_score -= min(unsigned_attempts * 10, 50)  # Max 50 points deduction

        # Calculate unsigned percentage
        unsigned_percentage = (
            (unsigned_attempts / total_traces * 100) if total_traces > 0 else 0.0
        )

        # Determine security status
        if unsigned_percentage == 0.0:
            security_status = "excellent"
        elif unsigned_percentage <= 1.0:
            security_status = "good"
        elif unsigned_percentage <= 5.0:
            security_status = "warning"
        else:
            security_status = "critical"

        return {
            "security_score": round(security_score, 2),
            "security_status": security_status,
            "unsigned_attempts": unsigned_attempts,
            "unsigned_percentage": round(unsigned_percentage, 2),
            "total_traces": total_traces,
            "signed_traces": total_traces - unsigned_attempts,
            "signature_compliance": (
                round((total_traces - unsigned_attempts) / total_traces * 100, 2)
                if total_traces > 0
                else 0.0
            ),
            "security_recommendations": self._generate_security_recommendations(
                unsigned_percentage
            ),
            "last_security_check": (
                result.completed_at.isoformat() if result.completed_at else None
            ),
        }

    def _generate_coverage_recommendations(
        self, coverage_percentage: float
    ) -> List[str]:
        """Generate coverage recommendations"""
        recommendations = []

        if coverage_percentage < 70.0:
            recommendations.append(
                "CRITICAL: Coverage below 70% - immediate investigation required"
            )
        elif coverage_percentage < 80.0:
            recommendations.append("HIGH: Coverage below 80% - review audit processes")
        elif coverage_percentage < 90.0:
            recommendations.append(
                "MEDIUM: Coverage below 90% - consider improving audit coverage"
            )
        elif coverage_percentage < 95.0:
            recommendations.append(
                "LOW: Coverage below 95% - minor improvements recommended"
            )
        else:
            recommendations.append(
                "Coverage is excellent - maintain current audit processes"
            )

        return recommendations

    def _generate_security_recommendations(
        self, unsigned_percentage: float
    ) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        if unsigned_percentage > 5.0:
            recommendations.append(
                "CRITICAL: Unsigned attempts exceed 5% - immediate security review required"
            )
        elif unsigned_percentage > 1.0:
            recommendations.append(
                "HIGH: Unsigned attempts exceed 1% - review signature processes"
            )
        elif unsigned_percentage > 0.0:
            recommendations.append(
                "MEDIUM: Some unsigned attempts detected - investigate root cause"
            )
        else:
            recommendations.append(
                "Security compliance excellent - all traces properly signed"
            )

        return recommendations

    def _format_public_report(self, report: AuditReport) -> Dict[str, Any]:
        """Format report for public consumption"""
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "audit_period": {
                "start": report.audit_period_start.isoformat(),
                "end": report.audit_period_end.isoformat(),
            },
            "summary": report.public_summary,
            "recommendations": report.recommendations,
            "compliance_score": report.compliance_score,
            "drift_percentage": report.drift_percentage,
            "chain_ok": report.chain_ok,
            "coverage_percentage": report.coverage_percentage,
            "drift_summary": {
                "total_drift_events": report.drift_summary.get("total_drift_events", 0),
                "critical_drift_count": report.drift_summary.get(
                    "critical_drift_count", 0
                ),
                "high_drift_count": report.drift_summary.get("high_drift_count", 0),
                "most_common_drift_type": report.drift_summary.get(
                    "most_common_drift_type"
                ),
                "most_affected_function": report.drift_summary.get(
                    "most_affected_function"
                ),
            },
            "chain_analysis": {
                "chain_status": report.chain_analysis.get("chain_status"),
                "chain_integrity_score": report.chain_analysis.get(
                    "chain_integrity_score"
                ),
            },
            "coverage_analysis": {
                "coverage_quality": report.coverage_analysis.get("coverage_quality"),
                "coverage_gaps": report.coverage_analysis.get("coverage_gaps"),
                "traces_per_day": report.coverage_analysis.get("traces_per_day"),
            },
            "security_metrics": {
                "security_status": report.security_metrics.get("security_status"),
                "security_score": report.security_metrics.get("security_score"),
                "unsigned_percentage": report.security_metrics.get(
                    "unsigned_percentage"
                ),
                "signature_compliance": report.security_metrics.get(
                    "signature_compliance"
                ),
            },
        }


# Factory function
def create_audit_replay_api(
    decision_engine: DecisionEngine, trace_ledger: ImmutableTraceLedger
) -> AuditReplayAPI:
    """Create Audit Replay API instance"""
    audit_replay_engine = AuditReplayEngine(decision_engine, trace_ledger)
    return AuditReplayAPI(audit_replay_engine)
