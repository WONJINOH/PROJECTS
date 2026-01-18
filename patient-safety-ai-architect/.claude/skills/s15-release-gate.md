---
name: release-gate
description: Evaluate release readiness based on security scans and PIPA evidence
user-invocable: true
---

# S15. Release Gate

## Category
DECIDE — Final pass/fail approval for merge/release

## Owner
- **Security_Analyst (R)**: Provides scan results and technical evidence
- **Compliance_Expert_KR (A)**: Final pass/fail approval

---

## Goal
Determine if the current codebase meets all security and compliance requirements for release.

---

## FAIL Conditions (must block)

Check each item. If ANY is true → **FAIL**

| # | Condition | Check Command |
|---|-----------|---------------|
| F1 | Scan execution failed (tool error/timeout) | Review CI logs |
| F2 | Required artifact missing (SARIF/JSON/Markdown) | `ls outputs/` |
| F3 | High/Critical findings unresolved WITHOUT exception | Review SARIF summaries |
| F4 | Secrets detected and not revoked/rotated | Check S3 output |
| F5 | PIPA evidence missing | Check `docs/pipa-*.md` exists |

---

## PASS Conditions

All must be true → **PASS**

| # | Condition | Evidence |
|---|-----------|----------|
| P1 | High/Critical = 0 (or exception approved with expiry + mitigation) | SARIF + exception log |
| P2 | Medium has remediation plan + due date | Ticket links |
| P3 | Required Markdown evidence exists and linked in PR | PR description |

---

## Steps

### 1. Collect Artifacts
```bash
# Check SARIF files exist
ls -la outputs/*.sarif 2>/dev/null || echo "NO SARIF FOUND"

# Check PIPA evidence
ls -la docs/pipa-*.md 2>/dev/null || echo "NO PIPA EVIDENCE"
```

### 2. Summarize Findings
```markdown
## Security Scan Summary
- SAST: X High / Y Medium / Z Low
- SCA: X High / Y Medium / Z Low
- Secrets: X detected (revoked: Y, pending: Z)
```

### 3. Evaluate Gate

```
IF High > 0 AND no_approved_exception:
    → FAIL (reason: unresolved High findings)

IF secrets_pending > 0:
    → FAIL (reason: secrets not revoked)

IF pipa_evidence_missing:
    → FAIL (reason: PIPA docs incomplete)

ELSE:
    → PASS
```

### 4. Generate Decision Report

Output to: `outputs/release-gate-decision.md`

---

## Output Template

```markdown
# Release Gate Decision

**Date**: YYYY-MM-DD
**Commit**: {sha}
**Reviewer**: {name}

## Summary
| Category | High | Medium | Low | Status |
|----------|------|--------|-----|--------|
| SAST     |      |        |     |        |
| SCA      |      |        |     |        |
| Secrets  |      |        |     |        |

## PIPA Evidence
- [ ] pipa-checklist.md
- [ ] pipa-retention-disposal.md
- [ ] pipa-access-control.md
- [ ] pipa-audit-logging.md

## Decision
**[ ] PASS** / **[ ] FAIL**

### Reason (if FAIL)
-

### Exceptions (if any)
| Finding ID | Reason | Expiry | Mitigation |
|------------|--------|--------|------------|
|            |        |        |            |

## Follow-up Tickets
- [ ]

---
Approved by: _________________ (Compliance_Expert_KR)
Date: _________________
```

---

## Related Skills
- S1. SAST (`/sast`)
- S2. SCA (`/sca`)
- S3. Secrets Scan (`/secrets-scan`)
- S7. PIPA Evidence (`/pipa-evidence`)
