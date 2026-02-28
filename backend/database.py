from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, Generator
from datetime import datetime
from models import Base, Question, Attempt, TopicStats

# ✅ Render-safe SQLite location
DATABASE_URL = "sqlite:////tmp/examino.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ── INIT DB ─────────────────────────────────────────────

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
        if db.query(Question).filter_by(question_id=q["question_id"]).first():
            continue

        if q.get("text_hash") and db.query(Question).filter_by(text_hash=q["text_hash"]).first():
            continue

        db.add(Question(
            question_id=q["question_id"],
            question_type=q["question_type"],
            question_text=q["question_text"],
            options=q.get("options"),
            correct_answer=q["correct_answer"],
            topic=q["topic"],
            subject=q.get("subject", "General"),
            unit=q.get("unit"),
            difficulty_level=q.get("difficulty_level", "medium"),
            source_file=source_file,
            source_type=q.get("source_type"),
            question_format=q.get("question_format", "MCQ"),
            text_hash=q.get("text_hash"),
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

    query = db.query(Question)

    if subject:
        query = query.filter(Question.subject == subject)

    if unit:
        query = query.filter(Question.unit == unit)

    if topic:
        query = query.filter(Question.topic == topic)

    if difficulty:
        query = query.filter(Question.difficulty_level == difficulty)

    if source:
        query = query.filter(Question.source_type == source)

    return query.limit(limit).all()


def get_question_by_id(question_id: str, db: Session) -> Optional[Question]:
    return db.query(Question).filter_by(question_id=question_id).first()


def count_questions(db: Session) -> int:
    return db.query(Question).count()


def get_subjects(db: Session) -> list[str]:
    rows = db.query(Question.subject).distinct().all()
    return sorted([r[0] for r in rows])


def get_units(db: Session, subject: str) -> list[str]:
    rows = db.query(Question.unit).filter(
        Question.subject == subject
    ).distinct().all()

    return sorted([r[0] for r in rows if r[0]])


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
        question_id=question_id,
        user_answer=user_answer,
        is_correct=is_correct,
        topic=topic,
        subject=subject,
        difficulty=difficulty,
    ))

    db.commit()
    _update_topic_stats(topic, subject, is_correct, db)


def get_recent_attempts(db: Session, limit: int = 50) -> list[Attempt]:
    return db.query(Attempt)\
             .order_by(Attempt.attempted_at.desc())\
             .limit(limit)\
             .all()


# ── STATS ─────────────────────────────────────────────

def _update_topic_stats(topic: str, subject: str, is_correct: bool, db: Session):
    stats = get_topic_stats(topic, subject, db)

    if not stats:
        stats = create_topic_stats(topic, subject, db)

    stats.total_attempts = (stats.total_attempts or 0) + 1

    if is_correct:
        stats.correct_count = (stats.correct_count or 0) + 1

    stats.accuracy = (
        stats.correct_count / stats.total_attempts
        if stats.total_attempts > 0 else 0.0
    )

    stats.last_updated = datetime.utcnow()
    db.commit()


# ── STATS HELPERS ─────────────────────────────────────────────

def get_topic_stats(topic: str, subject: str, db: Session):
    return db.query(TopicStats)\
             .filter_by(topic=topic, subject=subject)\
             .first()


def create_topic_stats(topic: str, subject: str, db: Session) -> TopicStats:
    stats = TopicStats(
        topic=topic,
        subject=subject,
        total_attempts=0,
        correct_count=0,
        accuracy=0.0,
        current_difficulty="medium",
    )

    db.add(stats)
    db.commit()
    db.refresh(stats)
    return stats


def get_all_stats(db: Session):
    return db.query(TopicStats).all()