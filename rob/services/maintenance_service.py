from __future__ import annotations

import asyncpg

from rob.database.repositories.bot_state import BotStateRepository


MAINTENANCE_MODE_KEY = "maintenance_mode"
MAINTENANCE_REASON_KEY = "maintenance_reason"

class MaintenanceService:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.bot_state = BotStateRepository(connection)

    async def is_enabled(self) -> bool:
        return await self.bot_state.get_bool(MAINTENANCE_MODE_KEY, default=False)
    
    async def get_reason(self) -> str | None:
        return await self.bot_state.get_value(MAINTENANCE_REASON_KEY)
    
    async def enable(self, *, reason: str = "") -> None:
        await self.bot_state.set_bool(MAINTENANCE_MODE_KEY, True)
        await self.bot_state.set_value(MAINTENANCE_REASON_KEY, reason)

    async def disable(self) -> None:
        await self.bot_state.set_bool(MAINTENANCE_MODE_KEY, False)
        await self.bot_state.set_value(MAINTENANCE_REASON_KEY, "")