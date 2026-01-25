#!/usr/bin/env python3
"""
Seed script for creating test incident data via API.
Run with: python -m scripts.seed_incidents

⚠️ 개발 환경 전용 - 운영에서는 실행하지 마세요!
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
import httpx

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# === 가상 테스트 데이터 (모두 가짜) ===
# CLAUDE.md 규칙: 실제 PII 금지, 가명만 사용

FAKE_REPORTERS = [
    "김간호", "이의사", "박물리", "최재활", "정영양",
    "강간병", "조사회", "윤행정", "임원무", "한청소",
]

FAKE_LOCATIONS = [
    "301호", "302호", "303호", "401호", "402호",
    "물리치료실", "작업치료실", "간호스테이션",
    "화장실(3층)", "화장실(4층)", "복도(3층)", "식당",
]

FAKE_DEPARTMENTS = [
    "간호부", "재활의학과", "내과", "신경과", "원무과",
]

# 사고 유형별 설명 템플릿
INCIDENT_TEMPLATES = {
    "fall": [
        "환자가 침대에서 내려오다 미끄러짐",
        "보행 중 균형을 잃고 넘어짐",
        "화장실에서 일어나다 낙상",
        "휠체어 이동 중 낙상",
        "야간 화장실 이동 중 넘어짐",
    ],
    "medication": [
        "투약 시간 지연 (30분 초과)",
        "용량 확인 후 수정 투여",
        "환자 확인 절차 누락 발견",
        "약물 상호작용 사전 발견",
        "투약 경로 재확인 후 수정",
    ],
    "pressure_ulcer": [
        "천골부 발적 발견 (Stage 1)",
        "발뒤꿈치 욕창 악화",
        "둔부 피부 손상 발견",
        "체위변경 누락으로 발적",
        "영양 불량으로 욕창 위험 증가",
    ],
    "infection": [
        "요로감염 의심 증상 발견",
        "발열 및 감염 징후 관찰",
        "카테터 관련 감염 의심",
        "호흡기 감염 증상 발현",
        "피부 감염 발견",
    ],
    "other": [
        "환자 식별 오류 사전 발견",
        "의사소통 오류로 인한 지연",
        "장비 오작동 발견",
        "인수인계 누락 사항 발견",
        "환자 이탈 시도 발견",
    ],
}

IMMEDIATE_ACTIONS = [
    "담당 의사에게 즉시 보고",
    "활력징후 측정 및 환자 상태 확인",
    "해당 부위 관찰 및 처치",
    "보호자에게 상황 설명",
    "추가 손상 예방 조치 시행",
    "관련 부서 협조 요청",
]

GRADES = ["near_miss", "no_harm", "mild", "moderate", "severe"]
GRADE_WEIGHTS = [30, 25, 25, 15, 5]


async def login(client: httpx.AsyncClient) -> str:
    """Login and get access token."""
    response = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "admin1234"},
    )
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    return response.json()["access_token"]


async def seed_incidents(count: int = 20, base_url: str = "http://localhost:8000"):
    """Create fake incident data via API."""

    print(f"[INFO] Creating {count} fake incidents for development...")
    print("       (All data is fake - DO NOT use in production)\n")

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Login
        try:
            token = await login(client)
            headers = {"Authorization": f"Bearer {token}"}
            print("[OK] Login successful\n")
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            return

        categories = list(INCIDENT_TEMPLATES.keys())
        base_date = datetime.now() - timedelta(days=90)

        created_count = 0
        for i in range(count):
            category = random.choice(categories)
            grade = random.choices(GRADES, weights=GRADE_WEIGHTS)[0]

            days_ago = random.randint(0, 90)
            hours = random.randint(6, 22)
            occurred_at = base_date + timedelta(days=days_ago, hours=hours)

            data = {
                "category": category,
                "grade": grade,
                "occurred_at": occurred_at.isoformat(),
                "location": random.choice(FAKE_LOCATIONS),
                "description": random.choice(INCIDENT_TEMPLATES[category]),
                "immediate_action": random.choice(IMMEDIATE_ACTIONS),
                "reported_at": (occurred_at + timedelta(hours=random.randint(1, 4))).isoformat(),
                "reporter_name": random.choice(FAKE_REPORTERS),
                "department": random.choice(FAKE_DEPARTMENTS),
            }

            try:
                response = await client.post("/api/incidents/", json=data, headers=headers)
                if response.status_code in (200, 201):
                    created_count += 1
                    print(f"   [{created_count}/{count}] {category} - {grade}")
                else:
                    print(f"   Skip: {response.status_code} - {response.text[:100]}")
            except Exception as e:
                print(f"   Error: {e}")

        print(f"\n[DONE] Created {created_count} fake incidents successfully")


async def clear_incidents(base_url: str = "http://localhost:8000"):
    """Note: API doesn't support bulk delete. Use DB directly."""
    print("[WARN] Bulk delete via API is not supported.")
    print("       Delete directly in DB: DELETE FROM incidents;")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed incident data for development")
    parser.add_argument("--count", type=int, default=20, help="Number of incidents to create")
    parser.add_argument("--clear", action="store_true", help="Show clear instructions")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="API base URL")

    args = parser.parse_args()

    if args.clear:
        asyncio.run(clear_incidents(args.url))
    else:
        asyncio.run(seed_incidents(args.count, args.url))
