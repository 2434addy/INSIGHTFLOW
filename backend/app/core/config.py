"""
Application configuration using Pydantic Settings.

All settings are loaded from environment variables with sensible defaults
for local development. Production values come from AWS Secrets Manager
via environment injection at container startup.
"""

from functools import lru_cache

from pydantic import Field, PostgresDsn, RedisDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the InsightFlow backend.

    Environment variables override defaults. Use .env file for local dev.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────
    APP_NAME: str = "InsightFlow"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    API_V1_PREFIX: str = "/v1"
    ALLOWED_HOSTS: list[str] = ["*"]

    # ── Security ───────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-use-openssl-rand-hex-64",
        min_length=32,
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # ── Database ───────────────────────────────────────────
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://insightflow:insightflow@localhost:5432/insightflow"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # ── Redis ──────────────────────────────────────────────
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")
    REDIS_CACHE_TTL: int = 300  # 5 minutes default

    # ── Celery ─────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Rate Limiting ──────────────────────────────────────
    RATE_LIMIT_AUTH: str = "5/15minutes"
    RATE_LIMIT_API: str = "100/minute"
    RATE_LIMIT_REPORT_GENERATION: str = "10/hour"

    # ── External Services ──────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    # ── Logging ────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" for production, "console" for dev

    # ── Storage ───────────────────────────────────────────
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    S3_REPORTS_PREFIX: str = "reports/"

    # ── AI Configuration ──────────────────────────────────
    ANTHROPIC_MODEL_PREMIUM: str = "claude-opus-4-6"
    ANTHROPIC_MAX_TOKENS: int = 4096
    ANTHROPIC_TIMEOUT: int = 120  # seconds
    AI_FALLBACK_TO_TEMPLATES: bool = True

    # ── Pipeline ──────────────────────────────────────────
    PIPELINE_TIMEOUT: int = 300  # 5 minutes max per report
    PIPELINE_MAX_RECORDS: int = 50000  # safety limit on input records

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance. Call this instead of constructing directly."""
    return Settings()
