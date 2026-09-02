"""Forensic Audit Report Generator for Data Breach Attribution."""

from typing import Dict, Any
from datetime import datetime, timezone
from .models import LeakAnalysisResult


def generate_forensic_html_report(result: LeakAnalysisResult, dataset_name: str) -> str:
    """Generates an enterprise-grade HTML forensic incident report."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    top_suspect_badge = ""
    if result.canary_confirmed_agent_id:
        top_suspect_badge = f'<span style="background-color: #dc2626; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">🚨 100% CANARY HONEYTOKEN CONFIRMED: {result.top_suspect_name}</span>'
    elif result.highest_probability >= 0.85:
        top_suspect_badge = f'<span style="background-color: #ea580c; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">⚠️ HIGH PROBABILITY CULPRIT: {result.top_suspect_name} ({result.highest_probability*100:.1f}%)</span>'
    else:
        top_suspect_badge = f'<span style="background-color: #4b5563; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold;">INCONCLUSIVE OVERLAP: {result.top_suspect_name}</span>'

    rows_html = ""
    for score in result.agent_scores:
        verdict_color = "#dc2626" if score.verdict == "CONFIRMED_LEAKER" else ("#ea580c" if score.verdict == "HIGH_SUSPICION" else ("#eab308" if score.verdict == "MODERATE_SUSPICION" else "#22c55e"))
        canary_text = f'<strong style="color: #dc2626;">🚨 {score.canary_records_found} Canary Hits</strong>' if score.canary_records_found > 0 else '0'
        rows_html += f"""
        <tr style="border-bottom: 1px solid #374151;">
            <td style="padding: 12px; font-weight: 600;">{score.agent_name} <span style="font-size: 11px; color: #9ca3af;">({score.agent_id})</span></td>
            <td style="padding: 12px; font-weight: bold; color: {verdict_color};">{score.guilt_probability * 100:.1f}%</td>
            <td style="padding: 12px;">{score.matching_records_count}</td>
            <td style="padding: 12px;">{canary_text}</td>
            <td style="padding: 12px;"><span style="color: {verdict_color}; font-weight: 600;">{score.verdict}</span></td>
            <td style="padding: 12px; font-size: 13px; color: #d1d5db;">{score.explanation}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Forensic Incident Report - {result.analysis_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 40px;
        }}
        .report-card {{
            max-width: 900px;
            margin: 0 auto;
            background-color: #1e293b;
            border-radius: 12px;
            padding: 32px;
            border: 1px solid #334155;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        }}
        .header-title {{
            font-size: 24px;
            font-weight: 800;
            color: #38bdf8;
            letter-spacing: -0.5px;
            margin-bottom: 4px;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin: 24px 0;
            padding: 16px;
            background-color: #0f172a;
            border-radius: 8px;
            border: 1px solid #334155;
        }}
        .meta-item {{
            font-size: 12px;
            color: #94a3b8;
        }}
        .meta-item strong {{
            display: block;
            font-size: 15px;
            color: #f1f5f9;
            margin-top: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
            font-size: 14px;
        }}
        th {{
            text-align: left;
            padding: 12px;
            background-color: #0f172a;
            color: #94a3b8;
            font-weight: 600;
            border-bottom: 2px solid #334155;
        }}
        .remediation {{
            background: rgba(14, 165, 233, 0.1);
            border-left: 4px solid #38bdf8;
            padding: 16px;
            border-radius: 4px;
            margin-top: 24px;
        }}
        .footer {{
            margin-top: 32px;
            text-align: center;
            font-size: 12px;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="report-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="display: flex; align-items: center; gap: 16px;">
                <img src="/branding/decodex_logo_full_horizontal.png" alt="DecodeX" style="height: 38px; object-fit: contain;" />
                <div>
                    <div class="header-title">Data Breach Attribution Forensic Report</div>
                    <div style="color: #94a3b8; font-size: 13px;">DecodeX Security Technologies Private Limited • Incident Response Unit</div>
                </div>
            </div>
            <div>{top_suspect_badge}</div>
        </div>

        <div class="meta-grid">
            <div class="meta-item">Incident ID<strong>{result.analysis_id}</strong></div>
            <div class="meta-item">Target Dataset<strong>{dataset_name}</strong></div>
            <div class="meta-item">Leaked Records<strong>{result.total_leaked_records} ({result.matched_leaked_records} matched)</strong></div>
            <div class="meta-item">Timestamp<strong>{timestamp}</strong></div>
        </div>

        <h3 style="color: #f1f5f9; margin-top: 28px; border-bottom: 1px solid #334155; padding-bottom: 8px;">
            Agent Attribution & Mathematical Guilt Scores
        </h3>
        <table>
            <thead>
                <tr>
                    <th>Agent / Third-Party</th>
                    <th>Guilt Prob</th>
                    <th>Matched Rows</th>
                    <th>Canary Traps</th>
                    <th>Verdict</th>
                    <th>Forensic Explanation</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        <div class="remediation">
            <h4 style="margin: 0 0 8px 0; color: #38bdf8;">⚖️ Recommended Incident Response Actions:</h4>
            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #e2e8f0; line-height: 1.6;">
                <li><strong>Immediate Credential Revocation:</strong> Suspend API tokens and data export privileges for suspect vendor: <code>{result.top_suspect_name}</code>.</li>
                <li><strong>Forensic Audit & Legal Notice:</strong> Issue formal breach notification and non-disclosure inquiry citing cryptographic canary signatures.</li>
                <li><strong>Regulatory Compliance:</strong> Prepare breach disclosure filing under GDPR Article 33 / HIPAA Breach Notification rules within 72 hours.</li>
            </ul>
        </div>

        <div class="footer">
            Generated by <strong>DecodeX DLD-SOC Engine</strong> • Proprietary work product of <strong>DecodeX Security Technologies Private Limited</strong>. All rights reserved.
        </div>
    </div>
</body>
</html>"""
    return html
