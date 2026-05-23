from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from rob.database.repositories.leaderboards import LeaderboardsRepository


class _FakeConnection:
    def __init__(self, *, fetch_rows=None, fetchrow_row=None):
        self.fetch_rows = fetch_rows or []
        self.fetchrow_row = fetchrow_row
        self.fetch_calls: list[tuple[str, tuple]] = []
        self.fetchrow_calls: list[tuple[str, tuple]] = []

    async def fetch(self, query: str, *params):
        self.fetch_calls.append((query, params))
        return self.fetch_rows

    async def fetchrow(self, query: str, *params):
        self.fetchrow_calls.append((query, params))
        return self.fetchrow_row


class _FakeDatabase:
    def __init__(self, connection: _FakeConnection):
        self.connection = connection

    @asynccontextmanager
    async def acquire(self):
        yield self.connection


def test_registered_domme_with_zero_total_is_mapped_from_left_join_query():
    connection = _FakeConnection(
        fetch_rows=[
            {"user_id": 123, "total_cents": 0, "send_count": 0},
            {"user_id": 456, "total_cents": 1099, "send_count": 1},
        ]
    )
    repo = LeaderboardsRepository(_FakeDatabase(connection))

    entries = asyncio.run(
        repo.get_top_dommes(
            1,
            limit=10,
            include_test_sends=False,
            test_gifter_usernames=("marie_123",),
            owner_test_user_id=None,
        )
    )

    query, params = connection.fetch_calls[0]
    assert "FROM dommes d" in query
    assert "LEFT JOIN valid_sends v" in query
    assert "is_private = false" in query
    assert "is_test_send" in query
    assert params == (1, False, ["marie_123"], None, 10)
    assert entries[0].label == "<@123>"
    assert entries[0].total_cents == 0
    assert entries[0].send_count == 0
    assert entries[1].total_cents == 1099


def test_summary_counts_registered_dommes_and_unclaimed_totals():
    connection = _FakeConnection(
        fetchrow_row={
            "total_cents": 5000,
            "send_count": 4,
            "domme_count": 3,
            "sub_count": 2,
            "unclaimed_send_count": 1,
            "unclaimed_total_cents": 1099,
        }
    )
    repo = LeaderboardsRepository(_FakeDatabase(connection))

    summary = asyncio.run(
        repo.get_summary(
            1,
            include_test_sends=False,
            test_gifter_usernames=("marie_123",),
            owner_test_user_id=None,
        )
    )

    query, params = connection.fetchrow_calls[0]
    assert "COUNT(*) FROM dommes" in query
    assert "valid_sends" in query
    assert params == (1, False, ["marie_123"], None)
    assert summary.domme_count == 3
    assert summary.send_count == 4
    assert summary.unclaimed_send_count == 1
    assert summary.unclaimed_total_cents == 1099
