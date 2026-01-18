---
event: PostToolUse
tools:
  - Write
  - Edit
match_files:
  - "backend/app/models/*.py"
  - "backend/app/schemas/*.py"
---

# API Schema Sync Hook

## Purpose
Ensure backend models and schemas stay synchronized.

## After Modifying Models or Schemas

### Check Synchronization
1. Model field names match schema field names
2. Enum values are consistent between model and schema
3. Required/optional fields match
4. Type annotations are compatible

### Files to Cross-Check
- `backend/app/models/*.py` ↔ `backend/app/schemas/*.py`
- `backend/app/schemas/*.py` ↔ `frontend/src/types/index.ts`

### Common Issues
- snake_case (Python) vs camelCase (TypeScript) mismatch
- Missing field in schema after model update
- Enum value discrepancy

## Reminder
After model changes, remind user to:
1. Update corresponding schema
2. Update frontend types if API response changes
3. Run Alembic migration if DB schema changed
