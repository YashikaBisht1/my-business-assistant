"""Export utilities for reports and analysis outputs.

This module provides functionality to export structured reports
to various formats (PDF, DOCX, JSON, etc.).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from business_assistant.core.config import settings


def export_to_json(output: Dict[str, str], output_path: Optional[Path] = None) -> Path:
    """
    Export structured output to JSON file.
    
    Args:
        output: Dictionary with keys: summary_of_findings, policy_alignment, 
                recommended_actions, limitations_confidence
        output_path: Optional path for output file
    
    Returns:
        Path to the exported file
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(settings.LOGS_DIR) / f"report_{timestamp}.json"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "report": output
    }
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    return output_path


def export_to_markdown(output: Dict[str, str], output_path: Optional[Path] = None) -> Path:
    """
    Export structured output to Markdown file.
    
    Args:
        output: Dictionary with structured output sections
        output_path: Optional path for output file
    
    Returns:
        Path to the exported file
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(settings.LOGS_DIR) / f"report_{timestamp}.md"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    md_content = f"""# Business Decision Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Summary of Findings

{output.get('summary_of_findings', 'N/A')}

---

## Policy Alignment

{output.get('policy_alignment', 'N/A')}

---

## Recommended Actions

{output.get('recommended_actions', 'N/A')}

---

## Limitations / Confidence

{output.get('limitations_confidence', 'N/A')}

---
"""
    
    with output_path.open("w", encoding="utf-8") as f:
        f.write(md_content)
    
    return output_path


def export_to_text(output: Dict[str, str], output_path: Optional[Path] = None) -> Path:
    """
    Export structured output to plain text file.
    
    Args:
        output: Dictionary with structured output sections
        output_path: Optional path for output file
    
    Returns:
        Path to the exported file
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(settings.LOGS_DIR) / f"report_{timestamp}.txt"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    text_content = f"""BUSINESS DECISION REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{'='*60}

SUMMARY OF FINDINGS
{'='*60}

{output.get('summary_of_findings', 'N/A')}

{'='*60}

POLICY ALIGNMENT
{'='*60}

{output.get('policy_alignment', 'N/A')}

{'='*60}

RECOMMENDED ACTIONS
{'='*60}

{output.get('recommended_actions', 'N/A')}

{'='*60}

LIMITATIONS / CONFIDENCE
{'='*60}

{output.get('limitations_confidence', 'N/A')}

{'='*60}
"""
    
    with output_path.open("w", encoding="utf-8") as f:
        f.write(text_content)
    
    return output_path

