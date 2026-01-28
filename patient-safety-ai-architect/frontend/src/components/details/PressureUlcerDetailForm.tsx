import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Loader2, CircleDot } from 'lucide-react'
import { pressureUlcerDetailApi } from '@/utils/api'
import {
  PRESSURE_ULCER_GRADE_OPTIONS,
  PRESSURE_ULCER_LOCATION_OPTIONS,
  PRESSURE_ULCER_ORIGIN_OPTIONS,
  PressureUlcerGrade,
  PressureUlcerLocation,
  PressureUlcerOrigin,
} from '@/types'

// Validation schema
const pressureUlcerDetailSchema = z.object({
  // 욕창 ID (자동 생성 가능)
  ulcer_id: z.string().min(1, '욕창 ID를 입력해주세요').max(50),
  // 발생 부위
  location: z.enum(['sacrum', 'heel', 'ischium', 'trochanter', 'elbow', 'occiput', 'scapula', 'ear', 'other']),
  location_detail: z.string().optional(),
  // 발생 시점
  origin: z.enum(['admission', 'acquired', 'unknown']),
  discovery_date: z.string().min(1, '발견일을 입력해주세요'),
  // 등급
  grade: z.enum(['stage_1', 'stage_2', 'stage_3', 'stage_4', 'unstageable', 'dtpi']),
  // PUSH Score
  push_length_width: z.number().min(0).max(10).optional().nullable(),
  push_exudate: z.number().min(0).max(3).optional().nullable(),
  push_tissue_type: z.number().min(0).max(4).optional().nullable(),
  // 크기
  length_cm: z.number().min(0).optional().nullable(),
  width_cm: z.number().min(0).optional().nullable(),
  depth_cm: z.number().min(0).optional().nullable(),
  // 부서
  department: z.string().min(1, '부서를 입력해주세요').max(100),
  // 추가 정보
  risk_factors: z.string().optional(),
  treatment_plan: z.string().optional(),
  note: z.string().optional(),
})

type PressureUlcerDetailFormData = z.infer<typeof pressureUlcerDetailSchema>

interface Props {
  incidentId: number
  existingDetail?: {
    id: number
    ulcer_id: string
    location: string
    location_detail?: string
    origin: string
    discovery_date: string
    grade: string
    push_length_width?: number
    push_exudate?: number
    push_tissue_type?: number
    push_total?: number
    length_cm?: number
    width_cm?: number
    depth_cm?: number
    department: string
    risk_factors?: string
    treatment_plan?: string
    note?: string
  } | null
  onClose: () => void
  onSuccess: () => void
}

// PUSH 점수 계산 함수
function calculatePushTotal(lengthWidth?: number | null, exudate?: number | null, tissueType?: number | null): number | null {
  if (lengthWidth != null && exudate != null && tissueType != null) {
    return lengthWidth + exudate + tissueType
  }
  return null
}

