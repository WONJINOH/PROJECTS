"""
Application Configuration

Environment-based settings with secure defaults.
Never hardcode secrets - use environment variables.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # === Application ===
    APP_NAME: str = "Patient Safety API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production

    # === Database ===
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/patient_safety"
    DB_ENCRYPTION_KEY: str = "change-this-in-production-32char"  # Must be 32 chars for AES

    # === Security ===
    SECRET_KEY: str = "change-this-in-production-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # === CORS ===
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # === File Storage ===
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # === Logging ===
    LOG_LEVEL: str = "INFO"

    # === Redis (Optional - for caching/sessions) ===
    REDIS_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()
