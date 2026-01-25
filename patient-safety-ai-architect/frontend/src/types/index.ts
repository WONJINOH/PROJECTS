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

export type UserStatus =
  | 'pending'
  | 'active'
  | 'dormant'
  | 'suspended'
  | 'deleted'

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
  status: UserStatus
  passwordExpiresAt?: string
  lastLogin?: string
  createdAt: string
  approvedAt?: string
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
  // PSR 공통 필드 (대시보드용)
  outcomeImpact?: IncidentOutcomeImpact
  outcomeImpactDetail?: string
  contributingFactors?: string[]
  contributingFactorsDetail?: string
  patientPhysicalOutcome?: PatientPhysicalOutcome
  patientPhysicalOutcomeDetail?: string
  // 메타데이터
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

// ===== Fall Detail Types =====

export type FallInjuryLevel = 'none' | 'minor' | 'moderate' | 'major' | 'death'
export type FallRiskLevel = 'low' | 'moderate' | 'high'
export type FallLocation = 'bed' | 'bathroom' | 'hallway' | 'wheelchair' | 'chair' | 'rehabilitation' | 'other'
export type FallCause = 'slip' | 'trip' | 'loss_of_balance' | 'fainting' | 'weakness' | 'cognitive' | 'medication' | 'environment' | 'other'

// PSR 양식 기반 추가 타입
export type FallConsciousnessLevel = 'alert' | 'drowsy' | 'stupor' | 'semicoma' | 'coma'
export type FallActivityLevel = 'independent' | 'needs_assistance' | 'dependent'
export type FallMobilityAid = 'none' | 'wheelchair' | 'walker' | 'cane' | 'crutch' | 'other'
export type FallType = 'bed_fall' | 'standing_fall' | 'sitting_fall' | 'walking_fall' | 'transfer_fall' | 'other'
export type FallPhysicalInjury = 'none' | 'abrasion' | 'contusion' | 'laceration' | 'hematoma' | 'fracture' | 'head_injury' | 'other'
export type FallTreatment = 'observation' | 'dressing' | 'suture' | 'cast_splint' | 'imaging' | 'surgery' | 'transfer' | 'other'

export interface FallDetail {
  id: number
  incidentId: number
  patientCode: string
  patientAgeGroup?: string
  patientGender?: string
  preFallRiskLevel?: FallRiskLevel
  morseScore?: number
  // PSR 양식 필드
  consciousnessLevel?: FallConsciousnessLevel
  activityLevel?: FallActivityLevel
  usesMobilityAid?: boolean
  mobilityAidType?: FallMobilityAid
  riskFactors?: string[]
  relatedMedications?: string[]
  fallType?: FallType
  // 기존 필드
  fallLocation: FallLocation
  fallLocationDetail?: string
  fallCause: FallCause
  fallCauseDetail?: string
  occurredHour?: number
  shift?: 'day' | 'evening' | 'night'
  injuryLevel: FallInjuryLevel
  injuryDescription?: string
  physicalInjuryType?: FallPhysicalInjury
  physicalInjuryDetail?: string
  treatmentsProvided?: string[]
  treatmentDetail?: string
  activityAtFall?: string
  wasSupervised: boolean
  hadFallPrevention: boolean
  department: string
  isRecurrence: boolean
  previousFallCount: number
  createdAt: string
}

export interface CreateFallDetailData {
  incident_id: number
  patient_code: string
  patient_age_group?: string
  patient_gender?: string
  pre_fall_risk_level?: FallRiskLevel
  morse_score?: number
  // PSR 양식 필드
  consciousness_level?: FallConsciousnessLevel
  activity_level?: FallActivityLevel
  uses_mobility_aid?: boolean
  mobility_aid_type?: FallMobilityAid
  risk_factors?: string[]
  related_medications?: string[]
  fall_type?: FallType
  // 기존 필드
  fall_location: FallLocation
  fall_location_detail?: string
  fall_cause: FallCause
  fall_cause_detail?: string
  occurred_hour?: number
  shift?: 'day' | 'evening' | 'night'
  injury_level: FallInjuryLevel
  injury_description?: string
  physical_injury_type?: FallPhysicalInjury
  physical_injury_detail?: string
  treatments_provided?: string[]
  treatment_detail?: string
  activity_at_fall?: string
  was_supervised?: boolean
  had_fall_prevention?: boolean
  department: string
  is_recurrence?: boolean
  previous_fall_count?: number
}

