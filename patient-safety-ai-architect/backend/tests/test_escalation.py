"""
PSR → Risk Auto-Escalation Tests

Tests for:
- Escalation candidates detection
- Manual escalation
- Batch auto-escalation
- Grade-based escalation rules
"""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient

from app.models.incident import Incident, IncidentCategory, IncidentGrade
from app.models.risk import Risk


@pytest.mark.asyncio
async def test_get_escalation_candidates_empty(client_as_qps: AsyncClient):
    """No candidates when no severe incidents exist."""
    response = await client_as_qps.get("/api/risks/escalation/candidates")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_escalation_candidates_with_severe(
    client_as_qps: AsyncClient,
    severe_incident,
):
    """Severe incident appears as escalation candidate."""
    response = await client_as_qps.get("/api/risks/escalation/candidates")

    assert response.status_code == 200
    data = response.json()

    # Should find the severe incident
    incident_ids = [c["incident_id"] for c in data]
    assert severe_incident.id in incident_ids

    # Check candidate structure
    candidate = next(c for c in data if c["incident_id"] == severe_incident.id)
    assert candidate["grade"] == "severe"
    assert candidate["category"] == "fall"
    assert "영구 손상" in candidate["reason"] or "SEVERE" in candidate["reason"]
    assert candidate["suggested_probability"] >= 4
    assert candidate["suggested_severity"] >= 4


@pytest.mark.asyncio
async def test_escalation_candidates_excludes_already_escalated(
    client_as_qps: AsyncClient,
    db_session,
    severe_incident,
    qps_user,
):
    """Already escalated incidents are not shown as candidates."""
    # Manually escalate the incident first
    await client_as_qps.post(
        f"/api/risks/escalation/{severe_incident.id}",
        params={"reason": "Test escalation"}
    )

    # Now check candidates
    response = await client_as_qps.get("/api/risks/escalation/candidates")

    assert response.status_code == 200
    data = response.json()

    # Should NOT include already escalated incident
    incident_ids = [c["incident_id"] for c in data]
    assert severe_incident.id not in incident_ids


