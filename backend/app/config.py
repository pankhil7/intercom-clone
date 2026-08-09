from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Intercom Clone"
    DEBUG: bool = False
    FRONTEND_URL: str = "http://localhost:5173"
    WIDGET_CDN_URL: str = "http://localhost:5174"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/intercom"

    # JWT
    SECRET_KEY: str = "change-me-in-production-32-bytes-min"
    WIDGET_SECRET_KEY: str = "widget-secret-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    WIDGET_SESSION_EXPIRE_HOURS: int = 24

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Groq AI
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-8b-8192"

    # Mailgun (outbound email)
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""
    MAILGUN_FROM_EMAIL: str = ""

    # Cloudmailin (inbound email)
    CLOUDMAILIN_SECRET: str = ""
    CLOUDMAILIN_ADDRESS: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
