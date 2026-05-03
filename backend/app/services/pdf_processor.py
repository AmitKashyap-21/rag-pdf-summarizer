import io
import logging
from typing import List, Dict, Any
import PyPDF2

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_bytes: bytes) -> List[Dict[str, Any]]:
    """Extract text from PDF with page tracking."""
    pages = []
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
                if text.strip():
                    pages.append({
                        "page_number": page_num,
                        "content": text
                    })
            except Exception as e:
                logger.warning(f"Failed to extract page {page_num}: {e}")
                continue
    except Exception as e:
        logger.error(f"Failed to read PDF: {e}")
        raise ValueError(f"Failed to read PDF: {e}")
    return pages


def get_page_count(pdf_bytes: bytes) -> int:
    """Get number of pages in PDF."""
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    return len(reader.pages)


def validate_pdf(pdf_bytes: bytes) -> bool:
    """Validate PDF integrity."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        _ = len(reader.pages)
        return True
    except Exception:
        return False
