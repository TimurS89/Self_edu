from datetime import date, datetime

from flask import Blueprint, abort, jsonify, render_template, request, session

from app import db
from app.models import LessonProgress, StudySession
from app.services.content import list_topics, load_lesson, load_quiz

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

    # Track lesson start time
    session["lesson_start"] = datetime.utcnow().isoformat()

    # Check if quiz exists for this topic
    quiz_questions = load_quiz(track, topic_slug)
    has_quiz = len(quiz_questions) > 0

    return render_template(
        "lesson.html",
        track=track,
        topic_slug=topic_slug,
        content=html_content,
        has_quiz=has_quiz,
    )


@lessons_bp.route("/<track>/<topic_slug>/quiz")
def take_quiz(track: str, topic_slug: str):
    """Show quiz for a topic."""
    questions = load_quiz(track, topic_slug)
    if not questions:
        abort(404)

    return render_template(
        "quiz.html", track=track, topic_slug=topic_slug, questions=questions
    )


@lessons_bp.route("/<track>/<topic_slug>/quiz/submit", methods=["POST"])
def submit_quiz(track: str, topic_slug: str):
    """Grade quiz and return results."""
    questions = load_quiz(track, topic_slug)
    if not questions:
        abort(404)

    data = request.get_json()
    answers = data.get("answers", [])

    correct = 0
    results = []
    for i, question in enumerate(questions):
        user_answer = answers[i] if i < len(answers) else -1
        is_correct = user_answer == question["answer"]
        if is_correct:
            correct += 1
        results.append({
            "correct": is_correct,
            "user_answer": user_answer,
            "correct_answer": question["answer"],
            "explanation": question.get("explanation", ""),
        })

    total = len(questions)
    passed = correct >= (total / 2)  # Pass with 50%+

    # If passed, mark lesson complete and record session
    if passed:
        _complete_lesson(track, topic_slug)

    return jsonify({
        "correct": correct,
        "total": total,
        "passed": passed,
        "results": results,
    })


@lessons_bp.route("/<track>/<topic_slug>/complete", methods=["POST"])
def complete_lesson(track: str, topic_slug: str):
    _complete_lesson(track, topic_slug)

    # Find next topic
    topics = list_topics(track)
    current_idx = next(
        (i for i, t in enumerate(topics) if t["slug"] == topic_slug), -1
    )
    next_topic = topics[current_idx + 1] if current_idx + 1 < len(topics) else None

    return render_template(
        "lesson_complete.html", track=track, next_topic=next_topic
    )


def _complete_lesson(track: str, topic_slug: str) -> None:
    """Mark lesson complete, track time, and record study session."""
    prog = db.session.query(LessonProgress).filter_by(
        track=track, topic=topic_slug
    ).first()
    if not prog:
        prog = LessonProgress(track=track, topic=topic_slug)
        db.session.add(prog)
    prog.completed = True
    prog.completed_at = datetime.utcnow()

    # Calculate time spent
    start_iso = session.pop("lesson_start", None)
    duration_min = 0
    if start_iso:
        start_time = datetime.fromisoformat(start_iso)
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        prog.time_spent_sec = int(elapsed)
        duration_min = max(1, int(elapsed / 60))

    # Record study session
    study = StudySession(
        session_date=date.today(),
        track=track,
        duration_min=duration_min,
        cards_reviewed=0,
        activity_type="lesson",
    )
    db.session.add(study)
    db.session.commit()
