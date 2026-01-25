import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { AlertTriangle, FileText, CheckCircle, Clock, Search, Clipboard } from 'lucide-react'
import { dashboardApi } from '@/utils/api'

interface RecentIncident {
  id: number
  category: string
  category_code: string
  grade: string
  location: string
  original_location: string
  occurred_at: string
  status: string
  has_analysis: boolean
  analysis_type: string | null
}

interface DashboardSummary {
  period: { year: number; month: number }
  kpi: {
    total_incidents: number
    fall_rate: number
    pressure_ulcer_rate: number
    medication_error_rate: number
    infection_rate: number
    hand_hygiene_rate: number
  }
  by_category: Record<string, Record<string, number>>
  trends: { direction: string; change_percent: number }
}

interface PSRData {
  by_classification: { name: string; count: number }[]
  by_severity: { name: string; count: number; color: string }[]
  monthly_trend: { month: string; count: number }[]
}

const gradeColors: Record<string, string> = {
  near_miss: 'badge-near-miss',
  no_harm: 'badge-no-harm',
  mild: 'badge-mild',
  moderate: 'badge-moderate',
  severe: 'badge-severe',
  death: 'badge-death',
}

const gradeLabels: Record<string, string> = {
  near_miss: '근접오류',
  no_harm: '위해없음',
  mild: '경증',
  moderate: '중등도',
  severe: '중증',
  death: '사망',
}

export default function Dashboard() {
  const navigate = useNavigate()

  // API 호출
  const { data: summary } = useQuery<DashboardSummary>({
    queryKey: ['dashboard', 'summary'],
    queryFn: async () => {
      const response = await dashboardApi.getSummary()
      return response.data
    },
  })

  const { data: psrData } = useQuery<PSRData>({
    queryKey: ['dashboard', 'psr'],
    queryFn: async () => {
      const response = await dashboardApi.getPSR()
      return response.data
    },
  })

  const { data: recentIncidents, isLoading: isLoadingIncidents } = useQuery<RecentIncident[]>({
    queryKey: ['dashboard', 'recent-incidents'],
    queryFn: async () => {
      const response = await dashboardApi.getRecentIncidents({ limit: 10 })
      return response.data
    },
  })

  // 카테고리별 색상 (차트용)
  const categoryColors = [
    '#3b82f6', // blue
    '#ef4444', // red
    '#f97316', // orange
    '#22c55e', // green
    '#94a3b8', // gray
  ]

  const categoryData = psrData?.by_classification?.map((item, index) => ({
    ...item,
    color: categoryColors[index % categoryColors.length],
  })) || []

  const monthlyData = psrData?.monthly_trend || []

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
        <p className="mt-1 text-sm text-gray-500">
          환자안전사고 현황을 한눈에 확인하세요
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="전체 사고"
          value={summary?.kpi?.total_incidents || 0}
          icon={FileText}
          color="blue"
        />
        <StatCard
          title="낙상률 (‰)"
          value={summary?.kpi?.fall_rate || 0}
          icon={AlertTriangle}
          color="orange"
          isDecimal
        />
        <StatCard
          title="승인 대기"
          value={summary?.by_category?.psr?.near_miss || 0}
          icon={Clock}
          color="yellow"
        />
        <StatCard
          title="손위생 이행률 (%)"
          value={summary?.kpi?.hand_hygiene_rate || 0}
          icon={CheckCircle}
          color="green"
          isDecimal
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Trend */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">월별 사고 추이</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Distribution */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">유형별 분포</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="count"
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Incidents */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">최근 사고 보고</h2>
          <button
            onClick={() => navigate('/incidents')}
            className="text-sm text-teal-600 hover:text-teal-700 flex items-center gap-1"
          >
            전체 보기
            <span aria-hidden="true">→</span>
          </button>
        </div>

        {isLoadingIncidents ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
          </div>
        ) : recentIncidents && recentIncidents.length > 0 ? (
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
                    날짜
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    분석
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentIncidents.map((incident) => (
                  <tr
                    key={incident.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/incidents/${incident.id}`)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #{incident.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {incident.category}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${gradeColors[incident.grade] || 'bg-gray-100 text-gray-800'}`}>
                        {gradeLabels[incident.grade] || incident.grade}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" title={incident.original_location}>
                      {incident.location}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {incident.occurred_at ? new Date(incident.occurred_at).toLocaleDateString('ko-KR') : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {incident.has_analysis ? (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          <Clipboard className="h-3 w-3" />
                          완료
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                          <Search className="h-3 w-3" />
                          대기
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <FileText className="h-12 w-12 mx-auto mb-2 text-gray-300" />
            <p>등록된 사고 보고가 없습니다.</p>
          </div>
        )}
      </div>
    </div>
  )
}

interface StatCardProps {
  title: string
  value: number
  icon: React.ComponentType<{ className?: string }>
  color: 'blue' | 'orange' | 'yellow' | 'green'
  isDecimal?: boolean
}

function StatCard({ title, value, icon: Icon, color, isDecimal }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    orange: 'bg-orange-50 text-orange-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    green: 'bg-green-50 text-green-600',
  }

  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
        <Icon className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className="text-2xl font-semibold text-gray-900">
          {isDecimal ? value.toFixed(1) : value}
        </p>
      </div>
    </div>
  )
}
