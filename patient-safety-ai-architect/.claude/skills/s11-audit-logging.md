---
name: audit-logging
description: Implement and verify audit logging for incident data access and modifications
user-invocable: true
---

# S11. Audit Logging

## Category
DEFEND — Evidence trail for compliance and security

## Owner
- **Security_Analyst (R)**: Design and implement logging
- **Compliance_Expert_KR (A)**: Approve retention policy

---

## Goal
Log all access/update/export/download events for incident records and attachments to support PIPA compliance and security investigations.

---

## Events to Log

### Required Events (PIPA Art. 29)

| Event Type | Trigger | Data Captured |
|------------|---------|---------------|
| AUTH_LOGIN | User login | user_id, timestamp, IP, user_agent, result |
| AUTH_LOGOUT | User logout | user_id, timestamp |
| AUTH_FAILED | Failed login | username_attempt, timestamp, IP, reason |
| INCIDENT_VIEW | View incident | user_id, incident_id, timestamp |
| INCIDENT_CREATE | Create incident | user_id, incident_id, timestamp |
| INCIDENT_UPDATE | Edit incident | user_id, incident_id, fields_changed, old_values, new_values |
| INCIDENT_DELETE | Delete/archive | user_id, incident_id, timestamp, reason |
| INCIDENT_EXPORT | Export data | user_id, query_params, record_count, format |
| ATTACHMENT_UPLOAD | Upload file | user_id, incident_id, file_id, filename, size |
| ATTACHMENT_DOWNLOAD | Download file | user_id, file_id, timestamp |
| ATTACHMENT_DELETE | Delete file | user_id, file_id, timestamp, reason |
| APPROVAL_ACTION | Approve/reject | user_id, incident_id, action, level |
| PERMISSION_CHANGE | Role change | admin_id, target_user_id, old_role, new_role |

---

## Steps

### 1. Design Audit Schema

```python
# backend/app/models/audit.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum
from app.database import Base
import enum

class AuditEventType(str, enum.Enum):
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    AUTH_FAILED = "auth_failed"
    INCIDENT_VIEW = "incident_view"
    INCIDENT_CREATE = "incident_create"
    INCIDENT_UPDATE = "incident_update"
    INCIDENT_DELETE = "incident_delete"
    INCIDENT_EXPORT = "incident_export"
    ATTACHMENT_UPLOAD = "attachment_upload"
    ATTACHMENT_DOWNLOAD = "attachment_download"
    ATTACHMENT_DELETE = "attachment_delete"
    APPROVAL_ACTION = "approval_action"
    PERMISSION_CHANGE = "permission_change"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(AuditEventType), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    user_id = Column(Integer, index=True)  # nullable for failed logins
    user_role = Column(String(50))
    ip_address = Column(String(45))  # IPv6 max length
    user_agent = Column(String(500))
    resource_type = Column(String(50))  # incident, attachment, user
    resource_id = Column(String(100))
    action_detail = Column(JSON)  # flexible field for event-specific data
    result = Column(String(20))  # success, failure, denied

    # Tamper detection
    previous_hash = Column(String(64))
    entry_hash = Column(String(64))
```

### 2. Implement Logging Service

```python
# backend/app/security/audit.py
import hashlib
import json
from datetime import datetime

class AuditService:
    def __init__(self, db_session):
        self.db = db_session

    async def log(
        self,
        event_type: AuditEventType,
        user_id: int = None,
        resource_type: str = None,
        resource_id: str = None,
        detail: dict = None,
        result: str = "success",
        request: Request = None
    ):
        # Get previous hash for chain
        last_entry = await self._get_last_entry()
        previous_hash = last_entry.entry_hash if last_entry else "0" * 64

        entry = AuditLog(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            action_detail=detail,
            result=result,
            previous_hash=previous_hash
        )

        # Calculate entry hash
        entry.entry_hash = self._calculate_hash(entry, previous_hash)

        self.db.add(entry)
        await self.db.commit()

    def _calculate_hash(self, entry, previous_hash):
        data = f"{entry.event_type}|{entry.timestamp}|{entry.user_id}|{previous_hash}"
        return hashlib.sha256(data.encode()).hexdigest()
```

### 3. Integrate with Endpoints

```python
# Example: Incident view endpoint
@router.get("/incidents/{id}")
async def get_incident(
    id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service)
):
    incident = await get_incident_by_id(id)

    # Log access
    await audit.log(
        event_type=AuditEventType.INCIDENT_VIEW,
        user_id=current_user.id,
        resource_type="incident",
        resource_id=id,
        request=request
    )

    return incident
```

### 4. Implement Masking Rules

```python
# Mask sensitive data in logs
MASKED_FIELDS = ["password", "token", "secret", "ssn", "resident_number"]

def mask_sensitive(data: dict) -> dict:
    if not data:
        return data
    masked = {}
    for key, value in data.items():
        if any(f in key.lower() for f in MASKED_FIELDS):
            masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked[key] = mask_sensitive(value)
        else:
            masked[key] = value
    return masked
```

### 5. Verify Implementation

---

## Output

### Files
- `backend/app/models/audit.py`
- `backend/app/security/audit.py`
- `outputs/audit-logging-review.md`

### Review Template

```markdown
# Audit Logging Review

**Date**: YYYY-MM-DD
**Reviewer**: {name}

## Event Coverage
| Event Type | Implemented | Tested | Notes |
|------------|-------------|--------|-------|
| AUTH_LOGIN | ✓ | ✓ | |
| AUTH_LOGOUT | ✓ | ✓ | |
| AUTH_FAILED | ✓ | ✓ | |
| INCIDENT_VIEW | ✓ | ✓ | |
| INCIDENT_CREATE | ✓ | ✓ | |
| INCIDENT_UPDATE | ✓ | ✓ | Fields tracked |
| INCIDENT_DELETE | ✓ | ✓ | Soft delete only |
| INCIDENT_EXPORT | ✓ | ✓ | Count logged |
| ATTACHMENT_UPLOAD | ✓ | ✓ | |
| ATTACHMENT_DOWNLOAD | ✓ | ✓ | |
| ATTACHMENT_DELETE | ✓ | ✓ | |
| APPROVAL_ACTION | ✓ | ✓ | |
| PERMISSION_CHANGE | ✓ | ✓ | |

## Data Captured
- [ ] User ID captured
- [ ] Timestamp (UTC) captured
- [ ] IP address captured
- [ ] Resource identifiers captured
- [ ] Action details captured
- [ ] Result status captured

## Security Measures
- [ ] Append-only (no UPDATE/DELETE on audit table)
- [ ] Hash chain for tamper detection
- [ ] Sensitive data masked
- [ ] Separate access control for audit queries

## Retention
- Retention period: 5 years
- Archive strategy: {describe}
- Disposal method: {describe}

## Issues Found
| # | Issue | Severity | Status |
|---|-------|----------|--------|
|   |       |          |        |

## Test Cases
- [ ] Login success logged
- [ ] Login failure logged
- [ ] View incident logged
- [ ] Update with field changes logged
- [ ] Export with count logged
- [ ] Hash chain integrity verified
```

---

## Retention & PIPA Linkage

| Requirement | Implementation |
|-------------|----------------|
| PIPA Art. 29 (Security measures) | Audit logging enabled |
| PIPA Art. 21 (Retention limits) | 5-year retention, then secure delete |
| Evidence for data subject requests | Query by user_id, resource_id |

---

## Related Skills
- S7. PIPA Evidence (`/pipa-evidence`) — Links to audit policy
- S10. Access Control (`/access-control`) — Events to log
- S15. Release Gate (`/release-gate`) — Audit implementation required
