"""
Authentication for Decision Layer API
"""

import os
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


class APIKeyAuth:
    """Simple API key authentication"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DECISION_LAYER_API_KEY")
        self.security = HTTPBearer(auto_error=False)

    def require_auth(self, request: Request):
        """Require API key authentication"""
        if not self.api_key:
            # No API key configured, allow all requests
            return

        # Check for API key in header
        auth_header = request.headers.get("X-API-Key")
        if auth_header and auth_header == self.api_key:
            return

        # Check for Bearer token
        credentials: Optional[HTTPAuthorizationCredentials] = self.security(request)
        if credentials and credentials.credentials == self.api_key:
            return

        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_auth_middleware(api_key: Optional[str] = None):
    """Create authentication middleware"""
    auth = APIKeyAuth(api_key)
    return auth.require_auth


def require_auth(func):
    """Decorator to require authentication"""

    async def wrapper(request: Request, *args, **kwargs):
        auth = APIKeyAuth()
        auth.require_auth(request)
        return await func(request, *args, **kwargs)

    return wrapper
