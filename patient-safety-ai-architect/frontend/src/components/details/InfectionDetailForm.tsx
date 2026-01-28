import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Loader2, Bug } from 'lucide-react'
import { infectionDetailApi } from '@/utils/api'
import {
  INFECTION_TYPE_OPTIONS,
  INFECTION_SITE_OPTIONS,
  DEVICE_TYPE_LABELS,
  InfectionType,
  InfectionSite,
  DeviceType,
} from '@/types'

// Validation schema
const infectionDetailSchema = z.object({
  // 감염 유형 (필수)
  infection_type: z.enum([
    'uti_non_catheter', 'cauti', 'pneumonia', 'vap', 'clabsi', 'ssi', 'cdiff', 'mrsa', 'other'
  ]),
  infection_type_detail: z.string().optional(),
  // 감염 부위
  infection_site: z.enum(['urinary', 'respiratory', 'skin', 'bloodstream', 'surgical', 'gastrointestinal', 'other']).optional(),
  infection_site_detail: z.string().optional(),
  // 발생일/진단일
  onset_date: z.string().optional(),
  diagnosis_date: z.string().optional(),
  // 원인균
  pathogen: z.string().optional(),
  is_mdro: z.boolean(),
  pathogen_culture_result: z.string().optional(),
  // 기기 관련
  device_related: z.boolean(),
  device_type: z.enum(['urinary_catheter', 'central_line', 'ventilator', 'peripheral_iv', 'ng_tube', 'tracheostomy', 'other']).optional(),
  device_insertion_date: z.string().optional(),
  device_days: z.number().min(0).optional().nullable(),
  // 원내 감염
  is_hospital_acquired: z.boolean(),
  admission_date: z.string().optional(),
  // 부서
  department: z.string().min(1, '부서를 입력해주세요').max(100),
  // 치료 정보
  antibiotic_used: z.string().optional(),
  treatment_notes: z.string().optional(),
})

type InfectionDetailFormData = z.infer<typeof infectionDetailSchema>

interface Props {
  incidentId: number
  existingDetail?: {
    id: number
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
  } | null
  onClose: () => void
  onSuccess: () => void
}

const deviceTypeOptions = [
  { value: '', label: '선택하세요' },
  { value: 'urinary_catheter', label: '유치도뇨관' },
  { value: 'central_line', label: '중심정맥관' },
  { value: 'ventilator', label: '인공호흡기' },
  { value: 'peripheral_iv', label: '말초정맥관' },
  { value: 'ng_tube', label: '비위관' },
  { value: 'tracheostomy', label: '기관절개관' },
  { value: 'other', label: '기타' },
]

