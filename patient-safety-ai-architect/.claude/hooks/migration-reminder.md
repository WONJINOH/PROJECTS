---
event: PostToolUse
tools:
  - Write
  - Edit
match_files:
  - "backend/app/models/*.py"
---

# Migration Reminder Hook

## Purpose
Remind to create Alembic migrations after model changes.

## After Model Changes

### When Migration is Needed
- New model/table added
- Column added/removed/renamed
- Column type changed
- Relationship added/modified
- Index added/removed

### Migration Commands
```bash
cd backend

# Generate migration
alembic revision --autogenerate -m "description of changes"

# Review generated migration file
# Check: backend/alembic/versions/

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Pre-Migration Checklist
1. Backup database (production)
2. Review auto-generated migration
3. Test migration on dev environment
4. Check for data loss risks

## Reminder Message
"Model changes detected. Remember to:
1. Generate Alembic migration
2. Review the migration file
3. Test before applying to production"
