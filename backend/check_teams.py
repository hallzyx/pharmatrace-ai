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
    "product": "Semaglutide 1mg (Ozempic-equivalent)",
    "risk_score": 94,
    "risk_band": "CRÍTICO",
    "explanation": (
        "Lote clonado (misma unidad en Madrid y Guadalajara con 15 min de diferencia), "
        "proveedor en lista negra FDA y patrón de distribución ilícito. Retiro inmediato recomendado."
    ),
}


def main() -> None:
    print("=== PharmaTrace AI · Teams (Work IQ) webhook check ===\n")
    if not os.getenv("TEAMS_WEBHOOK_URL"):
        print("[X] Falta TEAMS_WEBHOOK_URL en backend/.env")
        print("    El demo usará alerta SIMULADA (igual funciona).")
        return

    print("[..] Enviando Adaptive Card de prueba al canal de Teams...\n")
    result = notify.send_teams_alert(SAMPLE_REPORT)
    print("    sent   :", result["sent"])
    print("    channel:", result["channel"])
    print("    message:", result["message"])
    print()
    if result["sent"]:
        print("[OK] POST aceptado. Revisá el canal de Teams: deberías ver una tarjeta")
        print("     '⚠️ PharmaTrace AI — Riesgo CRÍTICO' con lote, score y explicación.")
        print("\n     Si el POST fue aceptado pero NO ves la tarjeta (o llega vacía),")
        print("     avisame: hay que ajustar el formato del payload a tu plantilla de Power Automate.")
    else:
        print("[X] No se pudo enviar. Revisá la URL del webhook en backend/.env")


if __name__ == "__main__":
    main()
