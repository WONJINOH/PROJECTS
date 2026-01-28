import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, Loader2, Building2, Check, X } from 'lucide-react'
import { lookupApi } from '@/utils/api'
import type { Department } from '@/types'

export default function DepartmentManagement() {
  const queryClient = useQueryClient()
  const [isAdding, setIsAdding] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({ name: '', code: '' })

  // Fetch departments
  const { data, isLoading, error } = useQuery({
    queryKey: ['departments', 'all'],
    queryFn: () => lookupApi.listDepartments(false), // Include inactive
  })
  const departments: Department[] = data?.data || []

  // Create mutation
  const createMutation = useMutation({
    mutationFn: lookupApi.createDepartment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      setIsAdding(false)
      setFormData({ name: '', code: '' })
      alert('진료과가 추가되었습니다.')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      alert(error.response?.data?.detail || '추가에 실패했습니다.')
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { name?: string; code?: string; is_active?: boolean } }) =>
      lookupApi.updateDepartment(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      setEditingId(null)
      setFormData({ name: '', code: '' })
      alert('진료과가 수정되었습니다.')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      alert(error.response?.data?.detail || '수정에 실패했습니다.')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: lookupApi.deleteDepartment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      alert('진료과가 삭제되었습니다.')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      alert(error.response?.data?.detail || '삭제에 실패했습니다.')
    },
  })

  const handleAdd = () => {
    if (!formData.name.trim()) {
      alert('진료과 이름을 입력해주세요.')
      return
    }
    createMutation.mutate({ name: formData.name, code: formData.code || undefined })
  }

  const handleUpdate = (id: number) => {
    if (!formData.name.trim()) {
      alert('진료과 이름을 입력해주세요.')
      return
    }
    updateMutation.mutate({ id, data: { name: formData.name, code: formData.code || undefined } })
  }

  const handleToggleActive = (dept: Department) => {
    updateMutation.mutate({ id: dept.id, data: { is_active: !dept.isActive } })
  }

  const handleDelete = (id: number) => {
    if (confirm('정말 삭제하시겠습니까? 연결된 주치의가 있으면 삭제가 불가능합니다.')) {
      deleteMutation.mutate(id)
    }
  }

  const startEdit = (dept: Department) => {
    setEditingId(dept.id)
    setFormData({ name: dept.name, code: dept.code || '' })
  }

  const cancelEdit = () => {
    setEditingId(null)
    setFormData({ name: '', code: '' })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-teal-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-600">
        데이터를 불러오는데 실패했습니다.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Building2 className="h-6 w-6 text-teal-600" />
          <h1 className="text-2xl font-bold text-gray-900">진료과 관리</h1>
        </div>
        <button
          onClick={() => {
            setIsAdding(true)
            setFormData({ name: '', code: '' })
          }}
          disabled={isAdding}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          진료과 추가
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                진료과명
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                코드
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                주치의 수
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                상태
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                작업
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {/* Add new row */}
            {isAdding && (
              <tr className="bg-teal-50">
                <td className="px-6 py-4">
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="진료과 이름"
                    className="input-field w-full"
                    autoFocus
                  />
                </td>
                <td className="px-6 py-4">
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    placeholder="코드 (선택)"
                    className="input-field w-full"
                  />
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">-</td>
                <td className="px-6 py-4 text-sm text-gray-500">신규</td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={handleAdd}
                      disabled={createMutation.isPending}
                      className="p-2 text-green-600 hover:bg-green-100 rounded-lg"
                    >
                      {createMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                    </button>
                    <button
                      onClick={() => {
                        setIsAdding(false)
                        setFormData({ name: '', code: '' })
                      }}
                      className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            )}

            {/* Existing departments */}
            {departments.map((dept) => (
              <tr key={dept.id} className={!dept.isActive ? 'bg-gray-50 opacity-60' : ''}>
                <td className="px-6 py-4">
                  {editingId === dept.id ? (
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input-field w-full"
                      autoFocus
                    />
                  ) : (
                    <span className="text-sm font-medium text-gray-900">{dept.name}</span>
                  )}
                </td>
                <td className="px-6 py-4">
                  {editingId === dept.id ? (
                    <input
                      type="text"
                      value={formData.code}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                      placeholder="코드"
                      className="input-field w-full"
                    />
                  ) : (
                    <span className="text-sm text-gray-500">{dept.code || '-'}</span>
                  )}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {dept.physicianCount || 0}명
                </td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => handleToggleActive(dept)}
                    disabled={updateMutation.isPending}
                    className={`px-2 py-1 text-xs rounded-full ${
                      dept.isActive
                        ? 'bg-green-100 text-green-800 hover:bg-green-200'
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                  >
                    {dept.isActive ? '활성' : '비활성'}
                  </button>
                </td>
                <td className="px-6 py-4 text-right">
                  {editingId === dept.id ? (
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleUpdate(dept.id)}
                        disabled={updateMutation.isPending}
                        className="p-2 text-green-600 hover:bg-green-100 rounded-lg"
                      >
                        {updateMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Check className="h-4 w-4" />
                        )}
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => startEdit(dept)}
                        className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(dept.id)}
                        disabled={deleteMutation.isPending}
                        className="p-2 text-red-600 hover:bg-red-100 rounded-lg"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}

            {departments.length === 0 && !isAdding && (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                  등록된 진료과가 없습니다. 진료과를 추가해주세요.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Help text */}
      <div className="text-sm text-gray-500 space-y-1">
        <p>* 진료과를 삭제하면 복구할 수 없습니다. 연결된 주치의가 있으면 삭제가 불가능합니다.</p>
        <p>* 비활성화된 진료과는 사고 보고 폼에서 선택할 수 없습니다.</p>
      </div>
    </div>
  )
}
