#!/usr/bin/env python3
"""
Seed script for creating fall incident test data.
Run with: python -m scripts.seed_fall_details

Creates realistic fall incident scenarios with pseudonymized patient data
for testing and demonstration purposes.
"""

import asyncio
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings


# Pseudonymized patient names (Korean pseudonyms)
PATIENT_NAMES = ["김OO", "이OO", "박OO", "최OO", "정OO", "강OO", "조OO", "윤OO", "장OO", "임OO"]

# Fall scenarios for realistic test data
FALL_SCENARIOS = [
    {
        "description": "침대에서 내려오다가 균형을 잃고 넘어짐. 환자는 야간에 화장실을 가기 위해 혼자 침대에서 내려오다가 발생.",
        "immediate_action": "즉시 의료진 호출. 바이탈 체크 및 외상 확인. 환자 안정 후 침대로 안전하게 이동.",
        "fall_location": "bed",
        "fall_cause": "loss_of_balance",
        "injury_level": "minor",
        "consciousness_level": "alert",
        "activity_level": "needs_assistance",
        "morse_score": 55,
        "risk_factors": ["history_of_fall", "urinary_frequency"],
    },
    {
        "description": "화장실에서 미끄러져 넘어짐. 물에 젖은 바닥에서 발을 헛디뎌 넘어짐.",
        "immediate_action": "의료진 호출 후 환자 상태 확인. 활력징후 측정 및 의식상태 확인. 외상 부위 냉찜질.",
        "fall_location": "bathroom",
        "fall_cause": "slip",
        "injury_level": "moderate",
        "consciousness_level": "alert",
        "activity_level": "needs_assistance",
        "morse_score": 65,
        "risk_factors": ["gait_disturbance", "dizziness"],
    },
    {
        "description": "복도에서 보행 중 어지러움을 느끼고 넘어짐. 보행 중 갑작스러운 어지러움으로 주저앉음.",
        "immediate_action": "즉시 환자 상태 확인 및 의료진 호출. 바닥에서 안전하게 눕힌 후 다리 거상. 혈압 측정.",
        "fall_location": "hallway",
        "fall_cause": "fainting",
        "injury_level": "none",
        "consciousness_level": "drowsy",
        "activity_level": "dependent",
        "morse_score": 75,
        "risk_factors": ["dizziness", "cognitive_impairment", "weakness"],
    },
    {
        "description": "휠체어에서 일어나려다 넘어짐. 혼자 휠체어에서 침대로 이동하려다 중심을 잃음.",
        "immediate_action": "의료진 호출 후 외상 여부 확인. 우측 손목 통증 호소하여 부목 고정 후 X-ray 촬영 의뢰.",
        "fall_location": "wheelchair",
        "fall_cause": "loss_of_balance",
        "injury_level": "moderate",
        "consciousness_level": "alert",
        "activity_level": "needs_assistance",
        "morse_score": 60,
        "risk_factors": ["weakness", "history_of_fall"],
    },
    {
        "description": "재활치료실에서 운동 중 넘어짐. 평행봉 보행 훈련 중 발을 헛디뎌 넘어짐.",
        "immediate_action": "치료사가 즉시 환자 지지 후 안전하게 매트로 이동. 외상 확인 후 냉찜질 시행.",
        "fall_location": "rehabilitation",
        "fall_cause": "trip",
        "injury_level": "minor",
        "consciousness_level": "alert",
        "activity_level": "needs_assistance",
        "morse_score": 45,
        "risk_factors": ["gait_disturbance"],
    },
    {
        "description": "야간에 침대 난간을 넘어 낙상. 환자가 야간에 혼란 상태로 침대 난간을 넘어 바닥으로 떨어짐.",
        "immediate_action": "즉시 의료진 호출. 의식상태 및 외상 확인. 두부 외상 의심되어 CT 촬영 의뢰.",
        "fall_location": "bed",
        "fall_cause": "cognitive",
        "injury_level": "major",
        "consciousness_level": "drowsy",
        "activity_level": "dependent",
        "morse_score": 85,
        "risk_factors": ["cognitive_impairment", "history_of_fall", "urinary_frequency"],
    },
    {
        "description": "투약 후 어지러움으로 화장실에서 넘어짐. 진정제 투여 1시간 후 화장실 이용 중 넘어짐.",
        "immediate_action": "의료진 호출 후 환자 상태 확인. 활력징후 안정. 약물 부작용 모니터링 강화.",
        "fall_location": "bathroom",
        "fall_cause": "medication",
        "injury_level": "minor",
        "consciousness_level": "drowsy",
        "activity_level": "needs_assistance",
        "morse_score": 70,
        "risk_factors": ["dizziness", "weakness"],
        "immediate_risk_medications": ["sedative"],
    },
    {
        "description": "의자에 앉다가 미끄러져 넘어짐. 병실 의자에 앉으려다 엉덩이가 미끄러져 바닥에 주저앉음.",
        "immediate_action": "환자 상태 확인 후 침대로 안전하게 이동. 활력징후 정상. 외상 없음 확인.",
        "fall_location": "chair",
        "fall_cause": "slip",
        "injury_level": "none",
        "consciousness_level": "alert",
        "activity_level": "independent",
        "morse_score": 35,
        "risk_factors": [],
    },
]

