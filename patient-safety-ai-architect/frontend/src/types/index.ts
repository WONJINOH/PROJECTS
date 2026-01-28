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

// === 환자 정보 타입 ===

export type PatientWard =
  | 'ward_2'
  | 'ward_3'
  | 'ward_5'
  | 'ward_6'
  | 'ward_7'
  | 'ward_8'
  | 'ward_9'
  | 'ward_10'
  | 'ward_11'
  | 'outpatient'

export type PatientGender = 'M' | 'F'

// 병동 옵션 (드롭다운용)
export const WARD_OPTIONS = [
  { value: 'ward_2', label: '2병동' },
  { value: 'ward_3', label: '3병동' },
  { value: 'ward_5', label: '5병동' },
  { value: 'ward_6', label: '6병동' },
  { value: 'ward_7', label: '7병동' },
  { value: 'ward_8', label: '8병동' },
  { value: 'ward_9', label: '9병동' },
  { value: 'ward_10', label: '10병동' },
  { value: 'ward_11', label: '11병동' },
  { value: 'outpatient', label: '외래 환자' },
] as const

// 성별 옵션 (라디오버튼용)
export const GENDER_OPTIONS = [
  { value: 'M', label: '남' },
  { value: 'F', label: '여' },
] as const

export const WARD_LABELS: Record<PatientWard, string> = {
  ward_2: '2병동',
  ward_3: '3병동',
  ward_5: '5병동',
  ward_6: '6병동',
  ward_7: '7병동',
  ward_8: '8병동',
  ward_9: '9병동',
  ward_10: '10병동',
  ward_11: '11병동',
  outpatient: '외래 환자',
}

export const GENDER_LABELS: Record<PatientGender, string> = {
  M: '남',
  F: '여',
}

// === 발생장소 타입 (Feature 2) ===

export type LocationType =
  | 'own_room'       // 본인병실
  | 'other_room'     // 타병실
  | 'bathroom'       // 화장실
  | 'hallway'        // 복도
  | 'rehabilitation' // 재활치료실
  | 'nursing_station'// 간호사실
  | 'other'          // 기타

export const LOCATION_TYPE_OPTIONS = [
  { value: 'own_room', label: '본인병실', needsDetail: false },
  { value: 'other_room', label: '타병실', needsDetail: true, detailPlaceholder: '병실번호를 입력해주세요 (예: 302호)' },
  { value: 'bathroom', label: '화장실', needsDetail: true, detailPlaceholder: '위치를 입력해주세요 (예: 3층 화장실)' },
  { value: 'hallway', label: '복도', needsDetail: true, detailPlaceholder: '위치를 입력해주세요 (예: 3층 복도)' },
  { value: 'rehabilitation', label: '재활치료실', needsDetail: false },
  { value: 'nursing_station', label: '간호사실/처치실', needsDetail: false },
  { value: 'other', label: '기타', needsDetail: true, detailPlaceholder: '구체적인 장소를 입력해주세요' },
] as const

export const LOCATION_TYPE_LABELS: Record<LocationType, string> = {
  own_room: '본인병실',
  other_room: '타병실',
  bathroom: '화장실',
  hallway: '복도',
  rehabilitation: '재활치료실',
  nursing_station: '간호사실/처치실',
  other: '기타',
}

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
  // === 환자 정보 (공통 폼에서 입력) ===
  patientRegistrationNo: string
  patientName: string
  patientWard: PatientWard
  roomNumber: string
  patientGender: PatientGender
  patientAge: number
  patientDepartmentId: number
  patientPhysicianId: number
  patientDepartmentName?: string
  patientPhysicianName?: string
  diagnosis?: string
  // PSR 공통 필드 (대시보드용)
  outcomeImpact?: IncidentOutcomeImpact
  outcomeImpactDetail?: string
  contributingFactors?: string[]
  contributingFactorsDetail?: string
  patientPhysicalOutcome?: PatientPhysicalOutcome
  patientPhysicalOutcomeDetail?: string
  // 메타데이터
  reporterId: number
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

