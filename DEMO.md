# Demo runbook

Everything you need to record or present PharmaTrace AI without surprises.

## Pre-flight checklist

- [ ] `cd backend && python -m uvicorn app.main:app --port 8077` (plain command — **not** `dev.py`)
- [ ] Open http://127.0.0.1:8077 — header badges show `gpt-4.1-mini`, `hedera-hcs · 0.0.xxxx`, `Teams`
- [ ] Teams channel open in another window (so step 5 lands instantly)
- [ ] (Optional) run `python check_hedera.py` and `python check_azure.py` first to confirm connectivity
- [ ] Do one full dry run, including **Verify on-chain**, before recording

## The 90-second script

| # | You click / show | You say |
|---|------------------|---------|
| 1 | The header badges | "Three Microsoft IQ layers plus a public Hedera ledger — all real." |
| 2 | Pick `MX-2026-4471`, click **Analyze batch** | "This is an agent that reasons in steps, streamed live — not a chatbot." |
| 3 | Step 1 appears (cloning) | "Same serial received in Madrid and Guadalajara 15 minutes apart — physically impossible. Cloning." |
| 4 | Step 2 (blacklist) | "Origin supplier on an FDA regulatory blacklist." |
| 5 | Step 3 + route timeline | "Distribution pattern consistent with illicit diversion." |
| 6 | Step 4 — score animates to **94** | "The score is deterministic — computed in code. The AI explains; it doesn't invent the number." |
| 7 | The `⛓ Anchored on Hedera` line | "And the verdict is sealed on Hedera — public, timestamped, writable only by our quality authority." |
| 8 | Switch to Teams | "The quality team is already alerted — in their real Teams." |
| 9 | Click **Download compliance report (PDF)** | "And an audit-ready compliance document, DSCSA/FMD." |
| 10 | Wait ~10s, click **Verify on-chain** → ✔ | "I don't ask you to trust our database. The app re-checks the public Hedera ledger and confirms the verdict wasn't altered. Tamper-proof, end to end." |

## The contrast move (kills "is this hardcoded?")

After the critical batch, analyze a clean one:

- `BR-2026-5500` → **45 / HIGH**, one finding only ("clone, but the supplier is certified").
- `US-2026-1102` → **0 / LOW**, no findings.

"Same agent, different batches, different evidence, different scores."

## Golden lines

- "Risk score is deterministic; the AI explains the findings, it doesn't invent them."
- "Sealed on a public consensus network — immutable, timestamped, and only our account could have written it."
- "If one data point were altered, the fingerprint wouldn't match and it would say TAMPERED."

## Gotchas (read before recording)

### Avoid the reload trap

Use the plain `uvicorn` command, **not** `python dev.py`. On Windows, `--reload`
(which `dev.py` uses) spawns child processes that survive a normal kill. A stale process
can keep serving on the port with an **old Hedera topic** or old code. Symptoms: you
edited `.env` but the app ignores it; Verify finds nothing.

If it happens:
```bash
netstat -ano | grep LISTENING | grep :8077     # find the PID
taskkill //PID <pid> //F //T                    # kill it + children
```
The header badge shows the **active topic id** — glance at it to confirm you're not
talking to a ghost.

### Mirror-node lag on Verify

Right after analyzing, the on-chain record takes **~5–10 seconds** to propagate to
Hedera's public mirror node. If you click **Verify on-chain** immediately it may say
"try again in a few seconds" — that's normal. **Analyze, count to ten, then verify** so
it shows ✔ on the first click.

### Credentials

If a badge shows `mock` (Azure) or the ledger shows `local-hashchain` (Hedera), the
`.env` isn't being read by the running process. See [CONFIGURATION.md](CONFIGURATION.md).

## If the network fails live

The whole app degrades gracefully — but your safest net is the **pre-recorded video**.
Have it ready as a fallback regardless of how solid the live setup looks.
