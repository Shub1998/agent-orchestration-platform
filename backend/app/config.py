from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "AgentFlow"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/agentflow.db"
    CHECKPOINTER_DB_PATH: str = "./data/checkpointer.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DEFAULT_MODEL: str = "gpt-4o-mini"
    DEFAULT_PROVIDER: str = "openai"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3001", "http://localhost:3000", "http://localhost:5173"]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
