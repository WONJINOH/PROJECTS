"""
Action Model

CAPA (Corrective and Preventive Action) tracking with:
- owner: 담당자
- due_date: 기한
- definition_of_done (DoD): 완료 기준
- status: OPEN → IN_PROGRESS → COMPLETED → VERIFIED
- evidence_attachment_id: 증거 첨부
"""

import enum
from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Date, Enum, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class ActionStatus(str, enum.Enum):
    """Action status lifecycle."""

    OPEN = "open"                 # 신규 생성됨
    IN_PROGRESS = "in_progress"  # 진행 중
    COMPLETED = "completed"      # 완료됨 (검증 대기)
    VERIFIED = "verified"        # 검증 완료
    CANCELLED = "cancelled"      # 취소됨


class ActionPriority(str, enum.Enum):
    """Action priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Action(Base):
    """CAPA action model for incident follow-up."""

    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)

    # References
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True, index=True)
    risk_id = Column(Integer, ForeignKey("risks.id"), nullable=True, index=True)  # 위험 연결

    # === Core Fields ===
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # CAPA Required Fields
    owner = Column(String(100), nullable=False)  # 담당자
    due_date = Column(Date, nullable=False)      # 기한
    definition_of_done = Column(Text, nullable=False)  # DoD (완료 기준)

    # Status tracking
    status = Column(
        Enum(ActionStatus),
        default=ActionStatus.OPEN,
        nullable=False,
        index=True
    )
    priority = Column(
        Enum(ActionPriority),
        default=ActionPriority.MEDIUM,
        nullable=False
    )

    # Evidence attachment (optional, linked when completed)
    evidence_attachment_id = Column(
        Integer, ForeignKey("attachments.id"), nullable=True
    )

    # Completion tracking
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    completion_notes = Column(Text, nullable=True)

    # Verification tracking
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verification_notes = Column(Text, nullable=True)

    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Boolean, default=False)

    # Relationships
    incident = relationship("Incident", back_populates="actions")
    risk = relationship("Risk", backref="actions")  # 위험 연결
    evidence_attachment = relationship(
        "Attachment",
        foreign_keys=[evidence_attachment_id]
    )
    created_by = relationship(
        "User",
        foreign_keys=[created_by_id],
        back_populates="created_actions"
    )
    completed_by = relationship(
        "User",
        foreign_keys=[completed_by_id]
    )
    verified_by = relationship(
        "User",
        foreign_keys=[verified_by_id]
    )

    def __repr__(self) -> str:
        return f"<Action {self.id} ({self.title[:30]}... - {self.status.value})>"

    def is_overdue(self) -> bool:
        """Check if action is past due date and not completed."""
        if self.status in [ActionStatus.COMPLETED, ActionStatus.VERIFIED, ActionStatus.CANCELLED]:
            return False
        return date.today() > self.due_date

    def can_complete(self) -> bool:
        """Check if action can be marked as completed."""
        return self.status in [ActionStatus.OPEN, ActionStatus.IN_PROGRESS]

    def can_verify(self) -> bool:
        """Check if action can be verified."""
        return self.status == ActionStatus.COMPLETED
