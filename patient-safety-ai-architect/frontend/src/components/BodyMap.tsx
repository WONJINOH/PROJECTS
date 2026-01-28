/**
 * Professional BodyMap Component
 * 의료용 인체 다이어그램 - 앞면/뒷면/측면 회전 가능
 * 욕창 호발부위 및 의료기기 관련 부위(MDRPI) 선택
 */
import { useState } from 'react'
import { RotateCcw, Stethoscope } from 'lucide-react'
import { PRESSURE_ULCER_LOCATION_OPTIONS, BODY_SIDE_OPTIONS, LOCATION_CATEGORIES } from '@/types'

interface BodyMapProps {
  selectedLocation: string | undefined
  selectedSide: string | undefined
  onLocationChange: (location: string) => void
  onSideChange: (side: string) => void
  error?: string
}

type ViewType = 'front' | 'back' | 'side'

// 부위별 위치 좌표 (SVG viewBox 0-200 기준)
const LOCATION_COORDS: Record<string, Record<ViewType, { x: number; y: number } | null>> = {
  // 후면
  occiput: { back: { x: 100, y: 22 }, front: null, side: { x: 100, y: 22 } },
  scapula: { back: { x: 70, y: 62 }, front: null, side: null },
  spinous_process: { back: { x: 100, y: 75 }, front: null, side: null },
  sacrum: { back: { x: 100, y: 115 }, front: null, side: { x: 115, y: 115 } },
  coccyx: { back: { x: 100, y: 128 }, front: null, side: null },
  ischium: { back: { x: 85, y: 135 }, front: null, side: null },
  heel: { back: { x: 85, y: 195 }, front: null, side: { x: 95, y: 195 } },

  // 측면
  ear: { back: { x: 115, y: 28 }, front: null, side: { x: 115, y: 28 } },
  shoulder: { back: { x: 55, y: 52 }, front: { x: 55, y: 52 }, side: { x: 100, y: 52 } },
  elbow: { back: { x: 45, y: 95 }, front: { x: 45, y: 95 }, side: { x: 125, y: 95 } },
  trochanter: { back: { x: 65, y: 120 }, front: null, side: { x: 100, y: 120 } },
  knee_lateral: { back: { x: 72, y: 155 }, front: null, side: { x: 100, y: 155 } },
  malleolus: { back: { x: 75, y: 188 }, front: { x: 75, y: 188 }, side: { x: 100, y: 188 } },

  // 전면
  forehead: { back: null, front: { x: 100, y: 15 }, side: { x: 85, y: 15 } },
  nose: { back: null, front: { x: 100, y: 25 }, side: { x: 75, y: 25 } },
  chin: { back: null, front: { x: 100, y: 35 }, side: { x: 80, y: 35 } },
  clavicle: { back: null, front: { x: 75, y: 48 }, side: null },
  sternum: { back: null, front: { x: 100, y: 60 }, side: null },
  iliac_crest: { back: null, front: { x: 70, y: 105 }, side: { x: 90, y: 105 } },
  patella: { back: null, front: { x: 85, y: 155 }, side: { x: 90, y: 155 } },
  shin: { back: null, front: { x: 85, y: 170 }, side: { x: 85, y: 170 } },
  dorsum_foot: { back: null, front: { x: 85, y: 192 }, side: { x: 80, y: 192 } },
  toes: { back: null, front: { x: 85, y: 198 }, side: { x: 75, y: 198 } },

  // 의료기기 관련
  nares: { back: null, front: { x: 100, y: 27 }, side: { x: 72, y: 27 } },
  lip: { back: null, front: { x: 100, y: 32 }, side: { x: 75, y: 32 } },
  neck_anterior: { back: null, front: { x: 100, y: 42 }, side: { x: 85, y: 42 } },
  meatus: { back: null, front: { x: 100, y: 125 }, side: null },
  finger: { back: null, front: { x: 40, y: 120 }, side: { x: 135, y: 100 } },
  bridge_of_nose: { back: null, front: { x: 100, y: 23 }, side: { x: 73, y: 23 } },
  cheek: { back: null, front: { x: 88, y: 28 }, side: { x: 82, y: 28 } },
}

// 중앙선 부위 (좌/우 선택 불필요)
const CENTER_LOCATIONS = [
  'sacrum', 'coccyx', 'spinous_process', 'sternum', 'nose', 'chin',
  'forehead', 'neck_anterior', 'meatus', 'bridge_of_nose', 'nares', 'lip', 'other'
]