export type IndicatorStatusType = 'active' | 'inactive' | 'planned' | 'pending_approval' | 'rejected'

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
  code?: string  // Optional - auto-generated if not provided
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
  psr: '진료영역',
  pressure_ulcer: '환자안전영역 - 욕창',
  fall: '환자안전영역 - 낙상',
  medication: '환자안전영역 - 투약',
  restraint: '환자안전영역 - 신체보호대',
  infection: '환자안전영역 - 감염',
  staff_safety: '직원안전영역',
  lab_tat: '기타영역 - 검사 TAT',
  composite: '종합 환자안전 지표',
}

export const INDICATOR_STATUS_LABELS: Record<IndicatorStatusType, string> = {
  active: '활성',
  inactive: '비활성',
  planned: '예정',
  pending_approval: '승인 대기',
  rejected: '반려됨',
}

// ===== Lookup Types (진료과/주치의) =====

export interface Department {
  id: number
  name: string
  code?: string
  isActive: boolean
  physicianCount?: number
  createdAt: string
}

export interface Physician {
  id: number
  name: string
  departmentId: number
  departmentName?: string
  licenseNumber?: string
  specialty?: string
  isActive: boolean
  createdAt: string
}

export interface CreateDepartmentData {
  name: string
  code?: string
}

export interface CreatePhysicianData {
  name: string
  department_id: number
  license_number?: string
  specialty?: string
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
  // 환자 정보 (PDF 양식 기준)
  patientCode: string  // 환자등록번호
  patientName?: string  // 환자명
  patientAgeGroup?: string
  patientGender?: string
  roomNumber?: string  // 병실
  departmentId?: number  // 환자 진료과
  physicianId?: number  // 담당 주치의
  diagnosis?: string  // 진단명
  preFallRiskLevel?: FallRiskLevel
  morseScore?: number
  // PSR 양식 필드
  consciousnessLevel?: FallConsciousnessLevel
  activityLevel?: FallActivityLevel
  usesMobilityAid?: boolean
  mobilityAidType?: FallMobilityAid
  riskFactors?: string[]
  relatedMedications?: string[]
  // 1-2시간 이내 낙상위험약물
  immediateRiskMedications?: string[]
  immediateRiskMedicationsDetail?: string
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
  // 환자 정보 (PDF 양식 기준)
  patient_code: string  // 환자등록번호
  patient_name?: string  // 환자명
  patient_age_group?: string
  patient_gender?: string
  room_number?: string  // 병실
  department_id?: number  // 환자 진료과
  physician_id?: number  // 담당 주치의
  diagnosis?: string  // 진단명
  pre_fall_risk_level?: FallRiskLevel
  morse_score?: number
  // PSR 양식 필드
  consciousness_level?: FallConsciousnessLevel
  activity_level?: FallActivityLevel
  uses_mobility_aid?: boolean
  mobility_aid_type?: FallMobilityAid
  risk_factors?: string[]
  related_medications?: string[]
  // 1-2시간 이내 낙상위험약물
  immediate_risk_medications?: string[]
  immediate_risk_medications_detail?: string
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

// 낙상 관련 투약 옵션 (24시간 이내)
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

// 1-2시간 이내 낙상위험약물 옵션
export const FALL_IMMEDIATE_MEDICATION_OPTIONS = [
  { value: 'sedative', label: '진정제' },
  { value: 'analgesic', label: '진통제' },
  { value: 'muscle_relaxant', label: '근이완제' },
  { value: 'antipsychotic', label: '항정신병약' },
  { value: 'antiemetic', label: '항구토제' },
  { value: 'hypnotic', label: '수면제' },
  { value: 'opioid', label: '마약성진통제' },
  { value: 'other', label: '기타' },
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
  // 환자 정보 (PDF 양식 기준)
  patientCode: string  // 환자등록번호
  patientName?: string  // 환자명
  patientAgeGroup?: string
  patientGender?: string
  roomNumber?: string  // 병실
  departmentId?: number  // 환자 진료과
  physicianId?: number  // 담당 주치의
  diagnosis?: string  // 진단명
  // 오류 정보
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
  // 환자 정보 (PDF 양식 기준)
  patient_code: string  // 환자등록번호
  patient_name?: string  // 환자명
  patient_age_group?: string
  patient_gender?: string
  room_number?: string  // 병실
  department_id?: number  // 환자 진료과
  physician_id?: number  // 담당 주치의
  diagnosis?: string  // 진단명
  // 오류 정보
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

// ===== 투약오류 PDF 양식 기반 옵션 =====

// 발견 시점 옵션
export const MEDICATION_DISCOVERY_TIMING_OPTIONS = [
  { value: 'pre_administration', label: '1. 투약전발견' },
  { value: 'post_administration', label: '2. 투약후발견' },
] as const

// 오류유형 - 투약전발견
export const MEDICATION_ERROR_TYPE_BEFORE_OPTIONS = [
  { value: 'dispensing_error', label: '조제오류' },
  { value: 'prescribing', label: '처방오류' },
  { value: 'transcribing', label: '준비오류' },
] as const

// 오류유형 - 투약후발견
export const MEDICATION_ERROR_TYPE_AFTER_OPTIONS = [
  { value: 'wrong_patient', label: '환자오류' },
  { value: 'wrong_drug', label: '약품오류' },
  { value: 'wrong_time', label: '시간오류' },
  { value: 'wrong_route', label: '경로오류' },
  { value: 'wrong_dose', label: '용량오류' },
  { value: 'monitoring', label: '투약부작용' },
  { value: 'other', label: '기타' },
] as const

// 발견된 오류의 원인 (PDF 양식 기준)
export const MEDICATION_ERROR_CAUSE_OPTIONS = [
  { value: 'prescription_not_checked', label: '처방을 확인하지 않음' },
  { value: 'patient_not_verified', label: '투약직전 환자를 확인하지 않음' },
  { value: 'medication_card_not_checked', label: '투약직전 투약카드를 확인하지 않음' },
  { value: 'prescription_misinterpreted', label: '처방을 잘못 해석함' },
  { value: 'label_not_checked', label: '약품 라벨을 확인하지 않음' },
  { value: 'dose_calculation_error', label: '용량 계산오류' },
  { value: 'pharmacy_dispensing_error', label: '약국의 조제 오류' },
  { value: 'medication_delivery_delay', label: '약품의 전달 지연' },
  { value: 'physician_prescription_error', label: '의사의 처방 오류' },
  { value: 'wrong_diluent', label: '잘못된 주사 용해액 사용' },
  { value: 'wrong_infusion_rate', label: '수액세트 주입속도를 잘못 맞춤' },
  { value: 'other', label: '기타' },
] as const

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

// ===== Infection Detail Types =====

export type InfectionType =
  | 'uti_non_catheter'  // 비카테터성 요로감염
  | 'cauti'             // 카테터 관련 요로감염
  | 'pneumonia'         // 폐렴
  | 'vap'               // 인공호흡기 관련 폐렴
  | 'clabsi'            // 중심정맥관 관련 혈류감염
  | 'ssi'               // 수술부위 감염
  | 'cdiff'             // 클로스트리디움 디피실 감염
  | 'mrsa'              // MRSA
  | 'other'             // 기타

export type InfectionSite =
  | 'urinary'           // 요로
  | 'respiratory'       // 호흡기
  | 'skin'              // 피부/연조직
  | 'bloodstream'       // 혈류
  | 'surgical'          // 수술부위
  | 'gastrointestinal'  // 위장관
  | 'other'             // 기타

export type DeviceType =
  | 'urinary_catheter'  // 유치도뇨관
  | 'central_line'      // 중심정맥관
  | 'ventilator'        // 인공호흡기
  | 'peripheral_iv'     // 말초정맥관
  | 'ng_tube'           // 비위관
  | 'tracheostomy'      // 기관절개관
  | 'other'             // 기타

export interface InfectionDetail {
  id: number
  incidentId: number
  // 환자 정보
  patientCode: string
  patientName?: string
  patientAgeGroup?: string
  patientGender?: string
  roomNumber?: string
  departmentId?: number
  physicianId?: number
  diagnosis?: string
  // 감염 정보
  infectionType: InfectionType
  infectionSite?: string
  infectionSiteDetail?: string
  onsetDate?: string
  diagnosisDate?: string
  // 원인균
  pathogen?: string
  isMdro: boolean
  pathogenCultureResult?: string
  // 기기 관련
  deviceRelated: boolean
  deviceType?: string
  deviceInsertionDate?: string
  deviceDays?: number
  // 원내 감염
  isHospitalAcquired: boolean
  admissionDate?: string
  // 추가 정보
  department: string
  antibioticUsed?: string
  treatmentNotes?: string
  createdAt: string
}

export interface CreateInfectionDetailData {
  incident_id: number
  patient_code: string
  patient_name?: string
  patient_age_group?: string
  patient_gender?: string
  room_number?: string
  department_id?: number
  physician_id?: number
  diagnosis?: string
  infection_type: InfectionType
  infection_site?: string
  infection_site_detail?: string
  onset_date?: string
  diagnosis_date?: string
  pathogen?: string
  is_mdro?: boolean
  pathogen_culture_result?: string
  device_related?: boolean
  device_type?: string
  device_insertion_date?: string
  device_days?: number
  is_hospital_acquired?: boolean
  admission_date?: string
  department: string
  antibiotic_used?: string
  treatment_notes?: string
}

export const INFECTION_TYPE_LABELS: Record<InfectionType, string> = {
  uti_non_catheter: '비카테터성 요로감염',
  cauti: '카테터 관련 요로감염 (CAUTI)',
  pneumonia: '폐렴',
  vap: '인공호흡기 관련 폐렴 (VAP)',
  clabsi: '중심정맥관 관련 혈류감염 (CLABSI)',
  ssi: '수술부위 감염 (SSI)',
  cdiff: 'C.diff 감염',
  mrsa: 'MRSA 감염',
  other: '기타',
}

export const INFECTION_SITE_LABELS: Record<InfectionSite, string> = {
  urinary: '요로',
  respiratory: '호흡기',
  skin: '피부/연조직',
  bloodstream: '혈류',
  surgical: '수술부위',
  gastrointestinal: '위장관',
  other: '기타',
}

export const DEVICE_TYPE_LABELS: Record<DeviceType, string> = {
  urinary_catheter: '유치도뇨관',
  central_line: '중심정맥관',
  ventilator: '인공호흡기',
  peripheral_iv: '말초정맥관',
  ng_tube: '비위관',
  tracheostomy: '기관절개관',
  other: '기타',
}

export const INFECTION_TYPE_OPTIONS = [
  { value: 'uti_non_catheter', label: '비카테터성 요로감염' },
  { value: 'cauti', label: '카테터 관련 요로감염 (CAUTI)' },
  { value: 'pneumonia', label: '폐렴' },
  { value: 'vap', label: '인공호흡기 관련 폐렴 (VAP)' },
  { value: 'clabsi', label: '중심정맥관 관련 혈류감염 (CLABSI)' },
  { value: 'ssi', label: '수술부위 감염 (SSI)' },
  { value: 'cdiff', label: 'C.diff 감염' },
  { value: 'mrsa', label: 'MRSA 감염' },
  { value: 'other', label: '기타' },
] as const

export const INFECTION_SITE_OPTIONS = [
  { value: 'urinary', label: '요로' },
  { value: 'respiratory', label: '호흡기' },
  { value: 'skin', label: '피부/연조직' },
  { value: 'bloodstream', label: '혈류' },
  { value: 'surgical', label: '수술부위' },
  { value: 'gastrointestinal', label: '위장관' },
  { value: 'other', label: '기타' },
] as const

export const DEVICE_TYPE_OPTIONS = [
  { value: 'urinary_catheter', label: '유치도뇨관' },
  { value: 'central_line', label: '중심정맥관' },
  { value: 'ventilator', label: '인공호흡기' },
  { value: 'peripheral_iv', label: '말초정맥관' },
  { value: 'ng_tube', label: '비위관' },
  { value: 'tracheostomy', label: '기관절개관' },
  { value: 'other', label: '기타' },
] as const

// ===== Pressure Ulcer Detail Types =====

export type PressureUlcerGrade =
  | 'stage_1'        // 1단계: 발적
  | 'stage_2'        // 2단계: 부분층 손실
  | 'stage_3'        // 3단계: 전층 손실
  | 'stage_4'        // 4단계: 전층 조직 손실
  | 'unstageable'    // 미분류
  | 'dtpi'           // 심부조직손상

export type PressureUlcerLocation =
  | 'sacrum'         // 천골
  | 'heel'           // 발뒤꿈치
  | 'ischium'        // 좌골
  | 'trochanter'     // 대전자
  | 'elbow'          // 팔꿈치
  | 'occiput'        // 후두부
  | 'scapula'        // 견갑골
  | 'ear'            // 귀
  | 'other'          // 기타

export type PressureUlcerOrigin =
  | 'admission'      // 입원 시 보유
  | 'acquired'       // 재원 중 발생
  | 'unknown'        // 불명

export interface PressureUlcerDetail {
  id: number
  incidentId: number
  // 환자 정보
  patientCode: string
  patientName?: string
  patientAgeGroup?: string
  patientGender?: string
  roomNumber?: string
  admissionDate?: string
  // 욕창 정보
  ulcerId: string
  location: PressureUlcerLocation
  locationDetail?: string
  origin: PressureUlcerOrigin
  discoveryDate: string
  grade: PressureUlcerGrade
  // PUSH Score
  pushLengthWidth?: number
  pushExudate?: number
  pushTissueType?: number
  pushTotal?: number
  // 크기
  lengthCm?: number
  widthCm?: number
  depthCm?: number
  // 부서 및 추가 정보
  department: string
  riskFactors?: string
  treatmentPlan?: string
  note?: string
  // 상태
  isHealed: boolean
  healedDate?: string
  createdAt: string
}

export interface CreatePressureUlcerDetailData {
  incident_id: number
  patient_code: string
  patient_name?: string
  patient_age_group?: string
  patient_gender?: string
  room_number?: string
  admission_date?: string
  ulcer_id: string
  location: PressureUlcerLocation
  location_detail?: string
  origin: PressureUlcerOrigin
  discovery_date: string
  grade: PressureUlcerGrade
  push_length_width?: number
  push_exudate?: number
  push_tissue_type?: number
  length_cm?: number
  width_cm?: number
  depth_cm?: number
  department: string
  risk_factors?: string
  treatment_plan?: string
  note?: string
}

export const PRESSURE_ULCER_GRADE_LABELS: Record<PressureUlcerGrade, string> = {
  stage_1: '1단계 (발적)',
  stage_2: '2단계 (부분층 손실)',
  stage_3: '3단계 (전층 손실)',
  stage_4: '4단계 (전층 조직 손실)',
  unstageable: '미분류 (Unstageable)',
  dtpi: '심부조직손상 (DTPI)',
}

export const PRESSURE_ULCER_LOCATION_LABELS: Record<PressureUlcerLocation, string> = {
  sacrum: '천골',
  heel: '발뒤꿈치',
  ischium: '좌골',
  trochanter: '대전자',
  elbow: '팔꿈치',
  occiput: '후두부',
  scapula: '견갑골',
  ear: '귀',
  other: '기타',
}

export const PRESSURE_ULCER_ORIGIN_LABELS: Record<PressureUlcerOrigin, string> = {
  admission: '입원 시 보유',
  acquired: '재원 중 발생',
  unknown: '불명',
}

export const PRESSURE_ULCER_GRADE_OPTIONS = [
  { value: 'stage_1', label: '1단계 (발적)' },
  { value: 'stage_2', label: '2단계 (부분층 손실)' },
  { value: 'stage_3', label: '3단계 (전층 손실)' },
  { value: 'stage_4', label: '4단계 (전층 조직 손실)' },
  { value: 'unstageable', label: '미분류 (Unstageable)' },
  { value: 'dtpi', label: '심부조직손상 (DTPI)' },
] as const

// 욕창 발생 부위 - 앞면/뒷면 구분
export const PRESSURE_ULCER_LOCATION_OPTIONS = [
  // 후면 (Posterior) - 전통적 욕창 호발부위
  { value: 'occiput', label: '후두부 (Occiput)', labelKo: '후두부', labelEn: 'Occiput', view: 'back', category: 'bony' },
  { value: 'scapula', label: '견갑골 (Scapula)', labelKo: '견갑골', labelEn: 'Scapula', view: 'back', category: 'bony' },
  { value: 'spinous_process', label: '척추돌기 (Spinous Process)', labelKo: '척추돌기', labelEn: 'Spinous Process', view: 'back', category: 'bony' },
  { value: 'sacrum', label: '천골 (Sacrum)', labelKo: '천골', labelEn: 'Sacrum', view: 'back', category: 'bony' },
  { value: 'coccyx', label: '미골 (Coccyx)', labelKo: '미골', labelEn: 'Coccyx', view: 'back', category: 'bony' },
  { value: 'ischium', label: '좌골 (Ischium)', labelKo: '좌골', labelEn: 'Ischium', view: 'back', category: 'bony' },
  { value: 'heel', label: '발뒤꿈치 (Heel)', labelKo: '발뒤꿈치', labelEn: 'Heel', view: 'back', category: 'bony' },

  // 측면 (Lateral)
  { value: 'ear', label: '귀 (Ear)', labelKo: '귀', labelEn: 'Ear', view: 'side', category: 'bony' },
  { value: 'shoulder', label: '어깨 (Shoulder)', labelKo: '어깨', labelEn: 'Shoulder', view: 'side', category: 'bony' },
  { value: 'elbow', label: '팔꿈치 (Elbow)', labelKo: '팔꿈치', labelEn: 'Elbow', view: 'side', category: 'bony' },
  { value: 'trochanter', label: '대전자 (Trochanter)', labelKo: '대전자', labelEn: 'Trochanter', view: 'side', category: 'bony' },
  { value: 'knee_lateral', label: '무릎 외측 (Lateral Knee)', labelKo: '무릎 외측', labelEn: 'Lateral Knee', view: 'side', category: 'bony' },
  { value: 'malleolus', label: '복사뼈 (Malleolus)', labelKo: '복사뼈', labelEn: 'Malleolus', view: 'side', category: 'bony' },

  // 전면 (Anterior)
  { value: 'forehead', label: '이마 (Forehead)', labelKo: '이마', labelEn: 'Forehead', view: 'front', category: 'bony' },
  { value: 'nose', label: '코 (Nose)', labelKo: '코', labelEn: 'Nose', view: 'front', category: 'device' },
  { value: 'chin', label: '턱 (Chin)', labelKo: '턱', labelEn: 'Chin', view: 'front', category: 'bony' },
  { value: 'clavicle', label: '쇄골 (Clavicle)', labelKo: '쇄골', labelEn: 'Clavicle', view: 'front', category: 'bony' },
  { value: 'sternum', label: '흉골 (Sternum)', labelKo: '흉골', labelEn: 'Sternum', view: 'front', category: 'bony' },
  { value: 'iliac_crest', label: '장골능 (Iliac Crest)', labelKo: '장골능', labelEn: 'Iliac Crest', view: 'front', category: 'bony' },
  { value: 'patella', label: '슬개골 (Patella)', labelKo: '슬개골', labelEn: 'Patella', view: 'front', category: 'bony' },
  { value: 'shin', label: '정강이 (Shin)', labelKo: '정강이', labelEn: 'Shin', view: 'front', category: 'bony' },
  { value: 'dorsum_foot', label: '발등 (Dorsum of Foot)', labelKo: '발등', labelEn: 'Dorsum of Foot', view: 'front', category: 'bony' },
  { value: 'toes', label: '발가락 (Toes)', labelKo: '발가락', labelEn: 'Toes', view: 'front', category: 'bony' },

  // 의료기기 관련 (MDRPI)
  { value: 'nares', label: '비공 (Nares) - 비위관', labelKo: '비공', labelEn: 'Nares', view: 'front', category: 'device', device: 'NG tube' },
  { value: 'lip', label: '입술 (Lip) - 기관튜브', labelKo: '입술', labelEn: 'Lip', view: 'front', category: 'device', device: 'ETT' },
  { value: 'neck_anterior', label: '목 전면 (Anterior Neck) - 기관절개', labelKo: '목 전면', labelEn: 'Anterior Neck', view: 'front', category: 'device', device: 'Tracheostomy' },
  { value: 'meatus', label: '요도구 (Meatus) - 유치도뇨관', labelKo: '요도구', labelEn: 'Meatus', view: 'front', category: 'device', device: 'Foley catheter' },
  { value: 'finger', label: '손가락 (Finger) - SpO2 센서', labelKo: '손가락', labelEn: 'Finger', view: 'front', category: 'device', device: 'SpO2 sensor' },
  { value: 'bridge_of_nose', label: '콧등 (Bridge of Nose) - 산소마스크', labelKo: '콧등', labelEn: 'Bridge of Nose', view: 'front', category: 'device', device: 'O2 mask' },
  { value: 'cheek', label: '볼 (Cheek) - CPAP/BiPAP', labelKo: '볼', labelEn: 'Cheek', view: 'front', category: 'device', device: 'CPAP/BiPAP' },

  // 기타
  { value: 'other', label: '기타 (Other)', labelKo: '기타', labelEn: 'Other', view: 'other', category: 'other' },
] as const

// 좌/우측 옵션
export const BODY_SIDE_OPTIONS = [
  { value: 'left', label: '좌측 (Left)' },
  { value: 'right', label: '우측 (Right)' },
  { value: 'center', label: '중앙 (Center)' },
  { value: 'both', label: '양측 (Both)' },
] as const

// 부위 카테고리
export const LOCATION_CATEGORIES = [
  { value: 'bony', label: '골돌출부 (Bony Prominence)' },
  { value: 'device', label: '의료기기 관련 (MDRPI)' },
  { value: 'other', label: '기타 (Other)' },
] as const

export const PRESSURE_ULCER_ORIGIN_OPTIONS = [
  { value: 'admission', label: '입원 시 보유' },
  { value: 'acquired', label: '재원 중 발생' },
  { value: 'unknown', label: '불명' },
] as const

// ===== FMEA 위험분류 (Risk Priority Number) =====

// 심각도 (Severity) - S
export type FMEASeverity = 1 | 3 | 5 | 6 | 8 | 10

export const FMEA_SEVERITY_OPTIONS = [
  { value: 1, label: '미미한 영향 (1점)', description: '개인적으로 받는 손상이 주목할 만하지 않고 과정에 영향을 미치지 않음' },
  { value: 3, label: '약간 영향 (3점)', description: '개인적으로 받는 영향이 있고 과정상 약간의 영향을 주는 결과를 초래' },
  { value: 5, label: '중간 영향 (5점)', description: '개인이 받는 영향이 있고 과정상 주요영향을 주는 결과를 초래할 수 있음' },
  { value: 6, label: '작은 손상 (6점)', description: '개인에게 영향을 주고 과정상 주요 영향을 초래하는 것' },
  { value: 8, label: '주요 손상 (8점)', description: '개인에게 큰 손상을 초래하고 그 과정상 큰 영향을 주는 것' },
  { value: 10, label: '치명적 손상/사망 (10점)', description: '극단적으로 위험함, 고장은 개인의 죽음을 초래하고 과정에 큰 영향' },
] as const

// 발생 가능성 (Probability of Occurrence) - O
export type FMEAProbability = 1 | 3 | 5 | 7 | 9

export const FMEA_PROBABILITY_OPTIONS = [
  { value: 1, label: '발생가능성 희박 (1점)', description: '1/10,000 - 발생 없거나 거의 알려지지 않음' },
  { value: 3, label: '낮은 가능성 (3점)', description: '1/5,000 - 가능하지만 알려진 자료 없음' },
  { value: 5, label: '중간 가능성 (5점)', description: '1/200 - 문서화되어 있지만 빈번하지 않음' },
  { value: 7, label: '높은 가능성 (7점)', description: '1/100 - 문서화 되어있고 빈번함' },
  { value: 9, label: '일정하게 발생 (9점)', description: '1/20 - 문서화 되어있고 거의 확실히 발생함' },
] as const

// 발견 가능성 (Detectability) - D
export type FMEADetectability = 1 | 3 | 5 | 7 | 9

export const FMEA_DETECTABILITY_OPTIONS = [
  { value: 1, label: '확실히 발견됨 (1점)', description: '10개중 10개 - 대부분 항상 즉각적으로 발견됨' },
  { value: 3, label: '높은 가능성 (3점)', description: '10개중 7개 - 발견가능성이 높음' },
  { value: 5, label: '중간 가능성 (5점)', description: '10개중 5개 - 중간 정도의 발견 가능성' },
  { value: 7, label: '낮은 가능성 (7점)', description: '10개중 2개 - 거의 발견되지 않음' },
  { value: 9, label: '대부분 발견못함 (9점)', description: '10개중 0개 - 어떤 지점에서도 발견가능성이 없음' },
] as const

// RPN (Risk Priority Number) = Severity × Occurrence × Detectability
// 최소: 1×1×1 = 1, 최대: 10×9×9 = 810
export interface FMEARiskAssessment {
  severity: FMEASeverity
  probability: FMEAProbability
  detectability: FMEADetectability
  rpn: number // 자동 계산
}

// RPN 위험 수준 분류
export const getRPNLevel = (rpn: number): { level: string; color: string; description: string } => {
  if (rpn <= 40) return { level: '낮음', color: 'text-green-600 bg-green-100', description: '수용 가능한 위험' }
  if (rpn <= 100) return { level: '보통', color: 'text-yellow-600 bg-yellow-100', description: '관리 필요' }
  if (rpn <= 200) return { level: '높음', color: 'text-orange-600 bg-orange-100', description: '개선 조치 필요' }
  return { level: '매우 높음', color: 'text-red-600 bg-red-100', description: '즉각적인 조치 필요' }
}

// 욕창발생보고서용 타입
export interface PressureUlcerOccurrenceReport {
  // 환자 정보
  patient_registration_no: string
  patient_name: string
  patient_ward: PatientWard
  room_number: string
  patient_gender: PatientGender
  patient_age: number
  patient_department_id: number
  patient_physician_id: number
  admission_date: string
  diagnosis?: string

  // 욕창 정보
  origin: PressureUlcerOrigin
  discovery_date: string
  location: PressureUlcerLocation
  location_detail?: string
  grade: PressureUlcerGrade

  // PUSH 점수
  push_length_width?: number
  push_exudate?: number
  push_tissue_type?: number

  // 크기
  length_cm?: number
  width_cm?: number
  depth_cm?: number

  // 추가 정보
  risk_factors?: string
  treatment_plan?: string
  note?: string

  // FMEA 위험분류 (원내발생 시)
  fmea_severity?: FMEASeverity
  fmea_probability?: FMEAProbability
  fmea_detectability?: FMEADetectability
}
