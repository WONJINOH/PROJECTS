import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  HeartPulse,
  ArrowLeft,
  Save,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { pressureUlcerManagementApi, lookupApi } from '@/utils/api'
import {
  WARD_OPTIONS,
  GENDER_OPTIONS,
  PRESSURE_ULCER_ORIGIN_OPTIONS,
  PRESSURE_ULCER_GRADE_OPTIONS,
} from '@/types'
import BodyMap from '@/components/BodyMap'

// Zod schema for form validation
const pressureUlcerReportSchema = z.object({
  // 환자 정보
  patient_registration_no: z.string().min(1, '등록번호를 입력해주세요'),
  patient_name: z.string().min(1, '환자명을 입력해주세요'),
  patient_ward: z.string().min(1, '병동을 선택해주세요'),
  room_number: z.string().min(1, '병실번호를 입력해주세요'),
  patient_gender: z.enum(['M', 'F'], { required_error: '성별을 선택해주세요' }),
  patient_age: z.number({ invalid_type_error: '나이를 입력해주세요' }).min(0).max(150),
  patient_department_id: z.number({ invalid_type_error: '진료과를 선택해주세요' }).min(1, '진료과를 선택해주세요'),
  patient_physician_id: z.number({ invalid_type_error: '주치의를 선택해주세요' }).min(1, '주치의를 선택해주세요'),
  admission_date: z.string().min(1, '입원일을 입력해주세요'),
  diagnosis: z.string().optional(),

  // 욕창 정보
  origin: z.enum(['admission', 'acquired', 'unknown'], { required_error: '발생시점을 선택해주세요' }),
  discovery_date: z.string().min(1, '발견일을 입력해주세요'),
  location: z.string().min(1, '부위를 선택해주세요'), // 동적 부위 목록 사용
  location_side: z.enum(['left', 'right', 'center', 'both']).optional(),
  location_detail: z.string().optional(),
  grade: z.enum(['stage_1', 'stage_2', 'stage_3', 'stage_4', 'unstageable', 'dtpi'], { required_error: '단계를 선택해주세요' }),

  // PUSH 점수
  push_length_width: z.number().min(0).max(10).optional(),
  push_exudate: z.number().min(0).max(3).optional(),
  push_tissue_type: z.number().min(0).max(4).optional(),

  // 크기
  length_cm: z.number().min(0).optional(),
  width_cm: z.number().min(0).optional(),
  depth_cm: z.number().min(0).optional(),

  // 추가 정보
  risk_factors: z.string().optional(),
  treatment_plan: z.string().optional(),
  note: z.string().optional(),
})

type PressureUlcerReportForm = z.infer<typeof pressureUlcerReportSchema>

