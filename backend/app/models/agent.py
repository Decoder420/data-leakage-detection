"""Agent & Third-Party Vendor SQLAlchemy model."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    risk_level = Column(String(50), default="Medium")  # Low, Medium, High, Critical
    trust_score = Column(Float, default=85.0)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    allocations = relationship("AgentAllocation", back_populates="agent")
