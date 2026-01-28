import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery } from '@tanstack/react-query'
import { AlertCircle, Save, Upload, Shield, Info, User } from 'lucide-react'
import { incidentApi, lookupApi, CreateIncidentData } from '@/utils/api'
import { useAuth } from '@/hooks/useAuth'
import { WARD_OPTIONS, GENDER_OPTIONS, LOCATION_TYPE_OPTIONS, Department, Physician, LocationType } from '@/types'

// Validation schema matching backend requirements
const incidentSchema = z.object({
  category: z.enum(['fall', 'medication', 'pressure_ulcer', 'infection', 'medical_device', 'surgery', 'transfusion', 'other'], {
    required_error: '유형을 선택해주세요',
  }),
  category_other_detail: z.string().max(200).optional(),
  grade: z.enum(['near_miss', 'no_harm', 'mild', 'moderate', 'severe', 'death'], {
    required_error: '등급을 선택해주세요',
  }),
  occurred_at: z.string().min(1, '발생일시를 입력해주세요'),
  location: z.string().min(1, '발생장소를 입력해주세요').max(200),
  location_type: z.enum(['own_room', 'other_room', 'bathroom', 'hallway', 'rehabilitation', 'nursing_station', 'other']).optional(),
  location_detail: z.string().max(200).optional(),
  description: z.string().min(10, '상세 내용을 10자 이상 입력해주세요'),
  immediate_action: z.string().min(5, '즉시 조치 내용을 5자 이상 입력해주세요'),
  reported_at: z.string().min(1, '보고일시를 입력해주세요'),
  reporter_name: z.string().optional(),
  root_cause: z.string().optional(),
  improvements: z.string().optional(),
  // 환자 정보 필드
  patient_registration_no: z.string().min(1, '환자등록번호를 입력해주세요').max(50),
  patient_name: z.string().min(1, '환자명을 입력해주세요').max(100),
  patient_ward: z.enum(['ward_2', 'ward_3', 'ward_5', 'ward_6', 'ward_7', 'ward_8', 'ward_9', 'ward_10', 'ward_11', 'outpatient'], {
    required_error: '병동을 선택해주세요',
  }),
  room_number: z.string().min(1, '병실을 입력해주세요').max(50),
  patient_gender: z.enum(['M', 'F'], {
    required_error: '성별을 선택해주세요',
  }),
  patient_age: z.number({ required_error: '연령을 입력해주세요' }).min(0, '연령은 0 이상이어야 합니다').max(150, '연령은 150 이하여야 합니다'),
  patient_department_id: z.number({ required_error: '진료과를 선택해주세요' }).min(1, '진료과를 선택해주세요'),
  patient_physician_id: z.number({ required_error: '담당 주치의를 선택해주세요' }).min(1, '담당 주치의를 선택해주세요'),
  diagnosis: z.string().optional(),
}).refine((data) => {
  // reporter_name required except for near_miss
  if (data.grade !== 'near_miss' && !data.reporter_name) {
    return false
  }
  return true
}, {
  message: '근접오류가 아닌 경우 보고자 이름은 필수입니다',
  path: ['reporter_name'],
}).refine((data) => {
  // category_other_detail required when category is 'other'
  if (data.category === 'other' && !data.category_other_detail) {
    return false
  }
  return true
}, {
  message: '기타를 선택한 경우 상세 내용을 입력해주세요',
  path: ['category_other_detail'],
})

type IncidentForm = z.infer<typeof incidentSchema>

