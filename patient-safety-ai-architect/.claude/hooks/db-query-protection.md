---
event: PreToolUse
tools:
  - Bash
---

# DB Query Protection Hook

## Purpose
DB 쿼리 실행 시 실제 환자 데이터 노출을 방지합니다.

## 차단/경고 대상 명령어

### 1. 직접 DB 쿼리 (높은 위험)
```
psql -c "SELECT * FROM ..."
docker exec ... psql ...
python -c "...execute..."
```

### 2. 데이터 조회 패턴
```
SELECT * FROM incidents
SELECT * FROM users
SELECT * FROM patients
SELECT * FROM audit_logs
```

### 3. 로그/덤프 명령
```
pg_dump
cat *.log
tail -f *api*.log
docker logs patient-safety-backend
```

## Action

### 감지 시 동작:

1. **BLOCK** 하고 다음 메시지 표시:
```
⚠️ DB 데이터 조회 명령 감지

이 명령은 실제 환자 데이터를 노출할 수 있습니다.
정말 실행하시겠습니까?

안전한 대안:
- 스키마만 확인: \d 테이블명
- 카운트만 확인: SELECT COUNT(*) FROM ...
- 테스트 데이터로 확인: WHERE id = 'test-...'
```

2. 사용자가 명시적으로 승인하면 실행

## 허용되는 안전한 명령

```sql
-- 스키마 확인
\d incidents
\dt
DESCRIBE incidents;

-- 개수만 확인
SELECT COUNT(*) FROM incidents;

-- 테이블 구조
SELECT column_name, data_type FROM information_schema.columns;

-- 마이그레이션
alembic upgrade head
alembic history
```

## 예외 상황

다음 경우는 경고 없이 허용:
- `--help` 플래그가 포함된 명령
- `alembic` 마이그레이션 명령
- `CREATE`, `ALTER` DDL 명령 (데이터 조회 아님)
