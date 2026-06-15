"""Deterministic supply-chain analysis.

Risk scoring is computed in code (not by the LLM) so the demo is reproducible
and defensible. The LLM narrates and explains these findings; it does not
invent them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .data import DataStore
from .ledger import LedgerRecord


@dataclass
class Finding:
    severity: str  # "info" | "warning" | "critical"
    points: int
    title: str
    detail: str
    evidence: list[str]


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _haversine_km(a: list[float], b: list[float]) -> float:
    from math import asin, cos, radians, sin, sqrt

    lat1, lon1, lat2, lon2 = map(radians, [a[0], a[1], b[0], b[1]])
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def detect_duplicate_location(records: list[LedgerRecord]) -> Finding | None:
    """A genuine unit cannot be physically received in two distant places at
    once. Overlapping custody windows across far-apart locations => cloning."""
    receives = [r.public() for r in records if r.public().get("event") == "RECEIVE"]
    for i in range(len(receives)):
        for j in range(i + 1, len(receives)):
            a, b = receives[i], receives[j]
            gap_h = abs((_parse(a["timestamp"]) - _parse(b["timestamp"])).total_seconds()) / 3600
            dist = _haversine_km(a["geo"], b["geo"])
            if dist > 500 and gap_h < 24:
                gap_txt = f"{gap_h * 60:.0f} min" if gap_h < 1 else f"{gap_h:.0f}h"
                return Finding(
                    severity="critical",
                    points=45,
                    title="Lote clonado: misma unidad en dos lugares a la vez",
                    detail=(
                        f"El serial fue 'recibido' en {a['location']} y {b['location']} "
                        f"con sólo {gap_txt} de diferencia ({dist:.0f} km aparte). "
                        "Una unidad física no puede estar en ambos lugares."
                    ),
                    evidence=[
                        f"{a['location']} @ {a['timestamp']} (hash {a['hash'][:12]}…)",
                        f"{b['location']} @ {b['timestamp']} (hash {b['hash'][:12]}…)",
                    ],
                )
    return None


def assess_origin_supplier(records: list[LedgerRecord], store: DataStore) -> Finding | None:
    ordered = sorted((r.public() for r in records), key=lambda e: e["timestamp"])
    if not ordered:
        return None
    origin = store.supplier(ordered[0].get("supplier_id"))
    if not origin:
        return None
    if origin["blacklisted"]:
        return Finding(
            severity="critical",
            points=35,
            title="Proveedor de origen en lista negra regulatoria",
            detail=(
                f"{origin['name']} ({origin['country']}) figura en {origin.get('blacklist_source', 'lista negra')}. "
                f"Sin certificación EMA/FDA ni licencia GDP."
            ),
            evidence=[
                f"Origen: {origin['name']} — {origin.get('risk_notes', '')}",
                f"Fuente: {origin.get('blacklist_source', 'N/D')}",
            ],
        )
    if not origin["certified_by"]:
        return Finding(
            severity="warning",
            points=20,
            title="Proveedor de origen no certificado",
            detail=f"{origin['name']} no tiene certificación EMA/FDA verificable.",
            evidence=[f"Origen: {origin['name']} ({origin['country']})"],
        )
    return None


def evaluate_distribution_pattern(records: list[LedgerRecord], store: DataStore) -> Finding | None:
    ordered = sorted((r.public() for r in records), key=lambda e: e["timestamp"])
    if len(ordered) < 2:
        return None

    handoffs = {e.get("supplier_id") for e in ordered}
    span_h = (_parse(ordered[-1]["timestamp"]) - _parse(ordered[0]["timestamp"])).total_seconds() / 3600
    countries = []
    for e in ordered:
        c = (store.supplier(e.get("supplier_id")) or {}).get("country")
        if c and (not countries or countries[-1] != c):
            countries.append(c)

    fast_handoffs = len(handoffs) >= 3 and span_h <= 72
    cross_continent = len(countries) >= 3

    if fast_handoffs or cross_continent:
        route = " → ".join(countries)
        return Finding(
            severity="critical" if (fast_handoffs and cross_continent) else "warning",
            points=14 if (fast_handoffs and cross_continent) else 8,
            title="Patrón de distribución consistente con diversión ilícita",
            detail=(
                f"{len(handoffs)} cambios de manos en {span_h:.0f}h sobre una ruta "
                f"inusual: {route}."
            ),
            evidence=[f"Ruta: {route}", f"Custodios: {len(handoffs)} en {span_h:.0f}h"],
        )
    return None


def route_geo(records: list[LedgerRecord]) -> list[dict[str, Any]]:
    return [
        {
            "location": r.public()["location"],
            "geo": r.public()["geo"],
            "event": r.public()["event"],
            "timestamp": r.public()["timestamp"],
        }
        for r in sorted(records, key=lambda x: x.public()["timestamp"])
    ]


def score_band(score: int) -> str:
    if score >= 75:
        return "CRÍTICO"
    if score >= 40:
        return "ALTO"
    if score >= 15:
        return "MODERADO"
    return "BAJO"


def recommended_actions(score: int, findings: list[Finding]) -> list[str]:
    if score >= 75:
        return [
            "Retiro inmediato del lote de la cadena de distribución",
            "Notificación a COFEPRIS / EMA / FDA en las próximas 24h",
            "Cuarentena de todas las unidades con este serial",
            "Apertura de investigación de falsificación (DSCSA §582)",
        ]
    if score >= 40:
        return [
            "Bloqueo temporal del lote pendiente de verificación",
            "Solicitud de documentación GDP al proveedor de origen",
            "Escalamiento al responsable de calidad",
        ]
    return ["Monitoreo continuo", "Registro en bitácora de auditoría"]
