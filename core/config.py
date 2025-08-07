"""
Configuration module for OLX Database FastAPI service.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings class for OLX Database FastAPI service.

    Uses environment variables.
    """

    # Pydantic v2 model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database configuration (no prefix)
    DATABASE_URL: str

    # OLX specific settings (with OLX_ prefix)
    DEFAULT_SENDING_FREQUENCY_MINUTES: int = Field(
        1, description="Default frequency for tasks getting from DB (default: 60)"
    )
    DEFAULT_LAST_MINUTES_GETTING: int = Field(
        60, description="Default time window for new items (default: 30)"
    )

    @field_validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v


# Global settings instance
settings = Settings()
