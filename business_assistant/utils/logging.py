"""Logging utilities for Business Assistant.

Provides structured logging with context and performance tracking.
"""
from __future__ import annotations

import logging
import time
import functools
from contextlib import contextmanager
from typing import Optional, Dict, Any
from pathlib import Path

from business_assistant.core.config import settings


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
    return logger


def log_function_call(logger: Optional[logging.Logger] = None):
    """Decorator to log function calls with timing."""
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"Calling {func.__name__} with args={len(args)}, kwargs={list(kwargs.keys())}")
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


@contextmanager
def log_performance(operation: str, logger: Optional[logging.Logger] = None):
    """Context manager to log operation performance."""
    if logger is None:
        logger = get_logger(__name__)
    
    start_time = time.time()
    logger.info(f"Starting {operation}")
    try:
        yield
        elapsed = time.time() - start_time
        logger.info(f"Completed {operation} in {elapsed:.2f}s")
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"{operation} failed after {elapsed:.2f}s: {e}", exc_info=True)
        raise


def log_decision(
    logger: logging.Logger,
    decision_id: Optional[int],
    action: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Log a decision-related event."""
    log_data = {
        "decision_id": decision_id,
        "action": action,
        "details": details or {},
    }
    logger.info(f"Decision event: {log_data}")


def setup_logging() -> None:
    """Set up logging configuration."""
    # Ensure log directory exists
    log_dir = Path(settings.LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(
        settings.LOG_FILE,
        encoding="utf-8",
        mode="a"
    )
    file_handler.setLevel(logging.DEBUG if settings.ENABLE_DEBUG else logging.INFO)
    file_formatter = logging.Formatter(settings.LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_level = logging.DEBUG if settings.ENABLE_DEBUG else logging.INFO
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(settings.LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

