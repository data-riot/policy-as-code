"""
Core error classes for Policy as Code framework
"""


class DecisionLayerError(Exception):
    """Base exception for decision layer errors"""

    pass


class DeploymentError(DecisionLayerError):
    """Error during deployment"""

    pass


class ExecutionError(DecisionLayerError):
    """Error during execution"""

    pass


class FunctionNotFoundError(DecisionLayerError):
    """Function not found error"""

    pass


class ValidationError(DecisionLayerError):
    """Validation error"""

    pass


class StorageError(DecisionLayerError):
    """Storage error"""

    pass
