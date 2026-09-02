"""PDF Incident Report Generator using ReportLab — DecodeX Security Technologies."""

import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from typing import Dict, Any


def generate_pdf_incident_report(analysis_data: Dict[str, Any], dataset_name: str) -> bytes:
    """Generates an audit-ready PDF forensic incident report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0ea5e9')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b')
    )

    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("DECODEX SECURITY TECHNOLOGIES", subtitle_style))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("Data Breach Attribution & Forensic Incident Report", title_style))
    elements.append(Paragraph("Automated Data Leakage Detection & Guilt Assessment Engine (DLD-SOC)", subtitle_style))
    elements.append(Spacer(1, 14))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0ea5e9'), spaceAfter=14))

    # Metadata Grid
    top_suspect = analysis_data.get("top_suspect_name") or "Inconclusive"
    top_prob = analysis_data.get("highest_probability", 0.0)
    canary_hits = analysis_data.get("canary_hits_total", 0)

    meta_table_data = [
        [
            Paragraph("<b>Incident ID:</b>", body_style),
            Paragraph(str(analysis_data.get("analysis_id", "N/A")), bold_body_style),
            Paragraph("<b>Target Dataset:</b>", body_style),
            Paragraph(dataset_name, bold_body_style)
        ],
        [
            Paragraph("<b>Attributed Culprit:</b>", body_style),
            Paragraph(f"<font color='#dc2626'><b>{top_suspect} ({top_prob*100:.1f}%)</b></font>", bold_body_style),
            Paragraph("<b>Canary Traps:</b>", body_style),
            Paragraph(f"<b>{canary_hits} Confirmed Hits</b>", bold_body_style)
        ],
        [
            Paragraph("<b>Total Leaked Rows:</b>", body_style),
            Paragraph(str(analysis_data.get("total_leaked_records", 0)), body_style),
            Paragraph("<b>Matched Rows:</b>", body_style),
            Paragraph(str(analysis_data.get("matched_leaked_records", 0)), body_style)
        ]
    ]

    meta_table = Table(meta_table_data, colWidths=[1.4*inch, 2.2*inch, 1.4*inch, 2.2*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 18))

    # Agent Breakdown Section
    elements.append(Paragraph("<b>Agent Guilt Assessment & Mathematical Attribution</b>", styles['Heading3']))
    elements.append(Spacer(1, 6))

    agent_scores = analysis_data.get("agent_scores", [])
    table_rows = [
        [
            Paragraph("<b>Vendor / Agent</b>", bold_body_style),
            Paragraph("<b>Guilt Prob</b>", bold_body_style),
            Paragraph("<b>Matched</b>", bold_body_style),
            Paragraph("<b>Canaries</b>", bold_body_style),
            Paragraph("<b>Verdict</b>", bold_body_style)
        ]
    ]

    for score in agent_scores:
        name = score.get("agent_name", "Unknown")
        prob = score.get("guilt_probability", 0.0)
        matched = str(score.get("matching_records_count", 0))
        canary = str(score.get("canary_records_found", 0))
        verdict = score.get("verdict", "CLEARED")
        
        v_color = "#dc2626" if verdict == "CONFIRMED_LEAKER" else ("#ea580c" if prob >= 0.85 else "#16a34a")
        
        table_rows.append([
            Paragraph(name, body_style),
            Paragraph(f"<b>{prob*100:.1f}%</b>", body_style),
            Paragraph(matched, body_style),
            Paragraph(f"<font color='#dc2626'><b>{canary}</b></font>" if int(canary) > 0 else "0", body_style),
            Paragraph(f"<font color='{v_color}'><b>{verdict}</b></font>", body_style)
        ])

    score_table = Table(table_rows, colWidths=[2.4*inch, 1.1*inch, 1.0*inch, 1.1*inch, 1.6*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 20))

    # Remediation Steps
    elements.append(Paragraph("<b>Recommended Incident Response Actions (DecodeX IR Unit)</b>", styles['Heading3']))
    elements.append(Spacer(1, 6))
    remediation_text = (
        "1. <b>Credential Revocation:</b> Suspend API credentials and export access for suspect vendor.<br/>"
        "2. <b>Cryptographic Evidence Preservation:</b> Retain HMAC canary records for legal discovery.<br/>"
        "3. <b>Statutory Compliance:</b> Execute breach notification under GDPR Art. 33 / DPDP regulations within 72 hours."
    )
    elements.append(Paragraph(remediation_text, body_style))
    elements.append(Spacer(1, 24))

    # Footer
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceAfter=10))
    elements.append(Paragraph("Copyright (c) 2026 DecodeX Security Technologies Private Limited. All rights reserved.", subtitle_style))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
