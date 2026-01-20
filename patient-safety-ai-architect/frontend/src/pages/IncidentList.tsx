import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, Filter, ChevronLeft, ChevronRight, Loader2, AlertCircle } from 'lucide-react'
import { incidentApi } from '@/utils/api'
import type { Incident, IncidentCategory, IncidentGrade, IncidentStatus, PaginatedResponse } from '@/types'

const categoryLabels: Record<IncidentCategory, string> = {
  fall: '낙상',
  medication: '투약',
  pressure_ulcer: '욕창',
  infection: '감염',
  medical_device: '의료기기',
  surgery: '수술',
  transfusion: '수혈',
  other: '기타',
}

const gradeColors: Record<IncidentGrade, string> = {
  near_miss: 'badge-near-miss',
  no_harm: 'badge-no-harm',
  mild: 'badge-mild',
  moderate: 'badge-moderate',
  severe: 'badge-severe',
  death: 'badge-death',
}

const gradeLabels: Record<IncidentGrade, string> = {
  near_miss: '근접오류',
  no_harm: '위해없음',
  mild: '경증',
  moderate: '중등도',
  severe: '중증',
  death: '사망',
}

const statusLabels: Record<IncidentStatus, string> = {
  draft: '초안',
  submitted: '제출됨',
  approved: '승인됨',
  closed: '종결',
}

const statusColors: Record<IncidentStatus, string> = {
  draft: 'bg-gray-100 text-gray-800',
  submitted: 'bg-blue-100 text-blue-800',
  approved: 'bg-green-100 text-green-800',
  closed: 'bg-purple-100 text-purple-800',
}

// Transform snake_case API response to camelCase
interface ApiIncident {
  id: number
  category: IncidentCategory
  grade: IncidentGrade
  occurred_at: string
  location: string
  description: string
  immediate_action: string
  reported_at: string
  reporter_name?: string
  root_cause?: string
  improvements?: string
  reporter_id: number
  department?: string
  status: IncidentStatus
  created_at: string
  updated_at: string
}

function transformIncident(api: ApiIncident): Incident {
  return {
    id: api.id,
    category: api.category,
    grade: api.grade,
    occurredAt: api.occurred_at,
    location: api.location,
    description: api.description,
    immediateAction: api.immediate_action,
    reportedAt: api.reported_at,
    reporterName: api.reporter_name,
    rootCause: api.root_cause,
    improvements: api.improvements,
    reporterId: api.reporter_id,
    department: api.department,
    status: api.status,
    createdAt: api.created_at,
    updatedAt: api.updated_at,
  }
}

export default function IncidentList() {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const limit = 10

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['incidents', page, limit],
    queryFn: async () => {
      const response = await incidentApi.list({ skip: (page - 1) * limit, limit })
      const apiData = response.data as PaginatedResponse<ApiIncident>
      return {
        items: apiData.items.map(transformIncident),
        total: apiData.total,
        skip: apiData.skip,
        limit: apiData.limit,
      }
    },
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const incidents = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / limit) || 1

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">사고 목록</h1>
          <p className="mt-1 text-sm text-gray-500">
            등록된 환자안전사고 보고서 목록입니다
          </p>
        </div>
        <Link to="/incidents/new" className="btn-primary flex items-center gap-2">
          <Plus className="h-4 w-4" />
          새 보고서
        </Link>
      </div>

      {/* Search and Filter */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <button className="btn-secondary flex items-center gap-2">
            <Filter className="h-4 w-4" />
            필터
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="card flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
          <span className="ml-3 text-gray-500">데이터를 불러오는 중...</span>
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex items-center gap-3 text-red-700">
            <AlertCircle className="h-5 w-5" />
            <span>데이터를 불러오는데 실패했습니다: {(error as Error)?.message || '알 수 없는 오류'}</span>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && incidents.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-gray-500">등록된 사고 보고서가 없습니다.</p>
          <Link to="/incidents/new" className="btn-primary mt-4 inline-flex items-center gap-2">
            <Plus className="h-4 w-4" />
            새 보고서 작성
          </Link>
        </div>
      )}

      {/* Incidents Table */}
      {!isLoading && !isError && incidents.length > 0 && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    유형
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    등급
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    장소
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    발생일시
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    상태
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    보고자
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {incidents.map((incident) => (
                  <tr
                    key={incident.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/incidents/${incident.id}`)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        to={`/incidents/${incident.id}`}
                        className="text-sm font-medium text-primary-600 hover:text-primary-800"
                        onClick={(e) => e.stopPropagation()}
                      >
                        #{incident.id}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {categoryLabels[incident.category] || incident.category}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${gradeColors[incident.grade] || 'bg-gray-100'}`}>
                        {gradeLabels[incident.grade] || incident.grade}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {incident.location}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(incident.occurredAt)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${statusColors[incident.status] || 'bg-gray-100'}`}>
                        {statusLabels[incident.status] || incident.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {incident.reporterName || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              총 <span className="font-medium">{total}</span>건
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <span className="text-sm text-gray-600">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= totalPages}
                className="p-2 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
