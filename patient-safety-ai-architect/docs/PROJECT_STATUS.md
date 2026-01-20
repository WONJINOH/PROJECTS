# 환자안전사고 보고 시스템 - 프로젝트 현황

> **마지막 업데이트:** 2026-01-21
> **Phase:** 1 (내부 QI 시스템)
> **대상:** 요양병원 내부 사용

---

## 1. 프로젝트 개요

### 1.1 시스템 목적
- 환자안전사고(PSR) 보고 및 관리
- CAPA(시정 및 예방 조치) 추적
- 3단계 승인 워크플로우 (QI담당자 → 부원장 → 원장)
- 대시보드를 통한 지표 시각화
- PIPA(개인정보보호법) 준수 감사 로깅

### 1.2 기술 스택

| 계층 | 기술 | 버전 |
|------|------|------|
| **백엔드** | FastAPI + SQLAlchemy (Async) | Python 3.11+ |
| **프론트엔드** | React + TypeScript + Vite | React 18 |
| **데이터베이스** | PostgreSQL | 15+ |
| **상태관리** | Zustand + React Query | Latest |
| **스타일링** | TailwindCSS | Latest |
| **인증** | JWT (HS256) + Argon2id | - |
| **암호화** | AES-256 (민감정보) | - |
| **컨테이너** | Docker + Docker Compose | - |

---

## 2. 진행 현황

### 2.1 완료된 기능 ✅

#### 백엔드 (FastAPI)
| 기능 | 파일 | 상태 |
|------|------|------|
| 사용자 인증 (JWT) | `security/jwt.py`, `api/auth.py` | ✅ |
| RBAC 권한관리 (6역할, 13권한) | `security/rbac.py` | ✅ |
| 사고 CRUD API | `api/incidents.py` | ✅ |
| 승인 워크플로우 API | `api/approvals.py` | ✅ |
| CAPA 조치 API | `api/actions.py` | ✅ |
| 첨부파일 관리 | `api/attachments.py` | ✅ |
| 감사 로그 (PIPA Art.29) | `models/audit.py` | ✅ |
| 낙상 상세 API | `api/fall_details.py` | ✅ |
| 투약오류 상세 API | `api/medication_details.py` | ✅ |
| 지표 설정 API | `api/indicators.py` | ✅ |
| DB 마이그레이션 | `alembic/versions/` | ✅ |

#### 프론트엔드 (React)
| 페이지/컴포넌트 | 파일 | 상태 |
|----------------|------|------|
| 로그인 페이지 | `pages/Login.tsx` | ✅ |
| 대시보드 | `pages/Dashboard.tsx` | ✅ |
| 사고 목록 | `pages/IncidentList.tsx` | ✅ |
| 사고 등록 | `pages/IncidentReport.tsx` | ✅ |
| 사고 상세 | `pages/IncidentDetail.tsx` | ✅ |
| 지표 목록 | `pages/IndicatorList.tsx` | ✅ |
| 지표 등록/수정 | `pages/IndicatorForm.tsx` | ✅ |
| 지표 상세 | `pages/IndicatorDetail.tsx` | ✅ |
| 접근 로그 | `pages/AccessLog.tsx` | ✅ |
| CAPA 조치 폼 | `components/actions/ActionForm.tsx` | ✅ |
| CAPA 조치 목록 | `components/actions/ActionList.tsx` | ✅ |
| 낙상 상세 폼 | `components/details/FallDetailForm.tsx` | ✅ |
| 투약오류 상세 폼 | `components/details/MedicationDetailForm.tsx` | ✅ |

#### 문서화
| 문서 | 파일 | 상태 |
|------|------|------|
| PIPA 체크리스트 | `docs/pipa-checklist.md` | ✅ |
| Phase 1 체크리스트 | `docs/PHASE1_CHECKLIST.md` | ✅ |
| 프로젝트 지침 | `CLAUDE.md` | ✅ |

### 2.2 진행 중 🔄

| 기능 | 설명 | 진행률 |
|------|------|--------|
| PSR 양식 필드 통합 | 대시보드용 상세 필드 추가 | 90% |
| 스키마 업데이트 | 새 필드에 대한 스키마 정의 | 80% |

