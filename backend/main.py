"""
main.py — Examino FastAPI backend
Run: uvicorn main:app --reload
"""

import os
import sys

# Ensure backend modules resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import (
    init_db,
    get_db,
    save_questions,
    get_questions,
    get_question_by_id,
    record_attempt,
    get_recent_attempts,
    count_questions,
    get_subjects,
    SessionLocal,
)

from question_engine import get_all_preloaded_questions
from scheduler import adjust_difficulty, get_performance_summary, get_recommended_difficulty
from models import Question


app = FastAPI(title="Examino API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── FRONTEND SERVING ─────────────────────────────────────────

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "frontend"
)

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ── STARTUP ──────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()
    db = SessionLocal()

    try:
        existing = count_questions(db)
        if existing == 0:
            questions = get_all_preloaded_questions()
            inserted = save_questions(questions, source_file="preloaded", db=db)
            print(f"[Examino] Seeded {inserted} questions.")
        else:
            print(f"[Examino] DB already has {existing} questions.")
    finally:
        db.close()


# ── BASIC ROUTES ─────────────────────────────────────────────

@app.get("/")
def serve_index():
    if os.path.exists(os.path.join(FRONTEND_DIR, "index.html")):
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
    return {"message": "Examino API running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/subjects")
def list_subjects(db: Session = Depends(get_db)):
    return get_subjects(db)


# ── QUESTION LISTING ─────────────────────────────────────────

@app.get("/questions")
def list_questions(
    subject: Optional[str] = None,
    unit: Optional[str] = None,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    qs = get_questions(
        db,
        subject=subject,
        unit=unit,
        topic=topic,
        difficulty=difficulty,
        source=source,
        limit=limit,
    )

    return [_serialize(q) for q in qs]


@app.get("/questions/{question_id}")
def get_single_question(question_id: str, db: Session = Depends(get_db)):
    q = get_question_by_id(question_id, db)
    if not q:
        raise HTTPException(404, "Question not found")
    return _serialize(q)


# ── STRUCTURED BROWSE MODE ──────────────────────────────────

@app.get("/browse")
def browse(
    subject: Optional[str] = None,
    unit: Optional[str] = None,
    source: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db),
):
    qs = get_questions(
        db,
        subject=subject,
        unit=unit,
        difficulty=difficulty,
        source=source,
        limit=1000,
    )

    structured = {}

    for q in qs:
        structured.setdefault(q.subject, {}) \
                  .setdefault(q.unit, {}) \
                  .setdefault(q.question_format or "MCQ", {}) \
                  .setdefault(q.difficulty_level, []) \
                  .append(_serialize(q))

    return structured


# ── PRACTICE MODE ───────────────────────────────────────────

@app.get("/practice")
def practice(subject: str, db: Session = Depends(get_db)):

    stats = get_performance_summary(db)

    if stats["topics"]:
        weakest_topic = stats["topics"][0]["topic"]
        difficulty = get_recommended_difficulty(weakest_topic, db)

        q = db.query(Question) \
              .filter(Question.topic == weakest_topic) \
              .filter(Question.difficulty_level == difficulty) \
              .first()
    else:
        q = db.query(Question) \
              .filter(Question.subject == subject) \
              .first()

    if not q:
        raise HTTPException(404, "No question available")

    return _serialize(q)


# ── ATTEMPTS ─────────────────────────────────────────────────

class AnswerPayload(BaseModel):
    question_id: str
    user_answer: str


@app.post("/attempt")
def submit_attempt(payload: AnswerPayload, db: Session = Depends(get_db)):

    q = get_question_by_id(payload.question_id, db)
    if not q:
        raise HTTPException(404, "Question not found")

    is_correct = payload.user_answer.strip().lower() == \
                 q.correct_answer.strip().lower()

    record_attempt(
        question_id=q.question_id,
        user_answer=payload.user_answer,
        is_correct=is_correct,
        topic=q.topic,
        subject=q.subject,
        difficulty=q.difficulty_level,
        db=db,
    )

    new_diff = adjust_difficulty(q.topic, db)

    return {
        "correct": is_correct,
        "correct_answer": q.correct_answer,
        "new_difficulty": new_diff,
    }


# ── STATS ────────────────────────────────────────────────────

@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    summary = get_performance_summary(db)
    summary["total_questions"] = count_questions(db)
    return summary


@app.get("/recent")
def recent(db: Session = Depends(get_db)):
    attempts = get_recent_attempts(db, limit=30)

    return [
        {
            "attempt_id": a.attempt_id,
            "question_id": a.question_id,
            "is_correct": a.is_correct,
            "topic": a.topic,
            "subject": a.subject,
            "difficulty": a.difficulty,
            "attempted_at": a.attempted_at.isoformat(),
        }
        for a in attempts
    ]


# ── SERIALIZER ───────────────────────────────────────────────

def _serialize(q: Question) -> dict:
    return {
        "question_id": q.question_id,
        "question_type": q.question_type,
        "question_text": q.question_text,
        "options": q.options,
        "correct_answer": q.correct_answer,
        "topic": q.topic,
        "subject": q.subject,
        "unit": q.unit,
        "difficulty_level": q.difficulty_level,
        "source_type": q.source_type,
        "question_format": q.question_format,
        "source_file": q.source_file,
        "created_at": q.created_at.isoformat() if q.created_at else None,
    }