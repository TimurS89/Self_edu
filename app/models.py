from datetime import date, datetime, timezone

from app import db


class Card(db.Model):
    """A flashcard for spaced repetition review."""

    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    track = db.Column(db.String(20), nullable=False, index=True)  # python, claude, japanese
    topic = db.Column(db.String(100), nullable=False)
    front = db.Column(db.Text, nullable=False)
    back = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(200), default="")

    # FSRS/SRS scheduling fields
    stability = db.Column(db.Float, default=0.0)
    difficulty = db.Column(db.Float, default=0.3)
    due_date = db.Column(db.Date, default=date.today, index=True)
    last_review = db.Column(db.DateTime, nullable=True)
    reps = db.Column(db.Integer, default=0)
    state = db.Column(db.Integer, default=0)  # 0=new, 1=learning, 2=review, 3=relearning

    reviews = db.relationship("CardReview", backref="card", lazy="dynamic")


class CardReview(db.Model):
    """A single review event for a card."""

    __tablename__ = "card_reviews"

    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey("cards.id"), nullable=False)
    reviewed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    rating = db.Column(db.Integer, nullable=False)  # 1=again, 2=hard, 3=good, 4=easy
    response_time_ms = db.Column(db.Integer, nullable=True)


class LessonProgress(db.Model):
    """Tracks completion of lessons."""

    __tablename__ = "lesson_progress"

    id = db.Column(db.Integer, primary_key=True)
    track = db.Column(db.String(20), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    time_spent_sec = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint("track", "topic"),)


class StudySession(db.Model):
    """Tracks each study session for streaks and analytics."""

    __tablename__ = "study_sessions"

    id = db.Column(db.Integer, primary_key=True)
    session_date = db.Column(db.Date, default=date.today, index=True)
    track = db.Column(db.String(20), nullable=False)
    duration_min = db.Column(db.Integer, default=0)
    cards_reviewed = db.Column(db.Integer, default=0)
    activity_type = db.Column(db.String(20), default="review")  # review, lesson, quiz
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
