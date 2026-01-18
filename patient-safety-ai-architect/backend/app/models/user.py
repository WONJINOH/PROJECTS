"""
User Model

Roles:
- REPORTER: 보고자 (incident reporter)
- QPS_STAFF: QI담당자 (Quality & Patient Safety staff)
- VICE_CHAIR: 부원장 (Vice Chairman)
- DIRECTOR: 원장 (Director)
- ADMIN: 시스템관리자 (System Admin)
- MASTER: 슈퍼유저 (all permissions)
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Role(str, enum.Enum):
    """User roles for RBAC."""

    REPORTER = "reporter"
    QPS_STAFF = "qps_staff"
    VICE_CHAIR = "vice_chair"
    DIRECTOR = "director"
    ADMIN = "admin"
    MASTER = "master"


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(Role), default=Role.REPORTER, nullable=False)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    incidents = relationship("Incident", back_populates="reporter")
    approvals = relationship("Approval", back_populates="approver")

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"
