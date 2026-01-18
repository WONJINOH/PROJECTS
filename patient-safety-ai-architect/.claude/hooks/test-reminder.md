---
event: PostToolUse
tools:
  - Write
  - Edit
match_files:
  - "backend/app/api/*.py"
  - "backend/app/models/*.py"
  - "frontend/src/pages/*.tsx"
  - "frontend/src/components/*.tsx"
---

# Test Reminder Hook

## Purpose
Remind to write/update tests after code changes.

## After Code Changes

### Backend Changes
When modifying:
- `backend/app/api/*.py` → Update `backend/tests/api/test_*.py`
- `backend/app/models/*.py` → Update `backend/tests/models/test_*.py`
- `backend/app/schemas/*.py` → Update schema validation tests

### Frontend Changes
When modifying:
- `frontend/src/pages/*.tsx` → Consider E2E tests
- `frontend/src/components/*.tsx` → Update component tests

## Test Coverage Requirements
Per CLAUDE.md Release Gate:
- All new API endpoints must have tests
- Critical business logic must have unit tests
- Integration tests for approval workflows

## Reminder Message
"Tests may need updating for the modified files. Run:
- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm test`"
