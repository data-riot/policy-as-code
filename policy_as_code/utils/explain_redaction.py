"""
Declarative Redaction Policy
Per-DF declarative redaction map for explanations with deny-by-default security

PRODUCTION STATUS: ⚠️ PARTIAL IMPLEMENTATION
- Redaction policy framework implemented
- Field-level redaction implemented
- Context-aware redaction implemented

MISSING PRODUCTION FEATURES:
- PII detection and classification
- Advanced redaction algorithms
- Performance optimization
- Redaction audit logging
- Integration with existing explain API
- Multi-tenant redaction policies
- Redaction policy versioning
- Automated redaction testing
- Redaction compliance reporting
- Cross-border data protection
- Redaction policy management UI
- Redaction performance monitoring
"""

import re
import json
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .errors import DecisionLayerError


class RedactionLevel(str, Enum):
    """Redaction levels"""

    NONE = "none"  # No redaction
    PARTIAL = "partial"  # Partial redaction (e.g., show first/last chars)
    FULL = "full"  # Complete redaction
    HASH = "hash"  # Show hash instead of value


class FieldType(str, Enum):
    """Field types for redaction"""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    PII = "pii"  # Personally Identifiable Information
    SENSITIVE = "sensitive"  # Sensitive business data


@dataclass
class RedactionRule:
    """Redaction rule for a specific field"""

    field_path: str  # JSONPath-like field path
    field_type: FieldType
    redaction_level: RedactionLevel
    pattern: Optional[str] = None  # Regex pattern for partial redaction
    replacement: str = "[REDACTED]"
    preserve_length: bool = False
    hash_algorithm: str = "sha256"
    allow_in_explanation: bool = False
    allow_in_audit: bool = True
    allow_in_trace: bool = False


@dataclass
class ExplainPolicy:
    """Explanation policy for a decision function"""

    function_id: str
    version: str
    allow_fields: List[str] = field(default_factory=list)  # Deny by default
    redact_fields: List[str] = field(default_factory=list)
    redaction_rules: List[RedactionRule] = field(default_factory=list)
    explanation_template: Optional[str] = None
    language: str = "en"
    include_legal_basis: bool = True
    include_decision_path: bool = True
    include_confidence: bool = True
    max_explanation_length: int = 1000

    def __post_init__(self):
        """Validate policy after initialization"""
        self._validate_policy()

    def _validate_policy(self) -> None:
        """Validate explanation policy"""
        # Ensure deny-by-default with explicit allow list
        if not self.allow_fields:
            raise DecisionLayerError(
                "missing_allow_fields",
                f"Explain policy for {self.function_id}:{self.version} must specify allow_fields (deny by default)",
            )

        # Validate field paths
        for field_path in self.allow_fields + self.redact_fields:
            if not self._is_valid_field_path(field_path):
                raise DecisionLayerError(
                    "invalid_field_path", f"Invalid field path: {field_path}"
                )

        # Validate redaction rules
        for rule in self.redaction_rules:
            if not self._is_valid_field_path(rule.field_path):
                raise DecisionLayerError(
                    "invalid_rule_field_path",
                    f"Invalid field path in redaction rule: {rule.field_path}",
                )

    def _is_valid_field_path(self, field_path: str) -> bool:
        """Validate field path format"""
        # Simple validation - in production, use proper JSONPath validation
        if not field_path or field_path.startswith("."):
            return False

        # Check for valid characters
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_.\[\]]*$", field_path):
            return False

        return True


