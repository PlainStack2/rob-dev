from __future__ import annotations

import asyncpg


class BotStateRepository:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.connection = connection

    async def get_value(self, key: str) -> str | None:
        row = await self.connection.fetchrow(
            """
            SELECT value
            FROM bot_state
            WHERE key = $1;
            """,
            key,
        )

        if row is None:
            return None
        
        return str(row["value"])
    
    async def set_value(self, key: str, value: str) -> None:
        await self.connection.execute(
            """
            INSERT INTO bot_state (key, value, updated_at)
            VALUES ($1, $2, now())
            ON CONFLICT (key)
            DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = now();
            """,
            key,
            value,
        )
    
    async def get_bool(self, key: str, *, default: bool = False) -> bool:
        value = await self.get_value(key)

        if value is None:
            return default
        
        return value.strip().lower() in {"1", "true", "yes", "on"}
    
    async def set_bool(self, key: str, value: bool) -> None:
        await self.set_value(key, "true" if value else "false")