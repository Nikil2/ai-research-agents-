"""
PDF Service — Extract text from uploaded PDFs using pdfplumber
"""
import pdfplumber
import re
from pathlib import Path


def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extract text from a PDF file.

    Returns:
        {
            "raw_text": str,        # Full extracted text
            "pages": list[str],     # Text per page
            "total_pages": int,
            "metadata": dict
        }
    """
    pages_text = []
    full_text = ""

    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        metadata = pdf.metadata or {}

        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
            full_text += text + "\n\n"

    return {
        "raw_text": full_text.strip(),
        "pages": pages_text,
        "total_pages": total_pages,
        "metadata": metadata,
    }


def clean_text(raw_text: str) -> str:
    """
    Clean extracted PDF text:
    - Remove excessive whitespace
    - Fix broken lines
    - Remove page numbers / headers / footers (basic)
    - Normalize unicode characters
    """
    text = raw_text

    # Replace multiple newlines with double newline (paragraph breaks)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Fix broken words (hyphenation at line breaks)
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)

    # Replace single newlines within paragraphs with spaces
    # (but keep double newlines as paragraph separators)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

    # Remove excessive spaces
    text = re.sub(r' {2,}', ' ', text)

    # Remove common page artifacts (Page 1, Page 2, etc.)
    text = re.sub(r'\bPage\s+\d+\s*(of\s+\d+)?\b', '', text, flags=re.IGNORECASE)

    # Strip each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks by word count.

    Args:
        text: Cleaned text to chunk
        chunk_size: Number of words per chunk
        overlap: Number of overlapping words between chunks

    Returns:
        List of text chunks
    """
    words = text.split()
    chunks = []

    if len(words) <= chunk_size:
        return [text] if text.strip() else []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = ' '.join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap  # overlap for context continuity

    return chunks


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    return Path(file_path).stat().st_size
