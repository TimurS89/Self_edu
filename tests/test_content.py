"""Tests for content loader and path traversal protection."""

import pytest

from app import create_app, db
from app.services.content import (
    _safe_path,
    list_tracks,
    list_topics,
    load_flashcards,
    load_lesson,
    load_quiz,
)


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


class TestPathTraversal:
    def test_safe_path_allows_valid_path(self, app):
        with app.app_context():
            from app.services.content import get_content_dir
            base = get_content_dir()
            result = _safe_path(base, "python", "01_advanced_fundamentals")
            assert "python" in str(result)
            assert "01_advanced_fundamentals" in str(result)

    def test_safe_path_blocks_parent_traversal(self, app):
        with app.app_context():
            from app.services.content import get_content_dir
            base = get_content_dir()
            with pytest.raises(ValueError, match="Path traversal"):
                _safe_path(base, "..", "..", "etc", "passwd")

    def test_safe_path_blocks_absolute_path_component(self, app):
        with app.app_context():
            from app.services.content import get_content_dir
            base = get_content_dir()
            with pytest.raises((ValueError, TypeError)):
                _safe_path(base, "..", "config.py")

    def test_list_topics_rejects_traversal(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="Path traversal"):
                list_topics("../../etc")

    def test_load_lesson_rejects_traversal(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="Path traversal"):
                load_lesson("../../etc", "passwd")

    def test_load_flashcards_rejects_traversal(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="Path traversal"):
                load_flashcards("../../etc", "passwd")

    def test_load_quiz_rejects_traversal(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="Path traversal"):
                load_quiz("../../etc", "passwd")


class TestContentLoader:
    def test_list_tracks_returns_tracks(self, app):
        with app.app_context():
            tracks = list_tracks()
            assert "python" in tracks
            assert "claude" in tracks
            assert "japanese" in tracks

    def test_list_topics_returns_topics(self, app):
        with app.app_context():
            topics = list_topics("python")
            assert len(topics) >= 1
            assert topics[0]["slug"] == "01_advanced_fundamentals"
            assert "name" in topics[0]
            assert "order" in topics[0]

    def test_list_topics_nonexistent_track_returns_empty(self, app):
        with app.app_context():
            topics = list_topics("nonexistent_track")
            assert topics == []

    def test_load_lesson_returns_html(self, app):
        with app.app_context():
            html = load_lesson("python", "01_advanced_fundamentals")
            assert html is not None
            assert "<" in html  # Contains HTML tags

    def test_load_lesson_nonexistent_returns_none(self, app):
        with app.app_context():
            html = load_lesson("python", "nonexistent_topic")
            assert html is None

    def test_load_flashcards_returns_list(self, app):
        with app.app_context():
            cards = load_flashcards("python", "01_advanced_fundamentals")
            assert isinstance(cards, list)
            assert len(cards) > 0
            assert "front" in cards[0]
            assert "back" in cards[0]

    def test_load_flashcards_nonexistent_returns_empty(self, app):
        with app.app_context():
            cards = load_flashcards("python", "nonexistent_topic")
            assert cards == []

    def test_load_quiz_returns_questions(self, app):
        with app.app_context():
            questions = load_quiz("python", "01_advanced_fundamentals")
            assert isinstance(questions, list)
            assert len(questions) > 0
            assert "question" in questions[0]
            assert "choices" in questions[0]
            assert "answer" in questions[0]

    def test_load_quiz_nonexistent_returns_empty(self, app):
        with app.app_context():
            questions = load_quiz("python", "nonexistent_topic")
            assert questions == []
