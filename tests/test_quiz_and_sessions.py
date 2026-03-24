"""Tests for Phase 2: Quiz system, session tracking, and lesson flow."""

import json
from datetime import date

import pytest

from app import create_app, db
from app.models import Card, LessonProgress, StudySession


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["APP_TOKEN"] = ""  # Disable auth for tests
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


class TestQuizRoute:
    def test_quiz_page_loads(self, client):
        resp = client.get("/lessons/python/01_advanced_fundamentals/quiz")
        assert resp.status_code == 200
        assert b"quiz" in resp.data.lower()

    def test_quiz_404_for_missing_topic(self, client):
        resp = client.get("/lessons/python/nonexistent/quiz")
        assert resp.status_code == 404

    def test_quiz_submit_correct_answers(self, client):
        resp = client.post(
            "/lessons/python/01_advanced_fundamentals/quiz/submit",
            data=json.dumps({"answers": [0, 0]}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] == 2
        assert data["correct"] == 2
        assert data["passed"] is True

    def test_quiz_submit_wrong_answers(self, client):
        resp = client.post(
            "/lessons/python/01_advanced_fundamentals/quiz/submit",
            data=json.dumps({"answers": [3, 3]}),
            content_type="application/json",
        )
        data = resp.get_json()
        assert data["correct"] == 0
        assert data["passed"] is False

    def test_quiz_pass_creates_study_session(self, app, client):
        with app.app_context():
            client.post(
                "/lessons/python/01_advanced_fundamentals/quiz/submit",
                data=json.dumps({"answers": [0, 0]}),
                content_type="application/json",
            )
            sessions = db.session.query(StudySession).all()
            assert len(sessions) == 1
            assert sessions[0].track == "python"
            assert sessions[0].activity_type == "lesson"

    def test_quiz_fail_no_study_session(self, app, client):
        with app.app_context():
            client.post(
                "/lessons/python/01_advanced_fundamentals/quiz/submit",
                data=json.dumps({"answers": [3, 3]}),
                content_type="application/json",
            )
            sessions = db.session.query(StudySession).all()
            assert len(sessions) == 0


class TestLessonCompletion:
    def test_complete_creates_study_session(self, app, client):
        with app.app_context():
            # View lesson first to set start time
            client.get("/lessons/python/01_advanced_fundamentals")
            # Complete it
            client.post("/lessons/python/01_advanced_fundamentals/complete")
            sessions = db.session.query(StudySession).all()
            assert len(sessions) == 1
            assert sessions[0].activity_type == "lesson"

    def test_complete_marks_progress(self, app, client):
        with app.app_context():
            client.get("/lessons/python/01_advanced_fundamentals")
            client.post("/lessons/python/01_advanced_fundamentals/complete")
            prog = db.session.query(LessonProgress).filter_by(
                track="python", topic="01_advanced_fundamentals"
            ).first()
            assert prog is not None
            assert prog.completed is True


class TestReviewSessionTracking:
    def test_complete_review_creates_session(self, app, client):
        with app.app_context():
            resp = client.post(
                "/flashcards/review/python/complete",
                data=json.dumps({"cards_reviewed": 10, "duration_sec": 300}),
                content_type="application/json",
            )
            assert resp.status_code == 200
            sessions = db.session.query(StudySession).all()
            assert len(sessions) == 1
            assert sessions[0].cards_reviewed == 10
            assert sessions[0].duration_min == 5
            assert sessions[0].activity_type == "review"


class TestLogout:
    def test_logout_redirects_to_login(self, client):
        resp = client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]
