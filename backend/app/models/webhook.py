"""Webhook and WebhookDelivery SQLAlchemy models."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False)
    secret = Column(String(255), nullable=True)
    event_types = Column(JSON, default=lambda: ["guilt_detection", "canary_triggered", "leak_analysis_complete"])
    is_active = Column(Boolean, default=True)
    failure_count = Column(Integer, default=0)
    last_dispatched_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String(64), primary_key=True, index=True)
    webhook_id = Column(String(64), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(64), index=True, nullable=True)
    payload = Column(JSON, nullable=False)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempts = Column(Integer, default=1)
    success = Column(Boolean, default=False)
    dispatched_at = Column(DateTime(timezone=True), default=get_utc_now)

    webhook = relationship("Webhook", back_populates="deliveries")
