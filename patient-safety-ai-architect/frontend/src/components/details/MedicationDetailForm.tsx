import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Loader2, Pill } from 'lucide-react'
import { medicationDetailApi } from '@/utils/api'
import {
  MEDICATION_STAGE_LABELS,
  MEDICATION_SEVERITY_LABELS,
  HIGH_ALERT_LABELS,
  MEDICATION_DISCOVERY_TIMING_OPTIONS,
  MEDICATION_ERROR_TYPE_BEFORE_OPTIONS,
  MEDICATION_ERROR_TYPE_AFTER_OPTIONS,
  MEDICATION_ERROR_CAUSE_OPTIONS,
  MedicationErrorType,
  MedicationErrorStage,
  MedicationErrorSeverity,
  HighAlertMedication,
  MedicationDiscoveryTiming,
} from '@/types'

// Validation schema (환자 정보는 Incident 공통 폼에서 입력)
const medicationDetailSchema = z.object({
  // 오류 정보
  discovery_timing: z.enum(['pre_administration', 'post_administration']).optional(),
  error_type: z.enum(['wrong_patient', 'wrong_drug', 'wrong_dose', 'wrong_route', 'wrong_time', 'wrong_rate', 'omission', 'unauthorized', 'deteriorated', 'monitoring', 'other', 'dispensing_error', 'prescribing', 'transcribing']),
  error_stage: z.enum(['prescribing', 'transcribing', 'dispensing', 'administering', 'monitoring']),
  error_severity: z.enum(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']),
  is_near_miss: z.boolean(),
  // 오류 원인
  error_causes: z.array(z.string()).optional(),
  error_cause_detail: z.string().optional(),
  // 약물 정보
  medication_category: z.string().optional(),
  is_high_alert: z.boolean(),
  high_alert_type: z.enum(['anticoagulant', 'insulin', 'opioid', 'chemotherapy', 'sedative', 'potassium', 'neuromuscular', 'other']).optional().nullable(),
  intended_dose: z.string().optional(),
  actual_dose: z.string().optional(),
  intended_route: z.string().optional(),
  actual_route: z.string().optional(),
  // 발견 정보
  discovered_by_role: z.string().optional(),
  discovery_method: z.string().optional(),
  discovery_method_detail: z.string().max(200).optional(),
  // 기타 (department는 UI에서 제거됨 - 환자 정보는 Incident 공통폼에서 관리)
  department: z.string().max(100).optional(),
  barcode_scanned: z.boolean().optional(),
  contributing_factors: z.string().optional(),
}).refine((data) => {
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
    // 환자 정보는 Incident에서 관리 (공통 폼)
    discovery_timing?: string
    error_type: string
    error_stage: string
    error_severity: string
    is_near_miss: boolean
    error_causes?: string[]
    error_cause_detail?: string
    medication_category?: string
    is_high_alert: boolean
    high_alert_type?: string
    intended_dose?: string
    actual_dose?: string
    intended_route?: string
    actual_route?: string
    discovered_by_role?: string
    discovery_method?: string
    discovery_method_detail?: string
    department: string
    barcode_scanned?: boolean
    contributing_factors?: string
  } | null
  onClose: () => void
  onSuccess: () => void
}

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
    control,
    setValue,
    formState: { errors },
  } = useForm<MedicationDetailFormData>({
    resolver: zodResolver(medicationDetailSchema),
    defaultValues: existingDetail
      ? {
          discovery_timing: existingDetail.discovery_timing as MedicationDiscoveryTiming | undefined,
          error_type: existingDetail.error_type as MedicationErrorType,
          error_stage: existingDetail.error_stage as MedicationErrorStage,
          error_severity: existingDetail.error_severity as MedicationErrorSeverity,
          is_near_miss: existingDetail.is_near_miss,
          error_causes: existingDetail.error_causes || [],
          error_cause_detail: existingDetail.error_cause_detail || '',
          medication_category: existingDetail.medication_category || '',
          is_high_alert: existingDetail.is_high_alert,
          high_alert_type: existingDetail.high_alert_type as HighAlertMedication | null || null,
          intended_dose: existingDetail.intended_dose || '',
          actual_dose: existingDetail.actual_dose || '',
          intended_route: existingDetail.intended_route || '',
          actual_route: existingDetail.actual_route || '',
          discovered_by_role: existingDetail.discovered_by_role || '',
          discovery_method: existingDetail.discovery_method || '',
          discovery_method_detail: existingDetail.discovery_method_detail || '',
          department: existingDetail.department,
          barcode_scanned: existingDetail.barcode_scanned ?? false,
          contributing_factors: existingDetail.contributing_factors || '',
        }
      : {
          is_near_miss: false,
          is_high_alert: false,
          barcode_scanned: false,
          error_severity: 'C',
          error_causes: [],
        },
  })

  const isHighAlert = watch('is_high_alert')
  const discoveryTiming = watch('discovery_timing')
  const selectedErrorCauses = watch('error_causes') || []
  const selectedDiscoveryMethod = watch('discovery_method')

  // Get error type options based on discovery timing
  const errorTypeOptions = discoveryTiming === 'pre_administration'
    ? MEDICATION_ERROR_TYPE_BEFORE_OPTIONS
    : discoveryTiming === 'post_administration'
    ? MEDICATION_ERROR_TYPE_AFTER_OPTIONS
    : [...MEDICATION_ERROR_TYPE_BEFORE_OPTIONS, ...MEDICATION_ERROR_TYPE_AFTER_OPTIONS]

  const createMutation = useMutation({
    mutationFn: (data: MedicationDetailFormData) =>
      medicationDetailApi.create({
        incident_id: incidentId,
        patient_code: '', // Placeholder - 환자 정보는 Incident에서 관리
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

  // Checkbox change handler for error causes
  const handleErrorCauseChange = (value: string, checked: boolean) => {
    const current = watch('error_causes') || []
    if (checked) {
      setValue('error_causes', [...current, value])
    } else {
      setValue('error_causes', current.filter(v => v !== value))
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
          <Pill className="h-5 w-5 text-purple-600" />
          <h3 className="text-lg font-semibold">
            {isEdit ? '투약 오류 상세 정보 수정' : '투약 오류 상세 정보 입력'}
          </h3>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* 환자 정보 안내 */}
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            환자 정보 및 발생 부서는 사고 보고(공통 폼)에서 입력합니다. 투약 오류 상세 정보만 아래에 입력해주세요.
          </p>
        </div>

        {/* Error Classification - PDF 양식 기반 발견 시점 → 오류 유형 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">오류 분류</h4>
          <div className="grid grid-cols-2 gap-4">
            {/* 발견 시점 (투약전/투약후) */}
            <div>
              <label className="block text-sm font-medium text-gray-700">발견 시점</label>
              <select {...register('discovery_timing')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {MEDICATION_DISCOVERY_TIMING_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            {/* 오류 유형 - 발견 시점에 따라 동적 변경 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">오류 유형 *</label>
              <select {...register('error_type')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {errorTypeOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
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
              <label className="flex items-center gap-2">
                <input {...register('is_near_miss')} type="checkbox" className="rounded border-gray-300" />
                <span className="text-sm text-gray-700">근접오류 (환자에게 도달하지 않음)</span>
              </label>
            </div>
          </div>
        </div>

        {/* 위험도 분류 (NCC MERP) - 별도 섹션 */}
        <div className="border rounded-lg p-4 space-y-4 bg-amber-50">
          <h4 className="font-medium text-gray-900">위험도 분류 (NCC MERP)</h4>
          <div>
            <label className="block text-sm font-medium text-gray-700">심각도 *</label>
            <select {...register('error_severity')} className="input-field mt-1">
              {(Object.keys(MEDICATION_SEVERITY_LABELS) as MedicationErrorSeverity[]).map((sev) => (
                <option key={sev} value={sev}>{MEDICATION_SEVERITY_LABELS[sev]}</option>
              ))}
            </select>
            {errors.error_severity && (
              <p className="mt-1 text-sm text-red-600">{errors.error_severity.message}</p>
            )}
            <p className="mt-2 text-xs text-gray-500">
              NCC MERP 분류 기준: A(오류 가능 상황) ~ I(사망)
            </p>
          </div>
        </div>

        {/* 발견된 오류의 원인 - PDF 양식 기반 */}
        <div className="border rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900">발견된 오류의 원인</h4>
          <div className="grid grid-cols-2 gap-3">
            {MEDICATION_ERROR_CAUSE_OPTIONS.map((option) => (
              <Controller
                key={option.value}
                name="error_causes"
                control={control}
                render={({ field }) => (
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300"
                      checked={field.value?.includes(option.value) || false}
                      onChange={(e) => handleErrorCauseChange(option.value, e.target.checked)}
                    />
                    <span className="text-sm text-gray-700">{option.label}</span>
                  </label>
                )}
              />
            ))}
          </div>
          {selectedErrorCauses.includes('other') && (
            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700">기타 원인 상세</label>
              <input
                {...register('error_cause_detail')}
                className="input-field mt-1"
                placeholder="기타 원인 입력"
              />
            </div>
          )}
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
              {/* 기타 발견 방법 상세 입력 */}
              {selectedDiscoveryMethod === 'other' && (
                <div className="mt-2">
                  <input
                    {...register('discovery_method_detail')}
                    type="text"
                    placeholder="기타 발견 방법 상세 내용을 입력해주세요"
                    className="input-field"
                  />
                </div>
              )}
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
