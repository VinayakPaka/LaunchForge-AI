"""
User and RefreshToken models.

RefreshToken design (RFC 6749 §10.4 — refresh token rotation):
  - Raw token is NEVER stored; only SHA-256(token) is persisted
  - Each refresh creates a new token and invalidates the old one
  - Tokens belong to a "family"; reuse of a revoked token triggers
    family-wide revocation (detects token theft)
  - Binding hash ties the token to a specific user_agent + IP
    for soft anomaly detection
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from models.pipeline import Base


class SubscriptionTier(str):
    FREE       = "free"
    PRO        = "pro"
    TEAM       = "team"
    ENTERPRISE = "enterprise"


# ── User ──────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Founder")
    tier: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "id":        self.id,
            "email":     self.email,
            "name":      self.name,
            "tier":      self.tier,
            "isActive":  self.is_active,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


# ── RefreshToken ──────────────────────────────────────────────────────────────
class RefreshToken(Base):
    """
    Stores hashed refresh tokens with rotation + family tracking.

    Columns
    -------
    token_hash   — SHA-256(raw_token); raw token is NEVER persisted
    user_id      — FK to users
    family       — UUID grouping tokens from the same login session;
                   reuse of a revoked token voids the whole family
    expires_at   — absolute expiry (UTC)
    used         — True after the token has been exchanged for a new one
    revoked      — True if explicitly revoked (logout) or family-voided
    binding_hash — SHA-256(user_agent|ip)[:32] for soft anomaly detection
    created_at   — issuance timestamp
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    family: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    binding_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
    )

    __table_args__ = (
        Index("ix_refresh_tokens_user_family", "user_id", "family"),
    )

    @property
    def is_valid(self) -> bool:
        """True if the token has not been used, revoked, or expired."""
        return (
            not self.used
            and not self.revoked
            and self.expires_at > datetime.utcnow()
        )
