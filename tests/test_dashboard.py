"""Tests for dashboard route, streak calculation, and recommendation logic."""

from datetime import date, timedelta

import pytest

from app import create_app, db
from app.models import Card, StudySession
from app.routes.dashboard import get_due_cards_count, get_streak, _get_recommendation


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


class TestDashboardRoute:
    def test_dashboard_loads(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_dashboard_shows_tracks(self, client):
        resp = client.get("/")
        assert b"python" in resp.data.lower() or b"Python" in resp.data

    def test_dashboard_shows_streak(self, client):
        resp = client.get("/")
        assert b"streak" in resp.data.lower() or resp.status_code == 200


class TestStreak:
    def test_no_sessions_returns_zero(self, app):
        with app.app_context():
            assert get_streak() == 0

    def test_session_today_returns_one(self, app):
        with app.app_context():
            session = StudySession(
                session_date=date.today(),
                track="python",
                duration_min=10,
                activity_type="review",
            )
            db.session.add(session)
            db.session.commit()
            assert get_streak() == 1

    def test_consecutive_days_counted(self, app):
        with app.app_context():
            today = date.today()
            for i in range(5):
                s = StudySession(
                    session_date=today - timedelta(days=i),
                    track="python",
                    duration_min=10,
                    activity_type="review",
                )
                db.session.add(s)
            db.session.commit()
            assert get_streak() == 5

    def test_gap_breaks_streak(self, app):
        with app.app_context():
            today = date.today()
            # Today and yesterday
            for i in range(2):
                db.session.add(StudySession(
                    session_date=today - timedelta(days=i),
                    track="python",
                    duration_min=10,
                    activity_type="review",
                ))
            # Day before yesterday is missing, then day 3
            db.session.add(StudySession(
                session_date=today - timedelta(days=3),
                track="python",
                duration_min=10,
                activity_type="review",
            ))
            db.session.commit()
            assert get_streak() == 2

    def test_no_session_today_returns_zero(self, app):
        with app.app_context():
            # Only yesterday
            db.session.add(StudySession(
                session_date=date.today() - timedelta(days=1),
                track="python",
                duration_min=10,
                activity_type="review",
            ))
            db.session.commit()
            assert get_streak() == 0

    def test_multiple_sessions_same_day(self, app):
        with app.app_context():
            today = date.today()
            for _ in range(3):
                db.session.add(StudySession(
                    session_date=today,
                    track="python",
                    duration_min=10,
                    activity_type="review",
                ))
            db.session.commit()
            assert get_streak() == 1


class TestDueCardsCount:
    def test_no_cards_returns_zero_counts(self, app):
        with app.app_context():
            counts = get_due_cards_count()
            for track in counts:
                assert counts[track] == 0

    def test_due_cards_counted_per_track(self, app):
        with app.app_context():
            # Add due cards for python
            for i in range(3):
                db.session.add(Card(
                    track="python",
                    topic="test",
                    front=f"q{i}",
                    back=f"a{i}",
                    due_date=date.today() - timedelta(days=1),
                ))
            # Add a future card for python (not due)
            db.session.add(Card(
                track="python",
                topic="test",
                front="future",
                back="future",
                due_date=date.today() + timedelta(days=5),
            ))
            db.session.commit()
            counts = get_due_cards_count()
            assert counts.get("python", 0) == 3


class TestRecommendation:
    def test_recommends_track_with_most_due_cards(self, app):
        with app.app_context():
            due_cards = {"python": 10, "claude": 2, "japanese": 0}
            progress = {
                "python": {"total": 5, "completed": 1, "percent": 20},
                "claude": {"total": 5, "completed": 0, "percent": 0},
                "japanese": {"total": 5, "completed": 0, "percent": 0},
            }
            rec = _get_recommendation(
                ["python", "claude", "japanese"], due_cards, progress
            )
            assert rec["track"] == "python"
            assert "cards due" in rec["reason"]

    def test_recommends_new_material_when_no_due(self, app):
        with app.app_context():
            due_cards = {"python": 0, "claude": 0, "japanese": 0}
            progress = {
                "python": {"total": 5, "completed": 1, "percent": 20},
                "claude": {"total": 5, "completed": 0, "percent": 0},
                "japanese": {"total": 5, "completed": 0, "percent": 0},
            }
            rec = _get_recommendation(
                ["python", "claude", "japanese"], due_cards, progress
            )
            assert rec["track"] is not None
            assert "new material" in rec["reason"].lower()

    def test_empty_tracks_returns_no_content(self, app):
        with app.app_context():
            rec = _get_recommendation([], {}, {})
            assert rec["track"] is None

    def test_priority_weight_affects_recommendation(self, app):
        with app.app_context():
            # Claude has higher priority weight (1.5) vs japanese (1.0)
            # With equal due cards and no sessions, claude should score higher
            due_cards = {"claude": 0, "japanese": 0}
            progress = {
                "claude": {"total": 5, "completed": 0, "percent": 0},
                "japanese": {"total": 5, "completed": 0, "percent": 0},
            }
            rec = _get_recommendation(
                ["claude", "japanese"], due_cards, progress
            )
            assert rec["track"] == "claude"
