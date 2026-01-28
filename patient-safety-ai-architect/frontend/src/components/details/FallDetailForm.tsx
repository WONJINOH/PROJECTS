import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Loader2, Activity } from 'lucide-react'
import { fallDetailApi } from '@/utils/api'
import {
  FALL_INJURY_LABELS,
  FALL_LOCATION_LABELS,
  FALL_CAUSE_LABELS,
  FALL_RELATED_MEDICATION_OPTIONS,
  FALL_IMMEDIATE_MEDICATION_OPTIONS,
  FallInjuryLevel,
  FallLocation,
  FallCause,
  FallRiskLevel,
} from '@/types'

// Validation schema (환자 정보는 Incident 공통 폼에서 입력)
const fallDetailSchema = z.object({
  // 낙상 위험도
  pre_fall_risk_level: z.enum(['low', 'moderate', 'high']).optional(),
  morse_score: z.number().min(0).max(125).optional().nullable(),
  // 관련 투약
  related_medications: z.array(z.string()).optional(),
  immediate_risk_medications: z.array(z.string()).optional(),
  immediate_risk_medications_detail: z.string().optional(),
  // 낙상 상황
  fall_location: z.enum(['bed', 'bathroom', 'hallway', 'wheelchair', 'chair', 'rehabilitation', 'other']),
  fall_location_detail: z.string().optional(),
  fall_cause: z.enum(['slip', 'trip', 'loss_of_balance', 'fainting', 'weakness', 'cognitive', 'medication', 'environment', 'other']),
  fall_cause_detail: z.string().optional(),
  occurred_hour: z.number().min(0).max(23).optional().nullable(),
  shift: z.enum(['day', 'evening', 'night']).optional(),
  // 손상
  injury_level: z.enum(['none', 'minor', 'moderate', 'major', 'death']),
  injury_description: z.string().optional(),
  activity_at_fall: z.string().optional(),
  // 예방조치
  was_supervised: z.boolean(),
  had_fall_prevention: z.boolean(),
  department: z.string().min(1, '부서를 입력해주세요').max(100),
  is_recurrence: z.boolean(),
  previous_fall_count: z.number().min(0).optional(),
}).refine((data) => {
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
    // 환자 정보는 Incident에서 관리 (공통 폼)
    pre_fall_risk_level?: string
    morse_score?: number
    related_medications?: string[]
    immediate_risk_medications?: string[]
    immediate_risk_medications_detail?: string
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
    control,
    setValue,
    formState: { errors },
  } = useForm<FallDetailFormData>({
    resolver: zodResolver(fallDetailSchema),
    defaultValues: existingDetail
      ? {
          pre_fall_risk_level: existingDetail.pre_fall_risk_level as FallRiskLevel | undefined,
          morse_score: existingDetail.morse_score ?? null,
          related_medications: existingDetail.related_medications || [],
          immediate_risk_medications: existingDetail.immediate_risk_medications || [],
          immediate_risk_medications_detail: existingDetail.immediate_risk_medications_detail || '',
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
          related_medications: [],
          immediate_risk_medications: [],
        },
  })

  const injuryLevel = watch('injury_level')
  const isRecurrence = watch('is_recurrence')
  const selectedImmediateMeds = watch('immediate_risk_medications') || []

  const createMutation = useMutation({
    mutationFn: (data: FallDetailFormData) =>
      fallDetailApi.create({
        incident_id: incidentId,
        patient_code: '', // Placeholder - 환자 정보는 Incident에서 관리
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

  // Checkbox change handlers
  const handleRelatedMedicationChange = (value: string, checked: boolean) => {
    const current = watch('related_medications') || []
    if (checked) {
      setValue('related_medications', [...current, value])
    } else {
      setValue('related_medications', current.filter(v => v !== value))
    }
  }

  const handleImmediateMedicationChange = (value: string, checked: boolean) => {
    const current = watch('immediate_risk_medications') || []
    if (checked) {
      setValue('immediate_risk_medications', [...current, value])
    } else {
      setValue('immediate_risk_medications', current.filter(v => v !== value))
    }
  }

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
        {/* 환자 정보 안내 */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            환자 정보는 사고 보고(공통 폼)에서 입력합니다. 낙상 상세 정보만 아래에 입력해주세요.
          </p>
        </div>

        {/* 부서 입력 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">발생 부서</h4>
          <div>
            <label className="block text-sm font-medium text-gray-700">부서 *</label>
            <input {...register('department')} className="input-field mt-1" placeholder="발생 부서" />
            {errors.department && (
              <p className="mt-1 text-sm text-red-600">{errors.department.message}</p>
            )}
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

        {/* Related Medications - 24시간 이내 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">24시간 이내 투여된 낙상유발약물</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {FALL_RELATED_MEDICATION_OPTIONS.map((option) => (
              <Controller
                key={option.value}
                name="related_medications"
                control={control}
                render={({ field }) => (
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                      checked={field.value?.includes(option.value) || false}
                      onChange={(e) => handleRelatedMedicationChange(option.value, e.target.checked)}
                    />
                    <span className="text-sm text-gray-700">{option.label}</span>
                  </label>
                )}
              />
            ))}
          </div>
        </div>

        {/* Immediate Risk Medications - 1-2시간 이내 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">1-2시간 이내 투여된 낙상위험약물</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {FALL_IMMEDIATE_MEDICATION_OPTIONS.map((option) => (
              <Controller
                key={option.value}
                name="immediate_risk_medications"
                control={control}
                render={({ field }) => (
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                      checked={field.value?.includes(option.value) || false}
                      onChange={(e) => handleImmediateMedicationChange(option.value, e.target.checked)}
                    />
                    <span className="text-sm text-gray-700">{option.label}</span>
                  </label>
                )}
              />
            ))}
          </div>
          {selectedImmediateMeds.includes('other') && (
            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700">기타 약물 상세</label>
              <input
                {...register('immediate_risk_medications_detail')}
                className="input-field mt-1"
                placeholder="기타 약물명 입력"
              />
            </div>
          )}
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
