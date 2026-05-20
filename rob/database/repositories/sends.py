from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import asyncpg

@dataclass(frozen=True)
class SendInsert:
    guild_id: int
    domme_id: int | None
    domme_user_id: int
    sub_id: int | None
    sub_user_id: int | None
    sub_name: str | None
    amount_cents: int
    currency: str
    method: str | None
    source: str
    item_name: str | None
    item_image_url: str | None
    external_id: str | None
    event_id: str | None
    fallback_event_hash: str | None
    is_private: bool
    seeded: bool
    sent_at: datetime
    discord_post_status: str

class SendsRepository:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.connection = connection
    
    async def insert_send(self, send: SendInsert) -> int | None:
        row = await self.connection.fetchrow(
            """
            INSERT INTO sends (
                guild_id,
                domme_id,
                domme_user_id,
                sub_id,
                sub_user_id,
                sub_name,
                amount_cents,
                currency,
                method,
                source,
                item_name,
                item_image_url,
                external_id,
                event_id,
                fallback_event_hash,
                is_private,
                seeded,
                sent_at,
                received_at,
                discord_post_status
            )
            VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15,
                $16, $17, $18, now(), $19
            )
            ON CONFLICT DO NOTHING
            RETURNING id;
            """,
            self.guild_id,
            self.domme_id,
            self.domme_user_id,
            self.sub_id,
            self.sub_user_id,
            self.sub_name,
            self.amount_cents,
            self.currency,
            self.method,
            self.source,
            self.item_name,
            self.item_image_url,
            self.external_id,
            self.event_id,
            self.fallback_event_hash,
            self.is_private,
            self.seeded,
            self.sent_at,
            self.received_at,
            self.discord_post_status
        )

        if row is None:
            return None
        
        return int(row["id"])