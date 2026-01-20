"""Decision service that combines inputs and produces the structured output.

This module implements the logic that prepares an auditable record and
returns the structured four-part reasoning output. It uses
`business_assistant.ui.processor.build_structured_output` for the core
assembly and logs an audit record to database and file system.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from business_assistant.core.config import settings
from business_assistant.ui.processor import build_structured_output
from business_assistant.utils.logging import get_logger, log_performance
from business_assistant.db.schemas import Decision, AuditLog, SessionLocal

logger = get_logger(__name__)

AUDIT_LOG = Path(settings.LOGS_DIR) / "decision_audit.jsonl"


def _write_audit_file(record: Dict[str, object]) -> None:
    """Write audit record to JSONL file (backup)."""
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write audit file: {e}")


def _save_decision_to_db(
    question: str,
    output: Dict[str, str],
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> Optional[int]:
    """Save decision to database. Returns decision ID."""
    try:
        db = SessionLocal()
        try:
            decision = Decision(
                question=question,
                summary_of_findings=output.get("summary_of_findings", ""),
                policy_alignment=output.get("policy_alignment", ""),
                recommended_actions=output.get("recommended_actions", ""),
                limitations_confidence=output.get("limitations_confidence", ""),
                user_id=user_id,
                session_id=session_id,
                extra_metadata=metadata or {},
            )
            db.add(decision)
            db.commit()
            db.refresh(decision)
            return decision.id
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to save decision to database: {e}", exc_info=True)
        return None


def _save_audit_log_to_db(
    decision_id: Optional[int],
    action: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict] = None,
) -> None:
    """Save audit log to database."""
    try:
        db = SessionLocal()
        try:
            audit_log = AuditLog(
                decision_id=decision_id,
                action=action,
                user_id=user_id,
                ip_address=ip_address,
                details=details or {},
            )
            db.add(audit_log)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to save audit log to database: {e}", exc_info=True)


def answer_question(
    question: str,
    computed_insights: str,
    policies: List[str],
    past_feedback: Optional[List[Dict[str, object]]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Dict[str, object]:
    """Prepare the combined inputs, build structured output, and audit.

    Args:
        question: User's question
        computed_insights: JSON string or raw text with insights
        policies: List of policy document strings
        past_feedback: Optional list of feedback dictionaries
        user_id: Optional user identifier
        session_id: Optional session identifier
        ip_address: Optional IP address for audit

    Returns:
        dict with keys:
        - output: the structured output (summary, policy_alignment, recommended_actions, limitations_confidence)
        - audit_record: metadata about inputs and where the audit was stored
        - decision_id: database ID of the saved decision (if saved)
    """
    with log_performance("answer_question", logger):
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Validate inputs
        if not computed_insights or not computed_insights.strip():
            logger.warning("No computed insights provided")
        
        if not policies:
            logger.warning("No policies provided")

        # Build structured reasoning output (this uses only provided inputs)
        try:
            out = build_structured_output(
                computed_insights,
                policies,
                json.dumps(past_feedback) if past_feedback else None
            )
        except Exception as e:
            logger.error(f"Failed to build structured output: {e}", exc_info=True)
            raise

        # Prepare metadata
        metadata = {
            "computed_insights_present": bool(computed_insights and computed_insights.strip()),
            "policies_count": len(policies or []),
            "past_feedback_count": len(past_feedback or []),
            "computed_insights_length": len(computed_insights) if computed_insights else 0,
        }

        # Save to database
        decision_id = _save_decision_to_db(
            question=question,
            output=out,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
        )

        # Create audit record
        audit = {
            "timestamp": timestamp,
            "question": question,
            "decision_id": decision_id,
            "inputs": metadata,
            "output_keys": list(out.keys()),
        }

        # Save audit log to database
        _save_audit_log_to_db(
            decision_id=decision_id,
            action="decision_created",
            user_id=user_id,
            ip_address=ip_address,
            details=audit,
        )

        # Also write to file (backup)
        _write_audit_file({"timestamp": timestamp, "audit": audit})

        return {
            "output": out,
            "audit_record": audit,
            "decision_id": decision_id,
        }
