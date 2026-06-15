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
        print("[X] Missing variables (add a .env in backend/ with):")
        for k in missing:
            print(f"   - {k}")
        print("\nCurrent mode:", llm.mode(), "→ the demo will use mock narration (still works).")
        return

    print("[OK] Variables present. Endpoint:", os.getenv("AZURE_OPENAI_ENDPOINT"))
    print("  Deployment:", os.getenv("AZURE_OPENAI_DEPLOYMENT"))
    print("\nTesting a real call to GPT-4o...\n")
    try:
        out = llm._azure_narrate(
            "Confirm in one sentence that the compliance agent is operational.",
            ["Test batch MX-2026-4471", "Risk score 94/100"],
        )
        print("[OK] GPT-4o response:\n  ", out)
        print("\n[OK] All good — the demo will run with real reasoning (badge 'GPT-4o').")
    except Exception as exc:  # noqa: BLE001
        print("[X] The call failed:", repr(exc))
        print("\nCheck endpoint/key/deployment/api-version. The demo falls back to mock automatically.")


if __name__ == "__main__":
    main()
