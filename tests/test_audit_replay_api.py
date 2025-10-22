"""
Tests for Audit Replay API

This module tests the Audit Replay API functionality including:
- Audit replay execution
- Drift detection
- Report generation
- Public report formatting
- Error handling
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from policy_as_code.audit.audit_replay_api import (
    AuditReplayEngine,
    AuditReplayAPI,
    AuditReplayResult,
    AuditStatus,
    DriftDetection,
    DriftType,
    AuditReport,
    create_audit_replay_api,
)
from policy_as_code.core.enhanced_engine import DecisionEngine
from policy_as_code.tracing.enhanced_ledger import ImmutableTraceLedger


class TestAuditReplayEngine:
    """Test Audit Replay Engine functionality"""

    @pytest.fixture
    def mock_decision_engine(self):
        """Create mock decision engine"""
        engine = MagicMock(spec=DecisionEngine)
        engine.storage_backend = MagicMock()
        return engine

    @pytest.fixture
    def mock_trace_ledger(self):
        """Create mock trace ledger"""
        ledger = MagicMock(spec=ImmutableTraceLedger)
        return ledger

    @pytest.fixture
    def audit_replay_engine(self, mock_decision_engine, mock_trace_ledger):
        """Create audit replay engine instance"""
        return AuditReplayEngine(mock_decision_engine, mock_trace_ledger)

    @pytest.mark.asyncio
    async def test_replay_audit_no_traces(self, audit_replay_engine):
        """Test audit replay when no traces found"""
        # Mock empty traces
        audit_replay_engine._get_traces_for_period = AsyncMock(return_value=[])

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = await audit_replay_engine.replay_audit(from_date, to_date)

        assert result.status == AuditStatus.COMPLETED
        assert result.total_traces_checked == 0
        assert result.traces_with_drift == 0
        assert result.drift_percentage == 0.0
        assert result.summary["message"] == "No traces found for specified period"

    @pytest.mark.asyncio
    async def test_replay_audit_with_traces(self, audit_replay_engine):
        """Test audit replay with traces"""
        # Mock traces
        mock_traces = [
            {
                "trace_id": "trace_1",
                "df_id": "TEST.DF_001",
                "version": "1.0.0",
                "ts": "2024-01-15T10:00:00Z",
                "signatures": ["sig1", "sig2"],
                "output": {"decision": "APPROVED"},
            },
            {
                "trace_id": "trace_2",
                "df_id": "TEST.DF_001",
                "version": "1.0.0",
                "ts": "2024-01-16T10:00:00Z",
                "signatures": ["sig1"],
                "output": {"decision": "DENIED"},
            },
        ]

        audit_replay_engine._get_traces_for_period = AsyncMock(return_value=mock_traces)
        audit_replay_engine._detect_trace_drift = AsyncMock(return_value=[])
        audit_replay_engine._verify_chain_integrity = AsyncMock(return_value=True)
        audit_replay_engine._calculate_coverage_percentage = AsyncMock(
            return_value=95.0
        )

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = await audit_replay_engine.replay_audit(from_date, to_date)

        assert result.status == AuditStatus.COMPLETED
        assert result.total_traces_checked == 2
        assert result.traces_with_drift == 0
        assert result.drift_percentage == 0.0
        assert result.chain_ok is True
        assert result.unsigned_attempts == 1  # trace_2 has only 1 signature
        assert result.coverage_percentage == 95.0

    @pytest.mark.asyncio
    async def test_replay_audit_with_drift(self, audit_replay_engine):
        """Test audit replay with drift detection"""
        # Mock traces
        mock_traces = [
            {
                "trace_id": "trace_1",
                "df_id": "TEST.DF_001",
                "version": "1.0.0",
                "ts": "2024-01-15T10:00:00Z",
                "signatures": ["sig1", "sig2"],
                "output": {"decision": "APPROVED"},
            }
        ]

        # Mock drift detection
        mock_drift = DriftDetection(
            trace_id="trace_1",
            df_id="TEST.DF_001",
            version="1.0.0",
            drift_type=DriftType.HASH_MISMATCH,
            severity="critical",
            description="Hash mismatch detected",
            detected_at=datetime.utcnow(),
        )

        audit_replay_engine._get_traces_for_period = AsyncMock(return_value=mock_traces)
        audit_replay_engine._detect_trace_drift = AsyncMock(return_value=[mock_drift])
        audit_replay_engine._verify_chain_integrity = AsyncMock(return_value=True)
        audit_replay_engine._calculate_coverage_percentage = AsyncMock(
            return_value=95.0
        )

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = await audit_replay_engine.replay_audit(from_date, to_date)

        assert result.status == AuditStatus.COMPLETED
        assert result.total_traces_checked == 1
        assert result.traces_with_drift == 1
        assert result.drift_percentage == 100.0
        assert len(result.drift_detections) == 1
        assert result.drift_detections[0].drift_type == DriftType.HASH_MISMATCH

    @pytest.mark.asyncio
    async def test_replay_audit_error_handling(self, audit_replay_engine):
        """Test audit replay error handling"""
        # Mock error in trace retrieval
        audit_replay_engine._get_traces_for_period = AsyncMock(
            side_effect=Exception("Database error")
        )

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = await audit_replay_engine.replay_audit(from_date, to_date)

        assert result.status == AuditStatus.FAILED
        assert result.error_message == "Database error"

    @pytest.mark.asyncio
    async def test_verify_trace_hash_valid(self, audit_replay_engine):
        """Test trace hash verification with valid hash"""
        # Mock trace and spec
        trace = {
            "trace_id": "trace_1",
            "df_id": "TEST.DF_001",
            "version": "1.0.0",
            "df_hash": "sha256:validhash",
        }

        spec = {"id": "TEST.DF_001", "version": "1.0.0", "logic": "test logic"}

        # Mock storage backend
        audit_replay_engine.storage_backend.retrieve_function_spec = AsyncMock(
            return_value=spec
        )

        # Mock hash calculation
        with patch("policy_as_code.audit.audit_replay_api.hashlib.sha256") as mock_hash:
            mock_hash.return_value.hexdigest.return_value = "validhash"

            result = await audit_replay_engine._verify_trace_hash(trace)

            assert result is None  # No drift detected

    @pytest.mark.asyncio
    async def test_verify_trace_hash_mismatch(self, audit_replay_engine):
        """Test trace hash verification with hash mismatch"""
        # Mock trace and spec
        trace = {
            "trace_id": "trace_1",
            "df_id": "TEST.DF_001",
            "version": "1.0.0",
            "df_hash": "sha256:oldhash",
        }

        spec = {"id": "TEST.DF_001", "version": "1.0.0", "logic": "updated logic"}

        # Mock storage backend
        audit_replay_engine.storage_backend.retrieve_function_spec = AsyncMock(
            return_value=spec
        )

        # Mock hash calculation
        with patch("policy_as_code.audit.audit_replay_api.hashlib.sha256") as mock_hash:
            mock_hash.return_value.hexdigest.return_value = "newhash"

            result = await audit_replay_engine._verify_trace_hash(trace)

            assert result is not None
            assert result.drift_type == DriftType.HASH_MISMATCH
            assert result.severity == "critical"
            assert result.expected_value == "newhash"
            assert result.actual_value == "oldhash"

    @pytest.mark.asyncio
    async def test_verify_eli_reference_valid(self, audit_replay_engine):
        """Test ELI reference verification with valid reference"""
        trace = {"trace_id": "trace_1", "df_id": "TEST.DF_001", "version": "1.0.0"}

        spec = {
            "id": "TEST.DF_001",
            "version": "1.0.0",
            "law_reference": {"eli": "https://finlex.fi/eli/laki/2023/123#Pykala4"},
        }

        audit_replay_engine.storage_backend.retrieve_function_spec = AsyncMock(
            return_value=spec
        )

        result = await audit_replay_engine._verify_eli_reference(trace)

        assert result is None  # No drift detected

    @pytest.mark.asyncio
    async def test_verify_eli_reference_missing(self, audit_replay_engine):
        """Test ELI reference verification with missing reference"""
        trace = {"trace_id": "trace_1", "df_id": "TEST.DF_001", "version": "1.0.0"}

        spec = {"id": "TEST.DF_001", "version": "1.0.0", "law_reference": {}}

        audit_replay_engine.storage_backend.retrieve_function_spec = AsyncMock(
            return_value=spec
        )

        result = await audit_replay_engine._verify_eli_reference(trace)

        assert result is not None
        assert result.drift_type == DriftType.ELI_INVALID
        assert result.severity == "critical"
        assert "missing ELI reference" in result.description

    @pytest.mark.asyncio
    async def test_verify_eli_reference_invalid_format(self, audit_replay_engine):
        """Test ELI reference verification with invalid format"""
        trace = {"trace_id": "trace_1", "df_id": "TEST.DF_001", "version": "1.0.0"}

        spec = {
            "id": "TEST.DF_001",
            "version": "1.0.0",
            "law_reference": {"eli": "invalid-uri"},
        }

        audit_replay_engine.storage_backend.retrieve_function_spec = AsyncMock(
            return_value=spec
        )

        result = await audit_replay_engine._verify_eli_reference(trace)

        assert result is not None
        assert result.drift_type == DriftType.ELI_INVALID
        assert result.severity == "high"
        assert "Invalid ELI URI format" in result.description

    @pytest.mark.asyncio
    async def test_verify_signatures_insufficient(self, audit_replay_engine):
        """Test signature verification with insufficient signatures"""
        trace = {"trace_id": "trace_1", "df_id": "TEST.DF_001", "version": "1.0.0"}

        spec = {
            "id": "TEST.DF_001",
            "version": "1.0.0",
            "signatures": [{"kid": "owner_key", "sig": "sig1"}],
        }

        audit_replay_engine.storage_backend.retrieve_function_spec = AsyncMock(
            return_value=spec
        )

        result = await audit_replay_engine._verify_signatures(trace)

        assert result is not None
        assert result.drift_type == DriftType.SIGNATURE_INVALID
        assert result.severity == "high"
        assert "Insufficient signatures: 1/2 required" in result.description

    @pytest.mark.asyncio
    async def test_verify_logic_consistency_violation(self, audit_replay_engine):
        """Test logic consistency verification with invariant violation"""
        trace = {
            "trace_id": "trace_1",
            "df_id": "TEST.DF_001",
            "version": "1.0.0",
            "output": {"decision": "INVALID_DECISION"},
        }

        spec = {
            "id": "TEST.DF_001",
            "version": "1.0.0",
            "invariants": ["output.decision in ['APPROVED','DENIED']"],
        }

        audit_replay_engine.storage_backend.retrieve_function_spec = AsyncMock(
            return_value=spec
        )

        result = await audit_replay_engine._verify_logic_consistency(trace)

        assert result is not None
        assert result.drift_type == DriftType.LOGIC_CHANGE
        assert result.severity == "medium"
        assert "Decision output violates invariant" in result.description

    @pytest.mark.asyncio
    async def test_verify_timestamp_future(self, audit_replay_engine):
        """Test timestamp verification with future timestamp"""
        future_time = datetime.utcnow() + timedelta(hours=1)

        trace = {
            "trace_id": "trace_1",
            "df_id": "TEST.DF_001",
            "version": "1.0.0",
            "ts": future_time.isoformat(),
        }

        result = await audit_replay_engine._verify_timestamp(trace)

        assert result is not None
        assert result.drift_type == DriftType.TIMESTAMP_ANOMALY
        assert result.severity == "low"
        assert "Future timestamp" in result.description

    @pytest.mark.asyncio
    async def test_verify_timestamp_invalid_format(self, audit_replay_engine):
        """Test timestamp verification with invalid format"""
        trace = {
            "trace_id": "trace_1",
            "df_id": "TEST.DF_001",
            "version": "1.0.0",
            "ts": "invalid-timestamp",
        }

        result = await audit_replay_engine._verify_timestamp(trace)

        assert result is not None
        assert result.drift_type == DriftType.TIMESTAMP_ANOMALY
        assert result.severity == "medium"
        assert "Invalid timestamp format" in result.description

    def test_summarize_drift_types(self, audit_replay_engine):
        """Test drift types summarization"""
        detections = [
            DriftDetection(
                trace_id="trace_1",
                df_id="TEST.DF_001",
                version="1.0.0",
                drift_type=DriftType.HASH_MISMATCH,
                severity="critical",
                description="Hash mismatch",
                detected_at=datetime.utcnow(),
            ),
            DriftDetection(
                trace_id="trace_2",
                df_id="TEST.DF_001",
                version="1.0.0",
                drift_type=DriftType.HASH_MISMATCH,
                severity="critical",
                description="Another hash mismatch",
                detected_at=datetime.utcnow(),
            ),
            DriftDetection(
                trace_id="trace_3",
                df_id="TEST.DF_001",
                version="1.0.0",
                drift_type=DriftType.ELI_INVALID,
                severity="high",
                description="Invalid ELI",
                detected_at=datetime.utcnow(),
            ),
        ]

        summary = audit_replay_engine._summarize_drift_types(detections)

        assert summary["hash_mismatch"] == 2
        assert summary["eli_invalid"] == 1

    def test_generate_recommendations_critical_drift(self, audit_replay_engine):
        """Test recommendation generation for critical drift"""
        detections = [
            DriftDetection(
                trace_id="trace_1",
                df_id="TEST.DF_001",
                version="1.0.0",
                drift_type=DriftType.HASH_MISMATCH,
                severity="critical",
                description="Hash mismatch",
                detected_at=datetime.utcnow(),
            )
        ]

        recommendations = audit_replay_engine._generate_recommendations(detections, 2.0)

        assert "CRITICAL: Drift percentage exceeds 1% threshold" in recommendations
        assert "Review decision function modifications" in recommendations

    def test_generate_recommendations_no_issues(self, audit_replay_engine):
        """Test recommendation generation with no issues"""
        recommendations = audit_replay_engine._generate_recommendations([], 0.0)

        assert "No critical issues detected" in recommendations


class TestAuditReplayAPI:
    """Test Audit Replay API functionality"""

    @pytest.fixture
    def mock_audit_replay_engine(self):
        """Create mock audit replay engine"""
        engine = MagicMock(spec=AuditReplayEngine)
        return engine

    @pytest.fixture
    def audit_replay_api(self, mock_audit_replay_engine):
        """Create audit replay API instance"""
        return AuditReplayAPI(mock_audit_replay_engine)

    @pytest.mark.asyncio
    async def test_run_audit_replay_success(self, audit_replay_api):
        """Test successful audit replay execution"""
        # Mock audit result
        mock_result = AuditReplayResult(
            audit_id="audit_123",
            status=AuditStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            total_traces_checked=10,
            traces_with_drift=1,
            drift_percentage=10.0,
            drift_detections=[],
            chain_ok=True,
            unsigned_attempts=0,
            coverage_percentage=95.0,
            summary={"message": "Audit completed"},
        )

        audit_replay_api.audit_replay_engine.replay_audit = AsyncMock(
            return_value=mock_result
        )

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = await audit_replay_api.run_audit_replay(from_date, to_date)

        assert result["audit_id"] == "audit_123"
        assert result["status"] == "completed"
        assert result["total_traces_checked"] == 10
        assert result["traces_with_drift"] == 1
        assert result["drift_percentage"] == 10.0
        assert result["chain_ok"] is True
        assert result["unsigned_attempts"] == 0
        assert result["coverage_percentage"] == 95.0

    @pytest.mark.asyncio
    async def test_run_audit_replay_error(self, audit_replay_api):
        """Test audit replay error handling"""
        audit_replay_api.audit_replay_engine.replay_audit = AsyncMock(
            side_effect=Exception("Database error")
        )

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        result = await audit_replay_api.run_audit_replay(from_date, to_date)

        assert result["error"] == "Audit replay failed"
        assert result["message"] == "Database error"

    @pytest.mark.asyncio
    async def test_get_latest_report_success(self, audit_replay_api):
        """Test getting latest report successfully"""
        # Mock report
        mock_report = AuditReport(
            report_id="audit_123",
            generated_at=datetime.utcnow(),
            audit_period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            audit_period_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
            total_decisions=10,
            total_traces=10,
            chain_ok=True,
            drift_count=1,
            unsigned_attempts=0,
            coverage_percentage=95.0,
            drift_percentage=10.0,
            compliance_score=85.0,
            drift_detections=[],
            recommendations=["Test recommendation"],
            public_summary={"system_health": "warning"},
        )

        audit_replay_api.reports_cache["audit_123"] = mock_report

        result = await audit_replay_api.get_latest_report()

        assert result["report_id"] == "audit_123"
        assert result["compliance_score"] == 85.0
        assert result["drift_percentage"] == 10.0
        assert result["chain_ok"] is True
        assert result["coverage_percentage"] == 95.0

    @pytest.mark.asyncio
    async def test_get_latest_report_no_reports(self, audit_replay_api):
        """Test getting latest report when no reports exist"""
        audit_replay_api.reports_cache = {}

        result = await audit_replay_api.get_latest_report()

        assert result["message"] == "No audit reports available"
        assert result["recommendation"] == "Run audit replay to generate first report"

    @pytest.mark.asyncio
    async def test_get_report_success(self, audit_replay_api):
        """Test getting specific report successfully"""
        # Mock report
        mock_report = AuditReport(
            report_id="audit_123",
            generated_at=datetime.utcnow(),
            audit_period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            audit_period_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
            total_decisions=10,
            total_traces=10,
            chain_ok=True,
            drift_count=1,
            unsigned_attempts=0,
            coverage_percentage=95.0,
            drift_percentage=10.0,
            compliance_score=85.0,
            drift_detections=[],
            recommendations=["Test recommendation"],
            public_summary={"system_health": "warning"},
        )

        audit_replay_api.reports_cache["audit_123"] = mock_report

        result = await audit_replay_api.get_report("audit_123")

        assert result["report_id"] == "audit_123"
        assert result["compliance_score"] == 85.0

    @pytest.mark.asyncio
    async def test_get_report_not_found(self, audit_replay_api):
        """Test getting non-existent report"""
        result = await audit_replay_api.get_report("nonexistent")

        assert result is None

    def test_calculate_compliance_score_perfect(self, audit_replay_api):
        """Test compliance score calculation for perfect audit"""
        result = AuditReplayResult(
            audit_id="audit_123",
            status=AuditStatus.COMPLETED,
            started_at=datetime.utcnow(),
            drift_percentage=0.0,
            chain_ok=True,
            unsigned_attempts=0,
            coverage_percentage=100.0,
        )

        score = audit_replay_api._calculate_compliance_score(result)

        assert score == 100.0

    def test_calculate_compliance_score_with_issues(self, audit_replay_api):
        """Test compliance score calculation with issues"""
        result = AuditReplayResult(
            audit_id="audit_123",
            status=AuditStatus.COMPLETED,
            started_at=datetime.utcnow(),
            drift_percentage=2.0,  # 20 points deduction
            chain_ok=False,  # 20 points deduction
            unsigned_attempts=2,  # 10 points deduction
            coverage_percentage=90.0,  # 10 points deduction
        )

        score = audit_replay_api._calculate_compliance_score(result)

        # 100 - 20 - 20 - 10 - 10 = 40
        assert score == 40.0

    def test_format_public_report(self, audit_replay_api):
        """Test public report formatting"""
        report = AuditReport(
            report_id="audit_123",
            generated_at=datetime.utcnow(),
            audit_period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            audit_period_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
            total_decisions=10,
            total_traces=10,
            chain_ok=True,
            drift_count=1,
            unsigned_attempts=0,
            coverage_percentage=95.0,
            drift_percentage=10.0,
            compliance_score=85.0,
            drift_detections=[],
            recommendations=["Test recommendation"],
            public_summary={"system_health": "warning"},
        )

        formatted = audit_replay_api._format_public_report(report)

        assert formatted["report_id"] == "audit_123"
        assert formatted["compliance_score"] == 85.0
        assert formatted["drift_percentage"] == 10.0
        assert formatted["chain_ok"] is True
        assert formatted["coverage_percentage"] == 95.0
        assert "summary" in formatted
        assert "recommendations" in formatted


class TestAuditReplayAPIIntegration:
    """Test Audit Replay API integration with FastAPI"""

    @pytest.fixture
    def mock_decision_engine(self):
        """Create mock decision engine"""
        engine = MagicMock(spec=DecisionEngine)
        engine.storage_backend = MagicMock()
        engine.trace_ledger = MagicMock(spec=ImmutableTraceLedger)
        return engine

    @pytest.fixture
    def audit_replay_api(self, mock_decision_engine):
        """Create audit replay API instance"""
        return create_audit_replay_api(
            mock_decision_engine, mock_decision_engine.trace_ledger
        )

    @pytest.mark.asyncio
    async def test_create_audit_replay_api(self, mock_decision_engine):
        """Test audit replay API creation"""
        api = create_audit_replay_api(
            mock_decision_engine, mock_decision_engine.trace_ledger
        )

        assert isinstance(api, AuditReplayAPI)
        assert api.audit_replay_engine is not None

    @pytest.mark.asyncio
    async def test_audit_replay_end_to_end(self, audit_replay_api):
        """Test end-to-end audit replay functionality"""
        # Mock successful audit result
        mock_result = AuditReplayResult(
            audit_id="audit_123",
            status=AuditStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            total_traces_checked=5,
            traces_with_drift=0,
            drift_percentage=0.0,
            drift_detections=[],
            chain_ok=True,
            unsigned_attempts=0,
            coverage_percentage=100.0,
            summary={"message": "Audit completed successfully"},
        )

        audit_replay_api.audit_replay_engine.replay_audit = AsyncMock(
            return_value=mock_result
        )

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        # Test audit replay
        result = await audit_replay_api.run_audit_replay(from_date, to_date)

        assert result["audit_id"] == "audit_123"
        assert result["status"] == "completed"
        assert result["total_traces_checked"] == 5
        assert result["drift_percentage"] == 0.0

        # Test getting latest report
        latest_report = await audit_replay_api.get_latest_report()

        assert latest_report["report_id"] == "audit_123"
        assert latest_report["compliance_score"] == 100.0
        assert latest_report["chain_ok"] is True


if __name__ == "__main__":
    pytest.main([__file__])
