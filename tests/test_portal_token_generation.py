from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_portal_leaderboard_token_generation_uses_token_urlsafe():
    source = (REPO_ROOT / "portal" / "rob_admin" / "views.py").read_text(encoding="utf-8")
    assert "secrets.token_urlsafe(32)" in source
    assert "secrets.token_hex(16)" not in source


def test_portal_admin_rotate_token_uses_token_urlsafe():
    source = (REPO_ROOT / "portal" / "rob_admin" / "admin.py").read_text(encoding="utf-8")
    assert "secrets.token_urlsafe(32)" in source
    assert "secrets.token_hex(16)" not in source
