#!/usr/bin/env python3
"""
통합 시드 스크립트 - 개발 환경용 테스트 데이터 생성

사용법:
    python -m scripts.seed_all           # 전체 시드 데이터 생성
    python -m scripts.seed_all --clear   # 기존 데이터 삭제 후 생성

⚠️ 개발 환경 전용 - 운영에서는 절대 실행하지 마세요!
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.seed_users import seed_users
from scripts.seed_incidents import seed_incidents, clear_incidents


async def seed_all(clear: bool = False, incident_count: int = 20):
    """Run all seed scripts."""

    # 운영 환경 체크 - production에서는 실행 차단
    from app.config import settings
    if settings.ENVIRONMENT == "production":
        print("❌ 운영 환경에서는 시드 데이터를 생성할 수 없습니다!")
        print("   ENVIRONMENT=production 감지됨")
        return

    print("=" * 50)
    print("🌱 개발용 시드 데이터 생성")
    print("=" * 50)
    print()

    if clear:
        print("[1/3] 기존 데이터 삭제...")
        await clear_incidents()
        print()

    print("[2/3] 사용자 데이터 생성...")
    await seed_users()
    print()

    print("[3/3] 사고 데이터 생성...")
    await seed_incidents(count=incident_count)
    print()

    print("=" * 50)
    print("✅ 모든 시드 데이터 생성 완료!")
    print("=" * 50)
    print()
    print("테스트 계정:")
    print("  - admin / admin1234 (시스템관리자)")
    print("  - qps / qps1234 (QI담당자)")
    print("  - reporter / reporter1234 (보고자)")
    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed all development data")
    parser.add_argument("--clear", action="store_true", help="Clear existing data first")
    parser.add_argument("--incidents", type=int, default=20, help="Number of incidents")

    args = parser.parse_args()

    asyncio.run(seed_all(clear=args.clear, incident_count=args.incidents))
