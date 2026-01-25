import { useMemo } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Grid3X3, AlertTriangle, List } from 'lucide-react'
import { riskApi } from '@/utils/api'
import type { RiskLevel } from '@/types'
import { RISK_LEVEL_LABELS, RISK_LEVEL_COLORS } from '@/types'

interface MatrixCell {
  probability: number
  severity: number
  count: number
  riskIds: number[]
  level: RiskLevel
}

// Cell background colors based on level
const CELL_BG_COLORS: Record<RiskLevel, string> = {
  low: 'bg-green-100 hover:bg-green-200',
  medium: 'bg-yellow-100 hover:bg-yellow-200',
  high: 'bg-orange-200 hover:bg-orange-300',
  critical: 'bg-red-200 hover:bg-red-300',
}

// Probability labels (Y-axis)
const PROBABILITY_LABELS = [
  { value: 5, label: '5 - 거의 확실' },
  { value: 4, label: '4 - 높음' },
  { value: 3, label: '3 - 보통' },
  { value: 2, label: '2 - 낮음' },
  { value: 1, label: '1 - 드묾' },
]

// Severity labels (X-axis)
const SEVERITY_LABELS = [
  { value: 1, label: '1\n경미' },
  { value: 2, label: '2\n보통' },
  { value: 3, label: '3\n중대' },
  { value: 4, label: '4\n심각' },
  { value: 5, label: '5\n치명적' },
]

