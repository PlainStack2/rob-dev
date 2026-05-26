from __future__ import annotations

from typing import TYPE_CHECKING
import logging

import discord
from discord import app_commands
from discord.ext import commands

from rob.ui.cards.privacy import privacy_notice_messages

if TYPE_CHECKING:
    from rob.discord.client import RobBot


class PrivacyCog(commands.Cog):
    def __init__(self, bot: RobBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="privacy",
        description="View Rob's privacy notice, including what information may be collected, stored, and used.",
    )
    async def privacy(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        for index, message in enumerate(privacy_notice_messages(), start=1):
            try:
                await interaction.followup.send(
                    **message.send_kwargs(),
                    ephemeral=True,
                )
            except discord.HTTPException:
                logging.exception("Failed to send /privacy follow-up part %s", index)
                await interaction.followup.send(
                    "Unable to send the full privacy notice right now. Please try again shortly.",
                    ephemeral=True,
                )
                return
