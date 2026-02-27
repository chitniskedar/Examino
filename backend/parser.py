"""
parser.py — Extract clean text from uploaded files.
Supported: .txt  .pdf  .md  .py  .cpp  .java
"""

import re
import io
from pathlib import Path


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _parse_pdf(file_bytes)
    elif ext in (".py", ".cpp", ".java"):
        return _parse_code(file_bytes, ext)
    else:
        return _parse_plaintext(file_bytes)


def _parse_plaintext(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="replace")


def _parse_pdf(file_bytes: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages  = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(p for p in pages if p.strip())
    except ImportError:
        return "[PDF parsing requires pypdf: pip install pypdf]"
    except Exception as e:
        return f"[PDF parse error: {e}]"


def _parse_code(file_bytes: bytes, ext: str) -> str:
    lang_map = {".py": "Python", ".cpp": "C++", ".java": "Java"}
    return f"[LANGUAGE: {lang_map[ext]}]\n\n{_parse_plaintext(file_bytes)}"


def extract_sections(text: str) -> list[dict]:
    """Split text into logical sections by markdown headings or blank-line chunks."""
    sections = []
    heading  = re.compile(r'^(#{1,3}\s+.+|[A-Z][A-Z\s]{3,}:?)$', re.MULTILINE)
    matches  = list(heading.finditer(text))

    if matches:
        for i, m in enumerate(matches):
            title   = m.group().strip("# ").strip()
            start   = m.end()
            end     = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            if content:
                sections.append({"title": title, "content": content})
    else:
        for i, chunk in enumerate(re.split(r'\n{2,}', text)):
            chunk = chunk.strip()
            if chunk:
                sections.append({"title": f"Section {i + 1}", "content": chunk})

    return sections


def extract_key_terms(text: str) -> list[str]:
    terms = set()
    terms.update(re.findall(r'\*\*(.+?)\*\*', text))
    terms.update(re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', text))
    terms.update(re.findall(r'\b[A-Z]{2,6}\b', text))

    cs_vocab = {
        "algorithm","recursion","iteration","stack","queue","heap","hash",
        "tree","graph","pointer","class","object","inheritance","polymorphism",
        "encapsulation","abstraction","complexity","sorting","searching",
        "dynamic programming","greedy","backtracking","binary search",
        "linked list","array","string","function","loop","exception",
        "thread","process","memory","cache","database","index","API",
        "HTTP","REST","TCP","UDP","socket","protocol","force","moment",
        "equilibrium","statics","dynamics","thermodynamics","electrostatics",
        "current","voltage","resistance","capacitance","inductance","circuit",
        "entropy","enthalpy","bond","reaction","oxidation","reduction",
        "ecosystem","biodiversity","pollution","wavelength","frequency",
        "interference","diffraction","quantum","photon","electron",
    }
    text_lower = text.lower()
    for kw in cs_vocab:
        if kw in text_lower:
            terms.add(kw)

    return sorted(terms)[:40]