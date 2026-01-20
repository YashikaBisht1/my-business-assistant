"""Feedback storage utilities.

Stores feedback in database and JSON Lines file for backup.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from business_assistant.core.config import settings
from business_assistant.db.schemas import Feedback, SessionLocal
from business_assistant.utils.logging import get_logger

logger = get_logger(__name__)

FEEDBACK_LOG = Path(settings.LOGS_DIR) / "feedback.jsonl"


def save_feedback(
    feedback: Dict[str, object],
    decision_id: Optional[int] = None,
    user_id: Optional[str] = None,
) -> Optional[int]:
    """Save feedback record to database and file.

    Args:
        feedback: Feedback dictionary (should contain rating, comment, is_helpful, etc.)
        decision_id: Optional ID of related decision
        user_id: Optional user identifier

    Returns:
        Feedback ID if saved successfully, None otherwise
    """
    timestamp = datetime.utcnow()
    
    # Extract common feedback fields
    rating = feedback.get("rating")
    comment = feedback.get("comment")
    is_helpful = feedback.get("is_helpful")
    metadata = {k: v for k, v in feedback.items() if k not in ["rating", "comment", "is_helpful"]}

    # Save to database
    feedback_id = None
    try:
        db = SessionLocal()
        try:
            feedback_record = Feedback(
                decision_id=decision_id,
                user_id=user_id,
                rating=rating,
                comment=comment,
                is_helpful=is_helpful,
                metadata=metadata,
            )
            db.add(feedback_record)
            db.commit()
            db.refresh(feedback_record)
            feedback_id = feedback_record.id
            logger.info(f"Saved feedback {feedback_id} to database")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to save feedback to database: {e}", exc_info=True)

    # Also save to file (backup)
    try:
        FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": timestamp.isoformat() + "Z",
            "feedback_id": feedback_id,
            "decision_id": decision_id,
            "user_id": user_id,
            "feedback": feedback,
        }
        with FEEDBACK_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write feedback file: {e}")

    return feedback_id


def get_feedback_for_decision(decision_id: int) -> list[Dict]:
    """Get all feedback for a specific decision."""
    try:
        db = SessionLocal()
        try:
            feedbacks = db.query(Feedback).filter(
                Feedback.decision_id == decision_id
            ).order_by(Feedback.timestamp.desc()).all()
            return [f.to_dict() for f in feedbacks]
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to get feedback: {e}", exc_info=True)
        return []
