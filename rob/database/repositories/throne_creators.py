from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import asyncpg


@dataclass(frozen=True)
class ThroneCreator:
    id: int
    guild_id: int
    domme_id: int | None
    discord_user_id: int
    throne_handle: str
    throne_creator_id: str
    webhook_secret: str | None
    webhook_secret_hash: str | None
    tracking_mode: str

class ThroneCreatorsRepository:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.connection = connection

    async def get_by_creator_id(
            self,
            *,
            throne_creator_id: str,
    ) -> list[ThroneCreator]:
        rows = await self.connection.fetch(
            """
            SELECT
                id,
                guild_id,
                domme_id,
                discord_user_id,
                throne_handle,
                throne_creator_id,
                webhook_secret,
                webhook_secret_hash,
                tracking_mode
            FROM throne_creators
            WHERE throne_creator_id = $1;
            """,
            throne_creator_id,
        )

        return [
            ThroneCreator(
                id=int(row["id"]),
                guild_id=int(row["guild_id"]),
                domme_id=int(row["domme_id"]),
                discord_user_id=int(row["discord_user_id"]),
                throne_handle=str(row["throne_handle"]),
                throne_creator_id=str(row["throne_creator_id"]),
                webhook_secret=row["webhook_secret"],
                webhook_secret_hash=row["webhook_secret_hash"],
                tracking_mode=str(row["tracking_mode"]),
            )
            for row in rows
        ]
    
    async def mark_webhook_success(
            self,
            *,
            creator_id: int,
            when: datetime,
    ) -> None:
        await self.connection.execute(
            """
            UPDATE throne_creators
            SET
                webhook_connected_at = COALESCE(webhook_connected_at, $2),
                last_successful_event_at = $2,
                updated_at = now()
            WHERE id = $1;
            """,
            creator_id,
            when,
        )