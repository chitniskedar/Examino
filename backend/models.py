from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Question(Base):
    __tablename__ = "questions"

    question_id      = Column(String,  primary_key=True)
    question_type    = Column(String,  nullable=False)
    question_text    = Column(Text,    nullable=False)
    options          = Column(JSON,    nullable=True)
    correct_answer   = Column(String,  nullable=False)

    topic            = Column(String,  nullable=False)
    subject          = Column(String,  nullable=False, default="General")
    unit             = Column(String,  nullable=True)

    difficulty_level = Column(String,  default="medium")

    source_file      = Column(String,  nullable=True)
    source_type      = Column(String,  nullable=True)     # QB, QnA, PDF_UPLOAD
    question_format  = Column(String,  nullable=True)     # MCQ / 2M / 5M

    # Deduplication hash (MD5 of normalised question_text)
    text_hash        = Column(String,  nullable=True, unique=False, index=True)

    created_at       = Column(DateTime, default=datetime.utcnow)


class Attempt(Base):
    __tablename__ = "attempts"

    attempt_id   = Column(Integer, primary_key=True, autoincrement=True)
    question_id  = Column(String,  nullable=False)
    user_answer  = Column(String,  nullable=False)
    is_correct   = Column(Boolean, nullable=False)

    topic        = Column(String,  nullable=False)
    subject      = Column(String,  nullable=False, default="General")
    difficulty   = Column(String,  nullable=False)

    attempted_at = Column(DateTime, default=datetime.utcnow)


class TopicStats(Base):
    __tablename__ = "topic_stats"

    topic              = Column(String, primary_key=True)
    subject            = Column(String, nullable=False, default="General")

    total_attempts     = Column(Integer, default=0)
    correct_count      = Column(Integer, default=0)
    accuracy           = Column(Float,   default=0.0)

    current_difficulty = Column(String,  default="medium")

    last_updated       = Column(DateTime, default=datetime.utcnow)