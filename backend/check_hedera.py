"""Pre-demo check for the Hedera HCS ledger anchoring.

Run:  python check_hedera.py
Reads backend/.env. Connects to Hedera, ensures a topic exists (with a submit
key so only your account can write), anchors a test record, and prints the
topic id + HashScan link. Pin the printed topic id as HEDERA_TOPIC_ID to reuse
it (faster startup, stable demo).
"""

import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
except Exception:  # pragma: no cover
    pass

import app  # noqa: E402, F401 — triggers .env loading
from app import hedera_ledger  # noqa: E402


def main() -> None:
    print("=== PharmaTrace AI · Hedera HCS check ===\n")
    if not hedera_ledger.available():
        print("[X] Missing HEDERA_ACCOUNT_ID / HEDERA_PRIVATE_KEY in backend/.env")
        print("    Get a free testnet account at https://portal.hedera.com")
        print("    The demo runs fine without it (local hash-chained ledger).")
        return

    print("[..] Connecting to Hedera", hedera_ledger._network(), "and ensuring topic...\n")
    ledger, msg = hedera_ledger.try_connect()
    if ledger is None:
        print("[X] Connection failed:", msg)
        print("\n    Check the account id, private key format, and network.")
        return

    print("[OK] Connected.")
    print("     Topic ID :", ledger.topic_id)
    if not os.getenv("HEDERA_TOPIC_ID"):
        print("     ↳ Pin this in .env as HEDERA_TOPIC_ID to reuse it next time.")

    print("\n[..] Anchoring a test record (submit-key signed)...\n")
    result = ledger.anchor("self-test", {"hello": "PharmaTrace"})
    if result.get("anchored"):
        print("[OK] Record anchored on Hedera:")
        print("     Sequence #:", result["sequence_number"])
        print("     Running hash:", result["running_hash"])
        print("     Verify     :", result["hashscan_url"])
        print("\n[OK] All good — analyses will be notarized on Hedera (badge 'hedera-hcs').")
        print("     Access control: only this account's submit key can write to the topic.")
    else:
        print("[X] Anchor failed:", result.get("reason"))


if __name__ == "__main__":
    main()
