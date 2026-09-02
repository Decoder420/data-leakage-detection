"""IntegrationSettings model for external SOC (DecodeX Threat Hunting Platform) configuration."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text
from backend.app.core.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class IntegrationSetting(Base):
    __tablename__ = "integration_settings"

    id = Column(String(64), primary_key=True, index=True)
    target_name = Column(String(255), nullable=False, default="DecodeX Threat Hunting Platform")
    endpoint_url = Column(String(1024), nullable=True, default="http://localhost:8001/api/v1/alerts")
    api_key = Column(String(512), nullable=True)  # Bearer token / API key for external SOC
    is_enabled = Column(Boolean, default=True)
    alert_on_guilt = Column(Boolean, default=True)
    alert_on_canary = Column(Boolean, default=True)
    min_confidence_threshold = Column(String(32), default="0.75")
    
    # Custom payload schema transformer mapping
    # Allows re-mapping fields dynamically once DecodeX exact endpoint contract is confirmed
    field_mappings = Column(JSON, default=lambda: {
        "id": "event_id",
        "type": "event_type",
        "severity": "severity",
        "confidence": "confidence_score",
        "dataset": "source_dataset",
        "suspect": "implicated_agent",
        "evidence": "evidence",
        "created_at": "timestamp"
    })
    
    extra_headers = Column(JSON, default=lambda: {
        "User-Agent": "DecodeX-DLD-SOC-Dispatcher/2.1",
        "X-Source-System": "DecodeX-Data-Leakage-Detection"
    })
    
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_status = Column(String(64), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