### 2.3 미완료 ⏳

| 기능 | 우선순위 | 비고 |
|------|----------|------|
| 단위 테스트 (pytest) | P1 | Release Gate 필수 |
| 컴포넌트 테스트 (Vitest) | P1 | - |
| E2E 테스트 (Playwright) | P1 | - |
| 보안 스캔 자동화 | P1 | Bandit, pip-audit, Gitleaks |
| SBOM 생성 | P1 | Release Gate 필수 |
| 추가 지표 모델 | P2 | 욕창, 신체보호대, 감염, 직원안전 |
| 대시보드 API 집계 | P2 | 차트 데이터 |
| 운영 배포 파이프라인 | P2 | AWS 배포 |

---

## 3. 주요 특징

### 3.1 보안 및 규정 준수

#### PIPA(개인정보보호법) 준수
```
✅ 암호화
   - 저장 시: AES-256 (환자정보)
   - 전송 시: HTTPS/TLS (운영환경)
   - 비밀번호: Argon2id 해싱

✅ 감사 로그 (PIPA 제29조)
   - 추가전용(Append-only) 로그
   - 해시 체인으로 변조 탐지
   - 5년 보관 요건 지원

✅ 접근 통제
   - 6단계 역할 기반 접근제어 (RBAC)
   - 행 수준 보안 (사고 소유권)
   - 13개 세분화된 권한
```

#### 역할 및 권한 체계
```
┌─────────────┬────────────────────────────────────────┐
│ 역할        │ 권한                                   │
├─────────────┼────────────────────────────────────────┤
│ REPORTER    │ 본인 사고 조회/등록/수정               │
│ QPS_STAFF   │ 부서 사고 + L1 승인                    │
│ VICE_CHAIR  │ 전체 사고 + L2 승인                    │
│ DIRECTOR    │ 전체 사고 + L3 승인 + 아카이브         │
│ ADMIN       │ 시스템 설정만                          │
│ MASTER      │ 전체 권한 (슈퍼유저)                   │
└─────────────┴────────────────────────────────────────┘
```

### 3.2 핵심 워크플로우

#### 사고 보고 → 승인 → 종결
```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  초안    │ -> │  제출됨  │ -> │  승인됨  │ -> │  종결됨  │
│ (draft)  │    │(submitted)│   │(approved)│    │ (closed) │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                     │
            ┌────────┴────────┐
            │   3단계 승인    │
            ├─────────────────┤
            │ L1: QI담당자    │
            │ L2: 부원장      │
            │ L3: 원장        │
            └─────────────────┘
```

#### CAPA 조치 추적
```
┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 신규 │ -> │ 진행 중  │ -> │   완료   │ -> │ 검증완료 │
│(open)│    │(progress)│    │(completed)│   │(verified)│
└──────┘    └──────────┘    └──────────┘    └──────────┘

• 담당자 (owner) + 기한 (due_date) 지정
• 완료 기준 (Definition of Done) 필수
• 증거 첨부 + 검증 메모 지원
• 기한 초과 자동 감지
```

### 3.3 데이터 모델 구조

#### 엔티티 관계도
```
User (1) ─────────────────┐
                          │
                      (N) Incident ──────────┬─────────────┐
                          │                  │             │
                          │              (N) Action    (N) Attachment
                          │              (N) Approval
                          │
                 Approver ────── (N) Approval

FallDetail ──────── (1) Incident
MedicationDetail ── (1) Incident

Indicator (1) ────── (N) IndicatorValue

AuditLog ─────────── User (참조)
```

### 3.4 PSR 양식 기반 상세 필드 (대시보드용)

#### 낙상 상세 (FallDetail)
```python
# 기본 필드
patient_code, injury_level, fall_location, fall_cause

# PSR 양식 추가 필드 (대시보드용)
consciousness_level   # 의식상태: 명료/기면/혼미/반혼수/혼수
activity_level        # 활동수준: 독립적/부분도움/전적도움
mobility_aid_type     # 보행보조기구: 휠체어/워커/지팡이 등
risk_factors[]        # 위험요인: 낙상과거력, 인지장애 등 (복수선택)
related_medications[] # 관련투약: 진정제, 이뇨제 등 (복수선택)
fall_type            # 낙상유형: 침대/서있다가/이동중 등
physical_injury_type # 신체손상: 찰과상/타박상/골절 등
treatments_provided[] # 치료내용: 관찰/드레싱/봉합 등 (복수선택)
```

