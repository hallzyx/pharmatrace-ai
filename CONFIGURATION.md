# Configuration

Wiring the real integrations. **All are optional** — without them the app runs in a
demo-safe mode (mock narration, local ledger, simulated alerts).

## Quick path

1. Copy the template: `cp backend/env.example backend/.env`
2. Fill in only what you have (sections below).
3. Verify each with its check script: `python check_azure.py`, `python check_teams.py`, `python check_hedera.py`
4. Restart the server. The header badges reflect what's active.

> `.env` lives at `backend/.env` and is git-ignored. The app loads it automatically
> (`app/__init__.py`). A value set in your real OS environment overrides `.env`.

---

## Foundry IQ — the reasoning model

Two ways to provide the model. The app prefers **Foundry project (Entra ID)** and falls
back to the **Azure OpenAI key** if the project endpoint is absent or unreachable.

### Preferred — Microsoft Foundry project (Entra ID)

```ini
AZURE_AI_PROJECT_ENDPOINT=https://YOUR-RESOURCE.services.ai.azure.com/api/projects/YOUR-PROJECT
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

This uses the `azure-ai-projects` SDK with `DefaultAzureCredential` — **no API key**.
You must be signed in: `az login` (the running process inherits that session). Your
account needs an **Azure AI User / Developer** role on the project.

The project endpoint is the `…services.ai.azure.com/api/projects/<project>` URL — find it
on the Foundry project **Overview** page, or via:
`az cognitiveservices account show --name <resource> --query properties.endpoints`.

When active, the UI badge reads `gpt-4.1-mini · Foundry`.

### Fallback — Azure OpenAI key

```ini
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

> ⚠️ **Most common error.** `DeploymentNotFound (404)` means `AZURE_OPENAI_DEPLOYMENT`
> is wrong. The *project* and the *model deployment* are different things in Foundry.
> Open **Deployments / Models + endpoints** and copy the deployment's exact name
> (e.g. `gpt-4o`, `gpt-4.1-mini`). If there's no deployment yet, deploy a model first.

Verify: `python check_azure.py` → expects `[OK] GPT-4o response:`.

---

## Work IQ — Microsoft Teams

```ini
TEAMS_WEBHOOK_URL=https://prod-XX.logic.azure.com:443/workflows/...
```

To get the URL:

1. In Teams, open the target channel → **…** → **Workflows**.
2. Use the template **"Post webhook alerts to a channel"** (Power Automate).
3. Pick the team + channel, finish, and copy the generated URL.

> ⚠️ The classic **Office 365 Connectors** were retired in 2025 — use the **Workflows /
> Power Automate** template, not the old "Incoming Webhook" connector.

Verify: `python check_teams.py` → posts a test Adaptive Card; check the channel. If the
POST is accepted but no card appears, the payload shape needs to match your template —
adjust `app/notify.py`.

---

## Hedera Consensus Service

```ini
HEDERA_ACCOUNT_ID=0.0.xxxx
HEDERA_PRIVATE_KEY=your-private-key
HEDERA_NETWORK=testnet
HEDERA_TOPIC_ID=            # leave blank on first run; pin it after
```

1. Get a free testnet account at **https://portal.hedera.com** (gives Account ID + key).
2. Run `python check_hedera.py`. It connects, **creates a topic** whose `submit_key` is
   your account (write-access control), anchors a test record, and prints the **Topic ID**
   + a HashScan link.
3. **Pin that Topic ID** as `HEDERA_TOPIC_ID` in `.env` so the app reuses it instead of
   creating a new topic every startup.
4. Restart the server. Badge shows `hedera-hcs · 0.0.xxxx`; analyses anchor automatically.

> ⚠️ If you change `HEDERA_TOPIC_ID` but the app keeps using the old one, a **stale
> server process** is still running (see [DEMO.md](DEMO.md#avoid-the-reload-trap)). The
> badge shows the topic the running process actually uses.

Verify on-chain from the UI after an analysis — see [ARCHITECTURE.md](ARCHITECTURE.md#on-chain-verification-the-important-part).

---

## What each badge means

| Badge | Active | Fallback |
|-------|--------|----------|
| `model · Foundry` | Foundry project (Entra ID) | `model` alone = key fallback; `mock` = templated |
| `hedera-hcs · 0.0.xxxx` | Hedera anchoring on | `local-hashchain` = local ledger only |
| `Teams` | (always shown) | alert is simulated unless webhook set |

---

## Dependencies

`requirements.txt` pins everything. Optional extras and what they enable:

| Package | Enables | Without it |
|---------|---------|-----------|
| `azure-ai-projects` + `azure-identity` | Foundry project narration (Entra ID) | falls back to key |
| `openai` | Azure OpenAI key narration | mock narration |
| `hiero-sdk-python` | Hedera anchoring + verify | local ledger |
| `reportlab` | Compliance PDF | `/api/report` returns 503 |
