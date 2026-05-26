from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client, RequestFactory, override_settings

from rob_admin import views


def _attach_session(request) -> None:
    middleware = SessionMiddleware(lambda _req: None)
    middleware.process_request(request)
    request.session.save()


def _unwrap_view(func):
    current = func
    while hasattr(current, "__wrapped__"):
        current = current.__wrapped__
    return current


def test_portal_disabled_returns_404():
    client = Client()
    with override_settings(ROB_PORTAL_ENABLED=False):
        response = client.get("/portal/login/")
    assert response.status_code == 404
    assert b"disabled" in response.content.lower()


def test_django_admin_requires_authentication_redirects_to_portal_login():
    client = Client()
    response = client.get("/portal/admin/")
    assert response.status_code == 302
    assert "/portal/admin/login/" in response["Location"]


def test_discord_oauth_callback_denies_non_superadmin(monkeypatch):
    request = RequestFactory().get("/portal/auth/discord/callback/?code=abc&state=state-1")
    request.user = AnonymousUser()
    _attach_session(request)
    request.session["portal_oauth_state"] = "state-1"

    monkeypatch.setattr(views, "_discord_exchange_code", lambda _code: "token")
    monkeypatch.setattr(views, "_discord_fetch_identity", lambda _token: {"id": "999", "username": "nope"})

    response = views.discord_auth_callback(request)
    assert response.status_code == 403
    assert b"restricted" in response.content.lower()


def test_discord_oauth_callback_allows_superadmin(monkeypatch):
    request = RequestFactory().get("/portal/auth/discord/callback/?code=abc&state=state-2")
    request.user = AnonymousUser()
    _attach_session(request)
    request.session["portal_oauth_state"] = "state-2"
    request.session["portal_oauth_next"] = "/portal/admin/"

    monkeypatch.setattr(views, "_discord_exchange_code", lambda _code: "token")
    monkeypatch.setattr(
        views,
        "_discord_fetch_identity",
        lambda _token: {
            "id": "1299308718009356289",
            "username": "pat",
            "global_name": "Pat",
        },
    )
    monkeypatch.setattr(views, "_sync_django_user", lambda _identity: SimpleNamespace(get_username=lambda: "discord_1"))
    monkeypatch.setattr(views, "auth_login", lambda *_args, **_kwargs: None)

    response = views.discord_auth_callback(request)
    assert response.status_code == 302
    assert response["Location"] == "/portal/admin/"
    assert request.session["portal_discord_user_id"] == 1299308718009356289


def test_database_page_does_not_expose_raw_database_url(monkeypatch):
    request = RequestFactory().get("/portal/database/")
    request.user = SimpleNamespace(is_authenticated=True, get_username=lambda: "discord_1")
    _attach_session(request)
    request.session["portal_discord_user_id"] = 1299308718009356289
    request.session["portal_discord_display_name"] = "Pat"

    raw_view = _unwrap_view(views.database_view)
    response = raw_view(request)
    body = response.content.decode("utf-8")
    assert "postgresql://" not in body


def test_bot_ops_health_unavailable_does_not_crash_dashboard(monkeypatch):
    request = RequestFactory().get("/portal/dashboard/")
    request.user = SimpleNamespace(is_authenticated=True, get_username=lambda: "discord_1")
    _attach_session(request)
    request.session["portal_discord_user_id"] = 1299308718009356289
    request.session["portal_discord_display_name"] = "Pat"

    class _BrokenClient:
        def health(self):
            raise RuntimeError("offline")

    monkeypatch.setattr(views, "_build_bot_ops_client", lambda: _BrokenClient())
    raw_view = _unwrap_view(views.dashboard_view)
    response = raw_view(request)
    assert response.status_code == 200


def test_refresh_public_names_action_requires_superadmin():
    request = RequestFactory().post(
        "/portal/leaderboards/",
        data={"intent": "refresh_names", "guild_id": "123"},
    )
    request.user = SimpleNamespace(is_authenticated=True, get_username=lambda: "discord_2")
    _attach_session(request)
    request.session["portal_discord_user_id"] = 42
    response = views.leaderboards_view(request)
    assert response.status_code == 403


def test_leaderboard_actions_template_includes_csrf_tokens():
    repo_root = Path(__file__).resolve().parents[2]
    template_path = repo_root / "portal" / "rob_admin" / "templates" / "rob_admin" / "leaderboards.html"
    content = template_path.read_text(encoding="utf-8")
    assert "{% csrf_token %}" in content


def test_leaderboard_actions_reject_non_post_mutations():
    request = RequestFactory().put("/portal/leaderboards/")
    request.user = SimpleNamespace(is_authenticated=True, get_username=lambda: "discord_1")
    _attach_session(request)
    request.session["portal_discord_user_id"] = 1299308718009356289
    response = views.leaderboards_view(request)
    assert response.status_code == 405
