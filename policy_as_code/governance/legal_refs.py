"""
Legal References with validated IRIs
First-class legal linkage with Finlex/EUR-Lex validation
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from .errors import DecisionLayerError


class LegalSystem(str, Enum):
    """Supported legal systems"""

    FINLEX = "finlex"  # Finnish legal system
    EURLEX = "eurlex"  # European Union legal system
    CUSTOM = "custom"  # Custom legal system


@dataclass(frozen=True)
class LawReference:
    """Immutable legal reference with validated IRI"""

    system: LegalSystem
    act_id: str
    section: Optional[str] = None
    subsection: Optional[str] = None
    uri: str = ""
    title: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        """Validate the legal reference after creation"""
        if not self.uri:
            # Generate URI if not provided
            object.__setattr__(self, "uri", self._generate_uri())

        # Validate URI format
        if not self._is_valid_uri(self.uri):
            raise LegalReferenceError("invalid_uri", f"Invalid URI format: {self.uri}")

    def _generate_uri(self) -> str:
        """Generate URI based on system and act_id"""
        if self.system == LegalSystem.FINLEX:
            return f"https://finlex.fi/fi/laki/ajantasa/{self.act_id}/"
        elif self.system == LegalSystem.EURLEX:
            return f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{self.act_id}"
        else:
            return f"https://legal.example.com/{self.act_id}"

    def _is_valid_uri(self, uri: str) -> bool:
        """Validate URI format"""
        try:
            parsed = urlparse(uri)
            if not parsed.scheme or not parsed.netloc:
                return False

            if self.system == LegalSystem.FINLEX:
                return self._is_valid_finlex_uri(uri)
            elif self.system == LegalSystem.EURLEX:
                return self._is_valid_eurlex_uri(uri)
            else:
                return True  # Custom URIs are accepted as-is
        except Exception:
            return False

    def _is_valid_finlex_uri(self, uri: str) -> bool:
        """Validate Finlex URI format"""
        finlex_pattern = r"^https://finlex\.fi/fi/laki/ajantasa/\d{4}/\d+/?$"
        return bool(re.match(finlex_pattern, uri))

    def _is_valid_eurlex_uri(self, uri: str) -> bool:
        """Validate EUR-Lex URI format"""
        eurlex_pattern = r"^https://eur-lex\.europa\.eu/legal-content/EN/TXT/\?uri=CELEX:\d+[A-Z]?\d*$"
        return bool(re.match(eurlex_pattern, uri))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "system": self.system.value,
            "act_id": self.act_id,
            "section": self.section,
            "subsection": self.subsection,
            "uri": self.uri,
            "title": self.title,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LawReference":
        """Create from dictionary"""
        return cls(
            system=LegalSystem(data["system"]),
            act_id=data["act_id"],
            section=data.get("section"),
            subsection=data.get("subsection"),
            uri=data.get("uri", ""),
            title=data.get("title"),
            description=data.get("description"),
        )

    def __str__(self) -> str:
        """Human-readable string representation"""
        parts = [f"{self.system.value.upper()}: {self.act_id}"]
        if self.section:
            parts.append(f"§{self.section}")
        if self.subsection:
            parts.append(f"({self.subsection})")
        return " ".join(parts)


class LegalReferenceError(DecisionLayerError):
    """Legal reference validation errors"""

    def __init__(self, error_type: str, message: str):
        super().__init__(f"Legal reference error ({error_type}): {message}")
        self.error_type = error_type


class LegalReferenceValidator:
    """Validator for legal references"""

    @staticmethod
    def validate_reference(
        reference: Union[LawReference, Dict[str, Any]],
    ) -> LawReference:
        """Validate and normalize a legal reference"""
        if isinstance(reference, dict):
            try:
                return LawReference.from_dict(reference)
            except Exception as e:
                raise LegalReferenceError(
                    "validation", f"Invalid reference format: {str(e)}"
                )
        elif isinstance(reference, LawReference):
            return reference
        else:
            raise LegalReferenceError(
                "validation", f"Invalid reference type: {type(reference)}"
            )

    @staticmethod
    def validate_reference_list(
        references: List[Union[LawReference, Dict[str, Any]]],
    ) -> List[LawReference]:
        """Validate a list of legal references"""
        validated = []
        for ref in references:
            validated.append(LegalReferenceValidator.validate_reference(ref))
        return validated

    @staticmethod
    def require_legal_references(
        references: List[Union[LawReference, Dict[str, Any]]],
    ) -> List[LawReference]:
        """Require at least one valid legal reference"""
        if not references:
            raise LegalReferenceError(
                "missing_reference", "At least one legal reference is required"
            )

        validated = LegalReferenceValidator.validate_reference_list(references)

        if not validated:
            raise LegalReferenceError(
                "empty_reference", "No valid legal references found"
            )

        return validated


class LegalReferenceRegistry:
    """Registry for managing legal references"""

    def __init__(self):
        self.references: Dict[str, LawReference] = {}

    def register_reference(self, key: str, reference: LawReference) -> None:
        """Register a legal reference"""
        self.references[key] = reference

    def get_reference(self, key: str) -> Optional[LawReference]:
        """Get a registered legal reference"""
        return self.references.get(key)

    def list_references(self) -> List[LawReference]:
        """List all registered references"""
        return list(self.references.values())

    def search_references(
        self, system: Optional[LegalSystem] = None, act_id: Optional[str] = None
    ) -> List[LawReference]:
        """Search references by criteria"""
        results = []
        for ref in self.references.values():
            if system and ref.system != system:
                continue
            if act_id and ref.act_id != act_id:
                continue
            results.append(ref)
        return results


# Predefined legal references for common use cases
COMMON_LEGAL_REFERENCES = {
    "gdpr": LawReference(
        system=LegalSystem.EURLEX,
        act_id="32016R0679",
        title="General Data Protection Regulation",
        description="EU regulation on data protection and privacy",
    ),
    "consumer_rights_directive": LawReference(
        system=LegalSystem.EURLEX,
        act_id="32011L0083",
        title="Consumer Rights Directive",
        description="EU directive on consumer rights",
    ),
    "finnish_data_protection_act": LawReference(
        system=LegalSystem.FINLEX,
        act_id="2018/1050",
        title="Personal Data Processing Act",
        description="Finnish Data Protection Act",
    ),
}


def create_legal_reference(
    system: str,
    act_id: str,
    section: Optional[str] = None,
    subsection: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> LawReference:
    """Create a legal reference with validation"""
    return LawReference(
        system=LegalSystem(system),
        act_id=act_id,
        section=section,
        subsection=subsection,
        title=title,
        description=description,
    )


def validate_legal_references_in_metadata(
    metadata: Dict[str, Any],
) -> List[LawReference]:
    """Validate legal references in function metadata"""
    policy_refs = metadata.get("policy_references", [])

    if not policy_refs:
        raise LegalReferenceError(
            "missing_reference",
            "Function metadata must include at least one legal reference",
        )

    # Convert string references to LawReference objects
    legal_refs: List[Union[LawReference, Dict[str, Any]]] = []
    for ref in policy_refs:
        if isinstance(ref, str):
            # Try to parse as URI
            try:
                parsed = urlparse(ref)
                if "finlex.fi" in parsed.netloc:
                    # Extract act_id from Finlex URI
                    act_id = (
                        parsed.path.split("/")[-2]
                        if parsed.path.endswith("/")
                        else parsed.path.split("/")[-1]
                    )
                    legal_refs.append(
                        LawReference(system=LegalSystem.FINLEX, act_id=act_id, uri=ref)
                    )
                elif "eur-lex.europa.eu" in parsed.netloc:
                    # Extract CELEX number from EUR-Lex URI
                    celex_match = re.search(r"CELEX:(\d+[A-Z]?)", ref)
                    if celex_match:
                        legal_refs.append(
                            LawReference(
                                system=LegalSystem.EURLEX,
                                act_id=celex_match.group(1),
                                uri=ref,
                            )
                        )
                else:
                    # Treat as custom reference
                    legal_refs.append(
                        LawReference(system=LegalSystem.CUSTOM, act_id=ref, uri=ref)
                    )
            except Exception:
                # If parsing fails, treat as custom reference
                legal_refs.append(
                    LawReference(system=LegalSystem.CUSTOM, act_id=ref, uri=ref)
                )
        elif isinstance(ref, dict):
            legal_refs.append(LawReference.from_dict(ref))
        elif isinstance(ref, LawReference):
            legal_refs.append(ref)

    # Validate all references
    return LegalReferenceValidator.validate_reference_list(legal_refs)
