import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { HeartPulse, AlertCircle, User, Lock, Mail, Building2, UserPlus, CheckCircle, ArrowLeft } from 'lucide-react'
import { api } from '@/utils/api'

const registerSchema = z.object({
  username: z.string()
    .min(3, '사원번호는 최소 3자 이상이어야 합니다')
    .max(50, '사원번호는 최대 50자까지 가능합니다'),
  email: z.string().email('올바른 이메일 형식을 입력해주세요'),
  password: z.string()
    .min(8, '비밀번호는 최소 8자 이상이어야 합니다')
    .max(100, '비밀번호는 최대 100자까지 가능합니다'),
  passwordConfirm: z.string(),
  fullName: z.string()
    .min(2, '이름은 최소 2자 이상이어야 합니다')
    .max(100, '이름은 최대 100자까지 가능합니다'),
  department: z.string().optional(),
}).refine((data) => data.password === data.passwordConfirm, {
  message: '비밀번호가 일치하지 않습니다',
  path: ['passwordConfirm'],
})

type RegisterForm = z.infer<typeof registerSchema>

export default function Register() {
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterForm) => {
    setError(null)
    setIsLoading(true)

    try {
      await api.post('/api/auth/request-registration', {
        username: data.username,
        email: data.email,
        password: data.password,
        full_name: data.fullName,
        department: data.department || null,
      })
      setIsSuccess(true)
    } catch (err: unknown) {
      const errorResponse = err as { response?: { data?: { detail?: string } } }
      setError(errorResponse.response?.data?.detail || '가입 신청 중 오류가 발생했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  if (isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-teal-50/30 py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        {/* Background decorative elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-teal-100/40 to-emerald-100/40 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-teal-100/40 to-cyan-100/40 rounded-full blur-3xl" />
        </div>

        <div className="max-w-md w-full relative z-10">
          <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200/60 p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center mx-auto mb-6 shadow-lg shadow-emerald-500/30">
              <CheckCircle className="h-8 w-8 text-white" />
            </div>
            <h2 className="text-xl font-bold text-slate-800 mb-3">
              가입 신청이 완료되었습니다
            </h2>
            <p className="text-slate-600 text-sm mb-6">
              시스템 관리자의 승인 후 로그인이 가능합니다.
              <br />
              승인 여부는 이메일로 안내됩니다.
            </p>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 bg-gradient-to-r from-teal-500 to-teal-600 text-white font-semibold py-3 px-6 rounded-xl shadow-lg shadow-teal-500/25 hover:shadow-xl hover:shadow-teal-500/30 transition-all duration-200"
            >
              <ArrowLeft className="h-4 w-4" />
              로그인 페이지로 돌아가기
            </Link>
          </div>
        </div>
      </div>
    )
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
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center shadow-xl shadow-teal-500/30">
                  <HeartPulse className="h-8 w-8 text-white" strokeWidth={2} />
                </div>
              </div>
            </div>
            <h1 className="text-xl font-bold text-slate-800 tracking-tight">
              회원가입 신청
            </h1>
            <p className="text-sm text-slate-500 mt-2">
              승인 후 시스템 이용이 가능합니다
            </p>
          </div>

          {/* Register Form */}
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            {error && (
              <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200/60 rounded-xl text-red-700">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="h-5 w-5 text-red-500" />
                </div>
                <span className="text-sm font-medium">{error}</span>
              </div>
            )}

            <div className="space-y-4">
              {/* Employee ID */}
              <div>
                <label htmlFor="username" className="block text-sm font-semibold text-slate-700 mb-2">
                  사원번호 <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    {...register('username')}
                    id="username"
                    type="text"
                    className="w-full pl-12 pr-4 py-3 bg-slate-50/80 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all duration-200"
                    placeholder="사원번호를 입력하세요"
                  />
                </div>
                {errors.username && (
                  <p className="mt-2 text-sm text-red-500 font-medium">{errors.username.message}</p>
                )}
              </div>

              {/* Full Name */}
              <div>
                <label htmlFor="fullName" className="block text-sm font-semibold text-slate-700 mb-2">
                  이름 <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <UserPlus className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    {...register('fullName')}
                    id="fullName"
                    type="text"
                    className="w-full pl-12 pr-4 py-3 bg-slate-50/80 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all duration-200"
                    placeholder="실명을 입력하세요"
                  />
                </div>
                {errors.fullName && (
                  <p className="mt-2 text-sm text-red-500 font-medium">{errors.fullName.message}</p>
                )}
              </div>

              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-slate-700 mb-2">
                  이메일 <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Mail className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    {...register('email')}
                    id="email"
                    type="email"
                    className="w-full pl-12 pr-4 py-3 bg-slate-50/80 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all duration-200"
                    placeholder="이메일을 입력하세요"
                  />
                </div>
                {errors.email && (
                  <p className="mt-2 text-sm text-red-500 font-medium">{errors.email.message}</p>
                )}
              </div>

              {/* Department */}
              <div>
                <label htmlFor="department" className="block text-sm font-semibold text-slate-700 mb-2">
                  부서
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Building2 className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    {...register('department')}
                    id="department"
                    type="text"
                    className="w-full pl-12 pr-4 py-3 bg-slate-50/80 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all duration-200"
                    placeholder="소속 부서 (선택)"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label htmlFor="password" className="block text-sm font-semibold text-slate-700 mb-2">
                  비밀번호 <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    {...register('password')}
                    id="password"
                    type="password"
                    className="w-full pl-12 pr-4 py-3 bg-slate-50/80 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all duration-200"
                    placeholder="8자 이상 입력하세요"
                  />
                </div>
                {errors.password && (
                  <p className="mt-2 text-sm text-red-500 font-medium">{errors.password.message}</p>
                )}
              </div>

              {/* Password Confirm */}
              <div>
                <label htmlFor="passwordConfirm" className="block text-sm font-semibold text-slate-700 mb-2">
                  비밀번호 확인 <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-slate-400" />
                  </div>
                  <input
                    {...register('passwordConfirm')}
                    id="passwordConfirm"
                    type="password"
                    className="w-full pl-12 pr-4 py-3 bg-slate-50/80 border border-slate-200 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500 transition-all duration-200"
                    placeholder="비밀번호를 다시 입력하세요"
                  />
                </div>
                {errors.passwordConfirm && (
                  <p className="mt-2 text-sm text-red-500 font-medium">{errors.passwordConfirm.message}</p>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700 text-white font-semibold py-3.5 px-6 rounded-xl shadow-lg shadow-teal-500/25 hover:shadow-xl hover:shadow-teal-500/30 transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed group mt-6"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>신청 중...</span>
                </>
              ) : (
                <>
                  <UserPlus className="h-5 w-5 group-hover:scale-110 transition-transform" />
                  <span>가입 신청</span>
                </>
              )}
            </button>
          </form>

          {/* Back to Login */}
          <div className="mt-6 pt-6 border-t border-slate-100 text-center">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-teal-600 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              로그인 페이지로 돌아가기
            </Link>
          </div>
        </div>

        {/* Notice */}
        <div className="text-center space-y-2">
          <p className="text-[11px] text-slate-500">
            비밀번호는 6개월마다 변경해야 합니다
          </p>
          <p className="text-[11px] text-slate-400">
            1년 이상 미접속 시 휴면계정으로 전환됩니다
          </p>
        </div>
      </div>
    </div>
  )
}
