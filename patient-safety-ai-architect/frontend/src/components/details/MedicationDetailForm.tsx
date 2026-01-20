import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Loader2, Pill } from 'lucide-react'
import { medicationDetailApi } from '@/utils/api'
import {
  MEDICATION_ERROR_TYPE_LABELS,
  MEDICATION_STAGE_LABELS,
  MEDICATION_SEVERITY_LABELS,
  HIGH_ALERT_LABELS,
  MedicationErrorType,
  MedicationErrorStage,
  MedicationErrorSeverity,
  HighAlertMedication,
} from '@/types'

// Validation schema
const medicationDetailSchema = z.object({
  patient_code: z.string().min(1, '환자 코드를 입력해주세요').max(50),
  patient_age_group: z.string().optional(),
  error_type: z.enum(['wrong_patient', 'wrong_drug', 'wrong_dose', 'wrong_route', 'wrong_time', 'wrong_rate', 'omission', 'unauthorized', 'deteriorated', 'monitoring', 'other']),
  error_stage: z.enum(['prescribing', 'transcribing', 'dispensing', 'administering', 'monitoring']),
  error_severity: z.enum(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']),
  is_near_miss: z.boolean(),
  medication_category: z.string().optional(),
  is_high_alert: z.boolean(),
  high_alert_type: z.enum(['anticoagulant', 'insulin', 'opioid', 'chemotherapy', 'sedative', 'potassium', 'neuromuscular', 'other']).optional().nullable(),
  intended_dose: z.string().optional(),
  actual_dose: z.string().optional(),
  intended_route: z.string().optional(),
  actual_route: z.string().optional(),
  discovered_by_role: z.string().optional(),
  discovery_method: z.string().optional(),
  department: z.string().min(1, '부서를 입력해주세요').max(100),
  barcode_scanned: z.boolean().optional(),
  contributing_factors: z.string().optional(),
}).refine((data) => {
  // high_alert_type required when is_high_alert is true
  if (data.is_high_alert && !data.high_alert_type) {
    return false
  }
  return true
}, {
  message: '고위험 약물인 경우 유형을 선택해주세요',
  path: ['high_alert_type'],
})

type MedicationDetailFormData = z.infer<typeof medicationDetailSchema>

interface Props {
  incidentId: number
  existingDetail?: {
    id: number
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

const discoveryMethods = [
  { value: '', label: '선택하세요' },
  { value: 'barcode_scan', label: '바코드 스캔' },
  { value: 'double_check', label: '이중 확인' },
  { value: 'patient_report', label: '환자 보고' },
  { value: 'family_report', label: '보호자 보고' },
  { value: 'routine_check', label: '정기 확인' },
  { value: 'adverse_event', label: '이상반응 발생 후' },
  { value: 'other', label: '기타' },
]

const routes = [
  { value: '', label: '선택하세요' },
  { value: 'PO', label: '경구 (PO)' },
  { value: 'IV', label: '정맥주사 (IV)' },
  { value: 'IM', label: '근육주사 (IM)' },
  { value: 'SC', label: '피하주사 (SC)' },
  { value: 'SL', label: '설하 (SL)' },
  { value: 'TOP', label: '외용 (TOP)' },
  { value: 'INH', label: '흡입 (INH)' },
  { value: 'PR', label: '직장 (PR)' },
  { value: 'other', label: '기타' },
]

export default function MedicationDetailForm({ incidentId, existingDetail, onClose, onSuccess }: Props) {
  const queryClient = useQueryClient()
  const isEdit = !!existingDetail

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<MedicationDetailFormData>({
    resolver: zodResolver(medicationDetailSchema),
    defaultValues: existingDetail
      ? {
          patient_code: existingDetail.patient_code,
          patient_age_group: existingDetail.patient_age_group || '',
          error_type: existingDetail.error_type as MedicationErrorType,
          error_stage: existingDetail.error_stage as MedicationErrorStage,
          error_severity: existingDetail.error_severity as MedicationErrorSeverity,
          is_near_miss: existingDetail.is_near_miss,
          medication_category: existingDetail.medication_category || '',
          is_high_alert: existingDetail.is_high_alert,
          high_alert_type: existingDetail.high_alert_type as HighAlertMedication | null || null,
          intended_dose: existingDetail.intended_dose || '',
          actual_dose: existingDetail.actual_dose || '',
          intended_route: existingDetail.intended_route || '',
          actual_route: existingDetail.actual_route || '',
          discovered_by_role: existingDetail.discovered_by_role || '',
          discovery_method: existingDetail.discovery_method || '',
          department: existingDetail.department,
          barcode_scanned: existingDetail.barcode_scanned ?? false,
          contributing_factors: existingDetail.contributing_factors || '',
        }
      : {
          is_near_miss: false,
          is_high_alert: false,
          barcode_scanned: false,
          error_severity: 'C',
        },
  })

  const isHighAlert = watch('is_high_alert')

  const createMutation = useMutation({
    mutationFn: (data: MedicationDetailFormData) =>
      medicationDetailApi.create({
        incident_id: incidentId,
        ...data,
        high_alert_type: data.high_alert_type || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['medicationDetail', incidentId] })
      alert('투약 오류 상세 정보가 저장되었습니다.')
      onSuccess()
    },
    onError: () => {
      alert('저장에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: MedicationDetailFormData) =>
      medicationDetailApi.update(existingDetail!.id, {
        ...data,
        high_alert_type: data.high_alert_type || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['medicationDetail', incidentId] })
      alert('투약 오류 상세 정보가 수정되었습니다.')
      onSuccess()
    },
    onError: () => {
      alert('수정에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const onSubmit = (data: MedicationDetailFormData) => {
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
          <Pill className="h-5 w-5 text-purple-600" />
          <h3 className="text-lg font-semibold">
            {isEdit ? '투약 오류 상세 정보 수정' : '투약 오류 상세 정보 입력'}
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
          </div>
        </div>

        {/* Error Classification */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">오류 분류</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">오류 유형 *</label>
              <select {...register('error_type')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {(Object.keys(MEDICATION_ERROR_TYPE_LABELS) as MedicationErrorType[]).map((type) => (
                  <option key={type} value={type}>{MEDICATION_ERROR_TYPE_LABELS[type]}</option>
                ))}
              </select>
              {errors.error_type && (
                <p className="mt-1 text-sm text-red-600">{errors.error_type.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">발생 단계 *</label>
              <select {...register('error_stage')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {(Object.keys(MEDICATION_STAGE_LABELS) as MedicationErrorStage[]).map((stage) => (
                  <option key={stage} value={stage}>{MEDICATION_STAGE_LABELS[stage]}</option>
                ))}
              </select>
              {errors.error_stage && (
                <p className="mt-1 text-sm text-red-600">{errors.error_stage.message}</p>
              )}
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700">심각도 (NCC MERP) *</label>
              <select {...register('error_severity')} className="input-field mt-1">
                {(Object.keys(MEDICATION_SEVERITY_LABELS) as MedicationErrorSeverity[]).map((sev) => (
                  <option key={sev} value={sev}>{MEDICATION_SEVERITY_LABELS[sev]}</option>
                ))}
              </select>
              {errors.error_severity && (
                <p className="mt-1 text-sm text-red-600">{errors.error_severity.message}</p>
              )}
            </div>
            <div className="col-span-2">
              <label className="flex items-center gap-2">
                <input {...register('is_near_miss')} type="checkbox" className="rounded border-gray-300" />
                <span className="text-sm text-gray-700">근접오류 (환자에게 도달하지 않음)</span>
              </label>
            </div>
          </div>
        </div>

        {/* Medication Info */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">약물 정보</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700">약물 분류</label>
              <input {...register('medication_category')} className="input-field mt-1" placeholder="예: 항생제, 혈압약" />
            </div>
            <div className="col-span-2 space-y-3">
              <label className="flex items-center gap-2">
                <input {...register('is_high_alert')} type="checkbox" className="rounded border-gray-300" />
                <span className="text-sm text-gray-700 font-medium text-red-600">고위험 약물</span>
              </label>
              {isHighAlert && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">고위험 약물 유형 *</label>
                  <select {...register('high_alert_type')} className="input-field mt-1">
                    <option value="">선택하세요</option>
                    {(Object.keys(HIGH_ALERT_LABELS) as HighAlertMedication[]).map((type) => (
                      <option key={type} value={type}>{HIGH_ALERT_LABELS[type]}</option>
                    ))}
                  </select>
                  {errors.high_alert_type && (
                    <p className="mt-1 text-sm text-red-600">{errors.high_alert_type.message}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Dose & Route */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">용량 및 경로</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">의도한 용량</label>
              <input {...register('intended_dose')} className="input-field mt-1" placeholder="예: 500mg" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">실제 용량</label>
              <input {...register('actual_dose')} className="input-field mt-1" placeholder="예: 50mg" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">의도한 경로</label>
              <select {...register('intended_route')} className="input-field mt-1">
                {routes.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">실제 경로</label>
              <select {...register('actual_route')} className="input-field mt-1">
                {routes.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Discovery */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">발견 정보</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">발견자 직종</label>
              <input {...register('discovered_by_role')} className="input-field mt-1" placeholder="예: 간호사" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">발견 방법</label>
              <select {...register('discovery_method')} className="input-field mt-1">
                {discoveryMethods.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
            <div className="col-span-2">
              <label className="flex items-center gap-2">
                <input {...register('barcode_scanned')} type="checkbox" className="rounded border-gray-300" />
                <span className="text-sm text-gray-700">투약 시 바코드 스캔 시행됨</span>
              </label>
            </div>
          </div>
        </div>

        {/* Contributing Factors */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">기여 요인</h4>
          <textarea
            {...register('contributing_factors')}
            rows={3}
            className="input-field w-full"
            placeholder="오류 발생에 기여한 요인들을 기술해주세요 (예: 유사 약품명, 과중한 업무량, 의사소통 오류 등)"
          />
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
