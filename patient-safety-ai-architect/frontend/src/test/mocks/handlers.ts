/**
 * MSW Request Handlers
 *
 * Mocks API endpoints for testing.
 * Uses pseudonyms only - no real PII.
 */

import { http, HttpResponse } from 'msw'
import { mockUser, mockIncident, mockRisk, mockIndicator } from '../utils'

const API_BASE = ''

// ===== Auth Handlers =====
const authHandlers = [
  // Login
  http.post(`${API_BASE}/api/auth/login`, async ({ request }) => {
    const body = await request.text()
    const params = new URLSearchParams(body)
    const username = params.get('username')
    const password = params.get('password')

    if (username === 'qps_test' && password === 'password') {
      return HttpResponse.json({
        access_token: 'test-token-qps',
        token_type: 'bearer',
      })
    }

    if (username === 'reporter_test' && password === 'password') {
      return HttpResponse.json({
        access_token: 'test-token-reporter',
        token_type: 'bearer',
      })
    }

    return HttpResponse.json(
      { detail: 'Invalid credentials' },
      { status: 401 }
    )
  }),

  // Get current user
  http.get(`${API_BASE}/api/auth/me`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')

    if (authHeader === 'Bearer test-token-qps') {
      return HttpResponse.json(mockUser.qpsStaff)
    }

    if (authHeader === 'Bearer test-token-reporter') {
      return HttpResponse.json(mockUser.reporter)
    }

    if (authHeader === 'Bearer test-token') {
      return HttpResponse.json(mockUser.qpsStaff)
    }

    return HttpResponse.json(
      { detail: 'Not authenticated' },
      { status: 401 }
    )
  }),
]

// ===== Incident Handlers =====
const incidentHandlers = [
  // List incidents
  http.get(`${API_BASE}/api/incidents`, () => {
    return HttpResponse.json({
      items: [mockIncident.basic, mockIncident.severe],
      total: 2,
      skip: 0,
      limit: 50,
    })
  }),

  // Get single incident
  http.get(`${API_BASE}/api/incidents/:id`, ({ params }) => {
    const { id } = params

    if (id === '1') {
      return HttpResponse.json(mockIncident.basic)
    }

    if (id === '2') {
      return HttpResponse.json(mockIncident.severe)
    }

    return HttpResponse.json(
      { detail: 'Incident not found' },
      { status: 404 }
    )
  }),

  // Create incident
  http.post(`${API_BASE}/api/incidents`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    return HttpResponse.json(
      {
        id: 3,
        ...body,
        status: 'draft',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      { status: 201 }
    )
  }),

  // Update incident
  http.put(`${API_BASE}/api/incidents/:id`, async ({ params, request }) => {
    const { id } = params
    const body = await request.json() as Record<string, unknown>

    return HttpResponse.json({
      ...mockIncident.basic,
      id: Number(id),
      ...body,
      updatedAt: new Date().toISOString(),
    })
  }),
]

// ===== Risk Handlers =====
// Transform camelCase mock to snake_case API format
function toSnakeCase(risk: typeof mockRisk.basic) {
  return {
    id: risk.id,
    risk_code: risk.riskCode,
    title: risk.title,
    description: risk.description,
    source_type: risk.sourceType,
    category: risk.category,
    current_controls: risk.currentControls,
    probability: risk.probability,
    severity: risk.severity,
    risk_score: risk.riskScore,
    risk_level: risk.riskLevel,
    status: risk.status,
    owner_id: risk.ownerId,
    created_by_id: risk.createdById,
    created_at: risk.createdAt,
    updated_at: risk.updatedAt,
  }
}

