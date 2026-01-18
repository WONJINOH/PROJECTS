---
name: secrets-scan
description: Detect hardcoded secrets and provide revocation/rotation steps
user-invocable: true
---

# S3. Secrets Scan

## Category
DETECT — Find hardcoded secrets (keys, tokens, passwords)

## Owner
- **Security_Analyst (R)**: Execute scans and coordinate revocation
- **Compliance_Expert_KR (I)**: Informed of incidents

---

## Goal
Detect hardcoded secrets before they reach the repository and ensure proper revocation/rotation if found.

---

## Tools
| Tool | Purpose |
|------|---------|
| Gitleaks | Git history & file scanning |
| TruffleHog | High-entropy string detection |
| detect-secrets | Yelp's secret detection |
| GitHub Secret Scanning | Native GitHub feature |

---

## Steps

### 1. Run Secrets Scan

**Full Repository Scan**
```bash
# Gitleaks (recommended)
gitleaks detect --source . --report-format sarif --report-path outputs/secrets-scan.sarif

# Include git history
gitleaks detect --source . --report-format sarif --report-path outputs/secrets-history.sarif --log-opts="--all"
```

**Pre-commit Hook (Prevention)**
```bash
# Install pre-commit
pip install pre-commit

# Add to .pre-commit-config.yaml
# - repo: https://github.com/gitleaks/gitleaks
#   rev: v8.18.0
#   hooks:
#     - id: gitleaks
```

### 2. Classify Findings

| Type | Examples | Risk Level |
|------|----------|------------|
| API Keys | AWS, GCP, Azure keys | Critical |
| Database Credentials | Connection strings | Critical |
| JWT Secrets | Signing keys | High |
| OAuth Tokens | Access/refresh tokens | High |
| Private Keys | SSH, SSL certificates | Critical |
| Passwords | Hardcoded passwords | High |

### 3. Revocation/Rotation Protocol

**CRITICAL: If secrets are found in git history, assume compromised**

| Secret Type | Revocation Steps |
|-------------|------------------|
| AWS Keys | AWS Console → IAM → Deactivate → Create new |
| Database | Change password → Update connection strings |
| JWT Secret | Generate new → Invalidate existing tokens |
| API Tokens | Provider dashboard → Revoke → Generate new |

### 4. Remediation

```bash
# Remove from git history (if not pushed)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/secret/file" \
  --prune-empty --tag-name-filter cat -- --all

# Or use BFG Repo-Cleaner
bfg --delete-files secret-file.txt
```

---

## Output

### Files
- `outputs/secrets-scan.sarif`
- `outputs/secrets-summary.md`

### Summary Template

```markdown
# Secrets Scan Summary

**Date**: YYYY-MM-DD
**Commit**: {sha}
**Scanner**: Gitleaks v8.x

## Findings
| # | File | Line | Type | Status |
|---|------|------|------|--------|
| 1 |      |      |      |        |

## Summary
| Status | Count |
|--------|-------|
| Detected | |
| Revoked | |
| Rotated | |
| False Positive | |
| Pending | |

## Revocation Log
| Secret | Found In | Revoked At | New Secret Location |
|--------|----------|------------|---------------------|
|        |          |            |                     |

## Prevention Measures
- [ ] Pre-commit hook installed
- [ ] .gitignore updated
- [ ] .env.example created (no real values)
- [ ] Secrets moved to environment variables
- [ ] Team notified of incident

## False Positives
| File | Pattern | Reason |
|------|---------|--------|
|      |         |        |

Add to `.gitleaksignore`:
```
# path/to/file:line
```

## Artifacts
- [Secrets SARIF](outputs/secrets-scan.sarif)
```

---

## Prevention Checklist

- [ ] `.gitignore` includes `.env`, `*.key`, `*.pem`, `credentials.*`
- [ ] `.env.example` has placeholder values only
- [ ] Pre-commit hooks configured
- [ ] CI/CD uses secrets manager (not env files)
- [ ] Team trained on secret handling

---

## Related Skills
- S1. SAST (`/sast`) — Code vulnerabilities
- S2. SCA (`/sca`) — Dependency vulnerabilities
- S12. Cryptography (`/cryptography`) — Key management
- S15. Release Gate (`/release-gate`) — Final decision
