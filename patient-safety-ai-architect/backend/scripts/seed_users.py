#!/usr/bin/env python3
"""
Seed script for creating initial test users.
Run with: python -m scripts.seed_users
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.security.password import hash_password


# Test users to create (use lowercase role values for PostgreSQL ENUM)
SEED_USERS = [
    {
        "username": "admin",
        "email": "admin@hospital.local",
        "password": "admin1234",
        "full_name": "시스템관리자",
        "role": "admin",  # lowercase for PostgreSQL ENUM
        "department": "IT팀",
    },
    {
        "username": "qps",
        "email": "qps@hospital.local",
        "password": "qps1234",
        "full_name": "QI담당자",
        "role": "qps_staff",
        "department": "QI팀",
    },
    {
        "username": "reporter",
        "email": "reporter@hospital.local",
        "password": "reporter1234",
        "full_name": "보고자",
        "role": "reporter",
        "department": "간호부",
    },
    {
        "username": "vicechair",
        "email": "vicechair@hospital.local",
        "password": "vicechair1234",
        "full_name": "부원장",
        "role": "vice_chair",
        "department": "원무과",
    },
    {
        "username": "director",
        "email": "director@hospital.local",
        "password": "director1234",
        "full_name": "원장",
        "role": "director",
        "department": "경영진",
    },
]


async def seed_users():
    """Create seed users in the database using raw SQL."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        for user_data in SEED_USERS:
            # Check if user already exists
            result = await conn.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": user_data["username"]}
            )
            existing = result.fetchone()

            if existing:
                print(f"User '{user_data['username']}' already exists, skipping...")
                continue

            # Create new user using raw SQL
            hashed_pw = hash_password(user_data["password"])
            await conn.execute(
                text("""
                    INSERT INTO users (username, email, hashed_password, full_name, role, department, is_active)
                    VALUES (:username, :email, :hashed_password, :full_name, CAST(:role_val AS role), :department, true)
                """),
                {
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "hashed_password": hashed_pw,
                    "full_name": user_data["full_name"],
                    "role_val": user_data["role"],
                    "department": user_data["department"],
                }
            )
            print(f"Created user: {user_data['username']} ({user_data['role']})")

    await engine.dispose()
    print("\nSeed users created successfully!")
    print("\nTest accounts:")
    for user_data in SEED_USERS:
        print(f"  - {user_data['username']} / {user_data['password']} ({user_data['role']})")


if __name__ == "__main__":
    asyncio.run(seed_users())
