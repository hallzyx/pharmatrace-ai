"""Pre-demo check for the Work IQ (Teams) webhook.

Run:  python check_teams.py
Reads backend/.env automatically, posts a real test Adaptive Card to your
Teams channel, and reports the result. Go look at the channel afterwards.
"""

import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
except Exception:  # pragma: no cover
    pass

import app  # noqa: E402, F401 — triggers .env loading
from app import notify  # noqa: E402

SAMPLE_REPORT = {
    "batch_id": "MX-2026-4471",
    "product": "Semaglutide 1mg (GLP-1 weight-loss therapy)",
    "risk_score": 94,
    "risk_band": "CRITICAL",
    "explanation": (
        "Cloned batch (same unit in Madrid and Guadalajara 15 min apart), "
        "FDA-blacklisted supplier and illicit distribution pattern. Immediate recall recommended."
    ),
}


def main() -> None:
    print("=== PharmaTrace AI · Teams (Work IQ) webhook check ===\n")
    if not os.getenv("TEAMS_WEBHOOK_URL"):
        print("[X] TEAMS_WEBHOOK_URL is missing in backend/.env")
        print("    The demo will use a SIMULATED alert (still works).")
        return

    print("[..] Sending a test Adaptive Card to the Teams channel...\n")
    result = notify.send_teams_alert(SAMPLE_REPORT)
    print("    sent   :", result["sent"])
    print("    channel:", result["channel"])
    print("    message:", result["message"])
    print()
    if result["sent"]:
        print("[OK] POST accepted. Check the Teams channel: you should see a card")
        print("     '⚠️ PharmaTrace AI — CRITICAL Risk' with batch, score and explanation.")
        print("\n     If the POST was accepted but you do NOT see the card (or it arrives empty),")
        print("     let me know: we need to match the payload to your Power Automate template.")
    else:
        print("[X] Could not send. Check the webhook URL in backend/.env")


if __name__ == "__main__":
    main()
