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
