"""APIKey and User SQLAlchemy models for Service-to-Service and Analyst Authentication."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    key_prefix = Column(String(32), nullable=False, index=True)
    hashed_key = Column(String(128), unique=True, nullable=False, index=True)
    scopes = Column(JSON, default=lambda: ["*"])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(64), default="analyst")  # admin, analyst, auditor
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
