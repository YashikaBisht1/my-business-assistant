"""Input validation utilities for Business Assistant.

Provides validation for user inputs, file uploads, and data formats.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from business_assistant.core.config import settings
from business_assistant.utils.logging import get_logger

logger = get_logger(__name__)


def validate_insights_json(insights_text: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Validate insights JSON format.
    
    Returns:
        (is_valid, parsed_dict, error_message)
    """
    if not insights_text or not insights_text.strip():
        return False, None, "Insights text is empty"
    
    try:
        parsed = json.loads(insights_text)
        if not isinstance(parsed, dict):
            return False, None, "Insights must be a JSON object"
        
        # Check for expected keys (optional but recommended)
        expected_keys = {"trends", "averages", "anomalies", "comparisons"}
        present_keys = set(k.lower() for k in parsed.keys())
        
        # Warn if expected keys missing but don't fail
        missing = expected_keys - present_keys
        if missing:
            logger.warning(f"Insights missing expected fields: {missing}")
        
        return True, parsed, None
        
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON format: {str(e)}"


def validate_policy_text(policy: str) -> Tuple[bool, Optional[str]]:
    """
    Validate policy text.
    
    Returns:
        (is_valid, error_message)
    """
    if not policy or not policy.strip():
        return False, "Policy text is empty"
    
    if len(policy) < 10:
        return False, "Policy text is too short (minimum 10 characters)"
    
    if len(policy) > 100000:  # 100KB limit
        return False, "Policy text is too long (maximum 100KB)"
    
    return True, None


def validate_question(question: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user question.
    
    Returns:
        (is_valid, error_message)
    """
    if not question or not question.strip():
        return False, "Question is empty"
    
    if len(question) < 5:
        return False, "Question is too short (minimum 5 characters)"
    
    if len(question) > 1000:
        return False, "Question is too long (maximum 1000 characters)"
    
    # Check for potentially malicious content
    suspicious_patterns = [
        r'<script',
        r'javascript:',
        r'onerror=',
        r'onload=',
    ]
    
    question_lower = question.lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, question_lower):
            return False, "Question contains potentially unsafe content"
    
    return True, None


def validate_file_upload(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded file.
    
    Returns:
        (is_valid, error_message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    # Check file size
    file_size = file_path.stat().st_size
    if file_size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        return False, f"File too large: {file_size / (1024*1024):.1f}MB (max: {max_mb}MB)"
    
    if file_size == 0:
        return False, "File is empty"
    
    # Check extension
    ext = file_path.suffix.lower().lstrip(".")
    if ext not in settings.allowed_extensions_list:
        return False, f"File type not allowed: {ext}"
    
    return True, None


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input text.
    
    Args:
        text: Input text to sanitize
        max_length: Optional maximum length
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    # Trim whitespace
    text = text.strip()
    
    # Apply length limit
    if max_length and len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Input truncated to {max_length} characters")
    
    return text


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_user_id(user_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user ID format.
    
    Returns:
        (is_valid, error_message)
    """
    if not user_id or not user_id.strip():
        return False, "User ID is empty"
    
    if len(user_id) > 100:
        return False, "User ID is too long (maximum 100 characters)"
    
    # Allow alphanumeric, underscore, hyphen, dot
    if not re.match(r'^[a-zA-Z0-9_.-]+$', user_id):
        return False, "User ID contains invalid characters"
    
    return True, None