@pytest.mark.asyncio
async def test_manual_escalation(
    client_as_qps: AsyncClient,
    sample_incident,
):
    """Manually escalate a PSR to Risk."""
    response = await client_as_qps.post(
        f"/api/risks/escalation/{sample_incident.id}",
        params={
            "probability": 3,
            "severity": 4,
            "reason": "반복 발생 우려로 수동 승격",
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["source_type"] == "psr"
    assert data["source_incident_id"] == sample_incident.id
    assert data["probability"] == 3
    assert data["severity"] == 4
    assert data["risk_score"] == 12
    assert data["auto_escalated"] is True
    assert "수동 승격" in data["escalation_reason"]


@pytest.mark.asyncio
async def test_manual_escalation_default_ps(
    client_as_qps: AsyncClient,
    severe_incident,
):
    """Manual escalation uses default P×S based on grade."""
    response = await client_as_qps.post(
        f"/api/risks/escalation/{severe_incident.id}"
    )

    assert response.status_code == 201
    data = response.json()

    # SEVERE grade should have high P×S defaults
    assert data["probability"] >= 4
    assert data["severity"] >= 4


@pytest.mark.asyncio
async def test_manual_escalation_duplicate_fails(
    client_as_qps: AsyncClient,
    sample_incident,
):
    """Cannot escalate same incident twice."""
    # First escalation
    response1 = await client_as_qps.post(
        f"/api/risks/escalation/{sample_incident.id}"
    )
    assert response1.status_code == 201

    # Second escalation should fail
    response2 = await client_as_qps.post(
        f"/api/risks/escalation/{sample_incident.id}"
    )
    assert response2.status_code == 400
    assert "already escalated" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_manual_escalation_nonexistent_incident(client_as_qps: AsyncClient):
    """Escalating nonexistent incident returns error."""
    response = await client_as_qps.post("/api/risks/escalation/99999")

    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_batch_escalation(
    client_as_qps: AsyncClient,
    db_session,
    reporter_user,
):
    """Batch auto-escalation processes multiple severe incidents."""
    # Create multiple severe incidents
    for i in range(3):
        incident = Incident(
            category=IncidentCategory.MEDICATION,
            grade=IncidentGrade.SEVERE,
            occurred_at=datetime.now(timezone.utc),
            location=f"병동 {i+1}",
            description=f"심각한 투약 사고 {i+1}",
            immediate_action="응급 조치 시행",
            reported_at=datetime.now(timezone.utc),
            reporter_name="테스트",
            reporter_id=reporter_user.id,
            department="내과",
            status="submitted",
        )
        db_session.add(incident)
    await db_session.commit()

    # Run batch escalation
    response = await client_as_qps.post("/api/risks/escalation/run")

    assert response.status_code == 200
    data = response.json()

    assert data["escalated_count"] >= 3
    assert len(data["created_risks"]) >= 3

    # All created risks should be linked to PSR
    for risk in data["created_risks"]:
        assert risk["source_type"] == "psr"
        assert risk["auto_escalated"] is True


@pytest.mark.asyncio
async def test_batch_escalation_with_days_filter(
    client_as_qps: AsyncClient,
    severe_incident,
):
    """Batch escalation respects days filter."""
    # Should find recent incidents
    response = await client_as_qps.post(
        "/api/risks/escalation/run",
        params={"days": 7}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["escalated_count"] >= 1


@pytest.mark.asyncio
async def test_escalation_reporter_forbidden(
    client_as_reporter: AsyncClient,
    sample_incident,
):
    """Reporter cannot escalate incidents."""
    response = await client_as_reporter.post(
        f"/api/risks/escalation/{sample_incident.id}"
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_escalation_creates_initial_assessment(
    client_as_qps: AsyncClient,
    sample_incident,
):
    """Escalation creates an initial risk assessment."""
    # Escalate
    escalate_response = await client_as_qps.post(
        f"/api/risks/escalation/{sample_incident.id}"
    )
    risk_id = escalate_response.json()["id"]

    # Check assessments
    response = await client_as_qps.get(f"/api/risks/{risk_id}/assessments")

    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 1
    initial = data[-1]  # Last one should be initial (sorted desc)
    assert initial["assessment_type"] == "initial"
    assert "승격" in initial["rationale"]


@pytest.mark.asyncio
async def test_escalation_maps_category(
    client_as_qps: AsyncClient,
    db_session,
    reporter_user,
):
    """Escalation maps incident category to risk category."""
    # Create medication incident
    incident = Incident(
        category=IncidentCategory.MEDICATION,
        grade=IncidentGrade.SEVERE,
        occurred_at=datetime.now(timezone.utc),
        location="약국",
        description="고위험 약물 투약 오류",
        immediate_action="해독제 투여",
        reported_at=datetime.now(timezone.utc),
        reporter_name="약사",
        reporter_id=reporter_user.id,
        department="약제과",
        status="submitted",
    )
    db_session.add(incident)
    await db_session.commit()

    response = await client_as_qps.post(f"/api/risks/escalation/{incident.id}")

    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "medication"


@pytest.mark.asyncio
async def test_death_grade_escalation_ps(
    client_as_qps: AsyncClient,
    db_session,
    reporter_user,
):
    """DEATH grade incidents get highest P×S values."""
    incident = Incident(
        category=IncidentCategory.FALL,
        grade=IncidentGrade.DEATH,
        occurred_at=datetime.now(timezone.utc),
        location="응급실",
        description="낙상으로 인한 사망",
        immediate_action="CPR 시행, 사망 선언",
        reported_at=datetime.now(timezone.utc),
        reporter_name="담당의",
        reporter_id=reporter_user.id,
        department="응급실",
        status="submitted",
    )
    db_session.add(incident)
    await db_session.commit()

    response = await client_as_qps.post(f"/api/risks/escalation/{incident.id}")

    assert response.status_code == 201
    data = response.json()

    # DEATH should have P=5, S=5
    assert data["probability"] == 5
    assert data["severity"] == 5
    assert data["risk_score"] == 25
    assert data["risk_level"] == "critical"
