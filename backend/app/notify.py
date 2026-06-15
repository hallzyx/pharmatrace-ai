"""Work IQ (M365) notification layer.

Posts an Adaptive-Card-style alert to a Teams Incoming Webhook when
TEAMS_WEBHOOK_URL is set. Otherwise returns a simulated alert so the demo
still shows the notification step working."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

_COLOR = {"CRITICAL": "attention", "HIGH": "warning", "MODERATE": "accent", "LOW": "good"}


def _card(report: dict[str, Any]) -> dict[str, Any]:
    facts = [
        {"title": "Batch", "value": report["batch_id"]},
        {"title": "Product", "value": report["product"]},
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
                     "text": f"⚠️ PharmaTrace AI — {report['risk_band']} Risk"},
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
            "message": f"[SIMULATED] {report['risk_band']} risk alert queued for the quality team (Teams).",
            "card": card,
        }
    try:
        req = urllib.request.Request(
            url, data=json.dumps(card).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=6)  # noqa: S310 (trusted webhook URL)
        return {"sent": True, "channel": "teams", "message": "Alert sent to the quality team's Teams channel."}
    except Exception as exc:  # HACK: degrade gracefully so the demo never breaks
        return {"sent": False, "channel": "teams-error",
                "message": f"[Fallback] Could not reach Teams ({exc}). Alert logged locally.",
                "card": card}
