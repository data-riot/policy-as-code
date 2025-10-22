"""
ELI (European Legislation Identifier) Validator for Policy as Code

This module provides comprehensive validation of ELI references to ensure
legal compliance and traceability of decision functions back to Finnish law.

ELI Format: https://finlex.fi/eli/laki/{year}/{number}#{section}
Example: https://finlex.fi/eli/laki/2023/123#Pykala4

CITIZEN BENEFIT PERSPECTIVE:
- Ensures that every decision can be traced back to law
- Prevents making illegal decisions
- Enables citizens' legal oversight
"""

import re
import asyncio
import aiohttp
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ELIValidationStatus(Enum):
    """ELI validation status"""

    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    LAW_NOT_FOUND = "law_not_found"
    SECTION_NOT_FOUND = "section_not_found"
    LAW_EXPIRED = "law_expired"
    NETWORK_ERROR = "network_error"
    PARSING_ERROR = "parsing_error"


@dataclass
class ELIValidationResult:
    """Result of ELI validation"""

    status: ELIValidationStatus
    eli_uri: str
    law_year: Optional[int] = None
    law_number: Optional[int] = None
    section: Optional[str] = None
    law_title: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    error_message: Optional[str] = None
    validated_at: datetime = None

    def __post_init__(self):
        if self.validated_at is None:
            self.validated_at = datetime.utcnow()


class ELIValidator:
    """ELI validator for Finnish legislation"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

        # ELI URI pattern for Finnish legislation
        self.eli_pattern = re.compile(
            r"^https://finlex\.fi/eli/laki/(\d{4})/(\d+)(?:#(.+))?$"
        )

        # Cache for validated ELIs (in production, use Redis/Memcached)
        self.validation_cache: Dict[str, ELIValidationResult] = {}

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _parse_eli_uri(
        self, eli_uri: str
    ) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """Parse ELI URI into components"""
        match = self.eli_pattern.match(eli_uri)
        if not match:
            return None, None, None

        year = int(match.group(1))
        number = int(match.group(2))
        section = match.group(3) if match.group(3) else None

        return year, number, section

    async def _fetch_law_metadata(self, year: int, number: int) -> Dict[str, Any]:
        """Fetch law metadata from Finlex API"""
        if not self.session:
            raise RuntimeError(
                "ELIValidator not initialized. Use async context manager."
            )

        # Finlex API endpoint for law metadata
        api_url = f"https://finlex.fi/api/v1/laki/{year}/{number}"

        try:
            async with self.session.get(api_url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    logger.warning(
                        f"Finlex API returned status {response.status} for {api_url}"
                    )
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching law metadata for {year}/{number}")
            return None
        except Exception as e:
            logger.error(f"Error fetching law metadata: {e}")
            return None

    async def _validate_law_exists(
        self, year: int, number: int
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate that law exists and get metadata"""
        metadata = await self._fetch_law_metadata(year, number)
        return metadata is not None, metadata

    async def _validate_section_exists(
        self, metadata: Dict[str, Any], section: str
    ) -> bool:
        """Validate that section exists in the law"""
        if not section:
            return True  # No section specified, assume valid

        # Check if section exists in law structure
        sections = metadata.get("sections", [])
        for sec in sections:
            if (
                sec.get("identifier") == section
                or sec.get("title", "").lower() == section.lower()
            ):
                return True

        return False

    def _is_law_effective(
        self, metadata: Dict[str, Any]
    ) -> Tuple[bool, Optional[date], Optional[date]]:
        """Check if law is currently effective"""
        effective_date_str = metadata.get("effective_date")
        expiry_date_str = metadata.get("expiry_date")

        effective_date = None
        expiry_date = None

        if effective_date_str:
            try:
                effective_date = datetime.strptime(
                    effective_date_str, "%Y-%m-%d"
                ).date()
            except ValueError:
                pass

        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        today = date.today()

        # Check if law is effective
        if effective_date and effective_date > today:
            return False, effective_date, expiry_date

        # Check if law has expired
        if expiry_date and expiry_date < today:
            return False, effective_date, expiry_date

        return True, effective_date, expiry_date

    async def validate_eli(
        self, eli_uri: str, force_refresh: bool = False
    ) -> ELIValidationResult:
        """
        Validate ELI URI comprehensively

        Args:
            eli_uri: ELI URI to validate
            force_refresh: Force refresh from cache

        Returns:
            ELIValidationResult with validation status and details
        """
        # Check cache first (unless force refresh)
        if not force_refresh and eli_uri in self.validation_cache:
            cached_result = self.validation_cache[eli_uri]
            # Cache valid for 24 hours
            if (datetime.utcnow() - cached_result.validated_at).total_seconds() < 86400:
                return cached_result

        # Parse ELI URI
        year, number, section = self._parse_eli_uri(eli_uri)

        if year is None or number is None:
            result = ELIValidationResult(
                status=ELIValidationStatus.INVALID_FORMAT,
                eli_uri=eli_uri,
                error_message="Invalid ELI URI format. Expected: https://finlex.fi/eli/laki/YYYY/NUMBER#SECTION",
            )
            self.validation_cache[eli_uri] = result
            return result

        try:
            # Validate law exists
            law_exists, metadata = await self._validate_law_exists(year, number)

            if not law_exists:
                result = ELIValidationResult(
                    status=ELIValidationStatus.LAW_NOT_FOUND,
                    eli_uri=eli_uri,
                    law_year=year,
                    law_number=number,
                    error_message=f"Law {year}/{number} not found in Finlex",
                )
                self.validation_cache[eli_uri] = result
                return result

            # Validate section exists
            if section and not await self._validate_section_exists(metadata, section):
                result = ELIValidationResult(
                    status=ELIValidationStatus.SECTION_NOT_FOUND,
                    eli_uri=eli_uri,
                    law_year=year,
                    law_number=number,
                    section=section,
                    law_title=metadata.get("title"),
                    error_message=f"Section '{section}' not found in law {year}/{number}",
                )
                self.validation_cache[eli_uri] = result
                return result

            # Check if law is effective
            is_effective, effective_date, expiry_date = self._is_law_effective(metadata)

            if not is_effective:
                result = ELIValidationResult(
                    status=ELIValidationStatus.LAW_EXPIRED,
                    eli_uri=eli_uri,
                    law_year=year,
                    law_number=number,
                    section=section,
                    law_title=metadata.get("title"),
                    effective_date=effective_date,
                    expiry_date=expiry_date,
                    error_message=f"Law {year}/{number} is not currently effective",
                )
                self.validation_cache[eli_uri] = result
                return result

            # All validations passed
            result = ELIValidationResult(
                status=ELIValidationStatus.VALID,
                eli_uri=eli_uri,
                law_year=year,
                law_number=number,
                section=section,
                law_title=metadata.get("title"),
                effective_date=effective_date,
                expiry_date=expiry_date,
            )
            self.validation_cache[eli_uri] = result
            return result

        except Exception as e:
            logger.error(f"Error validating ELI {eli_uri}: {e}")
            result = ELIValidationResult(
                status=ELIValidationStatus.PARSING_ERROR,
                eli_uri=eli_uri,
                law_year=year,
                law_number=number,
                section=section,
                error_message=f"Error validating ELI: {str(e)}",
            )
            return result

    async def validate_decision_function_spec(
        self, spec: Dict[str, Any]
    ) -> Dict[str, ELIValidationResult]:
        """
        Validate all ELI references in a decision function specification

        Args:
            spec: Decision function specification

        Returns:
            Dictionary mapping ELI URIs to validation results
        """
        results = {}

        # Get law_reference.eli
        law_ref = spec.get("law_reference", {})
        eli_uri = law_ref.get("eli")

        if eli_uri:
            results[eli_uri] = await self.validate_eli(eli_uri)

        # Check for additional ELI references in invariants or other fields
        invariants = spec.get("invariants", [])
        for invariant in invariants:
            # Look for ELI URIs in invariant strings
            eli_matches = re.findall(r'https://finlex\.fi/eli/[^\s\'"]+', invariant)
            for match in eli_matches:
                if match not in results:
                    results[match] = await self.validate_eli(match)

        return results

    def get_validation_summary(
        self, results: Dict[str, ELIValidationResult]
    ) -> Dict[str, Any]:
        """Get summary of validation results"""
        total = len(results)
        valid = sum(
            1 for r in results.values() if r.status == ELIValidationStatus.VALID
        )
        invalid = total - valid

        status_counts = {}
        for result in results.values():
            status_counts[result.status.value] = (
                status_counts.get(result.status.value, 0) + 1
            )

        return {
            "total_references": total,
            "valid_references": valid,
            "invalid_references": invalid,
            "validation_rate": valid / total if total > 0 else 0,
            "status_breakdown": status_counts,
            "all_valid": invalid == 0,
        }


