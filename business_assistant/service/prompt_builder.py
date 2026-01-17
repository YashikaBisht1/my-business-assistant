"""Prompt builder to assemble auditable prompts for the LLM.

This module assembles a reproducible prompt containing:
- an audit header (timestamp, sources)
- the user question
- computed insights (verbatim)
- retrieved policy texts (labelled)
- past feedback (verbatim)
- clear instructions for the LLM to output the required four sections.

The builder does not call any external LLMs; it only returns the prompt
string which can be previewed in the UI or sent to an LLM client.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from business_assistant.core.config import settings


INSTRUCTION_BLOCK = (
    "You are an assistant that must only use the provided information. Do NOT "
    "analyze raw files. Produce output with exactly four sections:"
    "\n1) Summary of Findings\n2) Policy Alignment\n3) Recommended Actions\n4) Limitations / Confidence\n"
    "If information is missing, explicitly state what is missing. Keep answers concise and auditable."
)


def build_prompt(
    question: str,
    computed_insights: str,
    policies: Optional[List[str]] = None,
    past_feedback: Optional[str] = None,
    max_policy_chars: int = 8000,
) -> str:
    """Assemble a full prompt string.

    - policies: list of policy document strings; each will be labelled.
    - max_policy_chars: if total policy text exceeds this limit, policies will be truncated
      with a notice to the LLM.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"

    header = f"AUDIT: timestamp={timestamp} | source=business_assistant | base_dir={settings.BASE_DIR}\n"

    parts: List[str] = [header, "QUESTION:", question, "\nCOMPUTED_INSIGHTS:", computed_insights or "(none provided)"]

    # Policies
    policy_text = ""
    if policies:
        labelled = []
        for i, p in enumerate(policies, start=1):
            labelled.append(f"Policy {i}:\n{p}")
        policy_text = "\n\n".join(labelled)

    if policy_text:
        if len(policy_text) > max_policy_chars:
            policy_text = policy_text[: max_policy_chars - 200] + "\n...[truncated due to length]..."
            policy_text += "\n(Full policies were truncated in the prompt; rely on retrieval to fetch full text when executing.)"
        parts.extend(["\nPOLICIES:", policy_text])
    else:
        parts.extend(["\nPOLICIES:", "(none provided)"])

    # Feedback
    parts.extend(["\nPAST_FEEDBACK:", past_feedback or "(none provided)"])

    # Instructions
    parts.extend(["\nINSTRUCTIONS:", INSTRUCTION_BLOCK])

    return "\n\n".join(parts)
