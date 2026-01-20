"""Caching utilities for Business Assistant.

Provides in-memory and database-backed caching for LLM responses and expensive operations.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Any, Callable, TypeVar
from functools import wraps

from business_assistant.core.config import settings
from business_assistant.db.schemas import CacheEntry, SessionLocal

T = TypeVar("T")

# In-memory cache (fallback)
_memory_cache: dict[str, tuple[Any, float]] = {}


def _generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments."""
    key_data = {
        "args": str(args),
        "kwargs": sorted(kwargs.items()),
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_string.encode()).hexdigest()


def get_cache(key: str) -> Optional[Any]:
    """Get value from cache (checks database first, then memory)."""
    if not settings.CACHE_ENABLED:
        return None
    
    # Try database cache first
    if settings.DB_TYPE == "sqlite" or settings.DB_TYPE == "postgresql":
        try:
            db = SessionLocal()
            try:
                entry = db.query(CacheEntry).filter(
                    CacheEntry.cache_key == key,
                    CacheEntry.expires_at > datetime.utcnow()
                ).first()
                
                if entry:
                    entry.hit_count += 1
                    db.commit()
                    return json.loads(entry.cache_value)
            finally:
                db.close()
        except Exception:
            pass  # Fall back to memory cache
    
    # Try memory cache
    if key in _memory_cache:
        value, expires_at = _memory_cache[key]
        if expires_at > time.time():
            return value
        else:
            del _memory_cache[key]
    
    return None


def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Set value in cache (stores in database and memory)."""
    if not settings.CACHE_ENABLED:
        return
    
    ttl = ttl or settings.CACHE_TTL
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    value_json = json.dumps(value, default=str)
    
    # Store in database
    if settings.DB_TYPE == "sqlite" or settings.DB_TYPE == "postgresql":
        try:
            db = SessionLocal()
            try:
                # Update or create
                entry = db.query(CacheEntry).filter(CacheEntry.cache_key == key).first()
                if entry:
                    entry.cache_value = value_json
                    entry.expires_at = expires_at
                    entry.hit_count = 0
                else:
                    entry = CacheEntry(
                        cache_key=key,
                        cache_value=value_json,
                        expires_at=expires_at
                    )
                    db.add(entry)
                db.commit()
            finally:
                db.close()
        except Exception:
            pass  # Continue to memory cache
    
    # Store in memory cache
    expires_at_timestamp = time.time() + ttl
    _memory_cache[key] = (value, expires_at_timestamp)
    
    # Clean up old memory cache entries if too large
    if len(_memory_cache) > settings.CACHE_MAX_SIZE:
        _cleanup_memory_cache()


def _cleanup_memory_cache() -> None:
    """Remove expired entries from memory cache."""
    current_time = time.time()
    expired_keys = [
        key for key, (_, expires_at) in _memory_cache.items()
        if expires_at <= current_time
    ]
    for key in expired_keys:
        del _memory_cache[key]


def clear_cache(key: Optional[str] = None) -> None:
    """Clear cache entry(ies)."""
    if key:
        # Clear specific key
        if key in _memory_cache:
            del _memory_cache[key]
        
        # Clear from database
        if settings.DB_TYPE == "sqlite" or settings.DB_TYPE == "postgresql":
            try:
                db = SessionLocal()
                try:
                    db.query(CacheEntry).filter(CacheEntry.cache_key == key).delete()
                    db.commit()
                finally:
                    db.close()
            except Exception:
                pass
    else:
        # Clear all
        _memory_cache.clear()
        
        # Clear database cache
        if settings.DB_TYPE == "sqlite" or settings.DB_TYPE == "postgresql":
            try:
                db = SessionLocal()
                try:
                    db.query(CacheEntry).filter(
                        CacheEntry.expires_at < datetime.utcnow()
                    ).delete()
                    db.commit()
                finally:
                    db.close()
            except Exception:
                pass


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """Decorator to cache function results."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            cache_key = _generate_cache_key(*args, **kwargs)
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"
            
            # Try to get from cache
            cached_value = get_cache(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Compute value
            value = func(*args, **kwargs)
            
            # Store in cache
            set_cache(cache_key, value, ttl)
            
            return value
        return wrapper
    return decorator