GRADE_OPTIONS = ["near_miss", "no_harm", "mild", "moderate", "severe"]
WARD_OPTIONS = ["ward_2", "ward_3", "ward_5", "ward_6", "ward_7", "ward_8", "ward_9", "ward_10", "ward_11"]
GENDER_OPTIONS = ["M", "F"]
SHIFT_OPTIONS = ["day", "evening", "night"]


def random_date_in_last_months(months: int = 3) -> datetime:
    """Generate a random datetime within the last N months."""
    now = datetime.now(timezone.utc)
    days_ago = random.randint(1, months * 30)
    hours_ago = random.randint(0, 23)
    return now - timedelta(days=days_ago, hours=hours_ago)


async def seed_fall_details():
    """Create seed fall incident and detail data."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # Check if reporter user exists
        result = await conn.execute(
            text("SELECT id FROM users WHERE username = 'reporter' LIMIT 1")
        )
        reporter = result.fetchone()

        if not reporter:
            print("Error: 'reporter' user not found. Please run seed_users.py first.")
            return

        reporter_id = reporter[0]

        # Create fall incidents with details
        for i, scenario in enumerate(FALL_SCENARIOS, start=1):
            patient_name = random.choice(PATIENT_NAMES)
            patient_age = random.randint(65, 95)
            patient_gender = random.choice(GENDER_OPTIONS)
            patient_ward = random.choice(WARD_OPTIONS)
            room_number = f"{random.randint(2, 11)}{random.randint(1, 20):02d}호"
            patient_code = f"P{datetime.now().year}{random.randint(10000, 99999)}"
            occurred_at = random_date_in_last_months(3)
            incident_number = f"{occurred_at.strftime('%Y%m%d')}-{i:02d}"
            grade = random.choice(GRADE_OPTIONS[:4])  # Exclude 'severe' for most
            if scenario["injury_level"] == "major":
                grade = "severe"
            shift = random.choice(SHIFT_OPTIONS)
            morse_score = scenario.get("morse_score", 50)

            # Insert incident
            await conn.execute(
                text("""
                    INSERT INTO incidents (
                        incident_number, category, grade, occurred_at, location, description,
                        immediate_action, reported_at, reporter_name, reporter_id, status,
                        patient_registration_no, patient_name, patient_ward, room_number,
                        patient_gender, patient_age, created_at, updated_at
                    )
                    VALUES (
                        :incident_number, CAST('fall' AS incidentcategory), CAST(:grade AS incidentgrade),
                        :occurred_at, :location, :description, :immediate_action, :reported_at,
                        :reporter_name, :reporter_id, 'submitted',
                        :patient_code, :patient_name, CAST(:patient_ward AS patientward), :room_number,
                        CAST(:patient_gender AS patientgender), :patient_age,
                        :created_at, :updated_at
                    )
                    RETURNING id
                """),
                {
                    "incident_number": incident_number,
                    "grade": grade,
                    "occurred_at": occurred_at,
                    "location": f"{patient_ward.replace('ward_', '')}병동 {room_number}",
                    "description": scenario["description"],
                    "immediate_action": scenario["immediate_action"],
                    "reported_at": occurred_at + timedelta(hours=random.randint(1, 4)),
                    "reporter_name": "담당간호사",
                    "reporter_id": reporter_id,
                    "patient_code": patient_code,
                    "patient_name": patient_name,
                    "patient_ward": patient_ward,
                    "room_number": room_number,
                    "patient_gender": patient_gender,
                    "patient_age": patient_age,
                    "created_at": occurred_at,
                    "updated_at": occurred_at,
                }
            )

            # Get the incident ID
            result = await conn.execute(
                text("SELECT id FROM incidents WHERE incident_number = :incident_number"),
                {"incident_number": incident_number}
            )
            incident_id = result.fetchone()[0]

            # Insert fall detail
            await conn.execute(
                text("""
                    INSERT INTO fall_details (
                        incident_id, patient_code, patient_name, patient_age_group, patient_gender,
                        room_number, pre_fall_risk_level, morse_score,
                        consciousness_level, activity_level, uses_mobility_aid, mobility_aid_type,
                        risk_factors, fall_type, fall_location, fall_cause, injury_level,
                        was_supervised, had_fall_prevention, department, shift,
                        is_recurrence, previous_fall_count, created_at
                    )
                    VALUES (
                        :incident_id, :patient_code, :patient_name, :age_group, :gender,
                        :room_number, CAST(:risk_level AS fallrisklevel), :morse_score,
                        CAST(:consciousness AS fallconsciousnesslevel),
                        CAST(:activity AS fallactivitylevel),
                        :uses_aid, CAST(:aid_type AS fallmobilityaid),
                        :risk_factors, CAST(:fall_type AS falltype),
                        CAST(:fall_location AS falllocation),
                        CAST(:fall_cause AS fallcause),
                        CAST(:injury_level AS fallinjurylevel),
                        :was_supervised, :had_prevention, :department, :shift,
                        :is_recurrence, :previous_count, :created_at
                    )
                """),
                {
                    "incident_id": incident_id,
                    "patient_code": patient_code,
                    "patient_name": patient_name,
                    "age_group": f"{patient_age // 10 * 10}대",
                    "gender": patient_gender,
                    "room_number": room_number,
                    "risk_level": "high" if morse_score >= 45 else ("moderate" if morse_score >= 25 else "low"),
                    "morse_score": morse_score,
                    "consciousness": scenario["consciousness_level"],
                    "activity": scenario["activity_level"],
                    "uses_aid": random.choice([True, False]),
                    "aid_type": random.choice(["none", "wheelchair", "walker", "cane"]),
                    "risk_factors": scenario["risk_factors"],
                    "fall_type": scenario["fall_location"] + "_fall" if scenario["fall_location"] in ["bed", "standing", "sitting", "walking", "transfer"] else "other",
                    "fall_location": scenario["fall_location"],
                    "fall_cause": scenario["fall_cause"],
                    "injury_level": scenario["injury_level"],
                    "was_supervised": random.choice([True, False]),
                    "had_prevention": random.choice([True, False]),
                    "department": f"{patient_ward.replace('ward_', '')}병동",
                    "shift": shift,
                    "is_recurrence": random.choice([True, False, False, False]),  # 25% recurrence
                    "previous_count": random.randint(0, 2),
                    "created_at": occurred_at,
                }
            )

            print(f"Created fall incident #{i}: {patient_name} ({patient_age}세) - {scenario['fall_location']} - {scenario['injury_level']}")

    await engine.dispose()
    print(f"\n{len(FALL_SCENARIOS)} fall incidents with details created successfully!")
    print("\nScenarios included:")
    for i, scenario in enumerate(FALL_SCENARIOS, start=1):
        print(f"  {i}. {scenario['fall_location']} / {scenario['fall_cause']} / {scenario['injury_level']}")


if __name__ == "__main__":
    asyncio.run(seed_fall_details())
