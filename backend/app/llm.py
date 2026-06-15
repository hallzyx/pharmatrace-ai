"""LLM narration layer.

Resolution order (each falls back to the next, so the demo never breaks):
1. Microsoft Foundry project — azure-ai-projects SDK + Entra ID (DefaultAzureCredential)
2. Azure OpenAI — direct endpoint + API key
3. Deterministic templated mock — no blank screen if everything is unreachable
"""

from __future__ import annotations

import os

SYSTEM_PROMPT = (
    "You are PharmaTrace AI, a pharmaceutical compliance agent. "
    "You reason in short steps and cite the evidence. Reply in English, "
    "in 1-2 sentences, with the firm tone of a regulatory risk analyst. "
    "The FINDINGS handed to you by the system are deterministic and already "
    "verified against the immutable ledger: your job is to EXPLAIN them with "
    "confidence, never to question them or say information is missing. "
    "Do not invent new data: rely only on the given finding and evidence."
)


# --- capability detection -----------------------------------------------------

def _foundry_available() -> bool:
    return bool(
        os.getenv("AZURE_AI_PROJECT_ENDPOINT") and os.getenv("AZURE_OPENAI_DEPLOYMENT")
    )


def _azure_available() -> bool:
    return bool(
        os.getenv("AZURE_OPENAI_ENDPOINT")
        and os.getenv("AZURE_OPENAI_API_KEY")
        and os.getenv("AZURE_OPENAI_DEPLOYMENT")
    )


def mode() -> str:
    if _foundry_available():
        return "foundry"
    if _azure_available():
        return "azure-openai"
    return "mock"


def model_label() -> str:
    """Human-friendly label for the active path (shown in the UI badge)."""
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "azure")
    if _foundry_available():
        return f"{deployment} · Foundry"
    if _azure_available():
        return deployment
    return "mock"


# --- narration ----------------------------------------------------------------

_foundry_disabled = False  # set after the first Foundry failure (e.g. no `az login`)


def narrate(instruction: str, evidence: list[str]) -> str:
    """Produce one reasoning sentence for the current step, via the best
    available backend, degrading gracefully."""
    global _foundry_disabled
    if _foundry_available() and not _foundry_disabled:
        try:
            return _foundry_narrate(instruction, evidence)
        except Exception:  # HACK: disable Foundry for the session, fall through
            _foundry_disabled = True  # don't retry slow auth on every step
    if _azure_available():
        try:
            return _azure_narrate(instruction, evidence)
        except Exception:  # HACK: same — fall back to mock
            pass
    return _mock_narrate(instruction, evidence)


def _build_messages(instruction: str, evidence: list[str]) -> list[dict[str, str]]:
    user = instruction
    if evidence:
        user += "\n\nAvailable evidence:\n- " + "\n- ".join(evidence)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def _mock_narrate(instruction: str, evidence: list[str]) -> str:
    if not evidence:
        return instruction
    return f"{instruction} Evidence: " + "; ".join(evidence) + "."


# --- backend 1: Microsoft Foundry project (Entra ID) --------------------------

_foundry_client = None  # cached OpenAI client bound to the Foundry project


def _get_foundry_client():
    global _foundry_client
    if _foundry_client is None:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential

        project = AIProjectClient(
            endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
            credential=DefaultAzureCredential(),
        )
        _foundry_client = project.get_openai_client()
    return _foundry_client


def _foundry_narrate(instruction: str, evidence: list[str]) -> str:
    client = _get_foundry_client()
    resp = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=_build_messages(instruction, evidence),
        temperature=0.3,
        max_tokens=160,
    )
    return resp.choices[0].message.content.strip()


# --- backend 2: Azure OpenAI (API key) ----------------------------------------

def _azure_narrate(instruction: str, evidence: list[str]) -> str:
    from openai import AzureOpenAI

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    )
    resp = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=_build_messages(instruction, evidence),
        temperature=0.3,
        max_tokens=160,
    )
    return resp.choices[0].message.content.strip()
