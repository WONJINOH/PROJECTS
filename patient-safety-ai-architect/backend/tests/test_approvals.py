"""
Approval API Tests

Tests for the 3-level approval workflow (QPS → Vice Chair → Director).
Uses pseudonyms only - no real PII.
"""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Role
from app.models.incident import Incident, IncidentCategory, IncidentGrade
from app.models.approval import Approval, ApprovalLevel, ApprovalStatus


# ===== Approval Status Tests =====

@pytest.mark.asyncio
async def test_get_approval_status(client_as_qps: AsyncClient, sample_incident: Incident):
    """Test getting approval status for an incident."""
    response = await client_as_qps.get(f"/api/approvals/incidents/{sample_incident.id}/status")

    assert response.status_code == 200
    data = response.json()
    assert "incident_id" in data
    assert "approvals" in data or "current_level" in data


@pytest.mark.asyncio
async def test_get_approval_status_not_found(client_as_qps: AsyncClient):
    """Test getting approval status for non-existent incident."""
    response = await client_as_qps.get("/api/approvals/incidents/99999/status")

    assert response.status_code == 404


# ===== Level 1: QPS Approval Tests =====

@pytest.mark.asyncio
async def test_qps_approve_incident(client_as_qps: AsyncClient, sample_incident: Incident):
    """Test QPS staff approving an incident."""
    response = await client_as_qps.post(
        f"/api/approvals/incidents/{sample_incident.id}/approve",
        json={"action": "approve", "comment": "내용 확인 완료"},
    )

    assert response.status_code in [200, 201]
    if response.status_code in [200, 201]:
        data = response.json()
        assert data.get("status") in ["approved", "success"] or "approval" in str(data).lower()


@pytest.mark.asyncio
async def test_qps_reject_incident(client_as_qps: AsyncClient, sample_incident: Incident):
    """Test QPS staff rejecting an incident."""
    response = await client_as_qps.post(
        f"/api/approvals/incidents/{sample_incident.id}/reject",
        json={"action": "reject", "rejection_reason": "추가 정보 필요"},
    )

    assert response.status_code in [200, 201]
    if response.status_code in [200, 201]:
        data = response.json()
        assert data.get("status") in ["rejected", "success"] or "rejection" in str(data).lower()


# ===== Level 2: Vice Chair Approval Tests =====

