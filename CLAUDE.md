# CLAUDE.md — Self Education App

## Project Overview

A personal self-education application with three learning tracks, designed for daily 20-40 minute study sessions on iPhone and Windows PC.

### Learning Goals

1. **Python** (Intermediate → AI/ML Expert) — Advanced concepts, data science, ML/DL, building AI tools
2. **Claude/AI** (Beginner → Full Expert) — API mastery, prompt engineering, agents, production systems — **highest priority**
3. **Japanese** (JLPT N5 → N3) — Kanji, vocabulary, grammar, reading comprehension

## Tech Stack

- **Framework**: Flask 3.x with Jinja2 templates
- **Database**: SQLAlchemy + SQLite
- **SRS Algorithm**: FSRS-inspired (stability/difficulty model, superior to SM-2)
- **Content**: Markdown lessons + YAML flashcards/quizzes
- **Hosting**: Render.com free tier (auto-deploys from GitHub)
- **Auth**: Simple token-based (single `APP_TOKEN` env var)
- **Frontend**: Mobile-first CSS, vanilla JS (no frameworks)

## Project Structure

```
Self_edu/
├── CLAUDE.md                    # Project conventions
├── requirements.txt             # Python dependencies
├── config.py                    # App configuration
├── Procfile                     # Render deployment
├── render.yaml                  # Render config
├── .gitignore
│
├── app/                         # Flask application
│   ├── __init__.py              # App factory + auth middleware
│   ├── models.py                # SQLAlchemy models (Card, CardReview, etc.)
│   ├── routes/
│   │   ├── auth.py              # Token login
│   │   ├── dashboard.py         # Home + smart scheduler
│   │   ├── lessons.py           # Lesson viewing + completion
│   │   └── flashcards.py        # SRS review + card seeding
│   ├── services/
│   │   ├── srs.py               # FSRS-inspired spaced repetition
│   │   └── content.py           # Markdown/YAML content loader
│   ├── templates/               # Jinja2 (mobile-first)
│   └── static/                  # CSS + JS
│
├── content/                     # Learning materials (markdown + YAML)
│   ├── python/                  # Topics: 01_advanced_fundamentals, ...
│   ├── claude/                  # Topics: 01_api_basics, ...
│   └── japanese/                # Topics: 01_hiragana_review, ...
│
├── cli/                         # PC-only CLI tool (future)
└── tests/                       # pytest tests
```

## Learning Science Principles

This app is built on evidence-based learning research:

- **FSRS Spaced Repetition** — Stability/difficulty model (replaces SM-2), adapts per-card
- **Active Recall** — Every lesson ends with quiz; flashcards force retrieval
- **Smart Scheduler** — Scores tracks by: overdue cards (3x), priority weight, days since last study
- **Habit Formation** — Streak counter, zero-friction "Start Session" button, 2-minute rule
- **Interleaving** — Mix card types within sessions, rotate subjects across days
- **Desirable Difficulties** — Difficulty auto-adjusts; reverse cards for mastery

## Development Conventions

- Python code follows **PEP 8** style
- Use **type hints** for function signatures
- Write **docstrings** for public functions and classes
- Keep modules focused and small
- Use `pytest` for testing
- Commit messages should be clear and descriptive

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run the app locally
flask run

# Seed flashcards into database
curl -X POST http://localhost:5000/flashcards/seed-all
```

## Content Format

### Lessons: `content/<track>/<topic>/lesson.md`
Standard markdown rendered to HTML.

### Flashcards: `content/<track>/<topic>/flashcards.yaml`
```yaml
cards:
  - front: "Question"
    back: "Answer"
    tags: [topic, subtopic]
```

### Quizzes: `content/<track>/<topic>/quiz.yaml`
```yaml
questions:
  - type: multiple_choice
    question: "Question text"
    choices: ["A", "B", "C", "D"]
    answer: 0  # index
    explanation: "Why this is correct"
```

## Adding New Content

1. Create a new directory under `content/<track>/` with format `NN_topic_name/`
2. Add `lesson.md`, `flashcards.yaml`, and optionally `quiz.yaml`
3. Push to GitHub — Render auto-deploys
4. Visit `/flashcards/seed-all` to import new cards into the database

## Monthly Updates

Claude and Python tracks should be reviewed monthly for:
- New API features, model releases (Claude)
- New Python features, library updates (Python)
- Add new lessons/cards as needed
