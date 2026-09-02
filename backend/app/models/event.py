"""Standard Security Event SQLAlchemy Model — DecodeX Security Technologies."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, JSON
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class SecurityEventRecord(Base):
    __tablename__ = "security_events"

    event_id = Column(String(64), primary_key=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)  # guilt_detection, canary_triggered, leak_analysis_complete
    severity = Column(String(32), nullable=False, default="medium", index=True)  # low, medium, high, critical
    confidence_score = Column(Float, default=0.0)
    source_dataset = Column(String(255), nullable=False)
    implicated_agent = Column(String(255), nullable=True, index=True)
    evidence = Column(JSON, default=dict)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now, index=True)
