---
event: PreToolUse
tools:
  - Write
  - Edit
  - Bash
---

# PII Protection Hook

## Purpose
Prevent accidental inclusion of real PII in code, tests, or logs per CLAUDE.md rules.

## Check Before Writing

### Prohibited Patterns
- Real Korean names (use pseudonyms: 김간호, 이의사, 박환자)
- Real phone numbers (use: 010-0000-0000)
- Real email addresses (use: test@example.com)
- Real patient IDs or registration numbers
- Real addresses

### Allowed Pseudonyms
- Names: 김간호, 이의사, 박환자, 최보호자, 정관리자
- Departments: 내과, 외과, 정형외과, 신경과
- Locations: 301호, 402호, 물리치료실, 간호스테이션

## Action
If real PII is detected:
1. BLOCK the operation
2. Suggest using pseudonyms instead
3. Reference CLAUDE.md PII rules
