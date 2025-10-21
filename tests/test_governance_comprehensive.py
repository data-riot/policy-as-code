"""
Comprehensive test suite for governance and tracing components
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from policy_as_code.governance.audit_service import AuditService, AuditReport
from policy_as_code.governance.release import ReleaseManager, ReleaseStatus
from policy_as_code.governance.legal_refs import LegalReferenceValidator
from policy_as_code.tracing.ledger import TraceLedger, TraceRecord
from policy_as_code.tracing.postgres import PostgreSQLTraceStore


class TestAuditService:
    """Test audit service functionality"""

    @pytest.fixture
    def audit_service(self):
        """Create test audit service"""
        return AuditService()

    @pytest.mark.asyncio
    async def test_run_comprehensive_audit(self, audit_service):
        """Test running comprehensive audit"""
        with patch.object(audit_service, "_verify_trace_integrity", return_value=True):
            with patch.object(
                audit_service, "_check_function_compliance", return_value=True
            ):
                result = await audit_service.run_comprehensive_audit()

                assert result["status"] == "completed"
                assert result["integrity_checks_passed"] is True
                assert result["compliance_checks_passed"] is True

    @pytest.mark.asyncio
    async def test_generate_audit_report(self, audit_service):
        """Test generating audit report"""
        audit_data = {
            "total_traces": 1000,
            "integrity_violations": 0,
            "compliance_violations": 2,
            "performance_issues": 1,
        }

        with patch.object(
            audit_service, "_collect_audit_data", return_value=audit_data
        ):
            report = await audit_service.generate_audit_report()

            assert isinstance(report, AuditReport)
            assert report.total_traces == 1000
            assert report.integrity_violations == 0
            assert report.compliance_violations == 2

    @pytest.mark.asyncio
    async def test_detect_anomalies(self, audit_service):
        """Test detecting anomalies"""
        trace_data = [
            {
                "timestamp": datetime.utcnow() - timedelta(hours=1),
                "execution_time": 0.1,
            },
            {
                "timestamp": datetime.utcnow() - timedelta(minutes=30),
                "execution_time": 0.1,
            },
            {"timestamp": datetime.utcnow(), "execution_time": 5.0},  # Anomaly
        ]

        anomalies = await audit_service.detect_anomalies(trace_data)

        assert len(anomalies) > 0
        assert any(anomaly["type"] == "performance" for anomaly in anomalies)


class TestReleaseManager:
    """Test release management functionality"""

    @pytest.fixture
    def release_manager(self):
        """Create test release manager"""
        return ReleaseManager()

    @pytest.mark.asyncio
    async def test_create_release(self, release_manager):
        """Test creating a release"""
        function_id = "test_function"
        version = "1.0.0"
        legal_references = ["https://finlex.fi/fi/laki/alkup/1999/19990544#L7"]

        with patch.object(
            release_manager, "_validate_legal_references", return_value=True
        ):
            release = await release_manager.create_release(
                function_id=function_id,
                version=version,
                legal_references=legal_references,
                change_summary="Initial release",
            )

            assert release.function_id == function_id
            assert release.version == version
            assert release.status == ReleaseStatus.DRAFT

    @pytest.mark.asyncio
    async def test_sign_release(self, release_manager):
        """Test signing a release"""
        release_id = "release_123"
        signer_id = "signer_456"
        signature = "mock_signature"

        with patch.object(release_manager, "_validate_signature", return_value=True):
            result = await release_manager.sign_release(
                release_id=release_id, signer_id=signer_id, signature=signature
            )

            assert result["status"] == "signed"
            assert result["signer_id"] == signer_id

    @pytest.mark.asyncio
    async def test_activate_release(self, release_manager):
        """Test activating a release"""
        release_id = "release_123"

        with patch.object(
            release_manager, "_check_signature_requirements", return_value=True
        ):
            result = await release_manager.activate_release(release_id)

            assert result["status"] == "active"
            assert result["activation_time"] is not None


class TestLegalReferenceValidator:
    """Test legal reference validation functionality"""

    @pytest.fixture
    def legal_validator(self):
        """Create test legal reference validator"""
        return LegalReferenceValidator()

    @pytest.mark.asyncio
    async def test_validate_finlex_reference(self, legal_validator):
        """Test validating Finlex reference"""
        finlex_url = "https://finlex.fi/fi/laki/alkup/1999/19990544#L7"

        with patch.object(
            legal_validator, "_check_finlex_accessibility", return_value=True
        ):
            result = await legal_validator.validate_reference(finlex_url)

            assert result["valid"] is True
            assert result["system"] == "finlex"
            assert result["act_id"] == "544/1999"

    @pytest.mark.asyncio
    async def test_validate_eurlex_reference(self, legal_validator):
        """Test validating EUR-Lex reference"""
        eurlex_url = (
            "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"
        )

        with patch.object(
            legal_validator, "_check_eurlex_accessibility", return_value=True
        ):
            result = await legal_validator.validate_reference(eurlex_url)

            assert result["valid"] is True
            assert result["system"] == "eurlex"

    @pytest.mark.asyncio
    async def test_validate_invalid_reference(self, legal_validator):
        """Test validating invalid reference"""
        invalid_url = "https://invalid-url.com/law"

        result = await legal_validator.validate_reference(invalid_url)

        assert result["valid"] is False
        assert "error" in result


class TestTraceLedger:
    """Test trace ledger functionality"""

    @pytest.fixture
    def trace_ledger(self):
        """Create test trace ledger"""
        return TraceLedger()

    @pytest.fixture
    def sample_trace_record(self):
        """Create sample trace record"""
        return TraceRecord(
            trace_id="trace_123",
            function_id="test_function",
            version="1.0.0",
            input_hash="input_hash_456",
            output_hash="output_hash_789",
            execution_time=0.5,
            timestamp=datetime.utcnow(),
            previous_hash="previous_hash_abc",
            current_hash="current_hash_def",
        )

    @pytest.mark.asyncio
    async def test_append_trace(self, trace_ledger, sample_trace_record):
        """Test appending trace to ledger"""
        with patch.object(
            trace_ledger, "_calculate_hash", return_value="calculated_hash"
        ):
            result = await trace_ledger.append_trace(sample_trace_record)

            assert result["success"] is True
            assert result["trace_id"] == sample_trace_record.trace_id

    @pytest.mark.asyncio
    async def test_verify_chain_integrity(self, trace_ledger):
        """Test verifying chain integrity"""
        trace_records = [
            TraceRecord(
                trace_id="trace_1",
                function_id="test_function",
                version="1.0.0",
                input_hash="input_1",
                output_hash="output_1",
                execution_time=0.1,
                timestamp=datetime.utcnow(),
                previous_hash="genesis",
                current_hash="hash_1",
            ),
            TraceRecord(
                trace_id="trace_2",
                function_id="test_function",
                version="1.0.0",
                input_hash="input_2",
                output_hash="output_2",
                execution_time=0.2,
                timestamp=datetime.utcnow(),
                previous_hash="hash_1",
                current_hash="hash_2",
            ),
        ]

        with patch.object(
            trace_ledger, "_calculate_hash", return_value="calculated_hash"
        ):
            integrity_result = await trace_ledger.verify_chain_integrity(trace_records)

            assert integrity_result["integrity_verified"] is True
            assert integrity_result["total_records"] == 2

    @pytest.mark.asyncio
    async def test_query_traces(self, trace_ledger):
        """Test querying traces"""
        query_params = {
            "function_id": "test_function",
            "start_time": datetime.utcnow() - timedelta(hours=1),
            "end_time": datetime.utcnow(),
        }

        with patch.object(trace_ledger, "_execute_query", return_value=[]):
            traces = await trace_ledger.query_traces(query_params)

            assert isinstance(traces, list)


class TestPostgreSQLTraceStore:
    """Test PostgreSQL trace store functionality"""

    @pytest.fixture
    def postgres_store(self):
        """Create test PostgreSQL store"""
        return PostgreSQLTraceStore(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_password",
        )

    @pytest.mark.asyncio
    async def test_store_trace(self, postgres_store):
        """Test storing trace in PostgreSQL"""
        trace_record = TraceRecord(
            trace_id="trace_123",
            function_id="test_function",
            version="1.0.0",
            input_hash="input_hash",
            output_hash="output_hash",
            execution_time=0.5,
            timestamp=datetime.utcnow(),
            previous_hash="prev_hash",
            current_hash="curr_hash",
        )

        with patch.object(postgres_store, "_execute_query", return_value=True):
            result = await postgres_store.store_trace(trace_record)

            assert result is True

    @pytest.mark.asyncio
    async def test_retrieve_trace(self, postgres_store):
        """Test retrieving trace from PostgreSQL"""
        trace_id = "trace_123"

        mock_trace_data = {
            "trace_id": trace_id,
            "function_id": "test_function",
            "version": "1.0.0",
            "execution_time": 0.5,
            "timestamp": datetime.utcnow(),
        }

        with patch.object(
            postgres_store, "_execute_query", return_value=[mock_trace_data]
        ):
            trace = await postgres_store.retrieve_trace(trace_id)

            assert trace is not None
            assert trace["trace_id"] == trace_id

    @pytest.mark.asyncio
    async def test_create_indexes(self, postgres_store):
        """Test creating database indexes"""
        with patch.object(postgres_store, "_execute_query", return_value=True):
            result = await postgres_store.create_indexes()

            assert result is True


class TestGovernanceIntegration:
    """Test governance integration scenarios"""

    @pytest.fixture
    def audit_service(self):
        """Create audit service for integration tests"""
        return AuditService()

    @pytest.fixture
    def release_manager(self):
        """Create release manager for integration tests"""
        return ReleaseManager()

    @pytest.fixture
    def legal_validator(self):
        """Create legal validator for integration tests"""
        return LegalReferenceValidator()

    @pytest.mark.asyncio
    async def test_complete_governance_workflow(
        self, audit_service, release_manager, legal_validator
    ):
        """Test complete governance workflow"""
        # 1. Validate legal references
        legal_references = ["https://finlex.fi/fi/laki/alkup/1999/19990544#L7"]

        with patch.object(
            legal_validator, "_check_finlex_accessibility", return_value=True
        ):
            validation_result = await legal_validator.validate_references(
                legal_references
            )
            assert validation_result["all_valid"] is True

        # 2. Create release
        with patch.object(
            release_manager, "_validate_legal_references", return_value=True
        ):
            release = await release_manager.create_release(
                function_id="loan_approval",
                version="1.0.0",
                legal_references=legal_references,
                change_summary="Initial release",
            )
            assert release.status == ReleaseStatus.DRAFT

        # 3. Sign release
        with patch.object(release_manager, "_validate_signature", return_value=True):
            sign_result = await release_manager.sign_release(
                release_id=release.release_id,
                signer_id="owner_123",
                signature="owner_signature",
            )
            assert sign_result["status"] == "signed"

        # 4. Activate release
        with patch.object(
            release_manager, "_check_signature_requirements", return_value=True
        ):
            activate_result = await release_manager.activate_release(release.release_id)
            assert activate_result["status"] == "active"

        # 5. Run audit
        with patch.object(audit_service, "_verify_trace_integrity", return_value=True):
            audit_result = await audit_service.run_comprehensive_audit()
            assert audit_result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_compliance_monitoring(self, audit_service):
        """Test compliance monitoring"""
        # Simulate compliance violations
        compliance_data = {
            "total_functions": 100,
            "functions_with_legal_refs": 95,
            "functions_without_legal_refs": 5,
            "unsigned_functions": 2,
            "expired_signatures": 1,
        }

        with patch.object(
            audit_service, "_collect_compliance_data", return_value=compliance_data
        ):
            compliance_report = await audit_service.generate_compliance_report()

            assert compliance_report["compliance_rate"] == 0.95
            assert compliance_report["violations"]["missing_legal_refs"] == 5
            assert compliance_report["violations"]["unsigned_functions"] == 2


class TestTracingPerformance:
    """Test tracing performance"""

    @pytest.fixture
    def trace_ledger(self):
        """Create trace ledger for performance tests"""
        return TraceLedger()

    @pytest.mark.asyncio
    async def test_bulk_trace_insertion(self, trace_ledger):
        """Test bulk trace insertion performance"""
        import time

        # Create multiple trace records
        trace_records = []
        for i in range(1000):
            trace_record = TraceRecord(
                trace_id=f"trace_{i}",
                function_id="test_function",
                version="1.0.0",
                input_hash=f"input_hash_{i}",
                output_hash=f"output_hash_{i}",
                execution_time=0.1,
                timestamp=datetime.utcnow(),
                previous_hash=f"prev_hash_{i}",
                current_hash=f"curr_hash_{i}",
            )
            trace_records.append(trace_record)

        start_time = time.time()

        with patch.object(
            trace_ledger, "_calculate_hash", return_value="calculated_hash"
        ):
            results = await trace_ledger.bulk_append_traces(trace_records)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete in reasonable time (less than 5 seconds for 1000 records)
        assert execution_time < 5.0
        assert len(results) == 1000
        assert all(result["success"] for result in results)

    @pytest.mark.asyncio
    async def test_trace_query_performance(self, trace_ledger):
        """Test trace query performance"""
        import time

        query_params = {
            "function_id": "test_function",
            "start_time": datetime.utcnow() - timedelta(days=1),
            "end_time": datetime.utcnow(),
        }

        start_time = time.time()

        with patch.object(trace_ledger, "_execute_query", return_value=[]):
            traces = await trace_ledger.query_traces(query_params)

        end_time = time.time()
        execution_time = end_time - start_time

        # Query should be fast (less than 1 second)
        assert execution_time < 1.0
        assert isinstance(traces, list)
