"""Initialize the database with tables.

Run this script to create all database tables before first use.

Usage:
    python -m scripts.init_database
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from business_assistant.db import init_db
from business_assistant.core.config import settings
from business_assistant.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


def main():
    """Initialize database tables."""
    setup_logging()
    
    logger.info("Initializing database...")
    logger.info(f"Database type: {settings.DB_TYPE}")
    logger.info(f"Database path: {settings.DB_PATH}")
    
    try:
        init_db()
        logger.info("✓ Database initialized successfully!")
        logger.info(f"  Tables created in: {settings.DB_PATH}")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

