"""
Error definitions for tracing module

This module defines custom exceptions used throughout the tracing
components including ledger, postgres, audit, query, integrity, and compression.
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


class TraceError(DecisionLayerError):
    """Exception raised during trace operations"""

    pass


class LedgerError(DecisionLayerError):
    """Exception raised during ledger operations"""

    pass


class PostgresError(DecisionLayerError):
    """Exception raised during PostgreSQL operations"""

    pass


class QueryError(DecisionLayerError):
    """Exception raised during query operations"""

    pass


class IntegrityError(DecisionLayerError):
    """Exception raised during integrity checks"""

    pass


class CompressionError(DecisionLayerError):
    """Exception raised during compression operations"""

    pass


class StorageError(DecisionLayerError):
    """Exception raised during storage operations"""

    pass


class SerializationError(DecisionLayerError):
    """Exception raised during serialization/deserialization"""

    pass


class ValidationError(DecisionLayerError):
    """Exception raised during data validation"""

    pass


class ConfigurationError(DecisionLayerError):
    """Exception raised during configuration operations"""

    pass


class AuditError(DecisionLayerError):
    """Exception raised during audit operations"""

    pass
