"""
Core authentication service — LaunchForge AI.

Security posture (OWASP ASVS v4.0.3 + RFC 7519):
  - RS256 asymmetric signing (private key signs, public key verifies)
  - Access tokens: 15-minute TTL, Bearer header
  - Refresh tokens: opaque 64-byte random hex, 7-day TTL, DB-backed with rotation
  - Passwords: Argon2id (NIST SP 800-63B), time=2 / memory=65536 / parallelism=2
  - Constant-time comparison to prevent timing attacks
  - Refresh token family invalidation on reuse (RFC 6749 §10.4)
  - RSA key pair auto-generated on first run, stored in apps/api/keys/
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from jose import jwt, JWTError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

# ── Token configuration ────────────────────────────────────────────────────────
ACCESS_TOKEN_TTL  = timedelta(minutes=15)
REFRESH_TOKEN_TTL = timedelta(days=7)
JWT_ALGORITHM     = "RS256"

# ── Argon2id hasher (NIST SP 800-63B recommendations) ─────────────────────────
_ph = PasswordHasher(
    time_cost=2,        # iterations
    memory_cost=65536,  # 64 MB
    parallelism=2,
    hash_len=32,
    salt_len=16,
)

# ── RSA key management ─────────────────────────────────────────────────────────
_KEYS_DIR      = Path(__file__).parent.parent / "keys"
_PRIVATE_KEY_F = _KEYS_DIR / "jwt_private.pem"
_PUBLIC_KEY_F  = _KEYS_DIR / "jwt_public.pem"

_private_key_pem: Optional[bytes] = None
_public_key_pem:  Optional[bytes] = None


def _load_or_generate_keys() -> tuple[bytes, bytes]:
    """
    Load RSA key pair from disk; generate a new 2048-bit pair if absent.
    Keys are stored in apps/api/keys/ (should be in .gitignore).
    """
    global _private_key_pem, _public_key_pem

    if _private_key_pem and _public_key_pem:
        return _private_key_pem, _public_key_pem

    _KEYS_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)

    if _PRIVATE_KEY_F.exists() and _PUBLIC_KEY_F.exists():
        _private_key_pem = _PRIVATE_KEY_F.read_bytes()
        _public_key_pem  = _PUBLIC_KEY_F.read_bytes()
        logger.info("Loaded existing RSA key pair from %s", _KEYS_DIR)
    else:
        logger.info("Generating new 2048-bit RSA key pair…")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        _private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        _public_key_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        # Write with restricted permissions
        _PRIVATE_KEY_F.write_bytes(_private_key_pem)
        _PRIVATE_KEY_F.chmod(0o600)
        _PUBLIC_KEY_F.write_bytes(_public_key_pem)
        _PUBLIC_KEY_F.chmod(0o644)
        logger.info("RSA key pair generated and saved to %s", _KEYS_DIR)

    return _private_key_pem, _public_key_pem


def get_public_key() -> bytes:
    _, pub = _load_or_generate_keys()
    return pub


# ── Password utilities ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a password with Argon2id."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a password against its Argon2id hash.
    Returns False (never raises) on any mismatch or invalid hash.
    """
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    """Return True if the hash was created with outdated parameters."""
    return _ph.check_needs_rehash(hashed)


# ── Access token (JWT RS256) ───────────────────────────────────────────────────

def create_access_token(user_id: str, email: str, tier: str) -> str:
    """Create a short-lived RS256 JWT access token."""
    priv, _ = _load_or_generate_keys()
    now = datetime.now(timezone.utc)
    payload = {
        "sub":   user_id,
        "email": email,
        "tier":  tier,
        "iat":   now,
        "exp":   now + ACCESS_TOKEN_TTL,
        "jti":   str(uuid.uuid4()),   # unique token ID for future revocation list
        "type":  "access",
    }
    return jwt.encode(payload, priv.decode(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify an RS256 access token.
    Returns the payload dict or None on any error.
    Uses constant-time comparison internally via python-jose.
    """
    try:
        _, pub = _load_or_generate_keys()
        payload = jwt.decode(token, pub.decode(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


# ── Refresh token (opaque) ─────────────────────────────────────────────────────

def generate_refresh_token() -> str:
    """Generate a cryptographically secure opaque refresh token."""
    return secrets.token_hex(64)          # 128-char hex string = 512 bits


def hash_token(token: str) -> str:
    """SHA-256 hash a token for secure storage (never store raw refresh tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()


def constant_time_compare(a: str, b: str) -> bool:
    """Timing-safe string comparison."""
    return hmac.compare_digest(a.encode(), b.encode())


def build_binding_hash(user_agent: str, ip: str) -> str:
    """Create a hash of user_agent + IP for soft token binding."""
    raw = f"{user_agent}|{ip}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + REFRESH_TOKEN_TTL
