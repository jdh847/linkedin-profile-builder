"""PDF resume parser — extracts raw text from resume PDFs."""

from __future__ import annotations

import re
from pathlib import Path


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract all text from a PDF file using pdfplumber.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Concatenated text from all pages.

    Raises:
        FileNotFoundError: If the PDF doesn't exist.
        RuntimeError: If PDF parsing fails.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if not path.suffix.lower() == ".pdf":
        raise ValueError(f"Not a PDF file: {path}")

    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError(
            "pdfplumber is required. Install with: pip install pdfplumber"
        )

    pages_text = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text.strip())
    except Exception as e:
        raise RuntimeError(f"Failed to parse PDF: {e}")

    if not pages_text:
        raise RuntimeError(f"No text extracted from PDF: {path}")

    result = "\n\n".join(pages_text)
    # Clean common PDF artifacts
    result = re.sub(r"\(cid:\d+\)", "▸", result)
    return result


def extract_text_from_multiple(pdf_paths: list[str | Path]) -> str:
    """Extract and merge text from multiple PDFs (e.g., different CV versions).

    Deduplicates content by keeping the longest version when pages overlap
    significantly.
    """
    texts = []
    for path in pdf_paths:
        try:
            text = extract_text_from_pdf(path)
            texts.append(text)
        except Exception as e:
            print(f"Warning: skipping {path}: {e}")

    if not texts:
        raise RuntimeError("No text extracted from any PDF")

    # Use the longest version as primary, append unique sections from others
    texts.sort(key=len, reverse=True)
    primary = texts[0]

    for extra in texts[1:]:
        # Find paragraphs in extra that aren't substantially in primary
        for paragraph in extra.split("\n\n"):
            paragraph = paragraph.strip()
            if len(paragraph) > 50 and paragraph not in primary:
                # Check if it's a genuinely new section
                words = set(paragraph.lower().split())
                primary_words = set(primary.lower().split())
                overlap = len(words & primary_words) / max(len(words), 1)
                if overlap < 0.7:
                    primary += f"\n\n{paragraph}"

    return primary
