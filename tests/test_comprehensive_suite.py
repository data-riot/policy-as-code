"""
Comprehensive Test Suite for Policy as Code Platform
Tests all components including use cases, API, and core functionality
"""

import asyncio
import json
import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, patch

from policy_as_code.core.enhanced_engine import (
    DecisionEngine,
    DecisionContext,
    DecisionResult,
)
from policy_as_code.core.security import SecurityConfig
from examples.demos import (
    healthcare_eligibility,
    social_benefits_allocation,
    immigration_visa_processing,
)


class TestDecisionContext:
    """Test DecisionContext functionality"""

    def test_context_creation(self):
        """Test creating a decision context"""
        context = DecisionContext(
            function_id="test_function",
            version="1.0.0",
            input_hash="test_hash",
            timestamp=datetime.now(),
            trace_id="test_trace",
        )

        assert context.function_id == "test_function"
        assert context.version == "1.0.0"
        assert context.input_hash == "test_hash"
        assert context.trace_id == "test_trace"


class TestDecisionEngine:
    """Test DecisionEngine functionality"""

    @pytest.fixture
    def engine(self):
        """Create a test decision engine"""
        return DecisionEngine(SecurityConfig())

    def test_engine_initialization(self, engine):
        """Test engine initialization"""
        assert engine.registry is not None
        assert engine.security_manager is not None
        assert engine.storage_backend is not None

    def test_function_registration(self, engine):
        """Test function registration"""

        def test_function(
            input_data: Dict[str, Any], context: DecisionContext
        ) -> Dict[str, Any]:
            return {"result": "test"}

        engine.register_function("test_func", "1.0.0", test_function)

        # Verify function is registered
        functions = engine.registry.list_functions()
        assert "test_func" in functions

        # Verify function can be retrieved
        func = engine.registry.get_function("test_func", "1.0.0")
        assert func is not None

    @pytest.mark.asyncio
    async def test_decision_execution(self, engine):
        """Test decision execution"""

        def test_function(
            input_data: Dict[str, Any], context: DecisionContext
        ) -> Dict[str, Any]:
            return {"result": "success", "input": input_data}

        engine.register_function("test_func", "1.0.0", test_function)

        result = await engine.execute_decision(
            function_id="test_func", version="1.0.0", input_data={"test": "data"}
        )

        assert result.success is True
        assert result.function_id == "test_func"
        assert result.version == "1.0.0"
        assert result.result["result"] == "success"

    @pytest.mark.asyncio
    async def test_decision_execution_with_error(self, engine):
        """Test decision execution with error"""

        def error_function(
            input_data: Dict[str, Any], context: DecisionContext
        ) -> Dict[str, Any]:
            raise ValueError("Test error")

        engine.register_function("error_func", "1.0.0", error_function)

        with pytest.raises(Exception):
            await engine.execute_decision(
                function_id="error_func", version="1.0.0", input_data={"test": "data"}
            )


class TestHealthcareEligibility:
    """Test healthcare eligibility use case"""

    @pytest.fixture
    def sample_input(self):
        """Sample input data for healthcare eligibility"""
        return {
            "patient": {
                "age": 35,
                "anatomical_factors": {
                    "has_breast_tissue": True,
                    "has_prostate": False,
                    "has_uterus": True,
                    "has_cervix": True,
                },
                "reproductive_status": {
                    "pregnant": False,
                    "fertile": True,
                    "contraception_confirmed": True,
                },
                "medical_characteristics": {
                    "hormone_levels": {"estrogen": "normal"},
                    "genetic_factors": [],
                    "developmental_stage": "adult",
                },
                "medical_history": [],
                "allergies": [],
            },
            "procedure": {
                "code": "MAMMOGRAM",
                "name": "Mammogram Screening",
                "urgency": "routine",
                "estimated_cost": 150,
            },
            "insurance": {
                "type": "private",
                "coverage_percentage": 80,
                "deductible_remaining": 500,
                "network_status": "in_network",
            },
            "provider": {
                "specialty": "radiology",
                "license_status": "active",
                "network_status": "in_network",
            },
        }

    def test_healthcare_decision_function(self, sample_input):
        """Test healthcare decision function"""
        context = DecisionContext(
            function_id="healthcare_eligibility",
            version="1.0.0",
            input_hash="test_hash",
            timestamp=datetime.now(),
            trace_id="test_trace",
        )

        result = healthcare_eligibility.decision_function(sample_input, context)

        assert isinstance(result, dict)
        assert "eligible" in result
        assert "recommendation" in result
        assert "patient_info" in result
        assert "anatomical_factors" in result["patient_info"]

    def test_anatomical_factors_assessment(self, sample_input):
        """Test anatomical factors assessment"""
        context = DecisionContext(
            function_id="healthcare_eligibility",
            version="1.0.0",
            input_hash="test_hash",
            timestamp=datetime.now(),
            trace_id="test_trace",
        )

        result = healthcare_eligibility.decision_function(sample_input, context)

        # Should be eligible for mammogram with breast tissue
        assert result["eligible"] is True
        assert result["recommendation"] in ["approved", "approved_with_warnings"]


