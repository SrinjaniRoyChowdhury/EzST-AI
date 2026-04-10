"""
api/dependencies.py
────────────────────
Shared FastAPI dependency functions.
Centralised here to avoid circular imports.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user


CurrentUser = Annotated[dict, Depends(get_current_user)]


async def require_seller(current_user: CurrentUser) -> dict:
    """Dependency that ensures the user has seller or both role."""
    role = current_user.get("user_metadata", {}).get("role", "")
    if role not in {"seller", "both", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller role required for this action",
        )
    return current_user


async def require_buyer(current_user: CurrentUser) -> dict:
    """Dependency that ensures the user has buyer or both role."""
    role = current_user.get("user_metadata", {}).get("role", "")
    if role not in {"buyer", "both", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Buyer role required for this action",
        )
    return current_user


async def require_admin(current_user: CurrentUser) -> dict:
    """Dependency that ensures the user is an admin."""
    role = current_user.get("user_metadata", {}).get("role", "")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user


SellerUser  = Annotated[dict, Depends(require_seller)]
BuyerUser   = Annotated[dict, Depends(require_buyer)]
AdminUser   = Annotated[dict, Depends(require_admin)]