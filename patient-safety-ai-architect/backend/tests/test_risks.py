"""
Risk Management API Tests

Tests for:
- Risk CRUD operations
- 5×5 Risk Matrix
- Risk Assessments
- Access control (RBAC)
"""

import pytest
from datetime import date
from httpx import AsyncClient

from app.models.risk import RiskStatus, RiskLevel


# === Risk CRUD Tests ===

@pytest.mark.asyncio
async def test_create_risk_as_qps(client_as_qps: AsyncClient, qps_user):
    """QPS staff can create a risk."""
    response = await client_as_qps.post(
        "/api/risks/",
        json={
            "title": "투약 오류 위험",
            "description": "고위험 약물 투여 시 더블체크 누락 사례 반복 발생",
            "source_type": "audit",
            "category": "medication",
            "probability": 4,
            "severity": 4,
            "owner_id": qps_user.id,
            "current_controls": "투약 지침 교육",
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "투약 오류 위험"
    assert data["risk_code"].startswith("R-")
    assert data["probability"] == 4
    assert data["severity"] == 4
    assert data["risk_score"] == 16  # 4 × 4
    assert data["risk_level"] == "high"  # P×S 10-16 = HIGH, >16 = CRITICAL


@pytest.mark.asyncio
async def test_create_risk_as_reporter_forbidden(client_as_reporter: AsyncClient, reporter_user):
    """Reporter cannot create risks."""
    response = await client_as_reporter.post(
        "/api/risks/",
        json={
            "title": "Test Risk",
            "description": "This should fail",
            "source_type": "other",
            "category": "other",
            "probability": 1,
            "severity": 1,
            "owner_id": reporter_user.id,
        }
    )

    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_risks(client_as_qps: AsyncClient, sample_risk):
    """QPS staff can list risks."""
    response = await client_as_qps.get("/api/risks/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["risk_code"] == "R-2026-001"


@pytest.mark.asyncio
async def test_list_risks_with_filters(client_as_qps: AsyncClient, sample_risk):
    """List risks with status and level filters."""
    # Filter by status
    response = await client_as_qps.get("/api/risks/?status_filter=identified")
    assert response.status_code == 200
    data = response.json()
    assert all(r["status"] == "identified" for r in data["items"])

    # Filter by level
    response = await client_as_qps.get("/api/risks/?level_filter=high")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_risk_by_id(client_as_qps: AsyncClient, sample_risk):
    """Get risk details by ID."""
    response = await client_as_qps.get(f"/api/risks/{sample_risk.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_risk.id
    assert data["title"] == sample_risk.title
    assert data["probability"] == 3
    assert data["severity"] == 4


@pytest.mark.asyncio
async def test_get_nonexistent_risk(client_as_qps: AsyncClient):
    """Get nonexistent risk returns 404."""
    response = await client_as_qps.get("/api/risks/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_risk(client_as_qps: AsyncClient, sample_risk):
    """QPS staff can update a risk."""
    response = await client_as_qps.put(
        f"/api/risks/{sample_risk.id}",
        json={
            "title": "낙상 위험 - 내과 병동 (업데이트)",
            "probability": 2,
            "severity": 3,
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "업데이트" in data["title"]
    assert data["probability"] == 2
    assert data["severity"] == 3
    assert data["risk_score"] == 6  # 2 × 3


@pytest.mark.asyncio
async def test_close_risk_requires_director(client_as_qps: AsyncClient, sample_risk):
    """Closing a risk requires DIRECTOR role."""
    response = await client_as_qps.put(
        f"/api/risks/{sample_risk.id}",
        json={"status": "closed"}
    )

    assert response.status_code == 403
    assert "DIRECTOR" in response.json()["detail"]


@pytest.mark.asyncio
async def test_close_risk_as_director(client_as_director: AsyncClient, sample_risk):
    """Director can close a risk."""
    response = await client_as_director.put(
        f"/api/risks/{sample_risk.id}",
        json={"status": "closed"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "closed"
    assert data["closed_at"] is not None


# === Risk Matrix Tests ===

@pytest.mark.asyncio
async def test_get_risk_matrix(client_as_qps: AsyncClient, sample_risk):
    """Get 5×5 risk matrix."""
    response = await client_as_qps.get("/api/risks/matrix")

    assert response.status_code == 200
    data = response.json()

    # Matrix should be 5×5
    assert len(data["matrix"]) == 5
    assert all(len(row) == 5 for row in data["matrix"])

    # Total risks should be counted
    assert data["total_risks"] >= 1

    # by_level should have all levels
    assert "low" in data["by_level"]
    assert "medium" in data["by_level"]
    assert "high" in data["by_level"]
    assert "critical" in data["by_level"]


@pytest.mark.asyncio
async def test_risk_matrix_cell_structure(client_as_qps: AsyncClient, sample_risk):
    """Verify risk matrix cell structure."""
    response = await client_as_qps.get("/api/risks/matrix")
    data = response.json()

    # Check a specific cell (P=3, S=4 where sample_risk is)
    cell = data["matrix"][2][3]  # 0-indexed: P=3 → index 2, S=4 → index 3
    assert cell["probability"] == 3
    assert cell["severity"] == 4
    assert cell["count"] >= 1
    assert sample_risk.id in cell["risk_ids"]
    assert cell["level"] == "high"  # P×S = 12 → high


# === Risk Assessment Tests ===

@pytest.mark.asyncio
async def test_create_risk_assessment(client_as_qps: AsyncClient, sample_risk):
    """Create a risk re-assessment."""
    response = await client_as_qps.post(
        f"/api/risks/{sample_risk.id}/assessments",
        json={
            "risk_id": sample_risk.id,
            "assessment_type": "periodic",
            "probability": 2,
            "severity": 3,
            "rationale": "개선 활동 후 위험도 감소",
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["probability"] == 2
    assert data["severity"] == 3
    assert data["score"] == 6
    assert data["level"] == "medium"
    assert data["assessment_type"] == "periodic"


@pytest.mark.asyncio
async def test_create_post_treatment_assessment(client_as_qps: AsyncClient, sample_risk):
    """Post-treatment assessment updates residual risk."""
    response = await client_as_qps.post(
        f"/api/risks/{sample_risk.id}/assessments",
        json={
            "risk_id": sample_risk.id,
            "assessment_type": "post_treatment",
            "probability": 1,
            "severity": 2,
            "rationale": "조치 완료 후 잔여 위험 평가",
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["assessment_type"] == "post_treatment"


@pytest.mark.asyncio
async def test_list_risk_assessments(client_as_qps: AsyncClient, sample_risk):
    """List assessment history for a risk."""
    # Create an assessment first
    await client_as_qps.post(
        f"/api/risks/{sample_risk.id}/assessments",
        json={
            "risk_id": sample_risk.id,
            "assessment_type": "periodic",
            "probability": 2,
            "severity": 2,
            "rationale": "정기 재평가",
        }
    )

    response = await client_as_qps.get(f"/api/risks/{sample_risk.id}/assessments")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Should be ordered by assessed_at desc
    assert data[0]["rationale"] == "정기 재평가"


# === Risk Level Calculation Tests ===

@pytest.mark.asyncio
async def test_risk_level_low(client_as_qps: AsyncClient, qps_user):
    """Risk level LOW for score 1-4."""
    response = await client_as_qps.post(
        "/api/risks/",
        json={
            "title": "Low Risk Test",
            "description": "Testing low risk level calculation",
            "source_type": "other",
            "category": "other",
            "probability": 1,
            "severity": 2,
            "owner_id": qps_user.id,
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["risk_score"] == 2
    assert data["risk_level"] == "low"


@pytest.mark.asyncio
async def test_risk_level_medium(client_as_qps: AsyncClient, qps_user):
    """Risk level MEDIUM for score 5-9."""
    response = await client_as_qps.post(
        "/api/risks/",
        json={
            "title": "Medium Risk Test",
            "description": "Testing medium risk level calculation",
            "source_type": "other",
            "category": "other",
            "probability": 3,
            "severity": 3,
            "owner_id": qps_user.id,
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["risk_score"] == 9
    assert data["risk_level"] == "medium"


@pytest.mark.asyncio
async def test_risk_level_high(client_as_qps: AsyncClient, qps_user):
    """Risk level HIGH for score 10-14."""
    response = await client_as_qps.post(
        "/api/risks/",
        json={
            "title": "High Risk Test",
            "description": "Testing high risk level calculation",
            "source_type": "other",
            "category": "other",
            "probability": 2,
            "severity": 5,
            "owner_id": qps_user.id,
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["risk_score"] == 10
    assert data["risk_level"] == "high"


@pytest.mark.asyncio
async def test_risk_level_critical(client_as_qps: AsyncClient, qps_user):
    """Risk level CRITICAL for score 15-25."""
    response = await client_as_qps.post(
        "/api/risks/",
        json={
            "title": "Critical Risk Test",
            "description": "Testing critical risk level calculation",
            "source_type": "other",
            "category": "other",
            "probability": 5,
            "severity": 5,
            "owner_id": qps_user.id,
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["risk_score"] == 25
    assert data["risk_level"] == "critical"


# === Validation Tests ===

@pytest.mark.asyncio
async def test_probability_validation(client_as_qps: AsyncClient, qps_user):
    """Probability must be 1-5."""
    response = await client_as_qps.post(
        "/api/risks/",
        json={
            "title": "Invalid Probability",
            "description": "Testing probability validation",
            "source_type": "other",
            "category": "other",
            "probability": 6,  # Invalid
            "severity": 3,
            "owner_id": qps_user.id,
        }
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_severity_validation(client_as_qps: AsyncClient, qps_user):
    """Severity must be 1-5."""
    response = await client_as_qps.post(
        "/api/risks/",
        json={
            "title": "Invalid Severity",
            "description": "Testing severity validation",
            "source_type": "other",
            "category": "other",
            "probability": 3,
            "severity": 0,  # Invalid
            "owner_id": qps_user.id,
        }
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_psr_source_requires_incident_id(client_as_qps: AsyncClient, qps_user):
    """PSR source type requires source_incident_id."""
    response = await client_as_qps.post(
        "/api/risks/",
        json={
            "title": "PSR without incident",
            "description": "Testing PSR source validation",
            "source_type": "psr",  # Requires source_incident_id
            "category": "fall",
            "probability": 3,
            "severity": 3,
            "owner_id": qps_user.id,
        }
    )

    assert response.status_code == 422  # Validation error
