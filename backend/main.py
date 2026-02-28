"""
main.py — Examino FastAPI backend
Run: uvicorn main:app --reload
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
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
    get_units,
    SessionLocal,
)

from question_engine import get_all_preloaded_questions
from scheduler import adjust_difficulty, get_performance_summary, get_recommended_difficulty
from models import Question

# PDF + generation imports
from pdf_service import (
    extract_text_from_bytes,
    split_into_sections,
    infer_metadata,
    compute_text_hash,
)
from llm_question_gen import (
    generate_mcqs_from_section,
    assemble_questions,
    infer_difficulty as llm_infer_difficulty,
)
from qb_sync import sync_to_question_bank, get_qb_stats


app = FastAPI(title="Examino API", version="2.1.0")

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
    return {"status": "ok", "version": "2.1.0"}


@app.get("/subjects")
def list_subjects(db: Session = Depends(get_db)):
    return get_subjects(db)


@app.get("/units")
def list_units(subject: str, db: Session = Depends(get_db)):
    return get_units(db, subject)


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
        "explanation": "",
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


# ── PDF UPLOAD + AUTO QUESTION GENERATION ────────────────────

@app.post("/upload-material")
async def upload_material(
    file: UploadFile = File(...),
    subject: Optional[str]  = Form(None),
    unit:    Optional[str]  = Form(None),
    topic:   Optional[str]  = Form(None),
    questions_per_section: int = Form(3),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF study material.
    Extracts text → splits sections → generates MCQs → saves to DB.

    Returns a summary: {inserted, skipped_duplicates, sections_processed, questions_generated}
    """
    # ── 1. Validate file type ──
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    # ── 2. Read bytes ──
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(400, "Uploaded file is empty.")

    # ── 3. Extract text ──
    try:
        full_text = extract_text_from_bytes(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(422, f"Could not extract text from PDF: {e}")

    if len(full_text.split()) < 50:
        raise HTTPException(422, "PDF contains too little extractable text (< 50 words).")

    # ── 4. Infer metadata if not provided ──
    meta = infer_metadata(full_text, file.filename)
    resolved_subject = subject or meta["subject"]
    resolved_unit    = unit    or meta["unit"]
    resolved_topic   = topic   or meta["topic"]

    # ── 5. Split into sections ──
    sections = split_into_sections(full_text)
    if not sections:
        raise HTTPException(422, "Could not split PDF into sections.")

    # ── 6. Generate questions per section (async) ──
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    all_raw_questions = []
    tasks = []

    for idx, section in enumerate(sections):
        difficulty = llm_infer_difficulty(section["content"], idx, len(sections))
        section_topic = section["title"] if len(section["title"]) > 3 else resolved_topic

        tasks.append(
            generate_mcqs_from_section(
                section_text=section["content"],
                num_questions=questions_per_section,
                difficulty=difficulty,
                subject=resolved_subject,
                topic=section_topic,
                api_key=api_key,
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for idx, (section, result) in enumerate(zip(sections, results)):
        if isinstance(result, Exception):
            continue  # Skip failed sections silently

        difficulty    = llm_infer_difficulty(section["content"], idx, len(sections))
        section_topic = section["title"] if len(section["title"]) > 3 else resolved_topic

        assembled = assemble_questions(
            raw_questions=result,
            subject=resolved_subject,
            unit=resolved_unit,
            topic=section_topic,
            difficulty=difficulty,
            source_file=file.filename,
        )

        # Attach text_hash for dedup
        for q in assembled:
            q["text_hash"] = compute_text_hash(q["question_text"])

        all_raw_questions.extend(assembled)

    # ── 7. Save to DB (with dedup) ──
    total_generated = len(all_raw_questions)
    db_inserted = save_questions(all_raw_questions, source_file=file.filename, db=db)
    db_skipped  = total_generated - db_inserted

    # ── 8. Sync to question_bank.json (master QB) ──
    qb_result = sync_to_question_bank(
        questions=all_raw_questions,
        subject=resolved_subject,
        source_label=file.filename,
    )

    return {
        "status":                "success",
        "filename":              file.filename,
        "subject":               resolved_subject,
        "unit":                  resolved_unit,
        "topic":                 resolved_topic,
        "sections_processed":    len(sections),
        "questions_generated":   total_generated,
        "db_inserted":           db_inserted,
        "db_skipped_duplicates": db_skipped,
        "qb_inserted":           qb_result["inserted"],
        "qb_skipped_duplicates": qb_result["skipped"],
        "qb_subject_total":      qb_result["total_in_subject"],
        "message": (
            f"Generated {total_generated} questions. "
            f"DB: +{db_inserted} (skipped {db_skipped}). "
            f"QB JSON: +{qb_result['inserted']} (skipped {qb_result['skipped']})."
        ),
    }


# ── QB JSON STATS ────────────────────────────────────────────────────────────

@app.get("/qb-stats")
def qb_stats():
    """Returns per-subject question counts in question_bank.json."""
    return get_qb_stats()


# ── SERIALIZER ───────────────────────────────────────────────

def _serialize(q: Question) -> dict:
    return {
        "question_id":     q.question_id,
        "question_type":   q.question_type,
        "question_text":   q.question_text,
        "options":         q.options,
        "correct_answer":  q.correct_answer,
        "topic":           q.topic,
        "subject":         q.subject,
        "unit":            q.unit,
        "difficulty_level": q.difficulty_level,
        "source_type":     q.source_type,
        "question_format": q.question_format,
        "source_file":     q.source_file,
        "created_at":      q.created_at.isoformat() if q.created_at else None,
    }