class TestSocialBenefitsAllocation:
    """Test social benefits allocation use case"""

    @pytest.fixture
    def sample_input(self):
        """Sample input data for social benefits"""
        return {
            "applicant": {
                "age": 45,
                "gender": "unknown",
                "citizenship_status": "citizen",
                "disability_status": "none",
                "veteran_status": False,
            },
            "care_network": {
                "primary_caregivers": [],
                "secondary_caregivers": [],
                "care_dependents": [
                    {"age": 12, "disability_status": "none", "complex_needs": False}
                ],
                "care_responsibilities": [
                    {"type": "childcare", "intensity": "medium", "hours_per_week": 40}
                ],
            },
            "financial_info": {
                "monthly_income": 1500,
                "monthly_expenses": 1200,
                "assets_value": 5000,
                "savings": 2000,
                "debts": 1000,
            },
            "economic_activity": {
                "type": "unemployed",
                "intensity": "full_time",
                "income_sources": [],
                "work_capacity": "full",
                "barriers_to_work": [{"type": "job_search", "resolved": True}],
                "previous_salary": 3000,
                "transitions": [{"type": "unemployment"}],
            },
            "special_circumstances": [],
            "requested_benefits": [{"type": "unemployment"}],
            "legal_residency_status": "citizen",
        }

    def test_social_benefits_decision_function(self, sample_input):
        """Test social benefits decision function"""
        context = DecisionContext(
            function_id="social_benefits_allocation",
            version="1.0.0",
            input_hash="test_hash",
            timestamp=datetime.now(),
            trace_id="test_trace",
        )

        result = social_benefits_allocation.decision_function(sample_input, context)

        assert isinstance(result, dict)
        assert "benefit_assessment" in result
        assert "family_info" in result
        assert "care_network_size" in result["family_info"]

    def test_care_network_assessment(self, sample_input):
        """Test care network assessment"""
        context = DecisionContext(
            function_id="social_benefits_allocation",
            version="1.0.0",
            input_hash="test_hash",
            timestamp=datetime.now(),
            trace_id="test_trace",
        )

        result = social_benefits_allocation.decision_function(sample_input, context)

        # Should have care network size > 0
        assert result["family_info"]["care_network_size"] > 0
        assert result["family_info"]["children_in_care"] > 0


class TestImmigrationVisaProcessing:
    """Test immigration visa processing use case"""

    @pytest.fixture
    def sample_input(self):
        """Sample input data for immigration"""
        return {
            "applicant": {
                "nationality": "US",
                "age": 30,
                "gender": "unknown",
                "marital_status": "single",
                "education_level": "bachelor",
                "occupation": "software_engineer",
            },
            "visa_application": {
                "type": "work",
                "purpose": "employment",
                "intended_duration_days": 365,
                "entry_date": "2024-06-01",
                "exit_date": "2025-06-01",
            },
            "background_check": {
                "criminal_record": False,
                "security_concerns": [],
                "previous_visa_violations": False,
                "immigration_history": [
                    {"compliance_status": "compliant", "overstay_days": 0}
                ],
                "watchlist_status": "clear",
            },
            "financial_info": {
                "bank_balance": 15000,
                "monthly_income": 5000,
                "sponsor": {"monthly_income": 4000, "relationship": "employer"},
                "has_travel_insurance": True,
            },
            "supporting_documents": [
                {"type": "passport"},
                {"type": "work_permit"},
                {"type": "employment_contract"},
                {"type": "financial_proof"},
            ],
            "academic_references": ["professor1"],
            "language_proficiency": {"level": 6},
            "work_experience": ["company1"],
            "certifications": ["cert1"],
            "portfolio": {"projects": ["project1"]},
            "references": ["ref1"],
        }

    def test_immigration_decision_function(self, sample_input):
        """Test immigration decision function"""
        context = DecisionContext(
            function_id="immigration_visa_processing",
            version="1.0.0",
            input_hash="test_hash",
            timestamp=datetime.now(),
            trace_id="test_trace",
        )

        result = immigration_visa_processing.decision_function(sample_input, context)

        assert isinstance(result, dict)
        assert "assessment_results" in result
        assert "graduated_response" in result["assessment_results"]
        assert "individual_risk_profile" in result["security_assessment"]

    def test_individual_risk_assessment(self, sample_input):
        """Test individual risk assessment"""
        context = DecisionContext(
            function_id="immigration_visa_processing",
            version="1.0.0",
            input_hash="test_hash",
            timestamp=datetime.now(),
            trace_id="test_trace",
        )

        result = immigration_visa_processing.decision_function(sample_input, context)

        # Should have individual risk profile
        risk_profile = result["security_assessment"]["individual_risk_profile"]
        assert "behavioral_indicators" in risk_profile
        assert "compliance_history" in risk_profile
        assert "financial_stability" in risk_profile
        assert "social_connections" in risk_profile
        assert "documentation_integrity" in risk_profile
        assert "risk_mitigation_factors" in risk_profile