export const FALL_INJURY_LABELS: Record<FallInjuryLevel, string> = {
  none: '손상 없음',
  minor: '경미 (찰과상, 타박상)',
  moderate: '중등도 (봉합 필요)',
  major: '중증 (골절, 의식 변화)',
  death: '사망',
}

export const FALL_LOCATION_LABELS: Record<FallLocation, string> = {
  bed: '침대',
  bathroom: '화장실',
  hallway: '복도',
  wheelchair: '휠체어',
  chair: '의자',
  rehabilitation: '재활치료실',
  other: '기타',
}

export const FALL_CAUSE_LABELS: Record<FallCause, string> = {
  slip: '미끄러짐',
  trip: '걸려 넘어짐',
  loss_of_balance: '균형 상실',
  fainting: '실신/어지러움',
  weakness: '근력 약화',
  cognitive: '인지 장애',
  medication: '약물 관련',
  environment: '환경 요인',
  other: '기타',
}

// PSR 양식 추가 레이블
export const FALL_CONSCIOUSNESS_LABELS: Record<FallConsciousnessLevel, string> = {
  alert: '명료',
  drowsy: '기면',
  stupor: '혼미',
  semicoma: '반혼수',
  coma: '혼수',
}

export const FALL_ACTIVITY_LABELS: Record<FallActivityLevel, string> = {
  independent: '독립적',
  needs_assistance: '부분 도움 필요',
  dependent: '전적 도움 필요',
}

export const FALL_MOBILITY_AID_LABELS: Record<FallMobilityAid, string> = {
  none: '없음',
  wheelchair: '휠체어',
  walker: '워커',
  cane: '지팡이',
  crutch: '목발',
  other: '기타',
}

export const FALL_TYPE_LABELS: Record<FallType, string> = {
  bed_fall: '침대에서 낙상',
  standing_fall: '서있다가 낙상',
  sitting_fall: '앉아있다가 낙상',
  walking_fall: '보행 중 낙상',
  transfer_fall: '이동 중 낙상',
  other: '기타',
}

export const FALL_PHYSICAL_INJURY_LABELS: Record<FallPhysicalInjury, string> = {
  none: '없음',
  abrasion: '찰과상',
  contusion: '타박상',
  laceration: '열상',
  hematoma: '혈종',
  fracture: '골절',
  head_injury: '두부손상',
  other: '기타',
}

export const FALL_TREATMENT_LABELS: Record<FallTreatment, string> = {
  observation: '관찰',
  dressing: '드레싱',
  suture: '봉합',
  cast_splint: '부목/석고',
  imaging: '영상검사',
  surgery: '수술',
  transfer: '전원',
  other: '기타',
}

// 낙상 위험요인 옵션
export const FALL_RISK_FACTOR_OPTIONS = [
  { value: 'history_of_fall', label: '낙상 과거력' },
  { value: 'cognitive_impairment', label: '인지장애' },
  { value: 'visual_impairment', label: '시력장애' },
  { value: 'hearing_impairment', label: '청력장애' },
  { value: 'gait_disturbance', label: '보행장애' },
  { value: 'weakness', label: '근력약화' },
  { value: 'dizziness', label: '어지러움' },
  { value: 'urinary_frequency', label: '빈뇨' },
  { value: 'incontinence', label: '실금' },
] as const

// 낙상 관련 투약 옵션
export const FALL_RELATED_MEDICATION_OPTIONS = [
  { value: 'sedative', label: '진정제' },
  { value: 'hypnotic', label: '수면제' },
  { value: 'antihypertensive', label: '항고혈압제' },
  { value: 'diuretic', label: '이뇨제' },
  { value: 'hypoglycemic', label: '혈당강하제' },
  { value: 'opioid', label: '마약성진통제' },
  { value: 'antipsychotic', label: '항정신병제' },
  { value: 'anticonvulsant', label: '항경련제' },
] as const

// ===== Medication Detail Types =====

export type MedicationErrorType =
  | 'wrong_patient'
  | 'wrong_drug'
  | 'wrong_dose'
  | 'wrong_route'
  | 'wrong_time'
  | 'wrong_rate'
  | 'omission'
  | 'unauthorized'
  | 'deteriorated'
  | 'monitoring'
  | 'other'

export type MedicationErrorStage =
  | 'prescribing'
  | 'transcribing'
  | 'dispensing'
  | 'administering'
  | 'monitoring'

export type MedicationErrorSeverity = 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'I'

export type HighAlertMedication =
  | 'anticoagulant'
  | 'insulin'
  | 'opioid'
  | 'chemotherapy'
  | 'sedative'
  | 'potassium'
  | 'neuromuscular'
  | 'other'

