---
name: sca
description: Scan dependencies for known vulnerabilities and recommend upgrades
user-invocable: true
---

# S2. SCA (Software Composition Analysis)

## Category
DETECT — Find vulnerable dependencies

## Owner
- **Security_Analyst (R)**: Execute scans and propose fixes
- **Compliance_Expert_KR (I)**: Informed of results

---

## Goal
Detect vulnerable dependencies and propose safe upgrades before they reach production.

---

## Tools
| Tool | Ecosystem | Purpose |
|------|-----------|---------|
| pip-audit | Python | PyPI vulnerability database |
| npm audit | Node.js | npm advisory database |
| Trivy | Multi | Container & dependency scanning |
| Dependabot | GitHub | Automated PRs for updates |

---

## Steps

### 1. Run SCA Scan

**Backend (Python)**
```bash
# pip-audit
pip-audit -r backend/requirements.txt -f json -o outputs/sca-python.json

# Or with Trivy
trivy fs backend/ --format sarif -o outputs/sca-trivy-backend.sarif
```

**Frontend (Node.js)**
```bash
# npm audit
cd frontend && npm audit --json > ../outputs/sca-npm.json

# Or with Trivy
trivy fs frontend/ --format sarif -o outputs/sca-trivy-frontend.sarif
```

### 2. Analyze Vulnerabilities

```bash
# Python - list vulnerable packages
pip-audit -r backend/requirements.txt

# Node.js - summary
npm audit --audit-level=moderate
```

### 3. Determine Upgrade Path

| Scenario | Action |
|----------|--------|
| Patch available | Upgrade immediately |
| Minor version fix | Test & upgrade |
| Major version required | Evaluate breaking changes |
| No fix available | Document exception + mitigation |

### 4. Create Remediation Plan

---

## Output

### Files
- `outputs/sca-python.json`
- `outputs/sca-npm.json`
- `outputs/sca-summary.md`

### Summary Template

```markdown
# SCA Scan Summary

**Date**: YYYY-MM-DD
**Commit**: {sha}

## Python Dependencies
| Package | Current | Vuln ID | Severity | Fixed In | Status |
|---------|---------|---------|----------|----------|--------|
|         |         |         |          |          |        |

## Node.js Dependencies
| Package | Current | Vuln ID | Severity | Fixed In | Status |
|---------|---------|---------|----------|----------|--------|
|         |         |         |          |          |        |

## Summary
| Severity | Python | Node.js | Total |
|----------|--------|---------|-------|
| Critical |        |         |       |
| High     |        |         |       |
| Medium   |        |         |       |
| Low      |        |         |       |

## Remediation Plan

### Immediate (Critical/High)
| Package | Action | Ticket | Due Date |
|---------|--------|--------|----------|
|         |        |        |          |

### Planned (Medium)
| Package | Action | Ticket | Due Date |
|---------|--------|--------|----------|
|         |        |        |          |

### Exceptions
| Package | Vulnerability | Reason | Mitigation | Expiry |
|---------|---------------|--------|------------|--------|
|         |               |        |            |        |

## Artifacts
- [Python SCA](outputs/sca-python.json)
- [npm audit](outputs/sca-npm.json)
```

---

## SBOM Integration

SCA results should feed into SBOM (Software Bill of Materials):

```bash
# Generate CycloneDX SBOM
cyclonedx-py environment -o outputs/sbom.json

# Include in release artifacts
```

---

## Related Skills
- S1. SAST (`/sast`) — Code vulnerabilities
- S3. Secrets Scan (`/secrets-scan`) — Hardcoded secrets
- S15. Release Gate (`/release-gate`) — Final decision
