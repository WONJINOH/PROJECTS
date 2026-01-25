"""
Audit Log Model

PIPA Art. 29 compliant audit logging.
Events logged:
- Authentication (login/logout/failed)
- Incident access (view/create/update/delete)
- Attachment operations (upload/download/delete)
- Approval actions
- Permission changes

Features:
- Append-only (no UPDATE/DELETE)
- Hash chain for tamper detection
- Sensitive data masking
"""

import enum
import hashlib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Enum, JSON, Text

from app.database import Base


class AuditEventType(str, enum.Enum):
    """Audit event types."""

    # Authentication
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    AUTH_FAILED = "auth_failed"

    # Incident operations
    INCIDENT_VIEW = "incident_view"
    INCIDENT_CREATE = "incident_create"
    INCIDENT_UPDATE = "incident_update"
    INCIDENT_DELETE = "incident_delete"
    INCIDENT_EXPORT = "incident_export"

    # Attachment operations
    ATTACHMENT_UPLOAD = "attachment_upload"
    ATTACHMENT_DOWNLOAD = "attachment_download"
    ATTACHMENT_DELETE = "attachment_delete"

    # Approval operations
    APPROVAL_ACTION = "approval_action"

    # Permission operations
    PERMISSION_CHANGE = "permission_change"

    # Risk operations
    RISK_CREATE = "risk_create"
    RISK_UPDATE = "risk_update"
    RISK_VIEW = "risk_view"
    RISK_ESCALATE = "risk_escalate"
    RISK_ASSESSMENT = "risk_assessment"


class AuditLog(Base):
    """Audit log entry (append-only)."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Event details
    event_type = Column(
        Enum(AuditEventType, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
        index=True
    )
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Actor
    user_id = Column(Integer, nullable=True, index=True)  # nullable for failed logins
    user_role = Column(String(50), nullable=True)
    username = Column(String(50), nullable=True)

    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)

    # Resource
    resource_type = Column(String(50), nullable=True)  # incident, attachment, user
    resource_id = Column(String(100), nullable=True)

    # Event-specific data (JSON)
    action_detail = Column(JSON, nullable=True)

    # Result
    result = Column(String(20), nullable=False)  # success, failure, denied

    # Tamper detection (hash chain)
    previous_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog {self.id} ({self.event_type.value})>"

    @staticmethod
    def calculate_hash(
        event_type: str,
        timestamp: datetime,
        user_id: Optional[int],
        resource_id: Optional[str],
        previous_hash: str,
    ) -> str:
        """Calculate SHA-256 hash for tamper detection."""
        data = f"{event_type}|{timestamp.isoformat()}|{user_id}|{resource_id}|{previous_hash}"
        return hashlib.sha256(data.encode()).hexdigest()
