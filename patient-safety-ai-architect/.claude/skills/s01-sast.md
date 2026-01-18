---
name: sast
description: Run Static Application Security Testing and generate SARIF + Markdown summary
user-invocable: true
---

# S1. SAST (Static Application Security Testing)

## Category
DETECT — Find code-level security vulnerabilities

## Owner
- **Security_Analyst (R)**: Execute scans and analyze results
- **Compliance_Expert_KR (C)**: Consulted on regulatory implications

---

## Goal
Detect code-level vulnerabilities (injection, XSS, insecure crypto, etc.) before merge/release.

---

## Tools
| Tool | Language | Purpose |
|------|----------|---------|
| Semgrep | Python, JS/TS | Pattern-based vulnerability detection |
| Bandit | Python | Python-specific security linter |
| ESLint (security plugin) | JS/TS | JavaScript security rules |

---

## Steps

### 1. Run SAST Scan

**Backend (Python)**
```bash
# Bandit
bandit -r backend/app -f sarif -o outputs/sast-backend.sarif

# Semgrep
semgrep --config=auto backend/app --sarif -o outputs/sast-semgrep-backend.sarif
```

**Frontend (TypeScript/React)**
```bash
# Semgrep
semgrep --config=auto frontend/src --sarif -o outputs/sast-frontend.sarif

# ESLint security
cd frontend && npx eslint src --format=json -o ../outputs/eslint-security.json
```

### 2. Analyze Results
```bash
# Count findings by severity
cat outputs/sast-*.sarif | jq '.runs[].results | group_by(.level) | map({level: .[0].level, count: length})'
```

### 3. Triage Findings

| Severity | Action Required |
|----------|-----------------|
| **Critical/High** | Must fix before release OR document exception |
| **Medium** | Create ticket with due date |
| **Low** | Document in backlog |

### 4. Generate Summary Report

---

## Output

### Files
- `outputs/sast-backend.sarif`
- `outputs/sast-frontend.sarif`
- `outputs/sast-summary.md`

### Summary Template

```markdown
# SAST Scan Summary

**Date**: YYYY-MM-DD
**Commit**: {sha}
**Scanner**: Bandit, Semgrep, ESLint

## Findings Summary
| Severity | Count | Fixed | Remaining |
|----------|-------|-------|-----------|
| Critical |       |       |           |
| High     |       |       |           |
| Medium   |       |       |           |
| Low      |       |       |           |

## Top Issues (High/Critical)

### 1. {Issue Title}
- **File**: `path/to/file.py:123`
- **CWE**: CWE-XXX
- **Description**:
- **Fix**:
- **Status**: [ ] Fixed / [ ] Exception

### 2. {Issue Title}
...

## Exceptions
| Finding | Reason | Approved By | Expiry |
|---------|--------|-------------|--------|
|         |        |             |        |

## Artifacts
- [Backend SARIF](outputs/sast-backend.sarif)
- [Frontend SARIF](outputs/sast-frontend.sarif)
```

---

## OWASP Top 10 Mapping

| OWASP | Common Findings |
|-------|-----------------|
| A01 Broken Access Control | Missing auth checks, IDOR |
| A02 Cryptographic Failures | Weak algorithms, hardcoded keys |
| A03 Injection | SQL injection, command injection, XSS |
| A07 Auth Failures | Weak passwords, session issues |

---

## Related Skills
- S2. SCA (`/sca`) — Dependency vulnerabilities
- S3. Secrets Scan (`/secrets-scan`) — Hardcoded secrets
- S15. Release Gate (`/release-gate`) — Final decision
