"""The multi-step reasoning agent.

Runs as a generator that yields events as it reasons, so the UI can stream
each step live (this is the heart of the demo: visible, step-by-step
reasoning with cited evidence — not a chatbot)."""

from __future__ import annotations

import time
from typing import Any, Iterator

from . import analysis, llm, notify
from .data import DataStore


def _ev(kind: str, **data: Any) -> dict[str, Any]:
    return {"kind": kind, **data}


def _narrate(task: str, finding: "analysis.Finding | None", ok_msg: str) -> str:
    """Have the LLM EXPLAIN the deterministic finding (not re-derive it).
    When a finding exists we hand the model the confirmed conclusion so it
    states it firmly instead of hedging."""
    if finding:
        instruction = (
            f"{task} HALLAZGO CONFIRMADO por el sistema: «{finding.title}». "
            f"{finding.detail} Explícalo en 1-2 frases con tono firme; NO lo pongas en duda."
        )
        return llm.narrate(instruction, finding.evidence)
    return llm.narrate(f"{task} No se detectaron anomalías.", [ok_msg])


def run(batch_id: str, store: DataStore, *, pace: float = 0.45) -> Iterator[dict[str, Any]]:
    batch_id = batch_id.strip().upper()
    records = store.ledger.events_for(batch_id)

    yield _ev("run_start", batch_id=batch_id, mode=llm.mode())

    if not records:
        yield _ev(
            "error",
            message=f"Lote {batch_id} no encontrado en el ledger. "
            f"Conocidos: {', '.join(store.known_batches())}",
        )
        return

    product = records[0].public().get("product", "—")
    findings: list[analysis.Finding] = []

    # Step 1 — authenticity vs. the immutable ledger
    yield _ev("step_start", n=1, title="Verificando autenticidad del lote")
    time.sleep(pace)
    dup = analysis.detect_duplicate_location(records)
    if dup:
        findings.append(dup)
    sev = dup.severity if dup else "info"
    ev = dup.evidence if dup else [f"{len(records)} eventos en cadena, integridad OK"]
    reasoning = _narrate(
        f"Verificación de autenticidad del lote {batch_id} ({product}) contra el ledger inmutable.",
        dup,
        f"{len(records)} eventos consistentes, sin duplicación de ubicación.",
    )
    yield _ev("step_result", n=1, severity=sev, reasoning=reasoning,
              finding=_finding_dict(dup), evidence=ev)

    # Step 2 — origin supplier
    yield _ev("step_start", n=2, title="Analizando proveedor de origen")
    time.sleep(pace)
    sup = analysis.assess_origin_supplier(records, store)
    if sup:
        findings.append(sup)
    reasoning = _narrate(
        "Evaluación de la certificación regulatoria (FDA/EMA) del proveedor de origen.",
        sup,
        "Proveedor de origen con certificación FDA/EMA vigente.",
    )
    yield _ev("step_result", n=2, severity=sup.severity if sup else "info",
              reasoning=reasoning, finding=_finding_dict(sup),
              evidence=sup.evidence if sup else ["Origen certificado"])

    # Step 3 — distribution pattern
    yield _ev("step_start", n=3, title="Evaluando patrón de distribución")
    time.sleep(pace)
    dist = analysis.evaluate_distribution_pattern(records, store)
    if dist:
        findings.append(dist)
    reasoning = _narrate(
        "Evaluación de la ruta geográfica y la velocidad de los cambios de custodia.",
        dist,
        "Ruta y velocidad de distribución dentro de parámetros normales.",
    )
    yield _ev("step_result", n=3, severity=dist.severity if dist else "info",
              reasoning=reasoning, finding=_finding_dict(dist),
              evidence=dist.evidence if dist else ["Patrón normal"],
              route=analysis.route_geo(records))

    # Step 4 — risk report
    yield _ev("step_start", n=4, title="Generando reporte de riesgo")
    time.sleep(pace)
    score = min(100, sum(f.points for f in findings))
    band = analysis.score_band(score)
    actions = analysis.recommended_actions(score, findings)
    explanation = llm.narrate(
        f"Sintetiza en 1-2 frases firmes el nivel de riesgo {band} (score {score}/100) "
        f"del lote {batch_id}, integrando los hallazgos confirmados.",
        [f"{f.title}: {f.detail}" for f in findings] or ["Sin hallazgos de riesgo"],
    )
    report = {
        "batch_id": batch_id,
        "product": product,
        "risk_score": score,
        "risk_band": band,
        "ledger_integrity": store.ledger.verify_integrity(),
        "ledger_backend": store.ledger.name,
        "findings": [_finding_dict(f) for f in findings],
        "recommended_actions": actions,
        "explanation": explanation,
    }
    yield _ev("step_result", n=4, severity="critical" if score >= 75 else "warning" if score >= 40 else "info",
              reasoning=explanation, report=report)

    # Step 5 — alert stakeholders (Work IQ)
    yield _ev("step_start", n=5, title="Alertando a stakeholders (Teams)")
    time.sleep(pace)
    alert = notify.send_teams_alert(report)
    yield _ev("step_result", n=5, severity="info",
              reasoning=alert["message"], alert=alert)

    yield _ev("run_complete", report=report)


def _finding_dict(f: analysis.Finding | None) -> dict[str, Any] | None:
    if not f:
        return None
    return {
        "severity": f.severity,
        "points": f.points,
        "title": f.title,
        "detail": f.detail,
        "evidence": f.evidence,
    }
