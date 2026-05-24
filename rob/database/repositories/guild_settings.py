from __future__ import annotations

from asyncpg import Record

from rob.database.connection import Database
from rob.database.repositories.models import GuildSettings


CHANNEL_FIELD_NAMES = {
    "registration_channel_id",
    "leaderboard_channel_id",
    "send_track_channel_id",
    "counting_channel_id",
    "report_channel_id",
    "warn_log_channel_id",
}


def _build_guild_settings(row: Record) -> GuildSettings:
    return GuildSettings(
        guild_id=int(row["guild_id"]),
        registration_channel_id=row["registration_channel_id"],
        leaderboard_channel_id=row["leaderboard_channel_id"],
        send_track_channel_id=row["send_track_channel_id"],
        counting_channel_id=row["counting_channel_id"],
        report_channel_id=row["report_channel_id"] if "report_channel_id" in row else None,
        domme_role_id=row["domme_role_id"],
        sub_role_id=row["sub_role_id"],
        mod_role_id=row["mod_role_id"],
        inactive_role_id=row["inactive_role_id"] if "inactive_role_id" in row else None,
        warn_log_channel_id=row["warn_log_channel_id"],
        carlbot_user_id=row["carlbot_user_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class GuildSettingsRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def ensure_guild(self, guild_id: int) -> None:
        async with self.database.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO guild_settings (guild_id)
                VALUES ($1)
                ON CONFLICT (guild_id) DO NOTHING
                """,
                guild_id,
            )

    async def get(self, guild_id: int) -> GuildSettings | None:
        async with self.database.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT * FROM guild_settings WHERE guild_id = $1",
                guild_id,
            )
        if row is None:
            return None
        return _build_guild_settings(row)

    async def list_guild_ids(self) -> list[int]:
        async with self.database.acquire() as connection:
            rows = await connection.fetch(
                "SELECT guild_id FROM guild_settings ORDER BY guild_id ASC"
            )
        return [int(row["guild_id"]) for row in rows]

    async def set_channel_id(
        self,
        guild_id: int,
        field_name: str,
        channel_id: int | None,
    ) -> GuildSettings:
        if field_name not in CHANNEL_FIELD_NAMES:
            raise ValueError(f"Unsupported guild_settings channel field: {field_name}")

        await self.ensure_guild(guild_id)
        query = f"""
            UPDATE guild_settings
            SET {field_name} = $2,
                updated_at = now()
            WHERE guild_id = $1
            RETURNING *
        """
        async with self.database.acquire() as connection:
            row = await connection.fetchrow(query, guild_id, channel_id)
        if row is None:
            raise RuntimeError(f"Failed to update guild_settings for guild_id={guild_id}")
        return _build_guild_settings(row)
