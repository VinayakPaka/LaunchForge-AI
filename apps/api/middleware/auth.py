"""
FastAPI auth dependencies.

Three dependency levels:
  get_current_user  — returns User or None (soft, for optional auth)
  require_user      — raises HTTP 401 if not authenticated
  require_tier      — factory that raises HTTP 403 if tier is insufficient

Usage:
    @router.get("/pipeline/start")
    async def start(user: User = Depends(require_user)):
        ...

    @router.get("/reports/full")
    async def full_report(user: User = Depends(require_tier("pro"))):
        ...
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from services.auth_service import decode_access_token

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)

# Subscription tier ordering for gate checks
_TIER_RANK = {"free": 0, "pro": 1, "team": 2, "enterprise": 3}


async def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Soft auth dependency — returns the authenticated User or None.

    Accepts the access token from:
      1. Authorization: Bearer <token>  header (preferred)
      2. `access_token` cookie (fallback for SSR scenarios)
    """
    token: Optional[str] = None

    if creds and creds.credentials:
        token = creds.credentials
    else:
        # Cookie fallback
        token = request.cookies.get("access_token")

    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user and not user.is_active:
        return None

    return user


async def require_user(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """Hard auth dependency — raises HTTP 401 if not authenticated."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_tier(minimum_tier: str):
    """
    Factory — returns a dependency that raises HTTP 403 if the user's
    subscription tier is below `minimum_tier`.

    Example:
        Depends(require_tier("pro"))
    """
    async def _check(user: User = Depends(require_user)) -> User:
        user_rank = _TIER_RANK.get(user.tier, 0)
        required_rank = _TIER_RANK.get(minimum_tier, 1)
        if user_rank < required_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires the '{minimum_tier}' plan or above. "
                       f"Your current plan is '{user.tier}'.",
            )
        return user

    return _check
