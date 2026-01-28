import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Pencil, Trash2, Loader2, UserCog, Check, X } from 'lucide-react'
import { lookupApi } from '@/utils/api'
import type { Department, Physician } from '@/types'

export default function PhysicianManagement() {
  const queryClient = useQueryClient()
  const [isAdding, setIsAdding] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    department_id: 0,
    license_number: '',
    specialty: '',
  })
  const [filterDepartmentId, setFilterDepartmentId] = useState<number | null>(null)

  // Fetch departments for dropdown
  const { data: deptData } = useQuery({
    queryKey: ['departments', 'active'],
    queryFn: () => lookupApi.listDepartments(true),
  })
  const departments: Department[] = deptData?.data || []

  // Fetch all departments for display
  const { data: allDeptData } = useQuery({
    queryKey: ['departments', 'all'],
    queryFn: () => lookupApi.listDepartments(false),
  })
  const allDepartments: Department[] = allDeptData?.data || []
  const departmentMap = new Map(allDepartments.map(d => [d.id, d.name]))

  // Fetch physicians
  const { data, isLoading, error } = useQuery({
    queryKey: ['physicians', filterDepartmentId],
    queryFn: () => lookupApi.listPhysicians({
      department_id: filterDepartmentId || undefined,
      active_only: false,
    }),
  })
  const physicians: Physician[] = data?.data || []

  // Create mutation
  const createMutation = useMutation({
    mutationFn: lookupApi.createPhysician,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['physicians'] })
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      setIsAdding(false)
      setFormData({ name: '', department_id: 0, license_number: '', specialty: '' })
      alert('주치의가 추가되었습니다.')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      alert(error.response?.data?.detail || '추가에 실패했습니다.')
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Physician> & { is_active?: boolean } }) =>
      lookupApi.updatePhysician(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['physicians'] })
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      setEditingId(null)
      setFormData({ name: '', department_id: 0, license_number: '', specialty: '' })
      alert('주치의 정보가 수정되었습니다.')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      alert(error.response?.data?.detail || '수정에 실패했습니다.')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: lookupApi.deletePhysician,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['physicians'] })
      queryClient.invalidateQueries({ queryKey: ['departments'] })
      alert('주치의가 삭제되었습니다.')
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      alert(error.response?.data?.detail || '삭제에 실패했습니다.')
    },
  })

  const handleAdd = () => {
    if (!formData.name.trim()) {
      alert('주치의 이름을 입력해주세요.')
      return
    }
    if (!formData.department_id) {
      alert('진료과를 선택해주세요.')
      return
    }
    createMutation.mutate({
      name: formData.name,
      department_id: formData.department_id,
      license_number: formData.license_number || undefined,
      specialty: formData.specialty || undefined,
    })
  }

  const handleUpdate = (id: number) => {
    if (!formData.name.trim()) {
      alert('주치의 이름을 입력해주세요.')
      return
    }
    if (!formData.department_id) {
      alert('진료과를 선택해주세요.')
      return
    }
    updateMutation.mutate({
      id,
      data: {
        name: formData.name,
        department_id: formData.department_id,
        license_number: formData.license_number || undefined,
        specialty: formData.specialty || undefined,
      },
    })
  }

  const handleToggleActive = (physician: Physician) => {
    updateMutation.mutate({ id: physician.id, data: { is_active: !physician.isActive } })
  }

  const handleDelete = (id: number) => {
    if (confirm('정말 삭제하시겠습니까?')) {
      deleteMutation.mutate(id)
    }
  }

  const startEdit = (physician: Physician) => {
    setEditingId(physician.id)
    setFormData({
      name: physician.name,
      department_id: physician.departmentId,
      license_number: physician.licenseNumber || '',
      specialty: physician.specialty || '',
    })
  }

  const cancelEdit = () => {
    setEditingId(null)
    setFormData({ name: '', department_id: 0, license_number: '', specialty: '' })
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
          <UserCog className="h-6 w-6 text-teal-600" />
          <h1 className="text-2xl font-bold text-gray-900">주치의 관리</h1>
        </div>
        <button
          onClick={() => {
            setIsAdding(true)
            setFormData({ name: '', department_id: 0, license_number: '', specialty: '' })
          }}
          disabled={isAdding}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          주치의 추가
        </button>
      </div>

      {/* Filter by department */}
      <div className="flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">진료과 필터:</label>
        <select
          value={filterDepartmentId || ''}
          onChange={(e) => setFilterDepartmentId(e.target.value ? Number(e.target.value) : null)}
          className="input-field w-48"
        >
          <option value="">전체</option>
          {allDepartments.map((dept) => (
            <option key={dept.id} value={dept.id}>
              {dept.name}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                이름
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                진료과
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                면허번호
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                전문분야
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
                    placeholder="주치의 이름"
                    className="input-field w-full"
                    autoFocus
                  />
                </td>
                <td className="px-6 py-4">
                  <select
                    value={formData.department_id || ''}
                    onChange={(e) => setFormData({ ...formData, department_id: Number(e.target.value) })}
                    className="input-field w-full"
                  >
                    <option value="">진료과 선택</option>
                    {departments.map((dept) => (
                      <option key={dept.id} value={dept.id}>
                        {dept.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-6 py-4">
                  <input
                    type="text"
                    value={formData.license_number}
                    onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
                    placeholder="면허번호 (선택)"
                    className="input-field w-full"
                  />
                </td>
                <td className="px-6 py-4">
                  <input
                    type="text"
                    value={formData.specialty}
                    onChange={(e) => setFormData({ ...formData, specialty: e.target.value })}
                    placeholder="전문분야 (선택)"
                    className="input-field w-full"
                  />
                </td>
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
                        setFormData({ name: '', department_id: 0, license_number: '', specialty: '' })
                      }}
                      className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            )}

            {/* Existing physicians */}
            {physicians.map((physician) => (
              <tr key={physician.id} className={!physician.isActive ? 'bg-gray-50 opacity-60' : ''}>
                <td className="px-6 py-4">
                  {editingId === physician.id ? (
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input-field w-full"
                      autoFocus
                    />
                  ) : (
                    <span className="text-sm font-medium text-gray-900">{physician.name}</span>
                  )}
                </td>
                <td className="px-6 py-4">
                  {editingId === physician.id ? (
                    <select
                      value={formData.department_id || ''}
                      onChange={(e) => setFormData({ ...formData, department_id: Number(e.target.value) })}
                      className="input-field w-full"
                    >
                      <option value="">진료과 선택</option>
                      {departments.map((dept) => (
                        <option key={dept.id} value={dept.id}>
                          {dept.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span className="text-sm text-gray-500">
                      {departmentMap.get(physician.departmentId) || '-'}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4">
                  {editingId === physician.id ? (
                    <input
                      type="text"
                      value={formData.license_number}
                      onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
                      placeholder="면허번호"
                      className="input-field w-full"
                    />
                  ) : (
                    <span className="text-sm text-gray-500">{physician.licenseNumber || '-'}</span>
                  )}
                </td>
                <td className="px-6 py-4">
                  {editingId === physician.id ? (
                    <input
                      type="text"
                      value={formData.specialty}
                      onChange={(e) => setFormData({ ...formData, specialty: e.target.value })}
                      placeholder="전문분야"
                      className="input-field w-full"
                    />
                  ) : (
                    <span className="text-sm text-gray-500">{physician.specialty || '-'}</span>
                  )}
                </td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => handleToggleActive(physician)}
                    disabled={updateMutation.isPending}
                    className={`px-2 py-1 text-xs rounded-full ${
                      physician.isActive
                        ? 'bg-green-100 text-green-800 hover:bg-green-200'
                        : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                    }`}
                  >
                    {physician.isActive ? '활성' : '비활성'}
                  </button>
                </td>
                <td className="px-6 py-4 text-right">
                  {editingId === physician.id ? (
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleUpdate(physician.id)}
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
                        onClick={() => startEdit(physician)}
                        className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(physician.id)}
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

            {physicians.length === 0 && !isAdding && (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                  등록된 주치의가 없습니다. 주치의를 추가해주세요.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Help text */}
      <div className="text-sm text-gray-500 space-y-1">
        <p>* 주치의를 삭제하면 복구할 수 없습니다.</p>
        <p>* 비활성화된 주치의는 사고 보고 폼에서 선택할 수 없습니다.</p>
        <p>* 진료과가 비활성화되면 해당 진료과의 주치의도 선택할 수 없습니다.</p>
      </div>
    </div>
  )
}