// PSR 양식 기반 추가 타입
export type MedicationDiscoveryTiming = 'pre_administration' | 'post_administration'
export type MedicationErrorCause =
  | 'communication'
  | 'name_confusion'
  | 'labeling'
  | 'storage'
  | 'standardization'
  | 'device_design'
  | 'distraction'
  | 'workload'
  | 'staff_shortage'
  | 'training'
  | 'patient_education'
  | 'verification_failure'
  | 'prescription_error'
  | 'transcription_error'
  | 'dispensing_error'
  | 'other'

export interface MedicationDetail {
  id: number
  incidentId: number
  patientCode: string
  patientAgeGroup?: string
  errorType: MedicationErrorType
  errorStage: MedicationErrorStage
  errorSeverity: MedicationErrorSeverity
  isNearMiss: boolean
  medicationCategory?: string
  isHighAlert: boolean
  highAlertType?: HighAlertMedication
  intendedDose?: string
  actualDose?: string
  intendedRoute?: string
  actualRoute?: string
  discoveredByRole?: string
  discoveryMethod?: string
  // PSR 양식 필드
  discoveryTiming?: MedicationDiscoveryTiming
  errorCauses?: string[]
  errorCauseDetail?: string
  // 기존 필드
  department: string
  barcodeScanned?: boolean
  contributingFactors?: string
  createdAt: string
}

export interface CreateMedicationDetailData {
  incident_id: number
  patient_code: string
  patient_age_group?: string
  error_type: MedicationErrorType
  error_stage: MedicationErrorStage
  error_severity: MedicationErrorSeverity
  is_near_miss?: boolean
  medication_category?: string
  is_high_alert?: boolean
  high_alert_type?: HighAlertMedication
  intended_dose?: string
  actual_dose?: string
  intended_route?: string
  actual_route?: string
  discovered_by_role?: string
  discovery_method?: string
  // PSR 양식 필드
  discovery_timing?: MedicationDiscoveryTiming
  error_causes?: string[]
  error_cause_detail?: string
  // 기존 필드
  department: string
  barcode_scanned?: boolean
  contributing_factors?: string
}

export const MEDICATION_ERROR_TYPE_LABELS: Record<MedicationErrorType, string> = {
  wrong_patient: '환자 오류',
  wrong_drug: '약물 오류',
  wrong_dose: '용량 오류',
  wrong_route: '경로 오류',
  wrong_time: '시간 오류',
  wrong_rate: '속도 오류 (주사)',
  omission: '누락',
  unauthorized: '무허가 투약',
  deteriorated: '변질 약물',
  monitoring: '모니터링 오류',
  other: '기타',
}

export const MEDICATION_STAGE_LABELS: Record<MedicationErrorStage, string> = {
  prescribing: '처방 단계',
  transcribing: '전사 단계',
  dispensing: '조제 단계',
  administering: '투여 단계',
  monitoring: '모니터링 단계',
}

export const MEDICATION_SEVERITY_LABELS: Record<MedicationErrorSeverity, string> = {
  A: 'A - 오류 가능성 있는 상황',
  B: 'B - 오류 발생, 환자 미도달',
  C: 'C - 환자 도달, 해 없음',
  D: 'D - 환자 도달, 모니터링 필요',
  E: 'E - 일시적 해, 중재 필요',
  F: 'F - 일시적 해, 입원/연장 필요',
  G: 'G - 영구적 해',
  H: 'H - 생명 위협, 중재 필요',
  I: 'I - 사망',
}

export const HIGH_ALERT_LABELS: Record<HighAlertMedication, string> = {
  anticoagulant: '항응고제',
  insulin: '인슐린',
  opioid: '마약성 진통제',
  chemotherapy: '항암제',
  sedative: '진정제',
  potassium: '고농도 칼륨',
  neuromuscular: '신경근차단제',
  other: '기타',
}

// PSR 양식 추가 레이블
export const MEDICATION_DISCOVERY_TIMING_LABELS: Record<MedicationDiscoveryTiming, string> = {
  pre_administration: '투약 전 발견',
  post_administration: '투약 후 발견',
}

