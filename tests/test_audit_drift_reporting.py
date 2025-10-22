"""
Tests for Enhanced Audit Drift Reporting

This module tests the enhanced audit drift reporting functionality including:
- Comprehensive drift summary generation
- Chain analysis
- Coverage analysis
- Security metrics
- Public report formatting
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from policy_as_code.audit.audit_replay_api import (
    AuditReplayAPI,
    AuditReplayEngine,
    AuditReplayResult,
    AuditStatus,
    DriftDetection,
    DriftType,
    AuditReport,
    create_audit_replay_api,
)


class TestEnhancedDriftReporting:
    """Test enhanced drift reporting functionality"""

    @pytest.fixture
    def mock_audit_replay_engine(self):
        """Create mock audit replay engine"""
        engine = MagicMock(spec=AuditReplayEngine)
        return engine

    @pytest.fixture
    def audit_replay_api(self, mock_audit_replay_engine):
        """Create audit replay API instance"""
        return AuditReplayAPI(mock_audit_replay_engine)

    def test_generate_drift_summary_empty(self, audit_replay_api):
        """Test drift summary generation with no drift detections"""
        drift_summary = audit_replay_api._generate_drift_summary([])

        assert drift_summary["total_drift_events"] == 0
        assert drift_summary["drift_by_type"] == {}
        assert drift_summary["drift_by_severity"] == {}
        assert drift_summary["drift_by_function"] == {}
        assert drift_summary["critical_drift_count"] == 0
        assert drift_summary["most_common_drift_type"] is None
        assert drift_summary["most_affected_function"] is None
        assert drift_summary["drift_timeline"] == []

    def test_generate_drift_summary_with_drift(self, audit_replay_api):
        """Test drift summary generation with drift detections"""
        detections = [
            DriftDetection(
                trace_id="trace_1",
                df_id="TEST.DF_001",
                version="1.0.0",
                drift_type=DriftType.HASH_MISMATCH,
                severity="critical",
                description="Hash mismatch detected",
                detected_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            ),
            DriftDetection(
                trace_id="trace_2",
                df_id="TEST.DF_001",
                version="1.0.0",
                drift_type=DriftType.HASH_MISMATCH,
                severity="critical",
                description="Another hash mismatch",
                detected_at=datetime(2024, 1, 16, 10, 0, 0, tzinfo=timezone.utc),
            ),
            DriftDetection(
                trace_id="trace_3",
                df_id="TEST.DF_002",
                version="1.0.0",
                drift_type=DriftType.ELI_INVALID,
                severity="high",
                description="Invalid ELI",
                detected_at=datetime(2024, 1, 17, 10, 0, 0, tzinfo=timezone.utc),
            ),
        ]

        drift_summary = audit_replay_api._generate_drift_summary(detections)

        assert drift_summary["total_drift_events"] == 3
        assert drift_summary["drift_by_type"]["hash_mismatch"] == 2
        assert drift_summary["drift_by_type"]["eli_invalid"] == 1
        assert drift_summary["drift_by_severity"]["critical"] == 2
        assert drift_summary["drift_by_severity"]["high"] == 1
        assert drift_summary["drift_by_function"]["TEST.DF_001"] == 2
        assert drift_summary["drift_by_function"]["TEST.DF_002"] == 1
        assert drift_summary["critical_drift_count"] == 2
        assert drift_summary["high_drift_count"] == 1
        assert drift_summary["most_common_drift_type"] == "hash_mismatch"
        assert drift_summary["most_affected_function"] == "TEST.DF_001"
        assert len(drift_summary["drift_timeline"]) == 3
        assert drift_summary["drift_timeline"][0]["trace_id"] == "trace_1"

    def test_generate_chain_analysis_intact(self, audit_replay_api):
        """Test chain analysis with intact chain"""
        result = AuditReplayResult(
            audit_id="audit_123",
            status=AuditStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            chain_ok=True,
        )

        chain_analysis = audit_replay_api._generate_chain_analysis(result)

        assert chain_analysis["chain_ok"] is True
        assert chain_analysis["chain_breaks_detected"] is False
        assert chain_analysis["chain_integrity_score"] == 100.0
        assert chain_analysis["chain_status"] == "intact"
        assert "Chain integrity verified" in chain_analysis["chain_recommendations"][0]

    def test_generate_chain_analysis_compromised(self, audit_replay_api):
        """Test chain analysis with compromised chain"""
        result = AuditReplayResult(
            audit_id="audit_123",
            status=AuditStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            chain_ok=False,
        )

        chain_analysis = audit_replay_api._generate_chain_analysis(result)

        assert chain_analysis["chain_ok"] is False
        assert chain_analysis["chain_breaks_detected"] is True
        assert chain_analysis["chain_integrity_score"] == 0.0
        assert chain_analysis["chain_status"] == "compromised"
        assert (
            "CRITICAL: Chain integrity compromised"
            in chain_analysis["chain_recommendations"][0]
        )

    def test_generate_coverage_analysis_excellent(self, audit_replay_api):
        """Test coverage analysis with excellent coverage"""
        result = AuditReplayResult(
            audit_id="audit_123",
            status=AuditStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            coverage_percentage=98.5,
            total_traces_checked=100,
        )

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        coverage_analysis = audit_replay_api._generate_coverage_analysis(
            result, from_date, to_date
        )

        assert coverage_analysis["coverage_percentage"] == 98.5
        assert coverage_analysis["coverage_quality"] == "excellent"
        assert coverage_analysis["total_traces_audited"] == 100
        assert coverage_analysis["audit_period_days"] == 30
        assert coverage_analysis["traces_per_day"] == 3.33
        assert coverage_analysis["coverage_gaps"] == 1.5
        assert (
            "Coverage is excellent" in coverage_analysis["coverage_recommendations"][0]
        )

    def test_generate_coverage_analysis_critical(self, audit_replay_api):
        """Test coverage analysis with critical coverage"""
        result = AuditReplayResult(
            audit_id="audit_123",
            status=AuditStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            coverage_percentage=65.0,
            total_traces_checked=50,
        )

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 7, tzinfo=timezone.utc)

        coverage_analysis = audit_replay_api._generate_coverage_analysis(
            result, from_date, to_date
        )

        assert coverage_analysis["coverage_percentage"] == 65.0
        assert coverage_analysis["coverage_quality"] == "critical"
        assert coverage_analysis["coverage_gaps"] == 35.0
        assert (
            "CRITICAL: Coverage below 70%"
            in coverage_analysis["coverage_recommendations"][0]
        )

    def test_generate_security_metrics_excellent(self, audit_replay_api):
        """Test security metrics with excellent security"""
        result = AuditReplayResult(
            audit_id="audit_123",
            status=AuditStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            unsigned_attempts=0,
            total_traces_checked=100,
        )

        security_metrics = audit_replay_api._generate_security_metrics(result)

        assert security_metrics["security_score"] == 100.0
        assert security_metrics["security_status"] == "excellent"
        assert security_metrics["unsigned_attempts"] == 0
        assert security_metrics["unsigned_percentage"] == 0.0
        assert security_metrics["signature_compliance"] == 100.0
        assert (
            "Security compliance excellent"
            in security_metrics["security_recommendations"][0]
        )

    def test_generate_security_metrics_critical(self, audit_replay_api):
        """Test security metrics with critical security issues"""
        result = AuditReplayResult(
            audit_id="audit_123",
            status=AuditStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            unsigned_attempts=10,
            total_traces_checked=100,
        )

        security_metrics = audit_replay_api._generate_security_metrics(result)

        assert security_metrics["security_score"] == 0.0  # Max deduction reached
        assert security_metrics["security_status"] == "critical"
        assert security_metrics["unsigned_attempts"] == 10
        assert security_metrics["unsigned_percentage"] == 10.0
        assert security_metrics["signature_compliance"] == 90.0
        assert (
            "CRITICAL: Unsigned attempts exceed 5%"
            in security_metrics["security_recommendations"][0]
        )

    def test_generate_coverage_recommendations(self, audit_replay_api):
        """Test coverage recommendations generation"""
        # Test critical coverage
        recommendations = audit_replay_api._generate_coverage_recommendations(65.0)
        assert "CRITICAL: Coverage below 70%" in recommendations[0]

        # Test high coverage
        recommendations = audit_replay_api._generate_coverage_recommendations(75.0)
        assert "HIGH: Coverage below 80%" in recommendations[0]

        # Test medium coverage
        recommendations = audit_replay_api._generate_coverage_recommendations(85.0)
        assert "MEDIUM: Coverage below 90%" in recommendations[0]

        # Test low coverage
        recommendations = audit_replay_api._generate_coverage_recommendations(92.0)
        assert "LOW: Coverage below 95%" in recommendations[0]

        # Test excellent coverage
        recommendations = audit_replay_api._generate_coverage_recommendations(98.0)
        assert "Coverage is excellent" in recommendations[0]

    def test_generate_security_recommendations(self, audit_replay_api):
        """Test security recommendations generation"""
        # Test critical security
        recommendations = audit_replay_api._generate_security_recommendations(10.0)
        assert "CRITICAL: Unsigned attempts exceed 5%" in recommendations[0]

        # Test high security
        recommendations = audit_replay_api._generate_security_recommendations(3.0)
        assert "HIGH: Unsigned attempts exceed 1%" in recommendations[0]

        # Test medium security
        recommendations = audit_replay_api._generate_security_recommendations(0.5)
        assert "MEDIUM: Some unsigned attempts detected" in recommendations[0]

        # Test excellent security
        recommendations = audit_replay_api._generate_security_recommendations(0.0)
        assert "Security compliance excellent" in recommendations[0]

    def test_format_public_report_comprehensive(self, audit_replay_api):
        """Test comprehensive public report formatting"""
        # Create comprehensive audit report
        report = AuditReport(
            report_id="audit_123",
            generated_at=datetime.utcnow(),
            audit_period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            audit_period_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
            total_decisions=100,
            total_traces=100,
            chain_ok=True,
            drift_count=5,
            unsigned_attempts=2,
            coverage_percentage=95.0,
            drift_percentage=5.0,
            compliance_score=85.0,
            drift_detections=[],
            recommendations=["Test recommendation 1", "Test recommendation 2"],
            public_summary={"system_health": "warning"},
            drift_summary={
                "total_drift_events": 5,
                "critical_drift_count": 2,
                "high_drift_count": 3,
                "most_common_drift_type": "hash_mismatch",
                "most_affected_function": "TEST.DF_001",
            },
            chain_analysis={
                "chain_status": "intact",
                "chain_integrity_score": 100.0,
            },
            coverage_analysis={
                "coverage_quality": "excellent",
                "coverage_gaps": 5.0,
                "traces_per_day": 3.23,
            },
            security_metrics={
                "security_status": "good",
                "security_score": 80.0,
                "unsigned_percentage": 2.0,
                "signature_compliance": 98.0,
            },
        )

        formatted = audit_replay_api._format_public_report(report)

        # Test basic fields
        assert formatted["report_id"] == "audit_123"
        assert formatted["compliance_score"] == 85.0
        assert formatted["drift_percentage"] == 5.0
        assert formatted["chain_ok"] is True
        assert formatted["coverage_percentage"] == 95.0

        # Test drift summary
        assert formatted["drift_summary"]["total_drift_events"] == 5
        assert formatted["drift_summary"]["critical_drift_count"] == 2
        assert formatted["drift_summary"]["most_common_drift_type"] == "hash_mismatch"

        # Test chain analysis
        assert formatted["chain_analysis"]["chain_status"] == "intact"
        assert formatted["chain_analysis"]["chain_integrity_score"] == 100.0

        # Test coverage analysis
        assert formatted["coverage_analysis"]["coverage_quality"] == "excellent"
        assert formatted["coverage_analysis"]["coverage_gaps"] == 5.0

        # Test security metrics
        assert formatted["security_metrics"]["security_status"] == "good"
        assert formatted["security_metrics"]["security_score"] == 80.0
        assert formatted["security_metrics"]["signature_compliance"] == 98.0


class TestAuditDriftIntegration:
    """Test audit drift integration with API endpoints"""

    @pytest.fixture
    def mock_decision_engine(self):
        """Create mock decision engine"""
        engine = MagicMock()
        engine.storage_backend = MagicMock()
        engine.trace_ledger = MagicMock()
        return engine

    @pytest.fixture
    def audit_replay_api(self, mock_decision_engine):
        """Create audit replay API instance"""
        return create_audit_replay_api(
            mock_decision_engine, mock_decision_engine.trace_ledger
        )

    @pytest.mark.asyncio
    async def test_comprehensive_audit_report_generation(self, audit_replay_api):
        """Test comprehensive audit report generation"""
        # Mock audit result with comprehensive data
        mock_result = AuditReplayResult(
            audit_id="audit_123",
            status=AuditStatus.COMPLETED,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            total_traces_checked=100,
            traces_with_drift=5,
            drift_percentage=5.0,
            drift_detections=[
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
                    drift_type=DriftType.ELI_INVALID,
                    severity="high",
                    description="Invalid ELI",
                    detected_at=datetime.utcnow(),
                ),
            ],
            chain_ok=True,
            unsigned_attempts=2,
            coverage_percentage=95.0,
            summary={
                "recommendations": [
                    "Review decision function modifications",
                    "Update ELI references",
                ]
            },
        )

        audit_replay_api.audit_replay_engine.replay_audit = AsyncMock(
            return_value=mock_result
        )

        from_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        # Run audit replay
        result = await audit_replay_api.run_audit_replay(from_date, to_date)

        # Verify comprehensive report was generated
        assert result["audit_id"] == "audit_123"
        assert result["status"] == "completed"
        assert result["total_traces_checked"] == 100
        assert result["traces_with_drift"] == 5
        assert result["drift_percentage"] == 5.0
        assert result["chain_ok"] is True
        assert result["unsigned_attempts"] == 2
        assert result["coverage_percentage"] == 95.0

        # Verify report was cached
        assert "audit_123" in audit_replay_api.reports_cache

        # Get the cached report
        cached_report = audit_replay_api.reports_cache["audit_123"]

        # Verify comprehensive analysis fields
        assert cached_report.drift_summary["total_drift_events"] == 2
        assert cached_report.drift_summary["critical_drift_count"] == 1
        assert cached_report.drift_summary["high_drift_count"] == 1
        assert cached_report.drift_summary["most_common_drift_type"] == "hash_mismatch"

        assert cached_report.chain_analysis["chain_status"] == "intact"
        assert cached_report.chain_analysis["chain_integrity_score"] == 100.0

        assert cached_report.coverage_analysis["coverage_quality"] == "excellent"
        assert cached_report.coverage_analysis["coverage_percentage"] == 95.0

        assert cached_report.security_metrics["security_status"] == "good"
        assert cached_report.security_metrics["unsigned_percentage"] == 2.0

    @pytest.mark.asyncio
    async def test_public_report_formatting(self, audit_replay_api):
        """Test public report formatting with comprehensive data"""
        # Create comprehensive report
        report = AuditReport(
            report_id="audit_123",
            generated_at=datetime.utcnow(),
            audit_period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            audit_period_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
            total_decisions=100,
            total_traces=100,
            chain_ok=True,
            drift_count=5,
            unsigned_attempts=2,
            coverage_percentage=95.0,
            drift_percentage=5.0,
            compliance_score=85.0,
            drift_detections=[],
            recommendations=["Test recommendation"],
            public_summary={"system_health": "warning"},
            drift_summary={
                "total_drift_events": 5,
                "critical_drift_count": 2,
                "high_drift_count": 3,
                "most_common_drift_type": "hash_mismatch",
                "most_affected_function": "TEST.DF_001",
            },
            chain_analysis={
                "chain_status": "intact",
                "chain_integrity_score": 100.0,
            },
            coverage_analysis={
                "coverage_quality": "excellent",
                "coverage_gaps": 5.0,
                "traces_per_day": 3.23,
            },
            security_metrics={
                "security_status": "good",
                "security_score": 80.0,
                "unsigned_percentage": 2.0,
                "signature_compliance": 98.0,
            },
        )

        audit_replay_api.reports_cache["audit_123"] = report

        # Get public report
        public_report = await audit_replay_api.get_latest_report()

        # Verify public report contains comprehensive data
        assert public_report["report_id"] == "audit_123"
        assert public_report["compliance_score"] == 85.0
        assert public_report["drift_percentage"] == 5.0
        assert public_report["chain_ok"] is True
        assert public_report["coverage_percentage"] == 95.0

        # Verify comprehensive analysis is included
        assert "drift_summary" in public_report
        assert "chain_analysis" in public_report
        assert "coverage_analysis" in public_report
        assert "security_metrics" in public_report

        # Verify specific metrics
        assert public_report["drift_summary"]["total_drift_events"] == 5
        assert public_report["chain_analysis"]["chain_status"] == "intact"
        assert public_report["coverage_analysis"]["coverage_quality"] == "excellent"
        assert public_report["security_metrics"]["security_status"] == "good"


if __name__ == "__main__":
    pytest.main([__file__])
