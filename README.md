# Business Decision Assistant (Gradio UI)

This repository contains a lightweight Gradio-based UI and processor for a
business decision assistant that follows strict rules:

- Do NOT analyze raw Excel files; accept only computed insights produced by
  other processing steps (JSON or raw text).
- Use only provided policy documents and feedback; do not hallucinate.
- Produce a structured four-section reasoning output: Summary of Findings,
  Policy Alignment, Recommended Actions, Limitations / Confidence.

What I added
- `business_assistant/ui/processor.py` — builds the structured reasoning output.
- `business_assistant/ui/gradio_app.py` — Gradio app (supports text input and file uploads).
- `business_assistant/ui/file_utils.py` — helpers to parse uploaded `.json` and `.txt` files.
- `business_assistant/run_gradio.py` — entrypoint to launch the UI.
- `requirements.txt` — minimal dependencies.
- `test_processor_run.py` — a simple smoke test used during development.

Quick start

1. Install dependencies (recommended in a virtual environment):

```powershell
python -m pip install -r requirements.txt
```

2. **Initialize the vector store** (required for RAG features):

```powershell
python -m scripts.init_vector_store
```

This loads policy documents from `data/sample/` into the ChromaDB vector store.
You can specify a custom directory with `--policy-dir PATH`.

3. Set up environment variables (optional, for LLM features):

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_api_key_here
```

4. Run the Gradio UI:

```powershell
python -m business_assistant.run_gradio
```

5. In the UI, either paste computed insights (JSON or raw text) and policy
   documents (separated with `---`), or upload a `.json` file for insights and
   `.txt` files for policies.

Notes
- The processor explicitly reports missing fields and returns conservative
  recommendations that must be validated against full data and policy texts.
- If you want PDF support or richer parsing, I can add it; it requires
  additional dependencies and handling.

## Recent Improvements

- ✅ **Vector Store Initialization**: Script to load policies into ChromaDB
- ✅ **Text Chunking**: Automatic chunking of large policy documents
- ✅ **Better Error Handling**: Clear error messages when LLM/API unavailable
- ✅ **Empty Store Detection**: Warns when vector store is empty
- ✅ **Export Functionality**: Export reports to JSON, Markdown, or TXT
- ✅ **Similarity Threshold**: Filter low-quality policy matches

## Next steps (optional)
- Add unit tests in `tests/` and run with `pytest`.
- Add PDF export functionality (requires reportlab or similar).
- Add authentication for production deployment.
- Add batch processing for multiple files.
- Add caching for LLM responses to reduce API costs.

## Testing the Application

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for comprehensive testing instructions.

### Quick Test

1. **Initialize database:**
   ```bash
   python -m scripts.init_database
   ```

2. **Initialize vector store:**
   ```bash
   python -m scripts.init_vector_store
   ```

3. **Run the app:**
   ```bash
   python -m business_assistant.run_gradio
   ```

4. **Test in browser:**
   - Open `http://127.0.0.1:7860`
   - Upload a CSV/Excel file
   - Click "Process data"
   - Add policies and click "Generate Report"

## Troubleshooting

**Vector store is empty:**
- Run `python -m scripts.init_vector_store` to populate it

**LLM features not working:**
- Check that `GROQ_API_KEY` is set in `.env` file
- Verify API key is valid and has credits
- Check console output for specific error messages
- System will use rule-based fallback if LLM unavailable (still works!)

**RAG retrieval returns no results:**
- Ensure vector store is initialized (see above)
- Check that policy documents are in `data/sample/` or specified directory
- Verify similarity threshold isn't too high in config

**Database errors:**
- Run `python -m scripts.init_database` to create tables
- Check database file permissions

**Import errors:**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` to install all dependencies 
