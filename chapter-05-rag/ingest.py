"""PDF validation boundary retained from Chapter 4."""

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from config import MAX_CHARS, MAX_PAGES, MIN_CHARS


class IngestError(Exception):
    """Raised when a PDF cannot be accepted safely."""


def extract_resume_text(uploaded_file) -> str:
    if uploaded_file is None:
        raise IngestError("Please upload a resume PDF to continue.")
    try:
        reader = PdfReader(uploaded_file)
    except PdfReadError as exc:
        raise IngestError("That file could not be read as a PDF. Please re-export it and try again.") from exc
    if reader.is_encrypted:
        raise IngestError("That PDF is password-protected. Please upload an unprotected copy.")
    if len(reader.pages) > MAX_PAGES:
        raise IngestError(f"That PDF has {len(reader.pages)} pages. This tool accepts up to {MAX_PAGES}.")
    try:
        text = " ".join(" ".join(page.extract_text() or "" for page in reader.pages).split())
    except Exception as exc:
        raise IngestError("That PDF's contents could not be read. Please re-export it and try again.") from exc
    if len(text) < MIN_CHARS:
        raise IngestError("I could not read enough text from that PDF. Please use a text-based PDF.")
    return text[:MAX_CHARS]
