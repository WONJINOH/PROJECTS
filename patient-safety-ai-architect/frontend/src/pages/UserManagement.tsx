import { useState, useEffect } from 'react'
import { api } from '@/utils/api'
import { useAuth } from '@/hooks/useAuth'
import type { UserRole } from '@/types'
import {
  Users,
  UserCheck,
  Clock,
  RefreshCw,
  Shield,
  AlertCircle,
  CheckCircle,
  XCircle,
  ChevronDown,
  Edit3,
  Ban,
  PlayCircle,
  X,
  Save,
} from 'lucide-react'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: UserRole
  department?: string
  is_active: boolean
  status: 'pending' | 'active' | 'dormant' | 'suspended' | 'deleted'
  password_expires_at?: string
  last_login?: string
  created_at: string
  approved_at?: string
}

interface UserListResponse {
  items: User[]
  total: number
  skip: number
  limit: number
}

const STATUS_LABELS: Record<string, string> = {
  pending: '승인 대기',
  active: '활성',
  dormant: '휴면',
  suspended: '정지',
  deleted: '삭제됨',
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-800',
  active: 'bg-emerald-100 text-emerald-800',
  dormant: 'bg-slate-100 text-slate-800',
  suspended: 'bg-red-100 text-red-800',
  deleted: 'bg-gray-100 text-gray-500',
}

const ROLE_LABELS: Record<UserRole, string> = {
  reporter: '보고자',
  qps_staff: 'QPS 담당자',
  vice_chair: '부위원장',
  director: '위원장',
  admin: '시스템 관리자',
  master: '최고 관리자',
}

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: 'reporter', label: '보고자' },
  { value: 'qps_staff', label: 'QPS 담당자' },
  { value: 'vice_chair', label: '부위원장' },
  { value: 'director', label: '위원장' },
  { value: 'admin', label: '시스템 관리자' },
  { value: 'master', label: '최고 관리자' },
]

