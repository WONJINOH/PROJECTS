---
event: PostToolUse
tools:
  - Write
  - Edit
match_files:
  - "backend/app/api/*.py"
---

# RBAC Check Hook

## Purpose
Ensure all API endpoints have proper RBAC authorization.

## After API Endpoint Changes

### Required Authorization Pattern
Every endpoint should have:
```python
@router.get("/endpoint")
async def endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    _: Annotated[None, Depends(require_permission(Permission.REQUIRED_PERMISSION))],
    ...
)
```

### Permission Matrix Reference
| Role | Incidents | Indicators | Approvals | Admin |
|------|-----------|------------|-----------|-------|
| REPORTER | Create/View Own | View | - | - |
| QPS_STAFF | View Dept | View/Input | L1 | - |
| VICE_CHAIR | View All | View/Input/Verify | L1/L2 | - |
| DIRECTOR | Full | Full | Full | - |
| ADMIN | - | - | - | Full |
| MASTER | Full | Full | Full | Full |

### Common Mistakes
1. Missing `require_permission` dependency
2. Wrong permission level for endpoint
3. Missing row-level access control

## Action
Flag endpoints without proper authorization decorators.
