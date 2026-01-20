import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Play,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Calendar,
  User,
  FileCheck,
} from 'lucide-react'
import { actionApi } from '@/utils/api'
import { useAuth } from '@/hooks/useAuth'
import type { ActionStatus, ActionPriority } from '@/types'
import {
  ACTION_STATUS_LABELS,
  ACTION_STATUS_COLORS,
  ACTION_PRIORITY_LABELS,
  ACTION_PRIORITY_COLORS,
} from '@/types'
import ActionForm from './ActionForm'

// API Response types (snake_case)
interface ApiAction {
  id: number
  incident_id: number
  title: string
  description?: string
  owner: string
  due_date: string
  definition_of_done: string
  priority: ActionPriority
  status: ActionStatus
  evidence_attachment_id?: number
  completed_at?: string
  completed_by_id?: number
  completion_notes?: string
  verified_at?: string
  verified_by_id?: number
  verification_notes?: string
  created_by_id: number
  created_at: string
  updated_at: string
  is_overdue: boolean
}

interface Props {
  incidentId: number
  incidentStatus: string
}

export default function ActionList({ incidentId }: Props) {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [showForm, setShowForm] = useState(false)
  const [selectedAction, setSelectedAction] = useState<ApiAction | null>(null)
  const [completeModal, setCompleteModal] = useState<ApiAction | null>(null)
  const [verifyModal, setVerifyModal] = useState<ApiAction | null>(null)
  const [completionNotes, setCompletionNotes] = useState('')
  const [verificationNotes, setVerificationNotes] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['actions', incidentId],
    queryFn: async () => {
      const response = await actionApi.listByIncident(incidentId)
      return response.data as { items: ApiAction[]; total: number }
    },
  })

  const startMutation = useMutation({
    mutationFn: (actionId: number) => actionApi.start(actionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions', incidentId] })
    },
  })

  const completeMutation = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes?: string }) =>
      actionApi.complete(id, { completion_notes: notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions', incidentId] })
      setCompleteModal(null)
      setCompletionNotes('')
    },
  })

  const verifyMutation = useMutation({
    mutationFn: ({ id, notes }: { id: number; notes?: string }) =>
      actionApi.verify(id, { verification_notes: notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions', incidentId] })
      setVerifyModal(null)
      setVerificationNotes('')
    },
  })

  const cancelMutation = useMutation({
    mutationFn: (actionId: number) => actionApi.cancel(actionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions', incidentId] })
    },
  })

  const canManageActions = user?.role && ['qps_staff', 'vice_chair', 'director', 'master'].includes(user.role)
  const canVerify = user?.role && ['qps_staff', 'vice_chair', 'director', 'master'].includes(user.role)

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  }

  const actions = data?.items ?? []

  const handleFormClose = () => {
    setShowForm(false)
    setSelectedAction(null)
  }

  const handleFormSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['actions', incidentId] })
    handleFormClose()
  }

  if (showForm || selectedAction) {
    return (
      <ActionForm
        incidentId={incidentId}
        action={selectedAction}
        onClose={handleFormClose}
        onSuccess={handleFormSuccess}
      />
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">개선 조치 (CAPA)</h3>
        {canManageActions && (
          <button
            onClick={() => setShowForm(true)}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            <Plus className="h-4 w-4" />
            조치 추가
          </button>
        )}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
        </div>
      )}

      {/* Empty State */}
      {!isLoading && actions.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <FileCheck className="h-12 w-12 mx-auto text-gray-300 mb-3" />
          <p>등록된 개선 조치가 없습니다</p>
          {canManageActions && (
            <button
              onClick={() => setShowForm(true)}
              className="mt-3 text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              첫 번째 조치 추가하기
            </button>
          )}
        </div>
      )}

      {/* Action List */}
      {!isLoading && actions.length > 0 && (
        <div className="space-y-3">
          {actions.map((action) => (
            <div
              key={action.id}
              className={`border rounded-lg p-4 ${
                action.is_overdue ? 'border-red-300 bg-red-50' : 'border-gray-200'
              }`}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-gray-900">{action.title}</h4>
                    {action.is_overdue && (
                      <span className="flex items-center gap-1 text-red-600 text-xs">
                        <AlertTriangle className="h-3 w-3" />
                        기한 초과
                      </span>
                    )}
                  </div>
                  {action.description && (
                    <p className="text-sm text-gray-600 mt-1">{action.description}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <span className={`badge ${ACTION_PRIORITY_COLORS[action.priority]}`}>
                    {ACTION_PRIORITY_LABELS[action.priority]}
                  </span>
                  <span className={`badge ${ACTION_STATUS_COLORS[action.status]}`}>
                    {ACTION_STATUS_LABELS[action.status]}
                  </span>
                </div>
              </div>

              {/* Info */}
              <div className="flex flex-wrap gap-4 text-sm text-gray-500 mb-3">
                <span className="flex items-center gap-1">
                  <User className="h-4 w-4" />
                  {action.owner}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  기한: {formatDate(action.due_date)}
                </span>
              </div>

              {/* DoD */}
              <div className="bg-gray-50 rounded p-2 mb-3">
                <p className="text-xs text-gray-500 mb-1">완료 기준 (DoD)</p>
                <p className="text-sm text-gray-700">{action.definition_of_done}</p>
              </div>

              {/* Completion/Verification Notes */}
              {action.completion_notes && (
                <div className="bg-green-50 rounded p-2 mb-3">
                  <p className="text-xs text-green-600 mb-1">완료 메모</p>
                  <p className="text-sm text-green-800">{action.completion_notes}</p>
                </div>
              )}
              {action.verification_notes && (
                <div className="bg-purple-50 rounded p-2 mb-3">
                  <p className="text-xs text-purple-600 mb-1">검증 메모</p>
                  <p className="text-sm text-purple-800">{action.verification_notes}</p>
                </div>
              )}

              {/* Actions */}
              {canManageActions && (
                <div className="flex flex-wrap gap-2 pt-2 border-t">
                  {action.status === 'open' && (
                    <>
                      <button
                        onClick={() => startMutation.mutate(action.id)}
                        disabled={startMutation.isPending}
                        className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                      >
                        <Play className="h-4 w-4" />
                        시작
                      </button>
                      <button
                        onClick={() => setSelectedAction(action)}
                        className="text-sm text-gray-600 hover:text-gray-700"
                      >
                        수정
                      </button>
                      <button
                        onClick={() => {
                          if (confirm('정말 취소하시겠습니까?')) {
                            cancelMutation.mutate(action.id)
                          }
                        }}
                        className="text-sm text-red-600 hover:text-red-700"
                      >
                        취소
                      </button>
                    </>
                  )}
                  {action.status === 'in_progress' && (
                    <>
                      <button
                        onClick={() => setCompleteModal(action)}
                        className="text-sm text-green-600 hover:text-green-700 flex items-center gap-1"
                      >
                        <CheckCircle className="h-4 w-4" />
                        완료
                      </button>
                      <button
                        onClick={() => setSelectedAction(action)}
                        className="text-sm text-gray-600 hover:text-gray-700"
                      >
                        수정
                      </button>
                      <button
                        onClick={() => {
                          if (confirm('정말 취소하시겠습니까?')) {
                            cancelMutation.mutate(action.id)
                          }
                        }}
                        className="text-sm text-red-600 hover:text-red-700"
                      >
                        취소
                      </button>
                    </>
                  )}
                  {action.status === 'completed' && canVerify && action.completed_by_id !== user?.id && (
                    <button
                      onClick={() => setVerifyModal(action)}
                      className="text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1"
                    >
                      <FileCheck className="h-4 w-4" />
                      검증
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Complete Modal */}
      {completeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold mb-4">조치 완료</h3>
            <p className="text-sm text-gray-600 mb-4">
              "{completeModal.title}" 조치를 완료 처리합니다.
            </p>
            <textarea
              placeholder="완료 메모 (선택사항)"
              value={completionNotes}
              onChange={(e) => setCompletionNotes(e.target.value)}
              className="input-field w-full mb-4"
              rows={3}
            />
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setCompleteModal(null)
                  setCompletionNotes('')
                }}
                className="flex-1 btn-secondary"
              >
                취소
              </button>
              <button
                onClick={() => completeMutation.mutate({ id: completeModal.id, notes: completionNotes })}
                disabled={completeMutation.isPending}
                className="flex-1 btn-primary flex items-center justify-center gap-2"
              >
                {completeMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle className="h-4 w-4" />
                )}
                완료
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Verify Modal */}
      {verifyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold mb-4">조치 검증</h3>
            <p className="text-sm text-gray-600 mb-4">
              "{verifyModal.title}" 조치가 완료 기준을 충족하는지 검증합니다.
            </p>
            <div className="bg-gray-50 rounded p-3 mb-4">
              <p className="text-xs text-gray-500 mb-1">완료 기준 (DoD)</p>
              <p className="text-sm text-gray-700">{verifyModal.definition_of_done}</p>
            </div>
            <textarea
              placeholder="검증 메모 (선택사항)"
              value={verificationNotes}
              onChange={(e) => setVerificationNotes(e.target.value)}
              className="input-field w-full mb-4"
              rows={3}
            />
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setVerifyModal(null)
                  setVerificationNotes('')
                }}
                className="flex-1 btn-secondary"
              >
                취소
              </button>
              <button
                onClick={() => verifyMutation.mutate({ id: verifyModal.id, notes: verificationNotes })}
                disabled={verifyMutation.isPending}
                className="flex-1 bg-purple-600 text-white rounded-md px-4 py-2 hover:bg-purple-700 flex items-center justify-center gap-2"
              >
                {verifyMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileCheck className="h-4 w-4" />
                )}
                검증 완료
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
