import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
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
  department?: string
}

import type {
  CreateIndicatorData,
  CreateIndicatorValueData,
  CreateFallDetailData,
  CreateMedicationDetailData,
  CreateActionData,
  IndicatorCategory,
  IndicatorStatusType,
  ActionStatus,
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
