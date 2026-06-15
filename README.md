# 🧬 PharmaTrace AI

**Drug Traceability & Counterfeit Risk Agent**
_"From batch to patient. Every step verified. Every anomaly caught."_

A multi-step **reasoning agent** that detects counterfeit pharmaceuticals before they
reach the patient. It reasons step-by-step over supply-chain data, cross-checks every
batch against a tamper-proof audit ledger, scores the counterfeit risk, **anchors the
verdict on a public Hedera ledger**, alerts the quality team on Teams, and produces an
audit-ready compliance PDF (DSCSA / FMD).

> Each year **over 1 million people die** from falsified or substandard medicines.
> PharmaTrace AI turns a fragmented, manual traceability process into a real-time,
> reasoning-driven defense.

---

## Documentation

| Doc | Read it for |
|-----|-------------|
| **README.md** (this file) | What it is, quick start, feature overview |
| [ARCHITECTURE.md](ARCHITECTURE.md) | How it works: layers, data flow, the verification design |
| [DEMO.md](DEMO.md) | Demo runbook: the script, talking points, gotchas |
| [CONFIGURATION.md](CONFIGURATION.md) | Wiring real Azure GPT-4o, Teams, and Hedera credentials |

---

## Quick start (2 minutes, zero config)

Requires **Python 3.10+**. No API keys needed — it ships with a demo-safe mock mode.

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --port 8077
```

Open **http://127.0.0.1:8077**, pick batch **`MX-2026-4471`**, click **Analyze batch**.

You'll watch the agent reason through 5 streamed steps and land on **Risk score
94/100 — CRITICAL**, with a Teams alert, an audit PDF, and an on-chain anchor.

> For development you can use `python dev.py` (auto-reload). For demos use the plain
> `uvicorn` command above — see [DEMO.md](DEMO.md#avoid-the-reload-trap) for why.

---

## What it does (5 streamed reasoning steps)

| Step | Reasoning | Layer |
|------|-----------|-------|
| 1. **Verify authenticity** | Cross-checks serial + lot against the immutable ledger; detects the same unit "received" in two distant places at once (cloning) | Fabric IQ — data |
| 2. **Analyze origin supplier** | Checks FDA/EMA certification and regulatory blacklists | Foundry IQ — agent |
| 3. **Evaluate distribution pattern** | Flags rapid hand-offs and impossible geographic routes | Foundry IQ — agent |
| 4. **Generate risk report** | Deterministic risk score + actions + **PDF** + **anchors the verdict on Hedera HCS** | Foundry IQ + Hedera |
| 5. **Alert stakeholders** | Pushes an Adaptive Card alert to the Teams quality channel | Work IQ — M365 |

Then **Verify on-chain**: one click recomputes the verdict's fingerprint and confirms
it against Hedera's public mirror node — independent, cryptographic proof it wasn't altered.

The reasoning is **streamed live**, step by step, with cited evidence — this is an
agent, not a chatbot.

---

## See the agent discriminate (the score is reasoned, not fixed)

| Batch | Anomalies | Risk |
|-------|-----------|------|
| `MX-2026-4471` | clone + blacklisted supplier + illicit route | **94 — CRITICAL** |
| `NG-2026-7788` | clone + blacklisted supplier | **80 — CRITICAL** |
| `BR-2026-5500` | clone only (certified supplier) | **45 — HIGH** |
| `IN-2026-3030` | grey-market supplier + intercontinental route | **28 — MODERATE** |
| `US-2026-1102`, `EU-2026-8830` | none | **0 — LOW** |

Same agent, different batches, different evidence → different scores. Nothing hardcoded.

---

## Feature status

| Capability | Status | Notes |
|------------|--------|-------|
| Multi-step reasoning agent (streamed) | ✅ | Runs on a **Microsoft Foundry project** (azure-ai-projects SDK + Entra ID) ▸ Azure OpenAI key ▸ mock |
| Deterministic risk scoring | ✅ | Computed in code — reproducible, defensible |
| Tamper-evident audit ledger | ✅ | Hash-chained; Hedera HCS backend when configured |
| Hedera HCS anchoring + access control | ✅ | `submit_key` restricts writes to your account |
| On-chain verification (mirror node) | ✅ | Independent cryptographic re-check |
| Teams alerts (Work IQ) | ✅ | Live Adaptive Card ▸ simulated fallback |
| Audit-ready compliance PDF | ✅ | DSCSA / FMD framing, integrity hash |

Every integration **degrades gracefully** — missing credentials never break the demo.

---

## Tech stack

`Python` · `FastAPI` · `Server-Sent Events` · `Azure OpenAI (GPT-4o)` ·
`Teams Adaptive Cards (Work IQ)` · `Hedera Consensus Service (hiero-sdk-python)` ·
`Hash-chained audit ledger` · `reportlab (PDF)`

---

## Disclaimer

Demonstration prototype built for a hackathon. **All companies, suppliers, batches,
serial numbers and distribution routes are fictional**; any resemblance to real entities
is coincidental. Drug names refer to **generic active ingredients (INN)**, which are not
trademarks. Third-party brand names are the property of their respective owners and imply
no affiliation. Nothing here is a real regulatory determination about any real product or company.

---

## Post-hackathon roadmap

- Back the dataset with a real **Microsoft Fabric** lakehouse (today: seeded JSON).
- Persist the ledger and add GS1 serialized-barcode ingestion.
- Encrypt anchored payloads for confidential read access.
- Replace the single-page UI with the planned **Next.js / TypeScript** frontend.
- Cryptographically sign the PDF compliance report for regulatory submission.
