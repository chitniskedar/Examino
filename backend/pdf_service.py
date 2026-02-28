"""
pdf_service.py — PDF text extraction and intelligent section splitting.
Uses pdfplumber (preferred) with PyPDF2 as fallback.
"""

import re
import io
import hashlib
from pathlib import Path
from typing import Optional


def extract_text_from_bytes(file_bytes: bytes, filename: str = "upload.pdf") -> str:
    """Extract all text from a PDF given as raw bytes."""
    ext = Path(filename).suffix.lower()
    if ext != ".pdf":
        raise ValueError(f"Unsupported file type: {ext}. Only PDF is supported.")

    # Try pdfplumber first (better layout preservation)
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                t = page.extract_text()
                if t and t.strip():
                    pages.append(t.strip())
            if pages:
                return "\n\n".join(pages)
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: PyPDF2
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                pages.append(t.strip())
        if pages:
            return "\n\n".join(pages)
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                pages.append(t.strip())
        return "\n\n".join(pages)
    except ImportError:
        raise RuntimeError(
            "No PDF library found. Install one:\n"
            "  pip install pdfplumber\n"
            "  pip install PyPDF2\n"
            "  pip install pypdf"
        )
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")


def split_into_sections(text: str, min_words: int = 30) -> list[dict]:
    """
    Intelligently split PDF text into logical sections.
    Returns list of: {title, content, word_count}
    """
    sections = []

    # Pattern 1: Markdown / numbered headings
    heading_pat = re.compile(
        r'^(?:#{1,3}\s+.+|'             # ## Heading
        r'(?:UNIT|CHAPTER|SECTION|MODULE)\s+[\dIVX]+[^\n]*|'  # UNIT 1, CHAPTER 2
        r'(?:\d+\.\s+[A-Z][^\n]{5,40})|'   # 1. Introduction
        r'[A-Z][A-Z\s]{4,40}:?)$',         # ALL CAPS HEADING:
        re.MULTILINE
    )

    matches = list(heading_pat.finditer(text))

    if len(matches) >= 2:
        for i, m in enumerate(matches):
            title   = m.group().strip("# ").strip(": ").strip()
            start   = m.end()
            end     = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            words   = len(content.split())
            if words >= min_words:
                sections.append({"title": title, "content": content, "word_count": words})
    else:
        # Fallback: split by double newlines → chunk into ~300-word blocks
        raw_chunks = re.split(r'\n{2,}', text)
        buffer, buf_words = [], 0
        chunk_idx = 1

        for chunk in raw_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            w = len(chunk.split())
            buffer.append(chunk)
            buf_words += w

            if buf_words >= 300:
                sections.append({
                    "title":      f"Section {chunk_idx}",
                    "content":    "\n\n".join(buffer),
                    "word_count": buf_words,
                })
                chunk_idx += 1
                buffer, buf_words = [], 0

        if buffer:
            sections.append({
                "title":      f"Section {chunk_idx}",
                "content":    "\n\n".join(buffer),
                "word_count": buf_words,
            })

    return [s for s in sections if s["word_count"] >= min_words]


def infer_metadata(text: str, filename: str) -> dict:
    """
    Heuristically infer subject, unit, and topic from filename + content.
    Returns: {subject, unit, topic}
    """
    text_lower  = text.lower()
    fname_lower = filename.lower()

    # Subject keywords
    SUBJ_KEYWORDS = {
        "Chemistry":    ["chemistry","chem","organic","inorganic","mol","bond","reaction","electron","atom"],
        "EEE":          ["electrical","circuit","voltage","current","resistance","capacitor","inductor","ohm","kirchhoff","semiconductor","transistor","diode"],
        "EPD":          ["engineering design","product design","design thinking","prototype","drawing","cad","manufacturing"],
        "EVS":          ["environment","ecology","biodiversity","pollution","sustainability","ecosystem","climate"],
        "MES":          ["mathematics","calculus","differential","integral","matrix","determinant","laplace","fourier","probability","statistics"],
        "Statics":      ["statics","dynamics","force","moment","equilibrium","beam","truss","friction","rigid body","torque","stress","strain"],
    }

    subject = "General"
    best_count = 0
    for subj, kws in SUBJ_KEYWORDS.items():
        count = sum(1 for kw in kws if kw in text_lower or kw in fname_lower)
        if count > best_count:
            best_count = count
            subject = subj

    # Unit: try to find unit number from text
    unit_match = re.search(r'unit\s*[:\-]?\s*(\d+|[ivx]+)', text_lower)
    unit = f"Unit {unit_match.group(1).upper()}" if unit_match else "Unit 1"

    # Topic: first meaningful heading or filename stem
    heading = re.search(r'^#{1,3}\s+(.+)$', text, re.MULTILINE)
    if heading:
        topic = heading.group(1).strip()[:60]
    else:
        # Use filename stem (cleaned up)
        stem = Path(filename).stem
        topic = re.sub(r'[_\-]+', ' ', stem).strip().title()[:60] or "General"

    return {"subject": subject, "unit": unit, "topic": topic}


def compute_text_hash(text: str) -> str:
    """Stable MD5 hash for deduplication."""
    cleaned = re.sub(r'\s+', ' ', text.strip().lower())
    return hashlib.md5(cleaned.encode()).hexdigest()