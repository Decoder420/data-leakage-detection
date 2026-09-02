"""Security Events API — DecodeX Interoperability REST Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_auth
from backend.app.models.event import SecurityEventRecord
from backend.app.schemas.event import SecurityEvent
from backend.app.services.event_service import emit_security_event

router = APIRouter(prefix="/events", tags=["Security Events (DecodeX Feed)"])


@router.get("", response_model=List[SecurityEvent], summary="Pull Recent Security Events")
def get_security_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high, critical"),
    implicated_agent: Optional[str] = Query(None, description="Filter by suspect vendor"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    """
    Returns recent security events adhering to the standard DecodeX JSON schema.
    Supports pull-based SIEM polling.
    """
    query = db.query(SecurityEventRecord)
    if event_type:
        query = query.filter(SecurityEventRecord.event_type == event_type)
    if severity:
        query = query.filter(SecurityEventRecord.severity == severity.lower())
    if implicated_agent:
        query = query.filter(SecurityEventRecord.implicated_agent.ilike(f"%{implicated_agent}%"))

    records = query.order_by(SecurityEventRecord.timestamp.desc()).offset(offset).limit(limit).all()

    return [
        SecurityEvent(
            event_id=r.event_id,
            event_type=r.event_type,
            severity=r.severity,
            confidence_score=r.confidence_score,
            source_dataset=r.source_dataset,
            implicated_agent=r.implicated_agent,
            evidence=r.evidence or {},
            timestamp=r.timestamp.isoformat() if r.timestamp else ""
        )
        for r in records
    ]


@router.get("/{event_id}", response_model=SecurityEvent, summary="Get Single Security Event")
def get_security_event_by_id(
    event_id: str,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    record = db.query(SecurityEventRecord).filter(SecurityEventRecord.event_id == event_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Security event not found")
    
    return SecurityEvent(
        event_id=record.event_id,
        event_type=record.event_type,
        severity=record.severity,
        confidence_score=record.confidence_score,
        source_dataset=record.source_dataset,
        implicated_agent=record.implicated_agent,
        evidence=record.evidence or {},
        timestamp=record.timestamp.isoformat() if record.timestamp else ""
    )


@router.post("/test-dispatch", response_model=SecurityEvent, summary="Emit Test Alert to DecodeX SOC")
def emit_test_security_event(
    event_type: str = "guilt_detection",
    severity: str = "high",
    confidence_score: float = 0.985,
    source_dataset: str = "Global Wealth Client PII",
    implicated_agent: str = "Alpha Analytics Corp",
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    """
    Generates and broadcasts a test security event to verify the outbound alert adapter.
    """
    event = emit_security_event(
        event_type=event_type,
        severity=severity,
        confidence_score=confidence_score,
        source_dataset=source_dataset,
        implicated_agent=implicated_agent,
        evidence={
            "matched_records": 48,
            "total_leaked": 50,
            "canary_token_found": "CNR-ALPH-7F2A-89CB",
            "test_mode": True
        },
        db=db,
        dispatch_alert=True
    )
    return event
