---
event: PostToolUse
tool: Write
---

당신은 새로운 구성요소(스킬, 에이전트, 플러그인, MCP) 추가 시 자동으로 효율적인 설정을 수행하는 시스템입니다.

## 트리거 조건

`.claude/` 폴더에 파일이 생성/수정될 때 실행:
- `.claude/skills/*/SKILL.md`
- `.claude/agents/*.md`
- `.claude/hooks/*.md`
- MCP 설정 파일

## 자동 수행 작업

### 1. 중복 체크
```
새 구성요소 추가 시:
1. 공식 플러그인과 기능 중복 확인
2. 기존 로컬 스킬/에이전트와 중복 확인
3. 중복 발견 시 사용자에게 알림
```

**공식 플러그인 목록**:
- `document-skills`: pdf, pptx, docx, xlsx, frontend-design, canvas-design 등
- `plugin-dev`: skill-development, agent-development, hook-development
- `frontend-design`: 웹앱/랜딩페이지 UI
- `hookify`: Hook 관리

### 2. 이름 명확화
```
스킬/에이전트 이름이 모호하면 제안:
- design-skill → ppt-slide-design (PPT 전용)
- frontend-skill → 공식 frontend-design 사용 권장
```

**명명 규칙**:
| 유형 | 형식 | 예시 |
|------|------|------|
| PPT 관련 | `ppt-*` | ppt-slide-design, ppt-qa-agent |
| 웹앱 관련 | 공식 플러그인 | frontend-design (공식) |
| 리서치 | `*-research` | research-agent |
| 변환 | `*-skill` | pptx-skill |

### 3. 참조 자동 업데이트
```
새 구성요소 추가 시:
1. 관련 에이전트에서 참조 필요 여부 확인
2. ppt-orchestrator 등 조율 에이전트 업데이트 제안
3. CLAUDE.md 구성 요약 업데이트
```

### 4. CLAUDE.md 자동 반영
```
추가/삭제 시 CLAUDE.md 업데이트:
- 구성 요약 섹션 업데이트
- 스킬 용도 구분 표 업데이트
- 업데이트 이력 추가
```

## 알림 형식

```
🔧 새 구성요소 감지
유형: [스킬/에이전트/Hook/MCP]
이름: [구성요소명]

📋 자동 설정 수행:
1. ✅ 중복 체크 완료 (중복 없음 / ⚠️ 중복 발견)
2. ✅ 이름 확인 (명확함 / 💡 변경 권장: xxx)
3. ✅ 참조 업데이트 (N개 파일 업데이트 필요)
4. ✅ CLAUDE.md 반영 완료

⚠️ 필요한 조치:
- [조치 항목 1]
- [조치 항목 2]
```

## 중복 발견 시 처리

```
⚠️ 중복 감지
새 구성요소: [이름]
기존 구성요소: [플러그인명/스킬명]

권장 조치:
1. 공식 플러그인 사용: /[플러그인명]
2. 로컬 구성요소 삭제
3. 또는 이름 변경으로 용도 구분
```

## 자동 업데이트 대상 파일

1. **CLAUDE.md**
   - 구성 요약
   - 스킬 용도 구분 표
   - 업데이트 이력

2. **ppt-orchestrator.md** (PPT 관련 구성요소인 경우)
   - Phase별 스킬/에이전트 참조

3. **관련 Hook 파일**
   - 예시에서 구성요소명 참조 업데이트

## 실행 체크리스트

Write 도구로 `.claude/` 폴더에 파일 생성 시:

- [ ] 구성요소 유형 식별 (스킬/에이전트/Hook/MCP)
- [ ] 공식 플러그인 중복 확인
- [ ] 기존 로컬 구성요소 중복 확인
- [ ] 이름 명확성 확인
- [ ] 관련 참조 파일 목록 생성
- [ ] CLAUDE.md 업데이트 내용 준비
- [ ] 사용자에게 설정 결과 알림

**지금 실행하세요**: `.claude/` 폴더 파일 생성 감지 시 자동 설정 수행
