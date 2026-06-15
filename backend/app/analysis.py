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
                    title="Cloned batch: same unit in two places at once",
                    detail=(
                        f"The serial was 'received' in {a['location']} and {b['location']} "
                        f"only {gap_txt} apart ({dist:.0f} km away). "
                        "A physical unit cannot be in both places."
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
            title="Origin supplier on a regulatory blacklist",
            detail=(
                f"{origin['name']} ({origin['country']}) is listed on {origin.get('blacklist_source', 'a blacklist')}. "
                f"No EMA/FDA certification or GDP license."
            ),
            evidence=[
                f"Origin: {origin['name']} — {origin.get('risk_notes', '')}",
                f"Source: {origin.get('blacklist_source', 'N/A')}",
            ],
        )
    if not origin["certified_by"]:
        return Finding(
            severity="warning",
            points=20,
            title="Uncertified origin supplier",
            detail=f"{origin['name']} has no verifiable EMA/FDA certification.",
            evidence=[f"Origin: {origin['name']} ({origin['country']})"],
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
            title="Distribution pattern consistent with illicit diversion",
            detail=(
                f"{len(handoffs)} hand-offs in {span_h:.0f}h over an unusual "
                f"route: {route}."
            ),
            evidence=[f"Route: {route}", f"Custodians: {len(handoffs)} in {span_h:.0f}h"],
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
        return "CRITICAL"
    if score >= 40:
        return "HIGH"
    if score >= 15:
        return "MODERATE"
    return "LOW"


def canonical_report(batch_id: str, store: DataStore) -> dict[str, Any]:
    """Deterministic subset of the report used for the on-chain fingerprint.
    Excludes the LLM narrative (non-deterministic) so re-deriving the hash
    later yields the exact same value — that is what makes verification work."""
    bid = batch_id.strip().upper()
    records = store.ledger.events_for(bid)
    findings = [
        f for f in (
            detect_duplicate_location(records),
            assess_origin_supplier(records, store),
            evaluate_distribution_pattern(records, store),
        ) if f
    ]
    score = min(100, sum(f.points for f in findings))
    return {
        "batch_id": bid,
        "risk_score": score,
        "risk_band": score_band(score),
        "findings": [
            {"severity": f.severity, "points": f.points, "title": f.title, "detail": f.detail}
            for f in findings
        ],
        "recommended_actions": recommended_actions(score, findings),
    }


def recommended_actions(score: int, findings: list[Finding]) -> list[str]:
    if score >= 75:
        return [
            "Immediate recall of the batch from the distribution chain",
            "Notify COFEPRIS / EMA / FDA within the next 24h",
            "Quarantine every unit carrying this serial",
            "Open a counterfeiting investigation (DSCSA §582)",
        ]
    if score >= 40:
        return [
            "Temporary hold on the batch pending verification",
            "Request GDP documentation from the origin supplier",
            "Escalate to the quality lead",
        ]
    return ["Continuous monitoring", "Log in the audit trail"]
