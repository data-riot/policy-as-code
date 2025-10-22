"""
Integration tests for ELI validation in Registry API

These tests ensure that ELI validation works correctly in the Registry API
and protects citizens from decisions based on invalid or non-existent laws.

CITIZEN BENEFIT PERSPECTIVE:
- Ensures that decisions are based on valid laws
- Prevents making illegal decisions
- Enables citizens' legal oversight
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, date
from fastapi.testclient import TestClient

from policy_as_code.api.enhanced_rest import app
from policy_as_code.validation.eli_validator import (
    ELIValidationStatus,
    ELIValidationResult,
)


class TestELIRegistryAPI:
    """Test ELI validation in Registry API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def valid_decision_function_spec(self):
        """Valid decision function specification with ELI reference"""
        return {
            "id": "TEST.DF_001",
            "version": "1.0.0",
            "status": "DRAFT",
            "law_reference": {"eli": "https://finlex.fi/eli/laki/2020/123#Pykala1"},
            "owner": {"ministry_id": "STM", "unit": "Kela"},
            "inputs_schema_ref": "urn:schema:eligibility_input:v1",
            "outputs_schema_ref": "urn:schema:eligibility_output:v1",
            "logic_hash": "sha256:abcd1234",
            "signatures": [
                {"kid": "key1", "role": "owner", "sig": "signature1"},
                {"kid": "key2", "role": "reviewer", "sig": "signature2"},
            ],
            "explain_allow_fields": ["decision", "basis"],
            "invariants": ["output.decision in ['APPROVED','DENIED']"],
        }

    @pytest.fixture
    def invalid_decision_function_spec_no_eli(self):
        """Decision function specification without ELI reference"""
        return {
            "id": "TEST.DF_002",
            "version": "1.0.0",
            "status": "DRAFT",
            "law_reference": {},  # Missing ELI
            "owner": {"ministry_id": "STM", "unit": "Kela"},
            "inputs_schema_ref": "urn:schema:eligibility_input:v1",
            "outputs_schema_ref": "urn:schema:eligibility_output:v1",
            "logic_hash": "sha256:abcd1234",
            "signatures": [
                {"kid": "key1", "role": "owner", "sig": "signature1"},
                {"kid": "key2", "role": "reviewer", "sig": "signature2"},
            ],
            "explain_allow_fields": ["decision", "basis"],
            "invariants": ["output.decision in ['APPROVED','DENIED']"],
        }

    @pytest.fixture
    def invalid_decision_function_spec_bad_eli(self):
        """Decision function specification with invalid ELI reference"""
        return {
            "id": "TEST.DF_003",
            "version": "1.0.0",
            "status": "DRAFT",
            "law_reference": {"eli": "invalid-uri-format"},
            "owner": {"ministry_id": "STM", "unit": "Kela"},
            "inputs_schema_ref": "urn:schema:eligibility_input:v1",
            "outputs_schema_ref": "urn:schema:eligibility_output:v1",
            "logic_hash": "sha256:abcd1234",
            "signatures": [
                {"kid": "key1", "role": "owner", "sig": "signature1"},
                {"kid": "key2", "role": "reviewer", "sig": "signature2"},
            ],
            "explain_allow_fields": ["decision", "basis"],
            "invariants": ["output.decision in ['APPROVED','DENIED']"],
        }

    def test_register_decision_function_missing_eli(
        self, client, invalid_decision_function_spec_no_eli
    ):
        """Test that decision function without ELI reference is rejected"""
        response = client.post(
            "/registry/df",
            json=invalid_decision_function_spec_no_eli,
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 400
        assert (
            "Decision function must have law_reference.eli" in response.json()["detail"]
        )

    def test_register_decision_function_invalid_eli_format(
        self, client, invalid_decision_function_spec_bad_eli
    ):
        """Test that decision function with invalid ELI format is rejected"""
        with patch(
            "policy_as_code.validation.eli_validator.validate_decision_function_eli"
        ) as mock_validate:
            mock_validate.return_value = {
                "invalid-uri-format": ELIValidationResult(
                    status=ELIValidationStatus.INVALID_FORMAT,
                    eli_uri="invalid-uri-format",
                    error_message="Invalid ELI URI format. Expected: https://finlex.fi/eli/laki/YYYY/NUMBER#SECTION",
                )
            }

            response = client.post(
                "/registry/df",
                json=invalid_decision_function_spec_bad_eli,
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 400
            assert "ELI validation failed" in response.json()["detail"]
            assert "Invalid ELI URI format" in response.json()["detail"]

    def test_register_decision_function_law_not_found(
        self, client, valid_decision_function_spec
    ):
        """Test that decision function with non-existent law is rejected"""
        with patch(
            "policy_as_code.validation.eli_validator.validate_decision_function_eli"
        ) as mock_validate:
            mock_validate.return_value = {
                "https://finlex.fi/eli/laki/2020/123#Pykala1": ELIValidationResult(
                    status=ELIValidationStatus.LAW_NOT_FOUND,
                    eli_uri="https://finlex.fi/eli/laki/2020/123#Pykala1",
                    law_year=2020,
                    law_number=123,
                    error_message="Law 2020/123 not found in Finlex",
                )
            }

            response = client.post(
                "/registry/df",
                json=valid_decision_function_spec,
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 400
            assert "ELI validation failed" in response.json()["detail"]
            assert "Law 2020/123 not found in Finlex" in response.json()["detail"]

    def test_register_decision_function_section_not_found(
        self, client, valid_decision_function_spec
    ):
        """Test that decision function with non-existent section is rejected"""
        with patch(
            "policy_as_code.validation.eli_validator.validate_decision_function_eli"
        ) as mock_validate:
            mock_validate.return_value = {
                "https://finlex.fi/eli/laki/2020/123#Pykala1": ELIValidationResult(
                    status=ELIValidationStatus.SECTION_NOT_FOUND,
                    eli_uri="https://finlex.fi/eli/laki/2020/123#Pykala1",
                    law_year=2020,
                    law_number=123,
                    section="Pykala1",
                    law_title="Test Law",
                    error_message="Section 'Pykala1' not found in law 2020/123",
                )
            }

            response = client.post(
                "/registry/df",
                json=valid_decision_function_spec,
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 400
            assert "ELI validation failed" in response.json()["detail"]
            assert "Section 'Pykala1' not found" in response.json()["detail"]

    def test_register_decision_function_law_expired(
        self, client, valid_decision_function_spec
    ):
        """Test that decision function with expired law is rejected"""
        with patch(
            "policy_as_code.validation.eli_validator.validate_decision_function_eli"
        ) as mock_validate:
            mock_validate.return_value = {
                "https://finlex.fi/eli/laki/2020/123#Pykala1": ELIValidationResult(
                    status=ELIValidationStatus.LAW_EXPIRED,
                    eli_uri="https://finlex.fi/eli/laki/2020/123#Pykala1",
                    law_year=2020,
                    law_number=123,
                    section="Pykala1",
                    law_title="Expired Law",
                    effective_date=date(2020, 1, 1),
                    expiry_date=date(2022, 12, 31),
                    error_message="Law 2020/123 is not currently effective",
                )
            }

            response = client.post(
                "/registry/df",
                json=valid_decision_function_spec,
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 400
            assert "ELI validation failed" in response.json()["detail"]
            assert "not currently effective" in response.json()["detail"]

    def test_register_decision_function_valid_eli(
        self, client, valid_decision_function_spec
    ):
        """Test that decision function with valid ELI reference is accepted"""
        with patch(
            "policy_as_code.validation.eli_validator.validate_decision_function_eli"
        ) as mock_validate:
            mock_validate.return_value = {
                "https://finlex.fi/eli/laki/2020/123#Pykala1": ELIValidationResult(
                    status=ELIValidationStatus.VALID,
                    eli_uri="https://finlex.fi/eli/laki/2020/123#Pykala1",
                    law_year=2020,
                    law_number=123,
                    section="Pykala1",
                    law_title="Valid Law",
                    effective_date=date(2020, 1, 1),
                )
            }

            with patch(
                "policy_as_code.api.enhanced_rest.decision_engine"
            ) as mock_engine:
                mock_engine.storage_backend.store_function_spec.return_value = None

                response = client.post(
                    "/registry/df",
                    json=valid_decision_function_spec,
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 200
                assert "Decision function registered" in response.json()["message"]

    def test_create_release_missing_eli(self, client):
        """Test that release creation without ELI reference is rejected"""
        release_request = {
            "df_id": "TEST.DF_001",
            "version": "1.0.0",
            "effective_from": "2024-01-01T00:00:00Z",
            "signatures": [
                {
                    "signer_id": "signer1",
                    "role": "owner",
                    "signature": "sig1",
                    "timestamp": "2024-01-01T00:00:00Z",
                },
                {
                    "signer_id": "signer2",
                    "role": "reviewer",
                    "signature": "sig2",
                    "timestamp": "2024-01-01T00:00:00Z",
                },
            ],
            "change_summary": "Test release",
        }

        with patch("policy_as_code.api.enhanced_rest.decision_engine") as mock_engine:
            mock_engine.storage_backend.retrieve_function_spec.return_value = {
                "id": "TEST.DF_001",
                "version": "1.0.0",
                "law_reference": {},  # Missing ELI
            }

            response = client.post(
                "/registry/releases",
                json=release_request,
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 400
            assert (
                "Decision function must have law_reference.eli"
                in response.json()["detail"]
            )

    def test_create_release_invalid_eli(self, client):
        """Test that release creation with invalid ELI is rejected"""
        release_request = {
            "df_id": "TEST.DF_001",
            "version": "1.0.0",
            "effective_from": "2024-01-01T00:00:00Z",
            "signatures": [
                {
                    "signer_id": "signer1",
                    "role": "owner",
                    "signature": "sig1",
                    "timestamp": "2024-01-01T00:00:00Z",
                },
                {
                    "signer_id": "signer2",
                    "role": "reviewer",
                    "signature": "sig2",
                    "timestamp": "2024-01-01T00:00:00Z",
                },
            ],
            "change_summary": "Test release",
        }

        with patch("policy_as_code.api.enhanced_rest.decision_engine") as mock_engine:
            mock_engine.storage_backend.retrieve_function_spec.return_value = {
                "id": "TEST.DF_001",
                "version": "1.0.0",
                "law_reference": {"eli": "invalid-uri-format"},
            }

            with patch(
                "policy_as_code.validation.eli_validator.validate_decision_function_eli"
            ) as mock_validate:
                mock_validate.return_value = {
                    "invalid-uri-format": ELIValidationResult(
                        status=ELIValidationStatus.INVALID_FORMAT,
                        eli_uri="invalid-uri-format",
                        error_message="Invalid ELI URI format",
                    )
                }

                response = client.post(
                    "/registry/releases",
                    json=release_request,
                    headers={"Authorization": "Bearer test-token"},
                )

                assert response.status_code == 400
                assert "ELI validation failed" in response.json()["detail"]


class TestELIValidationAPI:
    """Test ELI validation API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_validate_single_eli_reference(self, client):
        """Test single ELI reference validation endpoint"""
        with patch(
            "policy_as_code.validation.eli_validator.validate_eli_reference"
        ) as mock_validate:
            mock_validate.return_value = ELIValidationResult(
                status=ELIValidationStatus.VALID,
                eli_uri="https://finlex.fi/eli/laki/2020/123#Pykala1",
                law_year=2020,
                law_number=123,
                section="Pykala1",
                law_title="Valid Law",
                effective_date=date(2020, 1, 1),
                validated_at=datetime(2024, 1, 1, 12, 0, 0),
            )

            response = client.post(
                "/validation/eli",
                params={"eli_uri": "https://finlex.fi/eli/laki/2020/123#Pykala1"},
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["eli_uri"] == "https://finlex.fi/eli/laki/2020/123#Pykala1"
            assert data["status"] == "valid"
            assert data["law_year"] == 2020
            assert data["law_number"] == 123
            assert data["section"] == "Pykala1"
            assert data["law_title"] == "Valid Law"
            assert data["effective_date"] == "2020-01-01"

    def test_validate_single_eli_reference_invalid(self, client):
        """Test single ELI reference validation with invalid URI"""
        with patch(
            "policy_as_code.validation.eli_validator.validate_eli_reference"
        ) as mock_validate:
            mock_validate.return_value = ELIValidationResult(
                status=ELIValidationStatus.INVALID_FORMAT,
                eli_uri="invalid-uri",
                error_message="Invalid ELI URI format",
                validated_at=datetime(2024, 1, 1, 12, 0, 0),
            )

            response = client.post(
                "/validation/eli",
                params={"eli_uri": "invalid-uri"},
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["eli_uri"] == "invalid-uri"
            assert data["status"] == "invalid_format"
            assert data["error_message"] == "Invalid ELI URI format"

    def test_validate_batch_eli_references(self, client):
        """Test batch ELI reference validation endpoint"""
        eli_uris = [
            "https://finlex.fi/eli/laki/2020/123#Pykala1",
            "https://finlex.fi/eli/laki/2020/456#Pykala2",
            "invalid-uri",
        ]

        with patch(
            "policy_as_code.validation.eli_validator.ELIValidator"
        ) as mock_validator_class:
            mock_validator = AsyncMock()
            mock_validator_class.return_value.__aenter__.return_value = mock_validator

            # Mock validation results
            mock_results = {
                "https://finlex.fi/eli/laki/2020/123#Pykala1": ELIValidationResult(
                    status=ELIValidationStatus.VALID,
                    eli_uri="https://finlex.fi/eli/laki/2020/123#Pykala1",
                    law_year=2020,
                    law_number=123,
                    section="Pykala1",
                    law_title="Valid Law 1",
                    effective_date=date(2020, 1, 1),
                    validated_at=datetime(2024, 1, 1, 12, 0, 0),
                ),
                "https://finlex.fi/eli/laki/2020/456#Pykala2": ELIValidationResult(
                    status=ELIValidationStatus.VALID,
                    eli_uri="https://finlex.fi/eli/laki/2020/456#Pykala2",
                    law_year=2020,
                    law_number=456,
                    section="Pykala2",
                    law_title="Valid Law 2",
                    effective_date=date(2020, 1, 1),
                    validated_at=datetime(2024, 1, 1, 12, 0, 0),
                ),
                "invalid-uri": ELIValidationResult(
                    status=ELIValidationStatus.INVALID_FORMAT,
                    eli_uri="invalid-uri",
                    error_message="Invalid ELI URI format",
                    validated_at=datetime(2024, 1, 1, 12, 0, 0),
                ),
            }

            async def mock_validate_eli(uri):
                return mock_results[uri]

            mock_validator.validate_eli.side_effect = mock_validate_eli
            mock_validator.get_validation_summary.return_value = {
                "total_references": 3,
                "valid_references": 2,
                "invalid_references": 1,
                "validation_rate": 2 / 3,
                "status_breakdown": {"valid": 2, "invalid_format": 1},
                "all_valid": False,
            }

            response = client.post(
                "/validation/eli/batch",
                json=eli_uris,
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 3
            assert data["summary"]["total_references"] == 3
            assert data["summary"]["valid_references"] == 2
            assert data["summary"]["invalid_references"] == 1
            assert data["summary"]["validation_rate"] == 2 / 3
            assert not data["summary"]["all_valid"]


class TestELIValidationErrorHandling:
    """Test ELI validation error handling"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_eli_validation_service_error(self, client):
        """Test handling of ELI validation service errors"""
        with patch(
            "policy_as_code.validation.eli_validator.validate_decision_function_eli"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Network error")

            spec = {
                "id": "TEST.DF_001",
                "version": "1.0.0",
                "status": "DRAFT",
                "law_reference": {"eli": "https://finlex.fi/eli/laki/2020/123#Pykala1"},
                "owner": {"ministry_id": "STM", "unit": "Kela"},
                "inputs_schema_ref": "urn:schema:eligibility_input:v1",
                "outputs_schema_ref": "urn:schema:eligibility_output:v1",
                "logic_hash": "sha256:abcd1234",
                "signatures": [
                    {"kid": "key1", "role": "owner", "sig": "signature1"},
                    {"kid": "key2", "role": "reviewer", "sig": "signature2"},
                ],
                "explain_allow_fields": ["decision", "basis"],
                "invariants": ["output.decision in ['APPROVED','DENIED']"],
            }

            response = client.post(
                "/registry/df",
                json=spec,
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 500
            assert "ELI validation service error" in response.json()["detail"]
            assert "Network error" in response.json()["detail"]

    def test_eli_validation_timeout(self, client):
        """Test handling of ELI validation timeout"""
        with patch(
            "policy_as_code.validation.eli_validator.validate_decision_function_eli"
        ) as mock_validate:
            mock_validate.side_effect = asyncio.TimeoutError("Request timeout")

            spec = {
                "id": "TEST.DF_001",
                "version": "1.0.0",
                "status": "DRAFT",
                "law_reference": {"eli": "https://finlex.fi/eli/laki/2020/123#Pykala1"},
                "owner": {"ministry_id": "STM", "unit": "Kela"},
                "inputs_schema_ref": "urn:schema:eligibility_input:v1",
                "outputs_schema_ref": "urn:schema:eligibility_output:v1",
                "logic_hash": "sha256:abcd1234",
                "signatures": [
                    {"kid": "key1", "role": "owner", "sig": "signature1"},
                    {"kid": "key2", "role": "reviewer", "sig": "signature2"},
                ],
                "explain_allow_fields": ["decision", "basis"],
                "invariants": ["output.decision in ['APPROVED','DENIED']"],
            }

            response = client.post(
                "/registry/df",
                json=spec,
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 500
            assert "ELI validation service error" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__])
