import os
from pathlib import Path

basedir = Path(__file__).parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    APP_TOKEN = os.environ.get("APP_TOKEN", "")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{basedir / 'selfedu.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CONTENT_DIR = basedir / "content"