#### 투약오류 상세 (MedicationErrorDetail)
```python
# 기본 필드 (NCC MERP 분류)
error_type, error_stage, error_severity (A~I)

# PSR 양식 추가 필드
discovery_timing     # 발견시점: 투약전/투약후
error_causes[]       # 오류원인: 의사소통/약품명혼동/업무과중 등
```

#### 사고 공통 필드 (Incident)
```python
# PSR 양식 공통 필드 (대시보드용)
outcome_impact           # 문제의 결과: 입원연장/추가치료/재입원 등
contributing_factors[]   # 기여요인: 인적/시스템/시설 요인 (복수선택)
patient_physical_outcome # 환자손상결과: 없음/일시적/영구적/사망
```

---

## 4. 아키텍처

### 4.1 백엔드 구조
```
backend/
├── app/
│   ├── main.py              # FastAPI 앱 엔트리포인트
│   ├── config.py            # 환경 설정
│   ├── database.py          # DB 연결 (Async SQLAlchemy)
│   │
│   ├── models/              # SQLAlchemy 모델 (14개)
│   │   ├── user.py          # 사용자 (RBAC)
│   │   ├── incident.py      # 사고 (핵심)
│   │   ├── approval.py      # 승인 (3단계)
│   │   ├── action.py        # CAPA 조치
│   │   ├── attachment.py    # 첨부파일
│   │   ├── audit.py         # 감사 로그
│   │   ├── indicator.py     # 지표 설정
│   │   ├── fall_detail.py   # 낙상 상세
│   │   ├── medication_detail.py  # 투약오류 상세
│   │   └── ...
│   │
│   ├── schemas/             # Pydantic 스키마
│   │   ├── auth.py
│   │   ├── incident.py
│   │   ├── action.py
│   │   └── ...
│   │
│   ├── api/                 # API 엔드포인트
│   │   ├── auth.py          # POST /api/auth/login
│   │   ├── incidents.py     # /api/incidents/*
│   │   ├── approvals.py     # /api/approvals/*
│   │   ├── actions.py       # /api/actions/*
│   │   ├── attachments.py   # /api/attachments/*
│   │   ├── indicators.py    # /api/indicators/*
│   │   ├── fall_details.py
│   │   └── medication_details.py
│   │
│   └── security/            # 보안 모듈
│       ├── rbac.py          # 역할/권한 정의
│       ├── dependencies.py  # FastAPI 의존성
│       ├── jwt.py           # JWT 토큰
│       └── password.py      # 비밀번호 해싱
│
└── alembic/                 # DB 마이그레이션
    └── versions/
```

### 4.2 프론트엔드 구조
```
frontend/
├── src/
│   ├── main.tsx             # React 엔트리포인트
│   ├── App.tsx              # 라우터 설정
│   │
│   ├── pages/               # 페이지 컴포넌트 (9개)
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── IncidentList.tsx
│   │   ├── IncidentReport.tsx
│   │   ├── IncidentDetail.tsx
│   │   ├── IndicatorList.tsx
│   │   ├── IndicatorForm.tsx
│   │   ├── IndicatorDetail.tsx
│   │   └── AccessLog.tsx
│   │
│   ├── components/          # 재사용 컴포넌트
│   │   ├── Layout.tsx       # 레이아웃 (사이드바, 헤더)
│   │   ├── actions/         # CAPA 관련
│   │   │   ├── ActionForm.tsx
│   │   │   └── ActionList.tsx
│   │   └── details/         # 상세 양식
│   │       ├── FallDetailForm.tsx
│   │       └── MedicationDetailForm.tsx
│   │
│   ├── hooks/
│   │   └── useAuth.ts       # 인증 상태 (Zustand)
│   │
│   ├── utils/
│   │   └── api.ts           # Axios API 클라이언트
│   │
│   └── types/
│       └── index.ts         # TypeScript 타입 정의
│
└── index.html
```

