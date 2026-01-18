import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { AlertCircle, Save, Upload } from 'lucide-react'
import { incidentApi, CreateIncidentData } from '@/utils/api'

// Validation schema matching backend requirements
const incidentSchema = z.object({
  category: z.enum(['fall', 'medication', 'pressure_ulcer', 'infection', 'medical_device', 'surgery', 'transfusion', 'other'], {
    required_error: '유형을 선택해주세요',
  }),
  grade: z.enum(['near_miss', 'no_harm', 'mild', 'moderate', 'severe', 'death'], {
    required_error: '등급을 선택해주세요',
  }),
  occurred_at: z.string().min(1, '발생일시를 입력해주세요'),
  location: z.string().min(1, '발생장소를 입력해주세요').max(200),
  description: z.string().min(10, '상세 내용을 10자 이상 입력해주세요'),
  immediate_action: z.string().min(5, '즉시 조치 내용을 5자 이상 입력해주세요'),
  reported_at: z.string().min(1, '보고일시를 입력해주세요'),
  reporter_name: z.string().optional(),
  root_cause: z.string().optional(),
  improvements: z.string().optional(),
  department: z.string().optional(),
}).refine((data) => {
  // reporter_name required except for near_miss
  if (data.grade !== 'near_miss' && !data.reporter_name) {
    return false
  }
  return true
}, {
  message: '근접오류가 아닌 경우 보고자 이름은 필수입니다',
  path: ['reporter_name'],
})

type IncidentForm = z.infer<typeof incidentSchema>

const categories = [
  { value: 'fall', label: '낙상' },
  { value: 'medication', label: '투약' },
  { value: 'pressure_ulcer', label: '욕창' },
  { value: 'infection', label: '감염' },
  { value: 'medical_device', label: '의료기기' },
  { value: 'surgery', label: '수술' },
  { value: 'transfusion', label: '수혈' },
  { value: 'other', label: '기타' },
]

const grades = [
  { value: 'near_miss', label: '근접오류', description: '환자에게 도달하지 않음' },
  { value: 'no_harm', label: '위해없음', description: '환자에게 도달했으나 해가 없음' },
  { value: 'mild', label: '경증', description: '일시적 손상 - 경증' },
  { value: 'moderate', label: '중등도', description: '일시적 손상 - 중등도' },
  { value: 'severe', label: '중증', description: '영구적 손상' },
  { value: 'death', label: '사망', description: '사망' },
]

