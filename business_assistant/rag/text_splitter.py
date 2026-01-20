"""Text splitting utilities for policy documents.

This module provides text chunking functionality to split large policy
documents into smaller chunks suitable for vector store embedding.
"""
from __future__ import annotations

from typing import List
from business_assistant.core.config import settings


def split_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
    """
    Split text into chunks with overlap.
    
    Args:
        text: The text to split
        chunk_size: Maximum characters per chunk (defaults to config)
        chunk_overlap: Overlap between chunks (defaults to config)
    
    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = settings.CHUNK_OVERLAP
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                last_punct = text.rfind(punct, start, end)
                if last_punct != -1:
                    end = last_punct + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start forward, accounting for overlap
        start = end - chunk_overlap
        if start >= len(text):
            break
    
    return chunks if chunks else [text]

