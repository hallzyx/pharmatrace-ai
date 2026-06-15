"""Work IQ (M365) notification layer.

Posts an Adaptive-Card-style alert to a Teams Incoming Webhook when
TEAMS_WEBHOOK_URL is set. Otherwise returns a simulated alert so the demo
still shows the notification step working."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

_COLOR = {"CRÍTICO": "attention", "ALTO": "warning", "MODERADO": "accent", "BAJO": "good"}


def _card(report: dict[str, Any]) -> dict[str, Any]:
    facts = [
        {"title": "Lote", "value": report["batch_id"]},
        {"title": "Producto", "value": report["product"]},
        {"title": "Risk score", "value": f"{report['risk_score']}/100 ({report['risk_band']})"},
    ]
    return {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {"type": "TextBlock", "size": "Large", "weight": "Bolder",
                     "color": _COLOR.get(report["risk_band"], "default"),
                     "text": f"⚠️ PharmaTrace AI — Riesgo {report['risk_band']}"},
                    {"type": "FactSet", "facts": facts},
                    {"type": "TextBlock", "wrap": True, "text": report["explanation"]},
                ],
            },
        }],
    }


def send_teams_alert(report: dict[str, Any]) -> dict[str, Any]:
    card = _card(report)
    url = os.getenv("TEAMS_WEBHOOK_URL")
    if not url:
        return {
            "sent": False,
            "channel": "simulated",
            "message": f"[SIMULADO] Alerta de riesgo {report['risk_band']} encolada para el equipo de calidad (Teams).",
            "card": card,
        }
    try:
        req = urllib.request.Request(
            url, data=json.dumps(card).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=6)  # noqa: S310 (trusted webhook URL)
        return {"sent": True, "channel": "teams", "message": "Alerta enviada al canal de Teams del equipo de calidad."}
    except Exception as exc:  # HACK: degrade gracefully so the demo never breaks
        return {"sent": False, "channel": "teams-error",
                "message": f"[Fallback] No se pudo contactar Teams ({exc}). Alerta registrada localmente.",
                "card": card}
