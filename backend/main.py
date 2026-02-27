"""
main.py — Examino FastAPI backend
Run:  uvicorn main:app --reload  (from inside the backend/ folder)
"""

import os
import sys

# Make sure backend/ modules resolve when run from any cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import (
    init_db, get_db, save_questions, get_questions, get_question_by_id,
    record_attempt, get_recent_attempts, count_questions, get_subjects, SessionLocal,
)
from question_engine import get_all_preloaded_questions, generate_questions
from scheduler import adjust_difficulty, get_performance_summary

app = FastAPI(title="Examino API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend from ../frontend/
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.on_event("startup")
def startup() -> None:
    """Initialise DB and seed all pre-loaded subject questions."""
    init_db()
    db = SessionLocal()
    try:
        existing = count_questions(db)
        if existing == 0:
            questions = get_all_preloaded_questions()
            inserted  = save_questions(questions, source_file="preloaded", db=db)
            print(f"[Examino] Seeded {inserted} questions from 8 subjects.")
        else:
            print(f"[Examino] DB already has {existing} questions — skipping seed.")
    finally:
        db.close()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/health")
def health():
    return {"status": "ok", "service": "Examino"}


@app.get("/subjects")
def list_subjects(db: Session = Depends(get_db)):
    return get_subjects(db)


@app.get("/questions")
def list_questions(
    subject:    Optional[str] = None,
    topic:      Optional[str] = None,
    difficulty: Optional[str] = None,
    limit:      int = 20,
    db: Session = Depends(get_db),
):
    qs = get_questions(db, subject=subject, topic=topic, difficulty=difficulty, limit=limit)
    return [_serialize(q) for q in qs]


@app.get("/questions/{question_id}")
def get_question(question_id: str, db: Session = Depends(get_db)):
    q = get_question_by_id(question_id, db)
    if not q:
        raise HTTPException(404, "Question not found")
    return _serialize(q)


class AnswerPayload(BaseModel):
    question_id: str
    user_answer: str


@app.post("/attempt")
def submit_attempt(payload: AnswerPayload, db: Session = Depends(get_db)):
    q = get_question_by_id(payload.question_id, db)
    if not q:
        raise HTTPException(404, "Question not found")

    is_correct = payload.user_answer.strip().lower() == q.correct_answer.strip().lower()

    record_attempt(
        question_id = q.question_id,
        user_answer = payload.user_answer,
        is_correct  = is_correct,
        topic       = q.topic,
        subject     = q.subject,
        difficulty  = q.difficulty_level,
        db          = db,
    )

    new_diff = adjust_difficulty(q.topic, db)

    return {
        "correct":         is_correct,
        "correct_answer":  q.correct_answer,
        "explanation":     _explanation(q),
        "new_difficulty":  new_diff,
    }


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    summary = get_performance_summary(db)
    summary["total_questions"] = count_questions(db)
    return summary


@app.get("/recent")
def recent(db: Session = Depends(get_db)):
    attempts = get_recent_attempts(db, limit=30)
    return [
        {
            "attempt_id":   a.attempt_id,
            "question_id":  a.question_id,
            "is_correct":   a.is_correct,
            "topic":        a.topic,
            "subject":      a.subject,
            "difficulty":   a.difficulty,
            "attempted_at": a.attempted_at.isoformat(),
        }
        for a in attempts
    ]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize(q) -> dict:
    return {
        "question_id":    q.question_id,
        "question_type":  q.question_type,
        "question_text":  q.question_text,
        "options":        q.options,
        "topic":          q.topic,
        "subject":        q.subject,
        "unit":           q.unit,
        "difficulty_level": q.difficulty_level,
        "source_file":    q.source_file,
        "created_at":     q.created_at.isoformat() if q.created_at else None,
    }


def _explanation(q) -> str:
    return {
        "true_false":    f"The statement is {q.correct_answer}. Review '{q.topic}' in {q.subject}.",
        "fill_blank":    f"The correct answer is '{q.correct_answer}'.",
        "mcq":           f"Correct: {q.correct_answer}",
        "code":          f"The output is: {q.correct_answer}",
        "complexity":    f"The correct complexity is {q.correct_answer}",
    }.get(q.question_type, f"Answer: {q.correct_answer}")