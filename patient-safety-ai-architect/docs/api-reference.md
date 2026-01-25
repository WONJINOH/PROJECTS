# API Reference - Patient Safety QI System

**Version**: 1.0.0 (Phase 1 + 1.5)
**Base URL**: `/api`

## Authentication

All endpoints (except `/api/auth/login`) require JWT authentication.

### Headers

```
Authorization: Bearer <token>
Content-Type: application/json
```

---

## Auth API (`/api/auth`)

### POST `/auth/login`

Authenticate user and receive JWT token.

**Request Body** (form-urlencoded):
```
username=string&password=string
```

**Response** (200):
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errors**:
- `401`: Invalid credentials
- `403`: Account inactive

### POST `/auth/logout`

Log out current user.

**Response**: `204 No Content`

### GET `/auth/me`

Get current user profile.

**Response** (200):
```json
{
  "id": 1,
  "username": "qps_staff",
  "email": "qps@hospital.kr",
  "full_name": "QPS 담당자",
  "role": "qps_staff",
  "department": "환자안전팀",
  "is_active": true
}
```

### POST `/auth/register` (Admin only)

Register new user.

**Request Body**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string (min 8 chars)",
  "full_name": "string",
  "role": "reporter|qps_staff|vice_chair|director|admin|master",
  "department": "string (optional)"
}
```

**Response** (201): User object

---

## Incidents API (`/api/incidents`)

### GET `/incidents`

List incidents with pagination and filters.

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `skip` | int | Offset (default: 0) |
| `limit` | int | Limit (default: 50, max: 100) |
| `category` | string | Filter by category |
| `grade` | string | Filter by grade |
| `status` | string | Filter by status |
| `department` | string | Filter by department |

**Response** (200):
```json
{
  "items": [Incident],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

### POST `/incidents`

Create new incident.

**Request Body**:
```json
{
  "category": "fall|medication|pressure_ulcer|infection|...",
  "grade": "near_miss|no_harm|mild|moderate|severe|death",
  "occurred_at": "2026-01-15T10:00:00Z",
  "location": "string",
  "description": "string",
  "immediate_action": "string (REQUIRED)",
  "reported_at": "2026-01-15T10:30:00Z (REQUIRED)",
  "reporter_name": "string (required unless near_miss)",
  "root_cause": "string (optional)",
  "improvements": "string (optional)",
  "department": "string (optional)"
}
```

**Response** (201): Incident object

### GET `/incidents/{id}`

Get single incident by ID.

**Response** (200): Incident object

### PUT `/incidents/{id}`

Update incident.

**Request Body**: Partial incident fields

**Response** (200): Updated incident

### GET `/incidents/{id}/timeline`

Get incident timeline (actions, approvals, status changes).

**Response** (200):
```json
{
  "incident_id": 1,
  "events": [
    {
      "type": "created|status_change|approval|action|comment",
      "timestamp": "2026-01-15T10:30:00Z",
      "user": "username",
      "description": "Event description"
    }
  ]
}
```

---

## Approvals API (`/api/approvals`)

### GET `/approvals/incidents/{incident_id}/status`

Get approval status for an incident.

**Response** (200):
```json
{
  "incident_id": 1,
  "current_level": "l1_qps|l2_vice_chair|l3_director|completed",
  "approvals": [Approval],
  "can_approve": true,
  "can_reject": true
}
```

### POST `/approvals/incidents/{incident_id}/approve`

Approve incident at current level.

**Request Body**:
```json
{
  "action": "approve",
  "comment": "string (optional)"
}
```

**Response** (200): Approval object

### POST `/approvals/incidents/{incident_id}/reject`

Reject incident.

**Request Body**:
```json
{
  "action": "reject",
  "rejection_reason": "string (required)"
}
```

**Response** (200): Approval object

---

## Actions API (`/api/actions`)

### GET `/actions/incident/{incident_id}`

List actions for an incident.

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status |
| `skip` | int | Offset |
| `limit` | int | Limit |

**Response** (200):
```json
{
  "items": [Action],
  "total": 10,
  "skip": 0,
  "limit": 50
}
```

### POST `/actions`

Create new action (CAPA).

**Request Body**:
```json
{
  "incident_id": 1,
  "title": "string",
  "description": "string (optional)",
  "owner": "string",
  "due_date": "2026-02-15",
  "definition_of_done": "string",
  "priority": "low|medium|high|critical"
}
```

**Response** (201): Action object

### GET `/actions/{id}`

Get single action.

### PUT `/actions/{id}`

Update action.

### POST `/actions/{id}/start`

Start action (open → in_progress).

### POST `/actions/{id}/complete`

Complete action (in_progress → completed).

**Request Body**:
```json
{
  "completion_notes": "string (optional)",
  "evidence_attachment_id": "int (optional)"
}
```

### POST `/actions/{id}/verify`

Verify action (completed → verified). Director+ only.

**Request Body**:
```json
{
  "verification_notes": "string (optional)"
}
```

### POST `/actions/{id}/cancel`

Cancel action.

### GET `/actions/overdue`

List all overdue actions.

---

## Attachments API (`/api/attachments`)

### POST `/attachments/incidents/{incident_id}/upload`

Upload file attachment.

**Request**: `multipart/form-data` with `file` field

**Response** (201):
```json
{
  "id": 1,
  "filename": "uuid.pdf",
  "original_filename": "document.pdf",
  "content_type": "application/pdf",
  "file_size": 12345,
  "storage_uri": "file://uploads/incidents/1/uuid.pdf"
}
```

### GET `/attachments/{id}/download`

Download attachment file.

**Response**: Binary file content

---

## Risk Management API (`/api/risks`)

### GET `/risks`

List risks with filters.

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | identified|assessing|treating|monitoring|closed|accepted |
| `level` | string | low|medium|high|critical |
| `category` | string | Risk category |
| `skip` | int | Offset |
| `limit` | int | Limit |

**Response** (200):
```json
{
  "items": [Risk],
  "total": 50,
  "skip": 0,
  "limit": 50
}
```

### POST `/risks`

Create new risk.

**Request Body**:
```json
{
  "title": "string",
  "description": "string",
  "source_type": "psr|rounding|audit|complaint|indicator|external|proactive|other",
  "source_incident_id": "int (optional, for PSR)",
  "source_detail": "string (optional)",
  "category": "fall|medication|...",
  "current_controls": "string (optional)",
  "probability": "1-5",
  "severity": "1-5",
  "owner_id": "int",
  "target_date": "2026-03-01 (optional)"
}
```

**Response** (201): Risk object with auto-calculated `risk_score` and `risk_level`

### GET `/risks/{id}`

Get single risk.

### PUT `/risks/{id}`

Update risk.

### GET `/risks/matrix`

Get 5×5 risk matrix visualization.

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status (default: excludes closed) |

**Response** (200):
```json
{
  "matrix": [[RiskMatrixCell]],
  "total_risks": 25,
  "by_level": {
    "low": 5,
    "medium": 10,
    "high": 7,
    "critical": 3
  }
}
```

### POST `/risks/{id}/assessments`

Add risk assessment (re-evaluation).

**Request Body**:
```json
{
  "assessment_type": "initial|periodic|post_treatment|post_incident",
  "probability": "1-5",
  "severity": "1-5",
  "rationale": "string (optional)"
}
```

### GET `/risks/{id}/assessments`

Get risk assessment history.

### GET `/risks/escalation/candidates`

Get PSR escalation candidates (SEVERE/DEATH grade).

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `days` | int | Look back period (default: 30) |

### POST `/risks/escalation/run`

Run auto-escalation batch.

### POST `/risks/escalation/{incident_id}`

Manually escalate single PSR to risk.

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `probability` | int | Override probability (1-5) |
| `severity` | int | Override severity (1-5) |
| `reason` | string | Escalation reason |

---

## Indicators API (`/api/indicators`)

### GET `/indicators`

List indicators with filters.

### POST `/indicators`

Create new indicator configuration.

### GET `/indicators/{id}`

Get indicator details.

### PUT `/indicators/{id}`

Update indicator.

### DELETE `/indicators/{id}`

Delete indicator.

### GET `/indicators/{id}/values`

Get indicator values (time series).

### POST `/indicators/{id}/values`

Add indicator value.

### POST `/indicators/values/{id}/verify`

Verify indicator value.

---

## Dashboard API (`/api/dashboard`)

### GET `/dashboard/summary`

Get dashboard summary statistics.

**Response** (200):
```json
{
  "total_incidents": 100,
  "by_grade": {
    "near_miss": 20,
    "no_harm": 30,
    "mild": 25,
    "moderate": 15,
    "severe": 8,
    "death": 2
  },
  "by_category": {...},
  "pending_approvals": 5,
  "overdue_actions": 3
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

| Status | Description |
|--------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Schema validation failed |
| 500 | Internal Server Error |

---

## Data Types

### Incident Categories
- `fall`, `medication`, `pressure_ulcer`, `infection`
- `medical_device`, `surgery`, `transfusion`, `other`

### Incident Grades
- `near_miss`, `no_harm`, `mild`, `moderate`, `severe`, `death`

### Incident Status
- `draft`, `submitted`, `approved`, `closed`

### User Roles
- `reporter`, `qps_staff`, `vice_chair`, `director`, `admin`, `master`

### Approval Levels
- `l1_qps`, `l2_vice_chair`, `l3_director`

### Action Status
- `open`, `in_progress`, `completed`, `verified`, `cancelled`

### Risk Levels
- `low` (1-4), `medium` (5-9), `high` (10-16), `critical` (17-25)

### Risk Status
- `identified`, `assessing`, `treating`, `monitoring`, `closed`, `accepted`
