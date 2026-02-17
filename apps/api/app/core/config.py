from functools import lru_cache
from typing import Literal, cast

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ModelProvider = Literal["gemini", "openai"]


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
    model_provider: str | None = Field(default=None, alias="MODEL_PROVIDER")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")

    @staticmethod
    def _has_value(value: str | None) -> bool:
        return bool((value or "").strip())

    def resolved_model_provider(self) -> ModelProvider | None:
        has_gemini = self._has_value(self.gemini_api_key)
        has_openai = self._has_value(self.openai_api_key)
        requested_provider = (self.model_provider or "").strip().lower()

        if has_gemini and has_openai:
            if requested_provider in {"gemini", "openai"}:
                return cast(ModelProvider, requested_provider)
            return "gemini"
        if has_gemini:
            return "gemini"
        if has_openai:
            return "openai"
        return None

    def resolved_model_name(self) -> str | None:
        provider = self.resolved_model_provider()
        if provider == "gemini":
            return self.gemini_model
        if provider == "openai":
            return self.openai_model
        return None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
