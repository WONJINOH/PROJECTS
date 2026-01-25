import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Plus,
  Search,
  AlertTriangle,
  Grid3X3,
  ArrowUpRight,
} from 'lucide-react'
import { riskApi } from '@/utils/api'
import type { Risk, RiskLevel, RiskStatus, RiskCategory } from '@/types'
import {
  RISK_LEVEL_LABELS,
  RISK_LEVEL_COLORS,
  RISK_STATUS_LABELS,
  RISK_STATUS_COLORS,
  RISK_CATEGORY_LABELS,
} from '@/types'

const CATEGORY_ORDER: RiskCategory[] = [
  'fall',
  'medication',
  'pressure_ulcer',
  'infection',
  'transfusion',
  'procedure',
  'restraint',
  'environment',
  'security',
  'communication',
  'handoff',
  'identification',
  'other',
]

export default function RiskList() {
  const [searchTerm, setSearchTerm] = useState('')
  const [levelFilter, setLevelFilter] = useState<RiskLevel | ''>('')
  const [statusFilter, setStatusFilter] = useState<RiskStatus | ''>('')
  const [categoryFilter, setCategoryFilter] = useState<RiskCategory | ''>('')

  const { data, isLoading } = useQuery({
    queryKey: ['risks', levelFilter, statusFilter, categoryFilter],
    queryFn: () =>
      riskApi.list({
        level: levelFilter || undefined,
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
        limit: 100,
      }),
  })

  const risks: Risk[] = useMemo(() => {
    if (!data?.data?.items) return []
    // Transform snake_case to camelCase
    return data.data.items.map((item: Record<string, unknown>) => ({
      id: item.id,
      riskCode: item.risk_code,
      title: item.title,
      description: item.description,
      sourceType: item.source_type,
      sourceIncidentId: item.source_incident_id,
      category: item.category,
      currentControls: item.current_controls,
      probability: item.probability,
      severity: item.severity,
      riskScore: item.risk_score,
      riskLevel: item.risk_level,
      status: item.status,
      ownerId: item.owner_id,
      autoEscalated: item.auto_escalated,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
    }))
  }, [data])

  const filteredRisks = useMemo(() => {
    if (!searchTerm) return risks
    const term = searchTerm.toLowerCase()
    return risks.filter(
      (r) =>
        r.riskCode.toLowerCase().includes(term) ||
        r.title.toLowerCase().includes(term) ||
        r.description.toLowerCase().includes(term)
    )
  }, [risks, searchTerm])

  // Count by level
  const levelCounts = useMemo(() => {
    const counts: Record<RiskLevel, number> = { low: 0, medium: 0, high: 0, critical: 0 }
    risks.forEach((r) => {
      if (r.status !== 'closed') {
        counts[r.riskLevel]++
      }
    })
    return counts
  }, [risks])

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-orange-600" />
            위험 관리
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            위험 등록부 (Risk Register) 관리
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/risks/matrix"
            className="btn-secondary flex items-center gap-2"
          >
            <Grid3X3 className="h-4 w-4" />
            위험 매트릭스
          </Link>
          <Link to="/risks/new" className="btn-primary flex items-center gap-2">
            <Plus className="h-4 w-4" />
            위험 등록
          </Link>
        </div>
      </div>

      {/* Level Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        {(['critical', 'high', 'medium', 'low'] as RiskLevel[]).map((level) => (
          <button
            key={level}
            onClick={() => setLevelFilter(levelFilter === level ? '' : level)}
            className={`card p-4 text-left transition-all ${
              levelFilter === level ? 'ring-2 ring-primary-500' : ''
            }`}
          >
            <div className="flex items-center justify-between">
              <span className={`badge ${RISK_LEVEL_COLORS[level]}`}>
                {RISK_LEVEL_LABELS[level]}
              </span>
              <span className="text-2xl font-bold text-gray-900">
                {levelCounts[level]}
              </span>
            </div>
          </button>
        ))}
      </div>

      {/* Search and Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="코드, 제목, 설명으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value as RiskCategory | '')}
            className="input-field w-full sm:w-40"
          >
            <option value="">모든 분류</option>
            {CATEGORY_ORDER.map((cat) => (
              <option key={cat} value={cat}>
                {RISK_CATEGORY_LABELS[cat]}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as RiskStatus | '')}
            className="input-field w-full sm:w-36"
          >
            <option value="">모든 상태</option>
            <option value="identified">식별됨</option>
            <option value="assessing">평가 중</option>
            <option value="treating">조치 진행 중</option>
            <option value="monitoring">모니터링 중</option>
            <option value="accepted">수용됨</option>
            <option value="closed">종결</option>
          </select>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}

      {/* Risk List */}
      {!isLoading && (
        <div className="card overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  코드
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  제목
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  분류
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P×S
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  위험도
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상세
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredRisks.map((risk) => (
                <tr key={risk.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-gray-900">
                        {risk.riskCode}
                      </span>
                      {risk.autoEscalated && (
                        <span title="자동 승격">
                          <ArrowUpRight className="h-4 w-4 text-blue-500" />
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
                      {risk.title}
                    </div>
                    <div className="text-sm text-gray-500 truncate max-w-xs">
                      {risk.description}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-700">
                      {RISK_CATEGORY_LABELS[risk.category]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className="font-mono text-sm">
                      {risk.probability}×{risk.severity}={risk.riskScore}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`badge ${RISK_LEVEL_COLORS[risk.riskLevel]}`}>
                      {RISK_LEVEL_LABELS[risk.riskLevel]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`badge ${RISK_STATUS_COLORS[risk.status]}`}>
                      {RISK_STATUS_LABELS[risk.status]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <Link
                      to={`/risks/${risk.id}`}
                      className="text-primary-600 hover:text-primary-800 text-sm font-medium"
                    >
                      상세
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Empty State */}
          {filteredRisks.length === 0 && (
            <div className="py-12 text-center">
              <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {searchTerm || levelFilter || statusFilter || categoryFilter
                  ? '검색 조건에 맞는 위험이 없습니다.'
                  : '등록된 위험이 없습니다.'}
              </p>
              <Link
                to="/risks/new"
                className="inline-flex items-center gap-2 mt-4 text-primary-600 hover:text-primary-800"
              >
                <Plus className="h-4 w-4" />
                위험 등록하기
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
