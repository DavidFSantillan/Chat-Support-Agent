""" config.py - Configuration management for the application
This module defines the application settings using Pydantic's BaseSettings.
It loads configuration from environment variables and provides a singleton instance of the settings."""

from pydantic import Field
from pydantic_settings import BaseSettings  # Changed import
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    # Use 'default' and environment variables map automatically by field name
    # Or use validation_alias for custom env var names
    app_name: str = Field(default="Chat Support Agent", validation_alias="APP_NAME")
    app_version: str = Field(default="1.0.0", validation_alias="APP_VERSION")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    cache_expiry_seconds: int = Field(default=3600, validation_alias="CACHE_EXPIRY_SECONDS")
    rag_model_name: str = Field(default="gpt-3.5-turbo", validation_alias="RAG_MODEL_NAME")
    rag_max_tokens: int = Field(default=150, validation_alias="RAG_MAX_TOKENS")
    rag_temperature: float = Field(default=0.7, validation_alias="RAG_TEMPERATURE")
    support_ticket_enabled: bool = Field(default=True, validation_alias="SUPPORT_TICKET_ENABLED")
    support_ticket_api_url: str = Field(default="", validation_alias="SUPPORT_TICKET_API_URL")
    support_ticket_api_key: str = Field(default="", validation_alias="SUPPORT_TICKET_API_KEY")
        # ── Redis (Cache) ───────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 3600  # 1 hora de caché
@lru_cache()
def get_settings() -> Settings:
    """Get the application settings, cached for performance"""
    return Settings()

