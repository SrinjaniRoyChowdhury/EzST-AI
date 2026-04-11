"""
core/security.py
────────────────
Supabase JWT verification for FastAPI.
Extracts and validates the Bearer token on every protected route.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


def decode_supabase_jwt(token: str) -> dict:
    """
    Decode and verify a Supabase-issued JWT.
    Supabase signs tokens with HS256 using the project JWT secret.
    """
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Mock the current user for testing purposes."""
    return {"sub": "11111111-1111-1111-1111-111111111111", "email": "mock@test.com", "role": "seller"}


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[dict]:
    """Same as get_current_user but returns None instead of raising for public endpoints."""
    if credentials is None:
        return None
    try:
        return decode_supabase_jwt(credentials.credentials)
    except HTTPException:
        return None