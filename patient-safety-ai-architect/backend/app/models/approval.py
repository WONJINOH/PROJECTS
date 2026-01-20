"""
Approval Model

3-level approval workflow:
- L1: QPS Staff (QI담당자)
- L2: Vice Chair (부원장)
- L3: Director (원장)
"""

import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ApprovalLevel(str, enum.Enum):
    """Approval levels."""

    L1_QPS = "l1_qps"          # QPS Staff
    L2_VICE_CHAIR = "l2_vice_chair"  # Vice Chair
    L3_DIRECTOR = "l3_director"      # Director


class ApprovalStatus(str, enum.Enum):
    """Approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Approval(Base):
    """Incident approval record."""

    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)

    # References
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Approval details
    level = Column(Enum(ApprovalLevel), nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    comment = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    decided_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")

    def __repr__(self) -> str:
        return f"<Approval {self.id} ({self.level.value}: {self.status.value})>"
