"""APIKey and User Pydantic schemas."""

from typing import List, Optional, Any
from pydantic import BaseModel, EmailStr, Field


class APIKeyCreate(BaseModel):
    name: str = Field(..., description="Service name (e.g. DecodeX SOC Agent)")
    scopes: List[str] = Field(default=["*"], description="Access scopes")
    expires_in_days: Optional[int] = Field(365, description="Expiry duration in days")


class APIKeyCreatedResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    raw_api_key: str = Field(..., description="Full API key — display ONCE to user")
    scopes: List[str]
    created_at: Any
    expires_at: Optional[Any]


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    created_at: Any
    last_used_at: Optional[Any]
    expires_at: Optional[Any]

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "analyst"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: Any

    class Config:
        from_attributes = True
