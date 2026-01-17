"""Feedback storage utilities.

Stores feedback as JSON Lines in the configured feedback directory.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from business_assistant.core.config import settings


def save_feedback(feedback: Dict[str, object]) -> None:
    """Append a feedback record (JSON) to the feedback log file.

    The feedback dict should be JSON-serializable.
    """
    # Use a feedback file under the configured logs directory
    p = Path(settings.LOGS_DIR) / "feedback.jsonl"
    Path(settings.LOGS_DIR).mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "feedback": feedback,
    }
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
