"""Utilities for parsing uploaded files from the Gradio UI.

Currently supports:
- .json files (first .json is used as computed insights)
- .txt files (each becomes a policy document)

This module avoids heavy external dependencies so the UI remains lightweight.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_json_file(path: Path) -> str:
    # Return the raw JSON text so the processor can parse and validate it.
    return path.read_text(encoding="utf-8")


def parse_uploaded_files(paths: List[str]) -> Tuple[Optional[str], List[str]]:
    """Parse uploaded file paths and return (insights_text, policies).

    - insights_text: string or None. If multiple JSON files are present, the first is used.
    - policies: list of policy document strings (from .txt files).
    """
    if not paths:
        return None, []

    insights_text: Optional[str] = None
    policies: List[str] = []

    for p in paths:
        try:
            path = Path(p)
            if not path.exists():
                continue

            suffix = path.suffix.lower()
            if suffix == ".json" and insights_text is None:
                insights_text = _read_json_file(path)
            elif suffix == ".txt":
                policies.append(_read_text_file(path))
            else:
                # skip other file types for now
                continue
        except Exception:
            # Ignore individual file errors; caller will detect missing data
            continue

    return insights_text, policies
