"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "RetailIQ API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "mysql+aiomysql://retailiq:retailiq@localhost:3306/retailiq"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ───────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-to-a-random-secret-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── API Keys ──────────────────────────────────────────────────────────────
    OPENWEATHER_API_KEY: Optional[str] = None
    HOLIDAY_API_KEY: Optional[str] = None
    # Claude API key for the AI Business Advisor (optional)
    ANTHROPIC_API_KEY: Optional[str] = None
    # Groq API key for the Autonomous Decision Intelligence Engine & Advisor
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-20b"

    # ── Celery ────────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]

    # ── File Uploads ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ── Model Paths ───────────────────────────────────────────────────────────
    MODEL_DIR: str = "models"
    DATA_DIR: str = "data"

    model_config = {"env_file": [".env", "../.env"], "env_file_encoding": "utf-8", "case_sensitive": True, "extra": "ignore"}


settings = Settings()


