# 환자안전사고 보고 시스템 (Patient Safety Incident Reporting System)

> 요양병원을 위한 내부 QI(Quality Improvement) 시스템

## 🎯 비전

환자안전사고를 체계적으로 수집, 분석, 관리하여 의료 품질을 향상시키고 재발을 방지합니다.

### 3가지 시나리오

| 단계 | 범위 | 규제 | 상태 |
|------|------|------|------|
| **Phase 1** | 한국 요양병원 내부 QI | PIPA (개인정보보호법) | ✅ 현재 |
| **Phase 2** | 미국 시장 확장 | HIPAA | 🔜 계획 |
| **Phase 3** | 의료기기 인증 | MFDS/FDA SaMD | 🔜 계획 |

## 🚀 빠른 시작

### 사전 요구사항

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### 실행

```bash
# 1. 환경 설정
cp .env.example .env

# 2. Docker 실행
docker-compose up -d

# 3. 접속
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/docs
# Database: localhost:5432
```

### 개발 모드

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 📋 주요 기능 (Phase 1)

- **사고 보고**: 낙상, 투약, 욕창, 감염 등 환자안전사고 보고
- **3단계 승인**: QI담당자 → 부원장 → 원장
- **첨부파일**: 증거 자료 업로드 (로컬 저장)
- **대시보드**: 실시간 지표 시각화
- **감사 로그**: PIPA Art. 29 준수 접근 기록

## 🏗️ 기술 스택

### Backend
- **Python 3.11+** + **FastAPI**
- **PostgreSQL 15+** (암호화 at-rest)
- **SQLAlchemy** (async)
- **Argon2** (패스워드 해싱)

### Frontend
- **React 18** + **TypeScript**
- **Vite** (빌드)
- **TailwindCSS** (스타일링)
- **React Query** (서버 상태)
- **Zustand** (클라이언트 상태)

### Infrastructure
- **Docker** + **Docker Compose**
- **GitHub Actions** (CI/CD)
- **AWS** (Production)

## 🔒 보안

### 스캔 자동화
- **SAST**: Bandit, Semgrep
- **SCA**: pip-audit, npm audit
- **Secrets**: Gitleaks
- **SBOM**: CycloneDX

### 릴리스 게이트
```
PASS 조건:
- High/Critical = 0 (또는 승인된 예외)
- Medium에 대한 해결 계획 + 기한
- PIPA 증거 문서 존재
```

## 📁 프로젝트 구조

```
patient-safety-ai-architect/
├── backend/           # FastAPI 백엔드
│   ├── app/
│   │   ├── api/       # 라우터
│   │   ├── models/    # DB 모델
│   │   ├── schemas/   # Pydantic 스키마
│   │   └── security/  # RBAC, 암호화, 감사
│   └── tests/
├── frontend/          # React 프론트엔드
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── utils/
├── docs/              # 문서 (PIPA 증거 등)
├── config/            # 환경 설정
├── infrastructure/    # Docker, Terraform
├── outputs/           # 스캔 결과 (CI)
└── .github/workflows/ # CI/CD
```

## 👥 역할 (RBAC)

| 역할 | 설명 | 주요 권한 |
|------|------|-----------|
| REPORTER | 보고자 | 자기 사고 보고/조회 |
| QPS_STAFF | QI담당자 | 부서별 조회, L1 승인 |
| VICE_CHAIR | 부원장 | 전체 조회, L2 승인 |
| DIRECTOR | 원장 | 전체 조회, L3 승인, 삭제 |
| ADMIN | 시스템관리자 | 사용자 관리 (데이터 접근 없음) |

## 📚 문서

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - 시스템 아키텍처
- [API_SPECIFICATION.md](docs/API_SPECIFICATION.md) - API 명세
- [SECURITY_DESIGN.md](docs/SECURITY_DESIGN.md) - 보안 설계
- [EXPANSION_ROADMAP.md](docs/EXPANSION_ROADMAP.md) - 확장 로드맵

## 🤝 기여

[CONTRIBUTING.md](.github/CONTRIBUTING.md) 참조

## 📄 라이선스

MIT License - [LICENSE](LICENSE) 참조

---

**주의**: 이 시스템은 내부 QI 목적으로만 사용됩니다. 실제 환자 데이터 사용 시 PIPA 준수를 확인하세요.
