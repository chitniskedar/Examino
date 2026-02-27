"""
parser.py - File parsing and text extraction for SmartStudy
Handles: .txt, .pdf, .md, .py, .cpp, .java
"""

import re
import io
from pathlib import Path
from typing import Optional


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract clean text from uploaded file based on extension."""
    ext = Path(filename).suffix.lower()
    
    if ext == ".pdf":
        return _parse_pdf(file_bytes)
    elif ext in (".txt", ".md"):
        return _parse_text(file_bytes)
    elif ext in (".py", ".cpp", ".java"):
        return _parse_code(file_bytes, ext)
    else:
        return _parse_text(file_bytes)  # fallback


def _parse_text(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="replace")


def _parse_pdf(file_bytes: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)
    except ImportError:
        return "[PDF parsing requires pypdf. Install with: pip install pypdf]"
    except Exception as e:
        return f"[PDF parse error: {e}]"


def _parse_code(file_bytes: bytes, ext: str) -> str:
    code = _parse_text(file_bytes)
    # Add language hint for question engine
    lang_map = {".py": "Python", ".cpp": "C++", ".java": "Java"}
    lang = lang_map.get(ext, "code")
    return f"[LANGUAGE: {lang}]\n\n{code}"


def extract_sections(text: str) -> list[dict]:
    """
    Split text into logical sections based on headings or blank lines.
    Returns list of {'title': str, 'content': str}
    """
    sections = []

    # Try to find markdown/text headings
    heading_pattern = re.compile(r'^(#{1,3}\s+.+|[A-Z][A-Z\s]{3,}:?$)', re.MULTILINE)
    matches = list(heading_pattern.finditer(text))

    if matches:
        for i, match in enumerate(matches):
            title = match.group().strip("#").strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            if content:
                sections.append({"title": title, "content": content})
    else:
        # Fall back: split by double newlines into chunks
        chunks = [c.strip() for c in re.split(r'\n{2,}', text) if c.strip()]
        for i, chunk in enumerate(chunks):
            sections.append({"title": f"Section {i + 1}", "content": chunk})

    return sections


def extract_key_terms(text: str) -> list[str]:
    """
    Extract key technical terms from text.
    Simple heuristic: capitalized multi-word phrases, code identifiers, and bolded terms.
    """
    terms = set()

    # Bolded markdown terms **term**
    bold = re.findall(r'\*\*(.+?)\*\*', text)
    terms.update(bold)

    # CamelCase identifiers (likely class/method names)
    camel = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', text)
    terms.update(camel)

    # All-caps abbreviations (like API, SQL, CPU)
    abbrevs = re.findall(r'\b[A-Z]{2,6}\b', text)
    terms.update(abbrevs)

    # Technical lowercase terms (common CS vocabulary)
    cs_keywords = {
        "algorithm", "recursion", "iteration", "stack", "queue", "heap",
        "hash", "tree", "graph", "pointer", "class", "object", "inheritance",
        "polymorphism", "encapsulation", "abstraction", "complexity",
        "runtime", "sorting", "searching", "dynamic programming", "greedy",
        "backtracking", "binary search", "linked list", "array", "string",
        "function", "loop", "condition", "exception", "thread", "process",
        "memory", "cache", "database", "index", "query", "API", "HTTP",
        "REST", "JSON", "XML", "TCP", "UDP", "socket", "protocol"
    }
    text_lower = text.lower()
    for kw in cs_keywords:
        if kw in text_lower:
            terms.add(kw)

    return sorted(terms)[:30]  # cap at 30 terms