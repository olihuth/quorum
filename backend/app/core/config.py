from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    app_name: str = "Quorum Legislative Transparency API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./quorum.db"
    admin_api_key: str = "quorum-admin-secret"
    jwt_secret_key: str = "quorum-dev-jwt-secret"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173"
    enable_scheduler: bool = True
    llm_provider: str = "gemini"
    llm_model: str = "gemini-4-hydrogen"
    llm_api_key: str = ""
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_llm_api_key(self) -> str:
        return (self.llm_api_key or self.gemini_api_key).strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
