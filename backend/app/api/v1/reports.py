"""Reports API — PDF & HTML Forensic Audit Incident Reports."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.leak_analysis import LeakAnalysis, AgentGuiltScoreRecord
from backend.app.models.dataset import Dataset
from backend.app.services.pdf_report_service import generate_pdf_incident_report
from backend.engine.reports import generate_forensic_html_report
from backend.engine.models import LeakAnalysisResult, AgentGuiltScore

router = APIRouter(prefix="/reports", tags=["Forensic Incident Reports"])


def _build_analysis_dict(analysis_id: str, db: Session):
    la = db.query(LeakAnalysis).filter(LeakAnalysis.id == analysis_id).first()
    if not la:
        raise HTTPException(status_code=404, detail="Analysis result not found")

    scores = db.query(AgentGuiltScoreRecord).filter(AgentGuiltScoreRecord.analysis_id == analysis_id).all()
    score_dicts = [
        {
            "agent_id": s.agent_id,
            "agent_name": s.agent_name,
            "guilt_probability": s.guilt_probability,
            "matching_records_count": s.matching_records_count,
            "canary_records_found": s.canary_records_found,
            "verdict": s.verdict,
            "explanation": s.explanation
        }
        for s in scores
    ]

    dataset = db.query(Dataset).filter(Dataset.id == la.dataset_id).first()
    dataset_name = dataset.name if dataset else "Sensitive Enterprise Dataset"

    data = {
        "analysis_id": la.id,
        "dataset_id": la.dataset_id,
        "top_suspect_name": la.top_suspect_name,
        "highest_probability": la.highest_probability,
        "canary_hits_total": la.canary_hits_total,
        "total_leaked_records": la.total_leaked_records,
        "matched_leaked_records": la.matched_leaked_records,
        "agent_scores": score_dicts
    }
    return data, dataset_name, la, scores


@router.get("/{analysis_id}/pdf", summary="Download PDF Forensic Incident Report")
def download_pdf_report(analysis_id: str, db: Session = Depends(get_db)):
    data, dataset_name, _, _ = _build_analysis_dict(analysis_id, db)
    pdf_bytes = generate_pdf_incident_report(data, dataset_name)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="DecodeX_Forensic_Report_{analysis_id}.pdf"'}
    )


@router.get("/{analysis_id}/html", summary="View HTML Forensic Report")
def view_html_report(analysis_id: str, db: Session = Depends(get_db)):
    _, dataset_name, la, scores = _build_analysis_dict(analysis_id, db)

    score_models = [
        AgentGuiltScore(
            agent_id=s.agent_id,
            agent_name=s.agent_name,
            guilt_probability=s.guilt_probability,
            matching_records_count=s.matching_records_count,
            matching_genuine_count=s.matching_genuine_count,
            canary_records_found=s.canary_records_found,
            triggered_canary_tokens=s.triggered_canary_tokens or [],
            verdict=s.verdict,
            explanation=s.explanation or ""
        )
        for s in scores
    ]

    res_model = LeakAnalysisResult(
        analysis_id=la.id,
        dataset_id=la.dataset_id,
        leak_source_name=la.leak_source_name,
        total_leaked_records=la.total_leaked_records,
        matched_leaked_records=la.matched_leaked_records,
        unmatched_leaked_records=la.unmatched_leaked_records,
        canary_hits_total=la.canary_hits_total,
        independent_leak_prob_p=la.independent_leak_prob_p,
        agent_scores=score_models,
        top_suspect_id=la.top_suspect_id,
        top_suspect_name=la.top_suspect_name,
        highest_probability=la.highest_probability,
        canary_confirmed_agent_id=la.canary_confirmed_agent_id,
        overlap_matrix=la.overlap_matrix or {},
        analyzed_at=la.created_at.isoformat() if la.created_at else ""
    )

    html = generate_forensic_html_report(res_model, dataset_name)
    return Response(content=html, media_type="text/html")
