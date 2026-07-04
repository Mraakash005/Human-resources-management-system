"""
HRMS Core Configuration
Production-grade settings management using pydantic-settings.
All secrets loaded from environment variables. Never hardcoded.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "HRMS Enterprise"
    APP_VERSION: str = "3.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = Field(..., min_length=32, description="Application secret key")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        ..., description="PostgreSQL async connection string (postgresql+asyncpg://)"
    )
    DB_POOL_SIZE: int = Field(default=20, ge=1, le=100)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=5)
    DB_POOL_RECYCLE: int = Field(default=1800, ge=60)
    DB_ECHO: bool = False

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string",
    )
    REDIS_MAX_CONNECTIONS: int = Field(default=20, ge=1)
    REDIS_DECODER_RESPONSES: bool = True
    REDIS_RETURN_DECODE_MESSAGES: bool = False

    # ── Clerk Authentication ─────────────────────────────────────
    CLERK_PUBLISHABLE_KEY: str = Field(..., description="Clerk publishable key (pk_...)")
    CLERK_SECRET_KEY: str = Field(..., min_length=20, description="Clerk secret key (sk_...)")
    CLERK_JWT_VERIFICATION_KEY: str = Field(
        ..., description="Clerk JWT public key (PEM format, for RS256 verification)"
    )
    CLERK_WEBHOOK_SECRET: str = Field(
        default="", description="Clerk webhook signing secret (whsec_...)"
    )
    CLERK_JWT_TTL_MINUTES: int = Field(default=15, ge=1, le=60)

    # ── Email (Resend) ───────────────────────────────────────────
    RESEND_API_KEY: str = Field(..., description="Resend API key (re_...)")
    EMAIL_FROM: str = Field(
        default="hrms@localhost.com",
        description="Sender email address (must be verified in Resend)",
    )
    HR_EMAIL: str = Field(..., description="HR department email for notifications")

    # ── AI: Ollama ───────────────────────────────────────────────
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL",
    )
    OLLAMA_DEFAULT_MODEL: str = Field(default="llama3", description="Default Ollama model")
    OLLAMA_CHATBOT_MODEL: str = Field(default="mistral", description="Chatbot model (faster)")
    OLLAMA_TIMEOUT: int = Field(default=60, ge=10, description="Ollama request timeout (seconds)")
    OLLAMA_MAX_RETRIES: int = Field(default=2, ge=0, le=5)

    # ── AI: Whisper ──────────────────────────────────────────────
    WHISPER_URL: str = Field(
        default="http://localhost:9000",
        description="Whisper ASR webservice URL",
    )
    WHISPER_MODEL: str = Field(default="base", description="Whisper model size")
    WHISPER_TIMEOUT: int = Field(default=60, ge=10)

    # ── File Upload / ClamAV ─────────────────────────────────────
    CLAMAV_URL: str = Field(
        default="http://localhost:3310",
        description="ClamAV daemon URL",
    )
    MAX_DOCUMENT_SIZE_MB: int = Field(default=5, ge=1, le=50)
    MAX_AUDIO_SIZE_MB: int = Field(default=10, ge=1, le=100)
    ALLOWED_DOCUMENT_MIMES: set[str] = Field(
        default={"application/pdf", "image/jpeg", "image/png"}
    )
    ALLOWED_AUDIO_MIMES: set[str] = Field(
        default={"audio/wav", "audio/mpeg", "audio/webm"}
    )
    STORAGE_PATH: Path = Field(default=Path("./storage"), description="Local storage path")

    # ── R2 Object Storage (Profile Pictures) ─────────────────────
    R2_ACCOUNT_ID: str = Field(default="", description="Cloudflare R2 account ID")
    R2_ACCESS_KEY_ID: str = Field(default="", description="R2 access key ID")
    R2_SECRET_ACCESS_KEY: str = Field(default="", description="R2 secret access key")
    R2_BUCKET_NAME: str = Field(default="hrms-assets", description="R2 bucket name")
    R2_PUBLIC_BASE_URL: str = Field(default="", description="R2 public base URL")

    # ── Geofence ─────────────────────────────────────────────────
    OFFICE_LAT: float = Field(default=12.9716, description="Office latitude")
    OFFICE_LNG: float = Field(default=77.5946, description="Office longitude")
    GEOFENCE_RADIUS_METERS: int = Field(default=150, ge=10, le=5000)

    # ── Company ──────────────────────────────────────────────────
    COMPANY_NAME: str = Field(default="HRMS Corp", description="Company name for templates")

    # ── Leave Defaults ───────────────────────────────────────────
    LEAVE_PAID_DEFAULT: int = Field(default=12, ge=0, le=50)
    LEAVE_SICK_DEFAULT: int = Field(default=10, ge=0, le=50)
    LEAVE_UNPAID_DEFAULT: int = Field(default=999, ge=0)
    LEAVE_BEREAVEMENT_DEFAULT: int = Field(default=5, ge=0, le=20)

    # ── Payroll ──────────────────────────────────────────────────
    PAYROLL_PF_RATE: float = Field(default=0.12, ge=0.0, le=0.5)
    PAYROLL_STANDARD_DEDUCTION: int = Field(default=50000, ge=0)

    # ── Burnout Thresholds (Defaults) ────────────────────────────
    BURNOUT_MAX_CONSECUTIVE_DAYS: int = Field(default=14, ge=5, le=30)
    BURNOUT_MAX_WEEKLY_OVERTIME_HRS: int = Field(default=10, ge=1, le=40)
    BURNOUT_EXTREME_HOURS_THRESHOLD: int = Field(default=5, ge=1, le=14)

    # ── Cache TTLs (seconds) ─────────────────────────────────────
    CACHE_DASHBOARD_TTL: int = Field(default=60, ge=10)
    CACHE_ROLE_VERIFICATION_TTL: int = Field(default=120, ge=30)
    CACHE_CHATBOT_CONTEXT_TTL: int = Field(default=300, ge=60)
    CACHE_LEAVE_ADVISOR_TTL: int = Field(default=3600, ge=300)
    CACHE_HEATMAP_TTL: int = Field(default=3600, ge=300)
    CACHE_TEAM_HEALTH_TTL: int = Field(default=21600, ge=3600)

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=1)
    RATE_LIMIT_AI_PER_MINUTE: int = Field(default=10, ge=1)

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use postgresql+asyncpg:// scheme for async SQLAlchemy"
            )
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENVIRONMENT == Environment.PRODUCTION:
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")
            if "localhost" in self.DATABASE_URL:
                raise ValueError("Cannot use localhost database in production")
            if "localhost" in self.REDIS_URL:
                raise ValueError("Cannot use localhost Redis in production")
            if not self.CORS_ORIGINS or all("localhost" in o for o in self.CORS_ORIGINS):
                raise ValueError("CORS_ORIGINS must include production domain in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == Environment.TESTING


@lru_cache
def get_settings() -> Settings:
    return Settings()
