## Project scope (Phase 1)
- Internal-only QI system for a Korean long-term care hospital.
- No EMR integration.
- Phase 1 features: Incident intake (Common page) + Fall details + Medication details + Approvals + Actions + Attachments (local storage).

## Hard rules
- No real PII in code, tests, examples, or logs. Use pseudonyms only.
- If legal interpretation is unclear: escalate to DPO/legal; do not self-finalize.
- All releases must pass the Release Gate.
- All outputs must be reproducible and stored as Markdown + CI artifacts (SARIF/JSON where applicable).

## Core workflow (Incident → Risk management)
1. Intake incident (Common page) with required fields.
2. Triage severity (grade) and categorize.
3. If high-risk or repeated: initiate RCA and/or process improvement.
4. Track CAPA actions with owner/due-date/DoD and evidence attachments.
5. Approvals: QPS → Vice Chair → Director.
6. Close incident only when actions are verified.

## Form rules (Common page)
- immediate_action is REQUIRED for all incidents.
- reported_at is REQUIRED and must include date + optional time (store as datetime).
- reporter_name:
  - Optional ONLY if grade == NEAR_MISS
  - Required for all other grades

## Release Gate (PASS/FAIL)
FAIL if any:
- Required evidence missing (per workflow).
- High/Critical security findings unresolved without approved exception.
- Scan execution failed or artifacts missing (SARIF/SBOM/etc.).
PASS when:
- High = 0, Medium has plan + due date.
- Required Markdown reports exist and are linked in PR.

## Output templates (Markdown)

### T1. Security Review Report
- Scope (repo/commit/env)
- Summary (Critical/High/Medium/Low)
- Top 3–5 issues (evidence/impact/fix/repro)
- Full list links
- Gate decision + follow-up tickets

### T2. Incident Intake Record (Common page)
- Incident metadata (category/grade/occurred_at/location)
- Description
- Immediate action (required)
- Root cause (optional)
- Improvements (optional)
- Actions created (owner/due/DoD)
- Approval status (QPS/Vice Chair/Director)

## Storage (Phase 1)
- Attachments saved locally under: uploads/incidents/{incident_id}/...
- DB stores storage_uri using file:// style URI.

## Evidence locations (SSOT)
- docs/: Human-readable evidence (Markdown)
- CI artifacts: SARIF/JSON and scan logs
- Database: audit logs / incident records (no unnecessary PII)

## Escalation
- DPO / Legal: PIPA interpretation, retention, disposal, outsourcing/3rd party issues.
- Hospital security officer: infrastructure/security policy conflicts.

## Plugin & Tool Usage Guide

### Available Plugins
| Plugin | Command/Usage | Purpose |
|--------|---------------|---------|
| **feature-dev** | `/feature-dev` | Guided feature development with architecture focus |
| **frontend-design** | `/frontend-design` | High-quality UI/UX design for React components |
| **playwright** | MCP tools `mcp__playwright__*` | Browser automation & E2E testing |
| **context7** | MCP tools `mcp__context7__*` | Latest library documentation lookup |
| **hookify** | `/hookify` | Create and manage Claude Code hooks |

### When to Use Each Plugin

#### feature-dev
Use for new feature implementation:
- Adding new API endpoints
- Creating new pages/components
- Implementing complex business logic

#### frontend-design
Use for UI work:
- Designing new pages (IndicatorList, IndicatorForm, etc.)
- Improving existing component designs
- Creating responsive layouts

#### playwright (MCP)
Use for testing:
```
mcp__playwright__browser_navigate → Navigate to page
mcp__playwright__browser_snapshot → Capture page state
mcp__playwright__browser_click → Interact with elements
```

#### context7 (MCP)
Use for documentation lookup:
```
mcp__context7__resolve-library-id → Find library ID
mcp__context7__query-docs → Get latest docs (React, FastAPI, SQLAlchemy, etc.)
```

### Project-Specific Hooks
Located in `.claude/hooks/`:
- `pii-protection.md` - Prevents real PII in code
- `security-check.md` - Blocks security vulnerabilities
- `api-schema-sync.md` - Ensures model/schema sync
- `rbac-check.md` - Verifies API authorization
- `migration-reminder.md` - Reminds Alembic migrations
- `test-reminder.md` - Prompts test updates
