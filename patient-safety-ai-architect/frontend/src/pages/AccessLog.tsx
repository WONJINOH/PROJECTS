import { useState } from 'react'
import { Search, Filter, ChevronLeft, ChevronRight } from 'lucide-react'

// Mock data (replace with API)
const mockLogs = [
  {
    id: 1,
    event_type: 'INCIDENT_VIEW',
    timestamp: '2024-01-16T10:30:00',
    username: '김간호',
    user_role: 'QPS_STAFF',
    resource_type: 'incident',
    resource_id: '1',
    ip_address: '192.168.1.100',
    result: 'success',
  },
  {
    id: 2,
    event_type: 'AUTH_LOGIN',
    timestamp: '2024-01-16T09:00:00',
    username: '박원장',
    user_role: 'DIRECTOR',
    resource_type: null,
    resource_id: null,
    ip_address: '192.168.1.101',
    result: 'success',
  },
  {
    id: 3,
    event_type: 'INCIDENT_CREATE',
    timestamp: '2024-01-15T15:00:00',
    username: '이간호',
    user_role: 'REPORTER',
    resource_type: 'incident',
    resource_id: '3',
    ip_address: '192.168.1.102',
    result: 'success',
  },
  {
    id: 4,
    event_type: 'AUTH_FAILED',
    timestamp: '2024-01-15T08:45:00',
    username: 'unknown',
    user_role: null,
    resource_type: null,
    resource_id: null,
    ip_address: '192.168.1.200',
    result: 'failure',
  },
  {
    id: 5,
    event_type: 'ATTACHMENT_DOWNLOAD',
    timestamp: '2024-01-15T14:20:00',
    username: '김간호',
    user_role: 'QPS_STAFF',
    resource_type: 'attachment',
    resource_id: '1',
    ip_address: '192.168.1.100',
    result: 'success',
  },
]

const eventTypeLabels: Record<string, string> = {
  AUTH_LOGIN: '로그인',
  AUTH_LOGOUT: '로그아웃',
  AUTH_FAILED: '로그인 실패',
  INCIDENT_VIEW: '사고 조회',
  INCIDENT_CREATE: '사고 등록',
  INCIDENT_UPDATE: '사고 수정',
  INCIDENT_DELETE: '사고 삭제',
  INCIDENT_EXPORT: '사고 내보내기',
  ATTACHMENT_UPLOAD: '파일 업로드',
  ATTACHMENT_DOWNLOAD: '파일 다운로드',
  ATTACHMENT_DELETE: '파일 삭제',
  APPROVAL_ACTION: '승인 처리',
  PERMISSION_CHANGE: '권한 변경',
}

const roleLabels: Record<string, string> = {
  REPORTER: '보고자',
  QPS_STAFF: 'QI담당자',
  VICE_CHAIR: '부원장',
  DIRECTOR: '원장',
  ADMIN: '관리자',
}

export default function AccessLog() {
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const limit = 20

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">접근 로그</h1>
        <p className="mt-1 text-sm text-gray-500">
          시스템 접근 및 활동 기록입니다 (PIPA Art. 29 준수)
        </p>
      </div>

      {/* Search and Filter */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="사용자, IP 주소 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <select className="input-field w-auto">
            <option value="">모든 이벤트</option>
            <option value="AUTH">인증</option>
            <option value="INCIDENT">사고</option>
            <option value="ATTACHMENT">첨부파일</option>
            <option value="APPROVAL">승인</option>
          </select>
          <button className="btn-secondary flex items-center gap-2">
            <Filter className="h-4 w-4" />
            필터
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  시간
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  이벤트
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  사용자
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  역할
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  대상
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  결과
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {mockLogs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(log.timestamp)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {eventTypeLabels[log.event_type] || log.event_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {log.username}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {log.user_role ? roleLabels[log.user_role] || log.user_role : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {log.resource_type && log.resource_id
                      ? `${log.resource_type} #${log.resource_id}`
                      : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-500">
                    {log.ip_address}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`badge ${
                        log.result === 'success'
                          ? 'bg-green-100 text-green-800'
                          : log.result === 'failure'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {log.result === 'success'
                        ? '성공'
                        : log.result === 'failure'
                        ? '실패'
                        : '거부'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            총 <span className="font-medium">{mockLogs.length}</span>건
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
              {page} / {Math.ceil(mockLogs.length / limit) || 1}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(mockLogs.length / limit)}
              className="p-2 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-medium text-blue-800">PIPA 감사 로그 정책</h3>
        <ul className="mt-2 text-sm text-blue-700 space-y-1">
          <li>• 모든 개인정보 접근 기록은 5년간 보관됩니다</li>
          <li>• 로그는 변경 불가(append-only) 방식으로 저장됩니다</li>
          <li>• 해시 체인으로 위변조를 방지합니다</li>
          <li>• 민감 정보는 마스킹 처리됩니다</li>
        </ul>
      </div>
    </div>
  )
}
