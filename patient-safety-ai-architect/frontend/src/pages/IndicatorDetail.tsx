import { useState, useMemo } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Edit,
  Plus,
  Star,
  CheckCircle,
  AlertTriangle,
  X,
  TrendingUp,
  TrendingDown,
  Target,
  Check,
  XCircle,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  BarChart,
  Bar,
} from 'recharts'
import { indicatorApi } from '@/utils/api'
import type { IndicatorConfig, IndicatorValue } from '@/types'
import { INDICATOR_CATEGORY_LABELS, INDICATOR_STATUS_LABELS } from '@/types'

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  inactive: 'bg-gray-100 text-gray-800',
  planned: 'bg-blue-100 text-blue-800',
  pending_approval: 'bg-yellow-100 text-yellow-800',
  rejected: 'bg-red-100 text-red-800',
}

// Roles that can approve indicators
const APPROVER_ROLES = ['qps_staff', 'director', 'admin', 'master']

// Value input modal component
function ValueInputModal({
  indicatorId,
  onClose,
}: {
  indicatorId: number
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    periodStart: '',
    periodEnd: '',
    value: '',
    numerator: '',
    denominator: '',
    notes: '',
  })

  const createMutation = useMutation({
    mutationFn: () =>
      indicatorApi.createValue(indicatorId, {
        period_start: formData.periodStart,
        period_end: formData.periodEnd,
        value: Number(formData.value),
        numerator: formData.numerator ? Number(formData.numerator) : undefined,
        denominator: formData.denominator ? Number(formData.denominator) : undefined,
        notes: formData.notes || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['indicatorValues', indicatorId] })
      onClose()
      alert('값이 입력되었습니다.')
    },
    onError: () => {
      alert('입력에 실패했습니다.')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h3 className="text-lg font-semibold">값 입력</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                시작일 *
              </label>
              <input
                type="date"
                value={formData.periodStart}
                onChange={(e) =>
                  setFormData({ ...formData, periodStart: e.target.value })
                }
                className="input-field mt-1"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                종료일 *
              </label>
              <input
                type="date"
                value={formData.periodEnd}
                onChange={(e) =>
                  setFormData({ ...formData, periodEnd: e.target.value })
                }
                className="input-field mt-1"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">값 *</label>
            <input
              type="number"
              step="any"
              value={formData.value}
              onChange={(e) => setFormData({ ...formData, value: e.target.value })}
              className="input-field mt-1"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">분자</label>
              <input
                type="number"
                step="any"
                value={formData.numerator}
                onChange={(e) =>
                  setFormData({ ...formData, numerator: e.target.value })
                }
                className="input-field mt-1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">분모</label>
              <input
                type="number"
                step="any"
                value={formData.denominator}
                onChange={(e) =>
                  setFormData({ ...formData, denominator: e.target.value })
                }
                className="input-field mt-1"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">메모</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              rows={2}
              className="input-field mt-1"
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

// Rejection reason modal component
function RejectModal({
  indicatorId,
  onClose,
  onSuccess,
}: {
  indicatorId: number
  onClose: () => void
  onSuccess: () => void
}) {
  const [reason, setReason] = useState('')

  const rejectMutation = useMutation({
    mutationFn: () => indicatorApi.reject(indicatorId, reason),
    onSuccess: () => {
      onSuccess()
      onClose()
      alert('지표가 반려되었습니다.')
    },
    onError: () => {
      alert('반려 처리에 실패했습니다.')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason.trim()) {
      alert('반려 사유를 입력해주세요.')
      return
    }
    rejectMutation.mutate()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-red-600">지표 반려</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              반려 사유 *
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              className="input-field"
              placeholder="반려 사유를 입력해주세요..."
              required
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn-secondary">
              취소
            </button>
            <button
              type="submit"
              disabled={rejectMutation.isPending}
              className="btn-primary bg-red-600 hover:bg-red-700"
            >
              {rejectMutation.isPending ? '처리 중...' : '반려'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function IndicatorDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const indicatorId = Number(id)

  const [showValueModal, setShowValueModal] = useState(false)
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [activeTab, setActiveTab] = useState<'info' | 'chart' | 'values'>('chart')

  // Check if current user can approve
  const canApprove = user && APPROVER_ROLES.includes(user.role)

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (comment?: string) => indicatorApi.approve(indicatorId, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['indicator', indicatorId] })
      alert('지표가 승인되었습니다.')
    },
    onError: () => {
      alert('승인 처리에 실패했습니다.')
    },
  })

  const handleApprove = () => {
    if (confirm('이 지표를 승인하시겠습니까?')) {
      approveMutation.mutate()
    }
  }

  // Fetch indicator data
  const { data: indicatorData, isLoading: isLoadingIndicator } = useQuery({
    queryKey: ['indicator', indicatorId],
    queryFn: () => indicatorApi.get(indicatorId),
  })

  // Fetch indicator values
  const { data: valuesData, isLoading: isLoadingValues } = useQuery({
    queryKey: ['indicatorValues', indicatorId],
    queryFn: () => indicatorApi.listValues(indicatorId),
  })

  // Transform indicator data
  const indicator: IndicatorConfig | null = useMemo(() => {
    if (!indicatorData?.data) return null
    const item = indicatorData.data
    return {
      id: item.id,
      code: item.code,
      name: item.name,
      category: item.category,
      description: item.description,
      unit: item.unit,
      calculationFormula: item.calculation_formula,
      numeratorName: item.numerator_name,
      denominatorName: item.denominator_name,
      targetValue: item.target_value,
      warningThreshold: item.warning_threshold,
      criticalThreshold: item.critical_threshold,
      thresholdDirection: item.threshold_direction,
      periodType: item.period_type,
      chartType: item.chart_type,
      isKeyIndicator: item.is_key_indicator,
      displayOrder: item.display_order,
      dataSource: item.data_source,
      autoCalculate: item.auto_calculate,
      status: item.status,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
      createdById: item.created_by_id,
    }
  }, [indicatorData])

  // Transform values data
  const values: IndicatorValue[] = useMemo(() => {
    if (!valuesData?.data?.items) return []
    return valuesData.data.items.map((item: Record<string, unknown>) => ({
      id: item.id,
      indicatorId: item.indicator_id,
      periodStart: item.period_start,
      periodEnd: item.period_end,
      value: item.value,
      numerator: item.numerator,
      denominator: item.denominator,
      notes: item.notes,
      isVerified: item.is_verified,
      verifiedAt: item.verified_at,
      verifiedById: item.verified_by_id,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
      createdById: item.created_by_id,
    }))
  }, [valuesData])

  // Chart data
  const chartData = useMemo(() => {
    return values
      .map((v) => ({
        period: new Date(v.periodStart).toLocaleDateString('ko-KR', {
          year: '2-digit',
          month: '2-digit',
        }),
        value: v.value,
        target: indicator?.targetValue,
      }))
      .reverse()
  }, [values, indicator])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  }

  if (isLoadingIndicator) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!indicator) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">지표를 찾을 수 없습니다.</p>
        <Link to="/indicators" className="text-primary-600 hover:underline mt-2 inline-block">
          목록으로 돌아가기
        </Link>
      </div>
    )
  }

  const isLowerBetter = indicator.thresholdDirection === 'lower_is_better'
  const latestValue = values[0]?.value
  const prevValue = values[1]?.value
  const trend = latestValue && prevValue ? latestValue - prevValue : null
  const trendPositive = trend
    ? isLowerBetter
      ? trend < 0
      : trend > 0
    : null

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button
            onClick={() => navigate('/indicators')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            목록
          </button>
          <div className="flex items-center gap-3">
            <span className="font-mono text-lg text-gray-500">{indicator.code}</span>
            {indicator.isKeyIndicator && (
              <Star className="h-5 w-5 text-yellow-500 fill-yellow-500" />
            )}
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">{indicator.name}</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className="text-sm text-gray-500">
              {INDICATOR_CATEGORY_LABELS[indicator.category]}
            </span>
            <span className={`badge ${statusColors[indicator.status]}`}>
              {INDICATOR_STATUS_LABELS[indicator.status]}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Approve/Reject buttons for pending indicators */}
          {indicator.status === 'pending_approval' && canApprove && (
            <>
              <button
                onClick={handleApprove}
                disabled={approveMutation.isPending}
                className="btn-primary bg-green-600 hover:bg-green-700 flex items-center gap-2"
              >
                <Check className="h-4 w-4" />
                {approveMutation.isPending ? '처리 중...' : '승인'}
              </button>
              <button
                onClick={() => setShowRejectModal(true)}
                className="btn-secondary text-red-600 border-red-300 hover:bg-red-50 flex items-center gap-2"
              >
                <XCircle className="h-4 w-4" />
                반려
              </button>
            </>
          )}
          <Link
            to={`/indicators/${indicatorId}/edit`}
            className="btn-secondary flex items-center gap-2"
          >
            <Edit className="h-4 w-4" />
            편집
          </Link>
        </div>
      </div>

      {/* Pending Approval Notice */}
      {indicator.status === 'pending_approval' && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-yellow-800">승인 대기 중</h4>
            <p className="text-sm text-yellow-700 mt-1">
              이 지표는 아직 승인되지 않았습니다. QPS 담당자 또는 관리자의 승인이 필요합니다.
            </p>
          </div>
        </div>
      )}

      {/* Rejected Notice */}
      {indicator.status === 'rejected' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <XCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-red-800">반려됨</h4>
            <p className="text-sm text-red-700 mt-1">
              이 지표는 반려되었습니다. 수정 후 다시 제출해주세요.
            </p>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Latest Value */}
        <div className="card">
          <div className="text-sm text-gray-500 mb-1">최근 값</div>
          <div className="flex items-end gap-2">
            <span className="text-2xl font-bold text-gray-900">
              {latestValue ?? '-'}
            </span>
            <span className="text-sm text-gray-500 mb-1">{indicator.unit}</span>
          </div>
          {trend !== null && (
            <div
              className={`flex items-center gap-1 text-sm mt-1 ${
                trendPositive ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {trendPositive ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              {Math.abs(trend).toFixed(2)} ({isLowerBetter ? '감소' : '증가'})
            </div>
          )}
        </div>

        {/* Target */}
        <div className="card">
          <div className="text-sm text-gray-500 mb-1">목표</div>
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-primary-600" />
            <span className="text-2xl font-bold text-gray-900">
              {indicator.targetValue ?? '-'}
            </span>
            <span className="text-sm text-gray-500">{indicator.unit}</span>
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {isLowerBetter ? '낮을수록 좋음' : '높을수록 좋음'}
          </div>
        </div>

        {/* Warning Threshold */}
        <div className="card">
          <div className="text-sm text-gray-500 mb-1">경고 임계</div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            <span className="text-2xl font-bold text-yellow-600">
              {indicator.warningThreshold ?? '-'}
            </span>
            <span className="text-sm text-gray-500">{indicator.unit}</span>
          </div>
        </div>

        {/* Critical Threshold */}
        <div className="card">
          <div className="text-sm text-gray-500 mb-1">위험 임계</div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span className="text-2xl font-bold text-red-600">
              {indicator.criticalThreshold ?? '-'}
            </span>
            <span className="text-sm text-gray-500">{indicator.unit}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'info', label: '기본 정보' },
            { id: 'chart', label: '추세 차트' },
            { id: 'values', label: '값 목록' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'info' | 'chart' | 'values')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'info' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">지표 정보</h3>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm text-gray-500">설명</dt>
              <dd className="mt-1 text-gray-900">
                {indicator.description || '-'}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">계산 공식</dt>
              <dd className="mt-1 text-gray-900 font-mono text-sm">
                {indicator.calculationFormula || '-'}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">분자</dt>
              <dd className="mt-1 text-gray-900">
                {indicator.numeratorName || '-'}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">분모</dt>
              <dd className="mt-1 text-gray-900">
                {indicator.denominatorName || '-'}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">집계 주기</dt>
              <dd className="mt-1 text-gray-900 capitalize">
                {indicator.periodType}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">데이터 출처</dt>
              <dd className="mt-1 text-gray-900">
                {indicator.dataSource || '-'}
              </dd>
            </div>
          </dl>
        </div>
      )}

      {activeTab === 'chart' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">추세 차트</h3>
          {chartData.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                {indicator.chartType === 'bar' ? (
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" />
                    {indicator.targetValue && (
                      <ReferenceLine
                        y={indicator.targetValue}
                        stroke="#10b981"
                        strokeDasharray="3 3"
                        label="목표"
                      />
                    )}
                  </BarChart>
                ) : (
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: '#3b82f6', strokeWidth: 2 }}
                    />
                    {indicator.targetValue && (
                      <ReferenceLine
                        y={indicator.targetValue}
                        stroke="#10b981"
                        strokeDasharray="3 3"
                        label="목표"
                      />
                    )}
                    {indicator.warningThreshold && (
                      <ReferenceLine
                        y={indicator.warningThreshold}
                        stroke="#f59e0b"
                        strokeDasharray="3 3"
                      />
                    )}
                    {indicator.criticalThreshold && (
                      <ReferenceLine
                        y={indicator.criticalThreshold}
                        stroke="#ef4444"
                        strokeDasharray="3 3"
                      />
                    )}
                  </LineChart>
                )}
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              차트에 표시할 데이터가 없습니다.
            </div>
          )}
        </div>
      )}

      {activeTab === 'values' && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">값 목록</h3>
            <button
              onClick={() => setShowValueModal(true)}
              className="btn-primary flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />값 입력
            </button>
          </div>

          {isLoadingValues ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
            </div>
          ) : values.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      기간
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      값
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      분자
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      분모
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                      검증
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      메모
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {values.map((value) => (
                    <tr key={value.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(value.periodStart)} ~ {formatDate(value.periodEnd)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                        {value.value}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-500">
                        {value.numerator ?? '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-500">
                        {value.denominator ?? '-'}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-center">
                        {value.isVerified ? (
                          <CheckCircle className="h-5 w-5 text-green-500 mx-auto" />
                        ) : (
                          <span className="text-xs text-gray-400">미검증</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">
                        {value.notes || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              입력된 값이 없습니다.
            </div>
          )}
        </div>
      )}

      {/* Value Input Modal */}
      {showValueModal && (
        <ValueInputModal
          indicatorId={indicatorId}
          onClose={() => setShowValueModal(false)}
        />
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <RejectModal
          indicatorId={indicatorId}
          onClose={() => setShowRejectModal(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ['indicator', indicatorId] })
          }}
        />
      )}
    </div>
  )
}
