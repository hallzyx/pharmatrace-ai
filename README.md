# 🧬 PharmaTrace AI

**Drug Traceability & Counterfeit Risk Agent**
_"From batch to patient. Every step verified. Every anomaly caught."_

A multi-step **reasoning agent** that detects counterfeit pharmaceuticals before
they reach the patient. It reasons step-by-step over supply-chain data, cross-checks
every batch against a tamper-proof audit ledger, scores the counterfeit risk, and
alerts the quality team — producing an audit-ready compliance trail (DSCSA / FMD).

> Each year **over 1 million people die** from falsified or substandard medicines.
> PharmaTrace AI turns a fragmented, manual traceability process into a real-time,
> reasoning-driven defense.

---

## What it does (the agent's 5 reasoning steps)

| Step | Reasoning | Microsoft IQ layer |
|------|-----------|--------------------|
| 1. **Verify authenticity** | Cross-checks serial + lot against the immutable ledger; detects the same unit "received" in two distant places at once (cloning) | Fabric IQ (data) |
| 2. **Analyze origin supplier** | Checks FDA/EMA certification and regulatory blacklists | Foundry IQ (agent) |
| 3. **Evaluate distribution pattern** | Flags rapid hand-offs and impossible geographic routes | Foundry IQ (agent) |
| 4. **Generate risk report** | Deterministic risk score + recommended actions + downloadable **audit-ready PDF** (DSCSA/FMD) | Foundry IQ (agent) |
| 5. **Alert stakeholders** | Pushes an Adaptive Card alert to the Teams quality channel | Work IQ (M365) |

The reasoning is **streamed live** to the UI, step by step, with cited evidence —
this is an agent, not a chatbot.

---

## Run it locally (2 minutes, zero config)

Requires **Python 3.10+**. No API keys needed — it ships with a demo-safe mock mode.

```bash
cd backend
python -m pip install -r requirements.txt
python dev.py            # or: python -m uvicorn app.main:app --port 8077
```

Open **http://127.0.0.1:8077**, pick batch **`MX-2026-4471`**, click **Analizar lote**.

You'll see the agent reason through 5 steps and land on **Risk score 94/100 — CRÍTICO**,
with a live Teams alert (simulated) and an audit-ready action list.

**Try other batches to see the agent discriminate** (the score is reasoned, not fixed):

| Batch | Anomalies | Risk |
|-------|-----------|------|
| `MX-2026-4471` | clone + blacklisted supplier + illicit route | **94 — CRÍTICO** |
| `NG-2026-7788` | clone + blacklisted supplier | **80 — CRÍTICO** |
| `BR-2026-5500` | clone only (certified supplier) | **45 — ALTO** |
| `IN-2026-3030` | grey-market supplier + intercontinental route | **28 — MODERADO** |
| `US-2026-1102`, `EU-2026-8830` | none | **0 — BAJO** |

---

## Architecture

```
Browser (SSE stream)  ──►  FastAPI  ──►  Reasoning Agent
                                          ├─ Ledger backend (interface)
                                          │    • LocalHashChainLedger  ← default, tamper-evident
                                          │    • Hedera HCS            ← drop-in (stretch)
                                          ├─ Deterministic analysis (risk score is code, not LLM)
                                          ├─ LLM narration (Azure GPT-4o ▸ mock fallback)
                                          └─ Teams Adaptive Card alert (Work IQ)
```

**Design decisions for the hackathon:**
- **Risk score is computed in code**, not by the LLM → reproducible, defensible demo.
  The LLM *narrates and explains* the findings; it never invents them.
- **Everything degrades gracefully.** No Azure key → mock narration. No Teams webhook
  → simulated alert. The demo never shows a blank screen.
- **The ledger is behind an interface.** Today: a hash-chained ledger (each record
  commits to the previous record's hash — editing any past record breaks the chain).
  Stretch: Hedera Consensus Service for public, distributed tamper-proofing.

---

## Optional integrations

Copy `backend/env.example` to `backend/.env` and fill in what you have:

- **Foundry IQ — Azure OpenAI / GPT-4o**: set `AZURE_OPENAI_*` for real LLM reasoning narration.
- **Work IQ — Teams**: set `TEAMS_WEBHOOK_URL` to post live Adaptive Card alerts.
- **Hedera (stretch)**: `HEDERA_*` for public-ledger anchoring.

The header badges in the UI show which mode is active (`GPT-4o` vs `mock`, ledger backend).

---

## Tech stack

`Python` · `FastAPI` · `Server-Sent Events` · `Azure OpenAI (GPT-4o)` ·
`Microsoft Fabric (data model)` · `Teams Adaptive Cards (Work IQ)` ·
`Hash-chained audit ledger` (Hedera HCS-ready)

---

## Known issues / shortcuts (hackathon honesty)

- **Mock mode by default** — LLM narration is templated unless Azure credentials are set.
- **Dataset is fictional but realistic** — seeded from `backend/data/*.json`, not a live Fabric lakehouse.
- **Ledger is in-memory** — re-seeded on each server start; hash-chaining is real, persistence is not.
- **Teams alert is simulated** unless `TEAMS_WEBHOOK_URL` is configured.

## Disclaimer

This is a demonstration prototype built for a hackathon. **All companies, suppliers,
batches, serial numbers and distribution routes in this project are fictional** and were
created solely to illustrate the system; any resemblance to real entities is coincidental.
Drug names refer to **generic active ingredients (INN)**, which are not trademarks. Any
third-party brand names are the property of their respective owners and imply no affiliation.
Nothing here constitutes a real regulatory determination about any real product or company.

## Post-hackathon roadmap

- Swap the local ledger for **Hedera HCS** (interface already in place: `app/ledger.py`).
- Back the dataset with a real **Microsoft Fabric** lakehouse.
- Replace the single-page UI with the planned **Next.js / TypeScript** frontend.
- Persist the ledger and add GS1 serialized-barcode ingestion.
- Cryptographically sign the PDF compliance report for regulatory submission.
