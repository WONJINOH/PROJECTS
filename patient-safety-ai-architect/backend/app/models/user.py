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
from datetime import datetime, timezone
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


class UserStatus(str, enum.Enum):
    """User account status."""

    PENDING = "pending"        # 가입 승인 대기
    ACTIVE = "active"          # 활성
    DORMANT = "dormant"        # 휴면 (1년 이상 미접속)
    SUSPENDED = "suspended"    # 정지
    DELETED = "deleted"        # 삭제됨


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)  # 사원번호
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(
        Enum(Role, values_callable=lambda enum: [e.value for e in enum]),
        default=Role.REPORTER,
        nullable=False
    )
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    status = Column(
        Enum(UserStatus, values_callable=lambda enum: [e.value for e in enum]),
        default=UserStatus.PENDING,
        nullable=False
    )
    # Password management
    password_changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    password_expires_at = Column(DateTime(timezone=True), nullable=True)  # 6개월 후 만료
    # Account lifecycle
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_id = Column(Integer, nullable=True)
    dormant_at = Column(DateTime(timezone=True), nullable=True)  # 휴면 전환 일시
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # 삭제 예정 일시 (5년 후)

    # Relationships
    incidents = relationship("Incident", back_populates="reporter")
    approvals = relationship("Approval", back_populates="approver")
    created_actions = relationship(
        "Action",
        back_populates="created_by",
        foreign_keys="[Action.created_by_id]"
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"
