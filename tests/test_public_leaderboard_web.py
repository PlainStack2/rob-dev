from __future__ import annotations

import asyncio
from types import SimpleNamespace

from rob.throne import webhooks


class _FakePublicRepo:
    def __init__(self, row):
        self.row = row

    async def get_by_token(self, token: str):
        return self.row


class _FakeLeaderboards:
    async def get_top_dommes(self, *args, **kwargs):
        return [SimpleNamespace(total_cents=10000, send_count=1), SimpleNamespace(total_cents=0, send_count=0)]


class _Req:
    def __init__(self):
        self.match_info = {"public_token": "token"}
        self.app = {
            "database": object(),
            "settings": SimpleNamespace(
                leaderboard_limit=10,
                throne_parse_test_sends_as_real_sends=False,
                throne_test_gifter_usernames=("marie_123",),
                throne_test_send_leaderboard_owner_user_id=None,
            ),
        }


def test_public_route_404_for_missing_or_disabled(monkeypatch):
    monkeypatch.setattr(webhooks, "PublicLeaderboardsRepository", lambda _db: _FakePublicRepo(None))
    response = asyncio.run(webhooks.handle_public_leaderboard(_Req()))
    assert response.status == 404


def test_public_route_renders_html_with_required_style(monkeypatch):
    row = SimpleNamespace(guild_id=1, title="Send Leaderboard", enabled=True)
    monkeypatch.setattr(webhooks, "PublicLeaderboardsRepository", lambda _db: _FakePublicRepo(row))
    monkeypatch.setattr(webhooks, "LeaderboardsRepository", lambda _db: _FakeLeaderboards())
    response = asyncio.run(webhooks.handle_public_leaderboard(_Req()))
    text = response.text
    assert response.status == 200
    assert response.headers["Cache-Control"] == "public, max-age=60"
    assert "background:#000" in text
    assert "#b00000" in text
    assert "Times New Roman" in text
    assert "<img" not in text
    assert "<@" not in text
    assert "🥇" not in text
    assert "$100.00 sent" in text
    assert "1 sends" in text
