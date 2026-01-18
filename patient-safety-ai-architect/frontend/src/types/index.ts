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
  | 'master'

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

// ===== Indicator Types =====

export type IndicatorCategory =
  | 'psr'
  | 'pressure_ulcer'
  | 'fall'
  | 'medication'
  | 'restraint'
  | 'infection'
  | 'staff_safety'
  | 'lab_tat'
  | 'composite'

export type IndicatorStatusType = 'active' | 'inactive' | 'planned'

export type PeriodType = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'

export type ChartType = 'line' | 'bar' | 'pie' | 'area'

export type ThresholdDirection = 'higher_is_better' | 'lower_is_better'

export interface IndicatorConfig {
  id: number
  code: string
  name: string
  category: IndicatorCategory
  description?: string
  unit: string
  calculationFormula?: string
  numeratorName?: string
  denominatorName?: string
  targetValue?: number
  warningThreshold?: number
  criticalThreshold?: number
  thresholdDirection?: ThresholdDirection
  periodType: PeriodType
  chartType: ChartType
  isKeyIndicator: boolean
  displayOrder: number
  dataSource?: string
  autoCalculate: boolean
  status: IndicatorStatusType
  createdAt: string
  updatedAt: string
  createdById?: number
}

export interface IndicatorValue {
  id: number
  indicatorId: number
  periodStart: string
  periodEnd: string
  value: number
  numerator?: number
  denominator?: number
  notes?: string
  isVerified: boolean
  verifiedAt?: string
  verifiedById?: number
  createdAt: string
  updatedAt: string
  createdById?: number
}

export interface CreateIndicatorData {
  code: string
  name: string
  category: IndicatorCategory
  description?: string
  unit: string
  calculation_formula?: string
  numerator_name?: string
  denominator_name?: string
  target_value?: number
  warning_threshold?: number
  critical_threshold?: number
  threshold_direction?: ThresholdDirection
  period_type?: PeriodType
  chart_type?: ChartType
  is_key_indicator?: boolean
  display_order?: number
  data_source?: string
  auto_calculate?: boolean
  status?: IndicatorStatusType
}

export interface CreateIndicatorValueData {
  period_start: string
  period_end: string
  value: number
  numerator?: number
  denominator?: number
  notes?: string
}

// Category labels for display
export const INDICATOR_CATEGORY_LABELS: Record<IndicatorCategory, string> = {
  psr: '환자안전사건보고 (PSR)',
  pressure_ulcer: '욕창 관리',
  fall: '낙상 관리',
  medication: '투약 안전',
  restraint: '신체보호대 사용',
  infection: '감염 관리',
  staff_safety: '직원 안전',
  lab_tat: '검사 TAT',
  composite: '종합 환자안전 지표',
}

export const INDICATOR_STATUS_LABELS: Record<IndicatorStatusType, string> = {
  active: '활성',
  inactive: '비활성',
  planned: '예정',
}
