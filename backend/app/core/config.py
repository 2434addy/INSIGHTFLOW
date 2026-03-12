"""
Application configuration using Pydantic Settings.

All settings are loaded from environment variables with sensible defaults
for local development. Production values come from AWS Secrets Manager
via environment injection at container startup.

Security: the app refuses to start in production if SECRET_KEY is the
default placeholder value.
"""

import secrets
from functools import lru_cache

from pydantic import Field, PostgresDsn, RedisDsn, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The known-insecure default that must never be used in production.
_INSECURE_DEFAULT_KEY = "CHANGE-ME-IN-PRODUCTION-use-openssl-rand-hex-64"


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
        default=_INSECURE_DEFAULT_KEY,
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

    # Cookie settings for refresh tokens
    COOKIE_SECURE: bool = True         # Require HTTPS (relaxed in dev)
    COOKIE_SAMESITE: str = "strict"    # Strict same-site enforcement
    COOKIE_HTTPONLY: bool = True        # Never accessible to JavaScript
    COOKIE_DOMAIN: str | None = None   # Set to your domain in production

    # Request body size limit (bytes) — 1 MB default
    MAX_REQUEST_BODY_BYTES: int = 1_048_576

    # ── Database ───────────────────────────────────────────
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://insightflow:insightflow@localhost:5432/insightflow"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False
    DB_SSL_REQUIRED: bool = False      # Enforce SSL in production

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

    # Account lockout
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30

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

    @model_validator(mode="after")
    def _validate_production_safety(self) -> "Settings":
        """
        Block startup if production is configured with insecure defaults.

        Checks:
        - SECRET_KEY must not be the placeholder value
        - SECRET_KEY must be at least 64 hex chars (256-bit)
        - DEBUG must be False
        - ALLOWED_HOSTS must not include wildcard
        - Cookie security must be enabled
        - DB SSL should be enabled
        """
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == _INSECURE_DEFAULT_KEY:
                raise ValueError(
                    "FATAL: SECRET_KEY is set to the insecure default. "
                    "Generate a real key: python -c \"import secrets; print(secrets.token_hex(64))\""
                )

            if len(self.SECRET_KEY) < 64:
                raise ValueError(
                    "FATAL: SECRET_KEY must be at least 64 characters (256-bit) in production."
                )

            if self.DEBUG:
                raise ValueError(
                    "FATAL: DEBUG must be False in production."
                )

            if "*" in self.ALLOWED_HOSTS:
                raise ValueError(
                    "FATAL: ALLOWED_HOSTS must not include '*' in production."
                )

            if not self.COOKIE_SECURE:
                raise ValueError(
                    "FATAL: COOKIE_SECURE must be True in production (HTTPS required)."
                )

            if not self.DB_SSL_REQUIRED:
                import warnings
                warnings.warn(
                    "DB_SSL_REQUIRED is False in production. "
                    "Database connections should use SSL/TLS.",
                    RuntimeWarning,
                    stacklevel=2,
                )

        # In development, relax cookie security for local testing
        if self.ENVIRONMENT == "development":
            object.__setattr__(self, "COOKIE_SECURE", False)

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance. Call this instead of constructing directly."""
    return Settings()
