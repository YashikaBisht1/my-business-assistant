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

2. Run the Gradio UI:

```powershell
python -m business_assistant.run_gradio
```

3. In the UI, either paste computed insights (JSON or raw text) and policy
   documents (separated with `---`), or upload a `.json` file for insights and
   `.txt` files for policies.

Notes
- The processor explicitly reports missing fields and returns conservative
  recommendations that must be validated against full data and policy texts.
- If you want PDF support or richer parsing, I can add it; it requires
  additional dependencies and handling.

Next steps (optional)
- Add unit tests in `tests/` and run with `pytest`.
- Add file-type handling for PDFs and other document formats.
- Connect the UI to your Retrieval-Augmented Generation (RAG) pipeline to
  fetch policy documents automatically.
