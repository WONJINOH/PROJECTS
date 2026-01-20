import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Loader2, Activity } from 'lucide-react'
import { fallDetailApi } from '@/utils/api'
import {
  FALL_INJURY_LABELS,
  FALL_LOCATION_LABELS,
  FALL_CAUSE_LABELS,
  FallInjuryLevel,
  FallLocation,
  FallCause,
  FallRiskLevel,
} from '@/types'

// Validation schema
const fallDetailSchema = z.object({
  patient_code: z.string().min(1, '환자 코드를 입력해주세요').max(50),
  patient_age_group: z.string().optional(),
  patient_gender: z.enum(['male', 'female', 'other']).optional(),
  pre_fall_risk_level: z.enum(['low', 'moderate', 'high']).optional(),
  morse_score: z.number().min(0).max(125).optional().nullable(),
  fall_location: z.enum(['bed', 'bathroom', 'hallway', 'wheelchair', 'chair', 'rehabilitation', 'other']),
  fall_location_detail: z.string().optional(),
  fall_cause: z.enum(['slip', 'trip', 'loss_of_balance', 'fainting', 'weakness', 'cognitive', 'medication', 'environment', 'other']),
  fall_cause_detail: z.string().optional(),
  occurred_hour: z.number().min(0).max(23).optional().nullable(),
  shift: z.enum(['day', 'evening', 'night']).optional(),
  injury_level: z.enum(['none', 'minor', 'moderate', 'major', 'death']),
  injury_description: z.string().optional(),
  activity_at_fall: z.string().optional(),
  was_supervised: z.boolean(),
  had_fall_prevention: z.boolean(),
  department: z.string().min(1, '부서를 입력해주세요').max(100),
  is_recurrence: z.boolean(),
  previous_fall_count: z.number().min(0).optional(),
}).refine((data) => {
  // injury_description required when injury_level is not 'none'
  if (data.injury_level !== 'none' && !data.injury_description) {
    return false
  }
  return true
}, {
  message: '손상이 있는 경우 손상 설명을 입력해주세요',
  path: ['injury_description'],
})

type FallDetailFormData = z.infer<typeof fallDetailSchema>

interface Props {
  incidentId: number
  existingDetail?: {
    id: number
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
  } | null
  onClose: () => void
  onSuccess: () => void
}

const ageGroups = [
  { value: '', label: '선택하세요' },
  { value: '0-17', label: '소아 (0-17세)' },
  { value: '18-64', label: '성인 (18-64세)' },
  { value: '65-74', label: '초기 노인 (65-74세)' },
  { value: '75-84', label: '중기 노인 (75-84세)' },
  { value: '85+', label: '후기 노인 (85세 이상)' },
]

const riskLevels = [
  { value: '', label: '선택하세요' },
  { value: 'low', label: '저위험' },
  { value: 'moderate', label: '중위험' },
  { value: 'high', label: '고위험' },
]

const shifts = [
  { value: '', label: '선택하세요' },
  { value: 'day', label: '주간 (Day)' },
  { value: 'evening', label: '저녁 (Evening)' },
  { value: 'night', label: '야간 (Night)' },
]

