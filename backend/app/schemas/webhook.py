"""Webhook Pydantic schemas."""

from typing import List, Optional, Any
from pydantic import BaseModel, HttpUrl, Field


class WebhookCreate(BaseModel):
    name: str = Field(..., description="Descriptive name (e.g. DecodeX Threat Hunting SOC)")
    url: str = Field(..., description="Target HTTPS Webhook receiver URL")
    secret: Optional[str] = Field(None, description="HMAC secret for signature validation")
    event_types: List[str] = Field(
        default=["guilt_detection", "canary_triggered", "leak_analysis_complete"],
        description="Subscribed security event types"
    )


class WebhookResponse(BaseModel):
    id: str
    name: str
    url: str
    event_types: List[str]
    is_active: bool
    failure_count: int
    last_dispatched_at: Optional[Any]
    created_at: Any

    class Config:
        from_attributes = True


class WebhookDeliveryResponse(BaseModel):
    id: str
    webhook_id: str
    event_id: Optional[str]
    status_code: Optional[int]
    attempts: int
    success: bool
    dispatched_at: Any

    class Config:
        from_attributes = True
