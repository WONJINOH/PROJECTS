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
import { AlertTriangle, FileText, CheckCircle, Clock } from 'lucide-react'
import { api } from '@/utils/api'

// Mock data for dashboard (replace with API calls)
const mockStats = {
  total: 156,
  thisMonth: 23,
  pending: 12,
  approved: 144,
}

const mockCategoryData = [
  { name: '낙상', value: 45, color: '#3b82f6' },
  { name: '투약', value: 38, color: '#ef4444' },
  { name: '욕창', value: 28, color: '#f97316' },
  { name: '감염', value: 25, color: '#22c55e' },
  { name: '기타', value: 20, color: '#94a3b8' },
]

const mockMonthlyData = [
  { month: '1월', count: 12 },
  { month: '2월', count: 15 },
  { month: '3월', count: 18 },
  { month: '4월', count: 14 },
  { month: '5월', count: 22 },
  { month: '6월', count: 19 },
]

const mockRecentIncidents = [
  { id: 1, category: '낙상', grade: 'MILD', location: '301호', date: '2024-01-15' },
  { id: 2, category: '투약', grade: 'NEAR_MISS', location: '402호', date: '2024-01-14' },
  { id: 3, category: '욕창', grade: 'MODERATE', location: '205호', date: '2024-01-13' },
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

export default function Dashboard() {
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
          value={mockStats.total}
          icon={FileText}
          color="blue"
        />
        <StatCard
          title="이번 달"
          value={mockStats.thisMonth}
          icon={AlertTriangle}
          color="orange"
        />
        <StatCard
          title="승인 대기"
          value={mockStats.pending}
          icon={Clock}
          color="yellow"
        />
        <StatCard
          title="처리 완료"
          value={mockStats.approved}
          icon={CheckCircle}
          color="green"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Trend */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">월별 사고 추이</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockMonthlyData}>
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
                  data={mockCategoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                >
                  {mockCategoryData.map((entry, index) => (
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
        <h2 className="text-lg font-semibold mb-4">최근 사고 보고</h2>
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
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {mockRecentIncidents.map((incident) => (
                <tr key={incident.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    #{incident.id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
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
                    {incident.date}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

interface StatCardProps {
  title: string
  value: number
  icon: React.ComponentType<{ className?: string }>
  color: 'blue' | 'orange' | 'yellow' | 'green'
}

function StatCard({ title, value, icon: Icon, color }: StatCardProps) {
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
        <p className="text-2xl font-semibold text-gray-900">{value}</p>
      </div>
    </div>
  )
}
