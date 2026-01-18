import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Plus,
  Search,
  ChevronDown,
  ChevronRight,
  Star,
  BarChart2,
} from 'lucide-react'
import { indicatorApi } from '@/utils/api'
import type {
  IndicatorConfig,
  IndicatorCategory,
  IndicatorStatusType,
} from '@/types'
import {
  INDICATOR_CATEGORY_LABELS,
  INDICATOR_STATUS_LABELS,
} from '@/types'

const statusColors: Record<IndicatorStatusType, string> = {
  active: 'bg-green-100 text-green-800',
  inactive: 'bg-gray-100 text-gray-800',
  planned: 'bg-blue-100 text-blue-800',
}

// Category order for display
const CATEGORY_ORDER: IndicatorCategory[] = [
  'psr',
  'pressure_ulcer',
  'fall',
  'medication',
  'restraint',
  'infection',
  'staff_safety',
  'lab_tat',
  'composite',
]

interface IndicatorsByCategory {
  [key: string]: IndicatorConfig[]
}

export default function IndicatorList() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<IndicatorStatusType | ''>('')
  const [categoryFilter, setCategoryFilter] = useState<IndicatorCategory | ''>('')
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(CATEGORY_ORDER)
  )

  const { data, isLoading } = useQuery({
    queryKey: ['indicators', statusFilter, categoryFilter, searchTerm],
    queryFn: () =>
      indicatorApi.list({
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
        search: searchTerm || undefined,
        limit: 100,
      }),
  })

  const indicators: IndicatorConfig[] = useMemo(() => {
    if (!data?.data?.items) return []
    // Transform snake_case to camelCase
    return data.data.items.map((item: Record<string, unknown>) => ({
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
    }))
  }, [data])

  const indicatorsByCategory = useMemo(() => {
    const grouped: IndicatorsByCategory = {}
    indicators.forEach((indicator) => {
      const cat = indicator.category
      if (!grouped[cat]) grouped[cat] = []
      grouped[cat].push(indicator)
    })
    // Sort by display order within each category
    Object.keys(grouped).forEach((cat) => {
      grouped[cat].sort((a, b) => a.displayOrder - b.displayOrder)
    })
    return grouped
  }, [indicators])

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev)
      if (next.has(category)) {
        next.delete(category)
      } else {
        next.add(category)
      }
      return next
    })
  }

  const expandAll = () => setExpandedCategories(new Set(CATEGORY_ORDER))
  const collapseAll = () => setExpandedCategories(new Set())

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart2 className="h-6 w-6 text-primary-600" />
            지표 관리
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            환자안전 지표 설정 및 값 관리
          </p>
        </div>
        <Link to="/indicators/new" className="btn-primary flex items-center gap-2">
          <Plus className="h-4 w-4" />
          새 지표
        </Link>
      </div>

      {/* Search and Filter */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="코드 또는 이름으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value as IndicatorCategory | '')}
            className="input-field w-full sm:w-48"
          >
            <option value="">모든 카테고리</option>
            {CATEGORY_ORDER.map((cat) => (
              <option key={cat} value={cat}>
                {INDICATOR_CATEGORY_LABELS[cat]}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as IndicatorStatusType | '')}
            className="input-field w-full sm:w-32"
          >
            <option value="">모든 상태</option>
            <option value="active">활성</option>
            <option value="inactive">비활성</option>
            <option value="planned">예정</option>
          </select>
        </div>
      </div>

      {/* Expand/Collapse Controls */}
      <div className="flex gap-2">
        <button
          onClick={expandAll}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          모두 펼치기
        </button>
        <span className="text-gray-300">|</span>
        <button
          onClick={collapseAll}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          모두 접기
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}

      {/* Indicators by Category */}
      {!isLoading && (
        <div className="space-y-4">
          {CATEGORY_ORDER.map((category) => {
            const categoryIndicators = indicatorsByCategory[category] || []
            if (categoryFilter && category !== categoryFilter) return null
            if (categoryIndicators.length === 0 && !categoryFilter) return null

            const isExpanded = expandedCategories.has(category)

            return (
              <div key={category} className="card overflow-hidden">
                {/* Category Header */}
                <button
                  onClick={() => toggleCategory(category)}
                  className="w-full px-6 py-4 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? (
                      <ChevronDown className="h-5 w-5 text-gray-500" />
                    ) : (
                      <ChevronRight className="h-5 w-5 text-gray-500" />
                    )}
                    <span className="font-medium text-gray-900">
                      {INDICATOR_CATEGORY_LABELS[category]}
                    </span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {categoryIndicators.length}개
                  </span>
                </button>

                {/* Category Content */}
                {isExpanded && categoryIndicators.length > 0 && (
                  <div className="divide-y divide-gray-200">
                    {categoryIndicators.map((indicator) => (
                      <Link
                        key={indicator.id}
                        to={`/indicators/${indicator.id}`}
                        className="block px-6 py-4 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-sm text-gray-500 w-20">
                              {indicator.code}
                            </span>
                            {indicator.isKeyIndicator && (
                              <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                            )}
                            <span className="text-gray-900">{indicator.name}</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-sm text-gray-500">
                              {indicator.unit}
                            </span>
                            <span
                              className={`badge ${statusColors[indicator.status]}`}
                            >
                              {INDICATOR_STATUS_LABELS[indicator.status]}
                            </span>
                          </div>
                        </div>
                        {indicator.description && (
                          <p className="mt-1 text-sm text-gray-500 pl-[92px]">
                            {indicator.description}
                          </p>
                        )}
                      </Link>
                    ))}
                  </div>
                )}

                {/* Empty State */}
                {isExpanded && categoryIndicators.length === 0 && (
                  <div className="px-6 py-8 text-center text-gray-500">
                    이 카테고리에 등록된 지표가 없습니다.
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Empty State for All */}
      {!isLoading && indicators.length === 0 && (
        <div className="card py-12 text-center">
          <BarChart2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">등록된 지표가 없습니다.</p>
          <Link
            to="/indicators/new"
            className="inline-flex items-center gap-2 mt-4 text-primary-600 hover:text-primary-800"
          >
            <Plus className="h-4 w-4" />새 지표 추가하기
          </Link>
        </div>
      )}
    </div>
  )
}
