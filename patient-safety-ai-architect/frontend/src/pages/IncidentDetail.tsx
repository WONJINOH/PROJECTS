import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Calendar,
  MapPin,
  User,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
  AlertTriangle,
  Activity,
  Pill,
  HeartCrack,
  ThumbsUp,
  ThumbsDown,
  Edit3,
  Plus,
} from 'lucide-react'
import { incidentApi, approvalApi, fallDetailApi, medicationDetailApi, infectionDetailApi, pressureUlcerDetailApi } from '@/utils/api'
import { useAuth } from '@/hooks/useAuth'
import ActionList from '@/components/actions/ActionList'
import FallDetailForm from '@/components/details/FallDetailForm'
import MedicationDetailForm from '@/components/details/MedicationDetailForm'
import InfectionDetailForm from '@/components/details/InfectionDetailForm'
import PressureUlcerDetailForm from '@/components/details/PressureUlcerDetailForm'
import type {
  IncidentCategory,
  IncidentGrade,
  IncidentStatus,
  ApprovalLevel,
  ApprovalStatus,
} from '@/types'
import {
  FALL_INJURY_LABELS as fallInjuryLabels,
  FALL_LOCATION_LABELS as fallLocationLabels,
  FALL_CAUSE_LABELS as fallCauseLabels,
  MEDICATION_ERROR_TYPE_LABELS as medErrorTypeLabels,
  MEDICATION_STAGE_LABELS as medStageLabels,
  MEDICATION_SEVERITY_LABELS as medSeverityLabels,
  HIGH_ALERT_LABELS as highAlertLabels,
  INFECTION_TYPE_LABELS as infectionTypeLabels,
  INFECTION_SITE_LABELS as infectionSiteLabels,
  DEVICE_TYPE_LABELS as deviceTypeLabels,
  PRESSURE_ULCER_GRADE_LABELS as pressureUlcerGradeLabels,
  PRESSURE_ULCER_LOCATION_LABELS as pressureUlcerLocationLabels,
  PRESSURE_ULCER_ORIGIN_LABELS as pressureUlcerOriginLabels,
} from '@/types'

const gradeLabels: Record<IncidentGrade, string> = {
  near_miss: '근접오류',
  no_harm: '위해없음',
  mild: '경증',
  moderate: '중등도',
  severe: '중증',
  death: '사망',
}

const gradeColors: Record<IncidentGrade, string> = {
  near_miss: 'bg-gray-100 text-gray-800',
  no_harm: 'bg-green-100 text-green-800',
  mild: 'bg-yellow-100 text-yellow-800',
  moderate: 'bg-orange-100 text-orange-800',
  severe: 'bg-red-100 text-red-800',
  death: 'bg-red-200 text-red-900',
}

const categoryLabels: Record<IncidentCategory, string> = {
  fall: '낙상',
  medication: '투약',
  pressure_ulcer: '욕창',
  infection: '감염',
  medical_device: '의료기기',
  surgery: '수술',
  transfusion: '수혈',
  other: '기타',
}

const statusLabels: Record<IncidentStatus, string> = {
  draft: '초안',
  submitted: '제출됨',
  approved: '승인됨',
  closed: '종결',
}

const approvalLevelLabels: Record<string, string> = {
  l1_qps: 'QI담당자 (L1)',
  l2_vice_chair: '부원장 (L2)',
  l3_director: '원장 (L3)',
}

// Role to approval level mapping
const roleCanApproveLevel: Record<string, ApprovalLevel[]> = {
  qps_staff: ['l1_qps'],
  vice_chair: ['l1_qps', 'l2_vice_chair'],
  director: ['l1_qps', 'l2_vice_chair', 'l3_director'],
  master: ['l1_qps', 'l2_vice_chair', 'l3_director'],
}

// API Response types (snake_case)
interface ApiIncident {
  id: number
  category: IncidentCategory
  grade: IncidentGrade
  occurred_at: string
  location: string
  description: string
  immediate_action: string
  reported_at: string
  reporter_name?: string
  root_cause?: string
  improvements?: string
  reporter_id: number
  department?: string
  status: IncidentStatus
  created_at: string
  updated_at: string
}

interface ApiApproval {
  id: number
  incident_id: number
  approver_id?: number
  level: ApprovalLevel
  status: ApprovalStatus
  comment?: string
  rejection_reason?: string
  created_at: string
  decided_at?: string
  approver_name?: string
}

interface ApiFallDetail {
  id: number
  incident_id: number
  patient_code: string
  patient_age_group?: string
  patient_gender?: string
  pre_fall_risk_level?: string
  morse_score?: number
  fall_location: string
  fall_location_detail?: string
  fall_cause: string
  fall_cause_detail?: string
  occurred_hour?: number
  shift?: string
  injury_level: string
  injury_description?: string
  activity_at_fall?: string
  was_supervised: boolean
  had_fall_prevention: boolean
  department: string
  is_recurrence: boolean
  previous_fall_count: number
  created_at: string
}

