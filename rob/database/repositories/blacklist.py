from __future__ import annotations

from rob.database.connection import Database


class BlacklistRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(
        self,
        *,
        discord_user_id: int,
        reason: str | None,
        created_by: int | None,
    ) -> None:
        async with self.database.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO blacklist (
                    discord_user_id,
                    reason,
                    created_at,
                    created_by
                )
                VALUES ($1, $2, now(), $3)
                ON CONFLICT (discord_user_id) DO UPDATE SET
                    reason = EXCLUDED.reason,
                    created_by = EXCLUDED.created_by
                """,
                discord_user_id,
                reason,
                created_by,
            )

    async def remove(self, discord_user_id: int) -> None:
        async with self.database.acquire() as connection:
            await connection.execute(
                "DELETE FROM blacklist WHERE discord_user_id = $1",
                discord_user_id,
            )

    async def contains(self, discord_user_id: int) -> bool:
        async with self.database.acquire() as connection:
            value = await connection.fetchval(
                "SELECT 1 FROM blacklist WHERE discord_user_id = $1 LIMIT 1",
                discord_user_id,
            )
        return value is not None
