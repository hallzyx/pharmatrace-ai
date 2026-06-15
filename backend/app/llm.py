"""LLM narration layer.

Uses Azure OpenAI (GPT-4o) when credentials are present, otherwise falls back
to deterministic templated narration so the demo always runs — no blank screen
if the API is unreachable during judging.
"""

from __future__ import annotations

import os

SYSTEM_PROMPT = (
    "Eres PharmaTrace AI, un agente de cumplimiento farmacéutico. "
    "Razonas en pasos cortos y citas la evidencia. Responde en español, "
    "en 1-2 frases, con tono firme de analista de riesgo regulatorio. "
    "Los HALLAZGOS que te entrega el sistema son determinísticos y ya están "
    "verificados contra el ledger inmutable: tu trabajo es EXPLICARLOS con "
    "seguridad, nunca cuestionarlos ni decir que falta información. "
    "No inventes datos nuevos: apóyate sólo en el hallazgo y la evidencia dados."
)


def _azure_available() -> bool:
    return bool(
        os.getenv("AZURE_OPENAI_ENDPOINT")
        and os.getenv("AZURE_OPENAI_API_KEY")
        and os.getenv("AZURE_OPENAI_DEPLOYMENT")
    )


def mode() -> str:
    return "azure-gpt4o" if _azure_available() else "mock"


def model_label() -> str:
    """Human-friendly label for the active model (shown in the UI badge)."""
    if _azure_available():
        return os.getenv("AZURE_OPENAI_DEPLOYMENT", "azure")
    return "mock"


def narrate(instruction: str, evidence: list[str]) -> str:
    """Produce one reasoning sentence for the current step."""
    if not _azure_available():
        return _mock_narrate(instruction, evidence)
    try:
        return _azure_narrate(instruction, evidence)
    except Exception:  # HACK: never let LLM errors break the live demo
        return _mock_narrate(instruction, evidence)


def _mock_narrate(instruction: str, evidence: list[str]) -> str:
    if not evidence:
        return instruction
    return f"{instruction} Evidencia: " + "; ".join(evidence) + "."


def _azure_narrate(instruction: str, evidence: list[str]) -> str:
    from openai import AzureOpenAI

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
    )
    user = instruction
    if evidence:
        user += "\n\nEvidencia disponible:\n- " + "\n- ".join(evidence)
    resp = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=160,
    )
    return resp.choices[0].message.content.strip()
