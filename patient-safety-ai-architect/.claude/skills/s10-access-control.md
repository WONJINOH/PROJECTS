---
name: access-control
description: Review and implement RBAC for incident records access
user-invocable: true
---

# S10. Access Control Review (RBAC)

## Category
DEFEND — Protect personal data through authorization controls

## Owner
- **Security_Analyst (R)**: Design and implement RBAC
- **Compliance_Expert_KR (C)**: Validate against PIPA requirements

---

## Goal
Ensure only authorized roles can view/edit/export/delete incident records and attachments.

---

## Role Definitions

### Patient Safety System Roles

| Role | Korean | Description |
|------|--------|-------------|
| REPORTER | 보고자 | Staff who reports incidents |
| QPS_STAFF | QI담당자 | Quality & Patient Safety team |
| VICE_CHAIR | 부원장 | Department head, L2 approver |
| DIRECTOR | 원장 | Hospital director, L3 approver |
| ADMIN | 시스템관리자 | System configuration only |

---

## Permission Matrix

### Incident Records

| Permission | REPORTER | QPS_STAFF | VICE_CHAIR | DIRECTOR | ADMIN |
|------------|----------|-----------|------------|----------|-------|
| Create | ✓ (any) | ✓ (any) | ✓ (any) | ✓ (any) | ✗ |
| View Own | ✓ | ✓ | ✓ | ✓ | ✗ |
| View Dept | ✗ | ✓ | ✓ | ✓ | ✗ |
| View All | ✗ | ✗ | ✓ | ✓ | ✗ |
| Edit Own | ✓ (draft) | ✓ | ✓ | ✓ | ✗ |
| Edit Any | ✗ | ✓ (dept) | ✓ | ✓ | ✗ |
| Delete | ✗ | ✗ | ✗ | ✓ (archive) | ✗ |
| Export | ✗ | ✓ (dept) | ✓ | ✓ | ✗ |

### Attachments

| Permission | REPORTER | QPS_STAFF | VICE_CHAIR | DIRECTOR | ADMIN |
|------------|----------|-----------|------------|----------|-------|
| Upload | ✓ (own) | ✓ | ✓ | ✓ | ✗ |
| Download | ✓ (own) | ✓ (dept) | ✓ | ✓ | ✗ |
| Delete | ✗ | ✓ (own upload) | ✓ | ✓ | ✗ |

### Approvals

| Permission | REPORTER | QPS_STAFF | VICE_CHAIR | DIRECTOR | ADMIN |
|------------|----------|-----------|------------|----------|-------|
| Approve L1 | ✗ | ✓ | ✓ | ✓ | ✗ |
| Approve L2 | ✗ | ✗ | ✓ | ✓ | ✗ |
| Approve L3 | ✗ | ✗ | ✗ | ✓ | ✗ |
| Reject | ✗ | ✓ | ✓ | ✓ | ✗ |

---

## Steps

### 1. Review Current Implementation

```bash
# Find RBAC-related code
grep -r "role" backend/app/security/ --include="*.py"
grep -r "permission" backend/app/api/ --include="*.py"
```

### 2. Verify Permission Checks

**Every endpoint must have:**
```python
# Example: FastAPI dependency
from app.security.rbac import require_permission, Permission

@router.get("/incidents/{id}")
async def get_incident(
    id: int,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_permission(Permission.VIEW_INCIDENT))
):
    # Also check row-level access
    incident = await get_incident_by_id(id)
    if not can_access_incident(current_user, incident):
        raise HTTPException(403, "Access denied")
    return incident
```

### 3. Test Access Control

```python
# Test cases to verify
def test_reporter_cannot_view_others_incident():
    ...

def test_qps_staff_can_view_department_incidents():
    ...

def test_director_can_view_all_incidents():
    ...

def test_admin_cannot_access_incident_data():
    ...
```

### 4. Document Findings

---

## Output

### Files
- `outputs/rbac-matrix.md`
- `backend/tests/test_access_control.py`

### Review Template

```markdown
# Access Control Review

**Date**: YYYY-MM-DD
**Reviewer**: {name}
**Scope**: backend/app/api/, backend/app/security/

## Endpoints Reviewed
| Endpoint | Method | Required Permission | Row-Level Check | Status |
|----------|--------|---------------------|-----------------|--------|
| /incidents | GET | VIEW_INCIDENT | Yes (dept filter) | ✓ |
| /incidents | POST | CREATE_INCIDENT | N/A | ✓ |
| /incidents/{id} | GET | VIEW_INCIDENT | Yes | ✓ |
| /incidents/{id} | PUT | EDIT_INCIDENT | Yes (owner/role) | ✓ |
| /incidents/{id}/approve | POST | APPROVE_L{n} | Yes (level) | ✓ |
| /attachments/{id} | GET | VIEW_ATTACHMENT | Yes (incident) | ✓ |

## Issues Found
| # | Endpoint | Issue | Severity | Status |
|---|----------|-------|----------|--------|
| 1 |          |       |          |        |

## Test Coverage
- [ ] Unit tests for each permission
- [ ] Integration tests for role combinations
- [ ] Negative tests (unauthorized access)

## Recommendations
1.
2.

## Approval
- [ ] Security_Analyst reviewed
- [ ] Test cases pass
```

---

## Implementation Reference

### Backend Structure
```
backend/app/security/
├── rbac.py          # Role & permission definitions
├── dependencies.py  # FastAPI auth dependencies
└── policies.py      # Row-level access policies
```

### Key Code Patterns

```python
# rbac.py
from enum import Enum

class Role(str, Enum):
    REPORTER = "reporter"
    QPS_STAFF = "qps_staff"
    VICE_CHAIR = "vice_chair"
    DIRECTOR = "director"
    ADMIN = "admin"

class Permission(str, Enum):
    CREATE_INCIDENT = "create_incident"
    VIEW_INCIDENT = "view_incident"
    EDIT_INCIDENT = "edit_incident"
    DELETE_INCIDENT = "delete_incident"
    EXPORT_INCIDENT = "export_incident"
    APPROVE_L1 = "approve_l1"
    APPROVE_L2 = "approve_l2"
    APPROVE_L3 = "approve_l3"

ROLE_PERMISSIONS = {
    Role.REPORTER: {Permission.CREATE_INCIDENT, Permission.VIEW_INCIDENT},
    Role.QPS_STAFF: {Permission.CREATE_INCIDENT, Permission.VIEW_INCIDENT,
                     Permission.EDIT_INCIDENT, Permission.EXPORT_INCIDENT,
                     Permission.APPROVE_L1},
    # ... etc
}
```

---

## Related Skills
- S7. PIPA Evidence (`/pipa-evidence`) — Compliance documentation
- S11. Audit Logging (`/audit-logging`) — Access event logging
- S15. Release Gate (`/release-gate`) — RBAC verification required
