"""
Comprehensive test suite for bulletproof decision flow
Tests strict Pydantic validation and end-to-end decision flow
"""

import asyncio
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pytest
from pydantic import ValidationError

from policy_as_code.core.bulletproof_flow import BulletproofDecisionFlow
from policy_as_code.validation.strict_models import (
    EligibilityInput,
    EligibilityOutput,
    DecisionOutcome,
    PersonId,
    PersonIdType,
    Income,
    IncomeSource,
    Residence,
    ResidenceStatus,
    Family,
    Dependent,
    RelationshipType,
    EconomicActivity,
    EmploymentStatus,
    WorkCapacity,
    WorkBarrier,
    validate_eligibility_input,
    validate_eligibility_output,
)


class TestStrictValidation:
    """Test strict Pydantic validation models"""

    def test_valid_eligibility_input(self):
        """Test valid eligibility input passes validation"""
        valid_input = {
            "person_id": {
                "id": "010190-123A",
                "type": "hetu",
                "verified": True,
                "verification_date": "2024-01-01T00:00:00Z",
            },
            "income": {
                "monthly_net_eur": 2500.0,
                "source": "vero",
                "verification_status": "verified",
                "verification_date": "2024-01-01T00:00:00Z",
                "tax_year": 2024,
            },
            "residence": {
                "municipality_code": "091",
                "residence_status": "citizen",
                "address": "Testikatu 1, 00100 Helsinki",
                "postal_code": "00100",
            },
        }

        result = validate_eligibility_input(valid_input)
        assert result.is_valid
        assert result.validated_data is not None

        # Test Pydantic model creation
        eligibility_input = EligibilityInput(**valid_input)
        assert eligibility_input.person_id.id == "010190-123A"
        assert eligibility_input.income.monthly_net_eur == 2500.0

    def test_invalid_eligibility_input(self):
        """Test invalid eligibility input fails validation"""
        invalid_input = {
            "person_id": {
                "id": "invalid_id",  # Invalid HETU format
                "type": "hetu",
                "verified": True,
            },
            "income": {
                "monthly_net_eur": -100.0,  # Negative income
                "source": "invalid_source",  # Invalid source
            },
            "residence": {
                "municipality_code": "invalid",  # Invalid municipality code
                "residence_status": "invalid_status",  # Invalid status
            },
        }

        result = validate_eligibility_input(invalid_input)
        assert not result.is_valid
        assert len(result.errors) > 0

        # Check specific error types
        error_fields = [error["field"] for error in result.errors]
        assert "person_id.id" in error_fields
        assert "income.monthly_net_eur" in error_fields
        assert "income.source" in error_fields
        assert "residence.municipality_code" in error_fields
        assert "residence.residence_status" in error_fields

    def test_valid_eligibility_output(self):
        """Test valid eligibility output passes validation"""
        valid_output = {
            "decision": "APPROVED",
            "basis": {
                "rule": "income_threshold_met",
                "thresholds": {"min_income": 2000},
                "criteria_met": ["income_verified", "residence_confirmed"],
                "criteria_not_met": [],
            },
            "legal_basis": [
                {
                    "law_reference": "https://finlex.fi/fi/laki/ajantasa/2021/20210001",
                    "section": "5 §",
                    "description": "Income threshold for eligibility",
                }
            ],
            "reasoning": [
                "Applicant income exceeds minimum threshold",
                "Residence status confirmed as citizen",
                "All eligibility criteria met",
            ],
            "confidence_score": 0.95,
        }

        result = validate_eligibility_output(valid_output)
        assert result.is_valid
        assert result.validated_data is not None

        # Test Pydantic model creation
        eligibility_output = EligibilityOutput(**valid_output)
        assert eligibility_output.decision == DecisionOutcome.APPROVED
        assert eligibility_output.confidence_score == 0.95

    def test_invalid_eligibility_output(self):
        """Test invalid eligibility output fails validation"""
        invalid_output = {
            "decision": "INVALID_DECISION",  # Invalid decision
            "basis": {"rule": "test_rule"},
            "legal_basis": [],  # Empty legal basis (should have at least 1)
            "reasoning": [],  # Empty reasoning (should have at least 1)
            "confidence_score": 1.5,  # Invalid confidence score (> 1.0)
        }

        result = validate_eligibility_output(invalid_output)
        assert not result.is_valid
        assert len(result.errors) > 0

        # Check specific error types
        error_fields = [error["field"] for error in result.errors]
        assert "decision" in error_fields
        assert "legal_basis" in error_fields
        assert "reasoning" in error_fields
        assert "confidence_score" in error_fields

    def test_person_id_validation(self):
        """Test person ID validation with different types"""
        # Valid HETU
        hetu = PersonId(id="010190-123A", type=PersonIdType.HETU)
        assert hetu.id == "010190-123A"
        assert hetu.type == PersonIdType.HETU

        # Valid VTJ ID
        vtj = PersonId(id="VTJ_123456", type=PersonIdType.VTJ)
        assert vtj.id == "VTJ_123456"
        assert vtj.type == PersonIdType.VTJ

        # Invalid HETU format
        with pytest.raises(ValidationError):
            PersonId(id="invalid", type=PersonIdType.HETU)

    def test_income_validation(self):
        """Test income validation"""
        # Valid income
        income = Income(
            monthly_net_eur=2500.0,
            source=IncomeSource.VERO,
            verification_status="verified",
        )
        assert income.monthly_net_eur == 2500.0
        assert income.source == IncomeSource.VERO

        # Invalid income (negative)
        with pytest.raises(ValidationError):
            Income(monthly_net_eur=-100.0, source=IncomeSource.VERO)

        # Invalid income (too high)
        with pytest.raises(ValidationError):
            Income(monthly_net_eur=2000000.0, source=IncomeSource.VERO)

    def test_residence_validation(self):
        """Test residence validation"""
        # Valid residence
        residence = Residence(
            municipality_code="091", residence_status=ResidenceStatus.CITIZEN
        )
        assert residence.municipality_code == "091"
        assert residence.residence_status == ResidenceStatus.CITIZEN

        # Invalid municipality code
        with pytest.raises(ValidationError):
            Residence(
                municipality_code="invalid", residence_status=ResidenceStatus.CITIZEN
            )

    def test_family_validation(self):
        """Test family validation"""
        # Valid family
        family = Family(
            dependents=[
                Dependent(id="child_1", relationship=RelationshipType.CHILD, age=5)
            ],
            household_size=2,
        )
        assert len(family.dependents) == 1
        assert family.household_size == 2

        # Invalid household size (too small)
        with pytest.raises(ValidationError):
            Family(
                dependents=[
                    Dependent(id="child_1", relationship=RelationshipType.CHILD, age=5)
                ],
                household_size=1,  # Should be at least 2 (1 parent + 1 child)
            )