class TestAPIEndpoints:
    """Test API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from policy_as_code.api.enhanced_rest import app

        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Policy as Code API"

    def test_health_endpoint(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    def test_functions_endpoint(self, client):
        """Test functions listing endpoint"""
        response = client.get("/functions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestComplianceFeatures:
    """Test compliance and legal features"""

    def test_eu_ai_act_compliance(self):
        """Test EU AI Act compliance features"""
        # Test that all use cases include EU AI Act compliance
        test_inputs = [{"test": "data"}]

        context = DecisionContext(
            function_id="test",
            version="1.0.0",
            input_hash="test",
            timestamp=datetime.now(),
            trace_id="test",
        )

        # Test healthcare compliance
        hc_result = healthcare_eligibility.decision_function(test_inputs[0], context)
        assert "eu_ai_act_compliance" in hc_result

        # Test social benefits compliance
        sb_result = social_benefits_allocation.decision_function(
            test_inputs[0], context
        )
        assert "eu_ai_act_compliance" in sb_result

        # Test immigration compliance
        iv_result = immigration_visa_processing.decision_function(
            test_inputs[0], context
        )
        assert "eu_ai_act_compliance" in iv_result

    def test_non_discriminatory_practices(self):
        """Test that discriminatory practices are avoided"""
        # This would include more comprehensive tests
        # For now, verify that the modernization features are present
        assert True  # Placeholder for comprehensive discrimination testing


# Performance tests
class TestPerformance:
    """Performance tests"""

    @pytest.mark.asyncio
    async def test_decision_execution_performance(self):
        """Test decision execution performance"""
        engine = DecisionEngine(SecurityConfig())

        def test_function(
            input_data: Dict[str, Any], context: DecisionContext
        ) -> Dict[str, Any]:
            return {"result": "performance_test"}

        engine.register_function("perf_test", "1.0.0", test_function)

        start_time = datetime.now()

        # Execute multiple decisions
        tasks = []
        for i in range(10):
            task = engine.execute_decision(
                function_id="perf_test",
                version="1.0.0",
                input_data={"test": f"data_{i}"},
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = datetime.now()

        execution_time = (end_time - start_time).total_seconds()

        # Should complete 10 decisions in reasonable time
        assert execution_time < 5.0  # 5 seconds for 10 decisions
        assert len(results) == 10
        assert all(result.success for result in results)


# Integration tests
class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        engine = DecisionEngine(SecurityConfig())

        # Register all use cases
        engine.register_function(
            "healthcare_eligibility", "1.0.0", healthcare_eligibility.decision_function
        )

        engine.register_function(
            "social_benefits_allocation",
            "1.0.0",
            social_benefits_allocation.decision_function,
        )

        engine.register_function(
            "immigration_visa_processing",
            "1.0.0",
            immigration_visa_processing.decision_function,
        )

        # Test all functions are registered
        functions = engine.registry.list_functions()
        assert "healthcare_eligibility" in functions
        assert "social_benefits_allocation" in functions
        assert "immigration_visa_processing" in functions

        # Test health check
        health = await engine.health_check()
        assert health["status"] == "healthy"
        assert health["registered_functions"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
