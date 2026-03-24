from datetime import datetime

from flask import Blueprint, abort, render_template

from app import db
from app.models import LessonProgress
from app.services.content import list_topics, load_lesson

lessons_bp = Blueprint("lessons", __name__, url_prefix="/lessons")


@lessons_bp.route("/<track>")
def track_index(track: str):
    topics = list_topics(track)
    if not topics:
        abort(404)

    # Get completion status for each topic
    for topic in topics:
        prog = db.session.query(LessonProgress).filter_by(
            track=track, topic=topic["slug"]
        ).first()
        topic["completed"] = prog.completed if prog else False

    return render_template("track_index.html", track=track, topics=topics)


@lessons_bp.route("/<track>/<topic_slug>")
def view_lesson(track: str, topic_slug: str):
    html_content = load_lesson(track, topic_slug)
    if html_content is None:
        abort(404)

    # Mark as started (create progress record if not exists)
    prog = db.session.query(LessonProgress).filter_by(
        track=track, topic=topic_slug
    ).first()
    if not prog:
        prog = LessonProgress(track=track, topic=topic_slug)
        db.session.add(prog)
        db.session.commit()

    return render_template(
        "lesson.html", track=track, topic_slug=topic_slug, content=html_content
    )


@lessons_bp.route("/<track>/<topic_slug>/complete", methods=["POST"])
def complete_lesson(track: str, topic_slug: str):
    prog = db.session.query(LessonProgress).filter_by(
        track=track, topic=topic_slug
    ).first()
    if not prog:
        prog = LessonProgress(track=track, topic=topic_slug)
        db.session.add(prog)
    prog.completed = True
    prog.completed_at = datetime.utcnow()
    db.session.commit()

    # Find next topic
    topics = list_topics(track)
    current_idx = next(
        (i for i, t in enumerate(topics) if t["slug"] == topic_slug), -1
    )
    next_topic = topics[current_idx + 1] if current_idx + 1 < len(topics) else None

    return render_template(
        "lesson_complete.html", track=track, next_topic=next_topic
    )
