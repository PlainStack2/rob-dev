from __future__ import annotations

from dataclasses import dataclass

import discord

from rob.database.repositories.counting import CountingRepository
from rob.database.repositories.guild_settings import GuildSettingsRepository


@dataclass(frozen=True)
class CountingProcessResult:
    success: bool
    expected_number: int
    current_number: int
    reason: str | None = None


class CountingService:
    def __init__(
        self,
        *,
        counting: CountingRepository,
        guild_settings: GuildSettingsRepository,
    ) -> None:
        self.counting = counting
        self.guild_settings = guild_settings

    async def get_or_create_state(self, guild_id: int):
        state = await self.counting.get(guild_id)
        if state is not None:
            return state
        settings = await self.guild_settings.get(guild_id)
        channel_id = settings.counting_channel_id if settings is not None else None
        return await self.counting.upsert(
            guild_id=guild_id,
            channel_id=channel_id,
            current_number=0,
            last_user_id=None,
            is_enabled=channel_id is not None,
            pending_restore=False,
        )

    async def set_current_number(self, guild_id: int, number: int):
        state = await self.get_or_create_state(guild_id)
        return await self.counting.upsert(
            guild_id=guild_id,
            channel_id=state.channel_id,
            current_number=max(0, number),
            last_user_id=None,
            is_enabled=True,
            pending_restore=False,
        )

    async def process_message(self, message: discord.Message) -> CountingProcessResult | None:
        if message.guild is None or message.author.bot:
            return None

        state = await self.get_or_create_state(message.guild.id)
        if not state.is_enabled or state.channel_id is None:
            return None
        if message.channel.id != state.channel_id:
            return None

        content = message.content.strip()
        if not content.isdigit():
            return None

        expected = state.current_number + 1
        number = int(content)
        if state.last_user_id == message.author.id:
            return CountingProcessResult(
                success=False,
                expected_number=expected,
                current_number=state.current_number,
                reason="same_user",
            )
        if number != expected:
            return CountingProcessResult(
                success=False,
                expected_number=expected,
                current_number=state.current_number,
                reason="wrong_number",
            )

        await self.counting.upsert(
            guild_id=state.guild_id,
            channel_id=state.channel_id,
            current_number=number,
            last_user_id=message.author.id,
            is_enabled=state.is_enabled,
            pending_restore=False,
        )
        return CountingProcessResult(
            success=True,
            expected_number=expected,
            current_number=number,
        )
