"""Tests for flashcard routes: review page, card rating, and seeding."""

import json
from datetime import date, timedelta

import pytest

from app import create_app, db
from app.models import Card, CardReview


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["APP_TOKEN"] = ""
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def _seed_card(track="python", front="test q", back="test a", due_days_ago=1):
    card = Card(
        track=track,
        topic="test_topic",
        front=front,
        back=back,
        due_date=date.today() - timedelta(days=due_days_ago),
    )
    db.session.add(card)
    db.session.commit()
    return card


class TestReviewPage:
    def test_review_shows_due_cards(self, app, client):
        with app.app_context():
            _seed_card()
            resp = client.get("/flashcards/review/python")
            assert resp.status_code == 200

    def test_review_no_due_cards_shows_message(self, app, client):
        with app.app_context():
            # Add a card due in the future
            card = Card(
                track="python",
                topic="test",
                front="q",
                back="a",
                due_date=date.today() + timedelta(days=5),
            )
            db.session.add(card)
            db.session.commit()
            resp = client.get("/flashcards/review/python")
            assert resp.status_code == 200
            assert b"no" in resp.data.lower() or b"No" in resp.data


class TestRateCard:
    def test_rate_card_good(self, app, client):
        with app.app_context():
            card = _seed_card()
            resp = client.post(
                f"/flashcards/review/{card.id}/rate",
                data=json.dumps({"rating": 3}),
                content_type="application/json",
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["ok"] is True
            assert "next_due" in data

    def test_rate_card_creates_review(self, app, client):
        with app.app_context():
            card = _seed_card()
            client.post(
                f"/flashcards/review/{card.id}/rate",
                data=json.dumps({"rating": 3, "response_time_ms": 1500}),
                content_type="application/json",
            )
            reviews = db.session.query(CardReview).filter_by(card_id=card.id).all()
            assert len(reviews) == 1
            assert reviews[0].rating == 3
            assert reviews[0].response_time_ms == 1500

    def test_rate_card_updates_scheduling(self, app, client):
        with app.app_context():
            card = _seed_card()
            old_due = card.due_date
            client.post(
                f"/flashcards/review/{card.id}/rate",
                data=json.dumps({"rating": 3}),
                content_type="application/json",
            )
            db.session.refresh(card)
            assert card.due_date > old_due
            assert card.reps == 1

    def test_rate_card_invalid_rating_rejected(self, app, client):
        with app.app_context():
            card = _seed_card()
            resp = client.post(
                f"/flashcards/review/{card.id}/rate",
                data=json.dumps({"rating": 0}),
                content_type="application/json",
            )
            assert resp.status_code == 400

    def test_rate_card_rating_5_rejected(self, app, client):
        with app.app_context():
            card = _seed_card()
            resp = client.post(
                f"/flashcards/review/{card.id}/rate",
                data=json.dumps({"rating": 5}),
                content_type="application/json",
            )
            assert resp.status_code == 400

    def test_rate_card_negative_rating_rejected(self, app, client):
        with app.app_context():
            card = _seed_card()
            resp = client.post(
                f"/flashcards/review/{card.id}/rate",
                data=json.dumps({"rating": -1}),
                content_type="application/json",
            )
            assert resp.status_code == 400

    def test_rate_nonexistent_card_404(self, client):
        resp = client.post(
            "/flashcards/review/99999/rate",
            data=json.dumps({"rating": 3}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_all_valid_ratings(self, app, client):
        with app.app_context():
            for rating in (1, 2, 3, 4):
                card = _seed_card(front=f"q{rating}", back=f"a{rating}")
                resp = client.post(
                    f"/flashcards/review/{card.id}/rate",
                    data=json.dumps({"rating": rating}),
                    content_type="application/json",
                )
                assert resp.status_code == 200


    def test_rate_card_missing_json_body(self, app, client):
        with app.app_context():
            card = _seed_card()
            resp = client.post(
                f"/flashcards/review/{card.id}/rate",
                content_type="application/json",
            )
            assert resp.status_code == 400

    def test_rate_card_missing_rating_key(self, app, client):
        with app.app_context():
            card = _seed_card()
            resp = client.post(
                f"/flashcards/review/{card.id}/rate",
                data=json.dumps({"response_time_ms": 1000}),
                content_type="application/json",
            )
            assert resp.status_code == 400

    def test_complete_review_missing_json_body(self, app, client):
        with app.app_context():
            resp = client.post(
                "/flashcards/review/python/complete",
                content_type="application/json",
            )
            assert resp.status_code == 200


class TestSeedCards:
    def test_seed_track_topic(self, app, client):
        with app.app_context():
            resp = client.post("/flashcards/seed/python/01_advanced_fundamentals")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["added"] > 0
            assert data["total"] > 0

    def test_seed_is_idempotent(self, app, client):
        with app.app_context():
            resp1 = client.post("/flashcards/seed/python/01_advanced_fundamentals")
            data1 = resp1.get_json()
            resp2 = client.post("/flashcards/seed/python/01_advanced_fundamentals")
            data2 = resp2.get_json()
            assert data2["added"] == 0
            assert data2["total"] == data1["total"]

    def test_seed_all(self, app, client):
        with app.app_context():
            resp = client.post("/flashcards/seed-all")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["added"] > 0

    def test_seed_all_is_idempotent(self, app, client):
        with app.app_context():
            client.post("/flashcards/seed-all")
            resp2 = client.post("/flashcards/seed-all")
            data2 = resp2.get_json()
            assert data2["added"] == 0
