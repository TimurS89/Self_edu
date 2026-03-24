from datetime import date, datetime

from flask import Blueprint, abort, jsonify, render_template, request

from app import db
from app.models import Card, CardReview, StudySession
from app.services.content import list_tracks, load_flashcards, list_topics

flashcards_bp = Blueprint("flashcards", __name__, url_prefix="/flashcards")


@flashcards_bp.route("/seed/<track>/<topic_slug>", methods=["POST"])
def seed_cards(track: str, topic_slug: str):
    """Import flashcards from YAML into the database (idempotent)."""
    cards_data = load_flashcards(track, topic_slug)
    added = 0
    for card_data in cards_data:
        existing = db.session.query(Card).filter_by(
            track=track, topic=topic_slug, front=card_data["front"]
        ).first()
        if not existing:
            card = Card(
                track=track,
                topic=topic_slug,
                front=card_data["front"],
                back=card_data["back"],
                tags=",".join(card_data.get("tags", [])),
            )
            db.session.add(card)
            added += 1
    db.session.commit()
    return jsonify({"added": added, "total": len(cards_data)})


@flashcards_bp.route("/review/<track>")
def review(track: str):
    """Show the flashcard review session for a track."""
    today = date.today()

    # Get due cards, ordered by due date (most overdue first)
    due_cards = (
        db.session.query(Card)
        .filter(Card.track == track, Card.due_date <= today)
        .order_by(Card.due_date.asc())
        .limit(20)
        .all()
    )

    if not due_cards:
        return render_template("no_cards.html", track=track)

    # Serialize cards for the template
    cards = [
        {"id": c.id, "front": c.front, "back": c.back, "state": c.state}
        for c in due_cards
    ]

    return render_template("flashcard.html", track=track, cards=cards)


@flashcards_bp.route("/review/<int:card_id>/rate", methods=["POST"])
def rate_card(card_id: int):
    """Rate a card after review. Updates SRS scheduling."""
    from app.services.srs import schedule_review

    card = db.session.get(Card, card_id)
    if not card:
        abort(404)

    data = request.get_json()
    rating = int(data.get("rating", 3))  # 1=again, 2=hard, 3=good, 4=easy

    # Record the review
    review = CardReview(
        card_id=card.id,
        rating=rating,
        response_time_ms=data.get("response_time_ms"),
    )
    db.session.add(review)

    # Update card scheduling via SRS algorithm
    schedule_review(card, rating)
    db.session.commit()

    return jsonify({"ok": True, "next_due": card.due_date.isoformat()})


@flashcards_bp.route("/review/<track>/complete", methods=["POST"])
def complete_review(track: str):
    """Record a completed review session."""
    data = request.get_json()
    cards_reviewed = data.get("cards_reviewed", 0)
    duration_sec = data.get("duration_sec", 0)
    duration_min = max(1, int(duration_sec / 60))

    study = StudySession(
        session_date=date.today(),
        track=track,
        duration_min=duration_min,
        cards_reviewed=cards_reviewed,
        activity_type="review",
    )
    db.session.add(study)
    db.session.commit()

    return jsonify({"ok": True})


@flashcards_bp.route("/seed-all", methods=["POST"])
def seed_all():
    """Seed all flashcards from all tracks/topics."""
    total_added = 0
    for track in list_tracks():
        for topic in list_topics(track):
            cards_data = load_flashcards(track, topic["slug"])
            for card_data in cards_data:
                existing = db.session.query(Card).filter_by(
                    track=track, topic=topic["slug"], front=card_data["front"]
                ).first()
                if not existing:
                    card = Card(
                        track=track,
                        topic=topic["slug"],
                        front=card_data["front"],
                        back=card_data["back"],
                        tags=",".join(card_data.get("tags", [])),
                    )
                    db.session.add(card)
                    total_added += 1
    db.session.commit()
    return jsonify({"added": total_added})
