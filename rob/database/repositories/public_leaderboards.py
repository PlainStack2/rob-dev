from __future__ import annotations

from asyncpg import Record

from rob.database.connection import Database
from rob.database.repositories.models import PublicLeaderboard


def _build(row: Record) -> PublicLeaderboard:
    return PublicLeaderboard(
        id=int(row["id"]),
        guild_id=int(row["guild_id"]),
        public_token=str(row["public_token"]),
        title=str(row["title"]),
        enabled=bool(row["enabled"]),
        theme=str(row["theme"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PublicLeaderboardsRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def create(self, *, guild_id: int, public_token: str, title: str, theme: str = "goth_red") -> PublicLeaderboard:
        async with self.database.acquire() as connection:
            row = await connection.fetchrow(
                """
                INSERT INTO public_leaderboards (guild_id, public_token, title, enabled, theme)
                VALUES ($1, $2, $3, true, $4)
                RETURNING id, guild_id, public_token, title, enabled, theme, created_at, updated_at
                """,
                guild_id,
                public_token,
                title,
                theme,
            )
        assert row is not None
        return _build(row)

    async def list_for_guild(self, guild_id: int) -> list[PublicLeaderboard]:
        async with self.database.acquire() as connection:
            rows = await connection.fetch(
                """
                SELECT id, guild_id, public_token, title, enabled, theme, created_at, updated_at
                FROM public_leaderboards
                WHERE guild_id = $1
                ORDER BY created_at DESC
                """,
                guild_id,
            )
        return [_build(r) for r in rows]

    async def get_by_token(self, token: str) -> PublicLeaderboard | None:
        async with self.database.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT id, guild_id, public_token, title, enabled, theme, created_at, updated_at
                FROM public_leaderboards
                WHERE public_token = $1
                """,
                token,
            )
        return _build(row) if row else None

    async def set_enabled(self, *, token: str, enabled: bool) -> PublicLeaderboard | None:
        async with self.database.acquire() as connection:
            row = await connection.fetchrow(
                """
                UPDATE public_leaderboards
                SET enabled = $2, updated_at = now()
                WHERE public_token = $1
                RETURNING id, guild_id, public_token, title, enabled, theme, created_at, updated_at
                """,
                token,
                enabled,
            )
        return _build(row) if row else None

    async def rotate_token(self, *, token: str, new_token: str) -> PublicLeaderboard | None:
        async with self.database.acquire() as connection:
            row = await connection.fetchrow(
                """
                UPDATE public_leaderboards
                SET public_token = $2, updated_at = now()
                WHERE public_token = $1
                RETURNING id, guild_id, public_token, title, enabled, theme, created_at, updated_at
                """,
                token,
                new_token,
            )
        return _build(row) if row else None