export default function InfectionDetailForm({ incidentId, existingDetail, onClose, onSuccess }: Props) {
  const queryClient = useQueryClient()
  const isEdit = !!existingDetail

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<InfectionDetailFormData>({
    resolver: zodResolver(infectionDetailSchema),
    defaultValues: existingDetail
      ? {
          infection_type: existingDetail.infection_type as InfectionType,
          infection_site: existingDetail.infection_site as InfectionSite | undefined,
          infection_site_detail: existingDetail.infection_site_detail || '',
          onset_date: existingDetail.onset_date || '',
          diagnosis_date: existingDetail.diagnosis_date || '',
          pathogen: existingDetail.pathogen || '',
          is_mdro: existingDetail.is_mdro,
          pathogen_culture_result: existingDetail.pathogen_culture_result || '',
          device_related: existingDetail.device_related,
          device_type: existingDetail.device_type as DeviceType | undefined,
          device_insertion_date: existingDetail.device_insertion_date || '',
          device_days: existingDetail.device_days ?? null,
          is_hospital_acquired: existingDetail.is_hospital_acquired,
          admission_date: existingDetail.admission_date || '',
          department: existingDetail.department,
          antibiotic_used: existingDetail.antibiotic_used || '',
          treatment_notes: existingDetail.treatment_notes || '',
        }
      : {
          is_mdro: false,
          device_related: false,
          is_hospital_acquired: true,
          department: '',
        },
  })

  const infectionType = watch('infection_type')
  const infectionSite = watch('infection_site')
  const deviceRelated = watch('device_related')

  const createMutation = useMutation({
    mutationFn: (data: InfectionDetailFormData) =>
      infectionDetailApi.create({
        incident_id: incidentId,
        patient_code: '', // 환자 정보는 Incident에서 관리
        ...data,
        device_days: data.device_days ?? undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['infectionDetail', incidentId] })
      alert('감염 상세 정보가 저장되었습니다.')
      onSuccess()
    },
    onError: () => {
      alert('저장에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: InfectionDetailFormData) =>
      infectionDetailApi.update(existingDetail!.id, {
        ...data,
        device_days: data.device_days ?? undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['infectionDetail', incidentId] })
      alert('감염 상세 정보가 수정되었습니다.')
      onSuccess()
    },
    onError: () => {
      alert('수정에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const onSubmit = (data: InfectionDetailFormData) => {
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
          <Bug className="h-5 w-5 text-red-600" />
          <h3 className="text-lg font-semibold">
            {isEdit ? '감염 상세 정보 수정' : '감염 상세 정보 입력'}
          </h3>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* 환자 정보 안내 */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            환자 정보는 사고 보고(공통 폼)에서 입력합니다. 감염 상세 정보만 아래에 입력해주세요.
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

        {/* 감염 유형 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">감염 유형</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">감염 유형 *</label>
              <select {...register('infection_type')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {INFECTION_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
              {errors.infection_type && (
                <p className="mt-1 text-sm text-red-600">{errors.infection_type.message}</p>
              )}
            </div>
            {infectionType === 'other' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">기타 감염 유형 상세</label>
                <input {...register('infection_type_detail')} className="input-field mt-1" placeholder="감염 유형 상세" />
              </div>
            )}
          </div>
        </div>

        {/* 감염 부위 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">감염 부위</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">감염 부위</label>
              <select {...register('infection_site')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {INFECTION_SITE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            {infectionSite === 'other' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">기타 감염 부위 상세</label>
                <input {...register('infection_site_detail')} className="input-field mt-1" placeholder="감염 부위 상세" />
              </div>
            )}
          </div>
        </div>

        {/* 발생일/진단일 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">발생 시점</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">발생일 (onset)</label>
              <input {...register('onset_date')} type="date" className="input-field mt-1" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">진단일</label>
              <input {...register('diagnosis_date')} type="date" className="input-field mt-1" />
            </div>
          </div>
        </div>

        {/* 원인균 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">원인균 정보</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">원인균</label>
              <input {...register('pathogen')} className="input-field mt-1" placeholder="예: E.coli, Klebsiella 등" />
            </div>
            <div className="flex items-center pt-6">
              <label className="flex items-center gap-2">
                <input {...register('is_mdro')} type="checkbox" className="rounded border-gray-300" />
                <span className="text-sm text-gray-700">다제내성균 (MDRO)</span>
              </label>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">배양 결과</label>
            <textarea
              {...register('pathogen_culture_result')}
              rows={2}
              className="input-field mt-1"
              placeholder="배양 검사 결과 상세"
            />
          </div>
        </div>

        {/* 기기 관련 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">의료기기 관련</h4>
          <div className="space-y-4">
            <label className="flex items-center gap-2">
              <input {...register('device_related')} type="checkbox" className="rounded border-gray-300" />
              <span className="text-sm text-gray-700">의료기기 관련 감염</span>
            </label>
            {deviceRelated && (
              <div className="grid grid-cols-3 gap-4 pt-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700">기기 유형</label>
                  <select {...register('device_type')} className="input-field mt-1">
                    {deviceTypeOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">삽입일</label>
                  <input {...register('device_insertion_date')} type="date" className="input-field mt-1" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">유치 일수</label>
                  <input
                    {...register('device_days', { valueAsNumber: true })}
                    type="number"
                    min={0}
                    className="input-field mt-1"
                    placeholder="0"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 원내 감염 여부 */}
        <div className="border rounded-lg p-4 space-y-4 bg-yellow-50">
          <h4 className="font-medium text-gray-900">원내 감염 여부</h4>
          <div className="space-y-4">
            <label className="flex items-center gap-2">
              <input {...register('is_hospital_acquired')} type="checkbox" className="rounded border-gray-300" />
              <span className="text-sm text-gray-700">원내 감염 (입원 48시간 이후 발생)</span>
            </label>
            <div>
              <label className="block text-sm font-medium text-gray-700">입원일</label>
              <input {...register('admission_date')} type="date" className="input-field mt-1 max-w-xs" />
            </div>
          </div>
        </div>

        {/* 치료 정보 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">치료 정보</h4>
          <div>
            <label className="block text-sm font-medium text-gray-700">사용 항생제</label>
            <input
              {...register('antibiotic_used')}
              className="input-field mt-1"
              placeholder="예: Ceftriaxone, Vancomycin 등"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">치료 내용</label>
            <textarea
              {...register('treatment_notes')}
              rows={3}
              className="input-field mt-1"
              placeholder="치료 경과 및 내용을 기술"
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
