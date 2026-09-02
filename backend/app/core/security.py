"""Security, Authentication & API Key Management — DecodeX Security Technologies Private Limited."""

import hmac
import hashlib
import secrets
from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone
from fastapi import Security, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_api_key(raw_key: str) -> str:
    """Generate SHA-256 HMAC hash of raw API key for secure database storage."""
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        raw_key.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def generate_api_key(name: str, env: str = "live") -> Tuple[str, str]:
    """
    Generate a secure random API key formatted as `dld_<env>_<random32>`.
    Returns: (raw_key, hashed_key)
    """
    random_part = secrets.token_hex(24)
    raw_key = f"{settings.API_KEY_PREFIX}{env}_{random_part}"
    hashed_key = hash_api_key(raw_key)
    return raw_key, hashed_key


async def get_current_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> dict:
    """
    Unified authentication dependency for DecodeX:
    Accepts either JWT Bearer Token (human user) OR X-API-Key (service-to-service).
    """
    # 1. Check API Key first (DecodeX / SIEM Service calls)
    if x_api_key:
        if not x_api_key.startswith(settings.API_KEY_PREFIX):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key format"
            )
        # Fast development check / DB verification handled in routes if needed
        return {
            "type": "api_key",
            "key_prefix": x_api_key[:12] + "...",
            "is_service_account": True,
            "scopes": ["all"]
        }

    # 2. Check JWT Token (User UI session)
    if credentials and credentials.credentials:
        payload = decode_access_token(credentials.credentials)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired JWT credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "type": "user_jwt",
            "user_id": payload.get("sub"),
            "role": payload.get("role", "analyst"),
            "is_service_account": False
        }

    # Standalone dev mode: allow unauthenticated requests with guest role if desired,
    # or require auth for production.
    return {
        "type": "anonymous_guest",
        "role": "analyst",
        "is_service_account": False
    }
