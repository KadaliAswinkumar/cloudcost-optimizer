"""
Application Configuration
Loads settings from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_aws_regions() -> List[str]:
    return [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "eu-north-1",
        "ap-south-1", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
        "ap-northeast-2", "ap-northeast-3",
        "sa-east-1", "ca-central-1",
    ]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="CloudCost Optimizer")
    app_env: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )
    debug: bool = Field(default=True)
    secret_key: str = Field(default="dev-secret-key-CHANGE-IN-PRODUCTION")

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/cloudcost",
    )
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)

    @field_validator("database_url")
    @classmethod
    def convert_database_url(cls, v: str) -> str:
        """Convert postgresql:// to postgresql+asyncpg:// for async support."""
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_cache_ttl: int = Field(default=3600)

    aws_access_key_id: Optional[str] = Field(default=None)
    aws_secret_access_key: Optional[str] = Field(default=None)
    aws_default_region: str = Field(
        default="us-east-1",
        validation_alias=AliasChoices("AWS_DEFAULT_REGION", "AWS_REGION"),
    )

    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=60)

    # Comma-separated string — NOT List[str]. pydantic-settings tries json.loads() on
    # List fields from .env before validators run, which breaks "http://a,http://b".
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
    )

    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    aws_regions: List[str] = Field(default_factory=_default_aws_regions)

    @property
    def cors_origins_list(self) -> List[str]:
        """Origins for CORSMiddleware (parsed from comma-separated CORS_ORIGINS)."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
