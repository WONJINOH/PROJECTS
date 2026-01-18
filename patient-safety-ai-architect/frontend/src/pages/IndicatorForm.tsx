import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowLeft, Save, BarChart2 } from 'lucide-react'
import { indicatorApi } from '@/utils/api'
import type { CreateIndicatorData } from '@/types'
import { INDICATOR_CATEGORY_LABELS } from '@/types'

// Validation schema
const indicatorSchema = z.object({
  code: z
    .string()
    .min(1, '코드를 입력해주세요')
    .regex(/^[A-Z]{2,5}-\d{3}$/, '코드 형식: PSR-001, PU-001 등'),
  name: z.string().min(1, '지표명을 입력해주세요').max(200),
  category: z.enum([
    'psr',
    'pressure_ulcer',
    'fall',
    'medication',
    'restraint',
    'infection',
    'staff_safety',
    'lab_tat',
    'composite',
  ], {
    required_error: '카테고리를 선택해주세요',
  }),
  description: z.string().max(1000).optional().or(z.literal('')),
  unit: z.string().min(1, '단위를 입력해주세요').max(50),
  calculation_formula: z.string().max(500).optional().or(z.literal('')),
  numerator_name: z.string().max(200).optional().or(z.literal('')),
  denominator_name: z.string().max(200).optional().or(z.literal('')),
  target_value: z.coerce.number().optional().or(z.literal('')),
  warning_threshold: z.coerce.number().optional().or(z.literal('')),
  critical_threshold: z.coerce.number().optional().or(z.literal('')),
  threshold_direction: z
    .enum(['higher_is_better', 'lower_is_better'])
    .optional()
    .or(z.literal('')),
  period_type: z.enum(['daily', 'weekly', 'monthly', 'quarterly', 'yearly']).default('monthly'),
  chart_type: z.enum(['line', 'bar', 'pie', 'area']).default('line'),
  is_key_indicator: z.boolean().default(false),
  display_order: z.coerce.number().int().min(0).default(0),
  data_source: z.string().max(200).optional().or(z.literal('')),
  auto_calculate: z.boolean().default(false),
  status: z.enum(['active', 'inactive', 'planned']).default('active'),
})

type IndicatorFormData = z.infer<typeof indicatorSchema>

const categories = Object.entries(INDICATOR_CATEGORY_LABELS).map(([value, label]) => ({
  value,
  label,
}))

const periodTypes = [
  { value: 'daily', label: '일간' },
  { value: 'weekly', label: '주간' },
  { value: 'monthly', label: '월간' },
  { value: 'quarterly', label: '분기' },
  { value: 'yearly', label: '연간' },
]

const chartTypes = [
  { value: 'line', label: '라인 차트' },
  { value: 'bar', label: '막대 차트' },
  { value: 'pie', label: '파이 차트' },
  { value: 'area', label: '영역 차트' },
]

const thresholdDirections = [
  { value: '', label: '선택 안 함' },
  { value: 'higher_is_better', label: '높을수록 좋음' },
  { value: 'lower_is_better', label: '낮을수록 좋음' },
]

const statusOptions = [
  { value: 'active', label: '활성' },
  { value: 'inactive', label: '비활성' },
  { value: 'planned', label: '예정' },
]

