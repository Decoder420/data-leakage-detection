"""Integration Settings API for DecodeX Threat Hunting SOC & SIEM."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.core.database import get_db
from backend.app.core.security import get_current_auth
from backend.app.models.integration_setting import IntegrationSetting
from backend.app.schemas.event import SecurityEvent
from backend.app.services.alert_adapter import dispatch_event_to_decodex_soc

router = APIRouter(prefix="/integrations", tags=["DecodeX SOC Integration"])


class IntegrationSettingUpdate(BaseModel):
    target_name: str = "DecodeX Threat Hunting Platform"
    endpoint_url: str = Field(..., description="Target alert endpoint (e.g. http://localhost:8001/api/v1/alerts)")
    api_key: Optional[str] = Field(None, description="Bearer token / API key")
    is_enabled: bool = True
    alert_on_guilt: bool = True
    alert_on_canary: bool = True
    min_confidence_threshold: str = "0.75"
    field_mappings: Optional[Dict[str, str]] = None
    extra_headers: Optional[Dict[str, str]] = None


@router.get("", summary="Get DecodeX Integration Settings")
def get_integration_settings(db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    setting = db.query(IntegrationSetting).first()
    if not setting:
        setting = IntegrationSetting(
            id="cfg_decodex_default",
            target_name="DecodeX Threat Hunting Platform",
            endpoint_url="http://localhost:8001/api/v1/alerts",
            is_enabled=True
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.put("", summary="Update DecodeX Integration Settings")
def update_integration_settings(
    req: IntegrationSettingUpdate,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    setting = db.query(IntegrationSetting).first()
    if not setting:
        setting = IntegrationSetting(id="cfg_decodex_default")
        db.add(setting)

    setting.target_name = req.target_name
    setting.endpoint_url = req.endpoint_url
    if req.api_key is not None:
        setting.api_key = req.api_key
    setting.is_enabled = req.is_enabled
    setting.alert_on_guilt = req.alert_on_guilt
    setting.alert_on_canary = req.alert_on_canary
    setting.min_confidence_threshold = req.min_confidence_threshold
    if req.field_mappings:
        setting.field_mappings = req.field_mappings
    if req.extra_headers:
        setting.extra_headers = req.extra_headers

    db.commit()
    db.refresh(setting)
    return setting


@router.post("/test", summary="Test Connection to DecodeX SOC")
def test_connection_to_decodex_soc(db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    """
    Dispatches a synthetic test alert through the alert adapter to verify connectivity.
    """
    test_event = SecurityEvent(
        event_id="evt_test_ping_01",
        event_type="guilt_detection",
        severity="low",
        confidence_score=1.0,
        source_dataset="Integration Health Check",
        implicated_agent="Test Probe",
        evidence={"ping": True, "note": "Validating DecodeX Threat Hunting SOC adapter connection"},
        timestamp=datetime.now(timezone.utc).isoformat()
    )

    success, status_code, details = dispatch_event_to_decodex_soc(test_event, db=db, max_retries=1)
    
    return {
        "success": success,
        "status_code": status_code,
        "details": details,
        "message": "Connected successfully to DecodeX SOC" if success else "Endpoint unreachable or returned error"
    }
