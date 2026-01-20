# Phase 1 구현 체크리스트

## P0: Release Gate 필수 (먼저 완료)

### 1. PIPA 문서 (Gate 필수) ✅ 완료
- [x] `docs/pipa-checklist.md` 생성
- [x] 데이터 수집 범위 정의
- [x] 암호화 정책 문서화
- [x] 접근 제어 정책 문서화
- [x] 감사 추적 정책 문서화

### 2. 누락 모델 생성
- [ ] `backend/app/models/action.py` - CAPA Action 모델
- [ ] `backend/app/models/__init__.py` 에 Action 추가
- [ ] Alembic 초기화 (`alembic init alembic`)
- [ ] 초기 마이그레이션 생성

### 3. 인증 구현
- [ ] `backend/app/security/dependencies.py` - `get_current_user` 구현
- [ ] `backend/app/api/auth.py` - JWT 로그인/로그아웃
- [ ] 토큰 생성/검증 로직

---

## P0: 핵심 API 구현

### 4. Incident API
- [ ] `POST /api/incidents/` - 생성 (필수 필드 검증)
- [ ] `GET /api/incidents/` - 목록 (행 레벨 접근 제어)
- [ ] `GET /api/incidents/{id}` - 상세 조회
- [ ] `PUT /api/incidents/{id}` - 수정

### 5. Approval API
- [ ] `POST /api/approvals/incidents/{id}/approve` - 승인
- [ ] `POST /api/approvals/incidents/{id}/reject` - 거절
- [ ] `GET /api/approvals/incidents/{id}/status` - 상태 조회
- [ ] 순차 승인 로직 (L1 → L2 → L3)

### 6. Actions API (신규)
- [ ] `backend/app/api/actions.py` 생성
- [ ] `POST /api/actions/` - 생성
- [ ] `GET /api/incidents/{id}/actions` - 목록
- [ ] `PUT /api/actions/{id}` - 수정
- [ ] `PATCH /api/actions/{id}/status` - 상태 변경

### 7. Attachment API
- [ ] `POST /api/attachments/incidents/{id}/upload` - 업로드
- [ ] `GET /api/attachments/{id}/download` - 다운로드
- [ ] `DELETE /api/attachments/{id}` - 삭제
- [ ] 파일 저장 경로: `uploads/incidents/{id}/`

---

## P1: 상세 기능

### 8. Fall Detail API
- [ ] `backend/app/api/fall_details.py` 생성
- [ ] Incident와 연결
- [ ] 통계 집계

### 9. Medication Detail API
- [ ] `backend/app/api/medication_details.py` 생성
- [ ] NCC MERP 분류
- [ ] 통계 집계

---

## P0: Frontend 연결

### 10. API 클라이언트
- [ ] `frontend/src/utils/api.ts` 업데이트
- [ ] useQuery 훅 구현
- [ ] 에러 처리

### 11. 페이지 연결
- [ ] `IncidentList.tsx` - Mock 제거, API 연결
- [ ] `IncidentDetail.tsx` - Mock 제거, API 연결
- [ ] `IncidentReport.tsx` - 폼 제출 연결

### 12. Actions UI
- [ ] `frontend/src/pages/ActionList.tsx` 생성
- [ ] `frontend/src/pages/ActionForm.tsx` 생성
- [ ] IncidentDetail에 통합

### 13. Approval UI
- [ ] 승인/거절 버튼 추가
- [ ] 상태 표시 컴포넌트

---

## P0: 테스트

### 14. Backend 테스트
- [ ] `backend/tests/conftest.py` - 픽스처
- [ ] `backend/tests/test_auth.py`
- [ ] `backend/tests/test_incidents.py`
- [ ] `backend/tests/test_approvals.py`
- [ ] `backend/tests/test_actions.py`

### 15. Frontend 테스트
- [ ] 컴포넌트 테스트 (Vitest)

### 16. E2E 테스트
- [ ] Playwright 설정
- [ ] 로그인 플로우
- [ ] 사고 보고 플로우

---

## P0: Release Gate

### 17. 보안 스캔
- [ ] Bandit SAST 실행
- [ ] pip-audit SCA 실행
- [ ] HIGH 취약점 0개 확인

### 18. 문서화
- [ ] `docs/api-reference.md`
- [ ] `docs/security-review.md`

### 19. 최종 검증
- [ ] 테스트 통과
- [ ] PIPA 문서 완료
- [ ] Release Gate 워크플로우 통과

---

## 현재 진행 상황

**완료:** 1/19 섹션

**다음 작업:** 2. Action 모델 생성 (`backend/app/models/action.py`)

---

## 작업 순서 (권장)

```
1. docs/pipa-checklist.md         ← 현재
2. backend/app/models/action.py
3. Alembic 초기화
4. backend/app/security/dependencies.py (인증)
5. backend/app/api/auth.py (JWT)
6. backend/app/api/incidents.py (CRUD)
7. backend/app/api/approvals.py
8. backend/app/api/actions.py
9. backend/app/api/attachments.py
10. Frontend API 연결
11. 테스트 작성
12. 보안 스캔 + Release Gate
```
