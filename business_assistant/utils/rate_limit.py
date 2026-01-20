"""Rate limiting utilities for Business Assistant.

Prevents abuse and manages API usage.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
from threading import Lock

from business_assistant.core.config import settings


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self._requests: Dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()
    
    def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if request is allowed.
        
        Returns:
            (is_allowed, remaining_requests)
        """
        if not settings.RATE_LIMIT_ENABLED:
            return True, settings.RATE_LIMIT_REQUESTS
        
        current_time = time.time()
        window_start = current_time - settings.RATE_LIMIT_WINDOW
        
        with self._lock:
            # Clean old requests
            self._requests[identifier] = [
                req_time for req_time in self._requests[identifier]
                if req_time > window_start
            ]
            
            # Check limit
            request_count = len(self._requests[identifier])
            
            if request_count >= settings.RATE_LIMIT_REQUESTS:
                return False, 0
            
            # Add current request
            self._requests[identifier].append(current_time)
            
            remaining = settings.RATE_LIMIT_REQUESTS - request_count - 1
            return True, remaining
    
    def reset(self, identifier: Optional[str] = None) -> None:
        """Reset rate limit for identifier(s)."""
        with self._lock:
            if identifier:
                self._requests.pop(identifier, None)
            else:
                self._requests.clear()


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(identifier: str) -> Tuple[bool, int]:
    """Check rate limit for an identifier."""
    return rate_limiter.is_allowed(identifier)

