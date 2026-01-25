# 데이터베이스 관리 도구 설정 가이드

## SQLTools 확장 프로그램 설치

Cursor/VS Code에서 데이터베이스를 시각적으로 관리하기 위해 SQLTools 확장 프로그램을 설치합니다.

### 1단계: 확장 프로그램 설치

1. Cursor에서 `Ctrl+Shift+X` (또는 `Cmd+Shift+X` on Mac)를 눌러 확장 프로그램 패널을 엽니다.

2. 다음 확장 프로그램을 검색하여 설치합니다:
   - **SQLTools** (mtxr.sqltools)
   - **SQLTools PostgreSQL/Redshift** (mtxr.sqltools-driver-pg)

   또는 터미널에서 설치:
   ```bash
   code --install-extension mtxr.sqltools
   code --install-extension mtxr.sqltools-driver-pg
   ```

### 2단계: 데이터베이스 연결

1. Cursor를 재시작합니다.

2. 왼쪽 사이드바에서 **SQLTools** 아이콘을 클릭합니다 (데이터베이스 모양 아이콘).

3. **Connections** 섹션에서 **Patient Safety DB (Local)** 연결을 찾습니다.

4. 연결을 우클릭하고 **Connect**를 선택합니다.

5. 비밀번호를 입력하라는 메시지가 나타나면 `postgres`를 입력합니다.

### 3단계: 데이터베이스 사용

연결이 성공하면 다음을 수행할 수 있습니다:

- **테이블 탐색**: 연결을 확장하여 데이터베이스, 스키마, 테이블을 볼 수 있습니다.
- **쿼리 실행**: 새 SQL 파일을 만들고 쿼리를 작성한 후 실행할 수 있습니다.
- **데이터 조회**: 테이블을 우클릭하고 **Show Table Records**를 선택하여 데이터를 볼 수 있습니다.

## 대안: 터미널에서 접속

Docker 컨테이너가 실행 중인 경우, 터미널에서 직접 접속할 수 있습니다:

```bash
# Docker 컨테이너 내부에서 psql 실행
docker exec -it patient-safety-db psql -U postgres -d patient_safety
```

## 연결 정보

- **호스트**: `localhost`
- **포트**: `5432`
- **데이터베이스**: `patient_safety`
- **사용자**: `postgres`
- **비밀번호**: `postgres`

## 문제 해결

### 연결이 안 될 때

1. Docker 컨테이너가 실행 중인지 확인:
   ```bash
   docker ps
   ```

2. 데이터베이스 컨테이너가 정상인지 확인:
   ```bash
   docker logs patient-safety-db
   ```

3. 포트가 열려있는지 확인:
   ```bash
   netstat -an | findstr 5432  # Windows
   ```

### 확장 프로그램이 작동하지 않을 때

1. Cursor를 완전히 재시작합니다.
2. 확장 프로그램이 최신 버전인지 확인합니다.
3. SQLTools 출력 패널에서 오류 메시지를 확인합니다.