export const MEDICATION_ERROR_CAUSE_LABELS: Record<MedicationErrorCause, string> = {
  communication: '의사소통 오류',
  name_confusion: '약품명 혼동',
  labeling: '라벨/표시 문제',
  storage: '보관 문제',
  standardization: '표준화 미흡',
  device_design: '기기/설계 문제',
  distraction: '산만/방해',
  workload: '업무과중',
  staff_shortage: '인력 부족',
  training: '교육/훈련 부족',
  patient_education: '환자 교육 부족',
  verification_failure: '확인 절차 미이행',
  prescription_error: '처방 오류',
  transcription_error: '전사 오류',
  dispensing_error: '조제 오류',
  other: '기타',
}

// ===== Incident Common Types (PSR) =====

export type IncidentOutcomeImpact =
  | 'none'
  | 'extended_stay'
  | 'additional_treatment'
  | 'readmission'
  | 'disability'
  | 'death'
  | 'other'

export type ContributingFactorType =
  // 인적요인
  | 'human_communication'
  | 'human_fatigue'
  | 'human_knowledge'
  | 'human_supervision'
  | 'human_verification'
  // 시스템요인
  | 'system_policy'
  | 'system_workload'
  | 'system_staffing'
  | 'system_training'
  // 시설/장비요인
  | 'facility_equipment'
  | 'facility_environment'
  | 'facility_design'
  | 'other'

export type PatientPhysicalOutcome =
  | 'none'
  | 'temporary_mild'
  | 'temporary_moderate'
  | 'permanent'
  | 'death'

export const INCIDENT_OUTCOME_IMPACT_LABELS: Record<IncidentOutcomeImpact, string> = {
  none: '영향 없음',
  extended_stay: '입원 연장',
  additional_treatment: '추가 치료 필요',
  readmission: '재입원',
  disability: '장애',
  death: '사망',
  other: '기타',
}

export const CONTRIBUTING_FACTOR_LABELS: Record<ContributingFactorType, string> = {
  human_communication: '의사소통 문제',
  human_fatigue: '피로/스트레스',
  human_knowledge: '지식/기술 부족',
  human_supervision: '감독 부재',
  human_verification: '확인 절차 미이행',
  system_policy: '정책/절차 미흡',
  system_workload: '업무과중',
  system_staffing: '인력 부족',
  system_training: '교육/훈련 부족',
  facility_equipment: '장비 결함/부족',
  facility_environment: '환경 문제',
  facility_design: '설계/배치 문제',
  other: '기타',
}

export const CONTRIBUTING_FACTOR_CATEGORIES = {
  human: ['human_communication', 'human_fatigue', 'human_knowledge', 'human_supervision', 'human_verification'],
  system: ['system_policy', 'system_workload', 'system_staffing', 'system_training'],
  facility: ['facility_equipment', 'facility_environment', 'facility_design'],
} as const

export const PATIENT_PHYSICAL_OUTCOME_LABELS: Record<PatientPhysicalOutcome, string> = {
  none: '손상 없음',
  temporary_mild: '일시적 경미',
  temporary_moderate: '일시적 중등도',
  permanent: '영구적 손상',
  death: '사망',
}

// ===== Action Types =====

export type ActionStatus = 'open' | 'in_progress' | 'completed' | 'verified' | 'cancelled'
export type ActionPriority = 'low' | 'medium' | 'high' | 'critical'

export interface Action {
  id: number
  incidentId: number
  title: string
  description?: string
  owner: string
  dueDate: string
  definitionOfDone: string
  priority: ActionPriority
  status: ActionStatus
  evidenceAttachmentId?: number
  completedAt?: string
  completedById?: number
  completionNotes?: string
  verifiedAt?: string
  verifiedById?: number
  verificationNotes?: string
  createdById: number
  createdAt: string
  updatedAt: string
  isOverdue: boolean
}

export interface CreateActionData {
  incident_id: number
  title: string
  description?: string
  owner: string
  due_date: string
  definition_of_done: string
  priority?: ActionPriority
}

export const ACTION_STATUS_LABELS: Record<ActionStatus, string> = {
  open: '신규',
  in_progress: '진행 중',
  completed: '완료 (검증 대기)',
  verified: '검증 완료',
  cancelled: '취소됨',
}

export const ACTION_STATUS_COLORS: Record<ActionStatus, string> = {
  open: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  verified: 'bg-purple-100 text-purple-800',
  cancelled: 'bg-gray-100 text-gray-800',
}

export const ACTION_PRIORITY_LABELS: Record<ActionPriority, string> = {
  low: '낮음',
  medium: '보통',
  high: '높음',
  critical: '긴급',
}

export const ACTION_PRIORITY_COLORS: Record<ActionPriority, string> = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-blue-100 text-blue-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
}

// ===== Risk Types =====

