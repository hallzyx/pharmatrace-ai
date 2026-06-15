"""Tamper-proof audit ledger.

The agent only depends on the LedgerBackend interface, so the storage engine
is swappable: a local hash-chained ledger today (zero dependencies, always
available) and Hedera Consensus Service as a drop-in for public consensus.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

GENESIS_HASH = "0" * 64


def _hash_record(prev_hash: str, payload: dict[str, Any]) -> str:
    """Hash of (previous hash + canonical payload). Editing any past record
    breaks every hash that follows it — that is the tamper-evidence."""
    body = prev_hash + json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


@dataclass
class LedgerRecord:
    index: int
    payload: dict[str, Any]
    prev_hash: str
    hash: str

    def public(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
            **self.payload,
        }


class LedgerBackend(ABC):
    name: str = "abstract"

    @abstractmethod
    def append(self, payload: dict[str, Any]) -> LedgerRecord: ...

    @abstractmethod
    def events_for(self, batch_id: str) -> list[LedgerRecord]: ...

    @abstractmethod
    def verify_integrity(self) -> bool: ...


@dataclass
class LocalHashChainLedger(LedgerBackend):
    """In-memory blockchain-style ledger. Each record commits to the previous
    record's hash, so the whole chain is verifiable and tamper-evident."""

    name: str = "local-hashchain"
    _records: list[LedgerRecord] = field(default_factory=list)

    def append(self, payload: dict[str, Any]) -> LedgerRecord:
        prev_hash = self._records[-1].hash if self._records else GENESIS_HASH
        index = len(self._records)
        record = LedgerRecord(
            index=index,
            payload=payload,
            prev_hash=prev_hash,
            hash=_hash_record(prev_hash, payload),
        )
        self._records.append(record)
        return record

    def events_for(self, batch_id: str) -> list[LedgerRecord]:
        return [r for r in self._records if r.payload.get("batch_id") == batch_id]

    def verify_integrity(self) -> bool:
        prev_hash = GENESIS_HASH
        for record in self._records:
            if record.prev_hash != prev_hash:
                return False
            if record.hash != _hash_record(prev_hash, record.payload):
                return False
            prev_hash = record.hash
        return True

    @property
    def head(self) -> str:
        return self._records[-1].hash if self._records else GENESIS_HASH


def seed_from_events(ledger: LedgerBackend, events: list[dict[str, Any]]) -> None:
    """Append the historical supply-chain events in chronological order."""
    for event in sorted(events, key=lambda e: e["timestamp"]):
        ledger.append(event)
