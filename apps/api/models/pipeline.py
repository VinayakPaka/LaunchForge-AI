"""SQLAlchemy models for pipeline jobs and agent statuses."""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import enum


class Base(DeclarativeBase):
    pass


class PipelineStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    PARTIAL = "partial"


class AgentStatus(str, enum.Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, default="anonymous")
    idea_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=PipelineStatus.RUNNING)
    # JSON blob storing per-agent statuses and outputs
    agents_state: Mapped[dict] = mapped_column(JSON, default=dict)
    deploy_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    package_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "pipelineId": self.id,
            "userId": self.user_id,
            "ideaText": self.idea_text,
            "status": self.status,
            "agents": self.agents_state or {},
            "deployUrl": self.deploy_url,
            "packageUrl": self.package_url,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
        }
