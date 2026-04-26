"""
Document Processor for SupportSim AI.
Handles PDF, DOCX, TXT, and Markdown file processing for knowledge base uploads.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text(file_path: str) -> tuple[str, int]:
    """
    Extract text from a file. Returns (text, page_count).
    Supports: PDF, DOCX, TXT, MD
    """
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        return _extract_pdf(path)
    elif extension == ".docx":
        return _extract_docx(path)
    elif extension in (".txt", ".md"):
        return _extract_text_file(path)
    else:
        raise ValueError(f"Unsupported file type: {extension}")


def _extract_pdf(path: Path) -> tuple[str, int]:
    """Extract text from a PDF file."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages), len(reader.pages)
    except Exception as e:
        logger.error(f"PDF extraction failed for {path}: {e}")
        raise


def _extract_docx(path: Path) -> tuple[str, int]:
    """Extract text from a DOCX file."""
    try:
        from docx import Document
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        # Estimate pages (roughly 3000 chars per page)
        full_text = "\n\n".join(paragraphs)
        page_count = max(1, len(full_text) // 3000)
        return full_text, page_count
    except Exception as e:
        logger.error(f"DOCX extraction failed for {path}: {e}")
        raise


def _extract_text_file(path: Path) -> tuple[str, int]:
    """Extract text from a plain text or markdown file."""
    try:
        text = path.read_text(encoding="utf-8")
        page_count = max(1, len(text) // 3000)
        return text, page_count
    except Exception as e:
        logger.error(f"Text extraction failed for {path}: {e}")
        raise


def chunk_text(text: str, chunk_size: int = 1024, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks for RAG indexing."""
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at a sentence boundary
        if end < len(text):
            last_period = chunk.rfind(". ")
            last_newline = chunk.rfind("\n")
            break_point = max(last_period, last_newline)
            if break_point > chunk_size * 0.5:
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1

        chunks.append(chunk.strip())
        start = end - overlap

    return [c for c in chunks if c]  # Filter empty chunks
