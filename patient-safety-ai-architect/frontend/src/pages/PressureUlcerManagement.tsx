import { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  HeartPulse,
  Search,
  Filter,
  Activity,
  TrendingUp,
  TrendingDown,
  Users,
  CheckCircle,
  Calculator,
  RefreshCw,
  Plus,
} from 'lucide-react'
import { pressureUlcerManagementApi } from '@/utils/api'
import { useAuth } from '@/hooks/useAuth'
import { WARD_OPTIONS } from '@/types'

// Types
interface PressureUlcerPatientSummary {
  id: number
  patient_code: string
  patient_name?: string
  patient_gender?: string
  room_number?: string
  department: string
  ulcer_id: string
  location: string
  location_label: string
  origin: string
  origin_label: string
  grade?: string
  grade_label?: string
  discovery_date: string
  push_total?: number
  latest_assessment_date?: string
  latest_push_total?: number
  is_active: boolean
  end_reason?: string
  end_date?: string
}

interface StatsResponse {
  total_active: number
  total_healed: number
  total_closed: number
  acquired_count: number
  admission_count: number
  by_grade: Record<string, number>
  by_location: Record<string, number>
  by_department: Record<string, number>
  improvement_rate?: number
}

const ORIGIN_OPTIONS = [
  { value: '', label: '전체' },
  { value: 'admission', label: '입원 시 보유' },
  { value: 'acquired', label: '재원 중 발생' },
]

