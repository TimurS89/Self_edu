"""Tests for authentication middleware and login flow."""

import json

import pytest

from app import create_app, db


@pytest.fixture
def app_with_auth():
    """App with auth enabled."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["APP_TOKEN"] = "test-secret-token"
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client_with_auth(app_with_auth):
    return app_with_auth.test_client()


@pytest.fixture
def app_no_auth():
    """App with auth disabled."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["APP_TOKEN"] = ""
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client_no_auth(app_no_auth):
    return app_no_auth.test_client()


class TestAuthMiddleware:
    def test_unauthenticated_redirects_to_login(self, client_with_auth):
        resp = client_with_auth.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_unauthenticated_lesson_redirects(self, client_with_auth):
        resp = client_with_auth.get(
            "/lessons/python", follow_redirects=False
        )
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_login_page_accessible_without_auth(self, client_with_auth):
        resp = client_with_auth.get("/login")
        assert resp.status_code == 200
        assert b"Self Edu" in resp.data

    def test_static_paths_accessible_without_auth(self, client_with_auth):
        # Static path should not redirect (may 404 if file missing, but not 302)
        resp = client_with_auth.get("/static/css/style.css", follow_redirects=False)
        assert resp.status_code != 302

    def test_authenticated_session_allows_access(self, client_with_auth):
        # Login first
        client_with_auth.post("/login", data={"token": "test-secret-token"})
        resp = client_with_auth.get("/", follow_redirects=False)
        assert resp.status_code == 200

    def test_no_auth_configured_allows_access(self, client_no_auth):
        resp = client_no_auth.get("/", follow_redirects=False)
        assert resp.status_code == 200


class TestLoginFlow:
    def test_correct_token_logs_in(self, client_with_auth):
        resp = client_with_auth.post(
            "/login",
            data={"token": "test-secret-token"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        # Should redirect to dashboard
        assert resp.headers["Location"] in ("/", "http://localhost/")

    def test_incorrect_token_shows_error(self, client_with_auth):
        resp = client_with_auth.post(
            "/login", data={"token": "wrong-token"}
        )
        assert resp.status_code == 200
        assert b"Invalid token" in resp.data

    def test_empty_token_shows_error(self, client_with_auth):
        resp = client_with_auth.post("/login", data={"token": ""})
        assert resp.status_code == 200
        assert b"Invalid token" in resp.data

    def test_no_auth_configured_auto_redirects(self, client_no_auth):
        resp = client_no_auth.get("/login", follow_redirects=False)
        assert resp.status_code == 302

    def test_logout_clears_session(self, client_with_auth):
        # Login
        client_with_auth.post("/login", data={"token": "test-secret-token"})
        # Verify access
        resp = client_with_auth.get("/", follow_redirects=False)
        assert resp.status_code == 200
        # Logout
        client_with_auth.get("/logout")
        # Should be redirected now
        resp = client_with_auth.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]
