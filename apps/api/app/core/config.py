from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")
    database_url: str = Field(default="sqlite+aiosqlite:///./aas.db", alias="DATABASE_URL")
    redis_url: str | None = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    web_base_url: str = Field(default="http://localhost:3000", alias="WEB_BASE_URL")
    initial_credits: int = Field(default=3, alias="INITIAL_CREDITS")
    max_participants: int = Field(default=4, alias="MAX_PARTICIPANTS")
    inline_debate_runner: bool = Field(default=False, alias="INLINE_DEBATE_RUNNER")
    spectator_sse_enabled: bool = Field(default=True, alias="SPECTATOR_SSE_ENABLED")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