export default function IndicatorForm() {
  const navigate = useNavigate()
  const { id } = useParams()
  const isEdit = Boolean(id)

  // Fetch indicator data for edit mode
  const { data: indicatorData, isLoading: isLoadingIndicator } = useQuery({
    queryKey: ['indicator', id],
    queryFn: () => indicatorApi.get(Number(id)),
    enabled: isEdit,
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<IndicatorFormData>({
    resolver: zodResolver(indicatorSchema),
    defaultValues: {
      period_type: 'monthly',
      chart_type: 'line',
      is_key_indicator: false,
      display_order: 0,
      auto_calculate: false,
      status: 'active',
    },
    values: indicatorData?.data
      ? {
          code: indicatorData.data.code,
          name: indicatorData.data.name,
          category: indicatorData.data.category,
          description: indicatorData.data.description || '',
          unit: indicatorData.data.unit,
          calculation_formula: indicatorData.data.calculation_formula || '',
          numerator_name: indicatorData.data.numerator_name || '',
          denominator_name: indicatorData.data.denominator_name || '',
          target_value: indicatorData.data.target_value || '',
          warning_threshold: indicatorData.data.warning_threshold || '',
          critical_threshold: indicatorData.data.critical_threshold || '',
          threshold_direction: indicatorData.data.threshold_direction || '',
          period_type: indicatorData.data.period_type || 'monthly',
          chart_type: indicatorData.data.chart_type || 'line',
          is_key_indicator: indicatorData.data.is_key_indicator || false,
          display_order: indicatorData.data.display_order || 0,
          data_source: indicatorData.data.data_source || '',
          auto_calculate: indicatorData.data.auto_calculate || false,
          status: indicatorData.data.status || 'active',
        }
      : undefined,
  })

  const createMutation = useMutation({
    mutationFn: (data: CreateIndicatorData) => indicatorApi.create(data),
    onSuccess: () => {
      alert('지표가 생성되었습니다.')
      navigate('/indicators')
    },
    onError: () => {
      alert('생성에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Partial<CreateIndicatorData>) =>
      indicatorApi.update(Number(id), data),
    onSuccess: () => {
      alert('지표가 수정되었습니다.')
      navigate(`/indicators/${id}`)
    },
    onError: () => {
      alert('수정에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const onSubmit = (data: IndicatorFormData) => {
    // Clean up empty strings to undefined
    const cleanedData: CreateIndicatorData = {
      code: data.code,
      name: data.name,
      category: data.category,
      unit: data.unit,
      description: data.description || undefined,
      calculation_formula: data.calculation_formula || undefined,
      numerator_name: data.numerator_name || undefined,
      denominator_name: data.denominator_name || undefined,
      target_value: data.target_value === '' ? undefined : Number(data.target_value),
      warning_threshold:
        data.warning_threshold === '' ? undefined : Number(data.warning_threshold),
      critical_threshold:
        data.critical_threshold === '' ? undefined : Number(data.critical_threshold),
      threshold_direction: data.threshold_direction || undefined,
      period_type: data.period_type,
      chart_type: data.chart_type,
      is_key_indicator: data.is_key_indicator,
      display_order: data.display_order,
      data_source: data.data_source || undefined,
      auto_calculate: data.auto_calculate,
      status: data.status,
    }

    if (isEdit) {
      updateMutation.mutate(cleanedData)
    } else {
      createMutation.mutate(cleanedData)
    }
  }

  if (isEdit && isLoadingIndicator) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Page Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          돌아가기
        </button>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart2 className="h-6 w-6 text-primary-600" />
          {isEdit ? '지표 수정' : '새 지표 추가'}
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          {isEdit
            ? '지표 설정을 수정합니다.'
            : '새로운 환자안전 지표를 등록합니다. * 표시는 필수 항목입니다.'}
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Info */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">기본 정보</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Code */}
            <div>
              <label className="block text-sm font-medium text-gray-700">코드 *</label>
              <input
                {...register('code')}
                type="text"
                placeholder="PSR-001"
                className="input-field mt-1 font-mono"
              />
              {errors.code && (
                <p className="mt-1 text-sm text-red-600">{errors.code.message}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">형식: 대문자2~5자-숫자3자리</p>
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                카테고리 *
              </label>
              <select {...register('category')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {categories.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
              {errors.category && (
                <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>
              )}
            </div>

            {/* Name */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                지표명 *
              </label>
              <input
                {...register('name')}
                type="text"
                placeholder="환자안전사건 총 보고건수"
                className="input-field mt-1"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
              )}
            </div>

            {/* Unit */}
            <div>
              <label className="block text-sm font-medium text-gray-700">단위 *</label>
              <input
                {...register('unit')}
                type="text"
                placeholder="건, %, ‰"
                className="input-field mt-1"
              />
              {errors.unit && (
                <p className="mt-1 text-sm text-red-600">{errors.unit.message}</p>
              )}
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700">상태</label>
              <select {...register('status')} className="input-field mt-1">
                {statusOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">설명</label>
              <textarea
                {...register('description')}
                rows={2}
                placeholder="지표에 대한 설명"
                className="input-field mt-1"
              />
            </div>
          </div>
        </div>

        {/* Calculation Method */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">계산 방식</h2>

          <div className="space-y-4">
            {/* Calculation Formula */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                계산 공식
              </label>
              <input
                {...register('calculation_formula')}
                type="text"
                placeholder="(분자 / 분모) × 1000"
                className="input-field mt-1"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Numerator */}
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  분자 설명
                </label>
                <input
                  {...register('numerator_name')}
                  type="text"
                  placeholder="발생 건수"
                  className="input-field mt-1"
                />
              </div>

              {/* Denominator */}
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  분모 설명
                </label>
                <input
                  {...register('denominator_name')}
                  type="text"
                  placeholder="총 재원일수"
                  className="input-field mt-1"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Target & Thresholds */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">목표 및 기준</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Threshold Direction */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                기준 방향
              </label>
              <select {...register('threshold_direction')} className="input-field mt-1">
                {thresholdDirections.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Target Value */}
            <div>
              <label className="block text-sm font-medium text-gray-700">목표값</label>
              <input
                {...register('target_value')}
                type="number"
                step="any"
                placeholder="0.5"
                className="input-field mt-1"
              />
            </div>

            {/* Warning Threshold */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                경고 임계값
              </label>
              <input
                {...register('warning_threshold')}
                type="number"
                step="any"
                placeholder="0.8"
                className="input-field mt-1"
              />
            </div>

            {/* Critical Threshold */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                위험 임계값
              </label>
              <input
                {...register('critical_threshold')}
                type="number"
                step="any"
                placeholder="1.0"
                className="input-field mt-1"
              />
            </div>
          </div>
        </div>

        {/* Display Settings */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">표시 설정</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Period Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                집계 주기
              </label>
              <select {...register('period_type')} className="input-field mt-1">
                {periodTypes.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Chart Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                차트 유형
              </label>
              <select {...register('chart_type')} className="input-field mt-1">
                {chartTypes.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Display Order */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                표시 순서
              </label>
              <input
                {...register('display_order')}
                type="number"
                min="0"
                placeholder="0"
                className="input-field mt-1"
              />
            </div>

            {/* Key Indicator */}
            <div className="flex items-center pt-6">
              <input
                {...register('is_key_indicator')}
                type="checkbox"
                id="is_key_indicator"
                className="h-4 w-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
              />
              <label
                htmlFor="is_key_indicator"
                className="ml-2 text-sm text-gray-700"
              >
                핵심 지표로 지정 (★ 표시)
              </label>
            </div>
          </div>
        </div>

        {/* Data Settings */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">데이터 설정</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Data Source */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                데이터 출처
              </label>
              <input
                {...register('data_source')}
                type="text"
                placeholder="PSR 시스템, EMR 등"
                className="input-field mt-1"
              />
            </div>

            {/* Auto Calculate */}
            <div className="flex items-center pt-6">
              <input
                {...register('auto_calculate')}
                type="checkbox"
                id="auto_calculate"
                className="h-4 w-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
              />
              <label htmlFor="auto_calculate" className="ml-2 text-sm text-gray-700">
                자동 계산 사용
              </label>
            </div>
          </div>
        </div>

        {/* Submit Buttons */}
        <div className="flex justify-end gap-4">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
            취소
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending || updateMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {createMutation.isPending || updateMutation.isPending
              ? '저장 중...'
              : '저장'}
          </button>
        </div>
      </form>
    </div>
  )
}
