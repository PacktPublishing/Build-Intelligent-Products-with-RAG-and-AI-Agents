"""PDF in, clean validated text out -- or a clear reason why not.

Ingestion at this stage has exactly four jobs, in order: accept the
right things, extract text from them, clean what came out, and enforce
the size caps from config.py. Invalid input is refused here, before it
ever reaches a paid model call.
"""

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from config import MAX_CHARS, MAX_PAGES, MIN_CHARS

SCANNED_PDF_MESSAGE = (
    "I couldn't read text from that PDF. It may be a scanned image "
    "rather than a text document. Please export your resume directly "
    "from your editor as a PDF and try again."
)


class IngestError(Exception):
    """Raised with a user-facing message when input can't be accepted."""


def extract_resume_text(uploaded_file) -> str:
    """Extract, clean, and validate resume text from an uploaded PDF.

    Accepts anything ``pypdf.PdfReader`` accepts (a file path, a
    file-like object, or a Streamlit ``UploadedFile``).
    """
    if uploaded_file is None:
        raise IngestError("Please upload a resume PDF to continue.")

    try:
        reader = PdfReader(uploaded_file)
    except PdfReadError as exc:
        raise IngestError(
            "That file couldn't be read as a PDF. It may be corrupted "
            "or in a different format. Please export your resume as a "
            "PDF and try again."
        ) from exc

    if reader.is_encrypted:
        raise IngestError(
            "That PDF is password-protected. Please upload an "
            "unprotected copy of your resume."
        )

    if len(reader.pages) > MAX_PAGES:
        raise IngestError(
            f"That PDF has {len(reader.pages)} pages. Resumes are 1-2 "
            f"pages; this tool accepts up to {MAX_PAGES}. If this is a "
            "portfolio, please upload just the resume."
        )

    try:
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:  # pypdf can raise a variety of parser errors
        raise IngestError(
            "That PDF's contents couldn't be read. It may be corrupted. "
            "Please try re-exporting it and uploading again."
        ) from exc

    text = " ".join(text.split())  # collapse repeated whitespace

    if len(text) < MIN_CHARS:
        raise IngestError(SCANNED_PDF_MESSAGE)

    return text[:MAX_CHARS]
