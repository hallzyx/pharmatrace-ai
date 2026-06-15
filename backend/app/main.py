"""FastAPI app: serves the demo UI and streams the agent's reasoning over SSE."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse

from . import agent, llm
from .data import DataStore

app = FastAPI(title="PharmaTrace AI", version="0.1.0")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# Single shared, pre-seeded ledger for the session.
store = DataStore()


@app.get("/api/batches")
def batches() -> dict:
    return {
        "mode": llm.mode(),
        "model_label": llm.model_label(),
        "ledger_backend": store.ledger.name,
        "topic_id": getattr(store.ledger, "topic_id", ""),
        "batches": [
            {"batch_id": b, "product": store.products[b]} for b in store.known_batches()
        ],
    }


@app.get("/api/analyze")
def analyze(batch: str) -> StreamingResponse:
    def event_stream() -> Iterator[str]:
        for event in agent.run(batch, store):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/report")
def report(batch: str) -> Response:
    result = agent.analyze(batch, store)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Batch {batch} not found")
    try:
        from . import report as report_mod

        head = getattr(store.ledger, "head", "")
        pdf = report_mod.build_compliance_pdf(result, ledger_head=head)
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="PDF reports require reportlab (pip install reportlab).",
        )
    filename = f"PharmaTrace_{result['batch_id']}_compliance.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/verify")
def verify(batch: str) -> dict:
    """Independently verify the batch's risk fingerprint against Hedera's public
    mirror node. Recomputes the deterministic hash and looks for it on-chain."""
    if not hasattr(store.ledger, "anchor"):
        raise HTTPException(status_code=400, detail="Hedera ledger not active")
    from . import analysis, hedera_ledger

    canon = analysis.canonical_report(batch, store)
    fingerprint = hedera_ledger.canonical_sha256(canon)
    return hedera_ledger.verify_fingerprint(
        store.ledger.topic_id, store.ledger.network, fingerprint
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
