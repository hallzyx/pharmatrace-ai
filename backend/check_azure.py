"""Pre-demo connectivity check for Azure OpenAI / GPT-4o.

Run:  python check_azure.py
Reads backend/.env automatically. Tells you exactly what's missing.
"""

import os
import sys

# Windows consoles default to cp1252 and choke on UTF-8 output. Force UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
except Exception:  # pragma: no cover
    pass

import app  # noqa: E402, F401 — triggers .env loading
from app import llm  # noqa: E402


def main() -> None:
    print("=== PharmaTrace AI · Azure connectivity check ===\n")
    required = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print("[X] Faltan variables (poné un .env en backend/ con):")
        for k in missing:
            print(f"   - {k}")
        print("\nMode actual:", llm.mode(), "→ el demo usará narración mock (igual funciona).")
        return

    print("[OK] Variables presentes. Endpoint:", os.getenv("AZURE_OPENAI_ENDPOINT"))
    print("  Deployment:", os.getenv("AZURE_OPENAI_DEPLOYMENT"))
    print("\nProbando una llamada real a GPT-4o...\n")
    try:
        out = llm._azure_narrate(
            "Confirma en una frase que el agente de cumplimiento está operativo.",
            ["Lote de prueba MX-2026-4471", "Risk score 94/100"],
        )
        print("[OK] Respuesta de GPT-4o:\n  ", out)
        print("\n[OK] TODO OK — el demo correrá con razonamiento real (badge 'GPT-4o').")
    except Exception as exc:  # noqa: BLE001
        print("[X] La llamada falló:", repr(exc))
        print("\nRevisá endpoint/key/deployment/api-version. El demo caerá a mock automáticamente.")


if __name__ == "__main__":
    main()
