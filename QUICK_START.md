# Quick Start Guide

## Setup (One-Time)

```bash
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
# or
source venv/bin/activate  # Linux/Mac

# 2. Install dependencies (if not already done)
pip install -r requirements.txt

# 3. Initialize database
python -m scripts.init_database

# 4. Initialize vector store with sample policies
python -m scripts.init_vector_store --policy-dir data/sample

# 5. (Optional) Set up API key for LLM features
# Create .env file with:
# GROQ_API_KEY=your_key_here
```

## Run the App

```bash
python -m business_assistant.run_gradio
```

Open browser to: **http://127.0.0.1:7860**

## Quick Test

1. **Upload a CSV file** (or use sample data)
2. Click **"Process data"** → See insights JSON
3. **Add policies** (or use RAG from vector store)
4. Enter a **question**
5. Click **"Generate Report"** → Get 4-section output

## Expected Output

You should see 4 sections:
- ✅ **Summary of Findings** - Key insights
- ✅ **Policy Alignment** - How insights match policies  
- ✅ **Recommended Actions** - Actionable steps
- ✅ **Limitations / Confidence** - Confidence level

## Files Removed

- ❌ `business_assistant/rag/retriever.py` - Unused, functionality in QAPipeline
- ❌ `test_processor_run.py` - Redundant test file
- ❌ `SUMMARY.md` - Consolidated into README
- ❌ `ISSUES_AND_IMPROVEMENTS.md` - Consolidated into IMPROVEMENTS_SUMMARY.md

## Testing

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing instructions.

