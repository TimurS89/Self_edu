from functools import wraps

from flask import Flask, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)

    # Simple token-based auth
    @app.before_request
    def check_auth() -> None:
        token = app.config.get("APP_TOKEN")
        if not token:
            return  # No auth configured
        if request.endpoint == "auth.login" or request.path.startswith("/static"):
            return
        if session.get("authenticated"):
            return
        if request.endpoint and request.endpoint != "auth.login":
            return redirect(url_for("auth.login"))

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.lessons import lessons_bp
    from app.routes.flashcards import flashcards_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(lessons_bp)
    app.register_blueprint(flashcards_bp)

    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    return app
