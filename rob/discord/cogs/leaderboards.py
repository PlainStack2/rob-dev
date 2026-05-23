from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from rob.ui.cards.errors import error_card
from rob.ui.cards.leaderboard import leaderboard_card, leaderboard_stats_card

if TYPE_CHECKING:
    from rob.discord.client import RobBot


class LeaderboardsCog(commands.Cog):
    def __init__(self, bot: RobBot) -> None:
        self.bot = bot

    @app_commands.command(name="leaderboard", description="Show the current posted leaderboards.")
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(**error_card("This command can only be used in a server.").send_kwargs(), ephemeral=True)
            return

        summary = await self.bot.leaderboards_repo.get_summary(
            interaction.guild.id,
            include_test_sends=self.bot.settings.throne_parse_test_sends_as_real_sends,
            test_gifter_usernames=self.bot.settings.throne_test_gifter_usernames,
            owner_test_user_id=self.bot.settings.throne_test_send_leaderboard_owner_user_id,
        )
        dommes = await self.bot.leaderboards_repo.get_top_dommes(
            interaction.guild.id,
            limit=self.bot.settings.leaderboard_limit,
            include_test_sends=self.bot.settings.throne_parse_test_sends_as_real_sends,
            test_gifter_usernames=self.bot.settings.throne_test_gifter_usernames,
            owner_test_user_id=self.bot.settings.throne_test_send_leaderboard_owner_user_id,
        )
        dom_msg = leaderboard_card(
            title="ignored",
            entries=dommes,
            summary=summary,
            status=await self.bot.maintenance_service.get_leaderboard_status(),
        )
        stats_msg = leaderboard_stats_card(summary, dommes)
        await interaction.response.send_message(**dom_msg.send_kwargs(), ephemeral=True)
        await interaction.followup.send(**stats_msg.send_kwargs(), ephemeral=True)
