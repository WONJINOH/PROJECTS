import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import {
  AlertTriangle,
  ArrowLeft,
  Edit,
  History,
  ArrowUpRight,
  Calendar,
  User,
  Clock,
  FileText,
} from 'lucide-react'
import { riskApi } from '@/utils/api'
import type { Risk, RiskAssessment, RiskAssessmentType, RiskLevel, RiskStatus } from '@/types'
import {
  RISK_LEVEL_LABELS,
  RISK_LEVEL_COLORS,
  RISK_STATUS_LABELS,
  RISK_STATUS_COLORS,
  RISK_CATEGORY_LABELS,
  RISK_SOURCE_TYPE_LABELS,
  RISK_ASSESSMENT_TYPE_LABELS,
} from '@/types'

function transformRisk(item: Record<string, unknown>): Risk {
  return {
    id: item.id as number,
    riskCode: item.risk_code as string,
    title: item.title as string,
    description: item.description as string,
    sourceType: item.source_type as Risk['sourceType'],
    sourceIncidentId: item.source_incident_id as number | undefined,
    sourceDetail: item.source_detail as string | undefined,
    category: item.category as Risk['category'],
    currentControls: item.current_controls as string | undefined,
    probability: item.probability as number,
    severity: item.severity as number,
    riskScore: item.risk_score as number,
    riskLevel: item.risk_level as RiskLevel,
    residualProbability: item.residual_probability as number | undefined,
    residualSeverity: item.residual_severity as number | undefined,
    residualScore: item.residual_score as number | undefined,
    residualLevel: item.residual_level as RiskLevel | undefined,
    ownerId: item.owner_id as number,
    targetDate: item.target_date as string | undefined,
    status: item.status as RiskStatus,
    autoEscalated: item.auto_escalated as boolean,
    escalationReason: item.escalation_reason as string | undefined,
    createdById: item.created_by_id as number,
    createdAt: item.created_at as string,
    updatedAt: item.updated_at as string,
    closedAt: item.closed_at as string | undefined,
    closedById: item.closed_by_id as number | undefined,
  }
}

function transformAssessment(item: Record<string, unknown>): RiskAssessment {
  return {
    id: item.id as number,
    riskId: item.risk_id as number,
    assessmentType: item.assessment_type as RiskAssessmentType,
    assessedAt: item.assessed_at as string,
    assessorId: item.assessor_id as number,
    probability: item.probability as number,
    severity: item.severity as number,
    score: item.score as number,
    level: item.level as RiskLevel,
    rationale: item.rationale as string | undefined,
  }
}