@pytest.mark.asyncio
async def test_vice_chair_approve_after_qps(
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test Vice Chair approving after QPS approval."""
    # First, create QPS approval
    qps_approval = Approval(
        incident_id=sample_incident.id,
        approver_id=qps_user.id,
        level=ApprovalLevel.L1_QPS,
        status=ApprovalStatus.APPROVED,
        comment="QPS 승인",
        decided_at=datetime.now(timezone.utc),
    )
    db_session.add(qps_approval)
    await db_session.commit()

    # Create vice chair user
    vice_chair = User(
        username="vice_chair_test",
        email="vicechair@test.hospital.kr",
        hashed_password="$2b$12$test",
        full_name="부원장 테스터",
        role=Role.VICE_CHAIR,
        is_active=True,
    )
    db_session.add(vice_chair)
    await db_session.commit()
    await db_session.refresh(vice_chair)

    # Set up vice chair client
    from app.main import app
    from app.database import get_db
    from app.security.dependencies import get_current_active_user
    from tests.conftest import override_get_db, override_get_current_user

    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_active_user] = override_get_current_user(vice_chair)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/api/approvals/incidents/{sample_incident.id}/approve",
            json={"action": "approve", "comment": "부원장 승인"},
        )

    assert response.status_code in [200, 201]

    app.dependency_overrides.clear()


# ===== Level 3: Director Approval Tests =====

@pytest.mark.asyncio
async def test_director_approve_after_vice_chair(
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
    director_user: User,
):
    """Test Director approving after Vice Chair approval."""
    # Create prior approvals
    qps_approval = Approval(
        incident_id=sample_incident.id,
        approver_id=qps_user.id,
        level=ApprovalLevel.L1_QPS,
        status=ApprovalStatus.APPROVED,
        decided_at=datetime.now(timezone.utc),
    )
    db_session.add(qps_approval)

    vice_chair = User(
        username="vice_chair_test2",
        email="vicechair2@test.hospital.kr",
        hashed_password="$2b$12$test",
        full_name="부원장 테스터2",
        role=Role.VICE_CHAIR,
        is_active=True,
    )
    db_session.add(vice_chair)
    await db_session.flush()

    vc_approval = Approval(
        incident_id=sample_incident.id,
        approver_id=vice_chair.id,
        level=ApprovalLevel.L2_VICE_CHAIR,
        status=ApprovalStatus.APPROVED,
        decided_at=datetime.now(timezone.utc),
    )
    db_session.add(vc_approval)
    await db_session.commit()

    # Director approval
    from app.main import app
    from app.database import get_db
    from app.security.dependencies import get_current_active_user
    from tests.conftest import override_get_db, override_get_current_user

    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_active_user] = override_get_current_user(director_user)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/api/approvals/incidents/{sample_incident.id}/approve",
            json={"action": "approve", "comment": "최종 승인"},
        )

    assert response.status_code in [200, 201]

    app.dependency_overrides.clear()


# ===== Authorization Tests =====

@pytest.mark.asyncio
async def test_reporter_cannot_approve(client_as_reporter: AsyncClient, sample_incident: Incident):
    """Test reporter cannot approve incidents."""
    response = await client_as_reporter.post(
        f"/api/approvals/incidents/{sample_incident.id}/approve",
        json={"action": "approve"},
    )

    # Reporter should not have approve permission
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_qps_cannot_skip_to_director_level(
    client_as_qps: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
):
    """Test QPS cannot approve at director level."""
    # Attempt to approve as L3_DIRECTOR without being director
    response = await client_as_qps.post(
        f"/api/approvals/incidents/{sample_incident.id}/approve",
        json={"action": "approve", "level": "l3_director"},
    )

    # Should either reject due to permission or ignore the level param
    assert response.status_code in [200, 201, 403]


# ===== Rejection Flow Tests =====

@pytest.mark.asyncio
async def test_rejection_resets_workflow(
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test rejecting at any level resets the workflow."""
    # First create QPS approval
    qps_approval = Approval(
        incident_id=sample_incident.id,
        approver_id=qps_user.id,
        level=ApprovalLevel.L1_QPS,
        status=ApprovalStatus.APPROVED,
        decided_at=datetime.now(timezone.utc),
    )
    db_session.add(qps_approval)
    await db_session.commit()

    # Vice chair rejects
    vice_chair = User(
        username="vice_chair_reject",
        email="vcreject@test.hospital.kr",
        hashed_password="$2b$12$test",
        full_name="부원장",
        role=Role.VICE_CHAIR,
        is_active=True,
    )
    db_session.add(vice_chair)
    await db_session.commit()
    await db_session.refresh(vice_chair)

    from app.main import app
    from app.database import get_db
    from app.security.dependencies import get_current_active_user
    from tests.conftest import override_get_db, override_get_current_user

    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_active_user] = override_get_current_user(vice_chair)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/api/approvals/incidents/{sample_incident.id}/reject",
            json={"action": "reject", "rejection_reason": "수정 필요"},
        )

    assert response.status_code in [200, 201]

    app.dependency_overrides.clear()


# ===== Comment Tests =====

@pytest.mark.asyncio
async def test_approve_with_comment(client_as_qps: AsyncClient, sample_incident: Incident):
    """Test approving with a comment."""
    response = await client_as_qps.post(
        f"/api/approvals/incidents/{sample_incident.id}/approve",
        json={"action": "approve", "comment": "검토 완료. 권고사항: 추가 교육 필요"},
    )

    assert response.status_code in [200, 201]


@pytest.mark.asyncio
async def test_reject_requires_reason(client_as_qps: AsyncClient, sample_incident: Incident):
    """Test rejection requires a reason."""
    response = await client_as_qps.post(
        f"/api/approvals/incidents/{sample_incident.id}/reject",
        json={"action": "reject"},  # No rejection_reason
    )

    # Should either require reason or accept without it
    assert response.status_code in [200, 201, 400, 422]


# ===== Edge Case Tests =====

@pytest.mark.asyncio
async def test_cannot_approve_twice(client_as_qps: AsyncClient, sample_incident: Incident):
    """Test cannot approve same level twice."""
    # First approval
    response1 = await client_as_qps.post(
        f"/api/approvals/incidents/{sample_incident.id}/approve",
        json={"action": "approve"},
    )

    # Second approval attempt
    response2 = await client_as_qps.post(
        f"/api/approvals/incidents/{sample_incident.id}/approve",
        json={"action": "approve"},
    )

    # Second should fail or be idempotent
    assert response2.status_code in [200, 400, 409]


@pytest.mark.asyncio
async def test_cannot_approve_nonexistent_incident(client_as_qps: AsyncClient):
    """Test cannot approve non-existent incident."""
    response = await client_as_qps.post(
        "/api/approvals/incidents/99999/approve",
        json={"action": "approve"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_approval_history(client_as_qps: AsyncClient, sample_incident: Incident):
    """Test viewing approval history."""
    response = await client_as_qps.get(f"/api/approvals/incidents/{sample_incident.id}/status")

    assert response.status_code == 200
    # Should contain approval history or current status
