"""Application Configuration Settings — DecodeX Security Technologies Private Limited."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "DecodeX Data Leakage Detection & Cyber Attribution Platform"
    PROJECT_SLUG: str = "decodex-dld-soc"
    VERSION: str = "2.1.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Ownership & Branding
    OWNING_ORGANIZATION: str = "DecodeX Security Technologies Private Limited"
    COPYRIGHT: str = "Copyright (c) 2026 DecodeX Security Technologies Private Limited. All rights reserved."

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./dld_platform.db",
        description="PostgreSQL or SQLite connection string"
    )

    # Redis & Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0")

    # Security & Auth
    SECRET_KEY: str = Field(default="DECODEX-SUPER-SECRET-JWT-KEY-2026-CYBER-SOC-99X")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    API_KEY_PREFIX: str = "dld_"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Storage Paths
    DATA_STORAGE_DIR: str = "./data/storage"
    REPORTS_STORAGE_DIR: str = "./data/reports"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