export default function PressureUlcerOccurrenceReport() {
  const navigate = useNavigate()
  const { user } = useAuth()

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<PressureUlcerReportForm>({
    resolver: zodResolver(pressureUlcerReportSchema),
    defaultValues: {
      patient_ward: user?.department || '',
      discovery_date: new Date().toISOString().split('T')[0],
      origin: 'acquired',
    },
  })

  const selectedLocation = watch('location')
  const selectedSide = watch('location_side')
  const selectedDepartmentId = watch('patient_department_id')

  // Calculate PUSH total
  const pushLengthWidth = watch('push_length_width')
  const pushExudate = watch('push_exudate')
  const pushTissueType = watch('push_tissue_type')
  const pushTotal = (pushLengthWidth || 0) + (pushExudate || 0) + (pushTissueType || 0)

  // Fetch departments
  const { data: departmentsData } = useQuery({
    queryKey: ['departments'],
    queryFn: () => lookupApi.listDepartments(),
  })

  // Fetch physicians based on selected department
  const { data: physiciansData } = useQuery({
    queryKey: ['physicians', selectedDepartmentId],
    queryFn: () => lookupApi.listPhysicians({ department_id: selectedDepartmentId }),
    enabled: !!selectedDepartmentId,
  })

  const departments = departmentsData?.data?.items || []
  const physicians = physiciansData?.data?.items || []

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: (data: PressureUlcerReportForm) => {
      // 부위 상세에 좌/우측 정보 포함
      let locationDetail = data.location_detail || ''
      if (data.location_side && data.location_side !== 'center') {
        const sideLabel = { left: '좌측', right: '우측', both: '양측' }[data.location_side]
        locationDetail = sideLabel + (locationDetail ? ` - ${locationDetail}` : '')
      }

      return pressureUlcerManagementApi.createRecord({
        patient_code: data.patient_registration_no,
        patient_name: data.patient_name,
        patient_gender: data.patient_gender,
        room_number: data.room_number,
        patient_age_group: data.patient_age ? `${Math.floor(data.patient_age / 10) * 10}대` : undefined,
        admission_date: data.admission_date || undefined,
        location: data.location,
        location_detail: locationDetail || undefined,
        origin: data.origin,
        discovery_date: data.discovery_date,
        grade: data.grade,
        push_length_width: data.push_length_width || 0,
        push_exudate: data.push_exudate || 0,
        push_tissue_type: data.push_tissue_type || 0,
        length_cm: data.length_cm,
        width_cm: data.width_cm,
        depth_cm: data.depth_cm,
        department: data.patient_ward,
        risk_factors: data.risk_factors,
        treatment_plan: data.treatment_plan,
        note: data.note,
        reporter_name: user?.fullName,
      })
    },
    onSuccess: () => {
      alert('욕창발생보고서가 저장되었습니다.')
      navigate('/pressure-ulcer-management')
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || error.message || '알 수 없는 오류'
      alert(`저장 실패: ${errorMessage}`)
    },
  })

  const onSubmit = (data: PressureUlcerReportForm) => {
    submitMutation.mutate(data)
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/pressure-ulcer-management')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-gray-600" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <HeartPulse className="h-6 w-6 text-rose-600" />
            욕창발생보고서
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            새로운 욕창 환자를 등록합니다
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* 환자 정보 섹션 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
            환자 정보
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                등록번호 *
              </label>
              <input
                type="text"
                {...register('patient_registration_no')}
                className="input-field mt-1"
                placeholder="환자 등록번호"
              />
              {errors.patient_registration_no && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_registration_no.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                환자명 *
              </label>
              <input
                type="text"
                {...register('patient_name')}
                className="input-field mt-1"
                placeholder="환자명"
              />
              {errors.patient_name && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_name.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                성별 *
              </label>
              <div className="mt-2 flex gap-4">
                {GENDER_OPTIONS.map((option) => (
                  <label key={option.value} className="inline-flex items-center">
                    <input
                      type="radio"
                      value={option.value}
                      {...register('patient_gender')}
                      className="form-radio"
                    />
                    <span className="ml-2">{option.label}</span>
                  </label>
                ))}
              </div>
              {errors.patient_gender && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_gender.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                나이 *
              </label>
              <input
                type="number"
                {...register('patient_age', { valueAsNumber: true })}
                className="input-field mt-1"
                placeholder="나이"
              />
              {errors.patient_age && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_age.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                병동 *
              </label>
              <select {...register('patient_ward')} className="input-field mt-1">
                <option value="">선택하세요</option>
                {WARD_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {errors.patient_ward && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_ward.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                병실번호 *
              </label>
              <input
                type="text"
                {...register('room_number')}
                className="input-field mt-1"
                placeholder="예: 301호"
              />
              {errors.room_number && (
                <p className="mt-1 text-sm text-red-600">{errors.room_number.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                진료과 *
              </label>
              <select
                {...register('patient_department_id', { valueAsNumber: true })}
                className="input-field mt-1"
              >
                <option value="">선택하세요</option>
                {departments.map((dept: { id: number; name: string }) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </select>
              {errors.patient_department_id && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_department_id.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                주치의 *
              </label>
              <select
                {...register('patient_physician_id', { valueAsNumber: true })}
                className="input-field mt-1"
                disabled={!selectedDepartmentId}
              >
                <option value="">선택하세요</option>
                {physicians.map((phys: { id: number; name: string }) => (
                  <option key={phys.id} value={phys.id}>
                    {phys.name}
                  </option>
                ))}
              </select>
              {errors.patient_physician_id && (
                <p className="mt-1 text-sm text-red-600">{errors.patient_physician_id.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                입원일 *
              </label>
              <input
                type="date"
                {...register('admission_date')}
                className="input-field mt-1"
              />
              {errors.admission_date && (
                <p className="mt-1 text-sm text-red-600">{errors.admission_date.message}</p>
              )}
            </div>

            <div className="md:col-span-2 lg:col-span-3">
              <label className="block text-sm font-medium text-gray-700">
                진단명
              </label>
              <input
                type="text"
                {...register('diagnosis')}
                className="input-field mt-1"
                placeholder="진단명"
              />
            </div>
          </div>
        </div>

        {/* 욕창 정보 섹션 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
            욕창 정보
          </h2>
          <div className="space-y-6">
            {/* 기본 정보 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  발생시점 *
                </label>
                <select {...register('origin')} className="input-field mt-1">
                  {PRESSURE_ULCER_ORIGIN_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                {errors.origin && (
                  <p className="mt-1 text-sm text-red-600">{errors.origin.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  발견일 *
                </label>
                <input
                  type="date"
                  {...register('discovery_date')}
                  className="input-field mt-1"
                />
                {errors.discovery_date && (
                  <p className="mt-1 text-sm text-red-600">{errors.discovery_date.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  단계 *
                </label>
                <select {...register('grade')} className="input-field mt-1">
                  <option value="">선택하세요</option>
                  {PRESSURE_ULCER_GRADE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                {errors.grade && (
                  <p className="mt-1 text-sm text-red-600">{errors.grade.message}</p>
                )}
              </div>
            </div>

            {/* 바디맵 - 부위 선택 */}
            <div className="border-t pt-4">
              <BodyMap
                selectedLocation={selectedLocation}
                selectedSide={selectedSide}
                onLocationChange={(location) => setValue('location', location as any)}
                onSideChange={(side) => setValue('location_side', side as any)}
                error={errors.location?.message}
              />
            </div>

            {/* 부위 상세 (기타 선택 시) */}
            {selectedLocation === 'other' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  부위 상세 (기타)
                </label>
                <input
                  type="text"
                  {...register('location_detail')}
                  className="input-field mt-1"
                  placeholder="부위를 입력해주세요"
                />
              </div>
            )}

            {/* 크기 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 border-t pt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  크기 - 가로 (cm)
                </label>
                <input
                  type="number"
                  step="0.1"
                  {...register('length_cm', { valueAsNumber: true })}
                  className="input-field mt-1"
                  placeholder="가로"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  크기 - 세로 (cm)
                </label>
                <input
                  type="number"
                  step="0.1"
                  {...register('width_cm', { valueAsNumber: true })}
                  className="input-field mt-1"
                  placeholder="세로"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  크기 - 깊이 (cm)
                </label>
                <input
                  type="number"
                  step="0.1"
                  {...register('depth_cm', { valueAsNumber: true })}
                  className="input-field mt-1"
                  placeholder="깊이"
                />
              </div>
            </div>
          </div>
        </div>

        {/* PUSH Score 섹션 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
            PUSH 점수 (Pressure Ulcer Scale for Healing)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Length x Width (0-10점)
              </label>
              <select
                {...register('push_length_width', { valueAsNumber: true })}
                className="input-field mt-1"
              >
                <option value="">선택</option>
                <option value={0}>0 - 0 cm2</option>
                <option value={1}>1 - &lt;0.3 cm2</option>
                <option value={2}>2 - 0.3-0.6 cm2</option>
                <option value={3}>3 - 0.7-1.0 cm2</option>
                <option value={4}>4 - 1.1-2.0 cm2</option>
                <option value={5}>5 - 2.1-3.0 cm2</option>
                <option value={6}>6 - 3.1-4.0 cm2</option>
                <option value={7}>7 - 4.1-8.0 cm2</option>
                <option value={8}>8 - 8.1-12.0 cm2</option>
                <option value={9}>9 - 12.1-24.0 cm2</option>
                <option value={10}>10 - &gt;24.0 cm2</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Exudate Amount (0-3점)
              </label>
              <select
                {...register('push_exudate', { valueAsNumber: true })}
                className="input-field mt-1"
              >
                <option value="">선택</option>
                <option value={0}>0 - None (없음)</option>
                <option value={1}>1 - Light (경미)</option>
                <option value={2}>2 - Moderate (중등도)</option>
                <option value={3}>3 - Heavy (다량)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Tissue Type (0-4점)
              </label>
              <select
                {...register('push_tissue_type', { valueAsNumber: true })}
                className="input-field mt-1"
              >
                <option value="">선택</option>
                <option value={0}>0 - Closed (폐쇄)</option>
                <option value={1}>1 - Epithelial (상피조직)</option>
                <option value={2}>2 - Granulation (육아조직)</option>
                <option value={3}>3 - Slough (부육조직)</option>
                <option value={4}>4 - Necrotic (괴사조직)</option>
              </select>
            </div>
          </div>

          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">PUSH Total:</span>
              <span className="text-lg font-bold text-rose-600">{pushTotal} / 17</span>
            </div>
          </div>
        </div>

        {/* 추가 정보 섹션 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
            추가 정보
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                위험 요인
              </label>
              <textarea
                {...register('risk_factors')}
                className="input-field mt-1"
                rows={2}
                placeholder="영양불량, 실금, 의식저하, 거동불가 등"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                치료 계획
              </label>
              <textarea
                {...register('treatment_plan')}
                className="input-field mt-1"
                rows={2}
                placeholder="드레싱, 체위변경, 영양지원 등"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                비고
              </label>
              <textarea
                {...register('note')}
                className="input-field mt-1"
                rows={2}
                placeholder="기타 특이사항"
              />
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/pressure-ulcer-management')}
            className="btn-secondary"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={isSubmitting || submitMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {submitMutation.isPending ? '저장 중...' : '저장'}
          </button>
        </div>
      </form>
    </div>
  )
}