class FieldRedactor:
    """Field-level redaction engine"""

    def __init__(self):
        self._pii_patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        }

    def redact_field(self, value: Any, rule: RedactionRule) -> Any:
        """Redact field value according to rule"""

        if rule.redaction_level == RedactionLevel.NONE:
            return value

        elif rule.redaction_level == RedactionLevel.FULL:
            return rule.replacement

        elif rule.redaction_level == RedactionLevel.PARTIAL:
            return self._partial_redact(value, rule)

        elif rule.redaction_level == RedactionLevel.HASH:
            return self._hash_redact(value, rule)

        else:
            return rule.replacement

    def _partial_redact(self, value: Any, rule: RedactionRule) -> str:
        """Partially redact value"""
        if not isinstance(value, str):
            value = str(value)

        if rule.pattern:
            # Use regex pattern
            if rule.preserve_length:
                return re.sub(rule.pattern, rule.replacement, value)
            else:
                return re.sub(rule.pattern, rule.replacement, value)
        else:
            # Default partial redaction
            if len(value) <= 4:
                return rule.replacement
            elif rule.preserve_length:
                return value[0] + rule.replacement * (len(value) - 2) + value[-1]
            else:
                return value[:2] + rule.replacement + value[-2:]

    def _hash_redact(self, value: Any, rule: RedactionRule) -> str:
        """Hash redact value"""
        import hashlib

        value_str = str(value)

        if rule.hash_algorithm == "sha256":
            hash_obj = hashlib.sha256(value_str.encode())
        elif rule.hash_algorithm == "sha1":
            hash_obj = hashlib.sha1(value_str.encode())
        elif rule.hash_algorithm == "md5":
            hash_obj = hashlib.md5(value_str.encode())
        else:
            hash_obj = hashlib.sha256(value_str.encode())

        return f"hash:{hash_obj.hexdigest()[:8]}"

    def detect_pii(self, value: Any) -> List[str]:
        """Detect PII in value"""
        if not isinstance(value, str):
            return []

        detected = []
        for pii_type, pattern in self._pii_patterns.items():
            if re.search(pattern, value):
                detected.append(pii_type)

        return detected


