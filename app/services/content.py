"""Content loader — reads markdown lessons and YAML flashcards/quizzes from content/ directory."""

from pathlib import Path
from typing import Any

import markdown
import yaml
from flask import current_app


def get_content_dir() -> Path:
    return current_app.config["CONTENT_DIR"]


def _safe_path(base: Path, *parts: str) -> Path:
    """Resolve a path and ensure it stays within the base directory."""
    resolved = (base / Path(*parts)).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise ValueError("Path traversal detected")
    return resolved


def list_tracks() -> list[str]:
    """Return available track names (directory names under content/)."""
    content_dir = get_content_dir()
    return sorted(d.name for d in content_dir.iterdir() if d.is_dir())


def list_topics(track: str) -> list[dict[str, str]]:
    """Return topics for a track, sorted by directory name prefix."""
    track_dir = _safe_path(get_content_dir(), track)
    if not track_dir.exists():
        return []
    topics = []
    for d in sorted(track_dir.iterdir()):
        if d.is_dir():
            # Extract display name from directory name (e.g., "01_api_basics" -> "API Basics")
            parts = d.name.split("_", 1)
            order = parts[0]
            name = parts[1].replace("_", " ").title() if len(parts) > 1 else d.name
            topics.append({"slug": d.name, "name": name, "order": order})
    return topics


def load_lesson(track: str, topic_slug: str) -> str | None:
    """Load a lesson markdown file and return rendered HTML."""
    lesson_path = _safe_path(get_content_dir(), track, topic_slug, "lesson.md")
    if not lesson_path.exists():
        return None
    md_text = lesson_path.read_text(encoding="utf-8")
    return markdown.markdown(md_text, extensions=["fenced_code", "tables", "codehilite"])


def load_flashcards(track: str, topic_slug: str) -> list[dict[str, Any]]:
    """Load flashcard definitions from YAML."""
    cards_path = _safe_path(get_content_dir(), track, topic_slug, "flashcards.yaml")
    if not cards_path.exists():
        return []
    data = yaml.safe_load(cards_path.read_text(encoding="utf-8"))
    return data.get("cards", []) if data else []


def load_quiz(track: str, topic_slug: str) -> list[dict[str, Any]]:
    """Load quiz questions from YAML."""
    quiz_path = _safe_path(get_content_dir(), track, topic_slug, "quiz.yaml")
    if not quiz_path.exists():
        return []
    data = yaml.safe_load(quiz_path.read_text(encoding="utf-8"))
    return data.get("questions", []) if data else []