export default function RiskMatrix() {
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['risk-matrix'],
    queryFn: () => riskApi.getMatrix(),
  })

  const matrixData = useMemo(() => {
    if (!data?.data?.matrix) return null

    // Transform API response - matrix is [probability][severity]
    // API returns matrix[0] = P=1, we need to reverse for display (P=5 at top)
    const rawMatrix = data.data.matrix as Array<Array<{
      probability: number
      severity: number
      count: number
      risk_ids: number[]
      level: string
    }>>

    // Create 5x5 matrix (reversed: P=5 at row 0)
    const matrix: MatrixCell[][] = []
    for (let p = 5; p >= 1; p--) {
      const row: MatrixCell[] = []
      for (let s = 1; s <= 5; s++) {
        const apiCell = rawMatrix[p - 1]?.[s - 1]
        row.push({
          probability: p,
          severity: s,
          count: apiCell?.count || 0,
          riskIds: apiCell?.risk_ids || [],
          level: (apiCell?.level || 'low') as RiskLevel,
        })
      }
      matrix.push(row)
    }

    return matrix
  }, [data])

  const levelCounts = data?.data?.by_level || { low: 0, medium: 0, high: 0, critical: 0 }
  const totalRisks = data?.data?.total_risks || 0

  const handleCellClick = (cell: MatrixCell) => {
    if (cell.count > 0) {
      // Navigate to risk list filtered by these risks
      // For now, just navigate to the first risk
      navigate(`/risks/${cell.riskIds[0]}`)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/risks')}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Grid3X3 className="h-6 w-6 text-orange-600" />
              5×5 위험 매트릭스
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              발생가능성(P) × 심각도(S) 기반 위험 분포
            </p>
          </div>
        </div>

        <Link to="/risks" className="btn-secondary flex items-center gap-2">
          <List className="h-4 w-4" />
          목록으로
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-5 gap-4">
        <div className="card p-4 text-center">
          <div className="text-3xl font-bold text-gray-900">{totalRisks}</div>
          <div className="text-sm text-gray-500">전체 위험</div>
        </div>
        {(['critical', 'high', 'medium', 'low'] as RiskLevel[]).map((level) => (
          <div key={level} className="card p-4 text-center">
            <div className="text-3xl font-bold text-gray-900">
              {levelCounts[level] || 0}
            </div>
            <div className={`badge ${RISK_LEVEL_COLORS[level]} mt-1`}>
              {RISK_LEVEL_LABELS[level]}
            </div>
          </div>
        ))}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      )}

      {/* Matrix */}
      {!isLoading && matrixData && (
        <div className="card p-6">
          <div className="flex">
            {/* Y-axis Label */}
            <div className="flex items-center justify-center w-12 mr-2">
              <span className="text-sm font-medium text-gray-700 -rotate-90 whitespace-nowrap">
                발생가능성 (P)
              </span>
            </div>

            {/* Y-axis values + Matrix */}
            <div className="flex-1">
              <div className="flex">
                {/* Y-axis values */}
                <div className="flex flex-col gap-1 mr-2">
                  {PROBABILITY_LABELS.map((p) => (
                    <div
                      key={p.value}
                      className="h-20 flex items-center justify-end pr-2 text-sm text-gray-600"
                    >
                      {p.label}
                    </div>
                  ))}
                </div>

                {/* Matrix Grid */}
                <div className="flex-1">
                  <div className="grid grid-cols-5 gap-1">
                    {matrixData.flatMap((row, rowIndex) =>
                      row.map((cell, colIndex) => (
                        <button
                          key={`${rowIndex}-${colIndex}`}
                          onClick={() => handleCellClick(cell)}
                          disabled={cell.count === 0}
                          className={`
                            h-20 rounded-lg flex flex-col items-center justify-center
                            transition-all
                            ${CELL_BG_COLORS[cell.level]}
                            ${cell.count > 0 ? 'cursor-pointer shadow-sm' : 'cursor-default'}
                          `}
                        >
                          {cell.count > 0 ? (
                            <>
                              <AlertTriangle
                                className={`h-6 w-6 ${
                                  cell.level === 'critical'
                                    ? 'text-red-700'
                                    : cell.level === 'high'
                                    ? 'text-orange-700'
                                    : cell.level === 'medium'
                                    ? 'text-yellow-700'
                                    : 'text-green-700'
                                }`}
                              />
                              <span className="font-bold text-lg text-gray-900">
                                {cell.count}
                              </span>
                            </>
                          ) : (
                            <span className="text-gray-400 text-sm">-</span>
                          )}
                        </button>
                      ))
                    )}
                  </div>

                  {/* X-axis values */}
                  <div className="grid grid-cols-5 gap-1 mt-2">
                    {SEVERITY_LABELS.map((s) => (
                      <div
                        key={s.value}
                        className="text-center text-sm text-gray-600 whitespace-pre-line"
                      >
                        {s.label}
                      </div>
                    ))}
                  </div>

                  {/* X-axis Label */}
                  <div className="text-center mt-4">
                    <span className="text-sm font-medium text-gray-700">심각도 (S)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="mt-8 pt-6 border-t">
            <h3 className="text-sm font-medium text-gray-700 mb-3">범례</h3>
            <div className="flex flex-wrap gap-4">
              {(['low', 'medium', 'high', 'critical'] as RiskLevel[]).map((level) => (
                <div key={level} className="flex items-center gap-2">
                  <div
                    className={`w-6 h-6 rounded ${CELL_BG_COLORS[level].split(' ')[0]}`}
                  />
                  <span className="text-sm text-gray-600">
                    {RISK_LEVEL_LABELS[level]}
                    <span className="text-gray-400 ml-1">
                      (
                      {level === 'low' && '1-4'}
                      {level === 'medium' && '5-9'}
                      {level === 'high' && '10-16'}
                      {level === 'critical' && '17-25'}
                      )
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Score Formula */}
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 mb-2">위험 점수 산출</h3>
            <p className="text-sm text-gray-600">
              위험 점수 = 발생가능성(P) × 심각도(S)
            </p>
            <ul className="mt-2 text-sm text-gray-500 list-disc list-inside">
              <li>저위험 (Low): 1-4점</li>
              <li>중위험 (Medium): 5-9점</li>
              <li>고위험 (High): 10-16점</li>
              <li>극심 (Critical): 17-25점</li>
            </ul>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !matrixData && (
        <div className="card py-12 text-center">
          <Grid3X3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">위험 매트릭스 데이터를 불러올 수 없습니다.</p>
        </div>
      )}
    </div>
  )
}
