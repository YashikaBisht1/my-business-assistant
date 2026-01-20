"""Initialize the vector store with policy documents.

This script loads policy documents from the data/sample directory (or specified path)
and adds them to the ChromaDB vector store for RAG retrieval.

Usage:
    python -m scripts.init_vector_store [--policy-dir PATH] [--clear]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from business_assistant.data.document_loader import load_policy_document
from business_assistant.rag.vector_store import PolicyVectorStore
from business_assistant.rag.text_splitter import split_text
from business_assistant.core.config import settings


def load_policies_from_directory(policy_dir: Path) -> list[str]:
    """Load all policy documents from a directory."""
    policy_texts = []
    
    # Supported extensions
    extensions = {'.txt', '.pdf', '.json'}
    
    for file_path in policy_dir.rglob('*'):
        if file_path.suffix.lower() in extensions:
            try:
                print(f"Loading policy: {file_path.name}...", flush=True)
                text = load_policy_document(file_path)
                if text.strip():
                    policy_texts.append(text)
                    print(f"  [OK] Loaded {len(text)} characters", flush=True)
            except Exception as e:
                print(f"  [ERROR] Error loading {file_path.name}: {e}", flush=True)
    
    return policy_texts


def initialize_vector_store(policy_dir: Path = None, clear_existing: bool = False) -> None:
    """
    Initialize the vector store with policy documents.
    
    Args:
        policy_dir: Directory containing policy files (defaults to data/sample)
        clear_existing: If True, clear existing vector store first
    """
    if policy_dir is None:
        policy_dir = Path(settings.BASE_DIR) / "data" / "sample"
    
    policy_dir = Path(policy_dir)
    
    if not policy_dir.exists():
        print(f"Error: Policy directory not found: {policy_dir}", flush=True)
        return
    
    print(f"Initializing vector store from: {policy_dir}", flush=True)
    print(f"Vector store path: {settings.VECTOR_STORE_PATH}", flush=True)
    
    # Load policy documents
    policy_texts = load_policies_from_directory(policy_dir)
    
    if not policy_texts:
        print("No policy documents found!", flush=True)
        return
    
    # Split into chunks
    print("\nChunking policy documents...", flush=True)
    chunks = []
    for text in policy_texts:
        text_chunks = split_text(text)
        chunks.extend(text_chunks)
        print(f"  Split into {len(text_chunks)} chunks", flush=True)
    
    print(f"\nTotal chunks to add: {len(chunks)}", flush=True)
    
    # Initialize vector store
    try:
        vector_store = PolicyVectorStore()
        
        if clear_existing:
            print("Clearing existing vector store...", flush=True)
            # Note: ChromaDB doesn't have a simple clear() method
            # We'd need to delete the directory or use delete_collection
            # For now, we'll just add documents (they'll be deduplicated)
            print("  Note: Clear functionality requires manual directory deletion", flush=True)
        
        # Add chunks to vector store
        print("\nAdding documents to vector store...", flush=True)
        vector_store.add_documents(chunks)
        
        print(f"\n[SUCCESS] Successfully initialized vector store with {len(chunks)} chunks!", flush=True)
        print(f"  Vector store location: {settings.VECTOR_STORE_PATH}", flush=True)
        
    except Exception as e:
        print(f"\n[ERROR] Error initializing vector store: {e}", flush=True)
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Initialize vector store with policy documents")
    parser.add_argument(
        "--policy-dir",
        type=str,
        default=None,
        help="Directory containing policy files (default: data/sample)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing vector store before adding (requires manual deletion)"
    )
    
    args = parser.parse_args()
    
    policy_dir = Path(args.policy_dir) if args.policy_dir else None
    initialize_vector_store(policy_dir, args.clear)


if __name__ == "__main__":
    main()

