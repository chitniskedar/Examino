"""
qb_sync.py — Sync newly generated questions into question_bank.json.

When a PDF is uploaded and questions are generated, this module:
  1. Loads the existing question_bank.json
  2. Converts generated questions to the QB schema
  3. Deduplicates by question text (normalised)
  4. Appends new questions under the correct subject key
  5. Re-sorts by unit then difficulty
  6. Atomically writes the updated file back

QB entry schema:
{
  "type":   "mcq" | "true_false" | ...,
  "q":      "Question text",
  "opts":   ["A. ...", "B. ...", "C. ...", "D. ..."],   # None for non-MCQ
  "a":      "Correct answer string",
  "topic":  "Topic name",
  "unit":   "Unit 1",
  "diff":   "easy" | "medium" | "hard",
  "source_type":     "PDF_UPLOAD",   # added so you can filter by origin
  "question_format": "MCQ"
}
"""

import json
import os
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DIFFICULTY_ORDER = {"easy": 1, "medium": 2, "hard": 3}


# ── Path resolution ───────────────────────────────────────────────────────────

def _find_qb_path() -> Path:
    """
    Locate question_bank.json regardless of where the server is launched from.
    Search order:
      1. Same directory as this file  (backend/)
      2. Parent directory             (project root)
      3. QUESTION_BANK_PATH env var   (override)
    """
    env_override = os.environ.get("QUESTION_BANK_PATH")
    if env_override:
        p = Path(env_override)
        if p.exists():
            return p

    here = Path(__file__).parent
    candidates = [
        here / "question_bank.json",
        here.parent / "question_bank.json",
        here.parent / "data" / "question_bank.json",
    ]
    for c in candidates:
        if c.exists():
            return c

    # If none found, create in same directory as this file
    default = here / "question_bank.json"
    logger.warning(f"question_bank.json not found; will create at {default}")
    return default


QB_PATH: Path = _find_qb_path()


# ── Schema conversion ─────────────────────────────────────────────────────────

def _to_qb_entry(q: dict) -> dict:
    """Convert an internal question dict → QB JSON schema entry."""
    return {
        "type":            q.get("question_type", "mcq"),
        "q":               q["question_text"].strip(),
        "opts":            q.get("options"),           # list or None
        "a":               q["correct_answer"].strip(),
        "topic":           q.get("topic", "General"),
        "unit":            q.get("unit", "Unit 1"),
        "diff":            q.get("difficulty_level", "medium"),
        "source_type":     q.get("source_type", "PDF_UPLOAD"),
        "question_format": q.get("question_format", "MCQ"),
    }


def _normalise(text: str) -> str:
    """Normalise question text for deduplication (lowercase, collapse whitespace)."""
    return re.sub(r"\s+", " ", text.strip().lower())


# ── Core sync function ────────────────────────────────────────────────────────

def sync_to_question_bank(
    questions: list[dict],
    subject: str,
    source_label: Optional[str] = None,
) -> dict:
    """
    Append generated questions to question_bank.json under the given subject.

    Args:
        questions:    List of internal question dicts (same format as save_questions uses).
        subject:      Subject key (e.g. "EEE", "Chemistry", "General").
        source_label: Optional label for logging (e.g. filename).

    Returns:
        {
          "inserted":  int,   # new questions added to QB
          "skipped":   int,   # duplicates skipped
          "total_in_subject": int,
          "qb_path":   str,
        }
    """
    if not questions:
        return {"inserted": 0, "skipped": 0, "total_in_subject": 0, "qb_path": str(QB_PATH)}

    # ── Load existing QB ──────────────────────────────────────────────────────
    bank = _load_bank()

    # Ensure subject key exists
    if subject not in bank:
        bank[subject] = []

    # Build dedup set from existing entries in this subject
    existing_norms: set[str] = {
        _normalise(entry["q"])
        for entry in bank[subject]
        if "q" in entry
    }

    # ── Convert + deduplicate ─────────────────────────────────────────────────
    new_entries: list[dict] = []
    skipped = 0

    for q in questions:
        entry = _to_qb_entry(q)
        norm  = _normalise(entry["q"])

        if norm in existing_norms:
            skipped += 1
            continue

        existing_norms.add(norm)
        new_entries.append(entry)

    # ── Append + re-sort ──────────────────────────────────────────────────────
    bank[subject].extend(new_entries)
    bank[subject] = _sort_entries(bank[subject])

    # ── Atomic write ─────────────────────────────────────────────────────────
    _write_bank(bank)

    total = len(bank[subject])
    inserted = len(new_entries)

    logger.info(
        f"[qb_sync] {source_label or subject}: "
        f"+{inserted} questions (skipped {skipped} dupes). "
        f"Subject total: {total}. File: {QB_PATH}"
    )

    return {
        "inserted":          inserted,
        "skipped":           skipped,
        "total_in_subject":  total,
        "qb_path":           str(QB_PATH),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_bank() -> dict:
    """Load question_bank.json; return empty dict if file doesn't exist."""
    if not QB_PATH.exists():
        return {}
    try:
        with open(QB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load {QB_PATH}: {e}")
        raise RuntimeError(f"Could not read question_bank.json: {e}")


def _write_bank(bank: dict) -> None:
    """
    Write bank back to disk atomically:
    write to a temp file, then rename (prevents corruption on crash).
    Also creates a timestamped backup beforehand.
    """
    # Backup before overwriting (keep last 3)
    _rotate_backups()

    tmp_path = QB_PATH.with_suffix(".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(bank, f, indent=2, ensure_ascii=False)
        # Atomic rename
        shutil.move(str(tmp_path), str(QB_PATH))
    except OSError as e:
        # Clean up temp if it exists
        if tmp_path.exists():
            tmp_path.unlink()
        raise RuntimeError(f"Failed to write question_bank.json: {e}")


def _rotate_backups(keep: int = 3) -> None:
    """Keep up to `keep` timestamped backups of question_bank.json."""
    backup_dir = QB_PATH.parent / ".qb_backups"
    backup_dir.mkdir(exist_ok=True)

    ts   = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = backup_dir / f"question_bank_{ts}.json"

    try:
        if QB_PATH.exists():
            shutil.copy2(str(QB_PATH), str(dest))

        # Prune old backups
        backups = sorted(backup_dir.glob("question_bank_*.json"))
        for old in backups[:-keep]:
            old.unlink()
    except OSError:
        pass  # Backup failure should not block the write


def _sort_entries(entries: list[dict]) -> list[dict]:
    """Sort QB entries by unit (asc) then difficulty (easy < medium < hard)."""
    return sorted(
        entries,
        key=lambda x: (
            x.get("unit", ""),
            DIFFICULTY_ORDER.get(x.get("diff", "medium"), 2),
        ),
    )


# ── Utility: get current QB stats ────────────────────────────────────────────

def get_qb_stats() -> dict:
    """Return per-subject and total question counts from question_bank.json."""
    try:
        bank = _load_bank()
    except Exception:
        return {"error": "Could not read question_bank.json", "subjects": {}, "total": 0}

    by_subject = {s: len(qs) for s, qs in bank.items()}
    return {
        "subjects": by_subject,
        "total":    sum(by_subject.values()),
        "qb_path":  str(QB_PATH),
    }