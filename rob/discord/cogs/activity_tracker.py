from __future__ import annotations

import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class ActivityTrackerCog(commands.Cog):
    """Tracks member message activity to support inactivity detection."""

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Update last activity timestamp for non-bot users."""
        if message.author.bot:
            return
        if message.guild is None:
            return

        try:
            bot_state = getattr(self.bot, "bot_state_repo", None)
            if bot_state is None:
                return

            guild_id = message.guild.id
            user_id = message.author.id
            key = f"activity:{guild_id}:user:{user_id}:last_active"
            now_iso = discord.utils.utcnow().isoformat()
            await bot_state.set_value(key, now_iso)
        except Exception:
            log.exception(
                "Failed to record activity for user_id=%s guild_id=%s",
                message.author.id,
                message.guild.id,
            )

