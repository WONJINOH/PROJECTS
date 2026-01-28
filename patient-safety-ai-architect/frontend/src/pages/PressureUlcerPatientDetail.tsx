import { useState, useMemo } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  ArrowLeft,
  HeartPulse,
  Plus,
  X,
  Activity,
  TrendingUp,
  TrendingDown,
  Calendar,
  AlertCircle,
  CheckCircle,
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { pressureUlcerManagementApi } from '@/utils/api'

// Types
interface PushAssessment {
  id: number
  assessment_date: string
  grade: string
  grade_label: string
  previous_grade?: string
  push_length_width?: number
  push_exudate?: number
  push_tissue_type?: number
  push_total?: number
  length_cm?: number
  width_cm?: number
  depth_cm?: number
  is_improved?: boolean
  is_worsened?: boolean
  note?: string
  created_at: string
}

interface PatientDetail {
  id: number
  incident_id?: number
  patient_code: string
  patient_name?: string
  patient_gender?: string
  room_number?: string
  patient_age_group?: string
  admission_date?: string
  department: string
  ulcer_id: string
  location: string
  location_detail?: string
  origin: string
  discovery_date: string
  grade?: string
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
  is_active: boolean
  is_healed: boolean
  healed_date?: string
  end_date?: string
  end_reason?: string
  end_reason_detail?: string
  created_at: string
  updated_at: string
  assessments: PushAssessment[]
}

interface TrendDataPoint {
  date: string
  push_total?: number
  grade?: string
  grade_value?: number
}

