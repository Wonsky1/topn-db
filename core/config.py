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
        60, alias="OLX_DEFAULT_SENDING_FREQUENCY_MINUTES"
    )
    DEFAULT_LAST_MINUTES_GETTING: int = Field(
        30, alias="OLX_DEFAULT_LAST_MINUTES_GETTING"
    )

    @field_validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v


# Global settings instance
settings = Settings()
