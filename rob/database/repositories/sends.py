from __future__ import annotations

from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError

from rob.database.connection import Database
from rob.database.repositories.models import NewSend, QueueStatus, SendRecord


def _build_send(row: Record) -> SendRecord:
    return SendRecord(
        id=int(row["id"]),
        guild_id=int(row["guild_id"]),
        domme_id=row["domme_id"],
        domme_user_id=int(row["domme_user_id"]),
        sub_id=row["sub_id"],
        sub_user_id=row["sub_user_id"],
        sub_name=row["sub_name"],
        amount_cents=int(row["amount_cents"]),
        currency=str(row["currency"]),
        method=row["method"],
        source=str(row["source"]),
        item_name=row["item_name"],
        item_image_url=row["item_image_url"],
        external_id=row["external_id"],
        event_id=row["event_id"],
        fallback_event_hash=row["fallback_event_hash"],
        is_private=bool(row["is_private"]),
        seeded=bool(row["seeded"]),
        sent_at=row["sent_at"],
        received_at=row["received_at"],
        discord_post_status=str(row["discord_post_status"]),
        discord_posted_at=row["discord_posted_at"],
        discord_message_id=row["discord_message_id"],
        discord_post_error=row["discord_post_error"],
        created_at=row["created_at"],
    )


class SendsRepository:
    VALID_STATUSES = ("pending", "queued_maintenance", "posted", "failed", "ignored")

    def __init__(self, database: Database) -> None:
        self.database = database

    async def insert(self, send: NewSend) -> SendRecord | None:
        try:
            async with self.database.acquire() as connection:
                row = await connection.fetchrow(
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
                        discord_post_status
                    )
                    VALUES (
                        $1, $2, $3, $4, $5,
                        $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15,
                        $16, $17, $18, $19
                    )
                    RETURNING *
                    """,
                    send.guild_id,
                    send.domme_id,
                    send.domme_user_id,
                    send.sub_id,
                    send.sub_user_id,
                    send.sub_name,
                    send.amount_cents,
                    send.currency,
                    send.method,
                    send.source,
                    send.item_name,
                    send.item_image_url,
                    send.external_id,
                    send.event_id,
                    send.fallback_event_hash,
                    send.is_private,
                    send.seeded,
                    send.sent_at,
                    send.discord_post_status,
                )
        except UniqueViolationError:
            return None

        assert row is not None
        return _build_send(row)

    async def get(self, send_id: int) -> SendRecord | None:
        async with self.database.acquire() as connection:
            row = await connection.fetchrow("SELECT * FROM sends WHERE id = $1", send_id)
        if row is None:
            return None
        return _build_send(row)

    async def fetch_for_status(self, status: str, *, limit: int = 50) -> list[SendRecord]:
        async with self.database.acquire() as connection:
            rows = await connection.fetch(
                """
                SELECT *
                FROM sends
                WHERE discord_post_status = $1
                ORDER BY received_at ASC, id ASC
                LIMIT $2
                """,
                status,
                limit,
            )
        return [_build_send(row) for row in rows]

    async def release_queued_maintenance(self) -> int:
        async with self.database.acquire() as connection:
            result = await connection.execute(
                """
                UPDATE sends
                SET discord_post_status = 'pending'
                WHERE discord_post_status = 'queued_maintenance'
                """
            )
        return int(result.rsplit(" ", 1)[-1])

    async def mark_posted(self, send_id: int, *, message_id: int | None) -> None:
        async with self.database.acquire() as connection:
            await connection.execute(
                """
                UPDATE sends
                SET
                    discord_post_status = 'posted',
                    discord_posted_at = now(),
                    discord_message_id = $2,
                    discord_post_error = NULL
                WHERE id = $1
                """,
                send_id,
                message_id,
            )

    async def mark_failed(self, send_id: int, *, error: str) -> None:
        async with self.database.acquire() as connection:
            await connection.execute(
                """
                UPDATE sends
                SET
                    discord_post_status = 'failed',
                    discord_post_error = left($2, 500)
                WHERE id = $1
                """,
                send_id,
                error,
            )

    async def count_statuses(self) -> QueueStatus:
        async with self.database.acquire() as connection:
            rows = await connection.fetch(
                """
                SELECT discord_post_status, COUNT(*) AS count
                FROM sends
                GROUP BY discord_post_status
                """
            )
        counts = {status: 0 for status in self.VALID_STATUSES}
        for row in rows:
            counts[str(row["discord_post_status"])] = int(row["count"])
        return QueueStatus(
            pending=counts["pending"],
            queued_maintenance=counts["queued_maintenance"],
            posted=counts["posted"],
            failed=counts["failed"],
            ignored=counts["ignored"],
        )
