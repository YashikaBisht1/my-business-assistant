from pathlib import Path
from typing import List

import json

# Try multiple PDF parsers to be flexible in different environments
try:
    import PyPDF2  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    PyPDF2 = None  # type: ignore

try:
    from pdfminer.high_level import extract_text as _extract_pdf_text  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _extract_pdf_text = None  # type: ignore


def load_policy_document(file_path: Path) -> str:
    """
    Load a policy document (PDF, TXT, JSON) and return plain text.

    Args:
        file_path (Path): Path to the policy document.

    Returns:
        str: Extracted text from the document.
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return _load_pdf(file_path)

    if extension == ".txt":
        return _load_txt(file_path)

    if extension == ".json":
        return _load_json(file_path)

    raise ValueError(f"Unsupported policy file type: {extension}")


def _load_pdf(file_path: Path) -> str:
    """Extract text from a PDF file."""
    # Prefer pdfminer when available because extraction tends to be more robust
    if _extract_pdf_text is not None:
        try:
            return _extract_pdf_text(str(file_path)).strip()
        except Exception:
            pass

    if PyPDF2 is not None:
        text = ""
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text.strip()

    raise RuntimeError("No PDF parser available (install pdfminer.six or PyPDF2)")


def _load_txt(file_path: Path) -> str:
    """Load text from a TXT file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read().strip()


def _load_json(file_path: Path) -> str:
    """
    Load policy text from JSON.
    Assumes JSON contains text-based values.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return _flatten_json(data)


def _flatten_json(data) -> str:
    """
    Convert JSON data into a single text string.
    """
    texts: List[str] = []

    if isinstance(data, dict):
        for value in data.values():
            texts.append(_flatten_json(value))

    elif isinstance(data, list):
        for item in data:
            texts.append(_flatten_json(item))

    else:
        texts.append(str(data))

    return " ".join(texts)