export default function IncidentReport() {
  const navigate = useNavigate()
  const [files, setFiles] = useState<File[]>([])

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<IncidentForm>({
    resolver: zodResolver(incidentSchema),
    defaultValues: {
      reported_at: new Date().toISOString().slice(0, 16),
    },
  })

  const selectedGrade = watch('grade')

  const createMutation = useMutation({
    mutationFn: (data: CreateIncidentData) => incidentApi.create(data),
    onSuccess: () => {
      alert('사고 보고가 등록되었습니다.')
      navigate('/incidents')
    },
    onError: () => {
      alert('등록에 실패했습니다. 다시 시도해주세요.')
    },
  })

  const onSubmit = (data: IncidentForm) => {
    createMutation.mutate(data as CreateIncidentData)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">환자안전사고 보고</h1>
        <p className="mt-1 text-sm text-gray-500">
          사고 내용을 정확하게 기록해주세요. * 표시는 필수 항목입니다.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Info Card */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">기본 정보</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                유형 *
              </label>
              <select {...register('category')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {categories.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
              {errors.category && (
                <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>
              )}
            </div>

            {/* Grade */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                등급 *
              </label>
              <select {...register('grade')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {grades.map((grade) => (
                  <option key={grade.value} value={grade.value}>
                    {grade.label} - {grade.description}
                  </option>
                ))}
              </select>
              {errors.grade && (
                <p className="mt-1 text-sm text-red-600">{errors.grade.message}</p>
              )}
            </div>

            {/* Occurred At */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                발생일시 *
              </label>
              <input
                {...register('occurred_at')}
                type="datetime-local"
                className="input-field mt-1"
              />
              {errors.occurred_at && (
                <p className="mt-1 text-sm text-red-600">{errors.occurred_at.message}</p>
              )}
            </div>

            {/* Location */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                발생장소 *
              </label>
              <input
                {...register('location')}
                type="text"
                placeholder="예: 301호, 물리치료실"
                className="input-field mt-1"
              />
              {errors.location && (
                <p className="mt-1 text-sm text-red-600">{errors.location.message}</p>
              )}
            </div>

            {/* Reporter Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                보고자 이름 {selectedGrade !== 'near_miss' && '*'}
              </label>
              <input
                {...register('reporter_name')}
                type="text"
                className="input-field mt-1"
                placeholder={selectedGrade === 'near_miss' ? '선택 입력' : '필수 입력'}
              />
              {errors.reporter_name && (
                <p className="mt-1 text-sm text-red-600">{errors.reporter_name.message}</p>
              )}
              {selectedGrade === 'near_miss' && (
                <p className="mt-1 text-xs text-gray-500">
                  근접오류의 경우 보고자 이름은 선택 사항입니다
                </p>
              )}
            </div>

            {/* Reported At */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                보고일시 *
              </label>
              <input
                {...register('reported_at')}
                type="datetime-local"
                className="input-field mt-1"
              />
              {errors.reported_at && (
                <p className="mt-1 text-sm text-red-600">{errors.reported_at.message}</p>
              )}
            </div>
          </div>
        </div>

        {/* Description Card */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">사고 내용</h2>

          {/* Description */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700">
              상세 내용 *
            </label>
            <textarea
              {...register('description')}
              rows={4}
              className="input-field mt-1"
              placeholder="사고 발생 경위와 상황을 상세히 기술해주세요"
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
            )}
          </div>

          {/* Immediate Action - REQUIRED */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700">
              즉시 조치 *
            </label>
            <textarea
              {...register('immediate_action')}
              rows={3}
              className="input-field mt-1"
              placeholder="사고 발생 후 즉시 취한 조치를 기술해주세요"
            />
            {errors.immediate_action && (
              <p className="mt-1 text-sm text-red-600">{errors.immediate_action.message}</p>
            )}
            <div className="mt-1 flex items-center gap-1 text-amber-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-xs">모든 사고에 대해 즉시 조치 내용은 필수입니다</span>
            </div>
          </div>

          {/* Root Cause */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700">
              근본 원인 분석
            </label>
            <textarea
              {...register('root_cause')}
              rows={3}
              className="input-field mt-1"
              placeholder="사고의 근본 원인을 분석해주세요 (선택)"
            />
          </div>

          {/* Improvements */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              개선 방안
            </label>
            <textarea
              {...register('improvements')}
              rows={3}
              className="input-field mt-1"
              placeholder="재발 방지를 위한 개선 방안을 기술해주세요 (선택)"
            />
          </div>
        </div>

        {/* Attachments Card */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">첨부파일</h2>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <div className="mt-2">
              <label className="cursor-pointer">
                <span className="text-primary-600 hover:text-primary-500">
                  파일 선택
                </span>
                <input
                  type="file"
                  multiple
                  onChange={handleFileChange}
                  className="hidden"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                />
              </label>
              <span className="text-gray-500"> 또는 드래그 앤 드롭</span>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              PDF, JPG, PNG, DOC 파일 (최대 10MB)
            </p>
          </div>
          {files.length > 0 && (
            <ul className="mt-4 space-y-2">
              {files.map((file, index) => (
                <li key={index} className="text-sm text-gray-600">
                  {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Submit Buttons */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="btn-secondary"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {createMutation.isPending ? '저장 중...' : '저장'}
          </button>
        </div>
      </form>
    </div>
  )
}