export default function FallDetailForm({ incidentId, existingDetail, onClose, onSuccess }: Props) {
  const queryClient = useQueryClient()
  const isEdit = !!existingDetail

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FallDetailFormData>({
    resolver: zodResolver(fallDetailSchema),
    defaultValues: existingDetail
      ? {
          patient_code: existingDetail.patient_code,
          patient_age_group: existingDetail.patient_age_group || '',
          patient_gender: existingDetail.patient_gender as 'male' | 'female' | 'other' | undefined,
          pre_fall_risk_level: existingDetail.pre_fall_risk_level as FallRiskLevel | undefined,
          morse_score: existingDetail.morse_score ?? null,
          fall_location: existingDetail.fall_location as FallLocation,
          fall_location_detail: existingDetail.fall_location_detail || '',
          fall_cause: existingDetail.fall_cause as FallCause,
          fall_cause_detail: existingDetail.fall_cause_detail || '',
          occurred_hour: existingDetail.occurred_hour ?? null,
          shift: existingDetail.shift as 'day' | 'evening' | 'night' | undefined,
          injury_level: existingDetail.injury_level as FallInjuryLevel,
          injury_description: existingDetail.injury_description || '',
          activity_at_fall: existingDetail.activity_at_fall || '',
          was_supervised: existingDetail.was_supervised,
          had_fall_prevention: existingDetail.had_fall_prevention,
          department: existingDetail.department,
          is_recurrence: existingDetail.is_recurrence,
          previous_fall_count: existingDetail.previous_fall_count,
        }
      : {
          was_supervised: false,
          had_fall_prevention: false,
          is_recurrence: false,
          previous_fall_count: 0,
          injury_level: 'none',
        },
  })

  const injuryLevel = watch('injury_level')
  const isRecurrence = watch('is_recurrence')

  const createMutation = useMutation({
    mutationFn: (data: FallDetailFormData) =>
      fallDetailApi.create({
        incident_id: incidentId,
        ...data,
        morse_score: data.morse_score ?? undefined,
        occurred_hour: data.occurred_hour ?? undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fallDetail', incidentId] })
      alert('낙상 상세 정보가 저장되었습니다.')
      onSuccess()
    },
    onError: () => {
      alert('저장에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: FallDetailFormData) =>
      fallDetailApi.update(existingDetail!.id, {
        ...data,
        morse_score: data.morse_score ?? undefined,
        occurred_hour: data.occurred_hour ?? undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fallDetail', incidentId] })
      alert('낙상 상세 정보가 수정되었습니다.')
      onSuccess()
    },
    onError: () => {
      alert('수정에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const onSubmit = (data: FallDetailFormData) => {
    if (isEdit) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={onClose} className="p-1 text-gray-500 hover:text-gray-700">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-orange-600" />
          <h3 className="text-lg font-semibold">
            {isEdit ? '낙상 상세 정보 수정' : '낙상 상세 정보 입력'}
          </h3>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Patient Info */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">환자 정보</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">환자 코드 *</label>
              <input {...register('patient_code')} className="input-field mt-1" placeholder="P-001" />
              {errors.patient_code && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_code.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">부서 *</label>
              <input {...register('department')} className="input-field mt-1" placeholder="내과 병동" />
              {errors.department && (
                <p className="mt-1 text-sm text-red-600">{errors.department.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">연령대</label>
              <select {...register('patient_age_group')} className="input-field mt-1">
                {ageGroups.map((g) => (
                  <option key={g.value} value={g.value}>{g.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">성별</label>
              <select {...register('patient_gender')} className="input-field mt-1">
                <option value="">선택하세요</option>
                <option value="male">남성</option>
                <option value="female">여성</option>
                <option value="other">기타</option>
              </select>
            </div>
          </div>
        </div>

        {/* Fall Risk Assessment */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">낙상 위험도 평가</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">낙상 전 위험도</label>
              <select {...register('pre_fall_risk_level')} className="input-field mt-1">
                {riskLevels.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Morse 점수 (0-125)</label>
              <input
                {...register('morse_score', { valueAsNumber: true })}
                type="number"
                min={0}
                max={125}
                className="input-field mt-1"
                placeholder="0"
              />
            </div>
          </div>
        </div>

        {/* Fall Details */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">낙상 상황</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">발생 장소 *</label>
              <select {...register('fall_location')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {(Object.keys(FALL_LOCATION_LABELS) as FallLocation[]).map((loc) => (
                  <option key={loc} value={loc}>{FALL_LOCATION_LABELS[loc]}</option>
                ))}
              </select>
              {errors.fall_location && (
                <p className="mt-1 text-sm text-red-600">{errors.fall_location.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">장소 상세</label>
              <input {...register('fall_location_detail')} className="input-field mt-1" placeholder="상세 위치" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">낙상 원인 *</label>
              <select {...register('fall_cause')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {(Object.keys(FALL_CAUSE_LABELS) as FallCause[]).map((cause) => (
                  <option key={cause} value={cause}>{FALL_CAUSE_LABELS[cause]}</option>
                ))}
              </select>
              {errors.fall_cause && (
                <p className="mt-1 text-sm text-red-600">{errors.fall_cause.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">원인 상세</label>
              <input {...register('fall_cause_detail')} className="input-field mt-1" placeholder="상세 원인" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">발생 시간 (0-23시)</label>
              <input
                {...register('occurred_hour', { valueAsNumber: true })}
                type="number"
                min={0}
                max={23}
                className="input-field mt-1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">근무 시간대</label>
              <select {...register('shift')} className="input-field mt-1">
                {shifts.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700">낙상 시 활동</label>
              <input {...register('activity_at_fall')} className="input-field mt-1" placeholder="예: 화장실 가는 중" />
            </div>
          </div>
        </div>

        {/* Injury */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">손상 정도</h4>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">손상 수준 *</label>
              <select {...register('injury_level')} className="input-field mt-1">
                {(Object.keys(FALL_INJURY_LABELS) as FallInjuryLevel[]).map((level) => (
                  <option key={level} value={level}>{FALL_INJURY_LABELS[level]}</option>
                ))}
              </select>
            </div>
            {injuryLevel !== 'none' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">손상 설명 *</label>
                <textarea
                  {...register('injury_description')}
                  rows={2}
                  className="input-field mt-1"
                  placeholder="손상 부위, 정도 등을 상세히 기술"
                />
                {errors.injury_description && (
                  <p className="mt-1 text-sm text-red-600">{errors.injury_description.message}</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Prevention & Supervision */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">예방 조치 및 감독</h4>
          <div className="space-y-3">
            <label className="flex items-center gap-2">
              <input {...register('was_supervised')} type="checkbox" className="rounded border-gray-300" />
              <span className="text-sm text-gray-700">낙상 당시 감독/관찰 하에 있었음</span>
            </label>
            <label className="flex items-center gap-2">
              <input {...register('had_fall_prevention')} type="checkbox" className="rounded border-gray-300" />
              <span className="text-sm text-gray-700">낙상 예방 조치가 시행되고 있었음</span>
            </label>
            <label className="flex items-center gap-2">
              <input {...register('is_recurrence')} type="checkbox" className="rounded border-gray-300" />
              <span className="text-sm text-gray-700">재발 (이전 낙상 이력 있음)</span>
            </label>
            {isRecurrence && (
              <div>
                <label className="block text-sm font-medium text-gray-700">이전 낙상 횟수</label>
                <input
                  {...register('previous_fall_count', { valueAsNumber: true })}
                  type="number"
                  min={0}
                  className="input-field mt-1 w-24"
                />
              </div>
            )}
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-3 pt-2">
          <button type="button" onClick={onClose} className="flex-1 btn-secondary">
            취소
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="flex-1 btn-primary flex items-center justify-center gap-2"
          >
            {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            {isEdit ? '수정' : '저장'}
          </button>
        </div>
      </form>
    </div>
  )
}
