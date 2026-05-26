from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal"


def _import_settings_with_env(env_overrides: dict[str, str | None]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PORTAL_DATABASE_URL", None)
    env.pop("DATABASE_URL", None)
    env.pop("ROB_PORTAL_SECRET_KEY", None)
    env.pop("ROB_PORTAL_ENABLED", None)
    env.pop("ROB_PORTAL_ENV_FILE", None)
    for key, value in env_overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value

    code = f"""
import sys
import types
sys.path.insert(0, {str(PORTAL_DIR)!r})
sys.modules["dj_database_url"] = types.SimpleNamespace(parse=lambda *_args, **_kwargs: {{"ENGINE": "django.db.backends.postgresql", "NAME": "rob_dev"}})
import rob_portal.settings as settings
print(settings.DATABASES["default"]["ENGINE"])
"""
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_portal_enabled_without_database_url_fails_clearly():
    result = _import_settings_with_env(
        {
            "ROB_PORTAL_ENABLED": "true",
            "ROB_PORTAL_SECRET_KEY": "real-secret-value",
        }
    )
    assert result.returncode != 0
    assert "ROB_PORTAL_ENABLED=true requires PORTAL_DATABASE_URL or DATABASE_URL." in result.stderr


def test_portal_enabled_with_sqlite_url_fails_clearly():
    result = _import_settings_with_env(
        {
            "ROB_PORTAL_ENABLED": "true",
            "ROB_PORTAL_SECRET_KEY": "real-secret-value",
            "PORTAL_DATABASE_URL": "sqlite:////tmp/portal.db",
        }
    )
    assert result.returncode != 0
    assert "ROB_PORTAL_ENABLED=true requires a PostgreSQL PORTAL_DATABASE_URL or DATABASE_URL." in result.stderr


def test_portal_enabled_without_real_secret_key_fails_clearly():
    result = _import_settings_with_env(
        {
            "ROB_PORTAL_ENABLED": "true",
            "PORTAL_DATABASE_URL": "postgresql://portal:pass@localhost:5432/rob_dev",
            "ROB_PORTAL_SECRET_KEY": "rob-portal-dev-only-change-me",
        }
    )
    assert result.returncode != 0
    assert "ROB_PORTAL_ENABLED=true requires ROB_PORTAL_SECRET_KEY to be set to a non-default value." in result.stderr


def test_portal_disabled_allows_local_sqlite_fallback():
    result = _import_settings_with_env(
        {
            "ROB_PORTAL_ENABLED": "false",
            "ROB_PORTAL_SECRET_KEY": "",
        }
    )
    assert result.returncode == 0
    assert "django.db.backends.sqlite3" in result.stdout
