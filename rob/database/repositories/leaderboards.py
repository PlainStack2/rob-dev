from __future__ import annotations

from asyncpg import Record

from rob.database.connection import Database
from rob.database.repositories.models import (
    LeaderboardEntry,
    LeaderboardMessageRef,
    LeaderboardSummary,
)


def _normalized_test_usernames(test_gifter_usernames: tuple[str, ...] | list[str]) -> list[str]:
    return [value.strip().lower() for value in test_gifter_usernames if value.strip()]


def _counted_send_filter(alias: str = "s") -> str:
    return f"""
        {alias}.guild_id = $1
        AND {alias}.discord_post_status = 'posted'
        AND {alias}.is_private = false
        AND (
            $2::bool
            OR NOT (
                COALESCE({alias}.is_test_send, false)
                OR lower(COALESCE({alias}.sub_name, '')) = ANY($3::text[])
            )
            OR ($4::bigint IS NOT NULL AND {alias}.domme_user_id = $4)
        )
    """


def _build_message_ref(row: Record) -> LeaderboardMessageRef:
    return LeaderboardMessageRef(
        id=int(row["id"]),
        guild_id=int(row["guild_id"]),
        message_key=str(row["message_key"]),
        leaderboard_type=row["leaderboard_type"],
        channel_id=int(row["channel_id"]),
        message_id=int(row["message_id"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class LeaderboardsRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def get_summary(
        self,
        guild_id: int,
        *,
        include_test_sends: bool = False,
        test_gifter_usernames: tuple[str, ...] | list[str] = (),
        owner_test_user_id: int | None = None,
    ) -> LeaderboardSummary:
        usernames = _normalized_test_usernames(test_gifter_usernames)
        async with self.database.acquire() as connection:
            row = await connection.fetchrow(
                f"""
                WITH valid_sends AS (
                    SELECT *
                    FROM sends s
                    WHERE {_counted_send_filter("s")}
                )
                SELECT
                    COALESCE((SELECT SUM(amount_cents) FROM valid_sends), 0) AS total_cents,
                    (SELECT COUNT(*) FROM valid_sends) AS send_count,
                    (SELECT COUNT(*) FROM dommes WHERE guild_id = $1) AS domme_count,
                    (
                        SELECT COUNT(DISTINCT sub_user_id)
                        FROM valid_sends
                        WHERE sub_user_id IS NOT NULL
                    ) AS sub_count,
                    (
                        SELECT COUNT(*)
                        FROM valid_sends
                        WHERE sub_user_id IS NULL
                    ) AS unclaimed_send_count,
                    (
                        SELECT COALESCE(SUM(amount_cents), 0)
                        FROM valid_sends
                        WHERE sub_user_id IS NULL
                    ) AS unclaimed_total_cents
                """,
                guild_id,
                include_test_sends,
                usernames,
                owner_test_user_id,
            )
        assert row is not None
        return LeaderboardSummary(
            total_cents=int(row["total_cents"] or 0),
            send_count=int(row["send_count"] or 0),
            domme_count=int(row["domme_count"] or 0),
            sub_count=int(row["sub_count"] or 0),
            unclaimed_send_count=int(row["unclaimed_send_count"] or 0),
            unclaimed_total_cents=int(row["unclaimed_total_cents"] or 0),
        )

    async def get_top_dommes(
        self,
        guild_id: int,
        *,
        limit: int = 10,
        include_test_sends: bool = False,
        test_gifter_usernames: tuple[str, ...] | list[str] = (),
        owner_test_user_id: int | None = None,
    ) -> list[LeaderboardEntry]:
        usernames = _normalized_test_usernames(test_gifter_usernames)
        async with self.database.acquire() as connection:
            rows = await connection.fetch(
                f"""
                WITH valid_sends AS (
                    SELECT *
                    FROM sends s
                    WHERE {_counted_send_filter("s")}
                )
                SELECT
                    d.discord_user_id AS user_id,
                    COALESCE(SUM(v.amount_cents), 0) AS total_cents,
                    COUNT(v.id) AS send_count
                FROM dommes d
                LEFT JOIN valid_sends v
                    ON v.guild_id = d.guild_id
                    AND v.domme_user_id = d.discord_user_id
                WHERE d.guild_id = $1
                GROUP BY d.discord_user_id
                ORDER BY total_cents DESC, send_count DESC, d.discord_user_id ASC
                LIMIT $5
                """,
                guild_id,
                include_test_sends,
                usernames,
                owner_test_user_id,
                limit,
            )
        return [
            LeaderboardEntry(
                label=f"<@{int(row['user_id'])}>",
                user_id=int(row["user_id"]),
                total_cents=int(row["total_cents"] or 0),
                send_count=int(row["send_count"] or 0),
            )
            for row in rows
        ]

    async def get_current_leader(
        self,
        guild_id: int,
        *,
        include_test_sends: bool = False,
        test_gifter_usernames: tuple[str, ...] | list[str] = (),
        owner_test_user_id: int | None = None,
    ) -> LeaderboardEntry | None:
        entries = await self.get_top_dommes(
            guild_id,
            limit=1,
            include_test_sends=include_test_sends,
            test_gifter_usernames=test_gifter_usernames,
            owner_test_user_id=owner_test_user_id,
        )
        return entries[0] if entries else None

    async def get_top_subs(
        self,
        guild_id: int,
        *,
        limit: int = 10,
        include_test_sends: bool = False,
        test_gifter_usernames: tuple[str, ...] | list[str] = (),
        owner_test_user_id: int | None = None,
    ) -> list[LeaderboardEntry]:
        usernames = _normalized_test_usernames(test_gifter_usernames)
        async with self.database.acquire() as connection:
            rows = await connection.fetch(
                f"""
                SELECT
                    sends.sub_user_id AS user_id,
                    MIN(subs.send_name) AS send_name,
                    COALESCE(SUM(sends.amount_cents), 0) AS total_cents,
                    COUNT(*) AS send_count
                FROM sends
                JOIN subs ON subs.id = sends.sub_id
                WHERE {_counted_send_filter("sends")}
                AND sends.sub_user_id IS NOT NULL
                GROUP BY sends.sub_user_id
                ORDER BY total_cents DESC, send_count DESC, sends.sub_user_id ASC
                LIMIT $5
                """,
                guild_id,
                include_test_sends,
                usernames,
                owner_test_user_id,
                limit,
            )
        return [
            LeaderboardEntry(
                label=f"<@{int(row['user_id'])}>",
                user_id=int(row["user_id"]),
                total_cents=int(row["total_cents"] or 0),
                send_count=int(row["send_count"] or 0),
            )
            for row in rows
        ]

    async def get_message(self, guild_id: int, message_key: str) -> LeaderboardMessageRef | None:
        async with self.database.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT *
                FROM leaderboard_message
                WHERE guild_id = $1
                AND message_key = $2
                """,
                guild_id,
                message_key,
            )
        if row is None:
            return None
        return _build_message_ref(row)

    async def upsert_message(
        self,
        *,
        guild_id: int,
        message_key: str,
        leaderboard_type: str | None,
        channel_id: int,
        message_id: int,
    ) -> LeaderboardMessageRef:
        async with self.database.acquire() as connection:
            row = await connection.fetchrow(
                """
                INSERT INTO leaderboard_message (
                    guild_id,
                    message_key,
                    leaderboard_type,
                    channel_id,
                    message_id
                )
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (guild_id, message_key) DO UPDATE SET
                    leaderboard_type = EXCLUDED.leaderboard_type,
                    channel_id = EXCLUDED.channel_id,
                    message_id = EXCLUDED.message_id,
                    updated_at = now()
                RETURNING *
                """,
                guild_id,
                message_key,
                leaderboard_type,
                channel_id,
                message_id,
            )
        assert row is not None
        return _build_message_ref(row)
