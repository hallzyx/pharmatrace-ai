"""Audit-ready compliance report (PDF).

Turns the agent's risk report into a structured document a quality team can
file for regulatory audit (DSCSA / FMD). Built with reportlab Platypus.
reportlab is optional: the API guards the import so the rest of the app runs
without it.
"""

from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Any

_BAND_COLOR = {
    "CRITICAL": "#f0506e",
    "HIGH": "#f5a623",
    "MODERATE": "#5b8def",
    "LOW": "#34d399",
}
_SEV_COLOR = {"critical": "#f0506e", "warning": "#f5a623", "info": "#34d399"}


def report_id(report: dict[str, Any]) -> str:
    digest = hashlib.sha256(
        json.dumps(report, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return f"PT-{report['batch_id']}-{digest[:8].upper()}"


def build_compliance_pdf(report: dict[str, Any], *, ledger_head: str = "") -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
        title=f"PharmaTrace AI Compliance Report — {report['batch_id']}",
    )
    styles = getSampleStyleSheet()
    H = ParagraphStyle("H", parent=styles["Title"], fontSize=18, spaceAfter=2,
                       textColor=colors.HexColor("#0a3d4a"))
    sub = ParagraphStyle("sub", parent=styles["Normal"], fontSize=9,
                         textColor=colors.HexColor("#5a6b7a"))
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=11,
                        textColor=colors.HexColor("#0a3d4a"), spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9.5, leading=14)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8,
                           textColor=colors.HexColor("#7a8a99"))

    band = report["risk_band"]
    band_color = colors.HexColor(_BAND_COLOR.get(band, "#5a6b7a"))
    rid = report_id(report)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    story: list[Any] = []

    # Header
    story.append(Paragraph("PharmaTrace AI", H))
    story.append(Paragraph("Counterfeit Risk &amp; Compliance Report — DSCSA / FMD", sub))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#cfdae3")))
    story.append(Spacer(1, 8))

    # Metadata + risk banner side by side
    meta = [
        ["Report ID", rid],
        ["Generated", now],
        ["Batch", report["batch_id"]],
        ["Product", report["product"]],
    ]
    meta_tbl = Table(meta, colWidths=[28 * mm, 80 * mm])
    meta_tbl.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#7a8a99")),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))

    risk_style = ParagraphStyle(
        "risk", parent=styles["Normal"], alignment=TA_CENTER,
        textColor=colors.white, fontName="Helvetica-Bold", fontSize=24, leading=26,
    )
    risk_para = Paragraph(
        f"{report['risk_score']}/100<br/><font size='11'>{band} RISK</font>",
        risk_style,
    )
    risk_tbl = Table([[risk_para]], colWidths=[55 * mm], rowHeights=[25 * mm])
    risk_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), band_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    header = Table([[meta_tbl, risk_tbl]], colWidths=[112 * mm, 55 * mm])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(header)
    story.append(Spacer(1, 6))

    # Agent assessment
    story.append(Paragraph("Agent assessment", h2))
    story.append(Paragraph(report.get("explanation", "—"), body))

    # Findings
    story.append(Paragraph("Findings", h2))
    findings = report.get("findings", [])
    if findings:
        cell = ParagraphStyle("cell", parent=body, fontSize=8.5, leading=11)
        cell_b = ParagraphStyle("cellb", parent=cell, fontName="Helvetica-Bold")
        rows = [["Severity", "Finding", "Detail"]]
        for f in findings:
            rows.append([
                f["severity"].upper(),
                Paragraph(f["title"], cell_b),
                Paragraph(f["detail"], cell),
            ])
        ftbl = Table(rows, colWidths=[22 * mm, 50 * mm, 95 * mm])
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a3d4a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfdae3")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fa")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        for i, f in enumerate(findings, start=1):
            style.append(("TEXTCOLOR", (0, i), (0, i),
                          colors.HexColor(_SEV_COLOR.get(f["severity"], "#5a6b7a"))))
            style.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
        ftbl.setStyle(TableStyle(style))
        story.append(ftbl)
    else:
        story.append(Paragraph("No anomalies detected. Batch consistent with a legitimate supply chain.", body))

    # Recommended actions
    story.append(Paragraph("Recommended actions", h2))
    for i, action in enumerate(report.get("recommended_actions", []), start=1):
        story.append(Paragraph(f"{i}. {action}", body))

    # Ledger integrity
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#cfdae3")))
    integ = "VERIFIED" if report.get("ledger_integrity") else "COMPROMISED"
    story.append(Paragraph(
        f"<b>Audit ledger:</b> integrity {integ} · backend "
        f"<b>{report.get('ledger_backend', '—')}</b>"
        + (f" · head {ledger_head[:24]}…" if ledger_head else ""),
        small,
    ))
    hedera = report.get("hedera")
    if hedera and hedera.get("anchored"):
        story.append(Paragraph(
            f"<b>Hedera Consensus Service:</b> anchored on topic {hedera['topic_id']} "
            f"(seq #{hedera['sequence_number']}, {hedera['network']}) · "
            f"publicly verifiable at hashscan.io. Write access restricted to the "
            f"quality authority's account (submit key).",
            small,
        ))
    story.append(Paragraph(
        "This report is derived from a tamper-evident hash-chained ledger. "
        "Report integrity hash: " + rid, small,
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Generated by PharmaTrace AI — automated counterfeit risk agent. "
        "For regulatory audit support under DSCSA (US) and FMD (EU). "
        "Risk scoring is deterministic; narrative generated by the reasoning agent. "
        "Demonstration only — all companies, suppliers and batches are fictional.",
        ParagraphStyle("foot", parent=small, alignment=TA_CENTER),
    ))

    doc.build(story)
    return buf.getvalue()
