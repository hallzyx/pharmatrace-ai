"""FastAPI app: serves the demo UI and streams the agent's reasoning over SSE."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse

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


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
