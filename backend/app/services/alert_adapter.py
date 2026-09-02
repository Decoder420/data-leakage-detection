"""Swappable Alert Adapter for DecodeX Threat Hunting SOC & External SIEM.
Proprietary Work Product of DecodeX Security Technologies Private Limited.
"""

import time
import httpx
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.schemas.event import SecurityEvent
from backend.app.models.integration_setting import IntegrationSetting
from backend.app.core.config import settings

logger = logging.getLogger("decodex.alert_adapter")


def transform_event_to_soc_payload(
    event: SecurityEvent,
    custom_field_mappings: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Transforms the internal DLD SecurityEvent into the shape expected by DecodeX Threat Hunting SOC.
    
    TODO: Once DecodeX Threat Hunting Platform (github.com/Decoder420/DecodeX-Threat-Hunting-Platform)
    finalizes its exact /api/v1/alerts ingestion schema, update or configure the field mappings below.
    
    Current Default Payload Shape:
    {
        "alert_id": event.event_id,
        "alert_type": event.event_type,
        "source": "DecodeX-Data-Leakage-Detection",
        "severity": event.severity.upper(),
        "confidence": event.confidence_score,
        "target_resource": event.source_dataset,
        "attributed_entity": event.implicated_agent,
        "metadata": event.evidence,
        "timestamp": event.timestamp
    }
    """
    event_dict = event.model_dump()
    
    if custom_field_mappings:
        transformed = {}
        for target_key, source_key in custom_field_mappings.items():
            if source_key in event_dict:
                transformed[target_key] = event_dict[source_key]
        return transformed

    # Default working contract for DecodeX Threat Hunting SOC
    return {
        "alert_id": event.event_id,
        "alert_type": event.event_type,
        "source": "DecodeX-Data-Leakage-Detection",
        "severity": event.severity.upper(),
        "confidence": event.confidence_score,
        "target_resource": event.source_dataset,
        "attributed_entity": event.implicated_agent,
        "metadata": event.evidence,
        "timestamp": event.timestamp
    }


def dispatch_event_to_decodex_soc(
    event: SecurityEvent,
    db: Optional[Session] = None,
    max_retries: int = 3,
    initial_backoff: float = 0.5
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Dispatches a security event alert to the configured DecodeX Threat Hunting SOC endpoint
    with exponential backoff retry.
    
    Returns:
        (success: bool, status_code: Optional[int], error_or_body: Optional[str])
    """
    endpoint_url = None
    api_key = None
    field_mappings = None
    extra_headers = {}

    # 1. Fetch config from DB if session provided
    if db:
        config = db.query(IntegrationSetting).first()
        if config and not config.is_enabled:
            logger.info("DecodeX SOC integration is disabled in settings. Skipping dispatch.")
            return True, None, "SKIPPED_DISABLED"
        if config:
            endpoint_url = config.endpoint_url
            api_key = config.api_key
            field_mappings = config.field_mappings
            extra_headers = config.extra_headers or {}

    # Fallback to environment variables / defaults
    endpoint_url = endpoint_url or "http://localhost:8001/api/v1/alerts"
    
    payload = transform_event_to_soc_payload(event, field_mappings)
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DecodeX-DLD-SOC-Adapter/2.1",
        **extra_headers
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-Key"] = api_key

    # Retry loop with exponential backoff
    backoff = initial_backoff
    last_error = None
    last_status = None

    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=4.0) as client:
                response = client.post(endpoint_url, json=payload, headers=headers)
                if response.status_code in [200, 201, 202]:
                    logger.info(f"Successfully delivered alert {event.event_id} to DecodeX SOC (Attempt {attempt})")
                    if db and config:
                        config.last_status = f"200 OK (Delivered {event.event_id})"
                        config.last_tested_at = datetime.now(timezone.utc)
                        db.commit()
                    return True, response.status_code, response.text[:256]
                else:
                    last_status = response.status_code
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning(f"DecodeX SOC returned error on attempt {attempt}: {last_error}")
        except Exception as exc:
            last_error = str(exc)
            logger.warning(f"Connection attempt {attempt} to DecodeX SOC failed: {last_error}")

        if attempt < max_retries:
            time.sleep(backoff)
            backoff *= 2.0

    logger.error(f"Failed to deliver alert {event.event_id} to DecodeX SOC after {max_retries} attempts.")
    if db and config:
        config.last_status = f"FAILED: {last_error[:64]}"
        db.commit()

    return False, last_status, last_error