interface ApiMedicationDetail {
  id: number
  incident_id: number
  patient_code: string
  patient_age_group?: string
  error_type: string
  error_stage: string
  error_severity: string
  is_near_miss: boolean
  medication_category?: string
  is_high_alert: boolean
  high_alert_type?: string
  intended_dose?: string
  actual_dose?: string
  intended_route?: string
  actual_route?: string
  discovered_by_role?: string
  discovery_method?: string
  department: string
  barcode_scanned?: boolean
  contributing_factors?: string
  created_at: string
}

interface ApiInfectionDetail {
  id: number
  incident_id: number
  patient_code: string
  patient_name?: string
  patient_age_group?: string
  patient_gender?: string
  room_number?: string
  department_id?: number
  physician_id?: number
  diagnosis?: string
  infection_type: string
  infection_site?: string
  infection_site_detail?: string
  onset_date?: string
  diagnosis_date?: string
  pathogen?: string
  is_mdro: boolean
  pathogen_culture_result?: string
  device_related: boolean
  device_type?: string
  device_insertion_date?: string
  device_days?: number
  is_hospital_acquired: boolean
  admission_date?: string
  department: string
  antibiotic_used?: string
  treatment_notes?: string
  created_at: string
}

interface ApiPressureUlcerDetail {
  id: number
  incident_id: number
  patient_code: string
  patient_name?: string
  patient_gender?: string
  room_number?: string
  ulcer_id: string
  location: string
  location_detail?: string
  origin: string
  discovery_date?: string
  grade: string
  push_length_width?: number
  push_exudate?: number
  push_tissue_type?: number
  push_total?: number
  length_cm?: number
  width_cm?: number
  depth_cm?: number
  risk_factors?: string
  treatment_plan?: string
  note?: string
  department: string
  created_at: string
}

