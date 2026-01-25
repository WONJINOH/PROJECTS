import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { HeartPulse, AlertCircle, User, Lock, LogIn, Mail, UserPlus } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

const loginSchema = z.object({
  username: z.string().min(1, '아이디를 입력해주세요'),
  password: z.string().min(1, '비밀번호를 입력해주세요'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    setError(null)
    setIsLoading(true)

    try {
      await login(data.username, data.password)
      navigate('/dashboard')
    } catch (err) {
      setError('아이디 또는 비밀번호가 올바르지 않습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-teal-50/30 py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-teal-100/40 to-emerald-100/40 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-teal-100/40 to-cyan-100/40 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-teal-50/20 to-emerald-50/20 rounded-full blur-3xl" />
      </div>

      <div className="max-w-md w-full relative z-10">
        {/* Logo Card */}
        <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200/60 p-8 mb-6">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-5">
              <div className="relative">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center shadow-xl shadow-teal-500/30">
                  <HeartPulse className="h-10 w-10 text-white" strokeWidth={2} />
                </div>
                <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-emerald-400 rounded-full border-4 border-white shadow-md flex items-center justify-center">
                  <div className="w-2 h-2 bg-white rounded-full" />
                </div>
              </div>
            </div>
            <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
              환자안전
            </h1>
            <p className="text-sm text-teal-600 font-semibold tracking-wide mt-1">
              QI REPORTING SYSTEM
            </p>
            <div className="w-16 h-1 bg-gradient-to-r from-teal-400 to-emerald-400 mx-auto mt-4 rounded-full" />
          </div>

          {/* Login Form */}
          <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
            {error && (
              <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200/60 rounded-xl text-red-700">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-500" />
                </div>
                <span className="text-sm font-medium">{error}</span>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="username" className="block text-sm font-semibold text-slate-700 mb-2">
                  아이디
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    {...register('username')}
                    id="username"
                    type="text"
                    autoComplete="username"
                    className="w-full pl-12 pr-4 py-3.5 bg-slate-50/80 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all duration-200"
                    placeholder="사원번호를 입력하세요"
                  />
                </div>
                {errors.username && (
                  <p className="mt-2 text-sm text-red-500 font-medium">{errors.username.message}</p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-semibold text-slate-700 mb-2">
                  비밀번호
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    {...register('password')}
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    className="w-full pl-12 pr-4 py-3.5 bg-slate-50/80 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all duration-200"
                    placeholder="비밀번호를 입력하세요"
                  />
                </div>
                {errors.password && (
                  <p className="mt-2 text-sm text-red-500 font-medium">{errors.password.message}</p>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700 text-white font-semibold py-3.5 px-6 rounded-xl shadow-lg shadow-teal-500/25 hover:shadow-xl hover:shadow-teal-500/30 transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed group"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>로그인 중...</span>
                </>
              ) : (
                <>
                  <LogIn className="h-5 w-5 group-hover:translate-x-0.5 transition-transform" />
                  <span>로그인</span>
                </>
              )}
            </button>
          </form>

          {/* Internal Notice */}
          <div className="mt-6 pt-6 border-t border-slate-100">
            <p className="text-center text-xs text-slate-500">
              본 시스템은 <span className="font-semibold text-teal-700">내부 QI 활동 전용</span>입니다
            </p>
            <p className="text-center text-xs text-slate-400 mt-1">
              허가된 사용자만 접근 가능합니다
            </p>
          </div>

          {/* Register Link */}
          <div className="mt-4 text-center">
            <Link
              to="/register"
              className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-teal-600 transition-colors"
            >
              <UserPlus className="h-4 w-4" />
              계정이 없으신가요? 가입 신청
            </Link>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center space-y-2">
          <p className="text-[11px] text-slate-400">
            © 2026 Patient Safety QI System
          </p>
          <p className="text-[11px] text-slate-500">
            Developed by <span className="font-semibold text-teal-700">WONJIN OH</span>
          </p>
          <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
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
    </div>
  )
}
