"""
Error definitions for governance module

This module defines custom exceptions used throughout the governance
components including audit service, legal references, and release management.
"""

from typing import Optional, Dict, Any


class DecisionLayerError(Exception):
    """Base exception for all decision layer errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class AuditError(DecisionLayerError):
    """Exception raised during audit operations"""

    pass


class LegalReferenceError(DecisionLayerError):
    """Exception raised during legal reference validation"""

    pass


class ReleaseError(DecisionLayerError):
    """Exception raised during release management operations"""

    pass


class SignatureError(DecisionLayerError):
    """Exception raised during digital signature operations"""

    pass


class ComplianceError(DecisionLayerError):
    """Exception raised during compliance checks"""

    pass


class ValidationError(DecisionLayerError):
    """Exception raised during data validation"""

    pass


class ConfigurationError(DecisionLayerError):
    """Exception raised during configuration operations"""

    pass


class SecurityError(DecisionLayerError):
    """Exception raised during security operations"""

    pass


class DomainError(DecisionLayerError):
    """Exception raised during domain-specific operations"""

    pass
