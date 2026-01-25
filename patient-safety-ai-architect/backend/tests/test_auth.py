"""
Authentication API Tests

Tests for login, logout, token verification, and user management.
Uses pseudonyms only - no real PII.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Role
from app.security.password import hash_password


# ===== Login Tests =====

@pytest.mark.asyncio
async def test_login_success(client_as_reporter: AsyncClient, db_session: AsyncSession, reporter_user: User):
    """Test successful login with valid credentials."""
    # Create user with known password
    reporter_user.hashed_password = hash_password("testpassword123")
    await db_session.commit()

    # Clear auth overrides and login manually
    from app.main import app
    from app.database import get_db
    from tests.conftest import override_get_db

    app.dependency_overrides[get_db] = override_get_db(db_session)
    # Remove current_user override for this test
    from app.security.dependencies import get_current_active_user
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]

    async with AsyncClient(transport=client_as_reporter._transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            data={"username": "reporter_tester", "password": "testpassword123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client_as_reporter: AsyncClient, db_session: AsyncSession, reporter_user: User):
    """Test login fails with invalid password."""
    reporter_user.hashed_password = hash_password("correctpassword")
    await db_session.commit()

    from app.main import app
    from app.database import get_db
    from app.security.dependencies import get_current_active_user
    from tests.conftest import override_get_db

    app.dependency_overrides[get_db] = override_get_db(db_session)
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]

    async with AsyncClient(transport=client_as_reporter._transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            data={"username": "reporter_tester", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_invalid_username(client_as_reporter: AsyncClient, db_session: AsyncSession):
    """Test login fails with non-existent username."""
    from app.main import app
    from app.database import get_db
    from app.security.dependencies import get_current_active_user
    from tests.conftest import override_get_db

    app.dependency_overrides[get_db] = override_get_db(db_session)
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]

    async with AsyncClient(transport=client_as_reporter._transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            data={"username": "nonexistent_user", "password": "anypassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client_as_reporter: AsyncClient, db_session: AsyncSession, reporter_user: User):
    """Test login fails for inactive user."""
    reporter_user.hashed_password = hash_password("testpassword123")
    reporter_user.is_active = False
    await db_session.commit()

    from app.main import app
    from app.database import get_db
    from app.security.dependencies import get_current_active_user
    from tests.conftest import override_get_db

    app.dependency_overrides[get_db] = override_get_db(db_session)
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]

    async with AsyncClient(transport=client_as_reporter._transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            data={"username": "reporter_tester", "password": "testpassword123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


# ===== Token Verification Tests =====

@pytest.mark.asyncio
async def test_get_me_authenticated(client_as_qps: AsyncClient, qps_user: User):
    """Test getting current user info when authenticated."""
    response = await client_as_qps.get("/api/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == qps_user.username
    assert data["email"] == qps_user.email
    assert data["role"] == qps_user.role.value


@pytest.mark.asyncio
async def test_get_me_unauthenticated(db_session: AsyncSession):
    """Test getting current user info without authentication fails."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.database import get_db
    from tests.conftest import override_get_db

    app.dependency_overrides = {get_db: override_get_db(db_session)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/auth/me")

    assert response.status_code == 401


# ===== Logout Tests =====

@pytest.mark.asyncio
async def test_logout_success(client_as_qps: AsyncClient):
    """Test successful logout."""
    response = await client_as_qps.post("/api/auth/logout")
    assert response.status_code == 204


# ===== User Registration Tests =====

@pytest.mark.asyncio
async def test_register_user_as_admin(db_session: AsyncSession):
    """Test registering new user as admin."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.database import get_db
    from app.security.dependencies import get_current_active_user
    from tests.conftest import override_get_db, override_get_current_user

    # Create admin user
    admin = User(
        username="admin_tester",
        email="admin@test.hospital.kr",
        hashed_password=hash_password("adminpass"),
        full_name="관리자",
        role=Role.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_active_user] = override_get_current_user(admin)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "new_user",
                "email": "newuser@test.hospital.kr",
                "password": "newuserpass123",
                "full_name": "신규 사용자",
                "role": "reporter",
                "department": "외과",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_user"
    assert data["role"] == "reporter"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_user_as_non_admin_fails(client_as_qps: AsyncClient):
    """Test registering new user as non-admin fails."""
    response = await client_as_qps.post(
        "/api/auth/register",
        json={
            "username": "another_user",
            "email": "another@test.hospital.kr",
            "password": "password123",
            "full_name": "다른 사용자",
            "role": "reporter",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_register_duplicate_username(db_session: AsyncSession, reporter_user: User):
    """Test registering user with duplicate username fails."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    from app.database import get_db
    from app.security.dependencies import get_current_active_user
    from tests.conftest import override_get_db, override_get_current_user

    admin = User(
        username="admin_tester",
        email="admin@test.hospital.kr",
        hashed_password=hash_password("adminpass"),
        full_name="관리자",
        role=Role.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_active_user] = override_get_current_user(admin)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register",
            json={
                "username": reporter_user.username,  # Duplicate
                "email": "unique@test.hospital.kr",
                "password": "password123",
                "full_name": "중복 사용자",
                "role": "reporter",
            },
        )

    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]

    app.dependency_overrides.clear()


# ===== Password Change Tests =====

@pytest.mark.asyncio
async def test_change_password_success(client_as_qps: AsyncClient, db_session: AsyncSession, qps_user: User):
    """Test successful password change."""
    qps_user.hashed_password = hash_password("oldpassword123")
    await db_session.commit()

    response = await client_as_qps.put(
        "/api/auth/me/password",
        params={"current_password": "oldpassword123", "new_password": "newpassword123"},
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_change_password_wrong_current(client_as_qps: AsyncClient, db_session: AsyncSession, qps_user: User):
    """Test password change fails with wrong current password."""
    qps_user.hashed_password = hash_password("correctpassword")
    await db_session.commit()

    response = await client_as_qps.put(
        "/api/auth/me/password",
        params={"current_password": "wrongpassword", "new_password": "newpassword123"},
    )

    assert response.status_code == 400
    assert "Current password is incorrect" in response.json()["detail"]
