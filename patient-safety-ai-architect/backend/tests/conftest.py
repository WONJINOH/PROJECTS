"""
Test Configuration and Fixtures

Provides:
- In-memory SQLite database for tests
- Test client with async support
- Mock users with different roles
- Sample data fixtures
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User, Role
from app.models.incident import Incident, IncidentCategory, IncidentGrade
from app.models.risk import Risk, RiskSourceType, RiskCategory, RiskLevel, RiskStatus
from app.security.dependencies import get_current_active_user
from app.security.jwt import create_access_token


# Use PostgreSQL for testing if available, otherwise fallback to SQLite
# Set TEST_DATABASE_URL env var to use PostgreSQL
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:"
)

# Create async engine for testing
if "sqlite" in TEST_DATABASE_URL:
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
else:
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

# Session factory for testing
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        yield session

    # Drop all tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def qps_user(db_session: AsyncSession) -> User:
    """Create a QPS_STAFF user for testing."""
    user = User(
        username="qps_tester",
        email="qps@test.hospital.kr",
        hashed_password="$2b$12$test_hash",  # Not used in tests
        full_name="QPS 테스터",
        role=Role.QPS_STAFF,
        department="내과",  # Same as sample_incident for access control
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def director_user(db_session: AsyncSession) -> User:
    """Create a DIRECTOR user for testing."""
    user = User(
        username="director_tester",
        email="director@test.hospital.kr",
        hashed_password="$2b$12$test_hash",
        full_name="원장 테스터",
        role=Role.DIRECTOR,
        department="경영진",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def reporter_user(db_session: AsyncSession) -> User:
    """Create a REPORTER user for testing."""
    user = User(
        username="reporter_tester",
        email="reporter@test.hospital.kr",
        hashed_password="$2b$12$test_hash",
        full_name="보고자 테스터",
        role=Role.REPORTER,
        department="내과",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_incident(db_session: AsyncSession, reporter_user: User) -> Incident:
    """Create a sample incident for testing."""
    incident = Incident(
        category=IncidentCategory.FALL,
        grade=IncidentGrade.MODERATE,
        occurred_at=datetime.now(timezone.utc),
        location="3층 301호",
        description="환자가 침대에서 낙상함. 보호자 부재 중 화장실 가려다 발생.",
        immediate_action="의료진 호출, 환자 상태 확인, 진통제 투여",
        reported_at=datetime.now(timezone.utc),
        reporter_name="김간호",
        reporter_id=reporter_user.id,
        department="내과",
        status="submitted",
    )
    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)
    return incident


@pytest_asyncio.fixture
async def severe_incident(db_session: AsyncSession, reporter_user: User) -> Incident:
    """Create a severe incident for escalation testing."""
    incident = Incident(
        category=IncidentCategory.FALL,
        grade=IncidentGrade.SEVERE,
        occurred_at=datetime.now(timezone.utc),
        location="2층 ICU",
        description="중환자실 환자 낙상으로 골절 발생",
        immediate_action="응급 처치, X-ray 촬영, 정형외과 협진",
        reported_at=datetime.now(timezone.utc),
        reporter_name="박간호",
        reporter_id=reporter_user.id,
        department="중환자실",
        status="submitted",
    )
    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)
    return incident


@pytest_asyncio.fixture
async def sample_risk(db_session: AsyncSession, qps_user: User) -> Risk:
    """Create a sample risk for testing."""
    risk = Risk(
        risk_code="R-2026-001",
        title="낙상 위험 - 내과 병동",
        description="내과 병동에서 반복적인 낙상 발생. 환경 개선 필요.",
        source_type=RiskSourceType.PSR,
        category=RiskCategory.FALL,
        current_controls="낙상 예방 교육, 침대 난간 확인",
        probability=3,
        severity=4,
        owner_id=qps_user.id,
        created_by_id=qps_user.id,
        status=RiskStatus.IDENTIFIED,
    )
    db_session.add(risk)
    await db_session.commit()
    await db_session.refresh(risk)
    return risk


def override_get_db(db_session: AsyncSession):
    """Override get_db dependency with test session."""
    async def _override():
        yield db_session
    return _override


def override_get_current_user(user: User):
    """Override current user dependency for testing."""
    async def _override():
        return user
    return _override


@pytest_asyncio.fixture
async def client_as_qps(
    db_session: AsyncSession,
    qps_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Async client authenticated as QPS_STAFF."""
    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_active_user] = override_get_current_user(qps_user)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_as_director(
    db_session: AsyncSession,
    director_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Async client authenticated as DIRECTOR."""
    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_active_user] = override_get_current_user(director_user)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client_as_reporter(
    db_session: AsyncSession,
    reporter_user: User,
) -> AsyncGenerator[AsyncClient, None]:
    """Async client authenticated as REPORTER."""
    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_active_user] = override_get_current_user(reporter_user)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
