"""Event Service for logging security events and dispatching alerts."""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.event import SecurityEventRecord
from backend.app.schemas.event import SecurityEvent
from backend.app.services.alert_adapter import dispatch_event_to_decodex_soc


def emit_security_event(
    event_type: str,
    severity: str,
    confidence_score: float,
    source_dataset: str,
    implicated_agent: Optional[str] = None,
    evidence: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
    dispatch_alert: bool = True
) -> SecurityEvent:
    """
    Creates, persists, and broadcasts a standardized SecurityEvent.
    """
    event_id = f"evt_{uuid.uuid4().hex[:16]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    evidence_dict = evidence or {}

    event = SecurityEvent(
        event_id=event_id,
        event_type=event_type,
        severity=severity,
        confidence_score=round(confidence_score, 4),
        source_dataset=source_dataset,
        implicated_agent=implicated_agent,
        evidence=evidence_dict,
        timestamp=now_iso
    )

    if db:
        record = SecurityEventRecord(
            event_id=event.event_id,
            event_type=event.event_type,
            severity=event.severity,
            confidence_score=event.confidence_score,
            source_dataset=event.source_dataset,
            implicated_agent=event.implicated_agent,
            evidence=event.evidence,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(record)
        db.commit()

        if dispatch_alert:
            # Dispatch to external DecodeX Threat Hunting SOC via adapter
            dispatch_event_to_decodex_soc(event, db=db, max_retries=1)

    return event
