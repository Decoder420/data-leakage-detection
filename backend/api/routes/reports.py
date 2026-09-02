"""Forensic Audit Report and SIEM Webhook routes."""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Dict, Any

from backend.engine.reports import generate_forensic_html_report
from backend.api.state import state

router = APIRouter(prefix="/api/reports", tags=["Reports & SIEM"])


class SIEMAlertTest(BaseModel):
    analysis_id: str
    siem_type: str = "Splunk"  # Splunk, Elastic, Datadog, Slack, Microsoft Teams


@router.get("/{analysis_id}/html")
def get_html_report(analysis_id: str):
    """Render a full HTML forensic incident report for printing or PDF export."""
    target_result = None
    for res in state.analysis_history:
        if res.analysis_id == analysis_id:
            target_result = res
            break

    if not target_result:
        raise HTTPException(status_code=404, detail="Analysis result not found")

    dataset_name = state.datasets.get(target_result.dataset_id, {}).name if target_result.dataset_id in state.datasets else "Enterprise Sensitive Dataset"
    html_content = generate_forensic_html_report(target_result, dataset_name)
    return Response(content=html_content, media_type="text/html")


@router.post("/siem-test")
def test_siem_webhook_payload(req: SIEMAlertTest):
    """Generate and return an enterprise SIEM / SOC alert payload."""
    target_result = None
    for res in state.analysis_history:
        if res.analysis_id == req.analysis_id:
            target_result = res
            break

    if not target_result:
        raise HTTPException(status_code=404, detail="Analysis result not found")

    payload = {
        "event_type": "DATA_LEAKAGE_ATTRIBUTION_ALERT",
        "severity": "CRITICAL" if target_result.canary_hits_total > 0 else "HIGH",
        "timestamp": target_result.analyzed_at,
        "incident_id": target_result.analysis_id,
        "target_dataset_id": target_result.dataset_id,
        "attributed_suspect": {
            "agent_id": target_result.top_suspect_id,
            "agent_name": target_result.top_suspect_name,
            "guilt_confidence_percentage": round(target_result.highest_probability * 100, 2),
            "canary_honeytoken_confirmed": target_result.canary_hits_total > 0
        },
        "statistics": {
            "total_leaked_records": target_result.total_leaked_records,
            "matched_records": target_result.matched_leaked_records,
            "canary_hits": target_result.canary_hits_total
        },
        "target_siem": req.siem_type,
        "dispatch_status": "MOCKED_SUCCESS_200_OK"
    }
    return payload