export default function BodyMap({
  selectedLocation,
  selectedSide,
  onLocationChange,
  onSideChange,
  error,
}: BodyMapProps) {
  const [view, setView] = useState<ViewType>('back')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [hoveredLocation, setHoveredLocation] = useState<string | null>(null)

  const getLocationOption = (value: string) =>
    PRESSURE_ULCER_LOCATION_OPTIONS.find((opt) => opt.value === value)

  // 현재 뷰에서 표시할 부위들
  const visibleLocations = PRESSURE_ULCER_LOCATION_OPTIONS.filter((loc) => {
    if (loc.value === 'other') return false
    const coords = LOCATION_COORDS[loc.value]
    if (!coords) return false
    if (categoryFilter !== 'all' && loc.category !== categoryFilter) return false
    return coords[view] !== null
  })

  // 카테고리별 부위 목록
  const locationsByCategory = PRESSURE_ULCER_LOCATION_OPTIONS.filter((loc) => {
    if (categoryFilter === 'all') return true
    return loc.category === categoryFilter
  })

  const rotateView = () => {
    const views: ViewType[] = ['front', 'side', 'back']
    const currentIndex = views.indexOf(view)
    setView(views[(currentIndex + 1) % views.length])
  }

  const viewLabels: Record<ViewType, string> = {
    front: '전면 (Anterior)',
    back: '후면 (Posterior)',
    side: '측면 (Lateral)',
  }

  return (
    <div className="space-y-4">
      {/* 카테고리 필터 */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm font-medium text-gray-600">분류:</span>
        <button
          type="button"
          onClick={() => setCategoryFilter('all')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
            categoryFilter === 'all'
              ? 'bg-gray-800 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          전체
        </button>
        {LOCATION_CATEGORIES.map((cat) => (
          <button
            key={cat.value}
            type="button"
            onClick={() => setCategoryFilter(cat.value)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all flex items-center gap-1 ${
              categoryFilter === cat.value
                ? cat.value === 'device'
                  ? 'bg-purple-600 text-white'
                  : 'bg-rose-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {cat.value === 'device' && <Stethoscope className="w-3 h-3" />}
            {cat.label}
          </button>
        ))}
      </div>

      <div className="flex gap-6">
        {/* 바디맵 SVG */}
        <div className="flex-shrink-0">
          <div className="relative bg-gradient-to-b from-slate-50 to-slate-100 rounded-xl p-4 border border-slate-200 shadow-sm">
            {/* 뷰 전환 버튼 */}
            <div className="absolute top-2 right-2 flex items-center gap-2">
              <span className="text-xs font-medium text-slate-500">{viewLabels[view]}</span>
              <button
                type="button"
                onClick={rotateView}
                className="p-1.5 rounded-lg bg-white shadow-sm border border-slate-200 hover:bg-slate-50 transition-colors"
                title="회전 (앞면/측면/후면)"
              >
                <RotateCcw className="w-4 h-4 text-slate-600" />
              </button>
            </div>

            <svg viewBox="0 0 200 210" className="w-48 h-56">
              {/* 그라데이션 정의 */}
              <defs>
                <linearGradient id="bodyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#f1f5f9" />
                  <stop offset="100%" stopColor="#e2e8f0" />
                </linearGradient>
                <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="0" dy="1" stdDeviation="2" floodOpacity="0.1"/>
                </filter>
              </defs>

              {/* 인체 실루엣 */}
              <g filter="url(#shadow)">
                {view === 'front' && <FrontBody />}
                {view === 'back' && <BackBody />}
                {view === 'side' && <SideBody />}
              </g>

              {/* 부위 마커들 */}
              {visibleLocations.map((loc) => {
                const coords = LOCATION_COORDS[loc.value]?.[view]
                if (!coords) return null

                const isSelected = selectedLocation === loc.value
                const isHovered = hoveredLocation === loc.value
                const isDevice = loc.category === 'device'

                return (
                  <g
                    key={loc.value}
                    onClick={() => onLocationChange(loc.value)}
                    onMouseEnter={() => setHoveredLocation(loc.value)}
                    onMouseLeave={() => setHoveredLocation(null)}
                    className="cursor-pointer"
                  >
                    {/* 외곽 원 (선택/호버 시) */}
                    {(isSelected || isHovered) && (
                      <circle
                        cx={coords.x}
                        cy={coords.y}
                        r={isSelected ? 10 : 8}
                        fill="none"
                        stroke={isDevice ? '#9333ea' : '#dc2626'}
                        strokeWidth="2"
                        strokeDasharray={isHovered && !isSelected ? '3,2' : 'none'}
                        className="transition-all duration-200"
                      />
                    )}
                    {/* 내부 원 */}
                    <circle
                      cx={coords.x}
                      cy={coords.y}
                      r={isSelected ? 6 : 5}
                      fill={isSelected
                        ? (isDevice ? '#9333ea' : '#dc2626')
                        : isHovered
                          ? (isDevice ? '#c084fc' : '#f87171')
                          : (isDevice ? '#e9d5ff' : '#fecaca')
                      }
                      stroke={isDevice ? '#7c3aed' : '#ef4444'}
                      strokeWidth="1.5"
                      className="transition-all duration-200"
                    />
                    {/* 라벨 (선택/호버 시) */}
                    {(isSelected || isHovered) && (
                      <g>
                        <rect
                          x={coords.x - 25}
                          y={coords.y - 22}
                          width="50"
                          height="14"
                          rx="3"
                          fill="white"
                          fillOpacity="0.95"
                          stroke={isDevice ? '#9333ea' : '#dc2626'}
                          strokeWidth="0.5"
                        />
                        <text
                          x={coords.x}
                          y={coords.y - 12}
                          textAnchor="middle"
                          className="text-[8px] font-medium pointer-events-none"
                          fill={isDevice ? '#7c3aed' : '#dc2626'}
                        >
                          {loc.labelKo}
                        </text>
                      </g>
                    )}
                  </g>
                )
              })}
            </svg>

            <p className="text-xs text-slate-400 text-center mt-2">
              클릭하여 부위 선택
            </p>
          </div>
        </div>

        {/* 부위 목록 */}
        <div className="flex-1 min-w-0">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            부위 선택 *
            <span className="text-xs text-gray-400 ml-2">
              (또는 좌측 그림에서 클릭)
            </span>
          </label>

          <div className="max-h-64 overflow-y-auto border rounded-lg p-2 bg-white">
            <div className="grid grid-cols-2 gap-1.5">
              {locationsByCategory.map((option) => {
                const isSelected = selectedLocation === option.value
                const isDevice = option.category === 'device'

                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => onLocationChange(option.value)}
                    className={`
                      px-2 py-1.5 rounded-md text-xs text-left transition-all border
                      ${isSelected
                        ? isDevice
                          ? 'bg-purple-600 text-white border-purple-600 ring-2 ring-purple-300'
                          : 'bg-rose-600 text-white border-rose-600 ring-2 ring-rose-300'
                        : 'bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }
                    `}
                  >
                    <span className="block font-medium truncate">
                      {option.labelKo}
                    </span>
                    <span className={`block text-[10px] truncate ${
                      isSelected ? 'opacity-80' : 'text-gray-400'
                    }`}>
                      {option.labelEn}
                      {isDevice && 'device' in option && (
                        <span className="ml-1">• {option.device}</span>
                      )}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>

          {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
        </div>
      </div>

      {/* 좌/우측 선택 */}
      {selectedLocation && !CENTER_LOCATIONS.includes(selectedLocation) && (
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            위치 (좌/우측)
          </label>
          <div className="flex gap-2 flex-wrap">
            {BODY_SIDE_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => onSideChange(option.value)}
                className={`
                  px-4 py-2 rounded-lg text-sm font-medium transition-all
                  ${selectedSide === option.value
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-white text-gray-700 hover:bg-blue-100 border border-gray-200'
                  }
                `}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 선택된 부위 표시 */}
      {selectedLocation && (
        <div className={`p-3 rounded-lg border ${
          getLocationOption(selectedLocation)?.category === 'device'
            ? 'bg-purple-50 border-purple-200'
            : 'bg-rose-50 border-rose-200'
        }`}>
          <div className="flex items-center gap-2">
            {getLocationOption(selectedLocation)?.category === 'device' && (
              <Stethoscope className="w-4 h-4 text-purple-600" />
            )}
            <span className="text-sm text-gray-600">선택된 부위: </span>
            <span className={`font-semibold ${
              getLocationOption(selectedLocation)?.category === 'device'
                ? 'text-purple-700'
                : 'text-rose-700'
            }`}>
              {getLocationOption(selectedLocation)?.label}
              {selectedSide && !CENTER_LOCATIONS.includes(selectedLocation) && (
                <span className="ml-1 font-normal">
                  ({BODY_SIDE_OPTIONS.find((o) => o.value === selectedSide)?.label})
                </span>
              )}
            </span>
          </div>
          {getLocationOption(selectedLocation)?.category === 'device' && 'device' in (getLocationOption(selectedLocation) || {}) && (
            <p className="text-xs text-purple-600 mt-1">
              관련 의료기기: {(getLocationOption(selectedLocation) as any)?.device}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// 전면 인체 SVG
function FrontBody() {
  return (
    <g fill="url(#bodyGradient)" stroke="#94a3b8" strokeWidth="1.5" strokeLinejoin="round">
      {/* 머리 */}
      <ellipse cx="100" cy="22" rx="18" ry="20" />
      {/* 목 */}
      <path d="M92,40 L92,48 L108,48 L108,40" fill="url(#bodyGradient)" />
      {/* 몸통 */}
      <path d="M70,48 L130,48 L135,60 L135,105 L125,130 L75,130 L65,105 L65,60 Z" />
      {/* 왼팔 */}
      <path d="M70,48 L55,52 L45,95 L38,120 L48,122 L55,100 L62,60" />
      {/* 오른팔 */}
      <path d="M130,48 L145,52 L155,95 L162,120 L152,122 L145,100 L138,60" />
      {/* 왼다리 */}
      <path d="M75,130 L70,165 L68,195 L82,198 L85,165 L90,130" />
      {/* 오른다리 */}
      <path d="M125,130 L130,165 L132,195 L118,198 L115,165 L110,130" />
      {/* 가슴 중앙선 */}
      <line x1="100" y1="55" x2="100" y2="100" stroke="#cbd5e1" strokeWidth="0.5" strokeDasharray="3,3" />
    </g>
  )
}

// 후면 인체 SVG
function BackBody() {
  return (
    <g fill="url(#bodyGradient)" stroke="#94a3b8" strokeWidth="1.5" strokeLinejoin="round">
      {/* 머리 */}
      <ellipse cx="100" cy="22" rx="18" ry="20" />
      {/* 목 */}
      <path d="M92,40 L92,48 L108,48 L108,40" fill="url(#bodyGradient)" />
      {/* 몸통 */}
      <path d="M70,48 L130,48 L135,60 L135,105 L125,130 L75,130 L65,105 L65,60 Z" />
      {/* 왼팔 */}
      <path d="M70,48 L55,52 L45,95 L38,120 L48,122 L55,100 L62,60" />
      {/* 오른팔 */}
      <path d="M130,48 L145,52 L155,95 L162,120 L152,122 L145,100 L138,60" />
      {/* 왼다리 */}
      <path d="M75,130 L70,165 L68,195 L82,198 L85,165 L90,130" />
      {/* 오른다리 */}
      <path d="M125,130 L130,165 L132,195 L118,198 L115,165 L110,130" />
      {/* 척추선 */}
      <line x1="100" y1="45" x2="100" y2="125" stroke="#cbd5e1" strokeWidth="1" strokeDasharray="4,2" />
      {/* 견갑골 */}
      <ellipse cx="80" cy="62" rx="10" ry="12" fill="none" stroke="#cbd5e1" strokeWidth="0.8" />
      <ellipse cx="120" cy="62" rx="10" ry="12" fill="none" stroke="#cbd5e1" strokeWidth="0.8" />
    </g>
  )
}

// 측면 인체 SVG
function SideBody() {
  return (
    <g fill="url(#bodyGradient)" stroke="#94a3b8" strokeWidth="1.5" strokeLinejoin="round">
      {/* 머리 */}
      <ellipse cx="95" cy="22" rx="15" ry="20" />
      {/* 얼굴 특징 */}
      <path d="M80,20 L75,25 L80,30" fill="none" strokeWidth="1" />
      {/* 목 */}
      <path d="M88,38 L88,48 L102,48 L105,42" fill="url(#bodyGradient)" />
      {/* 몸통 */}
      <path d="M88,48 L115,48 L120,60 L118,105 L115,130 L85,130 L82,105 L85,60 Z" />
      {/* 팔 */}
      <path d="M115,50 L125,60 L135,95 L140,115 L130,118 L125,100 L118,65" />
      {/* 엉덩이/허벅지 */}
      <path d="M115,118 L118,125 L115,130" fill="none" />
      {/* 다리 */}
      <path d="M95,130 L92,155 L88,195 L102,198 L105,160 L102,130" />
      {/* 뒤꿈치 */}
      <ellipse cx="95" cy="196" rx="8" ry="4" fill="none" stroke="#cbd5e1" strokeWidth="0.8" />
    </g>
  )
}
