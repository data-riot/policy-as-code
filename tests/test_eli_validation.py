"""
Tests for ELI (European Legislation Identifier) validation

These tests ensure that ELI validation works correctly and protects
citizens from decisions based on invalid or non-existent laws.

CITIZEN BENEFIT PERSPECTIVE:
- Ensures that decisions are based on valid laws
- Prevents making illegal decisions
- Enables citizens' legal oversight
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime

from policy_as_code.validation.eli_validator import (
    ELIValidator,
    ELIValidationStatus,
    ELIValidationResult,
    validate_eli_reference,
    validate_decision_function_eli,
)


class TestELIValidator:
    """Test ELI validator functionality"""

    @pytest.fixture
    def validator(self):
        """Create ELI validator instance"""
        return ELIValidator()

    def test_parse_valid_eli_uri(self, validator):
        """Test parsing valid ELI URI"""
        year, number, section = validator._parse_eli_uri(
            "https://finlex.fi/eli/laki/2023/123#Pykala4"
        )
        assert year == 2023
        assert number == 123
        assert section == "Pykala4"

    def test_parse_eli_uri_without_section(self, validator):
        """Test parsing ELI URI without section"""
        year, number, section = validator._parse_eli_uri(
            "https://finlex.fi/eli/laki/2023/123"
        )
        assert year == 2023
        assert number == 123
        assert section is None

    def test_parse_invalid_eli_uri(self, validator):
        """Test parsing invalid ELI URI"""
        year, number, section = validator._parse_eli_uri("invalid-uri")
        assert year is None
        assert number is None
        assert section is None

    def test_parse_wrong_domain_eli_uri(self, validator):
        """Test parsing ELI URI with wrong domain"""
        year, number, section = validator._parse_eli_uri(
            "https://example.com/eli/laki/2023/123"
        )
        assert year is None
        assert number is None
        assert section is None

    @pytest.mark.asyncio
    async def test_validate_invalid_format(self, validator):
        """Test validation of invalid ELI format"""
        result = await validator.validate_eli("invalid-uri")

        assert result.status == ELIValidationStatus.INVALID_FORMAT
        assert result.eli_uri == "invalid-uri"
        assert "Invalid ELI URI format" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_law_not_found(self, validator):
        """Test validation when law is not found"""
        with patch.object(validator, "_fetch_law_metadata", return_value=None):
            result = await validator.validate_eli("https://finlex.fi/eli/laki/2025/999")

            assert result.status == ELIValidationStatus.LAW_NOT_FOUND
            assert result.law_year == 2025
            assert result.law_number == 999
            assert "not found in Finlex" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_section_not_found(self, validator):
        """Test validation when section is not found"""
        mock_metadata = {
            "title": "Test Law",
            "sections": [
                {"identifier": "Pykala1", "title": "First Section"},
                {"identifier": "Pykala2", "title": "Second Section"},
            ],
        }

        with patch.object(validator, "_fetch_law_metadata", return_value=mock_metadata):
            result = await validator.validate_eli(
                "https://finlex.fi/eli/laki/2023/123#Pykala3"
            )

            assert result.status == ELIValidationStatus.SECTION_NOT_FOUND
            assert result.section == "Pykala3"
            assert "Section 'Pykala3' not found" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_law_expired(self, validator):
        """Test validation when law has expired"""
        mock_metadata = {
            "title": "Expired Law",
            "effective_date": "2020-01-01",
            "expiry_date": "2022-12-31",
            "sections": [],
        }

        with patch.object(validator, "_fetch_law_metadata", return_value=mock_metadata):
            result = await validator.validate_eli("https://finlex.fi/eli/laki/2020/123")

            assert result.status == ELIValidationStatus.LAW_EXPIRED
            assert result.effective_date == date(2020, 1, 1)
            assert result.expiry_date == date(2022, 12, 31)
            assert "not currently effective" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_law_not_yet_effective(self, validator):
        """Test validation when law is not yet effective"""
        mock_metadata = {
            "title": "Future Law",
            "effective_date": "2025-01-01",
            "sections": [],
        }

        with patch.object(validator, "_fetch_law_metadata", return_value=mock_metadata):
            result = await validator.validate_eli("https://finlex.fi/eli/laki/2025/123")

            assert result.status == ELIValidationStatus.LAW_EXPIRED
            assert result.effective_date == date(2025, 1, 1)
            assert "not currently effective" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_valid_law(self, validator):
        """Test validation of valid law"""
        mock_metadata = {
            "title": "Valid Law",
            "effective_date": "2020-01-01",
            "sections": [
                {"identifier": "Pykala1", "title": "First Section"},
                {"identifier": "Pykala2", "title": "Second Section"},
            ],
        }

        with patch.object(validator, "_fetch_law_metadata", return_value=mock_metadata):
            result = await validator.validate_eli(
                "https://finlex.fi/eli/laki/2020/123#Pykala1"
            )

            assert result.status == ELIValidationStatus.VALID
            assert result.law_year == 2020
            assert result.law_number == 123
            assert result.section == "Pykala1"
            assert result.law_title == "Valid Law"
            assert result.effective_date == date(2020, 1, 1)
            assert result.error_message is None

    @pytest.mark.asyncio
    async def test_validate_valid_law_without_section(self, validator):
        """Test validation of valid law without section"""
        mock_metadata = {
            "title": "Valid Law",
            "effective_date": "2020-01-01",
            "sections": [],
        }

        with patch.object(validator, "_fetch_law_metadata", return_value=mock_metadata):
            result = await validator.validate_eli("https://finlex.fi/eli/laki/2020/123")

            assert result.status == ELIValidationStatus.VALID
            assert result.section is None

    @pytest.mark.asyncio
    async def test_validate_decision_function_spec(self, validator):
        """Test validation of decision function specification"""
        spec = {
            "id": "TEST.DF_001",
            "version": "1.0.0",
            "law_reference": {"eli": "https://finlex.fi/eli/laki/2020/123#Pykala1"},
            "invariants": [
                "output.decision in ['APPROVED','DENIED']",
                "See also: https://finlex.fi/eli/laki/2020/456#Pykala2",
            ],
        }

        mock_metadata_1 = {
            "title": "First Law",
            "effective_date": "2020-01-01",
            "sections": [{"identifier": "Pykala1", "title": "First Section"}],
        }

        mock_metadata_2 = {
            "title": "Second Law",
            "effective_date": "2020-01-01",
            "sections": [{"identifier": "Pykala2", "title": "Second Section"}],
        }

        async def mock_fetch(year, number):
            if year == 2020 and number == 123:
                return mock_metadata_1
            elif year == 2020 and number == 456:
                return mock_metadata_2
            return None

        with patch.object(validator, "_fetch_law_metadata", side_effect=mock_fetch):
            results = await validator.validate_decision_function_spec(spec)

            assert len(results) == 2
            assert "https://finlex.fi/eli/laki/2020/123#Pykala1" in results
            assert "https://finlex.fi/eli/laki/2020/456#Pykala2" in results

            result1 = results["https://finlex.fi/eli/laki/2020/123#Pykala1"]
            result2 = results["https://finlex.fi/eli/laki/2020/456#Pykala2"]

            assert result1.status == ELIValidationStatus.VALID
            assert result2.status == ELIValidationStatus.VALID

    def test_get_validation_summary(self, validator):
        """Test validation summary generation"""
        results = {
            "uri1": ELIValidationResult(
                status=ELIValidationStatus.VALID, eli_uri="uri1"
            ),
            "uri2": ELIValidationResult(
                status=ELIValidationStatus.VALID, eli_uri="uri2"
            ),
            "uri3": ELIValidationResult(
                status=ELIValidationStatus.LAW_NOT_FOUND, eli_uri="uri3"
            ),
        }

        summary = validator.get_validation_summary(results)

        assert summary["total_references"] == 3
        assert summary["valid_references"] == 2
        assert summary["invalid_references"] == 1
        assert summary["validation_rate"] == 2 / 3
        assert summary["status_breakdown"]["valid"] == 2
        assert summary["status_breakdown"]["law_not_found"] == 1
        assert not summary["all_valid"]


class TestELIValidationIntegration:
    """Test ELI validation integration with API"""

    @pytest.mark.asyncio
    async def test_validate_eli_reference_function(self):
        """Test standalone ELI validation function"""
        with patch(
            "policy_as_code.validation.eli_validator.ELIValidator"
        ) as mock_validator_class:
            mock_validator = AsyncMock()
            mock_validator_class.return_value.__aenter__.return_value = mock_validator

            mock_result = ELIValidationResult(
                status=ELIValidationStatus.VALID,
                eli_uri="https://finlex.fi/eli/laki/2020/123",
                law_year=2020,
                law_number=123,
                law_title="Test Law",
            )
            mock_validator.validate_eli.return_value = mock_result

            result = await validate_eli_reference("https://finlex.fi/eli/laki/2020/123")

            assert result.status == ELIValidationStatus.VALID
            assert result.law_year == 2020
            assert result.law_number == 123

    @pytest.mark.asyncio
    async def test_validate_decision_function_eli_function(self):
        """Test standalone decision function ELI validation"""
        spec = {
            "id": "TEST.DF_001",
            "version": "1.0.0",
            "law_reference": {"eli": "https://finlex.fi/eli/laki/2020/123"},
        }

        with patch(
            "policy_as_code.validation.eli_validator.ELIValidator"
        ) as mock_validator_class:
            mock_validator = AsyncMock()
            mock_validator_class.return_value.__aenter__.return_value = mock_validator

            mock_result = ELIValidationResult(
                status=ELIValidationStatus.VALID,
                eli_uri="https://finlex.fi/eli/laki/2020/123",
            )
            mock_validator.validate_decision_function_spec.return_value = {
                "https://finlex.fi/eli/laki/2020/123": mock_result
            }

            results = await validate_decision_function_eli(spec)

            assert len(results) == 1
            assert "https://finlex.fi/eli/laki/2020/123" in results
            assert (
                results["https://finlex.fi/eli/laki/2020/123"].status
                == ELIValidationStatus.VALID
            )


class TestELIValidationEdgeCases:
    """Test ELI validation edge cases"""

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors"""
        validator = ELIValidator()

        with patch.object(
            validator, "_fetch_law_metadata", side_effect=Exception("Network error")
        ):
            result = await validator.validate_eli("https://finlex.fi/eli/laki/2020/123")

            assert result.status == ELIValidationStatus.PARSING_ERROR
            assert "Error validating ELI" in result.error_message

    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Test ELI validation caching"""
        validator = ELIValidator()

        mock_metadata = {
            "title": "Test Law",
            "effective_date": "2020-01-01",
            "sections": [],
        }

        with patch.object(
            validator, "_fetch_law_metadata", return_value=mock_metadata
        ) as mock_fetch:
            # First validation
            result1 = await validator.validate_eli(
                "https://finlex.fi/eli/laki/2020/123"
            )
            assert result1.status == ELIValidationStatus.VALID

            # Second validation should use cache
            result2 = await validator.validate_eli(
                "https://finlex.fi/eli/laki/2020/123"
            )
            assert result2.status == ELIValidationStatus.VALID

            # Should only call API once
            assert mock_fetch.call_count == 1

    @pytest.mark.asyncio
    async def test_force_refresh_cache(self):
        """Test forcing cache refresh"""
        validator = ELIValidator()

        mock_metadata = {
            "title": "Test Law",
            "effective_date": "2020-01-01",
            "sections": [],
        }

        with patch.object(
            validator, "_fetch_law_metadata", return_value=mock_metadata
        ) as mock_fetch:
            # First validation
            await validator.validate_eli("https://finlex.fi/eli/laki/2020/123")

            # Force refresh
            await validator.validate_eli(
                "https://finlex.fi/eli/laki/2020/123", force_refresh=True
            )

            # Should call API twice
            assert mock_fetch.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__])