// Labels
const LOCATION_LABELS: Record<string, string> = {
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

const ORIGIN_LABELS: Record<string, string> = {
  admission: '입원 시 보유',
  acquired: '재원 중 발생',
  unknown: '불명',
}

const GRADE_LABELS: Record<string, string> = {
  stage_1: '1단계',
  stage_2: '2단계',
  stage_3: '3단계',
  stage_4: '4단계',
  unstageable: '미분류',
  dtpi: '심부조직손상',
}

const END_REASON_LABELS: Record<string, string> = {
  healed: '치유',
  death: '사망',
  discharge: '퇴원',
  transfer: '전원',
  other: '기타',
}

// Form schemas
const assessmentSchema = z.object({
  assessment_date: z.string().min(1, '평가일을 입력하세요'),
  grade: z.string().min(1, '등급을 선택하세요'),
  push_length_width: z.number().min(0).max(10),
  push_exudate: z.number().min(0).max(3),
  push_tissue_type: z.number().min(0).max(4),
  length_cm: z.number().optional(),
  width_cm: z.number().optional(),
  depth_cm: z.number().optional(),
  note: z.string().optional(),
})

const closeSchema = z.object({
  end_date: z.string().min(1, '종료일을 입력하세요'),
  end_reason: z.string().min(1, '종료 사유를 선택하세요'),
  end_reason_detail: z.string().optional(),
})

type AssessmentFormData = z.infer<typeof assessmentSchema>
type CloseFormData = z.infer<typeof closeSchema>

// Assessment Modal Component
function AssessmentModal({
  recordId,
  onClose,
}: {
  recordId: number
  onClose: () => void
}) {
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<AssessmentFormData>({
    resolver: zodResolver(assessmentSchema),
    defaultValues: {
      assessment_date: new Date().toISOString().split('T')[0],
      grade: '',
      push_length_width: 0,
      push_exudate: 0,
      push_tissue_type: 0,
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: AssessmentFormData) =>
      pressureUlcerManagementApi.createAssessment(recordId, {
        assessment_date: data.assessment_date,
        grade: data.grade,
        push_length_width: data.push_length_width,
        push_exudate: data.push_exudate,
        push_tissue_type: data.push_tissue_type,
        length_cm: data.length_cm,
        width_cm: data.width_cm,
        depth_cm: data.depth_cm,
        note: data.note,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pressureUlcerPatient', recordId] })
      queryClient.invalidateQueries({ queryKey: ['pressureUlcerTrend', recordId] })
      onClose()
      alert('평가가 기록되었습니다.')
    },
    onError: () => {
      alert('평가 기록에 실패했습니다.')
    },
  })

  const pushLengthWidth = watch('push_length_width')
  const pushExudate = watch('push_exudate')
  const pushTissueType = watch('push_tissue_type')
  const pushTotal = (pushLengthWidth || 0) + (pushExudate || 0) + (pushTissueType || 0)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b sticky top-0 bg-white">
          <h3 className="text-lg font-semibold">PUSH 평가 추가</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit((data) => createMutation.mutate(data))} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">평가일 *</label>
              <input
                type="date"
                {...register('assessment_date')}
                className="input-field mt-1"
              />
              {errors.assessment_date && (
                <p className="text-sm text-red-600 mt-1">{errors.assessment_date.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">등급 *</label>
              <select {...register('grade')} className="input-field mt-1">
                <option value="">선택</option>
                {Object.entries(GRADE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
              {errors.grade && (
                <p className="text-sm text-red-600 mt-1">{errors.grade.message}</p>
              )}
            </div>
          </div>

          <div className="bg-rose-50 rounded-lg p-4">
            <h4 className="font-medium text-rose-900 mb-3">PUSH Score</h4>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Length×Width (0-10)
                </label>
                <input
                  type="number"
                  min={0}
                  max={10}
                  {...register('push_length_width', { valueAsNumber: true })}
                  className="input-field mt-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  삼출물 (0-3)
                </label>
                <input
                  type="number"
                  min={0}
                  max={3}
                  {...register('push_exudate', { valueAsNumber: true })}
                  className="input-field mt-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  조직유형 (0-4)
                </label>
                <input
                  type="number"
                  min={0}
                  max={4}
                  {...register('push_tissue_type', { valueAsNumber: true })}
                  className="input-field mt-1"
                />
              </div>
            </div>
            <div className="mt-3 text-center">
              <span className="text-sm text-gray-600">총점: </span>
              <span className="text-xl font-bold text-rose-700">{pushTotal}</span>
              <span className="text-sm text-gray-600"> / 17</span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">길이 (cm)</label>
              <input
                type="number"
                step="0.1"
                {...register('length_cm', { valueAsNumber: true })}
                className="input-field mt-1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">너비 (cm)</label>
              <input
                type="number"
                step="0.1"
                {...register('width_cm', { valueAsNumber: true })}
                className="input-field mt-1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">깊이 (cm)</label>
              <input
                type="number"
                step="0.1"
                {...register('depth_cm', { valueAsNumber: true })}
                className="input-field mt-1"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">메모</label>
            <textarea
              {...register('note')}
              rows={2}
              className="input-field mt-1"
              placeholder="평가 관련 메모..."
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary">
              취소
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="btn-primary"
            >
              {createMutation.isPending ? '저장 중...' : '저장'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Close Modal Component
function CloseModal({
  recordId,
  onClose,
}: {
  recordId: number
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<CloseFormData>({
    resolver: zodResolver(closeSchema),
    defaultValues: {
      end_date: new Date().toISOString().split('T')[0],
      end_reason: '',
    },
  })

  const closeMutation = useMutation({
    mutationFn: (data: CloseFormData) =>
      pressureUlcerManagementApi.closeUlcer(recordId, {
        end_date: data.end_date,
        end_reason: data.end_reason,
        end_reason_detail: data.end_reason_detail,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pressureUlcerPatient', recordId] })
      queryClient.invalidateQueries({ queryKey: ['pressureUlcerPatients'] })
      onClose()
      alert('욕창 기록이 종료되었습니다.')
      navigate('/pressure-ulcer-management')
    },
    onError: () => {
      alert('종료 처리에 실패했습니다.')
    },
  })

  const endReason = watch('end_reason')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">욕창 기록 종료</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit((data) => closeMutation.mutate(data))} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">종료일 *</label>
            <input
              type="date"
              {...register('end_date')}
              className="input-field mt-1"
            />
            {errors.end_date && (
              <p className="text-sm text-red-600 mt-1">{errors.end_date.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">종료 사유 *</label>
            <select {...register('end_reason')} className="input-field mt-1">
              <option value="">선택</option>
              {Object.entries(END_REASON_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
            {errors.end_reason && (
              <p className="text-sm text-red-600 mt-1">{errors.end_reason.message}</p>
            )}
          </div>

          {endReason === 'other' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">사유 상세</label>
              <input
                type="text"
                {...register('end_reason_detail')}
                className="input-field mt-1"
                placeholder="기타 사유를 입력하세요"
              />
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary">
              취소
            </button>
            <button
              type="submit"
              disabled={closeMutation.isPending}
              className="btn-primary bg-red-600 hover:bg-red-700"
            >
              {closeMutation.isPending ? '처리 중...' : '종료'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function PressureUlcerPatientDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const recordId = Number(id)

  const [showAssessmentModal, setShowAssessmentModal] = useState(false)
  const [showCloseModal, setShowCloseModal] = useState(false)

  // Fetch patient detail
  const { data: patientData, isLoading } = useQuery({
    queryKey: ['pressureUlcerPatient', recordId],
    queryFn: () => pressureUlcerManagementApi.getPatient(recordId),
  })

  // Fetch trend data
  const { data: trendData } = useQuery({
    queryKey: ['pressureUlcerTrend', recordId],
    queryFn: () => pressureUlcerManagementApi.getTrend(recordId),
  })

  const patient: PatientDetail | null = useMemo(() => {
    if (!patientData?.data) return null
    return patientData.data
  }, [patientData])

  const trendPoints: TrendDataPoint[] = useMemo(() => {
    if (!trendData?.data?.data_points) return []
    return trendData.data.data_points
  }, [trendData])

  const chartData = useMemo(() => {
    return trendPoints.map((p) => ({
      date: new Date(p.date).toLocaleDateString('ko-KR', {
        month: '2-digit',
        day: '2-digit',
      }),
      push: p.push_total,
      grade: p.grade_value,
    }))
  }, [trendPoints])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-600"></div>
      </div>
    )
  }

  if (!patient) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">환자 정보를 찾을 수 없습니다.</p>
        <Link to="/pressure-ulcer-management" className="text-rose-600 hover:underline mt-2 inline-block">
          목록으로 돌아가기
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button
            onClick={() => navigate('/pressure-ulcer-management')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            목록
          </button>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <HeartPulse className="h-6 w-6 text-rose-600" />
            {patient.patient_code}
          </h1>
          {patient.patient_name && (
            <p className="text-gray-500 mt-1">{patient.patient_name}</p>
          )}
          <div className="flex items-center gap-3 mt-2">
            <span className={`badge ${patient.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
              {patient.is_active
                ? '활성'
                : END_REASON_LABELS[patient.end_reason || ''] || '종료'}
            </span>
            <span className="text-sm text-gray-500">
              {LOCATION_LABELS[patient.location] || patient.location}
            </span>
          </div>
        </div>
        {patient.is_active && (
          <div className="flex gap-2">
            <button
              onClick={() => setShowAssessmentModal(true)}
              className="btn-primary flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              평가 추가
            </button>
            <button
              onClick={() => setShowCloseModal(true)}
              className="btn-secondary text-red-600 border-red-300 hover:bg-red-50"
            >
              종료
            </button>
          </div>
        )}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="text-sm text-gray-500 mb-1">현재 등급</div>
          <div className="text-xl font-bold text-rose-600">
            {GRADE_LABELS[patient.grade || ''] || '-'}
          </div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-500 mb-1">PUSH 점수</div>
          <div className="text-xl font-bold text-gray-900">
            {patient.assessments[0]?.push_total ?? patient.push_total ?? '-'}
            <span className="text-sm font-normal text-gray-500"> / 17</span>
          </div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-500 mb-1">발견일</div>
          <div className="text-xl font-bold text-gray-900">
            {formatDate(patient.discovery_date)}
          </div>
        </div>
        <div className="card">
          <div className="text-sm text-gray-500 mb-1">발생시점</div>
          <div className="text-xl font-bold text-gray-900">
            {ORIGIN_LABELS[patient.origin] || patient.origin}
          </div>
        </div>
      </div>

      {/* Trend Chart */}
      {chartData.length > 1 && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">PUSH 점수 추이</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 17]} />
                <Tooltip />
                <ReferenceLine y={0} stroke="#10b981" strokeDasharray="3 3" label="치유" />
                <Line
                  type="monotone"
                  dataKey="push"
                  stroke="#e11d48"
                  strokeWidth={2}
                  dot={{ fill: '#e11d48', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Patient Info */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">환자 정보</h3>
        <dl className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <dt className="text-sm text-gray-500">병실</dt>
            <dd className="mt-1 text-gray-900">{patient.room_number || '-'}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">부서</dt>
            <dd className="mt-1 text-gray-900">{patient.department}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">연령대</dt>
            <dd className="mt-1 text-gray-900">{patient.patient_age_group || '-'}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">성별</dt>
            <dd className="mt-1 text-gray-900">{patient.patient_gender || '-'}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">입원일</dt>
            <dd className="mt-1 text-gray-900">
              {patient.admission_date ? formatDate(patient.admission_date) : '-'}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">욕창 ID</dt>
            <dd className="mt-1 text-gray-900 font-mono">{patient.ulcer_id}</dd>
          </div>
        </dl>
        {patient.risk_factors && (
          <div className="mt-4">
            <dt className="text-sm text-gray-500">위험 요인</dt>
            <dd className="mt-1 text-gray-900">{patient.risk_factors}</dd>
          </div>
        )}
        {patient.treatment_plan && (
          <div className="mt-4">
            <dt className="text-sm text-gray-500">치료 계획</dt>
            <dd className="mt-1 text-gray-900">{patient.treatment_plan}</dd>
          </div>
        )}
      </div>

      {/* Assessment History */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">평가 기록</h3>
        {patient.assessments.length > 0 ? (
          <div className="space-y-4">
            {patient.assessments.map((assessment) => (
              <div
                key={assessment.id}
                className="border rounded-lg p-4 bg-gray-50"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Calendar className="h-5 w-5 text-gray-400" />
                    <span className="font-medium">
                      {formatDate(assessment.assessment_date)}
                    </span>
                    <span className="badge bg-rose-100 text-rose-800">
                      {assessment.grade_label}
                    </span>
                    {assessment.is_improved && (
                      <span className="flex items-center gap-1 text-green-600 text-sm">
                        <TrendingDown className="h-4 w-4" />
                        호전
                      </span>
                    )}
                    {assessment.is_worsened && (
                      <span className="flex items-center gap-1 text-red-600 text-sm">
                        <TrendingUp className="h-4 w-4" />
                        악화
                      </span>
                    )}
                  </div>
                  <span className="text-lg font-bold text-rose-600">
                    PUSH {assessment.push_total}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">L×W: </span>
                    <span className="font-medium">{assessment.push_length_width}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">삼출물: </span>
                    <span className="font-medium">{assessment.push_exudate}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">조직유형: </span>
                    <span className="font-medium">{assessment.push_tissue_type}</span>
                  </div>
                </div>
                {(assessment.length_cm || assessment.width_cm || assessment.depth_cm) && (
                  <div className="mt-2 text-sm text-gray-600">
                    크기: {assessment.length_cm || '-'}×{assessment.width_cm || '-'}×
                    {assessment.depth_cm || '-'} cm
                  </div>
                )}
                {assessment.note && (
                  <div className="mt-2 text-sm text-gray-600">{assessment.note}</div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            평가 기록이 없습니다.
          </div>
        )}
      </div>

      {/* Modals */}
      {showAssessmentModal && (
        <AssessmentModal
          recordId={recordId}
          onClose={() => setShowAssessmentModal(false)}
        />
      )}
      {showCloseModal && (
        <CloseModal
          recordId={recordId}
          onClose={() => setShowCloseModal(false)}
        />
      )}
    </div>
  )
}
