from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, Generator
from datetime import datetime
import os

from models import Base, Question, Attempt, TopicStats

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'examino.db')}"

engine       = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── QUESTIONS ─────────────────────────────────────────────

def save_questions(questions: list[dict], source_file: str, db: Session) -> int:
    inserted = 0

    for q in questions:
        if not db.query(Question).filter_by(question_id=q["question_id"]).first():
            db.add(Question(
                question_id      = q["question_id"],
                question_type    = q["question_type"],
                question_text    = q["question_text"],
                options          = q.get("options"),
                correct_answer   = q["correct_answer"],

                topic            = q["topic"],
                subject          = q.get("subject", "General"),
                unit             = q.get("unit"),

                difficulty_level = q.get("difficulty_level", "medium"),

                source_file      = source_file,
                source_type      = q.get("source_type"),
                question_format  = q.get("question_format", "MCQ"),
            ))
            inserted += 1

    db.commit()
    return inserted


def get_questions(
    db: Session,
    subject: Optional[str] = None,
    unit: Optional[str] = None,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 20,
) -> list[Question]:

    q = db.query(Question)

    if subject:
        q = q.filter(Question.subject == subject)

    if unit:
        q = q.filter(Question.unit == unit)

    if topic:
        q = q.filter(Question.topic == topic)

    if difficulty:
        q = q.filter(Question.difficulty_level == difficulty)

    if source:
        q = q.filter(Question.source_type == source)

    return q.limit(limit).all()


def get_question_by_id(question_id: str, db: Session) -> Optional[Question]:
    return db.query(Question).filter_by(question_id=question_id).first()


def count_questions(db: Session) -> int:
    return db.query(Question).count()


def get_subjects(db: Session) -> list[str]:
    rows = db.query(Question.subject).distinct().all()
    return sorted([r[0] for r in rows])


# ── ATTEMPTS ─────────────────────────────────────────────

def record_attempt(
    question_id: str,
    user_answer: str,
    is_correct: bool,
    topic: str,
    subject: str,
    difficulty: str,
    db: Session,
) -> None:

    db.add(Attempt(
        question_id = question_id,
        user_answer = user_answer,
        is_correct  = is_correct,
        topic       = topic,
        subject     = subject,
        difficulty  = difficulty,
    ))

    db.commit()
    _update_topic_stats(topic, subject, is_correct, db)


def get_recent_attempts(db: Session, limit: int = 50) -> list[Attempt]:
    return db.query(Attempt).order_by(Attempt.attempted_at.desc()).limit(limit).all()


# ── STATS ─────────────────────────────────────────────

def _update_topic_stats(topic, subject, is_correct, db):
    stats = get_topic_stats(topic, subject, db)

    # If no stats row exists, create it
    if not stats:
        stats = create_topic_stats(topic, subject, db)

    # SAFETY: Prevent NoneType crashes
    if stats.total_attempts is None:
        stats.total_attempts = 0
    if stats.correct_count is None:
        stats.correct_count = 0

    stats.total_attempts += 1

    if is_correct:
        stats.correct_count += 1

    # Update accuracy
    if stats.total_attempts > 0:
        stats.accuracy = stats.correct_count / stats.total_attempts
    
    stats.last_updated = datetime.utcnow()
    db.commit()


# ── STATS HELPERS ─────────────────────────────────────────────

def get_topic_stats(topic: str, subject: str, db: Session):
    return db.query(TopicStats).filter_by(topic=topic, subject=subject).first()


def create_topic_stats(topic: str, subject: str, db: Session) -> TopicStats:
    stats = TopicStats(
        topic=topic,
        subject=subject,
        total_attempts=0,
        correct_count=0,
        accuracy=0.0,
        current_difficulty="medium"
    )
    db.add(stats)
    db.commit()
    db.refresh(stats)
    return stats


def get_all_stats(db: Session):
    return db.query(TopicStats).all()
