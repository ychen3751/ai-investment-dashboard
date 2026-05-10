import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Investment Dashboard"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://investor:changeme@localhost:5432/investment_dashboard"
    DATABASE_URL_SYNC: str = "postgresql://investor:changeme@localhost:5432/investment_dashboard"

    # Redis (optional in production — falls back gracefully if not set)
    REDIS_URL: str = ""

    # Auth
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Rate Limiting
    RATE_LIMIT_GLOBAL: str = "60/minute"
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_ANALYSIS: str = "10/minute"

    # External APIs
    OPENAI_API_KEY: str = ""
    POLYGON_API_KEY: str = ""

    # CORS — comma-separated origins, or "*" to allow all (not recommended for production)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",")]
        return origins if origins != ["*"] else ["*"]

    @property
    def is_production(self) -> bool:
        return not self.DEBUG

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
