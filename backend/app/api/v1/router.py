"""Aggregate API Router for /api/v1 — DecodeX Security Technologies."""

from fastapi import APIRouter
from backend.app.api.v1 import datasets, agents, distribute, analyze, events, webhooks, api_keys, integrations, reports
from backend.app.core.config import settings

api_router = APIRouter(prefix=settings.API_V1_PREFIX)

api_router.include_router(datasets.router)
api_router.include_router(agents.router)
api_router.include_router(distribute.router)
api_router.include_router(analyze.router)
api_router.include_router(events.router)
api_router.include_router(webhooks.router)
api_router.include_router(api_keys.router)
api_router.include_router(integrations.router)
api_router.include_router(reports.router)


@api_router.get("/health", tags=["Health"])
def api_v1_health():
    return {
        "status": "healthy",
        "service": "DecodeX Data Leakage Detection & Cyber Attribution Platform",
        "version": settings.VERSION,
        "owning_organization": settings.OWNING_ORGANIZATION,
        "integration_target": "DecodeX Threat Hunting SOC (REST API)",
        "features": [
            "Vectorized Papadimitriou Guilt Engine (100k+ rows)",
            "Synthetic Canary / Honeytoken Ingestion",
            "Swappable DecodeX Alert Adapter with Retries",
            "Standard Security Event Feed (/api/v1/events)",
            "Service Account API Key Auth (X-API-Key)",
            "Audit-Ready PDF / HTML Forensic Reports"
        ]
    }
