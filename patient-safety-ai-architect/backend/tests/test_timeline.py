"""
Incident Timeline API Tests

Tests for:
- Timeline event generation
- Status progression
- Reporter feedback visibility
"""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient

from app.models.action import Action, ActionStatus
from app.models.approval import Approval


@pytest.mark.asyncio
async def test_get_incident_timeline_basic(
    client_as_qps: AsyncClient,
    sample_incident,
):
    """Get basic timeline for an incident."""
    response = await client_as_qps.get(
        f"/api/incidents/{sample_incident.id}/timeline"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["incident_id"] == sample_incident.id
    assert data["current_status"] == "submitted"
    assert len(data["events"]) >= 1

    # First event should be submission
    first_event = data["events"][0]
    assert first_event["event_type"] == "submitted"
    assert first_event["status"] == "submitted"
    assert first_event["icon"] == "document"


@pytest.mark.asyncio
async def test_timeline_with_actions(
    client_as_qps: AsyncClient,
    db_session,
    sample_incident,
    qps_user,
):
    """Timeline includes action events."""
    # Create an action for the incident
    action = Action(
        incident_id=sample_incident.id,
        title="환경 개선 조치",
        description="침대 난간 점검 및 보수",
        owner="김담당",
        due_date=datetime.now(timezone.utc).date(),
        definition_of_done="모든 침대 난간 점검 완료 기록",
        status=ActionStatus.OPEN,
        created_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()

    response = await client_as_qps.get(
        f"/api/incidents/{sample_incident.id}/timeline"
    )

    assert response.status_code == 200
    data = response.json()

    # Should have action_created event
    event_types = [e["event_type"] for e in data["events"]]
    assert "action_created" in event_types

    # Find the action event
    action_event = next(e for e in data["events"] if e["event_type"] == "action_created")
    assert "환경 개선" in action_event["detail"]
    assert action_event["actor"] == "김담당"


@pytest.mark.asyncio
async def test_timeline_with_completed_action(
    client_as_qps: AsyncClient,
    db_session,
    sample_incident,
    qps_user,
):
    """Timeline shows completed action events."""
    action = Action(
        incident_id=sample_incident.id,
        title="교육 실시",
        description="낙상 예방 교육 실시",
        owner="박담당",
        due_date=datetime.now(timezone.utc).date(),
        definition_of_done="교육 완료 서명",
        status=ActionStatus.COMPLETED,
        created_by_id=qps_user.id,
        completed_at=datetime.now(timezone.utc),
        completed_by_id=qps_user.id,
    )
    db_session.add(action)
    await db_session.commit()

    response = await client_as_qps.get(
        f"/api/incidents/{sample_incident.id}/timeline"
    )

    assert response.status_code == 200
    data = response.json()

    event_types = [e["event_type"] for e in data["events"]]
    assert "action_created" in event_types
    assert "action_completed" in event_types


@pytest.mark.asyncio
async def test_timeline_reporter_access(
    client_as_reporter: AsyncClient,
    sample_incident,
):
    """Reporter can view timeline of their own incident."""
    response = await client_as_reporter.get(
        f"/api/incidents/{sample_incident.id}/timeline"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["incident_id"] == sample_incident.id


@pytest.mark.asyncio
async def test_timeline_nonexistent_incident(client_as_qps: AsyncClient):
    """Timeline for nonexistent incident returns 404."""
    response = await client_as_qps.get("/api/incidents/99999/timeline")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_timeline_next_expected_action_submitted(
    client_as_qps: AsyncClient,
    sample_incident,
):
    """Next expected action for submitted incident."""
    response = await client_as_qps.get(
        f"/api/incidents/{sample_incident.id}/timeline"
    )

    assert response.status_code == 200
    data = response.json()

    # Submitted incidents should show QPS review pending
    assert data["next_expected_action"] == "QPS 검토 대기 중"


@pytest.mark.asyncio
async def test_timeline_events_sorted_by_time(
    client_as_qps: AsyncClient,
    db_session,
    sample_incident,
    qps_user,
):
    """Timeline events are sorted chronologically."""
    # Create multiple actions with different times
    action1 = Action(
        incident_id=sample_incident.id,
        title="First Action",
        description="First",
        owner="담당자1",
        due_date=datetime.now(timezone.utc).date(),
        definition_of_done="DoD",
        status=ActionStatus.OPEN,
        created_by_id=qps_user.id,
    )
    db_session.add(action1)
    await db_session.commit()

    action2 = Action(
        incident_id=sample_incident.id,
        title="Second Action",
        description="Second",
        owner="담당자2",
        due_date=datetime.now(timezone.utc).date(),
        definition_of_done="DoD",
        status=ActionStatus.OPEN,
        created_by_id=qps_user.id,
    )
    db_session.add(action2)
    await db_session.commit()

    response = await client_as_qps.get(
        f"/api/incidents/{sample_incident.id}/timeline"
    )

    assert response.status_code == 200
    data = response.json()

    # Check events are in chronological order
    events = data["events"]
    for i in range(len(events) - 1):
        current_time = events[i]["occurred_at"]
        next_time = events[i + 1]["occurred_at"]
        assert current_time <= next_time, "Events should be sorted by time"


@pytest.mark.asyncio
async def test_timeline_closed_incident(
    client_as_qps: AsyncClient,
    db_session,
    sample_incident,
):
    """Timeline shows closed event for closed incidents."""
    # Close the incident
    sample_incident.status = "closed"
    sample_incident.updated_at = datetime.now(timezone.utc)
    await db_session.commit()

    response = await client_as_qps.get(
        f"/api/incidents/{sample_incident.id}/timeline"
    )

    assert response.status_code == 200
    data = response.json()

    event_types = [e["event_type"] for e in data["events"]]
    assert "closed" in event_types

    closed_event = next(e for e in data["events"] if e["event_type"] == "closed")
    assert closed_event["detail"] == "사건 종결"
    assert closed_event["icon"] == "lock"
