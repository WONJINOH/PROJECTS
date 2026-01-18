import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Plus, Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react'
import { incidentApi } from '@/utils/api'

// Mock data (replace with API)
const mockIncidents = [
  {
    id: 1,
    category: '낙상',
    grade: 'MILD',
    location: '301호',
    occurred_at: '2024-01-15T14:30:00',
    status: 'submitted',
    reporter_name: '김간호',
  },
  {
    id: 2,
    category: '투약',
    grade: 'NEAR_MISS',
    location: '402호',
    occurred_at: '2024-01-14T09:15:00',
    status: 'approved',
    reporter_name: null,
  },
  {
    id: 3,
    category: '욕창',
    grade: 'MODERATE',
    location: '205호',
    occurred_at: '2024-01-13T11:45:00',
    status: 'draft',
    reporter_name: '이간호',
  },
]

const gradeColors: Record<string, string> = {
  NEAR_MISS: 'badge-near-miss',
  NO_HARM: 'badge-no-harm',
  MILD: 'badge-mild',
  MODERATE: 'badge-moderate',
  SEVERE: 'badge-severe',
  DEATH: 'badge-death',
}

const gradeLabels: Record<string, string> = {
  NEAR_MISS: '근접오류',
  NO_HARM: '위해없음',
  MILD: '경증',
  MODERATE: '중등도',
  SEVERE: '중증',
  DEATH: '사망',
}

const statusLabels: Record<string, string> = {
  draft: '초안',
  submitted: '제출됨',
  approved: '승인됨',
  closed: '종결',
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  submitted: 'bg-blue-100 text-blue-800',
  approved: 'bg-green-100 text-green-800',
  closed: 'bg-purple-100 text-purple-800',
}

export default function IncidentList() {
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const limit = 10

  // TODO: Replace with actual API call
  // const { data, isLoading } = useQuery({
  //   queryKey: ['incidents', page, searchTerm],
  //   queryFn: () => incidentApi.list({ skip: (page - 1) * limit, limit }),
  // })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

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

      {/* Incidents Table */}
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
              {mockIncidents.map((incident) => (
                <tr
                  key={incident.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => window.location.href = `/incidents/${incident.id}`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      to={`/incidents/${incident.id}`}
                      className="text-sm font-medium text-primary-600 hover:text-primary-800"
                    >
                      #{incident.id}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {incident.category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge ${gradeColors[incident.grade]}`}>
                      {gradeLabels[incident.grade]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {incident.location}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(incident.occurred_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge ${statusColors[incident.status]}`}>
                      {statusLabels[incident.status]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {incident.reporter_name || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            총 <span className="font-medium">{mockIncidents.length}</span>건
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
              {page} / {Math.ceil(mockIncidents.length / limit) || 1}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(mockIncidents.length / limit)}
              className="p-2 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
