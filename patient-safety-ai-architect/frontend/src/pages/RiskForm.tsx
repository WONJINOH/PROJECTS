import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AlertTriangle, Save, ArrowLeft } from 'lucide-react'
import { riskApi } from '@/utils/api'
import { useAuth } from '@/hooks/useAuth'
import type { RiskSourceType, RiskCategory, RiskLevel } from '@/types'
import {
  RISK_SOURCE_TYPE_LABELS,
  RISK_CATEGORY_LABELS,
  RISK_LEVEL_LABELS,
  RISK_LEVEL_COLORS,
} from '@/types'

// Schema with Korean error messages
const riskSchema = z.object({
  title: z.string().min(5, '제목은 5자 이상 입력하세요.').max(200),
  description: z.string().min(10, '설명은 10자 이상 입력하세요.'),
  source_type: z.enum([
    'psr', 'rounding', 'audit', 'complaint',
    'indicator', 'external', 'proactive', 'other'
  ] as const),
  source_incident_id: z.number().optional().nullable(),
  source_detail: z.string().optional(),
  category: z.enum([
    'fall', 'medication', 'pressure_ulcer', 'infection',
    'transfusion', 'procedure', 'restraint', 'environment',
    'security', 'communication', 'handoff', 'identification', 'other'
  ] as const),
  current_controls: z.string().optional(),
  probability: z.number().min(1).max(5),
  severity: z.number().min(1).max(5),
  owner_id: z.number().min(1, '담당자를 선택하세요.'),
  target_date: z.string().optional(),
})

type RiskFormData = z.infer<typeof riskSchema>

function calculateRiskLevel(p: number, s: number): RiskLevel {
  const score = p * s
  if (score <= 4) return 'low'
  if (score <= 9) return 'medium'
  if (score <= 16) return 'high'
  return 'critical'
}

export default function RiskForm() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<RiskFormData>({
    resolver: zodResolver(riskSchema),
    defaultValues: {
      probability: 1,
      severity: 1,
      source_type: 'psr',
      category: 'fall',
      owner_id: user?.id || 0,
    },
  })

  // Watch P and S for real-time calculation
  const probability = watch('probability')
  const severity = watch('severity')
  const riskScore = probability * severity
  const riskLevel = calculateRiskLevel(probability, severity)

  // Fetch existing risk for edit
  const { data: existingRisk } = useQuery({
    queryKey: ['risk', id],
    queryFn: () => riskApi.get(Number(id)),
    enabled: isEdit,
  })

  // Reset form when existing data loads
  useEffect(() => {
    if (existingRisk?.data) {
      const r = existingRisk.data
      reset({
        title: r.title,
        description: r.description,
        source_type: r.source_type,
        source_incident_id: r.source_incident_id,
        source_detail: r.source_detail,
        category: r.category,
        current_controls: r.current_controls,
        probability: r.probability,
        severity: r.severity,
        owner_id: r.owner_id,
        target_date: r.target_date,
      })
    }
  }, [existingRisk, reset])

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: RiskFormData) => riskApi.create({
      ...data,
      source_incident_id: data.source_incident_id ?? undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risks'] })
      navigate('/risks')
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: RiskFormData) => riskApi.update(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risks'] })
      queryClient.invalidateQueries({ queryKey: ['risk', id] })
      navigate(`/risks/${id}`)
    },
  })

  const onSubmit = (data: RiskFormData) => {
    if (isEdit) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  const error = createMutation.error || updateMutation.error

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-orange-600" />
            {isEdit ? '위험 수정' : '새 위험 등록'}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            위험 등록부에 새 위험을 등록합니다.
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {(error as Error).message || '저장 중 오류가 발생했습니다.'}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Info */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">기본 정보</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                제목 <span className="text-red-500">*</span>
              </label>
              <input
                {...register('title')}
                type="text"
                className="input-field"
                placeholder="위험 제목 (예: 낙상 위험 - 내과 병동)"
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                설명 <span className="text-red-500">*</span>
              </label>
              <textarea
                {...register('description')}
                rows={3}
                className="input-field"
                placeholder="위험에 대한 상세 설명"
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  출처 <span className="text-red-500">*</span>
                </label>
                <select {...register('source_type')} className="input-field">
                  {(Object.keys(RISK_SOURCE_TYPE_LABELS) as RiskSourceType[]).map((type) => (
                    <option key={type} value={type}>
                      {RISK_SOURCE_TYPE_LABELS[type]}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  분류 <span className="text-red-500">*</span>
                </label>
                <select {...register('category')} className="input-field">
                  {(Object.keys(RISK_CATEGORY_LABELS) as RiskCategory[]).map((cat) => (
                    <option key={cat} value={cat}>
                      {RISK_CATEGORY_LABELS[cat]}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                출처 상세
              </label>
              <input
                {...register('source_detail')}
                type="text"
                className="input-field"
                placeholder="PSR 번호, 감사 번호 등"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                현재 통제 방법
              </label>
              <textarea
                {...register('current_controls')}
                rows={2}
                className="input-field"
                placeholder="현재 적용 중인 위험 통제 방법"
              />
            </div>
          </div>
        </div>

        {/* Risk Assessment */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">위험 평가 (P×S)</h2>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                발생 가능성 (Probability) <span className="text-red-500">*</span>
              </label>
              <div className="space-y-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <label key={n} className="flex items-center gap-2">
                    <input
                      {...register('probability', { valueAsNumber: true })}
                      type="radio"
                      value={n}
                      className="h-4 w-4 text-primary-600"
                    />
                    <span className="text-sm text-gray-700">
                      {n} -{' '}
                      {n === 1 && '매우 낮음'}
                      {n === 2 && '낮음'}
                      {n === 3 && '보통'}
                      {n === 4 && '높음'}
                      {n === 5 && '매우 높음'}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                심각도 (Severity) <span className="text-red-500">*</span>
              </label>
              <div className="space-y-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <label key={n} className="flex items-center gap-2">
                    <input
                      {...register('severity', { valueAsNumber: true })}
                      type="radio"
                      value={n}
                      className="h-4 w-4 text-primary-600"
                    />
                    <span className="text-sm text-gray-700">
                      {n} -{' '}
                      {n === 1 && '경미'}
                      {n === 2 && '보통'}
                      {n === 3 && '중대'}
                      {n === 4 && '심각'}
                      {n === 5 && '치명적'}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Real-time Risk Score Display */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm text-gray-500">위험 점수:</span>
                <span className="ml-2 font-mono text-lg font-bold">
                  {probability} × {severity} = {riskScore}
                </span>
              </div>
              <span className={`badge text-sm ${RISK_LEVEL_COLORS[riskLevel]}`}>
                {RISK_LEVEL_LABELS[riskLevel]}
              </span>
            </div>
          </div>
        </div>

        {/* Assignment */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">담당 및 일정</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                담당자 ID <span className="text-red-500">*</span>
              </label>
              <input
                {...register('owner_id', { valueAsNumber: true })}
                type="number"
                className="input-field"
                placeholder="담당자 사용자 ID"
              />
              {errors.owner_id && (
                <p className="mt-1 text-sm text-red-600">{errors.owner_id.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                목표 완료일
              </label>
              <input
                {...register('target_date')}
                type="date"
                className="input-field"
              />
            </div>
          </div>
        </div>

        {/* Submit Buttons */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="btn-secondary"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="btn-primary flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {isSubmitting ? '저장 중...' : isEdit ? '수정' : '등록'}
          </button>
        </div>
      </form>
    </div>
  )
}
