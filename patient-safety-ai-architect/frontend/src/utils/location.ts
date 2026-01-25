/**
 * 장소 일반화 유틸리티
 *
 * 구체적인 장소(301호, 402호 등)를 일반 카테고리(병실, 화장실 등)로 변환
 */

// 장소 패턴과 일반화된 이름 매핑
const locationPatterns: { pattern: RegExp; label: string }[] = [
  // 병실 패턴: 301호, 402호, 501-1호, 3층 301호 등
  { pattern: /\d{2,3}(-\d)?호|병실/i, label: '병실' },
  // 화장실
  { pattern: /화장실|변기|욕실|샤워실/i, label: '화장실' },
  // 복도
  { pattern: /복도|홀|로비|현관/i, label: '복도' },
  // 간호사실/스테이션
  { pattern: /간호(사)?실|스테이션|NS/i, label: '간호사실' },
  // 처치실
  { pattern: /처치실|드레싱룸/i, label: '처치실' },
  // 물리치료/재활치료
  { pattern: /물리치료|재활치료|PT실|OT실|치료실/i, label: '재활치료실' },
  // 식당/급식
  { pattern: /식당|급식|식사|카페/i, label: '식당' },
  // 엘리베이터
  { pattern: /엘리베이터|승강기|EV/i, label: '엘리베이터' },
  // 계단
  { pattern: /계단/i, label: '계단' },
  // 야외/정원
  { pattern: /야외|정원|옥상|테라스/i, label: '야외' },
]

/**
 * 구체적인 장소를 일반화된 카테고리로 변환
 * @param location 원본 장소 문자열
 * @returns 일반화된 장소 이름
 */
export function generalizeLocation(location: string): string {
  if (!location) return '기타'

  const trimmed = location.trim()

  for (const { pattern, label } of locationPatterns) {
    if (pattern.test(trimmed)) {
      return label
    }
  }

  return '기타'
}

/**
 * 장소 일반화 + 원본 장소 반환 (툴팁용)
 * @param location 원본 장소 문자열
 * @returns { generalized: string, original: string }
 */
export function getLocationInfo(location: string): { generalized: string; original: string } {
  return {
    generalized: generalizeLocation(location),
    original: location,
  }
}