const categories = [
  { value: 'fall', label: '낙상' },
  { value: 'medication', label: '투약' },
  { value: 'infection', label: '감염' },
  { value: 'medical_device', label: '의료기기' },
  { value: 'surgery', label: '수술/시술' },
  { value: 'transfusion', label: '수혈' },
  { value: 'other', label: '기타' },
  // 욕창은 별도 욕창관리 메뉴에서 욕창발생보고서로 관리
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
  const { user } = useAuth()
  const [files, setFiles] = useState<File[]>([])
  const [isAnonymous, setIsAnonymous] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<IncidentForm>({
    resolver: zodResolver(incidentSchema),
    defaultValues: {
      reported_at: new Date().toISOString().slice(0, 16),
      reporter_name: '',
    },
  })

  const selectedGrade = watch('grade')
  const selectedCategory = watch('category')
  const selectedLocationType = watch('location_type')
  const selectedDepartmentId = watch('patient_department_id')

  // Fetch departments
  const { data: departmentsData } = useQuery({
    queryKey: ['departments'],
    queryFn: () => lookupApi.listDepartments(true),
  })
  const departments: Department[] = departmentsData?.data || []

  // Fetch physicians for selected department
  const { data: physiciansData } = useQuery({
    queryKey: ['physicians', selectedDepartmentId],
    queryFn: () => lookupApi.listPhysicians({ department_id: selectedDepartmentId }),
    enabled: !!selectedDepartmentId,
  })
  const physicians: Physician[] = physiciansData?.data || []

  // Auto-fill reporter name from logged-in user
  useEffect(() => {
    if (user?.fullName && !isAnonymous) {
      setValue('reporter_name', user.fullName)
    }
  }, [user, setValue, isAnonymous])

  // Handle anonymous checkbox change
  useEffect(() => {
    if (isAnonymous) {
      setValue('reporter_name', '')
    } else if (user?.fullName) {
      setValue('reporter_name', user.fullName)
    }
  }, [isAnonymous, user, setValue])

  // Reset anonymous when grade changes from near_miss
  useEffect(() => {
    if (selectedGrade !== 'near_miss') {
      setIsAnonymous(false)
    }
  }, [selectedGrade])

  // Reset physician when department changes
  useEffect(() => {
    setValue('patient_physician_id', 0)
  }, [selectedDepartmentId, setValue])

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

          {/* Privacy Notice */}
          <div className="mb-6 p-4 bg-teal-50 border border-teal-200 rounded-lg">
            <div className="flex items-start gap-3">
              <Shield className="h-5 w-5 text-teal-600 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-semibold text-teal-800">보고자 보호 안내</h3>
                <p className="mt-1 text-sm text-teal-700">
                  보고자의 이름은 <strong>비밀이 보장</strong>됩니다. 보고된 정보는 환자안전 개선 목적으로만 사용되며,
                  보고자에 대한 어떠한 불이익도 없습니다. 솔직한 보고가 환자안전을 향상시키는 첫걸음입니다.
                </p>
              </div>
            </div>
          </div>

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
              {/* 기타 유형 상세 입력 */}
              {selectedCategory === 'other' && (
                <div className="mt-2">
                  <input
                    {...register('category_other_detail')}
                    type="text"
                    placeholder="기타 유형 상세 내용을 입력해주세요"
                    className="input-field"
                  />
                  {errors.category_other_detail && (
                    <p className="mt-1 text-sm text-red-600">{errors.category_other_detail.message}</p>
                  )}
                </div>
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

            {/* Location Type Dropdown */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                발생장소 유형
              </label>
              <select {...register('location_type')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {LOCATION_TYPE_OPTIONS.map((loc) => (
                  <option key={loc.value} value={loc.value}>
                    {loc.label}
                  </option>
                ))}
              </select>
              {/* 조건부 상세 입력 */}
              {selectedLocationType && LOCATION_TYPE_OPTIONS.find(l => l.value === selectedLocationType)?.needsDetail && (
                <div className="mt-2">
                  <input
                    {...register('location_detail')}
                    type="text"
                    placeholder={LOCATION_TYPE_OPTIONS.find(l => l.value === selectedLocationType)?.detailPlaceholder || '상세 위치'}
                    className="input-field"
                  />
                </div>
              )}
            </div>

            {/* Location (기존 텍스트 필드 - 하위 호환성) */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                발생장소 상세 *
              </label>
              <input
                {...register('location')}
                type="text"
                placeholder="예: 301호, 물리치료실, 화장실"
                className="input-field mt-1"
              />
              {errors.location && (
                <p className="mt-1 text-sm text-red-600">{errors.location.message}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">위치 유형 선택과 함께 구체적인 장소를 입력해주세요</p>
            </div>

            {/* Reporter Name */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                보고자 이름 {selectedGrade !== 'near_miss' && '*'}
              </label>
              <div className="mt-1 flex items-center gap-4">
                <input
                  {...register('reporter_name')}
                  type="text"
                  className={`input-field flex-1 ${isAnonymous ? 'bg-gray-100 text-gray-500' : ''}`}
                  placeholder={selectedGrade === 'near_miss' ? '선택 입력 (익명 가능)' : '필수 입력'}
                  disabled={isAnonymous}
                  readOnly={!isAnonymous && !!user?.fullName}
                />
              </div>

              {/* Anonymous checkbox - only show for near_miss */}
              {selectedGrade === 'near_miss' && (
                <label className="mt-2 flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isAnonymous}
                    onChange={(e) => setIsAnonymous(e.target.checked)}
                    className="w-4 h-4 text-teal-600 border-gray-300 rounded focus:ring-teal-500"
                  />
                  <span className="text-sm text-gray-700">익명으로 보고하기</span>
                  <span className="text-xs text-gray-500">(근접오류에 한해 가능)</span>
                </label>
              )}

              {errors.reporter_name && (
                <p className="mt-1 text-sm text-red-600">{errors.reporter_name.message}</p>
              )}

              {selectedGrade === 'near_miss' && !isAnonymous && (
                <div className="mt-2 flex items-center gap-1 text-gray-500">
                  <Info className="h-4 w-4" />
                  <span className="text-xs">
                    근접오류의 경우 익명 보고가 가능합니다. 위 체크박스를 선택하면 보고자 이름 없이 제출됩니다.
                  </span>
                </div>
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

        {/* Patient Info Card */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <User className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold">환자 정보</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Patient Registration No */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                환자등록번호 *
              </label>
              <input
                {...register('patient_registration_no')}
                type="text"
                placeholder="예: 12345678"
                className="input-field mt-1"
              />
              {errors.patient_registration_no && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_registration_no.message}</p>
              )}
            </div>

            {/* Patient Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                환자명 *
              </label>
              <input
                {...register('patient_name')}
                type="text"
                placeholder="환자 이름"
                className="input-field mt-1"
              />
              {errors.patient_name && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_name.message}</p>
              )}
            </div>

            {/* Ward */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                병동 *
              </label>
              <select {...register('patient_ward')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {WARD_OPTIONS.map((ward) => (
                  <option key={ward.value} value={ward.value}>
                    {ward.label}
                  </option>
                ))}
              </select>
              {errors.patient_ward && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_ward.message}</p>
              )}
            </div>

            {/* Room Number */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                병실 *
              </label>
              <input
                {...register('room_number')}
                type="text"
                placeholder="예: 501호"
                className="input-field mt-1"
              />
              {errors.room_number && (
                <p className="mt-1 text-sm text-red-600">{errors.room_number.message}</p>
              )}
            </div>

            {/* Gender */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                성별 *
              </label>
              <div className="mt-2 flex gap-4">
                {GENDER_OPTIONS.map((option) => (
                  <label key={option.value} className="flex items-center gap-2 cursor-pointer">
                    <input
                      {...register('patient_gender')}
                      type="radio"
                      value={option.value}
                      className="w-4 h-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700">{option.label}</span>
                  </label>
                ))}
              </div>
              {errors.patient_gender && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_gender.message}</p>
              )}
            </div>

            {/* Age */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                연령 *
              </label>
              <input
                {...register('patient_age', { valueAsNumber: true })}
                type="number"
                min={0}
                max={150}
                placeholder="나이"
                className="input-field mt-1"
              />
              {errors.patient_age && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_age.message}</p>
              )}
            </div>

            {/* Patient Department */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                환자 진료과 *
              </label>
              <select
                {...register('patient_department_id', { valueAsNumber: true })}
                className="input-field mt-1"
              >
                <option value="">선택하세요</option>
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </select>
              {errors.patient_department_id && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_department_id.message}</p>
              )}
            </div>

            {/* Patient Physician */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                담당 주치의 *
              </label>
              <select
                {...register('patient_physician_id', { valueAsNumber: true })}
                className="input-field mt-1"
                disabled={!selectedDepartmentId}
              >
                <option value="">선택하세요</option>
                {physicians.map((physician) => (
                  <option key={physician.id} value={physician.id}>
                    {physician.name}
                  </option>
                ))}
              </select>
              {!selectedDepartmentId && (
                <p className="mt-1 text-xs text-gray-500">진료과를 먼저 선택해주세요</p>
              )}
              {errors.patient_physician_id && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_physician_id.message}</p>
              )}
            </div>

            {/* Diagnosis */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                진단명
              </label>
              <input
                {...register('diagnosis')}
                type="text"
                placeholder="진단명 (선택 입력)"
                className="input-field mt-1"
              />
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
