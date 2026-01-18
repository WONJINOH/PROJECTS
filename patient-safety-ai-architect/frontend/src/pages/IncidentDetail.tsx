import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft,
  Calendar,
  MapPin,
  User,
  FileText,
  Download,
  CheckCircle,
  XCircle,
  Clock,
} from 'lucide-react'
import { incidentApi, approvalApi } from '@/utils/api'

// Mock data (replace with API)
const mockIncident = {
  id: 1,
  category: 'fall',
  grade: 'MILD',
  location: '301호',
  occurred_at: '2024-01-15T14:30:00',
  reported_at: '2024-01-15T15:00:00',
  description: '환자가 화장실에서 미끄러져 넘어짐. 바닥이 젖어 있었음.',
  immediate_action: '환자 상태 확인 후 의사 호출. 활력징후 측정 및 외상 여부 확인.',
  root_cause: '화장실 바닥 배수 불량으로 물기가 고여 있었음',
  improvements: '배수구 점검 및 미끄럼 방지 매트 설치 권고',
  reporter_name: '김간호',
  status: 'submitted',
  created_at: '2024-01-15T15:00:00',
  attachments: [
    { id: 1, filename: '현장사진.jpg', size: 245000 },
    { id: 2, filename: '환자동의서.pdf', size: 128000 },
  ],
  approvals: [
    { level: 'L1_QPS', status: 'APPROVED', approver: '박QI담당', decided_at: '2024-01-16T10:00:00' },
    { level: 'L2_VICE_CHAIR', status: 'PENDING', approver: null, decided_at: null },
  ],
}

const gradeLabels: Record<string, string> = {
  NEAR_MISS: '근접오류',
  NO_HARM: '위해없음',
  MILD: '경증',
  MODERATE: '중등도',
  SEVERE: '중증',
  DEATH: '사망',
}

const categoryLabels: Record<string, string> = {
  fall: '낙상',
  medication: '투약',
  pressure_ulcer: '욕창',
  infection: '감염',
  medical_device: '의료기기',
  surgery: '수술',
  transfusion: '수혈',
  other: '기타',
}

const approvalLevelLabels: Record<string, string> = {
  L1_QPS: 'QI담당자 (L1)',
  L2_VICE_CHAIR: '부원장 (L2)',
  L3_DIRECTOR: '원장 (L3)',
}

export default function IncidentDetail() {
  const { id } = useParams()

  // TODO: Replace with actual API call
  // const { data: incident, isLoading } = useQuery({
  //   queryKey: ['incident', id],
  //   queryFn: () => incidentApi.get(Number(id)),
  // })

  const incident = mockIncident

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back Button */}
      <Link
        to="/incidents"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="h-4 w-4" />
        목록으로
      </Link>

      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            사고 보고서 #{incident.id}
          </h1>
          <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              {formatDate(incident.occurred_at)}
            </span>
            <span className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              {incident.location}
            </span>
            {incident.reporter_name && (
              <span className="flex items-center gap-1">
                <User className="h-4 w-4" />
                {incident.reporter_name}
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <span className="badge bg-blue-100 text-blue-800">
            {categoryLabels[incident.category]}
          </span>
          <span className="badge bg-yellow-100 text-yellow-800">
            {gradeLabels[incident.grade]}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-3">사고 내용</h2>
            <p className="text-gray-700 whitespace-pre-wrap">
              {incident.description}
            </p>
          </div>

          {/* Immediate Action */}
          <div className="card border-l-4 border-l-amber-500">
            <h2 className="text-lg font-semibold mb-3">즉시 조치</h2>
            <p className="text-gray-700 whitespace-pre-wrap">
              {incident.immediate_action}
            </p>
          </div>

          {/* Root Cause */}
          {incident.root_cause && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-3">근본 원인 분석</h2>
              <p className="text-gray-700 whitespace-pre-wrap">
                {incident.root_cause}
              </p>
            </div>
          )}

          {/* Improvements */}
          {incident.improvements && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-3">개선 방안</h2>
              <p className="text-gray-700 whitespace-pre-wrap">
                {incident.improvements}
              </p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Approval Status */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">승인 현황</h2>
            <div className="space-y-4">
              {incident.approvals.map((approval, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3"
                >
                  {approval.status === 'APPROVED' ? (
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                  ) : approval.status === 'REJECTED' ? (
                    <XCircle className="h-5 w-5 text-red-500 mt-0.5" />
                  ) : (
                    <Clock className="h-5 w-5 text-gray-400 mt-0.5" />
                  )}
                  <div>
                    <p className="font-medium text-gray-900">
                      {approvalLevelLabels[approval.level]}
                    </p>
                    {approval.status === 'APPROVED' && (
                      <p className="text-sm text-gray-500">
                        {approval.approver} • {approval.decided_at && formatDate(approval.decided_at)}
                      </p>
                    )}
                    {approval.status === 'PENDING' && (
                      <p className="text-sm text-gray-500">승인 대기 중</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Attachments */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">첨부파일</h2>
            {incident.attachments.length > 0 ? (
              <ul className="space-y-2">
                {incident.attachments.map((file) => (
                  <li key={file.id}>
                    <button
                      className="w-full flex items-center gap-3 p-2 rounded-md hover:bg-gray-50 text-left"
                      onClick={() => {
                        // TODO: Download file
                        alert('파일 다운로드 기능 구현 예정')
                      }}
                    >
                      <FileText className="h-5 w-5 text-gray-400" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {file.filename}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                      <Download className="h-4 w-4 text-gray-400" />
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">첨부파일이 없습니다</p>
            )}
          </div>

          {/* Metadata */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">정보</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">보고일시</dt>
                <dd className="text-gray-900">{formatDate(incident.reported_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">등록일시</dt>
                <dd className="text-gray-900">{formatDate(incident.created_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">상태</dt>
                <dd className="text-gray-900">{incident.status}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}
