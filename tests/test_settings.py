from __future__ import annotations

from rob.config.settings import load_base_settings, load_bot_settings, load_webhook_settings
from rob.services.registration_service import sanitize_webhook_base_url


def test_load_base_settings_only_requires_database(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/db")
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)

    settings = load_base_settings()

    assert settings.database_url == "postgresql://example/db"
    assert settings.app_env == "dev"


def test_load_bot_settings_requires_discord_token(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/db")
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)

    try:
        load_bot_settings()
    except RuntimeError as exc:
        assert "DISCORD_TOKEN" in str(exc)
    else:
        raise AssertionError("Expected DISCORD_TOKEN requirement to fail.")


def test_load_webhook_settings_does_not_require_discord_token(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/db")
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)

    settings = load_webhook_settings()

    assert settings.database_url == "postgresql://example/db"
    assert settings.throne_webhook_require_signature is True



def test_sanitize_webhook_base_url_handles_bad_equals_quotes_and_slash():
    raw = "  '=https://rob-dev.barecoding.com/'  "
    assert sanitize_webhook_base_url(raw) == "https://rob-dev.barecoding.com"


def test_load_webhook_url_sanitizes_when_generating_registration_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/db")
    monkeypatch.setenv("THRONE_WEBHOOK_BASE_URL", "==https://rob-dev.barecoding.com/")
    settings = load_webhook_settings()
    assert sanitize_webhook_base_url(settings.throne_webhook_base_url) == "https://rob-dev.barecoding.com"
