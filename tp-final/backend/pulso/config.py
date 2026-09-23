from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration read from environment variables (or a local .env file)."""

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    secret_key: str = Field(min_length=32)
    database_url: str = 'postgresql+psycopg://pulso:pulso@localhost:5432/pulso'
    cookie_secure: bool = False
    session_days: int = 7
    max_body_bytes: int = 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
