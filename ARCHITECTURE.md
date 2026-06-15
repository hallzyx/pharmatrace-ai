# Architecture

How PharmaTrace AI is built, and the design decisions behind it.

## At a glance

```
Browser (single page)
   │  GET /                → UI
   │  GET /api/batches     → mode, model, ledger backend, active topic
   │  GET /api/analyze     → SSE stream of reasoning steps
   │  GET /api/report      → compliance PDF
   │  GET /api/verify      → on-chain verification result
   ▼
FastAPI (app/main.py)
   ▼
Reasoning Agent (app/agent.py)  ── streams 5 steps ──►
   ├─ Deterministic analysis ....... app/analysis.py   (risk score = code, not LLM)
   ├─ LLM narration ................ app/llm.py        (Foundry SDK ▸ Azure key ▸ mock)
   ├─ Audit ledger ................. app/ledger.py / app/hedera_ledger.py
   ├─ Teams alert (Work IQ) ........ app/notify.py     (webhook ▸ simulated fallback)
   └─ Compliance PDF ............... app/report.py
```

## The three Microsoft IQ layers

| Layer | Role | Where |
|-------|------|-------|
| **Fabric IQ** | Data: batches, suppliers, ledger events | `app/data.py`, `data/*.json` (lakehouse-shaped) |
| **Foundry IQ** | The reasoning agent. The model runs on a **Microsoft Foundry project**, reached via the `azure-ai-projects` SDK with **Entra ID** auth (`DefaultAzureCredential`); falls back to a direct Azure OpenAI key, then mock. | `app/agent.py`, `app/llm.py` |
| **Work IQ** | Teams Adaptive Card alerts | `app/notify.py` |

Plus **Hedera Consensus Service** as a public, tamper-proof anchor for every verdict.

## Request flow (an analysis)

1. The browser opens an **SSE** connection to `/api/analyze?batch=…`.
2. `agent.run()` is a generator. For each of the 5 steps it: runs a deterministic
   check, asks the LLM to *explain* the finding, and `yield`s an event.
3. FastAPI streams each event as `data: {…}\n\n`; the UI renders it live.
4. At step 4 the agent builds the report, **anchors its fingerprint on Hedera**, and
   attaches the anchor proof.
5. At step 5 it posts the Teams alert.

## Key design decisions

| Decision | Why |
|----------|-----|
| **Risk score computed in code, not by the LLM** | Reproducible and defensible. The LLM *explains* findings; it never invents the number. A judge can re-run and always get 94/100. |
| **LLM explains confirmed findings, never re-derives them** | Early versions made GPT hedge ("I can't confirm…"). We hand it the verified finding and tell it to state it firmly. |
| **Everything degrades gracefully** | No Azure key → templated narration. No Teams webhook → simulated alert. No Hedera creds → local ledger. The demo never shows a blank screen. |
| **Ledger behind an interface** | `LedgerBackend` lets `LocalHashChainLedger` and `HederaLedger` swap with zero agent changes. |

## The audit ledger

`app/ledger.py` defines `LedgerBackend` and `LocalHashChainLedger`: each record commits
to the previous record's hash (`sha256(prev_hash + payload)`). Editing any past record
breaks every hash after it — that is the tamper-evidence. `verify_integrity()` walks the
chain to confirm it.

`HederaLedger` (`app/hedera_ledger.py`) **extends** the local ledger (so reads stay fast
and local) and **adds** public anchoring on Hedera Consensus Service.

### Access control (write = your account only)

The HCS topic is created with `submit_key = operator.public_key()`. Only the account
holding that key can write records. Reads stay public via mirror nodes — that is what
makes the immutability independently verifiable. (Confidential payloads would require
encryption; out of scope here — we anchor only a hash + reference, never sensitive data.)

## On-chain verification (the important part)

The challenge: a report contains the LLM's narrative, which differs every run. Hashing
the whole report would never reproduce. So:

1. **Anchor a deterministic fingerprint, not the prose.** `analysis.canonical_report()`
   returns only the reproducible facts — `batch_id`, `risk_score`, `risk_band`,
   `findings` (severity/points/title/detail), `recommended_actions`. The LLM
   `explanation` is **excluded**.
2. **One shared hash function.** `hedera_ledger.canonical_sha256()` is used both when
   anchoring and when verifying, so serialization is identical.
3. **Independent re-check.** `/api/verify` recomputes the fingerprint and queries
   Hedera's **public mirror node** REST API directly (no SDK, no auth) for a matching
   record. Anyone can reproduce this — it does not trust our database.

```
anchor:  canonical_report ─► sha256 ─► HCS topic message
verify:  canonical_report ─► sha256 ─► search mirror node ─► ✔ match / ✗ tampered
```

If a single deterministic field were altered, the fingerprint would differ and
verification would fail. That is end-to-end cryptographic integrity.

## File map

| File | Responsibility |
|------|----------------|
| `app/main.py` | FastAPI app, routes, SSE streaming |
| `app/agent.py` | The 5-step reasoning orchestrator (generator) |
| `app/analysis.py` | Deterministic anomaly detection, scoring, canonical fingerprint |
| `app/llm.py` | Azure OpenAI narration with mock fallback |
| `app/ledger.py` | `LedgerBackend` interface + local hash-chained ledger |
| `app/hedera_ledger.py` | Hedera HCS backend: anchoring, access control, mirror-node verify |
| `app/notify.py` | Teams Adaptive Card alerts (Work IQ) |
| `app/report.py` | Audit-ready compliance PDF (reportlab) |
| `app/data.py` | Loads the dataset, selects + seeds the ledger backend |
| `data/*.json` | Fictional batches and suppliers (lakehouse-shaped) |
| `static/index.html` | Single-page streaming UI |
| `check_*.py` | Pre-demo connectivity checks (Azure / Teams / Hedera) |

## Graceful degradation matrix

| Missing | Effect | Demo still works? |
|---------|--------|-------------------|
| Azure creds | Templated narration instead of GPT-4o | ✅ |
| Teams webhook | Simulated alert | ✅ |
| Hedera creds | Local hash-chained ledger; no anchor/verify | ✅ |
| reportlab | `/api/report` returns 503; rest unaffected | ✅ |