export default function UserManagement() {
  const { user: currentUser } = useAuth()
  const [activeTab, setActiveTab] = useState<'pending' | 'all'>('pending')
  const [users, setUsers] = useState<User[]>([])
  const [pendingUsers, setPendingUsers] = useState<User[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const [selectedRole, setSelectedRole] = useState<Record<number, UserRole>>({})

  // Edit modal state
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [editForm, setEditForm] = useState({
    full_name: '',
    email: '',
    department: '',
  })

  // Suspend modal state
  const [suspendingUser, setSuspendingUser] = useState<User | null>(null)
  const [suspendReason, setSuspendReason] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  // Clear success message after 3 seconds
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(null), 3000)
      return () => clearTimeout(timer)
    }
    return undefined
  }, [successMessage])

  const loadData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [pendingRes, allRes] = await Promise.all([
        api.get<UserListResponse>('/api/auth/pending-users'),
        api.get<UserListResponse>('/api/auth/users'),
      ])
      setPendingUsers(pendingRes.data.items)
      setUsers(allRes.data.items)
    } catch (err) {
      setError('사용자 목록을 불러오는데 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleApprove = async (userId: number) => {
    setActionLoading(userId)
    try {
      await api.post(`/api/auth/users/${userId}/approve`, {
        action: 'approve',
        role: selectedRole[userId] || 'reporter',
      })
      setSuccessMessage('사용자가 승인되었습니다.')
      await loadData()
    } catch (err) {
      setError('승인 처리에 실패했습니다.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleReject = async (userId: number) => {
    if (!window.confirm('정말 이 가입 신청을 거절하시겠습니까?')) return

    setActionLoading(userId)
    try {
      await api.post(`/api/auth/users/${userId}/approve`, {
        action: 'reject',
        rejection_reason: '관리자에 의해 거절됨',
      })
      setSuccessMessage('가입 신청이 거절되었습니다.')
      await loadData()
    } catch (err) {
      setError('거절 처리에 실패했습니다.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleReactivate = async (userId: number) => {
    setActionLoading(userId)
    try {
      await api.post(`/api/auth/users/${userId}/reactivate`)
      setSuccessMessage('사용자가 재활성화되었습니다.')
      await loadData()
    } catch (err) {
      setError('재활성화에 실패했습니다.')
    } finally {
      setActionLoading(null)
    }
  }

  const handleRoleChange = async (userId: number, newRole: UserRole) => {
    setActionLoading(userId)
    try {
      await api.put(`/api/auth/users/${userId}/role?new_role=${newRole}`)
      setSuccessMessage('역할이 변경되었습니다.')
      await loadData()
    } catch (err) {
      setError('역할 변경에 실패했습니다.')
    } finally {
      setActionLoading(null)
    }
  }

  const openEditModal = (user: User) => {
    setEditingUser(user)
    setEditForm({
      full_name: user.full_name,
      email: user.email,
      department: user.department || '',
    })
  }

  const handleEditSubmit = async () => {
    if (!editingUser) return

    setActionLoading(editingUser.id)
    try {
      await api.put(`/api/auth/users/${editingUser.id}`, {
        full_name: editForm.full_name || undefined,
        email: editForm.email || undefined,
        department: editForm.department || undefined,
      })
      setSuccessMessage('사용자 정보가 수정되었습니다.')
      setEditingUser(null)
      await loadData()
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      if (error.response?.data?.detail === 'Email already in use') {
        setError('이미 사용 중인 이메일입니다.')
      } else {
        setError('사용자 정보 수정에 실패했습니다.')
      }
    } finally {
      setActionLoading(null)
    }
  }

  const openSuspendModal = (user: User) => {
    setSuspendingUser(user)
    setSuspendReason('')
  }

  const handleSuspend = async () => {
    if (!suspendingUser) return

    setActionLoading(suspendingUser.id)
    try {
      await api.post(`/api/auth/users/${suspendingUser.id}/suspend`, {
        reason: suspendReason || undefined,
      })
      setSuccessMessage('사용자가 정지되었습니다.')
      setSuspendingUser(null)
      await loadData()
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      if (error.response?.data?.detail) {
        setError(error.response.data.detail)
      } else {
        setError('사용자 정지에 실패했습니다.')
      }
    } finally {
      setActionLoading(null)
    }
  }

  const handleUnsuspend = async (userId: number) => {
    setActionLoading(userId)
    try {
      await api.post(`/api/auth/users/${userId}/unsuspend`)
      setSuccessMessage('사용자 정지가 해제되었습니다.')
      await loadData()
    } catch (err) {
      setError('정지 해제에 실패했습니다.')
    } finally {
      setActionLoading(null)
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // Check if current user has permission
  const canManageUsers = currentUser?.role === 'admin' || currentUser?.role === 'master'
  if (!canManageUsers) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <Shield className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-red-800 mb-2">접근 권한이 없습니다</h2>
          <p className="text-red-600">사용자 관리는 관리자만 접근할 수 있습니다.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">사용자 관리</h1>
          <p className="text-slate-500 mt-1">가입 신청 승인 및 사용자 권한 관리</p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          새로고침
        </button>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
          <CheckCircle className="h-5 w-5 text-emerald-500" />
          <span className="text-emerald-700">{successMessage}</span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-xl">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <span className="text-red-700">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200">
        <button
          onClick={() => setActiveTab('pending')}
          className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors border-b-2 -mb-px ${
            activeTab === 'pending'
              ? 'border-teal-500 text-teal-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Clock className="h-4 w-4" />
          승인 대기
          {pendingUsers.length > 0 && (
            <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2 py-0.5 rounded-full">
              {pendingUsers.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('all')}
          className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors border-b-2 -mb-px ${
            activeTab === 'all'
              ? 'border-teal-500 text-teal-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Users className="h-4 w-4" />
          전체 사용자
          <span className="bg-slate-100 text-slate-600 text-xs font-semibold px-2 py-0.5 rounded-full">
            {users.length}
          </span>
        </button>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
        </div>
      ) : activeTab === 'pending' ? (
        /* Pending Users */
        pendingUsers.length === 0 ? (
          <div className="text-center py-12 bg-slate-50 rounded-xl">
            <UserCheck className="h-12 w-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">승인 대기 중인 사용자가 없습니다</p>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left text-xs font-semibold text-slate-600 uppercase tracking-wider px-6 py-4">
                    사용자 정보
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-600 uppercase tracking-wider px-6 py-4">
                    부서
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-600 uppercase tracking-wider px-6 py-4">
                    신청일
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-600 uppercase tracking-wider px-6 py-4">
                    역할 지정
                  </th>
                  <th className="text-right text-xs font-semibold text-slate-600 uppercase tracking-wider px-6 py-4">
                    작업
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pendingUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-slate-800">{user.full_name}</p>
                        <p className="text-sm text-slate-500">{user.username}</p>
                        <p className="text-xs text-slate-400">{user.email}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      {user.department || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-500">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="relative">
                        <select
                          value={selectedRole[user.id] || 'reporter'}
                          onChange={(e) => setSelectedRole({
                            ...selectedRole,
                            [user.id]: e.target.value as UserRole,
                          })}
                          className="appearance-none bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500"
                        >
                          {ROLE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleApprove(user.id)}
                          disabled={actionLoading === user.id}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                        >
                          <CheckCircle className="h-4 w-4" />
                          승인
                        </button>
                        <button
                          onClick={() => handleReject(user.id)}
                          disabled={actionLoading === user.id}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-700 hover:bg-red-100 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                        >
                          <XCircle className="h-4 w-4" />
                          거절
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : (
        /* All Users */
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left text-xs font-semibold text-slate-600 uppercase tracking-wider px-6 py-4">
                  사용자 정보
                </th>
                <th className="text-left text-xs font-semibold text-slate-600 uppercase tracking-wider px-6 py-4">
                  역할
                </th>
                <th className="text-left text-xs font-semibold text-slate-600 uppercase tracking-wider px-6 py-4">
                  상태
                </th>
                <th className="text-left text-xs font-semibold text-slate-600 uppercase tracking-wider px-6 py-4">
                  최근 로그인
                </th>
                <th className="text-right text-xs font-semibold text-slate-600 uppercase tracking-wider px-6 py-4">
                  작업
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-medium text-slate-800">{user.full_name}</p>
                      <p className="text-sm text-slate-500">{user.username}</p>
                      <p className="text-xs text-slate-400">{user.email}</p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {user.status === 'active' && user.id !== currentUser?.id ? (
                      <div className="relative">
                        <select
                          value={user.role}
                          onChange={(e) => handleRoleChange(user.id, e.target.value as UserRole)}
                          disabled={actionLoading === user.id}
                          className="appearance-none bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 disabled:opacity-50"
                        >
                          {ROLE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                      </div>
                    ) : (
                      <span className="text-sm text-slate-600">
                        {ROLE_LABELS[user.role]}
                        {user.id === currentUser?.id && (
                          <span className="ml-1.5 text-xs text-teal-600">(본인)</span>
                        )}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[user.status]}`}>
                      {STATUS_LABELS[user.status]}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {formatDate(user.last_login)}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {/* Edit Button */}
                      {user.id !== currentUser?.id && (
                        <button
                          onClick={() => openEditModal(user)}
                          disabled={actionLoading === user.id}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 text-slate-700 hover:bg-slate-100 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                          title="정보 수정"
                        >
                          <Edit3 className="h-4 w-4" />
                          수정
                        </button>
                      )}

                      {/* Status Actions */}
                      {user.status === 'dormant' && (
                        <button
                          onClick={() => handleReactivate(user.id)}
                          disabled={actionLoading === user.id}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-teal-50 text-teal-700 hover:bg-teal-100 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                        >
                          <RefreshCw className={`h-4 w-4 ${actionLoading === user.id ? 'animate-spin' : ''}`} />
                          재활성화
                        </button>
                      )}

                      {user.status === 'active' && user.id !== currentUser?.id && (
                        <button
                          onClick={() => openSuspendModal(user)}
                          disabled={actionLoading === user.id}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-700 hover:bg-red-100 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                          title="정지"
                        >
                          <Ban className="h-4 w-4" />
                          정지
                        </button>
                      )}

                      {user.status === 'suspended' && (
                        <button
                          onClick={() => handleUnsuspend(user.id)}
                          disabled={actionLoading === user.id}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                        >
                          <PlayCircle className="h-4 w-4" />
                          정지 해제
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Edit Modal */}
      {editingUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-800">사용자 정보 수정</h3>
              <button
                onClick={() => setEditingUser(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  사용자명
                </label>
                <input
                  type="text"
                  value={editingUser.username}
                  disabled
                  className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  이름
                </label>
                <input
                  type="text"
                  value={editForm.full_name}
                  onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  이메일
                </label>
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  부서
                </label>
                <input
                  type="text"
                  value={editForm.department}
                  onChange={(e) => setEditForm({ ...editForm, department: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500"
                  placeholder="부서를 입력하세요"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
              <button
                onClick={() => setEditingUser(null)}
                className="px-4 py-2 text-slate-600 hover:text-slate-800 font-medium"
              >
                취소
              </button>
              <button
                onClick={handleEditSubmit}
                disabled={actionLoading === editingUser.id}
                className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 font-medium disabled:opacity-50"
              >
                <Save className="h-4 w-4" />
                저장
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Suspend Modal */}
      {suspendingUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-800">사용자 정지</h3>
              <button
                onClick={() => setSuspendingUser(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="text-amber-800">
                  <strong>{suspendingUser.full_name}</strong> ({suspendingUser.username}) 사용자를 정지하시겠습니까?
                </p>
                <p className="text-sm text-amber-600 mt-1">
                  정지된 사용자는 로그인할 수 없습니다.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  정지 사유 (선택)
                </label>
                <textarea
                  value={suspendReason}
                  onChange={(e) => setSuspendReason(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 resize-none"
                  placeholder="정지 사유를 입력하세요 (선택사항)"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 bg-slate-50">
              <button
                onClick={() => setSuspendingUser(null)}
                className="px-4 py-2 text-slate-600 hover:text-slate-800 font-medium"
              >
                취소
              </button>
              <button
                onClick={handleSuspend}
                disabled={actionLoading === suspendingUser.id}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium disabled:opacity-50"
              >
                <Ban className="h-4 w-4" />
                정지
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
