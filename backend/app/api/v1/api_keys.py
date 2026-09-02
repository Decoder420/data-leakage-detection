"""API Keys API — Service Account Authentication Management."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_auth, generate_api_key
from backend.app.models.api_key import APIKey
from backend.app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyCreatedResponse

router = APIRouter(prefix="/api-keys", tags=["Service Accounts & API Keys"])


@router.get("", response_model=List[APIKeyResponse], summary="List Active API Keys")
def list_api_keys(db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    return db.query(APIKey).filter(APIKey.is_active == True).order_by(APIKey.created_at.desc()).all()


@router.post("", response_model=APIKeyCreatedResponse, summary="Generate New API Key for DecodeX SOC")
def create_api_key(
    req: APIKeyCreate,
    db: Session = Depends(get_db),
    auth: dict = Depends(get_current_auth)
):
    raw_key, hashed_key = generate_api_key(req.name)
    key_id = f"key_{uuid.uuid4().hex[:12]}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=req.expires_in_days or 365)

    api_key_db = APIKey(
        id=key_id,
        name=req.name,
        key_prefix=raw_key[:12],
        hashed_key=hashed_key,
        scopes=req.scopes,
        is_active=True,
        expires_at=expires_at
    )
    db.add(api_key_db)
    db.commit()
    db.refresh(api_key_db)

    return APIKeyCreatedResponse(
        id=api_key_db.id,
        name=api_key_db.name,
        key_prefix=api_key_db.key_prefix,
        raw_api_key=raw_key,
        scopes=api_key_db.scopes,
        created_at=api_key_db.created_at,
        expires_at=api_key_db.expires_at
    )


@router.delete("/{key_id}", summary="Revoke API Key")
def revoke_api_key(key_id: str, db: Session = Depends(get_db), auth: dict = Depends(get_current_auth)):
    key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
    key.is_active = False
    db.commit()
    return {"status": "success", "message": f"API Key {key_id} revoked"}
