"""
Pressure Ulcer Records Seed Data
Simplified version using string enum values for PostgreSQL compatibility

Usage:
  cd backend
  python scripts/seed_pressure_ulcer_records.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker

# Import all models to ensure proper relationship loading
from app.models import *  # noqa: F401, F403

from app.models.pressure_ulcer import (
    PressureUlcerRecord,
    PressureUlcerAssessment,
)


def generate_ulcer_id(discovery_date: date, seq: int) -> str:
    """Generate ulcer ID in format PU-YYYYMMDD-NNN"""
    return f"PU-{discovery_date.strftime('%Y%m%d')}-{seq:03d}"


async def seed_pressure_ulcer_records(db: AsyncSession) -> None:
    """Create sample pressure ulcer records"""
    print("[*] Seeding pressure ulcer records...")

    today = date.today()
    records_created = 0
    assessments_created = 0

    # Scenario 1: Admission - Stage 2 Sacrum
    discovery_date1 = today - timedelta(days=30)
    record1 = PressureUlcerRecord(
        patient_code="PT2024001",
        patient_name="Patient A",
        patient_gender="F",
        room_number="101",
        patient_age_group="80s",
        admission_date=discovery_date1 - timedelta(days=1),
        ulcer_id=generate_ulcer_id(discovery_date1, 1),
        location="sacrum",
        origin="admission",
        discovery_date=discovery_date1,
        grade="stage_2",
        push_length_width=3,
        push_exudate=1,
        push_tissue_type=2,
        push_total=6.0,
        length_cm=2.5,
        width_cm=2.0,
        department="Ward 2",
        risk_factors="Diabetes, Malnutrition",
        treatment_plan="Foam dressing, Position change every 2 hours",
        note="Admission sacral pressure ulcer",
        is_active=True,
        is_healed=False,
        reported_at=datetime.utcnow(),
        reporter_name="Nurse Kim",
    )
    db.add(record1)
    await db.flush()
    records_created += 1

    # Add improving assessments
    for i in range(2):
        assessment_date = discovery_date1 + timedelta(days=(i + 1) * 7)
        if assessment_date > today:
            break
        assessment = PressureUlcerAssessment(
            ulcer_record_id=record1.id,
            assessment_date=assessment_date,
            grade="stage_2" if i == 0 else "stage_1",
            previous_grade="stage_2",
            push_length_width=max(1, 3 - i),
            push_exudate=1,
            push_tissue_type=max(1, 2 - i),
            push_total=float(max(3, 6 - i * 1.5)),
            is_improved=True if i > 0 else False,
            is_worsened=False,
            note=f"Week {i + 1} assessment",
        )
        db.add(assessment)
        assessments_created += 1

    # Scenario 2: Acquired - Stage 3 Heel with FMEA
    discovery_date2 = today - timedelta(days=14)
    record2 = PressureUlcerRecord(
        patient_code="PT2024002",
        patient_name="Patient B",
        patient_gender="M",
        room_number="102",
        patient_age_group="70s",
        admission_date=discovery_date2 - timedelta(days=60),
        ulcer_id=generate_ulcer_id(discovery_date2, 1),
        location="heel",
        origin="acquired",
        discovery_date=discovery_date2,
        grade="stage_3",
        push_length_width=5,
        push_exudate=2,
        push_tissue_type=3,
        push_total=10.0,
        length_cm=3.5,
        width_cm=3.0,
        depth_cm=0.5,
        department="Ward 3",
        risk_factors="Stroke, Decreased consciousness",
        treatment_plan="Moist dressing, Heel protection pad",
        note="Acquired in hospital",
        fmea_severity=6,
        fmea_probability=5,
        fmea_detectability=5,
        fmea_rpn=150,
        is_active=True,
        is_healed=False,
        reported_at=datetime.utcnow(),
        reporter_name="Nurse Park",
    )
    db.add(record2)
    await db.flush()
    records_created += 1

    # Scenario 3: Healed case
    discovery_date3 = today - timedelta(days=60)
    record3 = PressureUlcerRecord(
        patient_code="PT2024003",
        patient_name="Patient C",
        patient_gender="F",
        room_number="103",
        patient_age_group="90s",
        admission_date=discovery_date3 - timedelta(days=10),
        ulcer_id=generate_ulcer_id(discovery_date3, 1),
        location="ischium",
        origin="admission",
        discovery_date=discovery_date3,
        grade="stage_1",
        push_length_width=2,
        push_exudate=0,
        push_tissue_type=1,
        push_total=3.0,
        length_cm=1.5,
        width_cm=1.5,
        department="Ward 2",
        risk_factors="Advanced age",
        treatment_plan="Film dressing",
        is_active=False,
        is_healed=True,
        healed_date=today - timedelta(days=30),
        end_date=today - timedelta(days=30),
        end_reason="healed",
        reported_at=datetime.utcnow() - timedelta(days=60),
        reporter_name="Nurse Lee",
    )
    db.add(record3)
    await db.flush()
    records_created += 1

    # Scenario 4: Worsening case
    discovery_date4 = today - timedelta(days=21)
    record4 = PressureUlcerRecord(
        patient_code="PT2024004",
        patient_name="Patient D",
        patient_gender="M",
        room_number="201",
        patient_age_group="60s",
        admission_date=discovery_date4 - timedelta(days=45),
        ulcer_id=generate_ulcer_id(discovery_date4, 2),
        location="trochanter",
        origin="acquired",
        discovery_date=discovery_date4,
        grade="stage_2",
        push_length_width=4,
        push_exudate=1,
        push_tissue_type=2,
        push_total=7.0,
        length_cm=2.0,
        width_cm=2.0,
        department="Ward 4",
        risk_factors="Diabetes, PVD",
        treatment_plan="Moist dressing, Nutrition support",
        note="Blood sugar control needed",
        fmea_severity=8,
        fmea_probability=7,
        fmea_detectability=5,
        fmea_rpn=280,
        is_active=True,
        is_healed=False,
        reported_at=datetime.utcnow() - timedelta(days=21),
        reporter_name="Nurse Choi",
    )
    db.add(record4)
    await db.flush()
    records_created += 1

    # Worsening assessment
    assessment4 = PressureUlcerAssessment(
        ulcer_record_id=record4.id,
        assessment_date=discovery_date4 + timedelta(days=7),
        grade="stage_3",
        previous_grade="stage_2",
        push_length_width=5,
        push_exudate=2,
        push_tissue_type=3,
        push_total=10.0,
        is_improved=False,
        is_worsened=True,
        note="Grade worsened",
    )
    db.add(assessment4)
    assessments_created += 1

    # Scenario 5: DTPI
    discovery_date5 = today - timedelta(days=7)
    record5 = PressureUlcerRecord(
        patient_code="PT2024005",
        patient_name="Patient E",
        patient_gender="F",
        room_number="202",
        patient_age_group="80s",
        admission_date=discovery_date5 - timedelta(days=30),
        ulcer_id=generate_ulcer_id(discovery_date5, 1),
        location="sacrum",
        origin="acquired",
        discovery_date=discovery_date5,
        grade="dtpi",
        push_length_width=4,
        push_exudate=1,
        push_tissue_type=3,
        push_total=8.0,
        length_cm=4.0,
        width_cm=3.5,
        department="Ward 5",
        risk_factors="Heart failure, Hypoalbuminemia",
        treatment_plan="Moist dressing, Nutrition, Pressure relief",
        note="DTPI discovered, intensive monitoring",
        fmea_severity=10,
        fmea_probability=5,
        fmea_detectability=7,
        fmea_rpn=350,
        is_active=True,
        is_healed=False,
        reported_at=datetime.utcnow() - timedelta(days=7),
        reporter_name="Nurse Jung",
    )
    db.add(record5)
    await db.flush()
    records_created += 1

    # Scenario 6: Death closure
    discovery_date6 = today - timedelta(days=45)
    record6 = PressureUlcerRecord(
        patient_code="PT2024006",
        patient_name="Patient F",
        patient_gender="M",
        room_number="203",
        patient_age_group="85s",
        admission_date=discovery_date6 - timedelta(days=90),
        ulcer_id=generate_ulcer_id(discovery_date6, 1),
        location="occiput",
        origin="acquired",
        discovery_date=discovery_date6,
        grade="stage_4",
        push_length_width=7,
        push_exudate=3,
        push_tissue_type=4,
        push_total=14.0,
        length_cm=5.0,
        width_cm=4.0,
        depth_cm=1.0,
        department="Ward 3",
        risk_factors="Terminal cancer, Cachexia",
        treatment_plan="Palliative care",
        note="Palliative care",
        fmea_severity=10,
        fmea_probability=9,
        fmea_detectability=3,
        fmea_rpn=270,
        is_active=False,
        is_healed=False,
        end_date=today - timedelta(days=10),
        end_reason="death",
        reported_at=datetime.utcnow() - timedelta(days=45),
        reporter_name="Nurse Kang",
    )
    db.add(record6)
    await db.flush()
    records_created += 1

    # Scenario 7: Transfer closure
    discovery_date7 = today - timedelta(days=35)
    record7 = PressureUlcerRecord(
        patient_code="PT2024007",
        patient_name="Patient G",
        patient_gender="F",
        room_number="301",
        patient_age_group="75s",
        admission_date=discovery_date7 - timedelta(days=20),
        ulcer_id=generate_ulcer_id(discovery_date7, 2),
        location="heel",
        origin="admission",
        discovery_date=discovery_date7,
        grade="unstageable",
        push_length_width=6,
        push_exudate=2,
        push_tissue_type=4,
        push_total=12.0,
        length_cm=3.0,
        width_cm=2.5,
        department="Ward 4",
        risk_factors="Diabetic foot disease",
        treatment_plan="Transfer for specialized care",
        note="Transferred to tertiary hospital",
        is_active=False,
        is_healed=False,
        end_date=today - timedelta(days=20),
        end_reason="transfer",
        end_reason_detail="University Hospital Plastic Surgery",
        reported_at=datetime.utcnow() - timedelta(days=35),
        reporter_name="Nurse Yoon",
    )
    db.add(record7)
    await db.flush()
    records_created += 1

    # Scenario 8: Recent case
    discovery_date8 = today - timedelta(days=3)
    record8 = PressureUlcerRecord(
        patient_code="PT2024008",
        patient_name="Patient H",
        patient_gender="M",
        room_number="302",
        patient_age_group="70s",
        admission_date=discovery_date8 - timedelta(days=14),
        ulcer_id=generate_ulcer_id(discovery_date8, 1),
        location="ear",
        origin="acquired",
        discovery_date=discovery_date8,
        grade="stage_1",
        push_length_width=1,
        push_exudate=0,
        push_tissue_type=1,
        push_total=2.0,
        length_cm=1.0,
        width_cm=0.8,
        department="Ward 2",
        risk_factors="Oxygen mask pressure",
        treatment_plan="Pressure relief pad, Mask adjustment",
        note="Pressure injury from oxygen mask",
        fmea_severity=5,
        fmea_probability=5,
        fmea_detectability=3,
        fmea_rpn=75,
        is_active=True,
        is_healed=False,
        reported_at=datetime.utcnow() - timedelta(days=3),
        reporter_name="Nurse Son",
    )
    db.add(record8)
    await db.flush()
    records_created += 1

    await db.commit()

    print(f"[OK] Created {records_created} pressure ulcer records")
    print(f"[OK] Created {assessments_created} assessments")
    print("")
    print("[SUMMARY]")
    print(f"  - Active: 5 records")
    print(f"  - Healed: 1 record")
    print(f"  - Death: 1 record")
    print(f"  - Transfer: 1 record")
    print(f"  - Admission origin: 3 records")
    print(f"  - Acquired origin: 5 records")


async def main():
    """Main entry point"""
    print("=" * 50)
    print("Pressure Ulcer Records Seed Script")
    print("=" * 50)
    print("")

    async with async_session_maker() as session:
        await seed_pressure_ulcer_records(session)

    print("")
    print("=" * 50)
    print("[OK] Seed data creation completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
