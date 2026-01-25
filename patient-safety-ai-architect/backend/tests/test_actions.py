"""
Action (CAPA) API Tests

Tests for Corrective and Preventive Action lifecycle.
Uses pseudonyms only - no real PII.
"""

import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.incident import Incident
from app.models.action import Action, ActionStatus, ActionPriority


# ===== Create Action Tests =====

@pytest.mark.asyncio
async def test_create_action_success(client_as_qps: AsyncClient, sample_incident: Incident):
    """Test creating a CAPA action for an incident."""
    action_data = {
        "incident_id": sample_incident.id,
        "title": "낙상 예방 교육 강화",
        "description": "병동 직원 대상 낙상 예방 교육 실시",
        "owner": "김QPS",
        "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d"),
        "definition_of_done": "교육 완료 및 평가 90점 이상",
        "priority": "high",
    }

    response = await client_as_qps.post("/api/actions/", json=action_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "낙상 예방 교육 강화"
    assert data["status"] == "open"
    assert data["priority"] == "high"


@pytest.mark.asyncio
async def test_create_action_missing_required(client_as_qps: AsyncClient, sample_incident: Incident):
    """Test creating action fails without required fields."""
    action_data = {
        "incident_id": sample_incident.id,
        "title": "조치 제목",
        # missing owner, due_date, definition_of_done
    }

    response = await client_as_qps.post("/api/actions/", json=action_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_action_all_priorities(client_as_qps: AsyncClient, sample_incident: Incident):
    """Test creating actions with all priority levels."""
    priorities = ["low", "medium", "high", "critical"]

    for priority in priorities:
        action_data = {
            "incident_id": sample_incident.id,
            "title": f"{priority} 우선순위 조치",
            "owner": "테스터",
            "due_date": "2026-03-01",
            "definition_of_done": "완료 기준",
            "priority": priority,
        }

        response = await client_as_qps.post("/api/actions/", json=action_data)
        assert response.status_code == 201, f"Failed for priority: {priority}"


# ===== Read Action Tests =====

@pytest.mark.asyncio
async def test_get_action_by_id(
    client_as_qps: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test getting action by ID."""
    action = Action(
        incident_id=sample_incident.id,
        title="테스트 조치",
        owner="담당자",
        due_date=datetime.now(timezone.utc).date() + timedelta(days=14),
        definition_of_done="완료 조건",
        priority=ActionPriority.MEDIUM,
        created_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    response = await client_as_qps.get(f"/api/actions/{action.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == action.id
    assert data["title"] == "테스트 조치"


@pytest.mark.asyncio
async def test_list_actions_by_incident(
    client_as_qps: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test listing actions for an incident."""
    # Create multiple actions
    for i in range(3):
        action = Action(
            incident_id=sample_incident.id,
            title=f"조치 {i+1}",
            owner="담당자",
            due_date=datetime.now(timezone.utc).date() + timedelta(days=14),
            definition_of_done="완료 조건",
            priority=ActionPriority.MEDIUM,
            created_by_id=qps_user.id,
        )
        db_session.add(action)
    await db_session.commit()

    response = await client_as_qps.get(f"/api/actions/incident/{sample_incident.id}")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 3


@pytest.mark.asyncio
async def test_list_actions_filter_by_status(
    client_as_qps: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test filtering actions by status."""
    # Create action with specific status
    action = Action(
        incident_id=sample_incident.id,
        title="진행중 조치",
        owner="담당자",
        due_date=datetime.now(timezone.utc).date() + timedelta(days=14),
        definition_of_done="완료 조건",
        priority=ActionPriority.HIGH,
        status=ActionStatus.IN_PROGRESS,
        created_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()

    response = await client_as_qps.get(
        f"/api/actions/incident/{sample_incident.id}",
        params={"status": "in_progress"},
    )

    assert response.status_code == 200


# ===== Action Lifecycle Tests =====

@pytest.mark.asyncio
async def test_start_action(
    client_as_qps: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test starting an action (open → in_progress)."""
    action = Action(
        incident_id=sample_incident.id,
        title="시작할 조치",
        owner="담당자",
        due_date=datetime.now(timezone.utc).date() + timedelta(days=14),
        definition_of_done="완료 조건",
        priority=ActionPriority.HIGH,
        status=ActionStatus.OPEN,
        created_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    response = await client_as_qps.post(f"/api/actions/{action.id}/start")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_complete_action(
    client_as_qps: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test completing an action (in_progress → completed)."""
    action = Action(
        incident_id=sample_incident.id,
        title="완료할 조치",
        owner="담당자",
        due_date=datetime.now(timezone.utc).date() + timedelta(days=14),
        definition_of_done="완료 조건",
        priority=ActionPriority.HIGH,
        status=ActionStatus.IN_PROGRESS,
        created_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    response = await client_as_qps.post(
        f"/api/actions/{action.id}/complete",
        json={"completion_notes": "모든 교육 완료됨"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_verify_action(
    client_as_director: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test verifying an action (completed → verified)."""
    action = Action(
        incident_id=sample_incident.id,
        title="검증할 조치",
        owner="담당자",
        due_date=datetime.now(timezone.utc).date() + timedelta(days=14),
        definition_of_done="완료 조건",
        priority=ActionPriority.HIGH,
        status=ActionStatus.COMPLETED,
        created_by_id=qps_user.id,
        completed_at=datetime.now(timezone.utc),
        completed_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    response = await client_as_director.post(
        f"/api/actions/{action.id}/verify",
        json={"verification_notes": "증빙 확인 완료"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "verified"


@pytest.mark.asyncio
async def test_cancel_action(
    client_as_qps: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test cancelling an action."""
    action = Action(
        incident_id=sample_incident.id,
        title="취소할 조치",
        owner="담당자",
        due_date=datetime.now(timezone.utc).date() + timedelta(days=14),
        definition_of_done="완료 조건",
        priority=ActionPriority.LOW,
        status=ActionStatus.OPEN,
        created_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    response = await client_as_qps.post(f"/api/actions/{action.id}/cancel")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


# ===== Invalid State Transition Tests =====

@pytest.mark.asyncio
async def test_cannot_complete_open_action(
    client_as_qps: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test cannot complete action that hasn't started."""
    action = Action(
        incident_id=sample_incident.id,
        title="시작 안된 조치",
        owner="담당자",
        due_date=datetime.now(timezone.utc).date() + timedelta(days=14),
        definition_of_done="완료 조건",
        priority=ActionPriority.HIGH,
        status=ActionStatus.OPEN,  # Not started
        created_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    response = await client_as_qps.post(
        f"/api/actions/{action.id}/complete",
        json={"completion_notes": "완료"},
    )

    # Should fail - cannot complete without starting
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_cannot_verify_open_action(
    client_as_director: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test cannot verify action that hasn't been completed."""
    action = Action(
        incident_id=sample_incident.id,
        title="미완료 조치",
        owner="담당자",
        due_date=datetime.now(timezone.utc).date() + timedelta(days=14),
        definition_of_done="완료 조건",
        priority=ActionPriority.HIGH,
        status=ActionStatus.OPEN,
        created_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    response = await client_as_director.post(
        f"/api/actions/{action.id}/verify",
        json={"verification_notes": "검증"},
    )

    assert response.status_code in [400, 422]


# ===== Overdue Actions Tests =====

@pytest.mark.asyncio
async def test_list_overdue_actions(
    client_as_qps: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test listing overdue actions."""
    # Create overdue action
    overdue_action = Action(
        incident_id=sample_incident.id,
        title="기한 초과 조치",
        owner="담당자",
        due_date=datetime.now(timezone.utc).date() - timedelta(days=7),  # Past due
        definition_of_done="완료 조건",
        priority=ActionPriority.HIGH,
        status=ActionStatus.OPEN,
        created_by_id=qps_user.id,
    )
    db_session.add(overdue_action)
    await db_session.commit()

    response = await client_as_qps.get("/api/actions/overdue")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))


# ===== Update Action Tests =====

@pytest.mark.asyncio
async def test_update_action(
    client_as_qps: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test updating action details."""
    action = Action(
        incident_id=sample_incident.id,
        title="수정 전 조치",
        owner="원래 담당자",
        due_date=datetime.now(timezone.utc).date() + timedelta(days=14),
        definition_of_done="원래 완료 조건",
        priority=ActionPriority.MEDIUM,
        created_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    update_data = {
        "title": "수정된 조치",
        "owner": "새 담당자",
        "priority": "high",
    }

    response = await client_as_qps.put(f"/api/actions/{action.id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "수정된 조치"
    assert data["owner"] == "새 담당자"


# ===== Authorization Tests =====

@pytest.mark.asyncio
async def test_reporter_cannot_create_action(
    client_as_reporter: AsyncClient,
    sample_incident: Incident,
):
    """Test reporter cannot create actions."""
    action_data = {
        "incident_id": sample_incident.id,
        "title": "보고자 조치 시도",
        "owner": "담당자",
        "due_date": "2026-03-01",
        "definition_of_done": "완료 조건",
    }

    response = await client_as_reporter.post("/api/actions/", json=action_data)

    # Reporter should not have permission
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_only_director_can_verify(
    client_as_qps: AsyncClient,
    db_session: AsyncSession,
    sample_incident: Incident,
    qps_user: User,
):
    """Test only director+ can verify actions."""
    action = Action(
        incident_id=sample_incident.id,
        title="QPS 검증 시도 조치",
        owner="담당자",
        due_date=datetime.now(timezone.utc).date() + timedelta(days=14),
        definition_of_done="완료 조건",
        priority=ActionPriority.HIGH,
        status=ActionStatus.COMPLETED,
        created_by_id=qps_user.id,
        completed_at=datetime.now(timezone.utc),
        completed_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()
    await db_session.refresh(action)

    response = await client_as_qps.post(
        f"/api/actions/{action.id}/verify",
        json={"verification_notes": "검증"},
    )

    # QPS cannot verify - only director+
    assert response.status_code == 403
