from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from rob.ui.cards.errors import error_embed
from rob.ui.cards.registration import registration_embed

if TYPE_CHECKING:
    from rob.discord.client import RobBot


class RegistrationCog(commands.Cog):
    register_group = app_commands.Group(
        name="register",
        description="Register as a Domme or Sub.",
    )

    def __init__(self, bot: RobBot) -> None:
        self.bot = bot

    @register_group.command(name="domme", description="Register a Domme Throne profile.")
    @app_commands.describe(throne="Your Throne profile URL or username.")
    async def register_domme(
        self,
        interaction: discord.Interaction,
        throne: str,
    ) -> None:
        if interaction.guild is None or interaction.user is None:
            await interaction.response.send_message(
                embed=error_embed("This command can only be used in a server."),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            result = await self.bot.registration_service.register_domme(
                guild_id=interaction.guild.id,
                discord_user_id=interaction.user.id,
                throne_input=throne,
            )
        except ValueError as exc:
            await interaction.followup.send(
                embed=error_embed("Domme registration could not be completed.", str(exc)),
                ephemeral=True,
            )
            return

        details = [
            ("Throne Handle", result.creator.throne_handle),
            ("Creator ID", result.creator.throne_creator_id),
            (
                "Tracking Status",
                "Webhook connected" if result.creator.tracking_mode == "webhook" else "Waiting for first webhook",
            ),
        ]
        if result.webhook_url:
            details.append(("Webhook URL", result.webhook_url))
        else:
            details.append(
                (
                    "Webhook URL",
                    "Not available from this bot config. The creator record is ready and can be completed from the webhook server setup.",
                )
            )

        await interaction.followup.send(
            embed=registration_embed(
                title="Rob | Domme Registered",
                summary="Your Throne profile has been linked.",
                details=details,
            ),
            ephemeral=True,
        )

    @register_group.command(name="sub", description="Register a sending name to claim sends.")
    @app_commands.describe(send_name="The exact name you use on Throne sends.")
    async def register_sub(
        self,
        interaction: discord.Interaction,
        send_name: str,
    ) -> None:
        if interaction.guild is None or interaction.user is None:
            await interaction.response.send_message(
                embed=error_embed("This command can only be used in a server."),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            result = await self.bot.registration_service.register_sub(
                guild_id=interaction.guild.id,
                discord_user_id=interaction.user.id,
                send_name=send_name,
            )
        except ValueError as exc:
            await interaction.followup.send(
                embed=error_embed("Sub registration could not be completed.", str(exc)),
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            embed=registration_embed(
                title="Rob | Sub Registered",
                summary="Your send-claim name is now active.",
                details=[("Tracked Name", result.sub.send_name)],
            ),
            ephemeral=True,
        )
