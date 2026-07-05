"""Application configuration.

All secrets come from environment variables (.env in dev, platform secrets in
prod). The app boots with zero AI keys: extraction fixtures seed the DB, and
AI endpoints degrade gracefully with a clear message if ANTHROPIC_API_KEY is
absent.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Senus Board Report"
    environment: str = "development"

    # sqlite default lets the repo run anywhere; docker-compose/prod set postgres
    database_url: str = "sqlite:///./senus.db"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"

    # Cost control: 0/false disables LLM commentary generation entirely.
    # Cached insights are still served from the DB; metrics are unaffected.
    ai_commentary: bool = True

    # OpenAI-compatible fallback (e.g. GitHub Models free tier)
    github_token: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str = "https://models.github.ai/inference"
    openai_model: str = "openai/gpt-4o"

    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60 * 12

    demo_user_email: str = "ceo@senus.com"
    demo_user_password: str = "senus2030"

    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
