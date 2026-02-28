"""
question_engine.py
Loads questions from question_bank.json
NO hardcoded dictionaries.
"""

import uuid
import json
import random
from pathlib import Path

BANK_PATH = Path(__file__).parent / "question_bank.json"

if not BANK_PATH.exists():
    raise FileNotFoundError("question_bank.json not found")

with open(BANK_PATH, "r", encoding="utf-8") as f:
    SUBJECT_BANKS = json.load(f)


def _bank_to_questions(subject: str):
    out = []

    for entry in SUBJECT_BANKS.get(subject, []):
        out.append({
            "question_id": str(uuid.uuid4()),
            "question_type": entry["type"],
            "question_text": entry["q"],
            "options": entry.get("opts"),
            "correct_answer": entry["a"],
            "topic": entry["topic"],
            "subject": subject,
            "unit": entry.get("unit"),
            "difficulty_level": entry.get("diff", "medium"),
            "source_type": entry.get("source_type"),
            "question_format": entry.get("question_format", "MCQ"),
        })

    return out


def get_all_preloaded_questions():
    all_qs = []
    for subject in SUBJECT_BANKS:
        all_qs.extend(_bank_to_questions(subject))
    return all_qs


def generate_questions(text: str, num_questions: int = 10, difficulty: str = "medium"):
    # Placeholder if needed later
    return []