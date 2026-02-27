"""
scheduler.py — Adaptive difficulty adjustment for Examino.
  accuracy > 75%  →  promote to harder difficulty
  accuracy < 40%  →  demote to easier difficulty
  else            →  keep current
"""

from sqlalchemy.orm import Session
from database import get_topic_stats, get_all_stats

LEVELS       = ["easy", "medium", "hard"]
HIGH         = 0.75
LOW          = 0.40
MIN_ATTEMPTS = 3


def get_recommended_difficulty(topic: str, db: Session) -> str:
    stats = get_topic_stats(topic, db)
    if not stats or stats.total_attempts < MIN_ATTEMPTS:
        return "medium"
    return stats.current_difficulty


def adjust_difficulty(topic: str, db: Session) -> str:
    from models import TopicStats
    stats = db.query(TopicStats).filter_by(topic=topic).first()
    if not stats or stats.total_attempts < MIN_ATTEMPTS:
        return "medium"

    idx = LEVELS.index(stats.current_difficulty) if stats.current_difficulty in LEVELS else 1

    if stats.accuracy >= HIGH:
        idx = min(idx + 1, len(LEVELS) - 1)
    elif stats.accuracy <= LOW:
        idx = max(idx - 1, 0)

    stats.current_difficulty = LEVELS[idx]
    db.commit()
    return stats.current_difficulty


def get_performance_summary(db: Session) -> dict:
    all_stats = get_all_stats(db)
    if not all_stats:
        return {"total_attempts": 0, "overall_accuracy": 0.0, "topics": [], "by_subject": {}}

    total   = sum(s.total_attempts for s in all_stats)
    correct = sum(s.correct_count  for s in all_stats)
    overall = round((correct / total * 100) if total else 0.0, 1)

    topics = sorted([
        {
            "topic":      s.topic,
            "subject":    s.subject,
            "attempts":   s.total_attempts,
            "correct":    s.correct_count,
            "accuracy":   round(s.accuracy * 100, 1),
            "difficulty": s.current_difficulty,
        }
        for s in all_stats
    ], key=lambda x: x["accuracy"])

    # Group by subject for the stats dashboard
    by_subject: dict[str, dict] = {}
    for s in all_stats:
        subj = s.subject
        if subj not in by_subject:
            by_subject[subj] = {"attempts": 0, "correct": 0}
        by_subject[subj]["attempts"] += s.total_attempts
        by_subject[subj]["correct"]  += s.correct_count

    for subj, data in by_subject.items():
        data["accuracy"] = round(
            (data["correct"] / data["attempts"] * 100) if data["attempts"] else 0.0, 1
        )

    return {
        "total_attempts":    total,
        "overall_accuracy":  overall,
        "topics":            topics,
        "by_subject":        by_subject,
    }