---

## 5. 개선 필요 사항

### 5.1 필수 개선 (P1 - Release Gate 필수)

| 항목 | 현재 상태 | 필요 조치 |
|------|----------|----------|
| **단위 테스트** | 미작성 | pytest로 API 테스트 작성 |
| **프론트엔드 테스트** | 미작성 | Vitest + React Testing Library |
| **E2E 테스트** | 미작성 | Playwright 시나리오 작성 |
| **보안 스캔** | 수동 | CI/CD 파이프라인에 자동화 |
| **SBOM 생성** | 미구현 | pip-licenses, npm-license-checker |

### 5.2 권장 개선 (P2)

| 항목 | 현재 상태 | 권장 조치 |
|------|----------|----------|
| **스키마 검증 강화** | 기본 검증 | Pydantic 커스텀 밸리데이터 추가 |
| **에러 처리 표준화** | 개별 처리 | 전역 예외 핸들러 구현 |
| **API 문서화** | 자동 생성 | OpenAPI 스키마 보강 |
| **프론트엔드 에러 바운더리** | 미구현 | React Error Boundary 추가 |
| **로딩 상태 UX** | 기본 스피너 | Skeleton UI 적용 |
| **번들 크기 최적화** | 867KB | 코드 스플리팅, 동적 import |

### 5.3 향후 확장 (P3)

| 항목 | 설명 |
|------|------|
| **추가 지표 모델** | 욕창, 신체보호대, 감염, 직원안전 |
| **대시보드 고도화** | 실시간 차트, 드릴다운 분석 |
| **알림 시스템** | 이메일/SMS 알림 |
| **보고서 내보내기** | PDF/Excel 생성 |
| **EMR 연동** | Phase 2에서 고려 |

---

## 6. 릴리스 게이트 체크리스트

### Phase 1 릴리스 기준

```
[P0 - 필수 통과 조건]
□ 모든 필수 필드 검증 (immediate_action, reported_at, reporter_name)
□ PIPA 문서 완성 (pipa-checklist.md)
□ 단위 테스트 커버리지 80% 이상
□ 보안 스캔 통과 (High/Critical = 0)
□ SBOM 생성 및 검토
□ 감사 로그 정상 작동 확인

[P1 - 릴리스 전 완료]
□ E2E 테스트 주요 시나리오 통과
□ 성능 테스트 (동시 사용자 50명)
□ 백업/복구 절차 문서화
□ 운영 매뉴얼 작성

[P2 - 릴리스 후 1주 내]
□ 사용자 교육 자료 준비
□ 피드백 수집 채널 구축
```

---

## 7. 파일 목록 요약

### 백엔드 주요 파일
```
backend/app/
├── main.py                    # FastAPI 앱
├── config.py                  # 설정
├── database.py                # DB 연결
├── models/                    # 14개 모델
├── schemas/                   # 6개 스키마
├── api/                       # 9개 API 모듈
└── security/                  # 4개 보안 모듈
```

### 프론트엔드 주요 파일
```
frontend/src/
├── App.tsx                    # 라우터
├── pages/                     # 9개 페이지
├── components/                # 5개 컴포넌트
├── hooks/useAuth.ts          # 인증 훅
├── utils/api.ts              # API 클라이언트
└── types/index.ts            # 타입 정의 (~700줄)
```

### 문서
```
docs/
├── pipa-checklist.md         # PIPA 준수 체크리스트
├── PHASE1_CHECKLIST.md       # Phase 1 구현 체크리스트
└── PROJECT_STATUS.md         # 이 문서
```

---

## 8. 연락처 및 참고

### 에스컬레이션 경로
- **PIPA 해석**: DPO / 법무팀
- **보안 이슈**: 병원 보안 담당자
- **기술 문의**: 개발팀

### 참고 문서
- [PIPA 개인정보보호법](https://www.law.go.kr/법령/개인정보보호법)
- [NCC MERP 투약오류 분류](https://www.nccmerp.org/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [React Query 문서](https://tanstack.com/query)

---

*이 문서는 프로젝트 진행에 따라 지속적으로 업데이트됩니다.*