export default function PressureUlcerDetailForm({ incidentId, existingDetail, onClose, onSuccess }: Props) {
  const queryClient = useQueryClient()
  const isEdit = !!existingDetail

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<PressureUlcerDetailFormData>({
    resolver: zodResolver(pressureUlcerDetailSchema),
    defaultValues: existingDetail
      ? {
          ulcer_id: existingDetail.ulcer_id,
          location: existingDetail.location as PressureUlcerLocation,
          location_detail: existingDetail.location_detail || '',
          origin: existingDetail.origin as PressureUlcerOrigin,
          discovery_date: existingDetail.discovery_date,
          grade: existingDetail.grade as PressureUlcerGrade,
          push_length_width: existingDetail.push_length_width ?? null,
          push_exudate: existingDetail.push_exudate ?? null,
          push_tissue_type: existingDetail.push_tissue_type ?? null,
          length_cm: existingDetail.length_cm ?? null,
          width_cm: existingDetail.width_cm ?? null,
          depth_cm: existingDetail.depth_cm ?? null,
          department: existingDetail.department,
          risk_factors: existingDetail.risk_factors || '',
          treatment_plan: existingDetail.treatment_plan || '',
          note: existingDetail.note || '',
        }
      : {
          ulcer_id: `PU-${Date.now().toString(36).toUpperCase()}`,
          origin: 'acquired' as PressureUlcerOrigin,
          discovery_date: new Date().toISOString().split('T')[0],
          department: '',
        },
  })

  const location = watch('location')
  const pushLengthWidth = watch('push_length_width')
  const pushExudate = watch('push_exudate')
  const pushTissueType = watch('push_tissue_type')
  const pushTotal = calculatePushTotal(pushLengthWidth, pushExudate, pushTissueType)

  const createMutation = useMutation({
    mutationFn: (data: PressureUlcerDetailFormData) =>
      pressureUlcerDetailApi.create({
        incident_id: incidentId,
        patient_code: '', // 환자 정보는 Incident에서 관리
        ...data,
        push_length_width: data.push_length_width ?? undefined,
        push_exudate: data.push_exudate ?? undefined,
        push_tissue_type: data.push_tissue_type ?? undefined,
        length_cm: data.length_cm ?? undefined,
        width_cm: data.width_cm ?? undefined,
        depth_cm: data.depth_cm ?? undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pressureUlcerDetail', incidentId] })
      alert('욕창 상세 정보가 저장되었습니다.')
      onSuccess()
    },
    onError: () => {
      alert('저장에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: PressureUlcerDetailFormData) =>
      pressureUlcerDetailApi.update(existingDetail!.id, {
        ...data,
        push_length_width: data.push_length_width ?? undefined,
        push_exudate: data.push_exudate ?? undefined,
        push_tissue_type: data.push_tissue_type ?? undefined,
        length_cm: data.length_cm ?? undefined,
        width_cm: data.width_cm ?? undefined,
        depth_cm: data.depth_cm ?? undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pressureUlcerDetail', incidentId] })
      alert('욕창 상세 정보가 수정되었습니다.')
      onSuccess()
    },
    onError: () => {
      alert('수정에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const onSubmit = (data: PressureUlcerDetailFormData) => {
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
          <CircleDot className="h-5 w-5 text-pink-600" />
          <h3 className="text-lg font-semibold">
            {isEdit ? '욕창 상세 정보 수정' : '욕창 상세 정보 입력'}
          </h3>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* 환자 정보 안내 */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            환자 정보는 사고 보고(공통 폼)에서 입력합니다. 욕창 상세 정보만 아래에 입력해주세요.
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

        {/* 욕창 기본 정보 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">욕창 기본 정보</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">욕창 ID *</label>
              <input {...register('ulcer_id')} className="input-field mt-1" placeholder="PU-XXXXX" />
              {errors.ulcer_id && (
                <p className="mt-1 text-sm text-red-600">{errors.ulcer_id.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">발견일 *</label>
              <input {...register('discovery_date')} type="date" className="input-field mt-1" />
              {errors.discovery_date && (
                <p className="mt-1 text-sm text-red-600">{errors.discovery_date.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">발생 시점 *</label>
              <select {...register('origin')} className="input-field mt-1">
                {PRESSURE_ULCER_ORIGIN_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">등급 *</label>
              <select {...register('grade')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {PRESSURE_ULCER_GRADE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              {errors.grade && (
                <p className="mt-1 text-sm text-red-600">{errors.grade.message}</p>
              )}
            </div>
          </div>
        </div>

        {/* 발생 부위 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">발생 부위</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">부위 *</label>
              <select {...register('location')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {PRESSURE_ULCER_LOCATION_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              {errors.location && (
                <p className="mt-1 text-sm text-red-600">{errors.location.message}</p>
              )}
            </div>
            {location === 'other' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">기타 부위 상세</label>
                <input {...register('location_detail')} className="input-field mt-1" placeholder="부위 상세" />
              </div>
            )}
          </div>
        </div>

        {/* 크기 측정 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">크기 측정 (cm)</h4>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">길이</label>
              <input
                {...register('length_cm', { valueAsNumber: true })}
                type="number"
                step="0.1"
                min="0"
                className="input-field mt-1"
                placeholder="0.0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">너비</label>
              <input
                {...register('width_cm', { valueAsNumber: true })}
                type="number"
                step="0.1"
                min="0"
                className="input-field mt-1"
                placeholder="0.0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">깊이</label>
              <input
                {...register('depth_cm', { valueAsNumber: true })}
                type="number"
                step="0.1"
                min="0"
                className="input-field mt-1"
                placeholder="0.0"
              />
            </div>
          </div>
        </div>

        {/* PUSH Score */}
        <div className="border rounded-lg p-4 space-y-4 bg-pink-50">
          <h4 className="font-medium text-gray-900">PUSH Score (Pressure Ulcer Scale for Healing)</h4>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">길이 x 너비 (0-10)</label>
              <input
                {...register('push_length_width', { valueAsNumber: true })}
                type="number"
                min="0"
                max="10"
                className="input-field mt-1"
                placeholder="0"
              />
              <p className="mt-1 text-xs text-gray-500">0: 0cm², 10: &gt;24cm²</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">삼출물 (0-3)</label>
              <input
                {...register('push_exudate', { valueAsNumber: true })}
                type="number"
                min="0"
                max="3"
                className="input-field mt-1"
                placeholder="0"
              />
              <p className="mt-1 text-xs text-gray-500">0: 없음, 3: 다량</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">조직 유형 (0-4)</label>
              <input
                {...register('push_tissue_type', { valueAsNumber: true })}
                type="number"
                min="0"
                max="4"
                className="input-field mt-1"
                placeholder="0"
              />
              <p className="mt-1 text-xs text-gray-500">0: 상피화, 4: 괴사</p>
            </div>
          </div>
          {pushTotal !== null && (
            <div className="mt-3 p-3 bg-white rounded border">
              <span className="text-sm font-medium text-gray-700">PUSH 총점: </span>
              <span className={`text-lg font-bold ${pushTotal <= 5 ? 'text-green-600' : pushTotal <= 10 ? 'text-yellow-600' : 'text-red-600'}`}>
                {pushTotal} / 17
              </span>
            </div>
          )}
        </div>

        {/* 추가 정보 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">추가 정보</h4>
          <div>
            <label className="block text-sm font-medium text-gray-700">위험 요인</label>
            <textarea
              {...register('risk_factors')}
              rows={2}
              className="input-field mt-1"
              placeholder="부동, 영양불량, 실금 등"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">치료 계획</label>
            <textarea
              {...register('treatment_plan')}
              rows={2}
              className="input-field mt-1"
              placeholder="드레싱, 체위변경, 영양지원 등"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">비고</label>
            <textarea
              {...register('note')}
              rows={2}
              className="input-field mt-1"
              placeholder="기타 참고사항"
            />
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
