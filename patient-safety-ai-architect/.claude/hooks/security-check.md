---
event: PreToolUse
tools:
  - Write
  - Edit
match_files:
  - "**/*.py"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.env*"
---

# Security Check Hook

## Purpose
Prevent security vulnerabilities per CLAUDE.md Release Gate requirements.

## Pre-Write Security Checks

### Prohibited Patterns
1. **Hardcoded Secrets**
   - API keys, passwords, tokens
   - Database connection strings with credentials
   - JWT secrets

2. **SQL Injection Risks**
   - String concatenation in SQL queries
   - Unparameterized queries

3. **XSS Vulnerabilities**
   - dangerouslySetInnerHTML without sanitization
   - Unescaped user input in templates

4. **PIPA/Privacy Violations**
   - Logging PII without masking
   - Storing sensitive data unencrypted

### Required Patterns
1. Use environment variables for secrets
2. Use parameterized queries (SQLAlchemy ORM)
3. Validate and sanitize all user inputs
4. Use RBAC for authorization checks

## Action on Detection
1. BLOCK the write operation
2. Explain the security risk
3. Provide secure alternative code
