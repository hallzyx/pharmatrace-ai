"""Loads the fictional-but-realistic dataset and seeds the audit ledger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import hedera_ledger
from .ledger import LedgerBackend, LocalHashChainLedger, seed_from_events

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load(name: str) -> dict[str, Any]:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


class DataStore:
    def __init__(self, ledger: LedgerBackend | None = None) -> None:
        suppliers_raw = _load("suppliers.json")["suppliers"]
        batches_raw = _load("batches.json")
        self.suppliers: dict[str, dict[str, Any]] = {
            s["id"]: s for s in suppliers_raw
        }
        self.products: dict[str, str] = batches_raw["products"]
        self.events: list[dict[str, Any]] = batches_raw["ledger_events"]

        if ledger is not None:
            self.ledger = ledger
            self.ledger_status = "explicit backend"
        else:
            hedera, msg = hedera_ledger.try_connect()
            self.ledger = hedera or LocalHashChainLedger()
            self.ledger_status = f"Hedera: {msg}"
        seed_from_events(self.ledger, self.events)

    def supplier(self, supplier_id: str | None) -> dict[str, Any] | None:
        return self.suppliers.get(supplier_id) if supplier_id else None

    def known_batches(self) -> list[str]:
        return sorted(self.products.keys())