export default function PressureUlcerManagement() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [searchTerm, setSearchTerm] = useState('')
  const [activeOnly, setActiveOnly] = useState(true)
  const [originFilter, setOriginFilter] = useState('')
  const [departmentFilter, setDepartmentFilter] = useState(user?.department || '')
  const [showCalcModal, setShowCalcModal] = useState(false)
  const [calcYear, setCalcYear] = useState(new Date().getFullYear())
  const [calcMonth, setCalcMonth] = useState(new Date().getMonth() + 1)
  const [calcResult, setCalcResult] = useState<{
    numerator: number
    denominator: number
    rate: number
    improved_push: number
    improved_grade: number
    saved_to_indicator: boolean
  } | null>(null)

  const queryClient = useQueryClient()

  // Fetch patient list
  const { data: patientData, isLoading: isLoadingPatients } = useQuery({
    queryKey: ['pressureUlcerPatients', activeOnly, originFilter],
    queryFn: () =>
      pressureUlcerManagementApi.listPatients({
        active_only: activeOnly,
        origin: originFilter || undefined,
        limit: 100,
      }),
  })

  // Fetch statistics
  const { data: statsData, isLoading: isLoadingStats } = useQuery({
    queryKey: ['pressureUlcerStats'],
    queryFn: () => pressureUlcerManagementApi.getStats(),
  })

  const patients: PressureUlcerPatientSummary[] = useMemo(() => {
    if (!patientData?.data?.items) return []
    return patientData.data.items
  }, [patientData])

  const stats: StatsResponse | null = useMemo(() => {
    if (!statsData?.data) return null
    return statsData.data
  }, [statsData])

  // Improvement rate calculation mutation
  const calcMutation = useMutation({
    mutationFn: (data: { year: number; month: number }) =>
      pressureUlcerManagementApi.calculateImprovementRate(data),
    onSuccess: (response) => {
      setCalcResult(response.data)
      queryClient.invalidateQueries({ queryKey: ['pressureUlcerStats'] })
    },
    onError: (error: Error) => {
      alert(`호전율 계산 실패: ${error.message}`)
    },
  })

  const filteredPatients = useMemo(() => {
    if (!searchTerm) return patients
    const term = searchTerm.toLowerCase()
    return patients.filter(
      (p) =>
        p.patient_code.toLowerCase().includes(term) ||
        p.patient_name?.toLowerCase().includes(term) ||
        p.room_number?.toLowerCase().includes(term) ||
        p.department.toLowerCase().includes(term)
    )
  }, [patients, searchTerm])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <HeartPulse className="h-6 w-6 text-rose-600" />
            욕창 관리
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            입원시 보유/재원 중 발생 욕창 환자 관리 및 PUSH 평가 기록
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCalcModal(true)}
            className="btn-secondary flex items-center gap-2"
          >
            <Calculator className="h-4 w-4" />
            호전율 계산
          </button>
          <button
            onClick={() => navigate('/pressure-ulcer-management/new')}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            욕창발생보고서 작성
          </button>
        </div>
      </div>

      {/* Improvement Rate Calculation Modal */}
      {showCalcModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              월별 욕창 호전율 계산
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              선택한 월의 첫째주 평가 기록을 기반으로 호전율을 계산합니다.
            </p>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  연도
                </label>
                <select
                  value={calcYear}
                  onChange={(e) => setCalcYear(Number(e.target.value))}
                  className="input-field"
                >
                  {[2024, 2025, 2026, 2027].map((y) => (
                    <option key={y} value={y}>{y}년</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  월
                </label>
                <select
                  value={calcMonth}
                  onChange={(e) => setCalcMonth(Number(e.target.value))}
                  className="input-field"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                    <option key={m} value={m}>{m}월</option>
                  ))}
                </select>
              </div>
            </div>

            {calcResult && (
              <div className="bg-rose-50 border border-rose-200 rounded-lg p-4 mb-4">
                <h3 className="font-medium text-rose-900 mb-2">계산 결과</h3>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">호전율:</span>
                    <span className="font-bold text-rose-700">{calcResult.rate}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">호전 건수:</span>
                    <span>{calcResult.numerator}건</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">전월말 활성:</span>
                    <span>{calcResult.denominator}건</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">PUSH 호전:</span>
                    <span>{calcResult.improved_push}건</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">등급 호전:</span>
                    <span>{calcResult.improved_grade}건</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">지표 저장:</span>
                    <span className={calcResult.saved_to_indicator ? 'text-green-600' : 'text-gray-500'}>
                      {calcResult.saved_to_indicator ? '✓ 저장됨' : '저장 실패'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowCalcModal(false)
                  setCalcResult(null)
                }}
                className="btn-secondary"
              >
                닫기
              </button>
              <button
                onClick={() => calcMutation.mutate({ year: calcYear, month: calcMonth })}
                disabled={calcMutation.isPending}
                className="btn-primary flex items-center gap-2"
              >
                {calcMutation.isPending ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Calculator className="h-4 w-4" />
                )}
                {calcMutation.isPending ? '계산 중...' : '계산 실행'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Statistics Cards */}
      {!isLoadingStats && stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card bg-rose-50 border-rose-200">
            <div className="flex items-center gap-3">
              <Activity className="h-8 w-8 text-rose-600" />
              <div>
                <div className="text-sm text-rose-600">활성 환자</div>
                <div className="text-2xl font-bold text-rose-900">
                  {stats.total_active}
                </div>
              </div>
            </div>
          </div>

          <div className="card bg-green-50 border-green-200">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div>
                <div className="text-sm text-green-600">치유 완료</div>
                <div className="text-2xl font-bold text-green-900">
                  {stats.total_healed}
                </div>
              </div>
            </div>
          </div>

          <div className="card bg-blue-50 border-blue-200">
            <div className="flex items-center gap-3">
              <Users className="h-8 w-8 text-blue-600" />
              <div>
                <div className="text-sm text-blue-600">재원 중 발생</div>
                <div className="text-2xl font-bold text-blue-900">
                  {stats.acquired_count}
                </div>
              </div>
            </div>
          </div>

          <div className="card bg-amber-50 border-amber-200">
            <div className="flex items-center gap-3">
              {stats.improvement_rate !== null && stats.improvement_rate !== undefined ? (
                stats.improvement_rate > 0 ? (
                  <TrendingUp className="h-8 w-8 text-amber-600" />
                ) : (
                  <TrendingDown className="h-8 w-8 text-amber-600" />
                )
              ) : (
                <TrendingUp className="h-8 w-8 text-amber-600" />
              )}
              <div>
                <div className="text-sm text-amber-600">호전율</div>
                <div className="text-2xl font-bold text-amber-900">
                  {stats.improvement_rate !== null && stats.improvement_rate !== undefined
                    ? `${stats.improvement_rate}%`
                    : '-'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Distribution Stats */}
      {!isLoadingStats && stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* By Grade */}
          <div className="card">
            <h3 className="font-medium text-gray-900 mb-3">등급별 현황</h3>
            <div className="space-y-2">
              {Object.entries(stats.by_grade).map(([grade, count]) => (
                <div key={grade} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{grade}</span>
                  <span className="font-medium text-gray-900">{count}건</span>
                </div>
              ))}
              {Object.keys(stats.by_grade).length === 0 && (
                <p className="text-sm text-gray-500">데이터 없음</p>
              )}
            </div>
          </div>

          {/* By Location */}
          <div className="card">
            <h3 className="font-medium text-gray-900 mb-3">부위별 현황</h3>
            <div className="space-y-2">
              {Object.entries(stats.by_location).map(([location, count]) => (
                <div key={location} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{location}</span>
                  <span className="font-medium text-gray-900">{count}건</span>
                </div>
              ))}
              {Object.keys(stats.by_location).length === 0 && (
                <p className="text-sm text-gray-500">데이터 없음</p>
              )}
            </div>
          </div>

          {/* By Department */}
          <div className="card">
            <h3 className="font-medium text-gray-900 mb-3">부서별 현황</h3>
            <div className="space-y-2">
              {Object.entries(stats.by_department).map(([dept, count]) => (
                <div key={dept} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{dept}</span>
                  <span className="font-medium text-gray-900">{count}건</span>
                </div>
              ))}
              {Object.keys(stats.by_department).length === 0 && (
                <p className="text-sm text-gray-500">데이터 없음</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Search and Filter */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="환자 코드, 이름, 병실, 부서 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={activeOnly}
                onChange={(e) => setActiveOnly(e.target.checked)}
                className="rounded text-rose-600 focus:ring-rose-500"
              />
              <span className="text-sm text-gray-700">활성 환자만</span>
            </label>
            <select
              value={originFilter}
              onChange={(e) => setOriginFilter(e.target.value)}
              className="input-field w-36"
            >
              {ORIGIN_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Patient List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            환자 목록
            <span className="ml-2 text-sm font-normal text-gray-500">
              {filteredPatients.length}건
            </span>
          </h2>
        </div>

        {isLoadingPatients ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rose-600"></div>
          </div>
        ) : filteredPatients.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    환자
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    병실/부서
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    부위
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    등급
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    발생시점
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    PUSH
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    최근평가
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                    상태
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredPatients.map((patient) => (
                  <tr key={patient.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link
                        to={`/pressure-ulcer-management/${patient.id}`}
                        className="text-rose-600 hover:text-rose-800 font-medium"
                      >
                        {patient.patient_code}
                      </Link>
                      {patient.patient_name && (
                        <div className="text-sm text-gray-500">
                          {patient.patient_name}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="text-gray-900">{patient.room_number || '-'}</div>
                      <div className="text-gray-500">{patient.department}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {patient.location_label}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-rose-100 text-rose-800">
                        {patient.grade_label || '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {patient.origin_label}
                      <div className="text-gray-500">
                        {formatDate(patient.discovery_date)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="font-mono text-sm font-medium">
                        {patient.latest_push_total ?? patient.push_total ?? '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {patient.latest_assessment_date
                        ? formatDate(patient.latest_assessment_date)
                        : '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {patient.is_active ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          활성
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          {patient.end_reason === 'healed'
                            ? '치유'
                            : patient.end_reason === 'death'
                            ? '사망'
                            : patient.end_reason === 'discharge'
                            ? '퇴원'
                            : patient.end_reason === 'transfer'
                            ? '전원'
                            : '종료'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <HeartPulse className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">등록된 욕창 환자가 없습니다.</p>
          </div>
        )}
      </div>
    </div>
  )
}