export default function RiskDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showAssessmentForm, setShowAssessmentForm] = useState(false)
  const [assessmentForm, setAssessmentForm] = useState({
    assessment_type: 'periodic' as RiskAssessmentType,
    probability: 1,
    severity: 1,
    rationale: '',
  })

  // Fetch risk
  const { data: riskData, isLoading: riskLoading } = useQuery({
    queryKey: ['risk', id],
    queryFn: () => riskApi.get(Number(id)),
    enabled: Boolean(id),
  })

  // Fetch assessments
  const { data: assessmentsData } = useQuery({
    queryKey: ['risk-assessments', id],
    queryFn: () => riskApi.listAssessments(Number(id)),
    enabled: Boolean(id),
  })

  const risk = riskData?.data ? transformRisk(riskData.data) : null
  const assessments: RiskAssessment[] = assessmentsData?.data
    ? assessmentsData.data.map(transformAssessment)
    : []

  // Create assessment mutation
  const assessmentMutation = useMutation({
    mutationFn: (data: typeof assessmentForm) =>
      riskApi.createAssessment(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk', id] })
      queryClient.invalidateQueries({ queryKey: ['risk-assessments', id] })
      setShowAssessmentForm(false)
      setAssessmentForm({
        assessment_type: 'periodic',
        probability: 1,
        severity: 1,
        rationale: '',
      })
    },
  })

  // Status update mutation
  const statusMutation = useMutation({
    mutationFn: (status: RiskStatus) =>
      riskApi.update(Number(id), { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk', id] })
      queryClient.invalidateQueries({ queryKey: ['risks'] })
    },
  })

  if (riskLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!risk) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500">위험을 찾을 수 없습니다.</p>
        <Link to="/risks" className="text-primary-600 hover:text-primary-800 mt-4 inline-block">
          목록으로 돌아가기
        </Link>
      </div>
    )
  }

  const newScore = assessmentForm.probability * assessmentForm.severity

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/risks')}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-gray-500">{risk.riskCode}</span>
              {risk.autoEscalated && (
                <span className="inline-flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                  <ArrowUpRight className="h-3 w-3" />
                  자동 승격
                </span>
              )}
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mt-1">{risk.title}</h1>
          </div>
        </div>

        <div className="flex gap-2">
          <Link
            to={`/risks/${id}/edit`}
            className="btn-secondary flex items-center gap-2"
          >
            <Edit className="h-4 w-4" />
            수정
          </Link>
        </div>
      </div>

      {/* Status and Risk Level */}
      <div className="grid grid-cols-2 gap-6">
        {/* Current Risk */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">현재 위험도</h2>
          <div className="flex items-center justify-between mb-4">
            <div className="text-center">
              <div className="text-3xl font-bold font-mono">
                {risk.probability}×{risk.severity}={risk.riskScore}
              </div>
              <div className="text-sm text-gray-500 mt-1">P × S = Score</div>
            </div>
            <span className={`badge text-lg px-4 py-2 ${RISK_LEVEL_COLORS[risk.riskLevel]}`}>
              {RISK_LEVEL_LABELS[risk.riskLevel]}
            </span>
          </div>

          {/* Residual Risk if exists */}
          {risk.residualScore && (
            <div className="border-t pt-4 mt-4">
              <h3 className="text-sm font-medium text-gray-500 mb-2">잔여 위험</h3>
              <div className="flex items-center justify-between">
                <div className="font-mono">
                  {risk.residualProbability}×{risk.residualSeverity}={risk.residualScore}
                </div>
                {risk.residualLevel && (
                  <span className={`badge ${RISK_LEVEL_COLORS[risk.residualLevel]}`}>
                    {RISK_LEVEL_LABELS[risk.residualLevel]}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Status */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">상태</h2>
          <div className="flex items-center justify-between mb-4">
            <span className={`badge text-lg px-4 py-2 ${RISK_STATUS_COLORS[risk.status]}`}>
              {RISK_STATUS_LABELS[risk.status]}
            </span>
          </div>

          {/* Status Transition Buttons */}
          <div className="space-y-2">
            {risk.status === 'identified' && (
              <button
                onClick={() => statusMutation.mutate('assessing')}
                className="btn-secondary w-full"
                disabled={statusMutation.isPending}
              >
                평가 시작
              </button>
            )}
            {risk.status === 'assessing' && (
              <button
                onClick={() => statusMutation.mutate('treating')}
                className="btn-secondary w-full"
                disabled={statusMutation.isPending}
              >
                조치 시작
              </button>
            )}
            {risk.status === 'treating' && (
              <button
                onClick={() => statusMutation.mutate('monitoring')}
                className="btn-secondary w-full"
                disabled={statusMutation.isPending}
              >
                모니터링 전환
              </button>
            )}
            {risk.status === 'monitoring' && (
              <>
                <button
                  onClick={() => statusMutation.mutate('closed')}
                  className="btn-primary w-full"
                  disabled={statusMutation.isPending}
                >
                  종결
                </button>
                <button
                  onClick={() => statusMutation.mutate('accepted')}
                  className="btn-secondary w-full"
                  disabled={statusMutation.isPending}
                >
                  잔여위험 수용
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Details */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">상세 정보</h2>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500">설명</h3>
            <p className="mt-1 text-gray-900 whitespace-pre-wrap">{risk.description}</p>
          </div>

          <div className="space-y-4">
            <div className="flex items-start gap-2">
              <FileText className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <div className="text-sm text-gray-500">분류</div>
                <div className="font-medium">{RISK_CATEGORY_LABELS[risk.category]}</div>
              </div>
            </div>

            <div className="flex items-start gap-2">
              <ArrowUpRight className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <div className="text-sm text-gray-500">출처</div>
                <div className="font-medium">{RISK_SOURCE_TYPE_LABELS[risk.sourceType]}</div>
                {risk.sourceDetail && (
                  <div className="text-sm text-gray-500">{risk.sourceDetail}</div>
                )}
                {risk.sourceIncidentId && (
                  <Link
                    to={`/incidents/${risk.sourceIncidentId}`}
                    className="text-sm text-primary-600 hover:text-primary-800"
                  >
                    PSR #{risk.sourceIncidentId}
                  </Link>
                )}
              </div>
            </div>

            <div className="flex items-start gap-2">
              <User className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <div className="text-sm text-gray-500">담당자 ID</div>
                <div className="font-medium">{risk.ownerId}</div>
              </div>
            </div>

            {risk.targetDate && (
              <div className="flex items-start gap-2">
                <Calendar className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <div className="text-sm text-gray-500">목표 완료일</div>
                  <div className="font-medium">{risk.targetDate}</div>
                </div>
              </div>
            )}

            <div className="flex items-start gap-2">
              <Clock className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <div className="text-sm text-gray-500">등록일</div>
                <div className="font-medium">
                  {format(new Date(risk.createdAt), 'yyyy-MM-dd HH:mm', { locale: ko })}
                </div>
              </div>
            </div>
          </div>
        </div>

        {risk.currentControls && (
          <div className="mt-6 pt-6 border-t">
            <h3 className="text-sm font-medium text-gray-500 mb-2">현재 통제 방법</h3>
            <p className="text-gray-900 whitespace-pre-wrap">{risk.currentControls}</p>
          </div>
        )}

        {risk.escalationReason && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <h3 className="text-sm font-medium text-blue-800">승격 사유</h3>
            <p className="text-sm text-blue-700 mt-1">{risk.escalationReason}</p>
          </div>
        )}
      </div>

      {/* Assessment History */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <History className="h-5 w-5" />
            평가 이력
          </h2>
          <button
            onClick={() => setShowAssessmentForm(!showAssessmentForm)}
            className="btn-secondary"
          >
            새 평가 추가
          </button>
        </div>

        {/* Assessment Form */}
        {showAssessmentForm && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  평가 유형
                </label>
                <select
                  value={assessmentForm.assessment_type}
                  onChange={(e) =>
                    setAssessmentForm((prev) => ({
                      ...prev,
                      assessment_type: e.target.value as RiskAssessmentType,
                    }))
                  }
                  className="input-field"
                >
                  <option value="periodic">정기 재평가</option>
                  <option value="post_treatment">조치 후 재평가</option>
                  <option value="post_incident">사건 발생 후 재평가</option>
                </select>
              </div>

              <div className="flex gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">P</label>
                  <select
                    value={assessmentForm.probability}
                    onChange={(e) =>
                      setAssessmentForm((prev) => ({
                        ...prev,
                        probability: Number(e.target.value),
                      }))
                    }
                    className="input-field w-20"
                  >
                    {[1, 2, 3, 4, 5].map((n) => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">S</label>
                  <select
                    value={assessmentForm.severity}
                    onChange={(e) =>
                      setAssessmentForm((prev) => ({
                        ...prev,
                        severity: Number(e.target.value),
                      }))
                    }
                    className="input-field w-20"
                  >
                    {[1, 2, 3, 4, 5].map((n) => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </div>
                <div className="flex items-end">
                  <span className="text-sm text-gray-500 pb-2">= {newScore}</span>
                </div>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                평가 근거
              </label>
              <textarea
                value={assessmentForm.rationale}
                onChange={(e) =>
                  setAssessmentForm((prev) => ({
                    ...prev,
                    rationale: e.target.value,
                  }))
                }
                rows={2}
                className="input-field"
                placeholder="평가 근거를 입력하세요"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowAssessmentForm(false)}
                className="btn-secondary"
              >
                취소
              </button>
              <button
                onClick={() => assessmentMutation.mutate(assessmentForm)}
                disabled={assessmentMutation.isPending}
                className="btn-primary"
              >
                {assessmentMutation.isPending ? '저장 중...' : '저장'}
              </button>
            </div>
          </div>
        )}

        {/* Assessment List */}
        <div className="space-y-3">
          {assessments.map((assessment) => (
            <div
              key={assessment.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-4">
                <div>
                  <span className="text-sm font-medium text-gray-900">
                    {RISK_ASSESSMENT_TYPE_LABELS[assessment.assessmentType]}
                  </span>
                  <div className="text-xs text-gray-500">
                    {format(new Date(assessment.assessedAt), 'yyyy-MM-dd HH:mm', {
                      locale: ko,
                    })}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <span className="font-mono text-sm">
                  {assessment.probability}×{assessment.severity}={assessment.score}
                </span>
                <span className={`badge ${RISK_LEVEL_COLORS[assessment.level]}`}>
                  {RISK_LEVEL_LABELS[assessment.level]}
                </span>
              </div>
            </div>
          ))}

          {assessments.length === 0 && (
            <p className="text-center text-gray-500 py-4">평가 이력이 없습니다.</p>
          )}
        </div>
      </div>
    </div>
  )
}
