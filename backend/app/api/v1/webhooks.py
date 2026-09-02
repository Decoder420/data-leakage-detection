"""Webhooks API — Outbound SIEM & Webhook Subscription Management."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_auth
from backend.app.models.webhook import Webhook, WebhookDelivery
from backend.app.schemas.webhook import WebhookCreate, WebhookResponse, WebhookDeliveryResponse

router = APIRouter(prefix="/webhooks", tags=["Outbound Webhooks"])


@router.get("", response_model=List[WebhookResponse], summary="List Registered Webhooks")
def list_webhooks(db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    return db.query(Webhook).order_by(Webhook.created_at.desc()).all()


@router.post("", response_model=WebhookResponse, summary="Register Webhook Endpoint")
def register_webhook(
    req: WebhookCreate,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    wh_id = f"wh_{uuid.uuid4().hex[:12]}"
    webhook = Webhook(
        id=wh_id,
        name=req.name,
        url=req.url,
        secret=req.secret,
        event_types=req.event_types,
        is_active=True
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.delete("/{webhook_id}", summary="Delete Webhook")
def delete_webhook(webhook_id: str, db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    wh = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(wh)
    db.commit()
    return {"status": "success", "message": f"Webhook {webhook_id} deleted"}


@router.get("/{webhook_id}/deliveries", response_model=List[WebhookDeliveryResponse], summary="Get Webhook Delivery History")
def get_webhook_deliveries(webhook_id: str, db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    return db.query(WebhookDelivery).filter(WebhookDelivery.webhook_id == webhook_id).order_by(WebhookDelivery.dispatched_at.desc()).limit(50).all()
