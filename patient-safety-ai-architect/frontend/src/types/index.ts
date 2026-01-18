// Type definitions for Patient Safety System

export type IncidentCategory =
  | 'fall'
  | 'medication'
  | 'pressure_ulcer'
  | 'infection'
  | 'medical_device'
  | 'surgery'
  | 'transfusion'
  | 'other'

export type IncidentGrade =
  | 'near_miss'
  | 'no_harm'
  | 'mild'
  | 'moderate'
  | 'severe'
  | 'death'

export type IncidentStatus = 'draft' | 'submitted' | 'approved' | 'closed'

export type UserRole =
  | 'reporter'
  | 'qps_staff'
  | 'vice_chair'
  | 'director'
  | 'admin'

export type ApprovalLevel = 'l1_qps' | 'l2_vice_chair' | 'l3_director'

export type ApprovalStatus = 'pending' | 'approved' | 'rejected'

export interface User {
  id: number
  username: string
  email: string
  fullName: string
  role: UserRole
  department?: string
  isActive: boolean
}

export interface Incident {
  id: number
  category: IncidentCategory
  grade: IncidentGrade
  occurredAt: string
  location: string
  description: string
  immediateAction: string
  reportedAt: string
  reporterName?: string
  rootCause?: string
  improvements?: string
  reporterId: number
  department?: string
  status: IncidentStatus
  createdAt: string
  updatedAt: string
  attachments?: Attachment[]
  approvals?: Approval[]
}

export interface Attachment {
  id: number
  filename: string
  originalFilename: string
  contentType: string
  fileSize: number
  storageUri: string
  incidentId: number
  uploadedById: number
  createdAt: string
}

export interface Approval {
  id: number
  incidentId: number
  approverId: number
  level: ApprovalLevel
  status: ApprovalStatus
  comment?: string
  rejectionReason?: string
  createdAt: string
  decidedAt?: string
}

export interface AuditLog {
  id: number
  eventType: string
  timestamp: string
  userId?: number
  userRole?: string
  username?: string
  ipAddress?: string
  userAgent?: string
  resourceType?: string
  resourceId?: string
  actionDetail?: Record<string, unknown>
  result: string
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

export interface ApiError {
  detail: string
  status: number
}