class ExplainRedactor:
    """Explanation redaction engine

    PRODUCTION STATUS: ⚠️ PARTIAL IMPLEMENTATION
    - Basic redaction framework implemented
    - In-memory policy cache only

    MISSING PRODUCTION FEATURES:
    - Database persistence for policies
    - Performance optimization
    - Redaction audit logging
    - Integration with explain API
    - Multi-tenant support
    - Policy versioning
    - Automated testing
    - Compliance reporting
    """

    def __init__(self):
        self.field_redactor = FieldRedactor()
        # PSEUDOCODE: In-memory cache - NOT production ready
        self._policy_cache: Dict[str, ExplainPolicy] = {}

        # MISSING PRODUCTION LOGIC:
        # 1. Database connection for policy persistence
        # 2. Performance monitoring and metrics
        # 3. Redaction audit logging
        # 4. Integration with existing explain API
        # 5. Multi-tenant policy isolation
        # 6. Policy versioning and migration
        # 7. Automated redaction testing
        # 8. Compliance reporting and analytics

    def register_policy(self, policy: ExplainPolicy) -> None:
        """Register explanation policy"""
        cache_key = f"{policy.function_id}:{policy.version}"
        self._policy_cache[cache_key] = policy

    def get_policy(self, function_id: str, version: str) -> Optional[ExplainPolicy]:
        """Get explanation policy"""
        cache_key = f"{function_id}:{version}"
        return self._policy_cache.get(cache_key)

    def redact_explanation_data(
        self,
        function_id: str,
        version: str,
        data: Dict[str, Any],
        context: str = "explanation",
    ) -> Dict[str, Any]:
        """Redact data according to explanation policy"""

        policy = self.get_policy(function_id, version)
        if not policy:
            # Default deny policy
            return {"error": "Explanation not available - no policy configured"}

        # Apply redaction based on context
        if context == "explanation":
            return self._apply_explanation_redaction(data, policy)
        elif context == "audit":
            return self._apply_audit_redaction(data, policy)
        elif context == "trace":
            return self._apply_trace_redaction(data, policy)
        else:
            return self._apply_explanation_redaction(data, policy)

    def _apply_explanation_redaction(
        self, data: Dict[str, Any], policy: ExplainPolicy
    ) -> Dict[str, Any]:
        """Apply explanation-specific redaction"""
        redacted_data: Dict[str, Any] = {}

        # Only include explicitly allowed fields
        for field_path in policy.allow_fields:
            value = self._get_field_value(data, field_path)
            if value is not None:
                # Apply redaction rules
                redacted_value = self._apply_redaction_rules(
                    value, field_path, policy, "explanation"
                )
                self._set_field_value(redacted_data, field_path, redacted_value)

        # Add explanation metadata
        redacted_data["_explanation_metadata"] = {
            "function_id": policy.function_id,
            "version": policy.version,
            "redaction_applied": True,
            "allowed_fields": policy.allow_fields,
            "redacted_at": datetime.now(timezone.utc).isoformat(),
        }

        return redacted_data

    def _apply_audit_redaction(
        self, data: Dict[str, Any], policy: ExplainPolicy
    ) -> Dict[str, Any]:
        """Apply audit-specific redaction"""
        redacted_data = data.copy()

        # Apply redaction rules for audit context
        for rule in policy.redaction_rules:
            if rule.allow_in_audit:
                continue  # Skip redaction for audit

            value = self._get_field_value(redacted_data, rule.field_path)
            if value is not None:
                redacted_value = self.field_redactor.redact_field(value, rule)
                self._set_field_value(redacted_data, rule.field_path, redacted_value)

        return redacted_data

    def _apply_trace_redaction(
        self, data: Dict[str, Any], policy: ExplainPolicy
    ) -> Dict[str, Any]:
        """Apply trace-specific redaction"""
        redacted_data = data.copy()

        # Apply redaction rules for trace context
        for rule in policy.redaction_rules:
            if rule.allow_in_trace:
                continue  # Skip redaction for trace

            value = self._get_field_value(redacted_data, rule.field_path)
            if value is not None:
                redacted_value = self.field_redactor.redact_field(value, rule)
                self._set_field_value(redacted_data, rule.field_path, redacted_value)

        return redacted_data

    def _apply_redaction_rules(
        self, value: Any, field_path: str, policy: ExplainPolicy, context: str
    ) -> Any:
        """Apply redaction rules to value"""

        # Find applicable rules
        applicable_rules = [
            rule
            for rule in policy.redaction_rules
            if rule.field_path == field_path
            and self._rule_applies_to_context(rule, context)
        ]

        if not applicable_rules:
            return value

        # Apply the most restrictive rule
        most_restrictive_rule = min(
            applicable_rules,
            key=lambda r: self._get_redaction_level_score(r.redaction_level),
        )

        return self.field_redactor.redact_field(value, most_restrictive_rule)

    def _rule_applies_to_context(self, rule: RedactionRule, context: str) -> bool:
        """Check if rule applies to context"""
        if context == "explanation":
            return rule.allow_in_explanation
        elif context == "audit":
            return rule.allow_in_audit
        elif context == "trace":
            return rule.allow_in_trace
        return False

    def _get_redaction_level_score(self, level: RedactionLevel) -> int:
        """Get redaction level score (higher = more restrictive)"""
        scores = {
            RedactionLevel.NONE: 0,
            RedactionLevel.PARTIAL: 1,
            RedactionLevel.HASH: 2,
            RedactionLevel.FULL: 3,
        }
        return scores.get(level, 3)

    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get field value using JSONPath-like syntax"""
        try:
            # Simple field path resolution - in production, use proper JSONPath library
            parts = field_path.split(".")
            value: Any = data

            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                    if value is None:
                        return None
                elif isinstance(value, list) and part.isdigit():
                    value = value[int(part)]
                else:
                    return None

            return value
        except (KeyError, IndexError, ValueError):
            return None

    def _set_field_value(
        self, data: Dict[str, Any], field_path: str, value: Any
    ) -> None:
        """Set field value using JSONPath-like syntax"""
        try:
            # Simple field path setting - in production, use proper JSONPath library
            parts = field_path.split(".")
            current = data

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value
        except (KeyError, IndexError, ValueError):
            pass  # Ignore errors in field setting

    def generate_explanation(
        self,
        function_id: str,
        version: str,
        decision_data: Dict[str, Any],
        legal_references: List[Dict[str, Any]],
        decision_path: List[str],
        confidence_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate explanation with redaction"""

        policy = self.get_policy(function_id, version)
        if not policy:
            return {"error": "Explanation not available - no policy configured"}

        # Redact decision data
        redacted_data = self.redact_explanation_data(
            function_id, version, decision_data
        )

        # Build explanation
        explanation = {
            "decision": self._format_decision_explanation(redacted_data, policy),
            "legal_basis": legal_references if policy.include_legal_basis else [],
            "decision_path": decision_path if policy.include_decision_path else [],
            "confidence_score": confidence_score if policy.include_confidence else None,
            "redacted_fields": self._get_redacted_fields(decision_data, redacted_data),
            "explanation_metadata": {
                "function_id": function_id,
                "version": version,
                "language": policy.language,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        return explanation

    def _format_decision_explanation(
        self, redacted_data: Dict[str, Any], policy: ExplainPolicy
    ) -> str:
        """Format decision explanation"""

        if policy.explanation_template:
            # Use custom template
            try:
                return policy.explanation_template.format(**redacted_data)
            except KeyError:
                pass  # Fall back to default

        # Default explanation format
        explanation_parts = []

        for field_path in policy.allow_fields:
            value = self._get_field_value(redacted_data, field_path)
            if value is not None:
                explanation_parts.append(f"{field_path}: {value}")

        explanation = "Decision based on: " + ", ".join(explanation_parts)

        # Truncate if too long
        if len(explanation) > policy.max_explanation_length:
            explanation = explanation[: policy.max_explanation_length - 3] + "..."

        return explanation

    def _get_redacted_fields(
        self, original_data: Dict[str, Any], redacted_data: Dict[str, Any]
    ) -> List[str]:
        """Get list of redacted fields"""
        redacted_fields = []

        def compare_values(orig: Any, redacted: Any, path: str = ""):
            if isinstance(orig, dict) and isinstance(redacted, dict):
                for key in orig:
                    new_path = f"{path}.{key}" if path else key
                    if key in redacted:
                        compare_values(orig[key], redacted[key], new_path)
                    else:
                        redacted_fields.append(new_path)
            elif orig != redacted:
                redacted_fields.append(path)

        compare_values(original_data, redacted_data)
        return redacted_fields


# Global explain redactor
_explain_redactor: Optional[ExplainRedactor] = None


def get_explain_redactor() -> ExplainRedactor:
    """Get explain redactor instance"""
    global _explain_redactor
    if _explain_redactor is None:
        _explain_redactor = ExplainRedactor()
    return _explain_redactor


def register_explain_policy(policy: ExplainPolicy) -> None:
    """Register explanation policy"""
    redactor = get_explain_redactor()
    redactor.register_policy(policy)


def redact_explanation_data(
    function_id: str, version: str, data: Dict[str, Any], context: str = "explanation"
) -> Dict[str, Any]:
    """Redact data according to explanation policy"""
    redactor = get_explain_redactor()
    return redactor.redact_explanation_data(function_id, version, data, context)


def generate_explanation(
    function_id: str,
    version: str,
    decision_data: Dict[str, Any],
    legal_references: List[Dict[str, Any]],
    decision_path: List[str],
    confidence_score: Optional[float] = None,
) -> Dict[str, Any]:
    """Generate explanation with redaction"""
    redactor = get_explain_redactor()
    return redactor.generate_explanation(
        function_id,
        version,
        decision_data,
        legal_references,
        decision_path,
        confidence_score,
    )
