"""Application settings loaded from the environment."""

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# The API is often started from backend/, while the local secret file lives at the repo root.
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Runtime configuration. Secrets come from the environment, never from code."""

    model_config = SettingsConfigDict(
        env_prefix="NEXUS_",
        env_file=_ENV_FILE,
        extra="ignore",
    )

    app_name: str = "NexusAI"
    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://nexus:nexus@postgres:5432/nexusai"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    chat_alias: str = "chat-default"
    chat_model: str = "openai/gpt-4o-mini"
    chat_api_base: str = ""
    llm_timeout_seconds: float = 60
    llm_max_retries: int = 2
    trace_database_url: str = "sqlite+aiosqlite:///./data/debug/llm_traces.db"
    openai_api_key: str = Field(
        default="",
        repr=False,
        validation_alias=AliasChoices("OPENAI_API_KEY", "NEXUS_OPENAI_API_KEY"),
    )
    openfga_api_url: str = "http://127.0.0.1:8090"
    openfga_store_name: str = "nexusai"
    litellm_master_key: str = Field(
        default="",
        repr=False,
        validation_alias=AliasChoices("LITELLM_MASTER_KEY", "NEXUS_LITELLM_MASTER_KEY"),
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def chat_provider(self) -> str:
        model = self.chat_model.strip()
        if "/" not in model:
            return "openai"
        return model.split("/", 1)[0]


@lru_cache
def get_settings() -> Settings:
    return Settings()