# Global ELI validator instance
_eli_validator: Optional[ELIValidator] = None


async def get_eli_validator() -> ELIValidator:
    """Get global ELI validator instance"""
    global _eli_validator
    if _eli_validator is None:
        _eli_validator = ELIValidator()
    return _eli_validator


async def validate_eli_reference(eli_uri: str) -> ELIValidationResult:
    """Validate a single ELI reference"""
    async with ELIValidator() as validator:
        return await validator.validate_eli(eli_uri)


async def validate_decision_function_eli(
    spec: Dict[str, Any],
) -> Dict[str, ELIValidationResult]:
    """Validate all ELI references in a decision function specification"""
    async with ELIValidator() as validator:
        return await validator.validate_decision_function_spec(spec)


# Example usage and testing
async def demo_eli_validation():
    """Demo ELI validation functionality"""
    test_elis = [
        "https://finlex.fi/eli/laki/2023/123#Pykala4",  # Valid format
        "https://finlex.fi/eli/laki/2025/999#Pykala1",  # Non-existent law
        "invalid-uri",  # Invalid format
        "https://finlex.fi/eli/laki/2023/123#NonExistentSection",  # Non-existent section
    ]

    async with ELIValidator() as validator:
        for eli_uri in test_elis:
            print(f"\nValidating: {eli_uri}")
            result = await validator.validate_eli(eli_uri)
            print(f"Status: {result.status.value}")
            if result.error_message:
                print(f"Error: {result.error_message}")
            if result.law_title:
                print(f"Law: {result.law_title}")


if __name__ == "__main__":
    asyncio.run(demo_eli_validation())
