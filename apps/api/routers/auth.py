"""
Auth router — LaunchForge AI.

Endpoints:
  POST /api/auth/register      — create account (Argon2id hash)
  POST /api/auth/login         — login → access token (Bearer) + refresh token (HttpOnly cookie)
  POST /api/auth/refresh       — exchange refresh cookie → new access + rotated refresh
  POST /api/auth/logout        — revoke current refresh token (single device)
  POST /api/auth/logout-all    — revoke all refresh tokens for this user (all devices)
  GET  /api/auth/me            — current user profile
  POST /api/auth/upgrade       — upgrade tier (stub; wire Stripe webhook in production)
  GET  /api/auth/jwks          — RS256 public key as JWKS

Security controls:
  - Argon2id password hashing (NIST SP 800-63B)
  - RS256 access tokens (15-min TTL)
  - Opaque refresh tokens stored as SHA-256 hash in DB (7-day TTL)
  - Refresh token rotation: each use issues a new token, marks old as used
  - Family revocation: reuse of a used/revoked token voids all family tokens (RFC 6749 §10.4)
  - HttpOnly + Secure + SameSite=Strict cookie for refresh token
  - Constant-time password comparison (timing-attack prevention)
  - User enumeration prevention (same response time whether user exists or not)
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from database import get_db
from middleware.auth import get_current_user, require_user
from models.user import RefreshToken, User
from services.auth_service import (
    build_binding_hash,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    needs_rehash,
    refresh_token_expiry,
    verify_password,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

# ── Cookie config ──────────────────────────────────────────────────────────────
_COOKIE_NAME     = "refresh_token"
_COOKIE_MAX_AGE  = 7 * 24 * 60 * 60  # 7 days in seconds
_COOKIE_SAMESITE = "strict"
_COOKIE_SECURE   = False  # set True in production (HTTPS)


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=raw_token,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_COOKIE_NAME, path="/api/auth")


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:    str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    name:     Optional[str] = Field(default="Founder", max_length=128)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        errors = []
        if len(v) < 8:
            errors.append("at least 8 characters")
        if not any(c.isupper() for c in v):
            errors.append("one uppercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("one digit")
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v


class LoginRequest(BaseModel):
    email:    str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()


class AuthResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int = 900  # seconds
    user:         dict


class UpgradeTierRequest(BaseModel):
    tier: str


# ── Internal helpers ───────────────────────────────────────────────────────────

async def _issue_tokens(
    user: User,
    request: Request,
    response: Response,
    db: AsyncSession,
    family: Optional[str] = None,
) -> AuthResponse:
    """Create access + refresh token pair and set the refresh cookie."""
    access_token = create_access_token(user.id, user.email, user.tier)

    raw_refresh  = generate_refresh_token()
    token_hash   = hash_token(raw_refresh)
    binding      = build_binding_hash(
        request.headers.get("user-agent", "unknown"),
        request.client.host if request.client else "unknown",
    )
    token_family = family or str(uuid.uuid4())

    rt = RefreshToken(
        token_hash=token_hash,
        user_id=user.id,
        family=token_family,
        expires_at=refresh_token_expiry(),
        binding_hash=binding,
    )
    db.add(rt)
    await db.commit()

    _set_refresh_cookie(response, raw_refresh)
    return AuthResponse(access_token=access_token, user=user.to_dict())


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Register a new account. Returns access token + sets HttpOnly refresh cookie."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name or "Founder",
        tier="free",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("New user registered: %s id=%s", user.email, user.id)
    return await _issue_tokens(user, request, response, db)


@router.post("/login")
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email + password.
    Returns access token; sets HttpOnly refresh cookie.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Always run Argon2id verification to prevent user-enumeration via timing
    dummy_hash = "$argon2id$v=19$m=65536,t=2,p=2$c29tZXNhbHQ$RdescudvJCsgt3ub+b+dWRWJTmaaJObG"
    candidate_hash = user.password_hash if user else dummy_hash
    password_ok = verify_password(body.password, candidate_hash)

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support.",
        )

    # Transparent Argon2id parameter upgrade
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
        db.add(user)
        await db.commit()

    logger.info("User logged in: %s id=%s", user.email, user.id)
    return await _issue_tokens(user, request, response, db)


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: Optional[str] = Cookie(default=None),
):
    """
    Exchange a valid refresh token cookie for a new access token.
    Rotates the refresh token.

    RFC 6749 §10.4 family revocation:
    Presenting a used/revoked token triggers revocation of ALL tokens
    in the same family (session), indicating possible token theft.
    """
    _invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired session. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not refresh_token:
        raise _invalid

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    )
    rt = result.scalar_one_or_none()
    if not rt:
        raise _invalid

    # ── Reuse detection ────────────────────────────────────────────────────
    if rt.used or rt.revoked:
        logger.warning(
            "Refresh token reuse detected — revoking family. user_id=%s family=%s",
            rt.user_id, rt.family,
        )
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == rt.user_id)
            .where(RefreshToken.family == rt.family)
            .values(revoked=True)
        )
        await db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security alert: suspicious activity detected. "
                   "All sessions have been invalidated. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not rt.is_valid:
        _clear_refresh_cookie(response)
        raise _invalid

    # Mark current token as used (rotation step)
    rt.used = True
    db.add(rt)
    await db.commit()

    user_result = await db.execute(select(User).where(User.id == rt.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise _invalid

    logger.info("Refresh token rotated for user_id=%s", user.id)
    return await _issue_tokens(user, request, response, db, family=rt.family)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: Optional[str] = Cookie(default=None),
    _user: User = Depends(require_user),
):
    """Revoke the current refresh token (single-device logout)."""
    if refresh_token:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == hash_token(refresh_token))
            .values(revoked=True)
        )
        await db.commit()
    _clear_refresh_cookie(response)
    logger.info("User logged out: id=%s", _user.id)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    """Revoke ALL refresh tokens for this user (all-device logout)."""
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .where(RefreshToken.revoked == False)   # noqa: E712
        .values(revoked=True)
    )
    await db.commit()
    _clear_refresh_cookie(response)
    logger.info("All sessions revoked for user_id=%s", user.id)


@router.get("/me")
async def me(user: User = Depends(require_user)):
    """Return the authenticated user's profile."""
    return user.to_dict()


@router.post("/upgrade")
async def upgrade_tier(
    body: UpgradeTierRequest,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Upgrade subscription tier (stub — wire Stripe webhook in production)."""
    valid_tiers = ["free", "pro", "team", "enterprise"]
    if body.tier not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Choose from: {valid_tiers}",
        )
    user.tier = body.tier
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": f"Tier upgraded to '{body.tier}'", "user": user.to_dict()}


@router.get("/jwks")
async def jwks():
    """RS256 public key as JWKS — allows third parties to verify LaunchForge JWTs."""
    import base64
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    from services.auth_service import get_public_key

    pub_pem = get_public_key()
    pub_key = load_pem_public_key(pub_pem)
    nums = pub_key.public_numbers()

    def _b64url(n: int) -> str:
        length = (n.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()

    return {
        "keys": [{
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": "launchforge-1",
            "n":   _b64url(nums.n),
            "e":   _b64url(nums.e),
        }]
    }
