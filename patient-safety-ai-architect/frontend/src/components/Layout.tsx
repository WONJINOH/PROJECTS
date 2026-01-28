import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useMemo } from 'react'
import {
  LayoutDashboard,
  FileText,
  FilePlus,
  ClipboardList,
  LogOut,
  BarChart2,
  AlertTriangle,
  Users,
  HeartPulse,
  Mail,
  ChevronRight,
  Building2,
  UserCog,
} from 'lucide-react'
import type { UserRole } from '@/types'

// Navigation items with role-based visibility
interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  allowedRoles: UserRole[]
}

const navigation: NavItem[] = [
  {
    name: '대시보드',
    href: '/dashboard',
    icon: LayoutDashboard,
    allowedRoles: ['reporter', 'qps_staff', 'vice_chair', 'director', 'master']
  },
  {
    name: '사고 보고',
    href: '/incidents/new',
    icon: FilePlus,
    allowedRoles: ['reporter', 'qps_staff', 'vice_chair', 'director', 'master']
  },
  {
    name: '사고 목록',
    href: '/incidents',
    icon: FileText,
    allowedRoles: ['reporter', 'qps_staff', 'vice_chair', 'director', 'master']
  },
  {
    name: '지표 관리',
    href: '/indicators',
    icon: BarChart2,
    allowedRoles: ['qps_staff', 'vice_chair', 'director', 'master']
  },
  {
    name: '위험 관리',
    href: '/risks',
    icon: AlertTriangle,
    allowedRoles: ['qps_staff', 'vice_chair', 'director', 'master']
  },
  {
    name: '욕창 관리',
    href: '/pressure-ulcer-management',
    icon: HeartPulse,
    allowedRoles: ['qps_staff', 'vice_chair', 'director', 'master']
  },
  {
    name: '사용자 관리',
    href: '/users',
    icon: Users,
    allowedRoles: ['admin', 'master']
  },
  {
    name: '진료과 관리',
    href: '/admin/departments',
    icon: Building2,
    allowedRoles: ['admin', 'master']
  },
  {
    name: '주치의 관리',
    href: '/admin/physicians',
    icon: UserCog,
    allowedRoles: ['admin', 'master']
  },
  {
    name: '접근 로그',
    href: '/access-log',
    icon: ClipboardList,
    allowedRoles: ['admin', 'qps_staff', 'vice_chair', 'director', 'master']
  },
]

// Role display names
const roleLabels: Record<UserRole, string> = {
  reporter: '보고자',
  qps_staff: 'QPS 담당자',
  vice_chair: '부위원장',
  director: '위원장',
  admin: '시스템 관리자',
  master: '최고 관리자',
}

export default function Layout() {
  const location = useLocation()
  const { user, logout } = useAuth()

  // Filter navigation based on user role
  const visibleNavigation = useMemo(() => {
    if (!user?.role) return []
    return navigation.filter(item =>
      item.allowedRoles.includes(user.role as UserRole)
    )
  }, [user?.role])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-teal-50/30">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-50 w-72 bg-white/80 backdrop-blur-xl border-r border-slate-200/60 shadow-xl shadow-slate-200/20 flex flex-col">
        {/* Logo Section */}
        <div className="h-20 px-6 flex items-center gap-3 border-b border-slate-100 bg-gradient-to-r from-teal-600 to-teal-700">
          <div className="relative">
            <div className="w-11 h-11 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center shadow-lg shadow-teal-900/20">
              <HeartPulse className="h-6 w-6 text-white" strokeWidth={2.5} />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white shadow-sm" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-white text-lg tracking-tight leading-tight">
              환자안전
            </span>
            <span className="text-teal-100 text-xs font-medium tracking-wide">
              QI REPORTING SYSTEM
            </span>
          </div>
        </div>

        {/* User Profile Card */}
        <div className="px-4 py-4">
          <div className="bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-xl p-4 border border-slate-200/60">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-white font-semibold text-sm shadow-md">
                {user?.fullName?.charAt(0) || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-800 truncate">
                  {user?.fullName || '사용자'}
                </p>
                <p className="text-xs text-teal-600 font-medium">
                  {roleLabels[user?.role as UserRole] || '역할'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
          <p className="px-3 py-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            메뉴
          </p>
          {visibleNavigation.map((item) => {
            const isActive = location.pathname === item.href ||
              (item.href !== '/dashboard' && location.pathname.startsWith(item.href))
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-teal-500 to-teal-600 text-white shadow-lg shadow-teal-500/25'
                    : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-900'
                }`}
              >
                <item.icon className={`h-5 w-5 transition-transform duration-200 ${
                  isActive ? 'text-white' : 'text-slate-400 group-hover:text-teal-600'
                } group-hover:scale-110`} />
                <span className="flex-1">{item.name}</span>
                {isActive && (
                  <ChevronRight className="h-4 w-4 text-white/70" />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Logout Button */}
        <div className="px-4 py-3 border-t border-slate-100">
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all duration-200 group"
          >
            <LogOut className="h-4 w-4 group-hover:scale-110 transition-transform" />
            <span>로그아웃</span>
          </button>
        </div>

        {/* Footer */}
        <div className="px-4 py-4 bg-gradient-to-b from-slate-50/50 to-slate-100/80 border-t border-slate-200/60">
          <div className="space-y-2.5 text-center">
            <p className="text-[10px] text-slate-400 font-medium">
              © 2026 Patient Safety QI System
            </p>
            <p className="text-[10px] text-slate-500">
              Developed by <span className="font-semibold text-teal-700">WONJIN OH</span>
            </p>
            <div className="flex items-center justify-center gap-1.5 text-[10px] text-slate-400">
              <Mail className="h-3 w-3" />
              <a
                href="mailto:nara.qps38@gmail.com"
                className="hover:text-teal-600 transition-colors underline decoration-dotted underline-offset-2"
              >
                nara.qps38@gmail.com
              </a>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="pl-72">
        {/* Top gradient line */}
        <div className="h-1 bg-gradient-to-r from-teal-400 via-teal-500 to-emerald-500" />

        <main className="p-8 min-h-[calc(100vh-4px)]">
          <Outlet />
        </main>

        {/* Bottom Footer for main content area */}
        <footer className="px-8 py-4 border-t border-slate-200/60 bg-white/50">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <p>본 시스템은 내부 QI 활동 전용입니다. 무단 접근 시 법적 책임이 있을 수 있습니다.</p>
            <p className="flex items-center gap-1.5">
              문의:
              <a
                href="mailto:nara.qps38@gmail.com"
                className="text-teal-600 hover:text-teal-700 font-medium transition-colors"
              >
                시스템관리자
              </a>
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}
