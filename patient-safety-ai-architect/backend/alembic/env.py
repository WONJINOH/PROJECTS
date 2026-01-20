"""
Alembic Environment Configuration

Async SQLAlchemy support for PostgreSQL migrations.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import application settings and models
from app.config import settings
from app.database import Base

# Import all models to ensure they're registered with Base.metadata
from app.models import (
    User,
    Incident,
    Attachment,
    Approval,
    Action,
    AuditLog,
    IndicatorConfig,
    IndicatorValue,
    PSRDetail,
    HeatmapData,
    PressureUlcerRecord,
    PressureUlcerAssessment,
    PressureUlcerMonthlyStats,
    FallDetail,
    FallMonthlyStats,
    MedicationErrorDetail,
    MedicationMonthlyStats,
    RestraintRecord,
    RestraintAdverseEventRecord,
    RestraintMonthlyStats,
    InfectionRecord,
    HandHygieneObservation,
    InfectionMonthlyStats,
    StaffExposureRecord,
    LabTATRecord,
    StaffSafetyMonthlyStats,
    LabTATMonthlyStats,
)

# Alembic Config object
config = context.config

# Setup logging from config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def get_url() -> str:
    """Get database URL from application settings."""
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine.

    Creates an Engine and associates a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
