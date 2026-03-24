from datetime import date, timedelta

from flask import Blueprint, render_template

from app import db
from app.models import Card, StudySession, LessonProgress
from app.services.content import list_tracks, list_topics

dashboard_bp = Blueprint("dashboard", __name__)


def get_streak() -> int:
    """Calculate current study streak (consecutive days with a session)."""
    today = date.today()
    streak = 0
    check_date = today
    while True:
        has_session = db.session.query(StudySession).filter(
            StudySession.session_date == check_date
        ).first()
        if has_session:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak


def get_due_cards_count() -> dict[str, int]:
    """Count cards due today per track."""
    today = date.today()
    counts: dict[str, int] = {}
    for track_name in list_tracks():
        count = db.session.query(Card).filter(
            Card.track == track_name,
            Card.due_date <= today,
        ).count()
        counts[track_name] = count
    return counts


def get_track_progress(track: str) -> dict:
    """Calculate completion percentage for a track."""
    topics = list_topics(track)
    if not topics:
        return {"total": 0, "completed": 0, "percent": 0}
    total = len(topics)
    completed = db.session.query(LessonProgress).filter(
        LessonProgress.track == track,
        LessonProgress.completed == True,
    ).count()
    return {
        "total": total,
        "completed": completed,
        "percent": round(completed / total * 100) if total else 0,
    }


@dashboard_bp.route("/")
def index():
    tracks = list_tracks()
    streak = get_streak()
    due_cards = get_due_cards_count()
    total_due = sum(due_cards.values())
    progress = {t: get_track_progress(t) for t in tracks}

    # Smart scheduler: recommend what to study
    recommendation = _get_recommendation(tracks, due_cards, progress)

    return render_template(
        "dashboard.html",
        tracks=tracks,
        streak=streak,
        due_cards=due_cards,
        total_due=total_due,
        progress=progress,
        recommendation=recommendation,
    )


def _get_recommendation(
    tracks: list[str], due_cards: dict[str, int], progress: dict
) -> dict:
    """Smart scheduler — score each track and recommend what to study."""
    priority_weights = {"claude": 1.5, "python": 1.2, "japanese": 1.0}
    scores: dict[str, float] = {}

    for track in tracks:
        due = due_cards.get(track, 0)
        weight = priority_weights.get(track, 1.0)

        # Last session for this track
        last_session = (
            db.session.query(StudySession)
            .filter(StudySession.track == track)
            .order_by(StudySession.session_date.desc())
            .first()
        )
        days_since = (
            (date.today() - last_session.session_date).days if last_session else 7
        )

        score = (due * 3.0) + (weight * 2.0) + (days_since * 0.5)
        scores[track] = score

    if not scores:
        return {"track": None, "reason": "No content available yet"}

    best_track = max(scores, key=scores.get)
    due = due_cards.get(best_track, 0)

    if due > 0:
        reason = f"{due} cards due for review"
    else:
        reason = "Continue with new material"

    return {"track": best_track, "reason": reason}
