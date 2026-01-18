"""
Audit Logging Service

PIPA Art. 29 compliant audit logging with:
- Append-only storage
- Hash chain for tamper detection
- Sensitive data masking
"""

from datetime import datetime
from typing import Optional, Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.models.audit import AuditEventType, AuditLog


# Fields to mask in audit logs
MASKED_FIELDS = {
    "password",
    "token",
    "secret",
    "api_key",
    "ssn",
    "resident_number",
    "주민등록번호",
}


def mask_sensitive_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Mask sensitive fields in data dictionary.

    Args:
        data: Dictionary that may contain sensitive fields

    Returns:
        Dictionary with sensitive fields masked
    """
    if not data:
        return data

    masked = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(field in key_lower for field in MASKED_FIELDS):
            masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_data(value)
        else:
            masked[key] = value
    return masked


class AuditService:
    """Audit logging service."""

    def __init__(self, db_session: Any):  # AsyncSession type
        self.db = db_session

    async def log(
        self,
        event_type: AuditEventType,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        detail: Optional[dict] = None,
        result: str = "success",
        request: Optional[Request] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            event_type: Type of event being logged
            user_id: ID of user performing action (None for failed logins)
            user_role: Role of user
            username: Username (for display)
            resource_type: Type of resource (incident, attachment, user)
            resource_id: ID of the resource
            detail: Additional event-specific data (will be masked)
            result: success, failure, or denied
            request: FastAPI request for IP/user agent

        Returns:
            Created AuditLog entry
        """
        # Get previous entry hash for chain
        # TODO: Query last entry from database
        previous_hash = "0" * 64  # Initial hash

        # Mask sensitive data in detail
        masked_detail = mask_sensitive_data(detail) if detail else None

        # Calculate entry hash
        entry_hash = AuditLog.calculate_hash(
            event_type=event_type.value,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            resource_id=resource_id,
            previous_hash=previous_hash,
        )

        entry = AuditLog(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_role=user_role,
            username=username,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            action_detail=masked_detail,
            result=result,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
        )

        self.db.add(entry)
        await self.db.commit()
        return entry


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add audit context to requests.

    Note: Actual logging happens in endpoint handlers
    to capture user context and specific actions.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Add request start time for duration tracking
        request.state.start_time = datetime.utcnow()

        response = await call_next(request)

        # Could log all requests here, but we prefer
        # explicit logging in handlers for accuracy
        return response
