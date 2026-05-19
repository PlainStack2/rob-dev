from __future__ import annotations

import argparse
import asyncio
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from rob.config.settings import configure_logging, load_settings
from rob.database.connection import Database

def parse_timestamp(value: Any) -> datetime | None:
    """Convert legacy SQLite timestamp strings into datetime objects."""

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    return datetime.fromisoformat(text)


def money_to_cents(value: Any) -> int:
    """Convert legacy dollar values into integer cents."""

    if value is None:
        return 0

    return int(round(float(value) * 100))


def sqlite_bool(value: Any) -> bool:
    """Convert SQLite 0/1 values into Python bools."""

    return bool(int(value or 0))


def hash_secret(secret: str | None) -> str | None:
    """Hash legacy raw webhook secrets for safer future lookup."""

    if not secret:
        return None

    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def fetch_all(sqlite: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
    cursor = sqlite.execute(query)
    return list(cursor.fetchall())


def get_bot_config(sqlite: sqlite3.Connection) -> dict[str, str]:
    rows = fetch_all(sqlite, "SELECT key, value FROM bot_config;")
    return {str(row["key"]): str(row["value"]) for row in rows}


async def import_guild_settings(postgres, *, guild_id: int) -> None:
    await postgres.execute(
        """
        INSERT INTO guild_settings (guild_id)
        VALUES ($1)
        ON CONFLICT (guild_id) DO NOTHING;
        """,
        guild_id,
    )


async def import_dommes(
    sqlite: sqlite3.Connection,
    postgres,
    *,
    guild_id: int,
) -> None:
    rows = fetch_all(
        sqlite,
        """
        SELECT user_id, throne_url, registered_at
        FROM event_dommes;
        """,
    )

    for row in rows:
        await postgres.execute(
            """
            INSERT INTO dommes (
                guild_id,
                discord_user_id,
                throne_url,
                registered_at
            )
            VALUES ($1, $2, $3, $4::timestamptz)
            ON CONFLICT (guild_id, discord_user_id)
            DO UPDATE SET
                throne_url = EXCLUDED.throne_url,
                registered_at = EXCLUDED.registered_at,
                updated_at = now();
            """,
            guild_id,
            int(row["user_id"]),
            str(row["throne_url"]),
            parse_timestamp(row["registered_at"]),
        )

    print(f"Imported dommes: {len(rows)}")


async def import_subs(
    sqlite: sqlite3.Connection,
    postgres,
    *,
    guild_id: int,
) -> None:
    rows = fetch_all(
        sqlite,
        """
        SELECT user_id, sub_name, registered_at
        FROM event_subs;
        """,
    )

    for row in rows:
        await postgres.execute(
            """
            INSERT INTO subs (
                guild_id,
                discord_user_id,
                send_name,
                registered_at
            )
            VALUES ($1, $2, $3, $4::timestamptz)
            ON CONFLICT (guild_id, discord_user_id)
            DO UPDATE SET
                send_name = EXCLUDED.send_name,
                registered_at = EXCLUDED.registered_at,
                updated_at = now();
            """,
            guild_id,
            int(row["user_id"]),
            str(row["sub_name"]),
            parse_timestamp(row["registered_at"]),
        )

    print(f"Imported subs: {len(rows)}")


async def import_throne_creators(
    sqlite: sqlite3.Connection,
    postgres,
    *,
    guild_id: int,
) -> None:
    rows = fetch_all(
        sqlite,
        """
        SELECT
            discord_user_id,
            throne_handle,
            throne_creator_id,
            hide_own_purchases,
            tracking_mode,
            webhook_secret,
            webhook_connected_at,
            overlay_detected,
            last_overlay_check_at,
            last_successful_event_at,
            created_at,
            updated_at
        FROM throne_creators;
        """,
    )

    for row in rows:
        discord_user_id = int(row["discord_user_id"])

        domme_id = await postgres.fetchval(
            """
            SELECT id
            FROM dommes
            WHERE guild_id = $1
            AND discord_user_id = $2;
            """,
            guild_id,
            discord_user_id,
        )

        raw_secret = str(row["webhook_secret"])

        await postgres.execute(
            """
            INSERT INTO throne_creators (
                guild_id,
                domme_id,
                discord_user_id,
                throne_handle,
                throne_creator_id,
                hide_own_purchases,
                tracking_mode,
                webhook_secret,
                webhook_secret_hash,
                webhook_connected_at,
                overlay_detected,
                last_overlay_check_at,
                last_successful_event_at,
                created_at,
                updated_at
            )
            VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9,
                $10,
                $11,
                $12,
                $13,
                $14,
                $15
            )
            ON CONFLICT (guild_id, throne_creator_id)
            DO UPDATE SET
                domme_id = EXCLUDED.domme_id,
                discord_user_id = EXCLUDED.discord_user_id,
                throne_handle = EXCLUDED.throne_handle,
                hide_own_purchases = EXCLUDED.hide_own_purchases,
                tracking_mode = EXCLUDED.tracking_mode,
                webhook_secret = EXCLUDED.webhook_secret,
                webhook_secret_hash = EXCLUDED.webhook_secret_hash,
                webhook_connected_at = EXCLUDED.webhook_connected_at,
                overlay_detected = EXCLUDED.overlay_detected,
                last_overlay_check_at = EXCLUDED.last_overlay_check_at,
                last_successful_event_at = EXCLUDED.last_successful_event_at,
                updated_at = EXCLUDED.updated_at;
            """,
            guild_id,
            domme_id,
            discord_user_id,
            str(row["throne_handle"]),
            str(row["throne_creator_id"]),
            None
            if row["hide_own_purchases"] is None
            else sqlite_bool(row["hide_own_purchases"]),
            str(row["tracking_mode"]),
            raw_secret,
            hash_secret(raw_secret),
            parse_timestamp(row["webhook_connected_at"]),
            sqlite_bool(row["overlay_detected"]),
            parse_timestamp(row["last_overlay_check_at"]),
            parse_timestamp(row["last_successful_event_at"]),
            parse_timestamp(row["created_at"]),
            parse_timestamp(row["updated_at"]),
        )

    print(f"Imported throne creators: {len(rows)}")


async def import_wishlist_items(
    sqlite: sqlite3.Connection,
    postgres,
) -> None:
    rows = fetch_all(
        sqlite,
        """
        SELECT
            creator_id,
            wishlist_item_id,
            item_name,
            item_image_url,
            amount_usd,
            currency,
            is_available,
            last_seen_at
        FROM throne_wishlist_items;
        """,
    )

    for row in rows:
        await postgres.execute(
            """
            INSERT INTO throne_wishlist_items (
                creator_id,
                wishlist_item_id,
                item_name,
                item_image_url,
                amount_cents,
                currency,
                is_available,
                last_seen_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::timestamptz)
            ON CONFLICT (creator_id, wishlist_item_id)
            DO UPDATE SET
                item_name = EXCLUDED.item_name,
                item_image_url = EXCLUDED.item_image_url,
                amount_cents = EXCLUDED.amount_cents,
                currency = EXCLUDED.currency,
                is_available = EXCLUDED.is_available,
                last_seen_at = EXCLUDED.last_seen_at;
            """,
            str(row["creator_id"]),
            str(row["wishlist_item_id"]),
            row["item_name"],
            row["item_image_url"],
            money_to_cents(row["amount_usd"]),
            row["currency"],
            None
            if row["is_available"] is None
            else sqlite_bool(row["is_available"]),
            parse_timestamp(row["last_seen_at"]),
        )

    print(f"Imported wishlist items: {len(rows)}")


async def import_sends(
    sqlite: sqlite3.Connection,
    postgres,
    *,
    guild_id: int,
) -> None:
    rows = fetch_all(
        sqlite,
        """
        SELECT
            id,
            domme_user_id,
            sub_name,
            claimed_sub_user_id,
            amount_usd,
            item_name,
            item_image_url,
            logged_by,
            sent_at,
            external_id,
            is_private,
            seeded,
            event_key,
            event_id,
            fallback_event_hash,
            source
        FROM event_sends
        ORDER BY id ASC;
        """,
    )

    for row in rows:
        domme_user_id = int(row["domme_user_id"])
        sub_user_id = (
            int(row["claimed_sub_user_id"])
            if row["claimed_sub_user_id"] is not None
            else None
        )

        domme_id = await postgres.fetchval(
            """
            SELECT id
            FROM dommes
            WHERE guild_id = $1
            AND discord_user_id = $2;
            """,
            guild_id,
            domme_user_id,
        )

        sub_id = None
        if sub_user_id is not None:
            sub_id = await postgres.fetchval(
                """
                SELECT id
                FROM subs
                WHERE guild_id = $1
                AND discord_user_id = $2;
                """,
                guild_id,
                sub_user_id,
            )

        source = row["source"] or "legacy"

        await postgres.execute(
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
                discord_post_status,
                created_at
            )
            VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, 'USD', NULL, $8,
                $9, $10, $11, $12, $13,
                $14, $15,
                $16,
                $16,
                'posted',
                now()
            )
            ON CONFLICT DO NOTHING;
            """,
            guild_id,
            domme_id,
            domme_user_id,
            sub_id,
            sub_user_id,
            row["sub_name"],
            money_to_cents(row["amount_usd"]),
            str(source),
            row["item_name"],
            row["item_image_url"],
            row["external_id"],
            row["event_id"],
            row["fallback_event_hash"],
            sqlite_bool(row["is_private"]),
            sqlite_bool(row["seeded"]),
            parse_timestamp(row["sent_at"]),
        )

    print(f"Imported sends: {len(rows)}")


async def import_send_requests(
    sqlite: sqlite3.Connection,
    postgres,
    *,
    guild_id: int,
) -> None:
    rows = fetch_all(
        sqlite,
        """
        SELECT
            id,
            sub_user_id,
            domme_user_id,
            amount_usd,
            method,
            note,
            status,
            created_at,
            resolved_at
        FROM send_requests
        ORDER BY id ASC;
        """,
    )

    for row in rows:
        await postgres.execute(
            """
            INSERT INTO send_requests (
                guild_id,
                sub_user_id,
                domme_user_id,
                amount_cents,
                currency,
                method,
                note,
                status,
                created_at,
                resolved_at
            )
            VALUES (
                $1, $2, $3, $4, 'USD',
                $5, $6, $7,
                $8,
                $9
            )
            ON CONFLICT DO NOTHING;
            """,
            guild_id,
            int(row["sub_user_id"]),
            int(row["domme_user_id"]),
            money_to_cents(row["amount_usd"]),
            str(row["method"]),
            row["note"],
            str(row["status"]),
            parse_timestamp(row["created_at"]),
            parse_timestamp(row["resolved_at"]),
        )

    print(f"Imported send requests: {len(rows)}")


async def import_blacklist(
    sqlite: sqlite3.Connection,
    postgres,
) -> None:
    rows = fetch_all(
        sqlite,
        """
        SELECT discord_user_id, reason, created_at, created_by
        FROM rob_blacklist;
        """,
    )

    for row in rows:
        await postgres.execute(
            """
            INSERT INTO blacklist (
                discord_user_id,
                reason,
                created_at,
                created_by
            )
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (discord_user_id)
            DO UPDATE SET
                reason = EXCLUDED.reason,
                created_at = EXCLUDED.created_at,
                created_by = EXCLUDED.created_by;
            """,
            int(row["discord_user_id"]),
            row["reason"],
            parse_timestamp(row["created_at"]),
            int(row["created_by"]) if str(row["created_by"] or "").isdigit() else None,
        )

    print(f"Imported blacklist entries: {len(rows)}")


async def import_leaderboard_messages(
    sqlite: sqlite3.Connection,
    postgres,
    *,
    guild_id: int,
) -> None:
    rows = fetch_all(
        sqlite,
        """
        SELECT message_key, message_id, channel_id
        FROM event_messages;
        """,
    )

    type_map = {
        "event:domme_totals": "dommes",
        "event:sub_leaderboard": "subs",
    }

    for row in rows:
        message_key = str(row["message_key"])

        await postgres.execute(
            """
            INSERT INTO leaderboard_messages (
                guild_id,
                message_key,
                leaderboard_type,
                channel_id,
                message_id
            )
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (guild_id, message_key)
            DO UPDATE SET
                leaderboard_type = EXCLUDED.leaderboard_type,
                channel_id = EXCLUDED.channel_id,
                message_id = EXCLUDED.message_id,
                updated_at = now();
            """,
            guild_id,
            message_key,
            type_map.get(message_key),
            int(row["channel_id"]),
            int(row["message_id"]),
        )

    print(f"Imported leaderboard messages: {len(rows)}")


async def import_counting_state(
    sqlite: sqlite3.Connection,
    postgres,
    *,
    guild_id: int,
) -> None:
    config = get_bot_config(sqlite)

    current_number = int(config.get("count.current", "0"))
    is_enabled = config.get("count.active", "0") == "1"
    pending_restore = config.get("count.pending_restore", "0") == "1"

    raw_last_user_id = config.get("count.last_user_id")
    last_user_id = int(raw_last_user_id) if raw_last_user_id else None

    await postgres.execute(
        """
        INSERT INTO counting_state (
            guild_id,
            current_number,
            last_user_id,
            is_enabled,
            pending_restore,
            updated_at
        )
        VALUES ($1, $2, $3, $4, $5, now())
        ON CONFLICT (guild_id)
        DO UPDATE SET
            current_number = EXCLUDED.current_number,
            last_user_id = EXCLUDED.last_user_id,
            is_enabled = EXCLUDED.is_enabled,
            pending_restore = EXCLUDED.pending_restore,
            updated_at = now();
        """,
        guild_id,
        current_number,
        last_user_id,
        is_enabled,
        pending_restore,
    )

    print("Imported counting state.")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import legacy Rob SQLite data into PostgreSQL."
    )
    parser.add_argument(
        "--sqlite-db",
        required=True,
        help="Path to legacy rob_the_bot.sqlite3 file.",
    )
    parser.add_argument(
        "--guild-id",
        required=True,
        type=int,
        help="Discord guild ID to attach imported data to.",
    )

    args = parser.parse_args()
    sqlite_path = Path(args.sqlite_db)

    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {sqlite_path}")

    settings = load_settings()
    configure_logging(settings.log_level)

    sqlite = sqlite3.connect(sqlite_path)
    sqlite.row_factory = sqlite3.Row

    database = Database(settings.database_url)
    await database.connect()

    try:
        async with database.transaction() as postgres:
            await import_guild_settings(postgres, guild_id=args.guild_id)
            await import_dommes(sqlite, postgres, guild_id=args.guild_id)
            await import_subs(sqlite, postgres, guild_id=args.guild_id)
            await import_throne_creators(sqlite, postgres, guild_id=args.guild_id)
            await import_wishlist_items(sqlite, postgres)
            await import_sends(sqlite, postgres, guild_id=args.guild_id)
            await import_send_requests(sqlite, postgres, guild_id=args.guild_id)
            await import_blacklist(sqlite, postgres)
            await import_leaderboard_messages(sqlite, postgres, guild_id=args.guild_id)
            await import_counting_state(sqlite, postgres, guild_id=args.guild_id)

        print("Legacy SQLite import complete.")
    finally:
        sqlite.close()
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())