export default function IncidentDetail() {
  const { id } = useParams()
  const incidentId = Number(id)
  const queryClient = useQueryClient()
  const { user } = useAuth()

  // State for approval actions
  const [approvalComment, setApprovalComment] = useState('')
  const [rejectionReason, setRejectionReason] = useState('')
  const [showRejectModal, setShowRejectModal] = useState(false)

  // State for detail forms
  const [showFallDetailForm, setShowFallDetailForm] = useState(false)
  const [showMedicationDetailForm, setShowMedicationDetailForm] = useState(false)
  const [showInfectionDetailForm, setShowInfectionDetailForm] = useState(false)
  const [showPressureUlcerDetailForm, setShowPressureUlcerDetailForm] = useState(false)

  // Fetch incident
  const {
    data: incident,
    isLoading: incidentLoading,
    isError: incidentError,
  } = useQuery({
    queryKey: ['incident', incidentId],
    queryFn: async () => {
      const response = await incidentApi.get(incidentId)
      return response.data as ApiIncident
    },
    enabled: !!incidentId,
  })

  // Fetch approval status
  const { data: approvals } = useQuery({
    queryKey: ['approvals', incidentId],
    queryFn: async () => {
      try {
        const response = await approvalApi.getStatus(incidentId)
        // API returns {incident_id, current_level, next_required_level, is_fully_approved, history}
        // Extract history array which contains the approval records
        return (response.data.history || []) as ApiApproval[]
      } catch {
        return []
      }
    },
    enabled: !!incidentId,
  })

  // Fetch fall detail (only for fall incidents)
  const { data: fallDetail } = useQuery({
    queryKey: ['fallDetail', incidentId],
    queryFn: async () => {
      try {
        const response = await fallDetailApi.getByIncident(incidentId)
        return response.data as ApiFallDetail
      } catch {
        return null
      }
    },
    enabled: !!incident && incident.category === 'fall',
  })

  // Fetch medication detail (only for medication incidents)
  const { data: medicationDetail } = useQuery({
    queryKey: ['medicationDetail', incidentId],
    queryFn: async () => {
      try {
        const response = await medicationDetailApi.getByIncident(incidentId)
        return response.data as ApiMedicationDetail
      } catch {
        return null
      }
    },
    enabled: !!incident && incident.category === 'medication',
  })

  // Fetch infection detail (only for infection incidents)
  const { data: infectionDetail } = useQuery({
    queryKey: ['infectionDetail', incidentId],
    queryFn: async () => {
      try {
        const response = await infectionDetailApi.getByIncident(incidentId)
        return response.data as ApiInfectionDetail
      } catch {
        return null
      }
    },
    enabled: !!incident && incident.category === 'infection',
  })

  // Fetch pressure ulcer detail (only for pressure_ulcer incidents)
  const { data: pressureUlcerDetail } = useQuery({
    queryKey: ['pressureUlcerDetail', incidentId],
    queryFn: async () => {
      try {
        const response = await pressureUlcerDetailApi.getByIncident(incidentId)
        return response.data as ApiPressureUlcerDetail
      } catch {
        return null
      }
    },
    enabled: !!incident && incident.category === 'pressure_ulcer',
  })

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: async (comment?: string) => {
      return approvalApi.approve(incidentId, comment)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals', incidentId] })
      queryClient.invalidateQueries({ queryKey: ['incident', incidentId] })
      setApprovalComment('')
      alert('승인되었습니다.')
    },
    onError: (error: Error) => {
      alert(`승인 실패: ${error.message}`)
    },
  })

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: async (reason: string) => {
      return approvalApi.reject(incidentId, reason)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals', incidentId] })
      queryClient.invalidateQueries({ queryKey: ['incident', incidentId] })
      setRejectionReason('')
      setShowRejectModal(false)
      alert('반려되었습니다.')
    },
    onError: (error: Error) => {
      alert(`반려 실패: ${error.message}`)
    },
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // Check if user can approve a specific level
  const canApproveLevel = (level: ApprovalLevel): boolean => {
    if (!user?.role) return false
    const allowedLevels = roleCanApproveLevel[user.role] || []
    return allowedLevels.includes(level)
  }

  // Find the next pending approval that user can handle
  const getNextPendingApproval = (): ApiApproval | null => {
    if (!approvals) return null
    const pending = approvals.find(
      (a) => a.status === 'pending' && canApproveLevel(a.level)
    )
    return pending || null
  }

  // Check if user can add/edit detail analysis (only QPS_STAFF and MASTER)
  const canEditDetailAnalysis = (): boolean => {
    if (!user?.role) return false
    return ['qps_staff', 'master'].includes(user.role.toLowerCase())
  }

  // Check if user can view reporter's optional fields (root_cause, improvements)
  // Only QPS_STAFF, VICE_CHAIR, DIRECTOR, MASTER can see these as reference
  const canViewReporterOptionalFields = (): boolean => {
    if (!user?.role) return false
    return ['qps_staff', 'vice_chair', 'director', 'master'].includes(user.role.toLowerCase())
  }

  const handleApprove = () => {
    approveMutation.mutate(approvalComment || undefined)
  }

  const handleReject = () => {
    if (!rejectionReason.trim()) {
      alert('반려 사유를 입력해주세요.')
      return
    }
    rejectMutation.mutate(rejectionReason)
  }

  if (incidentLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        <span className="ml-3 text-gray-500">데이터를 불러오는 중...</span>
      </div>
    )
  }

  if (incidentError || !incident) {
    return (
      <div className="max-w-4xl mx-auto">
        <Link
          to="/incidents"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="h-4 w-4" />
          목록으로
        </Link>
        <div className="card bg-red-50 border-red-200">
          <div className="flex items-center gap-3 text-red-700">
            <AlertCircle className="h-5 w-5" />
            <span>사고 보고서를 찾을 수 없습니다.</span>
          </div>
        </div>
      </div>
    )
  }

  const nextPendingApproval = getNextPendingApproval()

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back Button */}
      <Link
        to="/incidents"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="h-4 w-4" />
        목록으로
      </Link>

      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            사고 보고서 #{incident.id}
          </h1>
          <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              {formatDate(incident.occurred_at)}
            </span>
            <span className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              {incident.location}
            </span>
            {incident.reporter_name && (
              <span className="flex items-center gap-1">
                <User className="h-4 w-4" />
                {incident.reporter_name}
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <span className="badge bg-blue-100 text-blue-800">
            {categoryLabels[incident.category]}
          </span>
          <span className={`badge ${gradeColors[incident.grade]}`}>
            {gradeLabels[incident.grade]}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-3">사고 내용</h2>
            <p className="text-gray-700 whitespace-pre-wrap">
              {incident.description}
            </p>
          </div>

          {/* Immediate Action */}
          <div className="card border-l-4 border-l-amber-500">
            <h2 className="text-lg font-semibold mb-3">즉시 조치</h2>
            <p className="text-gray-700 whitespace-pre-wrap">
              {incident.immediate_action}
            </p>
          </div>

          {/* Fall Detail Section */}
          {incident.category === 'fall' && fallDetail && (
            <div className="card border-l-4 border-l-orange-500">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Activity className="h-5 w-5 text-orange-600" />
                  낙상 상세 정보
                  <span className="text-xs font-normal text-green-600 bg-green-50 px-2 py-0.5 rounded">분석 완료</span>
                </h2>
                {canEditDetailAnalysis() && (
                  <button
                    onClick={() => setShowFallDetailForm(true)}
                    className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    <Edit3 className="h-4 w-4" />
                    수정
                  </button>
                )}
              </div>
              <dl className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-gray-500">환자 코드</dt>
                  <dd className="font-medium">{fallDetail.patient_code}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">부서</dt>
                  <dd className="font-medium">{fallDetail.department}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">발생 장소</dt>
                  <dd className="font-medium">
                    {fallLocationLabels[fallDetail.fall_location as keyof typeof fallLocationLabels] || fallDetail.fall_location}
                    {fallDetail.fall_location_detail && ` (${fallDetail.fall_location_detail})`}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">낙상 원인</dt>
                  <dd className="font-medium">
                    {fallCauseLabels[fallDetail.fall_cause as keyof typeof fallCauseLabels] || fallDetail.fall_cause}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">손상 정도</dt>
                  <dd className="font-medium">
                    <span className={`badge ${
                      fallDetail.injury_level === 'none' ? 'bg-green-100 text-green-800' :
                      fallDetail.injury_level === 'minor' ? 'bg-yellow-100 text-yellow-800' :
                      fallDetail.injury_level === 'moderate' ? 'bg-orange-100 text-orange-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {fallInjuryLabels[fallDetail.injury_level as keyof typeof fallInjuryLabels] || fallDetail.injury_level}
                    </span>
                  </dd>
                </div>
                {fallDetail.morse_score !== null && fallDetail.morse_score !== undefined && (
                  <div>
                    <dt className="text-gray-500">Morse 점수</dt>
                    <dd className="font-medium">{fallDetail.morse_score}점</dd>
                  </div>
                )}
                {fallDetail.occurred_hour !== null && fallDetail.occurred_hour !== undefined && (
                  <div>
                    <dt className="text-gray-500">발생 시간</dt>
                    <dd className="font-medium">{fallDetail.occurred_hour}시 ({fallDetail.shift || '-'})</dd>
                  </div>
                )}
                <div>
                  <dt className="text-gray-500">감독 여부</dt>
                  <dd className="font-medium">{fallDetail.was_supervised ? '예' : '아니오'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">낙상예방조치</dt>
                  <dd className="font-medium">{fallDetail.had_fall_prevention ? '시행됨' : '미시행'}</dd>
                </div>
                {fallDetail.is_recurrence && (
                  <div>
                    <dt className="text-gray-500">재발</dt>
                    <dd className="font-medium text-red-600">예 (이전 {fallDetail.previous_fall_count}회)</dd>
                  </div>
                )}
              </dl>
              {fallDetail.injury_description && (
                <div className="mt-4 pt-4 border-t">
                  <dt className="text-gray-500 text-sm">손상 설명</dt>
                  <dd className="mt-1 text-gray-700">{fallDetail.injury_description}</dd>
                </div>
              )}
            </div>
          )}

          {/* Fall Detail Add Button (when no detail exists) - Only QPS/MASTER can add */}
          {incident.category === 'fall' && !fallDetail && (
            <div className="card border-l-4 border-l-orange-500 border-dashed">
              <div className="text-center py-4">
                <Activity className="h-8 w-8 text-orange-400 mx-auto mb-2" />
                <p className="text-gray-500 mb-3">
                  {canEditDetailAnalysis()
                    ? '낙상 상세 정보가 없습니다'
                    : '낙상 상세 분석 대기 중'}
                </p>
                {canEditDetailAnalysis() && (
                  <button
                    onClick={() => setShowFallDetailForm(true)}
                    className="btn-secondary flex items-center gap-2 mx-auto"
                  >
                    <Plus className="h-4 w-4" />
                    상세 정보 추가
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Medication Detail Section */}
          {incident.category === 'medication' && medicationDetail && (
            <div className="card border-l-4 border-l-purple-500">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Pill className="h-5 w-5 text-purple-600" />
                  투약 오류 상세 정보
                  <span className="text-xs font-normal text-green-600 bg-green-50 px-2 py-0.5 rounded">분석 완료</span>
                </h2>
                {canEditDetailAnalysis() && (
                  <button
                    onClick={() => setShowMedicationDetailForm(true)}
                    className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    <Edit3 className="h-4 w-4" />
                    수정
                  </button>
                )}
              </div>
              <dl className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-gray-500">환자 코드</dt>
                  <dd className="font-medium">{medicationDetail.patient_code}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">부서</dt>
                  <dd className="font-medium">{medicationDetail.department}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">오류 유형</dt>
                  <dd className="font-medium">
                    {medErrorTypeLabels[medicationDetail.error_type as keyof typeof medErrorTypeLabels] || medicationDetail.error_type}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">발견 단계</dt>
                  <dd className="font-medium">
                    {medStageLabels[medicationDetail.error_stage as keyof typeof medStageLabels] || medicationDetail.error_stage}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">심각도 (NCC MERP)</dt>
                  <dd className="font-medium">
                    <span className={`badge ${
                      ['A', 'B'].includes(medicationDetail.error_severity) ? 'bg-green-100 text-green-800' :
                      ['C', 'D'].includes(medicationDetail.error_severity) ? 'bg-yellow-100 text-yellow-800' :
                      ['E', 'F'].includes(medicationDetail.error_severity) ? 'bg-orange-100 text-orange-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {medSeverityLabels[medicationDetail.error_severity as keyof typeof medSeverityLabels] || medicationDetail.error_severity}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">근접오류</dt>
                  <dd className="font-medium">{medicationDetail.is_near_miss ? '예' : '아니오'}</dd>
                </div>
                {medicationDetail.is_high_alert && (
                  <div className="col-span-2">
                    <dt className="text-gray-500">고위험 약물</dt>
                    <dd className="font-medium text-red-600">
                      {highAlertLabels[medicationDetail.high_alert_type as keyof typeof highAlertLabels] || medicationDetail.high_alert_type || '해당'}
                    </dd>
                  </div>
                )}
                {(medicationDetail.intended_dose || medicationDetail.actual_dose) && (
                  <>
                    <div>
                      <dt className="text-gray-500">의도한 용량</dt>
                      <dd className="font-medium">{medicationDetail.intended_dose || '-'}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">실제 용량</dt>
                      <dd className="font-medium">{medicationDetail.actual_dose || '-'}</dd>
                    </div>
                  </>
                )}
                {medicationDetail.discovered_by_role && (
                  <div>
                    <dt className="text-gray-500">발견자</dt>
                    <dd className="font-medium">{medicationDetail.discovered_by_role}</dd>
                  </div>
                )}
                {medicationDetail.discovery_method && (
                  <div>
                    <dt className="text-gray-500">발견 방법</dt>
                    <dd className="font-medium">{medicationDetail.discovery_method}</dd>
                  </div>
                )}
              </dl>
              {medicationDetail.contributing_factors && (
                <div className="mt-4 pt-4 border-t">
                  <dt className="text-gray-500 text-sm">기여 요인</dt>
                  <dd className="mt-1 text-gray-700">{medicationDetail.contributing_factors}</dd>
                </div>
              )}
            </div>
          )}

          {/* Medication Detail Add Button (when no detail exists) - Only QPS/MASTER can add */}
          {incident.category === 'medication' && !medicationDetail && (
            <div className="card border-l-4 border-l-purple-500 border-dashed">
              <div className="text-center py-4">
                <Pill className="h-8 w-8 text-purple-400 mx-auto mb-2" />
                <p className="text-gray-500 mb-3">
                  {canEditDetailAnalysis()
                    ? '투약 오류 상세 정보가 없습니다'
                    : '투약 오류 상세 분석 대기 중'}
                </p>
                {canEditDetailAnalysis() && (
                  <button
                    onClick={() => setShowMedicationDetailForm(true)}
                    className="btn-secondary flex items-center gap-2 mx-auto"
                  >
                    <Plus className="h-4 w-4" />
                    상세 정보 추가
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Infection Detail Section */}
          {incident.category === 'infection' && infectionDetail && (
            <div className="card border-l-4 border-l-red-500">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  감염 상세 정보
                </h2>
                {canEditDetailAnalysis() && (
                  <button
                    onClick={() => setShowInfectionDetailForm(true)}
                    className="btn-secondary text-sm flex items-center gap-1"
                  >
                    <Edit3 className="h-4 w-4" />
                    수정
                  </button>
                )}
              </div>
              <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">환자등록번호</dt>
                  <dd className="font-medium">{infectionDetail.patient_code}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">발생 부서</dt>
                  <dd className="font-medium">{infectionDetail.department}</dd>
                </div>
                <div className="flex justify-between col-span-2">
                  <dt className="text-gray-500">감염 유형</dt>
                  <dd className="font-medium">
                    {infectionTypeLabels[infectionDetail.infection_type as keyof typeof infectionTypeLabels] || infectionDetail.infection_type}
                  </dd>
                </div>
                {infectionDetail.infection_site && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">감염 부위</dt>
                    <dd className="font-medium">
                      {infectionSiteLabels[infectionDetail.infection_site as keyof typeof infectionSiteLabels] || infectionDetail.infection_site}
                    </dd>
                  </div>
                )}
                {infectionDetail.onset_date && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">발생일</dt>
                    <dd className="font-medium">{infectionDetail.onset_date}</dd>
                  </div>
                )}
                {infectionDetail.pathogen && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">원인균</dt>
                    <dd className="font-medium">{infectionDetail.pathogen}</dd>
                  </div>
                )}
                <div className="flex justify-between">
                  <dt className="text-gray-500">다제내성균 (MDRO)</dt>
                  <dd className="font-medium">{infectionDetail.is_mdro ? '예' : '아니오'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">기기 관련</dt>
                  <dd className="font-medium">{infectionDetail.device_related ? '예' : '아니오'}</dd>
                </div>
                {infectionDetail.device_related && infectionDetail.device_type && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">관련 기기</dt>
                    <dd className="font-medium">
                      {deviceTypeLabels[infectionDetail.device_type as keyof typeof deviceTypeLabels] || infectionDetail.device_type}
                    </dd>
                  </div>
                )}
                <div className="flex justify-between">
                  <dt className="text-gray-500">원내 감염</dt>
                  <dd className="font-medium">{infectionDetail.is_hospital_acquired ? '예' : '아니오'}</dd>
                </div>
                {infectionDetail.antibiotic_used && (
                  <div className="flex justify-between col-span-2">
                    <dt className="text-gray-500">사용 항생제</dt>
                    <dd className="font-medium">{infectionDetail.antibiotic_used}</dd>
                  </div>
                )}
              </div>
              {infectionDetail.treatment_notes && (
                <div className="mt-4 pt-3 border-t">
                  <dt className="text-sm text-gray-500">치료 내용</dt>
                  <dd className="mt-1 text-gray-700">{infectionDetail.treatment_notes}</dd>
                </div>
              )}
            </div>
          )}

          {/* Infection Detail Add Button (when no detail exists) - Only QPS/MASTER can add */}
          {incident.category === 'infection' && !infectionDetail && (
            <div className="card border-l-4 border-l-red-500 border-dashed">
              <div className="text-center py-4">
                <AlertTriangle className="h-8 w-8 text-red-400 mx-auto mb-2" />
                <p className="text-gray-500 mb-3">
                  {canEditDetailAnalysis()
                    ? '감염 상세 정보가 없습니다'
                    : '감염 상세 분석 대기 중'}
                </p>
                {canEditDetailAnalysis() && (
                  <button
                    onClick={() => setShowInfectionDetailForm(true)}
                    className="btn-secondary flex items-center gap-2 mx-auto"
                  >
                    <Plus className="h-4 w-4" />
                    상세 정보 추가
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Pressure Ulcer Detail Section */}
          {incident.category === 'pressure_ulcer' && pressureUlcerDetail && (
            <div className="card border-l-4 border-l-pink-500">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <HeartCrack className="h-5 w-5 text-pink-600" />
                  욕창 상세 정보
                  <span className="text-xs font-normal text-green-600 bg-green-50 px-2 py-0.5 rounded">분석 완료</span>
                </h2>
                {canEditDetailAnalysis() && (
                  <button
                    onClick={() => setShowPressureUlcerDetailForm(true)}
                    className="btn-secondary text-sm flex items-center gap-1"
                  >
                    <Edit3 className="h-4 w-4" />
                    수정
                  </button>
                )}
              </div>
              <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">환자등록번호</dt>
                  <dd className="font-medium">{pressureUlcerDetail.patient_code}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">욕창 ID</dt>
                  <dd className="font-medium">{pressureUlcerDetail.ulcer_id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">발생 부위</dt>
                  <dd className="font-medium">
                    {pressureUlcerLocationLabels[pressureUlcerDetail.location as keyof typeof pressureUlcerLocationLabels] || pressureUlcerDetail.location}
                    {pressureUlcerDetail.location_detail && ` (${pressureUlcerDetail.location_detail})`}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">발생 시점</dt>
                  <dd className="font-medium">
                    {pressureUlcerOriginLabels[pressureUlcerDetail.origin as keyof typeof pressureUlcerOriginLabels] || pressureUlcerDetail.origin}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">단계</dt>
                  <dd className="font-medium">
                    <span className={`badge ${
                      pressureUlcerDetail.grade === 'stage_1' ? 'bg-yellow-100 text-yellow-800' :
                      pressureUlcerDetail.grade === 'stage_2' ? 'bg-orange-100 text-orange-800' :
                      pressureUlcerDetail.grade === 'stage_3' ? 'bg-red-100 text-red-800' :
                      pressureUlcerDetail.grade === 'stage_4' ? 'bg-red-200 text-red-900' :
                      'bg-purple-100 text-purple-800'
                    }`}>
                      {pressureUlcerGradeLabels[pressureUlcerDetail.grade as keyof typeof pressureUlcerGradeLabels] || pressureUlcerDetail.grade}
                    </span>
                  </dd>
                </div>
                {pressureUlcerDetail.discovery_date && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">발견일</dt>
                    <dd className="font-medium">{pressureUlcerDetail.discovery_date}</dd>
                  </div>
                )}
                {(pressureUlcerDetail.length_cm || pressureUlcerDetail.width_cm) && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">크기 (L×W×D)</dt>
                    <dd className="font-medium">
                      {pressureUlcerDetail.length_cm || '-'} × {pressureUlcerDetail.width_cm || '-'} × {pressureUlcerDetail.depth_cm || '-'} cm
                    </dd>
                  </div>
                )}
                {pressureUlcerDetail.push_total !== null && pressureUlcerDetail.push_total !== undefined && (
                  <div className="col-span-2 mt-2 pt-2 border-t">
                    <dt className="text-gray-500 mb-1">PUSH Score</dt>
                    <dd className="font-medium">
                      <span className={`text-lg ${
                        pressureUlcerDetail.push_total <= 6 ? 'text-green-600' :
                        pressureUlcerDetail.push_total <= 12 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {pressureUlcerDetail.push_total}점
                      </span>
                      <span className="text-gray-400 text-xs ml-2">
                        (면적 {pressureUlcerDetail.push_length_width || 0} + 삼출물 {pressureUlcerDetail.push_exudate || 0} + 조직유형 {pressureUlcerDetail.push_tissue_type || 0})
                      </span>
                    </dd>
                  </div>
                )}
                <div className="flex justify-between">
                  <dt className="text-gray-500">발생 부서</dt>
                  <dd className="font-medium">{pressureUlcerDetail.department}</dd>
                </div>
              </div>
              {pressureUlcerDetail.risk_factors && (
                <div className="mt-4 pt-3 border-t">
                  <dt className="text-sm text-gray-500">위험 요인</dt>
                  <dd className="mt-1 text-gray-700">{pressureUlcerDetail.risk_factors}</dd>
                </div>
              )}
              {pressureUlcerDetail.treatment_plan && (
                <div className="mt-3">
                  <dt className="text-sm text-gray-500">치료 계획</dt>
                  <dd className="mt-1 text-gray-700">{pressureUlcerDetail.treatment_plan}</dd>
                </div>
              )}
              {pressureUlcerDetail.note && (
                <div className="mt-3">
                  <dt className="text-sm text-gray-500">비고</dt>
                  <dd className="mt-1 text-gray-700">{pressureUlcerDetail.note}</dd>
                </div>
              )}
            </div>
          )}

          {/* Pressure Ulcer Detail Add Button (when no detail exists) - Only QPS/MASTER can add */}
          {incident.category === 'pressure_ulcer' && !pressureUlcerDetail && (
            <div className="card border-l-4 border-l-pink-500 border-dashed">
              <div className="text-center py-4">
                <HeartCrack className="h-8 w-8 text-pink-400 mx-auto mb-2" />
                <p className="text-gray-500 mb-3">
                  {canEditDetailAnalysis()
                    ? '욕창 상세 정보가 없습니다'
                    : '욕창 상세 분석 대기 중'}
                </p>
                {canEditDetailAnalysis() && (
                  <button
                    onClick={() => setShowPressureUlcerDetailForm(true)}
                    className="btn-secondary flex items-center gap-2 mx-auto"
                  >
                    <Plus className="h-4 w-4" />
                    상세 정보 추가
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Root Cause - Only visible to QPS/MASTER as reference */}
          {incident.root_cause && canViewReporterOptionalFields() && (
            <div className="card bg-blue-50 border border-blue-100">
              <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                근본 원인 분석
                <span className="text-xs font-normal text-blue-600 bg-blue-100 px-2 py-0.5 rounded">보고자 의견 (참고용)</span>
              </h2>
              <p className="text-gray-700 whitespace-pre-wrap">
                {incident.root_cause}
              </p>
            </div>
          )}

          {/* Improvements - Only visible to QPS/MASTER as reference */}
          {incident.improvements && canViewReporterOptionalFields() && (
            <div className="card bg-blue-50 border border-blue-100">
              <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
                개선 방안
                <span className="text-xs font-normal text-blue-600 bg-blue-100 px-2 py-0.5 rounded">보고자 의견 (참고용)</span>
              </h2>
              <p className="text-gray-700 whitespace-pre-wrap">
                {incident.improvements}
              </p>
            </div>
          )}

          {/* Actions (CAPA) */}
          <div className="card">
            <ActionList incidentId={incidentId} incidentStatus={incident.status} />
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Approval Actions */}
          {nextPendingApproval && incident.status === 'submitted' && (
            <div className="card border-2 border-primary-200 bg-primary-50">
              <h2 className="text-lg font-semibold mb-4 text-primary-900">승인 요청</h2>
              <p className="text-sm text-primary-700 mb-4">
                {approvalLevelLabels[nextPendingApproval.level]} 승인이 필요합니다.
              </p>

              <div className="space-y-3">
                <textarea
                  placeholder="승인 의견 (선택사항)"
                  value={approvalComment}
                  onChange={(e) => setApprovalComment(e.target.value)}
                  className="input-field text-sm"
                  rows={2}
                />

                <div className="flex gap-2">
                  <button
                    onClick={handleApprove}
                    disabled={approveMutation.isPending}
                    className="flex-1 btn-primary flex items-center justify-center gap-2"
                  >
                    {approveMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <ThumbsUp className="h-4 w-4" />
                    )}
                    승인
                  </button>
                  <button
                    onClick={() => setShowRejectModal(true)}
                    disabled={rejectMutation.isPending}
                    className="flex-1 bg-red-600 text-white rounded-md px-4 py-2 hover:bg-red-700 flex items-center justify-center gap-2"
                  >
                    <ThumbsDown className="h-4 w-4" />
                    반려
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Approval Status */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">승인 현황</h2>
            {approvals && approvals.length > 0 ? (
              <div className="space-y-4">
                {approvals.map((approval, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3"
                  >
                    {approval.status === 'approved' ? (
                      <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                    ) : approval.status === 'rejected' ? (
                      <XCircle className="h-5 w-5 text-red-500 mt-0.5" />
                    ) : (
                      <Clock className="h-5 w-5 text-gray-400 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">
                        {approvalLevelLabels[approval.level] || approval.level}
                      </p>
                      {approval.status === 'approved' && (
                        <>
                          <p className="text-sm text-green-600">
                            승인됨 {approval.decided_at && `• ${formatDate(approval.decided_at)}`}
                          </p>
                          {approval.comment && (
                            <p className="text-sm text-gray-500 mt-1">"{approval.comment}"</p>
                          )}
                        </>
                      )}
                      {approval.status === 'rejected' && (
                        <>
                          <p className="text-sm text-red-600">
                            반려됨 {approval.decided_at && `• ${formatDate(approval.decided_at)}`}
                          </p>
                          {approval.rejection_reason && (
                            <p className="text-sm text-red-500 mt-1">사유: {approval.rejection_reason}</p>
                          )}
                        </>
                      )}
                      {approval.status === 'pending' && (
                        <p className="text-sm text-gray-500">승인 대기 중</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                {incident.status === 'draft' ? '제출 후 승인 절차가 시작됩니다' : '승인 정보가 없습니다'}
              </p>
            )}
          </div>

          {/* Attachments */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">첨부파일</h2>
            <p className="text-sm text-gray-500">첨부파일 기능은 추후 지원됩니다</p>
          </div>

          {/* Metadata */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">정보</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">보고일시</dt>
                <dd className="text-gray-900">{formatDate(incident.reported_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">등록일시</dt>
                <dd className="text-gray-900">{formatDate(incident.created_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">상태</dt>
                <dd className="text-gray-900">{statusLabels[incident.status]}</dd>
              </div>
              {incident.department && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">부서</dt>
                  <dd className="text-gray-900">{incident.department}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold mb-4">반려 사유 입력</h3>
            <textarea
              placeholder="반려 사유를 입력해주세요 (필수)"
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="input-field w-full"
              rows={4}
              autoFocus
            />
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => {
                  setShowRejectModal(false)
                  setRejectionReason('')
                }}
                className="flex-1 btn-secondary"
              >
                취소
              </button>
              <button
                onClick={handleReject}
                disabled={rejectMutation.isPending || !rejectionReason.trim()}
                className="flex-1 bg-red-600 text-white rounded-md px-4 py-2 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {rejectMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ThumbsDown className="h-4 w-4" />
                )}
                반려
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Fall Detail Form Modal */}
      {showFallDetailForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full my-8 p-6 max-h-[90vh] overflow-y-auto">
            <FallDetailForm
              incidentId={incidentId}
              existingDetail={fallDetail}
              onClose={() => setShowFallDetailForm(false)}
              onSuccess={() => {
                setShowFallDetailForm(false)
                queryClient.invalidateQueries({ queryKey: ['fallDetail', incidentId] })
              }}
            />
          </div>
        </div>
      )}

      {/* Medication Detail Form Modal */}
      {showMedicationDetailForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full my-8 p-6 max-h-[90vh] overflow-y-auto">
            <MedicationDetailForm
              incidentId={incidentId}
              existingDetail={medicationDetail}
              onClose={() => setShowMedicationDetailForm(false)}
              onSuccess={() => {
                setShowMedicationDetailForm(false)
                queryClient.invalidateQueries({ queryKey: ['medicationDetail', incidentId] })
              }}
            />
          </div>
        </div>
      )}

      {showInfectionDetailForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full my-8 p-6 max-h-[90vh] overflow-y-auto">
            <InfectionDetailForm
              incidentId={incidentId}
              existingDetail={infectionDetail}
              onClose={() => setShowInfectionDetailForm(false)}
              onSuccess={() => {
                setShowInfectionDetailForm(false)
                queryClient.invalidateQueries({ queryKey: ['infectionDetail', incidentId] })
              }}
            />
          </div>
        </div>
      )}

      {/* Pressure Ulcer Detail Form Modal */}
      {showPressureUlcerDetailForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full my-8 p-6 max-h-[90vh] overflow-y-auto">
            <PressureUlcerDetailForm
              incidentId={incidentId}
              existingDetail={pressureUlcerDetail}
              onClose={() => setShowPressureUlcerDetailForm(false)}
              onSuccess={() => {
                setShowPressureUlcerDetailForm(false)
                queryClient.invalidateQueries({ queryKey: ['pressureUlcerDetail', incidentId] })
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
