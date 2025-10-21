"""
Security configuration and management for Policy as Code framework
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SecurityConfig:
    """Security configuration"""

    enabled: bool = True
    audit_logging: bool = True
    encryption_required: bool = False
    allowed_functions: Optional[List[str]] = None
    blocked_functions: Optional[List[str]] = None


class SecurityManager:
    """Security manager for decision functions"""

    def __init__(self, config: SecurityConfig):
        self.config = config

    def is_function_allowed(self, function_id: str) -> bool:
        """Check if function is allowed"""
        if not self.config.enabled:
            return True

        if (
            self.config.blocked_functions
            and function_id in self.config.blocked_functions
        ):
            return False

        if (
            self.config.allowed_functions
            and function_id not in self.config.allowed_functions
        ):
            return False

        return True

    def audit_log(self, function_id: str, action: str, details: Dict):
        """Log security audit event"""
        if self.config.audit_logging:
            print(f"AUDIT: {function_id} - {action} - {details}")