export type RiskSourceType =
  | 'psr'
  | 'rounding'
  | 'audit'
  | 'complaint'
  | 'indicator'
  | 'external'
  | 'proactive'
  | 'other'

export type RiskCategory =
  | 'fall'
  | 'medication'
  | 'pressure_ulcer'
  | 'infection'
  | 'transfusion'
  | 'procedure'
  | 'restraint'
  | 'environment'
  | 'security'
  | 'communication'
  | 'handoff'
  | 'identification'
  | 'other'

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

export type RiskStatus =
  | 'identified'
  | 'assessing'
  | 'treating'
  | 'monitoring'
  | 'closed'
  | 'accepted'

export type RiskAssessmentType =
  | 'initial'
  | 'periodic'
  | 'post_treatment'
  | 'post_incident'

export interface Risk {
  id: number
  riskCode: string
  title: string
  description: string
  sourceType: RiskSourceType
  sourceIncidentId?: number
  sourceDetail?: string
  category: RiskCategory
  currentControls?: string
  probability: number
  severity: number
  riskScore: number
  riskLevel: RiskLevel
  residualProbability?: number
  residualSeverity?: number
  residualScore?: number
  residualLevel?: RiskLevel
  ownerId: number
  ownerName?: string
  targetDate?: string
  status: RiskStatus
  autoEscalated: boolean
  escalationReason?: string
  createdById: number
  createdByName?: string
  createdAt: string
  updatedAt: string
  closedAt?: string
  closedById?: number
}

export interface RiskAssessment {
  id: number
  riskId: number
  assessmentType: RiskAssessmentType
  assessedAt: string
  assessorId: number
  assessorName?: string
  probability: number
  severity: number
  score: number
  level: RiskLevel
  rationale?: string
}

export interface RiskMatrixCell {
  probability: number
  severity: number
  count: number
  riskIds: number[]
  level: RiskLevel
}

export interface CreateRiskData {
  title: string
  description: string
  source_type: RiskSourceType
  source_incident_id?: number
  source_detail?: string
  category: RiskCategory
  current_controls?: string
  probability: number
  severity: number
  owner_id: number
  target_date?: string
}

export interface UpdateRiskData {
  title?: string
  description?: string
  current_controls?: string
  probability?: number
  severity?: number
  residual_probability?: number
  residual_severity?: number
  owner_id?: number
  target_date?: string
  status?: RiskStatus
}

export interface CreateRiskAssessmentData {
  assessment_type: RiskAssessmentType
  probability: number
  severity: number
  rationale?: string
}

export const RISK_SOURCE_TYPE_LABELS: Record<RiskSourceType, string> = {
  psr: '환자안전사건보고 (PSR)',
  rounding: '안전 라운딩',
  audit: '내부 감사',
  complaint: '민원/불만',
  indicator: '지표 이상',
  external: '외부 정보',
  proactive: '선제적 식별 (FMEA)',
  other: '기타',
}

export const RISK_CATEGORY_LABELS: Record<RiskCategory, string> = {
  fall: '낙상',
  medication: '투약',
  pressure_ulcer: '욕창',
  infection: '감염',
  transfusion: '수혈',
  procedure: '검사/시술',
  restraint: '신체보호대',
  environment: '환경/시설',
  security: '보안',
  communication: '의사소통',
  handoff: '인수인계',
  identification: '환자확인',
  other: '기타',
}

export const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  low: '저위험',
  medium: '중위험',
  high: '고위험',
  critical: '극심',
}

export const RISK_LEVEL_COLORS: Record<RiskLevel, string> = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
}

export const RISK_STATUS_LABELS: Record<RiskStatus, string> = {
  identified: '식별됨',
  assessing: '평가 중',
  treating: '조치 진행 중',
  monitoring: '모니터링 중',
  closed: '종결',
  accepted: '수용됨',
}

export const RISK_STATUS_COLORS: Record<RiskStatus, string> = {
  identified: 'bg-blue-100 text-blue-800',
  assessing: 'bg-purple-100 text-purple-800',
  treating: 'bg-yellow-100 text-yellow-800',
  monitoring: 'bg-cyan-100 text-cyan-800',
  closed: 'bg-gray-100 text-gray-800',
  accepted: 'bg-green-100 text-green-800',
}

export const RISK_ASSESSMENT_TYPE_LABELS: Record<RiskAssessmentType, string> = {
  initial: '초기 평가',
  periodic: '정기 재평가',
  post_treatment: '조치 후 재평가',
  post_incident: '사건 발생 후 재평가',
}
