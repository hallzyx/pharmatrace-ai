"""Hedera Consensus Service (HCS) ledger backend.

Drop-in for LocalHashChainLedger via the LedgerBackend interface. It keeps the
fast local hash chain for the agent's reads, and additionally *anchors*
records to a public Hedera topic for tamper-proof, consensus-timestamped,
publicly verifiable notarization.

Access control: the topic is created with a `submit_key` set to the operator's
public key, so ONLY the account that created the topic can write records.
Reads stay public via mirror nodes (that is what makes the immutability
verifiable). To keep confidentiality you would encrypt the payload — out of
scope here; we anchor only a hash + reference, never sensitive data.

Everything is optional and fails soft: if credentials are missing or the
network is unreachable, the app falls back to the local ledger and the demo
keeps working.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from .ledger import LocalHashChainLedger


def available() -> bool:
    return bool(os.getenv("HEDERA_ACCOUNT_ID") and os.getenv("HEDERA_PRIVATE_KEY"))


def _network() -> str:
    return os.getenv("HEDERA_NETWORK", "testnet")


class HederaLedger(LocalHashChainLedger):
    name: str = "hedera-hcs"

    def __init__(self) -> None:
        super().__init__()
        self.name = "hedera-hcs"  # dataclass __init__ sets the local name; override it
        self.client = None
        self.operator_id = None
        self.topic_id: str = ""
        self.network: str = _network()

    # --- connection / topic setup -------------------------------------------------

    def connect(self) -> "HederaLedger":
        """Set up the client and ensure a topic exists. Raises on failure so the
        caller can fall back to the local ledger."""
        from hiero_sdk_python import AccountId, Client, Network, PrivateKey

        operator_id = AccountId.from_string(os.environ["HEDERA_ACCOUNT_ID"])
        operator_key = PrivateKey.from_string(os.environ["HEDERA_PRIVATE_KEY"])
        client = Client(Network(self.network))
        client.set_operator(operator_id, operator_key)

        self.client = client
        self.operator_id = operator_id
        self._operator_key = operator_key

        existing = os.getenv("HEDERA_TOPIC_ID", "").strip()
        if existing:
            self.topic_id = existing
        else:
            self.topic_id = self._create_topic(operator_key)
        return self

    def _create_topic(self, operator_key: Any) -> str:
        """Create a private topic whose submit key is the operator's public key,
        so only this account can write records to it."""
        from hiero_sdk_python.consensus.topic_create_transaction import (
            TopicCreateTransaction,
        )
        from hiero_sdk_python.response_code import ResponseCode

        tx = (
            TopicCreateTransaction(
                memo="PharmaTrace AI — tamper-proof audit ledger",
                admin_key=operator_key.public_key(),
                submit_key=operator_key.public_key(),  # access control: write = this account only
            )
            .freeze_with(self.client)
            .sign(operator_key)
        )
        receipt = tx.execute(self.client)
        if receipt.status != ResponseCode.SUCCESS:
            raise RuntimeError(f"Topic creation failed: {receipt.status}")
        return str(receipt.topic_id)

    # --- anchoring ----------------------------------------------------------------

    def anchor(self, reference: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Submit a compact, signed notarization to the HCS topic. Returns proof
        metadata (sequence number, running hash, HashScan link). Never raises —
        degrades to a local-only result so the demo cannot break."""
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()
        message = json.dumps(
            {"app": "PharmaTrace", "ref": reference, "sha256": payload_hash}
        )
        if not self.client or not self.topic_id:
            return {"anchored": False, "reason": "hedera-not-connected", "sha256": payload_hash}
        try:
            from hiero_sdk_python import TopicId
            from hiero_sdk_python.consensus.topic_message_submit_transaction import (
                TopicMessageSubmitTransaction,
            )

            # The SDK needs a TopicId object, not a string (which has no _to_proto).
            topic = TopicId.from_string(self.topic_id)
            tx = (
                TopicMessageSubmitTransaction(topic_id=topic, message=message)
                .freeze_with(self.client)
                .sign(self._operator_key)
            )
            receipt = tx.execute(self.client)
            seq = receipt.topic_sequence_number
            # running hash is a nice-to-have; some SDK versions raise on access.
            try:
                running = receipt.topic_running_hash
                running_hex = running.hex()[:24] if running else ""
            except Exception:
                running_hex = ""
            return {
                "anchored": True,
                "topic_id": self.topic_id,
                "sequence_number": seq,
                "running_hash": running_hex,
                "sha256": payload_hash,
                "network": self.network,
                "hashscan_url": f"https://hashscan.io/{self.network}/topic/{self.topic_id}",
            }
        except Exception as exc:  # HACK: never break the demo on a network hiccup
            return {"anchored": False, "reason": str(exc), "sha256": payload_hash}


def try_connect() -> tuple[HederaLedger | None, str]:
    """Return (ledger, message). On any failure returns (None, reason)."""
    if not available():
        return None, "HEDERA_* env not set — using local ledger"
    try:
        ledger = HederaLedger().connect()
        return ledger, f"connected · topic {ledger.topic_id} ({ledger.network})"
    except Exception as exc:  # degrade to local ledger
        return None, f"connect failed ({exc}) — using local ledger"
