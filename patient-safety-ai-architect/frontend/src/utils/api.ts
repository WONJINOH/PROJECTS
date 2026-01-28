import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token (no trailing slashes - they cause redirect issues)
api.interceptors.request.use(
  (config) => {
    // Note: Don't add trailing slashes - they cause 307 redirects that lose auth headers
    const authStorage = localStorage.getItem('auth-storage')
    if (authStorage) {
      try {
        const { state } = JSON.parse(authStorage)
        if (state?.token) {
          config.headers.Authorization = `Bearer ${state.token}`
        }
      } catch {
        // Invalid storage, ignore
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth and redirect to login
      localStorage.removeItem('auth-storage')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API functions
// Note: No trailing slashes - FastAPI redirects cause auth header loss
export const incidentApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get('/api/incidents', { params }),

  get: (id: number) =>
    api.get(`/api/incidents/${id}`),

  create: (data: CreateIncidentData) =>
    api.post('/api/incidents', data),

  update: (id: number, data: Partial<CreateIncidentData>) =>
    api.put(`/api/incidents/${id}`, data),
}

export const attachmentApi = {
  upload: (incidentId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/api/attachments/incidents/${incidentId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  download: (attachmentId: number) =>
    api.get(`/api/attachments/${attachmentId}/download`, {
      responseType: 'blob',
    }),
}

export const approvalApi = {
  getStatus: (incidentId: number) =>
    api.get(`/api/approvals/incidents/${incidentId}/status`),

  approve: (incidentId: number, comment?: string) =>
    api.post(`/api/approvals/incidents/${incidentId}/approve`, {
      action: 'approve',
      comment,
    }),

  reject: (incidentId: number, reason: string) =>
    api.post(`/api/approvals/incidents/${incidentId}/reject`, {
      action: 'reject',
      rejection_reason: reason,
    }),
}

// Types
export interface CreateIncidentData {
  category: string
  grade: string
  occurred_at: string
  location: string
  description: string
  immediate_action: string
  reported_at: string
  reporter_name?: string
  root_cause?: string
  improvements?: string
  // 환자 정보 (필수)
  patient_registration_no: string
  patient_name: string
  patient_ward: string
  room_number: string
  patient_gender: string
  patient_age: number
  patient_department_id: number
  patient_physician_id: number
  diagnosis?: string
}

import type {
  CreateIndicatorData,
  CreateIndicatorValueData,
  CreateFallDetailData,
  CreateMedicationDetailData,
  CreateInfectionDetailData,
  CreatePressureUlcerDetailData,
  CreateActionData,
  CreateRiskData,
  UpdateRiskData,
  CreateRiskAssessmentData,
  CreateDepartmentData,
  CreatePhysicianData,
  IndicatorCategory,
  IndicatorStatusType,
  ActionStatus,
  RiskStatus,
  RiskLevel,
  RiskCategory,
} from '@/types'

// Indicator API
export const indicatorApi = {
  list: (params?: {
    category?: IndicatorCategory
    status?: IndicatorStatusType
    is_key?: boolean
    search?: string
    skip?: number
    limit?: number
  }) => api.get('/api/indicators', { params }),

  get: (id: number) => api.get(`/api/indicators/${id}`),

  create: (data: CreateIndicatorData) => api.post('/api/indicators', data),

  update: (id: number, data: Partial<CreateIndicatorData>) =>
    api.put(`/api/indicators/${id}`, data),

  delete: (id: number) => api.delete(`/api/indicators/${id}`),

  // Approval operations
  approve: (indicatorId: number, comment?: string) =>
    api.post(`/api/indicators/${indicatorId}/approve`, { comment }),

  reject: (indicatorId: number, reason: string) =>
    api.post(`/api/indicators/${indicatorId}/reject`, { reason }),

  // Value operations
  listValues: (
    indicatorId: number,
    params?: {
      start_date?: string
      end_date?: string
      verified_only?: boolean
      skip?: number
      limit?: number
    }
  ) => api.get(`/api/indicators/${indicatorId}/values`, { params }),

  createValue: (indicatorId: number, data: CreateIndicatorValueData) =>
    api.post(`/api/indicators/${indicatorId}/values`, data),

  updateValue: (valueId: number, data: Partial<CreateIndicatorValueData>) =>
    api.put(`/api/indicators/values/${valueId}`, data),

  verifyValue: (valueId: number, comment?: string) =>
    api.post(`/api/indicators/values/${valueId}/verify`, { comment }),
}

// Fall Detail API
export const fallDetailApi = {
  getByIncident: (incidentId: number) =>
    api.get(`/api/fall-details/incident/${incidentId}`),

  get: (id: number) =>
    api.get(`/api/fall-details/${id}`),

  create: (data: CreateFallDetailData) =>
    api.post('/api/fall-details', data),

  update: (id: number, data: Partial<CreateFallDetailData>) =>
    api.put(`/api/fall-details/${id}`, data),

  delete: (id: number) =>
    api.delete(`/api/fall-details/${id}`),
}

// Medication Detail API
export const medicationDetailApi = {
  getByIncident: (incidentId: number) =>
    api.get(`/api/medication-details/incident/${incidentId}`),

  get: (id: number) =>
    api.get(`/api/medication-details/${id}`),

  create: (data: CreateMedicationDetailData) =>
    api.post('/api/medication-details', data),

  update: (id: number, data: Partial<CreateMedicationDetailData>) =>
    api.put(`/api/medication-details/${id}`, data),

  delete: (id: number) =>
    api.delete(`/api/medication-details/${id}`),
}

// Infection Detail API
export const infectionDetailApi = {
  getByIncident: (incidentId: number) =>
    api.get(`/api/infection-details/incident/${incidentId}`),

  get: (id: number) =>
    api.get(`/api/infection-details/${id}`),

  create: (data: CreateInfectionDetailData) =>
    api.post('/api/infection-details', data),

  update: (id: number, data: Partial<CreateInfectionDetailData>) =>
    api.put(`/api/infection-details/${id}`, data),

  delete: (id: number) =>
    api.delete(`/api/infection-details/${id}`),
}

// Pressure Ulcer Detail API
export const pressureUlcerDetailApi = {
  getByIncident: (incidentId: number) =>
    api.get(`/api/pressure-ulcer-details/incident/${incidentId}`),

  get: (id: number) =>
    api.get(`/api/pressure-ulcer-details/${id}`),

  create: (data: CreatePressureUlcerDetailData) =>
    api.post('/api/pressure-ulcer-details', data),

  update: (id: number, data: Partial<CreatePressureUlcerDetailData>) =>
    api.put(`/api/pressure-ulcer-details/${id}`, data),

  delete: (id: number) =>
    api.delete(`/api/pressure-ulcer-details/${id}`),
}

// Action API (CAPA)
export const actionApi = {
  listByIncident: (incidentId: number, params?: { status?: ActionStatus; skip?: number; limit?: number }) =>
    api.get(`/api/actions/incident/${incidentId}`, { params }),

  get: (id: number) =>
    api.get(`/api/actions/${id}`),

  create: (data: CreateActionData) =>
    api.post('/api/actions', data),

  update: (id: number, data: Partial<CreateActionData>) =>
    api.put(`/api/actions/${id}`, data),

  start: (id: number) =>
    api.post(`/api/actions/${id}/start`),

  complete: (id: number, data: { completion_notes?: string; evidence_attachment_id?: number }) =>
    api.post(`/api/actions/${id}/complete`, data),

  verify: (id: number, data: { verification_notes?: string }) =>
    api.post(`/api/actions/${id}/verify`, data),

  cancel: (id: number) =>
    api.post(`/api/actions/${id}/cancel`),

  listOverdue: () =>
    api.get('/api/actions/overdue'),
}

// Risk API
export const riskApi = {
  list: (params?: {
    status?: RiskStatus
    level?: RiskLevel
    category?: RiskCategory
    skip?: number
    limit?: number
  }) => api.get('/api/risks', { params }),

  get: (id: number) => api.get(`/api/risks/${id}`),

  create: (data: CreateRiskData) => api.post('/api/risks', data),

  update: (id: number, data: UpdateRiskData) => api.put(`/api/risks/${id}`, data),

  // Risk Matrix
  getMatrix: (params?: { status?: RiskStatus }) =>
    api.get('/api/risks/matrix', { params }),

  // Risk Assessments
  listAssessments: (riskId: number) =>
    api.get(`/api/risks/${riskId}/assessments`),

  createAssessment: (riskId: number, data: CreateRiskAssessmentData) =>
    api.post(`/api/risks/${riskId}/assessments`, data),

  // Escalation
  getEscalationCandidates: (days?: number) =>
    api.get('/api/risks/escalation/candidates', { params: { days } }),

  runAutoEscalation: (days?: number) =>
    api.post('/api/risks/escalation/run', null, { params: { days } }),

  escalateIncident: (incidentId: number, params?: {
    probability?: number
    severity?: number
    reason?: string
  }) => api.post(`/api/risks/escalation/${incidentId}`, null, { params }),
}

// Dashboard API
export const dashboardApi = {
  getSummary: (params?: { year?: number; month?: number; department?: string }) =>
    api.get('/api/dashboard/summary', { params }),

  getPSR: (params?: { year?: number; month?: number; department?: string }) =>
    api.get('/api/dashboard/psr', { params }),

  getRecentIncidents: (params?: { limit?: number }) =>
    api.get('/api/dashboard/recent-incidents', { params }),

  getFall: (params?: { year?: number; month?: number }) =>
    api.get('/api/dashboard/fall', { params }),

  getMedication: (params?: { year?: number; month?: number }) =>
    api.get('/api/dashboard/medication', { params }),

  getPressureUlcer: (params?: { year?: number; month?: number }) =>
    api.get('/api/dashboard/pressure-ulcer', { params }),
}

// Lookup API (진료과/주치의)
export const lookupApi = {
  // Department
  listDepartments: (activeOnly: boolean = true) =>
    api.get('/api/lookup/departments', { params: { active_only: activeOnly } }),

  getDepartment: (id: number) =>
    api.get(`/api/lookup/departments/${id}`),

  createDepartment: (data: CreateDepartmentData) =>
    api.post('/api/lookup/departments', data),

  updateDepartment: (id: number, data: Partial<CreateDepartmentData> & { is_active?: boolean }) =>
    api.put(`/api/lookup/departments/${id}`, data),

  deleteDepartment: (id: number) =>
    api.delete(`/api/lookup/departments/${id}`),

  // Physician
  listPhysicians: (params?: { department_id?: number; active_only?: boolean }) =>
    api.get('/api/lookup/physicians', { params }),

  getPhysician: (id: number) =>
    api.get(`/api/lookup/physicians/${id}`),

  createPhysician: (data: CreatePhysicianData) =>
    api.post('/api/lookup/physicians', data),

  updatePhysician: (id: number, data: Partial<CreatePhysicianData> & { is_active?: boolean }) =>
    api.put(`/api/lookup/physicians/${id}`, data),

  deletePhysician: (id: number) =>
    api.delete(`/api/lookup/physicians/${id}`),
}

// Pressure Ulcer Management API (Feature 12)
export const pressureUlcerManagementApi = {
  // Patient list
  listPatients: (params?: {
    active_only?: boolean
    department?: string
    origin?: string
    skip?: number
    limit?: number
  }) => api.get('/api/pressure-ulcers/patients', { params }),

  // Patient detail
  getPatient: (recordId: number) =>
    api.get(`/api/pressure-ulcers/patients/${recordId}`),

  // Create new pressure ulcer record (욕창발생보고서)
  createRecord: (data: {
    patient_code: string
    patient_name: string
    patient_gender: string
    room_number: string
    patient_age_group?: string
    admission_date?: string
    location: string
    location_detail?: string
    origin: string
    discovery_date: string
    grade: string
    push_length_width: number
    push_exudate: number
    push_tissue_type: number
    length_cm?: number
    width_cm?: number
    depth_cm?: number
    department: string
    risk_factors?: string
    treatment_plan?: string
    note?: string
    fmea_severity?: number
    fmea_probability?: number
    fmea_detectability?: number
    reporter_name?: string
  }) => api.post('/api/pressure-ulcers/patients', data),

  // Add PUSH assessment
  createAssessment: (recordId: number, data: {
    assessment_date: string
    grade: string
    push_length_width: number
    push_exudate: number
    push_tissue_type: number
    length_cm?: number
    width_cm?: number
    depth_cm?: number
    note?: string
  }) => api.post(`/api/pressure-ulcers/patients/${recordId}/assessments`, data),

  // Close ulcer record
  closeUlcer: (recordId: number, data: {
    end_date: string
    end_reason: string
    end_reason_detail?: string
  }) => api.post(`/api/pressure-ulcers/patients/${recordId}/close`, data),

  // Trend data
  getTrend: (recordId: number) =>
    api.get(`/api/pressure-ulcers/patients/${recordId}/trend`),

  // Statistics
  getStats: (params?: { department?: string }) =>
    api.get('/api/pressure-ulcers/stats', { params }),

  // Feature 13: Manual improvement rate calculation
  calculateImprovementRate: (data: { year: number; month: number }) =>
    api.post('/api/pressure-ulcers/improvement-rate/calculate', data),
}
