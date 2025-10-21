"""
Comprehensive test suite for API components
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from policy_as_code.api.rest import DecisionLayerAPI, DecisionRequest
from policy_as_code.api.agentic import AgenticDecisionRequest
from policy_as_code.api.audit import AuditService, AuditReport


class TestDecisionRequest:
    """Test DecisionRequest model"""

    def test_decision_request_creation(self):
        """Test creating a decision request"""
        request = DecisionRequest(
            function_id="test_function",
            input_data={"amount": 1000},
            version="1.0.0",
            client_id="test_client",
        )

        assert request.function_id == "test_function"
        assert request.input_data == {"amount": 1000}
        assert request.version == "1.0.0"
        assert request.client_id == "test_client"

    def test_decision_request_validation(self):
        """Test decision request validation"""
        # Valid request
        request = DecisionRequest(
            function_id="test_function", input_data={"amount": 1000}, version="1.0.0"
        )
        assert request.function_id is not None

        # Missing required fields
        with pytest.raises(ValueError):
            DecisionRequest(
                function_id="",  # Empty function_id
                input_data={"amount": 1000},
                version="1.0.0",
            )


class TestAgenticDecisionRequest:
    """Test AgenticDecisionRequest model"""

    def test_agentic_request_creation(self):
        """Test creating an agentic decision request"""
        request = AgenticDecisionRequest(
            query="Should I approve this loan?",
            context={"user_id": "123", "amount": 5000},
            reasoning_mode="autonomous",
        )

        assert request.query == "Should I approve this loan?"
        assert request.context == {"user_id": "123", "amount": 5000}
        assert request.reasoning_mode == "autonomous"


class TestDecisionLayerAPI:
    """Test DecisionLayerAPI functionality"""

    @pytest.fixture
    def api(self):
        """Create a test API instance"""
        return DecisionLayerAPI()

    @pytest.fixture
    def client(self, api):
        """Create a test client"""
        app = FastAPI()
        app.include_router(api.router)
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_execute_decision(self, api):
        """Test executing a decision through API"""
        # Mock the engine
        mock_result = Mock()
        mock_result.decision = "approved"
        mock_result.confidence = 0.95
        mock_result.reasoning = "Test reasoning"
        mock_result.metadata = {}

        with patch.object(api.engine, "execute", return_value=mock_result):
            request = DecisionRequest(
                function_id="test_function",
                input_data={"amount": 1000},
                version="1.0.0",
            )

            result = await api.execute_decision(request)

            assert result.decision == "approved"
            assert result.confidence == 0.95

    @pytest.mark.asyncio
    async def test_execute_decision_error(self, api):
        """Test executing a decision with error"""
        with patch.object(api.engine, "execute", side_effect=Exception("Test error")):
            request = DecisionRequest(
                function_id="test_function",
                input_data={"amount": 1000},
                version="1.0.0",
            )

            with pytest.raises(Exception):
                await api.execute_decision(request)

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAuditService:
    """Test AuditService functionality"""

    @pytest.fixture
    def audit_service(self):
        """Create a test audit service"""
        return AuditService()

    @pytest.mark.asyncio
    async def test_run_audit(self, audit_service):
        """Test running an audit"""
        with patch.object(audit_service, "_verify_traces", return_value=True):
            result = await audit_service.run_audit()

            assert result.status == "completed"
            assert result.success_count >= 0

    @pytest.mark.asyncio
    async def test_generate_report(self, audit_service):
        """Test generating an audit report"""
        report = await audit_service.generate_report()

        assert isinstance(report, AuditReport)
        assert report.timestamp is not None
        assert report.summary is not None


class TestAPIIntegration:
    """Test API integration scenarios"""

    @pytest.fixture
    def api_client(self):
        """Create API client for integration tests"""
        api = DecisionLayerAPI()
        app = FastAPI()
        app.include_router(api.router)
        return TestClient(app)

    def test_complete_api_workflow(self, api_client):
        """Test complete API workflow"""
        # Register a function
        function_data = {
            "function_id": "test_function",
            "version": "1.0.0",
            "function_code": "async def test_func(input_data, context): return {'decision': 'approved'}",
            "metadata": {"author": "test_user"},
        }

        response = api_client.post("/functions/register", json=function_data)
        assert response.status_code == 200

        # Execute the function
        execution_data = {
            "function_id": "test_function",
            "input_data": {"amount": 1000},
            "version": "1.0.0",
        }

        response = api_client.post("/decisions/execute", json=execution_data)
        assert response.status_code == 200

        # Get audit report
        response = api_client.get("/audit/report/latest")
        assert response.status_code == 200


class TestErrorHandling:
    """Test API error handling"""

    @pytest.fixture
    def api_client(self):
        """Create API client for error testing"""
        api = DecisionLayerAPI()
        app = FastAPI()
        app.include_router(api.router)
        return TestClient(app)

    def test_invalid_function_id(self, api_client):
        """Test handling invalid function ID"""
        execution_data = {
            "function_id": "nonexistent_function",
            "input_data": {"amount": 1000},
            "version": "1.0.0",
        }

        response = api_client.post("/decisions/execute", json=execution_data)
        assert response.status_code == 404

    def test_invalid_input_data(self, api_client):
        """Test handling invalid input data"""
        execution_data = {
            "function_id": "test_function",
            "input_data": "invalid_data",  # Should be dict
            "version": "1.0.0",
        }

        response = api_client.post("/decisions/execute", json=execution_data)
        assert response.status_code == 422  # Validation error


class TestPerformance:
    """Test API performance"""

    @pytest.fixture
    def api_client(self):
        """Create API client for performance testing"""
        api = DecisionLayerAPI()
        app = FastAPI()
        app.include_router(api.router)
        return TestClient(app)

    def test_concurrent_requests(self, api_client):
        """Test handling concurrent requests"""
        import threading
        import time

        results = []

        def make_request():
            execution_data = {
                "function_id": "test_function",
                "input_data": {"amount": 1000},
                "version": "1.0.0",
            }
            response = api_client.post("/decisions/execute", json=execution_data)
            results.append(response.status_code)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10
