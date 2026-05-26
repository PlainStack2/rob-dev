from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def setup_django() -> None:
    pytest.importorskip("django")

    repo_root = Path(__file__).resolve().parents[2]
    portal_dir = repo_root / "portal"
    if str(portal_dir) not in sys.path:
        sys.path.insert(0, str(portal_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rob_portal.settings")
    os.environ.setdefault("ROB_PORTAL_ENABLED", "true")
    os.environ.setdefault("ROB_PORTAL_SECRET_KEY", "test-secret-key")
    os.environ.setdefault("ROB_PORTAL_ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
    os.environ.setdefault("ROB_PORTAL_SUPERADMIN_USER_IDS", "1299308718009356289")
    os.environ.setdefault("DISCORD_CLIENT_ID", "test-client-id")
    os.environ.setdefault("DISCORD_CLIENT_SECRET", "test-client-secret")
    os.environ.setdefault("DISCORD_REDIRECT_URI", "http://localhost/portal/auth/discord/callback")
    os.environ.setdefault("PORTAL_DATABASE_URL", "postgresql://portal:portal@127.0.0.1:5432/rob_dev")

    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()
