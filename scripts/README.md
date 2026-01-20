# Scripts Directory

Utility scripts for managing the Business Assistant application.

## Available Scripts

### `init_vector_store.py`

Initializes the ChromaDB vector store with policy documents from a directory.

**Usage:**
```bash
# Initialize with default policy directory (data/sample)
python -m scripts.init_vector_store

# Specify custom policy directory
python -m scripts.init_vector_store --policy-dir /path/to/policies

# Clear existing store (requires manual directory deletion)
python -m scripts.init_vector_store --clear
```

**What it does:**
1. Scans the policy directory for `.txt`, `.pdf`, and `.json` files
2. Loads and extracts text from each policy document
3. Splits large documents into chunks (using configurable chunk size)
4. Creates embeddings and stores them in ChromaDB
5. Makes policies searchable via RAG retrieval

**Requirements:**
- Policy documents in `data/sample/` directory (or specified path)
- Vector store directory will be created at `business_assistant/vector_store/`

**Note:** Run this script before using RAG features, otherwise the vector store will be empty.