const riskHandlers = [
  // List risks
  http.get(`${API_BASE}/api/risks`, () => {
    return HttpResponse.json({
      items: [toSnakeCase(mockRisk.basic), toSnakeCase(mockRisk.critical)],
      total: 2,
      skip: 0,
      limit: 50,
    })
  }),

  // Get risk matrix
  http.get(`${API_BASE}/api/risks/matrix`, () => {
    // Generate 5x5 matrix
    const matrix = []
    for (let p = 1; p <= 5; p++) {
      const row = []
      for (let s = 1; s <= 5; s++) {
        const score = p * s
        let level = 'low'
        if (score > 16) level = 'critical'
        else if (score > 9) level = 'high'
        else if (score > 4) level = 'medium'

        const riskIds = []
        if (p === 3 && s === 4) riskIds.push(1) // mockRisk.basic
        if (p === 4 && s === 5) riskIds.push(2) // mockRisk.critical

        row.push({
          probability: p,
          severity: s,
          count: riskIds.length,
          risk_ids: riskIds,
          level,
        })
      }
      matrix.push(row)
    }

    return HttpResponse.json({
      matrix,
      total_risks: 2,
      by_level: { low: 0, medium: 0, high: 1, critical: 1 },
    })
  }),

  // Get single risk
  http.get(`${API_BASE}/api/risks/:id`, ({ params }) => {
    const { id } = params

    if (id === '1') {
      return HttpResponse.json(toSnakeCase(mockRisk.basic))
    }

    if (id === '2') {
      return HttpResponse.json(toSnakeCase(mockRisk.critical))
    }

    return HttpResponse.json(
      { detail: 'Risk not found' },
      { status: 404 }
    )
  }),

  // Create risk
  http.post(`${API_BASE}/api/risks`, async ({ request }) => {
    const body = await request.json() as Record<string, unknown>
    const probability = (body.probability as number) || 1
    const severity = (body.severity as number) || 1
    const score = probability * severity
    let level = 'low'
    if (score > 16) level = 'critical'
    else if (score > 9) level = 'high'
    else if (score > 4) level = 'medium'

    return HttpResponse.json(
      {
        id: 3,
        risk_code: 'R-2026-003',
        ...body,
        risk_score: score,
        risk_level: level,
        status: 'identified',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      { status: 201 }
    )
  }),

  // Update risk
  http.put(`${API_BASE}/api/risks/:id`, async ({ params, request }) => {
    const { id } = params
    const body = await request.json() as Record<string, unknown>

    return HttpResponse.json({
      ...toSnakeCase(mockRisk.basic),
      id: Number(id),
      ...body,
      updated_at: new Date().toISOString(),
    })
  }),

  // Get risk assessments
  http.get(`${API_BASE}/api/risks/:id/assessments`, ({ params }) => {
    const { id } = params

    return HttpResponse.json([
      {
        id: 1,
        risk_id: Number(id),
        assessment_type: 'initial',
        assessed_at: '2026-01-15T10:00:00Z',
        assessor_id: 1,
        probability: 3,
        severity: 4,
        score: 12,
        level: 'high',
        rationale: 'Initial assessment',
      },
    ])
  }),

  // Create risk assessment
  http.post(`${API_BASE}/api/risks/:id/assessments`, async ({ params, request }) => {
    const { id } = params
    const body = await request.json() as Record<string, unknown>
    const probability = (body.probability as number) || 1
    const severity = (body.severity as number) || 1
    const score = probability * severity
    let level = 'low'
    if (score > 16) level = 'critical'
    else if (score > 9) level = 'high'
    else if (score > 4) level = 'medium'

    return HttpResponse.json(
      {
        id: 2,
        risk_id: Number(id),
        ...body,
        assessed_at: new Date().toISOString(),
        assessor_id: 1,
        score,
        level,
      },
      { status: 201 }
    )
  }),

  // Escalation candidates
  http.get(`${API_BASE}/api/risks/escalation/candidates`, () => {
    return HttpResponse.json([
      {
        incident_id: 2,
        category: 'fall',
        grade: 'severe',
        occurred_at: '2026-01-15T14:00:00Z',
        description: '중환자실 환자 낙상으로 골절 발생',
        reason: 'Grade is SEVERE',
        suggested_probability: 4,
        suggested_severity: 4,
      },
    ])
  }),

  // Run auto escalation
  http.post(`${API_BASE}/api/risks/escalation/run`, () => {
    return HttpResponse.json({
      escalated_count: 1,
      escalated_ids: [2],
      skipped_count: 0,
      errors: [],
    })
  }),

  // Escalate single incident
  http.post(`${API_BASE}/api/risks/escalation/:incidentId`, ({ params }) => {
    return HttpResponse.json({
      id: 3,
      risk_code: 'R-2026-003',
      title: '낙상 위험 - 중환자실',
      source_incident_id: Number(params.incidentId),
      status: 'identified',
    }, { status: 201 })
  }),
]

// ===== Indicator Handlers =====
const indicatorHandlers = [
  // List indicators
  http.get(`${API_BASE}/api/indicators`, () => {
    return HttpResponse.json({
      items: [mockIndicator.basic],
      total: 1,
      skip: 0,
      limit: 100,
    })
  }),

  // Get single indicator
  http.get(`${API_BASE}/api/indicators/:id`, ({ params }) => {
    if (params.id === '1') {
      return HttpResponse.json(mockIndicator.basic)
    }
    return HttpResponse.json(
      { detail: 'Indicator not found' },
      { status: 404 }
    )
  }),
]

// ===== Approval Handlers =====
const approvalHandlers = [
  // Get approval status
  http.get(`${API_BASE}/api/approvals/incidents/:id/status`, () => {
    return HttpResponse.json({
      incident_id: 1,
      current_level: 'l1_qps',
      approvals: [],
      can_approve: true,
      can_reject: true,
    })
  }),

  // Approve
  http.post(`${API_BASE}/api/approvals/incidents/:id/approve`, () => {
    return HttpResponse.json({
      id: 1,
      incident_id: 1,
      level: 'l1_qps',
      status: 'approved',
      comment: 'Approved',
    })
  }),

  // Reject
  http.post(`${API_BASE}/api/approvals/incidents/:id/reject`, () => {
    return HttpResponse.json({
      id: 1,
      incident_id: 1,
      level: 'l1_qps',
      status: 'rejected',
      rejection_reason: 'Need more info',
    })
  }),
]

// ===== Action Handlers =====
const actionHandlers = [
  // List actions by incident
  http.get(`${API_BASE}/api/actions/incident/:id`, () => {
    return HttpResponse.json({
      items: [
        {
          id: 1,
          incident_id: 1,
          title: '낙상 예방 교육 강화',
          description: '병동 직원 대상 낙상 예방 교육 실시',
          owner: '김QPS',
          due_date: '2026-02-15',
          definition_of_done: '교육 완료 및 평가 90점 이상',
          priority: 'high',
          status: 'open',
          is_overdue: false,
          created_at: '2026-01-15T10:00:00Z',
          updated_at: '2026-01-15T10:00:00Z',
        },
      ],
      total: 1,
      skip: 0,
      limit: 50,
    })
  }),
]

// ===== Dashboard Handlers =====
const dashboardHandlers = [
  http.get(`${API_BASE}/api/dashboard/summary`, () => {
    return HttpResponse.json({
      total_incidents: 25,
      by_grade: {
        near_miss: 5,
        no_harm: 8,
        mild: 6,
        moderate: 4,
        severe: 1,
        death: 1,
      },
      by_category: {
        fall: 10,
        medication: 8,
        pressure_ulcer: 4,
        infection: 3,
      },
      pending_approvals: 3,
      overdue_actions: 2,
    })
  }),
]

// Combine all handlers
export const handlers = [
  ...authHandlers,
  ...incidentHandlers,
  ...riskHandlers,
  ...indicatorHandlers,
  ...approvalHandlers,
  ...actionHandlers,
  ...dashboardHandlers,
]
