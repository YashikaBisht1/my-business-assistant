"""Decision service that combines inputs and produces the structured output.

This module implements the logic that prepares an auditable record and
returns the structured four-part reasoning output. It uses
`business_assistant.ui.processor.build_structured_output` for the core
assembly and logs an audit record to the `logs` directory.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from business_assistant.core.config import settings
from business_assistant.ui.processor import build_structured_output


AUDIT_LOG = Path(settings.LOGS_DIR) / "decision_audit.jsonl"


def _write_audit(record: Dict[str, object]) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def answer_question(
    question: str,
    computed_insights: str,
    policies: List[str],
    past_feedback: Optional[List[Dict[str, object]]] = None,
) -> Dict[str, object]:
    """Prepare the combined inputs, build structured output, and audit.

    Returns a dict with keys:
    - output: the structured output (summary, policy_alignment, recommended_actions, limitations_confidence)
    - audit_record: metadata about inputs and where the audit was stored
    """
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Build structured reasoning output (this uses only provided inputs)
    out = build_structured_output(computed_insights, policies, json.dumps(past_feedback) if past_feedback else None)

    audit = {
        "timestamp": timestamp,
        "question": question,
        "inputs": {
            "computed_insights_present": bool(computed_insights and computed_insights.strip()),
            "policies_count": len(policies or []),
            "past_feedback_count": len(past_feedback or []),
        },
        "output_keys": list(out.keys()),
    }

    _write_audit({"timestamp": timestamp, "audit": audit})

    return {"output": out, "audit_record": audit}