class TestBulletproofFlow:
    """Test bulletproof decision flow"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def flow(self, temp_dir):
        """Create bulletproof flow instance"""
        return BulletproofDecisionFlow(
            storage_path=temp_dir, enable_audit=True, enable_signing=True
        )

    @pytest.fixture
    def sample_policy(self):
        """Sample policy function for testing"""

        async def eligibility_policy(input_data: Dict[str, Any]) -> Dict[str, Any]:
            """Sample eligibility policy"""
            income = input_data.get("income", {}).get("monthly_net_eur", 0)

            if income >= 2000:
                return {
                    "decision": "APPROVED",
                    "basis": {
                        "rule": "income_threshold_met",
                        "thresholds": {"min_income": 2000},
                        "criteria_met": ["income_verified"],
                        "criteria_not_met": [],
                    },
                    "legal_basis": [
                        {
                            "law_reference": "https://finlex.fi/fi/laki/ajantasa/2021/20210001",
                            "section": "5 §",
                            "description": "Income threshold for eligibility",
                        }
                    ],
                    "reasoning": [
                        "Applicant income exceeds minimum threshold",
                        "All eligibility criteria met",
                    ],
                    "confidence_score": 0.9,
                }
            else:
                return {
                    "decision": "DENIED",
                    "basis": {
                        "rule": "income_threshold_not_met",
                        "thresholds": {"min_income": 2000},
                        "criteria_met": [],
                        "criteria_not_met": ["income_insufficient"],
                    },
                    "legal_basis": [
                        {
                            "law_reference": "https://finlex.fi/fi/laki/ajantasa/2021/20210001",
                            "section": "5 §",
                            "description": "Income threshold for eligibility",
                        }
                    ],
                    "reasoning": [
                        "Applicant income below minimum threshold",
                        "Eligibility criteria not met",
                    ],
                    "confidence_score": 0.95,
                }

        return eligibility_policy

    @pytest.mark.asyncio
    async def test_successful_decision_flow(self, flow, sample_policy):
        """Test successful end-to-end decision flow"""
        # Register policy
        flow.register_policy(
            "eligibility_check",
            "1.0.0",
            sample_policy,
            {"description": "Basic eligibility check"},
        )

        # Valid input data
        input_data = {
            "person_id": {
                "id": "010190-123A",
                "type": "hetu",
                "verified": True,
                "verification_date": "2024-01-01T00:00:00Z",
            },
            "income": {
                "monthly_net_eur": 2500.0,
                "source": "vero",
                "verification_status": "verified",
                "verification_date": "2024-01-01T00:00:00Z",
                "tax_year": 2024,
            },
            "residence": {"municipality_code": "091", "residence_status": "citizen"},
        }

        # Execute decision
        result = await flow.execute_decision(
            "eligibility_check",
            "1.0.0",
            input_data,
            client_id="test_client",
            request_id="test_request",
        )

        # Verify result
        assert result["success"] is True
        assert "trace_id" in result
        assert result["decision"]["decision"] == "APPROVED"
        assert result["validation"]["input_valid"] is True
        assert result["validation"]["output_valid"] is True
        assert result["audit"]["audit_persisted"] is True
        assert result["audit"]["signature_valid"] is True

        # Verify trace file exists
        trace_file = Path(flow.storage_path) / "traces" / f"{result['trace_id']}.json"
        assert trace_file.exists()

        # Verify audit file exists
        audit_file = (
            Path(flow.storage_path) / "audit" / f"audit_{result['trace_id']}.json"
        )
        assert audit_file.exists()

    @pytest.mark.asyncio
    async def test_invalid_input_validation(self, flow, sample_policy):
        """Test flow with invalid input data"""
        # Register policy
        flow.register_policy("eligibility_check", "1.0.0", sample_policy)

        # Invalid input data
        invalid_input = {
            "person_id": {"id": "invalid_id", "type": "hetu"},  # Invalid HETU
            "income": {
                "monthly_net_eur": -100.0,  # Negative income
                "source": "invalid_source",
            },
            "residence": {
                "municipality_code": "invalid",
                "residence_status": "invalid_status",
            },
        }

        # Execute decision
        result = await flow.execute_decision(
            "eligibility_check", "1.0.0", invalid_input
        )

        # Verify result
        assert result["success"] is False
        assert result["error"]["type"] == "ValidationError"
        assert result["validation"]["input_valid"] is False
        assert len(result["validation"]["input_errors"]) > 0

    @pytest.mark.asyncio
    async def test_policy_not_found(self, flow):
        """Test flow with non-existent policy"""
        input_data = {
            "person_id": {"id": "010190-123A", "type": "hetu"},
            "income": {"monthly_net_eur": 2500.0, "source": "vero"},
            "residence": {"municipality_code": "091", "residence_status": "citizen"},
        }

        # Execute decision with non-existent policy
        result = await flow.execute_decision("non_existent_policy", "1.0.0", input_data)

        # Verify result
        assert result["success"] is False
        assert result["error"]["type"] == "ValidationError"
        assert "not found" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_trace_integrity(self, flow, sample_policy):
        """Test trace chain integrity"""
        # Register policy
        flow.register_policy("eligibility_check", "1.0.0", sample_policy)

        # Execute multiple decisions
        for i in range(3):
            input_data = {
                "person_id": {"id": f"010190-12{i}A", "type": "hetu"},
                "income": {"monthly_net_eur": 2500.0 + i * 100, "source": "vero"},
                "residence": {
                    "municipality_code": "091",
                    "residence_status": "citizen",
                },
            }

            result = await flow.execute_decision(
                "eligibility_check", "1.0.0", input_data
            )
            assert result["success"] is True

        # Verify trace integrity
        integrity = flow.verify_trace_integrity()
        assert integrity["integrity_ok"] is True
        assert integrity["total_traces"] == 3

    @pytest.mark.asyncio
    async def test_audit_log(self, flow, sample_policy):
        """Test audit logging"""
        # Register policy
        flow.register_policy("eligibility_check", "1.0.0", sample_policy)

        # Execute decision
        input_data = {
            "person_id": {"id": "010190-123A", "type": "hetu"},
            "income": {"monthly_net_eur": 2500.0, "source": "vero"},
            "residence": {"municipality_code": "091", "residence_status": "citizen"},
        }

        result = await flow.execute_decision("eligibility_check", "1.0.0", input_data)

        # Verify audit log
        audit_log = flow.get_audit_log()
        assert len(audit_log) >= 2  # At least policy registration + decision execution

        # Check for policy registration log
        policy_logs = [log for log in audit_log if log["action"] == "policy_registered"]
        assert len(policy_logs) == 1
        assert policy_logs[0]["policy_id"] == "eligibility_check"

        # Check for decision execution log
        decision_logs = [
            log for log in audit_log if "trace_id" in log and log.get("success", False)
        ]
        assert len(decision_logs) == 1
        assert decision_logs[0]["trace_id"] == result["trace_id"]


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_input_validation(self):
        """Test validation with empty input"""
        result = validate_eligibility_input({})
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_malformed_json_validation(self):
        """Test validation with malformed data types"""
        malformed_input = {
            "person_id": {"id": 123, "type": "hetu"},  # Should be string
            "income": {
                "monthly_net_eur": "not_a_number",  # Should be number
                "source": "vero",
            },
        }

        result = validate_eligibility_input(malformed_input)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_boundary_values(self):
        """Test validation with boundary values"""
        # Test minimum valid values
        min_input = {
            "person_id": {"id": "010190-123A", "type": "hetu"},
            "income": {
                "monthly_net_eur": 0.0,  # Minimum valid income
                "source": "vero",
            },
            "residence": {
                "municipality_code": "000",  # Minimum municipality code
                "residence_status": "citizen",
            },
        }

        result = validate_eligibility_input(min_input)
        assert result.is_valid

        # Test maximum valid values
        max_input = {
            "person_id": {"id": "010190-123A", "type": "hetu"},
            "income": {
                "monthly_net_eur": 1000000.0,  # Maximum valid income
                "source": "vero",
            },
            "residence": {
                "municipality_code": "999",  # Maximum municipality code
                "residence_status": "citizen",
            },
        }

        result = validate_eligibility_input(max_input)
        assert result.is_valid


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
