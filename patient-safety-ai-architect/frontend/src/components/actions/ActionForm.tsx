import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { ArrowLeft, Save, Loader2 } from 'lucide-react'
import { actionApi } from '@/utils/api'
import type { ActionPriority, ActionStatus } from '@/types'
import { ACTION_PRIORITY_LABELS } from '@/types'

// Validation schema
const actionSchema = z.object({
  title: z.string().min(5, '제목은 5자 이상 입력해주세요').max(200),
  description: z.string().optional(),
  owner: z.string().min(2, '담당자를 2자 이상 입력해주세요').max(100),
  due_date: z.string().min(1, '기한을 입력해주세요'),
  definition_of_done: z.string().min(10, '완료 기준을 10자 이상 입력해주세요'),
  priority: z.enum(['low', 'medium', 'high', 'critical']),
})

type ActionFormData = z.infer<typeof actionSchema>

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
}

interface Props {
  incidentId: number
  action?: ApiAction | null
  onClose: () => void
  onSuccess: () => void
}

export default function ActionForm({ incidentId, action, onClose, onSuccess }: Props) {
  const isEdit = !!action

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ActionFormData>({
    resolver: zodResolver(actionSchema),
    defaultValues: action
      ? {
          title: action.title,
          description: action.description || '',
          owner: action.owner,
          due_date: action.due_date,
          definition_of_done: action.definition_of_done,
          priority: action.priority,
        }
      : {
          priority: 'medium',
          due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 week from now
        },
  })

  const createMutation = useMutation({
    mutationFn: (data: ActionFormData) =>
      actionApi.create({
        incident_id: incidentId,
        ...data,
      }),
    onSuccess: () => {
      alert('조치가 등록되었습니다.')
      onSuccess()
    },
    onError: () => {
      alert('등록에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: ActionFormData) => actionApi.update(action!.id, data),
    onSuccess: () => {
      alert('조치가 수정되었습니다.')
      onSuccess()
    },
    onError: () => {
      alert('수정에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const onSubmit = (data: ActionFormData) => {
    if (isEdit) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={onClose}
          className="p-1 text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <h3 className="text-lg font-semibold">
          {isEdit ? '조치 수정' : '새 조치 추가'}
        </h3>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            조치 제목 *
          </label>
          <input
            {...register('title')}
            type="text"
            placeholder="예: 낙상예방 교육 실시"
            className="input-field mt-1"
          />
          {errors.title && (
            <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
          )}
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            상세 설명
          </label>
          <textarea
            {...register('description')}
            rows={2}
            placeholder="조치에 대한 상세 설명 (선택사항)"
            className="input-field mt-1"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Owner */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              담당자 *
            </label>
            <input
              {...register('owner')}
              type="text"
              placeholder="홍길동"
              className="input-field mt-1"
            />
            {errors.owner && (
              <p className="mt-1 text-sm text-red-600">{errors.owner.message}</p>
            )}
          </div>

          {/* Due Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              기한 *
            </label>
            <input
              {...register('due_date')}
              type="date"
              className="input-field mt-1"
            />
            {errors.due_date && (
              <p className="mt-1 text-sm text-red-600">{errors.due_date.message}</p>
            )}
          </div>
        </div>

        {/* Priority */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            우선순위 *
          </label>
          <select {...register('priority')} className="input-field mt-1">
            {(Object.keys(ACTION_PRIORITY_LABELS) as ActionPriority[]).map((p) => (
              <option key={p} value={p}>
                {ACTION_PRIORITY_LABELS[p]}
              </option>
            ))}
          </select>
        </div>

        {/* Definition of Done */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            완료 기준 (DoD) *
          </label>
          <textarea
            {...register('definition_of_done')}
            rows={3}
            placeholder="이 조치가 완료되었음을 판단할 수 있는 구체적인 기준을 작성해주세요"
            className="input-field mt-1"
          />
          {errors.definition_of_done && (
            <p className="mt-1 text-sm text-red-600">{errors.definition_of_done.message}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            예: "전 직원 대상 낙상예방 교육 완료, 교육 참석자 명단 및 교육 자료 첨부"
          </p>
        </div>

        {/* Buttons */}
        <div className="flex gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 btn-secondary"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="flex-1 btn-primary flex items-center justify-center gap-2"
          >
            {isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            {isEdit ? '수정' : '저장'}
          </button>
        </div>
      </form>
    </div>
  )
}
