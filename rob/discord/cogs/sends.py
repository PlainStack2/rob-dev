from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from discord.ext import commands

from rob.ui.cards.errors import error_embed
from rob.ui.cards.registration import registration_embed
from rob.utils.money import dollars_to_cents, format_money_from_cents

if TYPE_CHECKING:
    from rob.discord.client import RobBot

_MANUAL_METHODS = ["cashapp", "paypal", "wishtender", "throne", "other"]
_REQUEST_METHODS = ["cashapp", "paypal", "wishtender", "throne", "other"]
_SEND_REQUEST_RATE_LIMIT = 3


class SendsCog(commands.Cog):
    def __init__(self, bot: RobBot) -> None:
        self.bot = bot

    @app_commands.command(name="add", description="Log a manual send for the leaderboard.")
    @app_commands.describe(
        amount="Amount sent in USD.",
        method="Where the send happened.",
        sub="Optional sending name to attribute.",
        note="Optional item or note for the send.",
    )
    @app_commands.choices(
        method=[app_commands.Choice(name=value, value=value) for value in _MANUAL_METHODS]
    )
    async def add_send(
        self,
        interaction: discord.Interaction,
        amount: app_commands.Range[float, 0.01],
        method: app_commands.Choice[str],
        sub: Optional[str] = None,
        note: Optional[str] = None,
    ) -> None:
        if interaction.guild is None or interaction.user is None:
            await interaction.response.send_message(
                embed=error_embed("This command can only be used in a server."),
                ephemeral=True,
            )
            return

        domme = await self.bot.dommes_repo.get_by_user_id(interaction.guild.id, interaction.user.id)
        if domme is None:
            await interaction.response.send_message(
                embed=error_embed("Only registered Dommes can use `/add`."),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        send = await self.bot.send_service.record_manual_send(
            guild_id=interaction.guild.id,
            domme_id=domme.id,
            domme_user_id=interaction.user.id,
            sub_name=(sub or "").strip() or None,
            amount_cents=dollars_to_cents(float(amount)),
            currency="USD",
            method=method.value,
            note=(note or "").strip() or None,
        )
        if send is None:
            await interaction.followup.send(
                embed=error_embed("That send could not be recorded."),
                ephemeral=True,
            )
            return

        queue_label = (
            "queued for after maintenance"
            if send.discord_post_status == "queued_maintenance"
            else "queued for posting"
        )
        await interaction.followup.send(
            embed=registration_embed(
                title="Rob | Send Logged",
                summary=f"Recorded {format_money_from_cents(send.amount_cents)} and {queue_label}.",
                details=[
                    ("Method", method.value),
                    ("Sender", send.sub_name or "Unclaimed"),
                ],
            ),
            ephemeral=True,
        )

    @app_commands.command(name="sendrequest", description="Ask a Domme to log a send you made.")
    @app_commands.describe(
        domme="The Domme you sent to.",
        amount="Amount sent in USD.",
        method="Where the send happened.",
        note="Optional proof link or note.",
    )
    @app_commands.choices(
        method=[app_commands.Choice(name=value, value=value) for value in _REQUEST_METHODS]
    )
    async def send_request(
        self,
        interaction: discord.Interaction,
        domme: discord.Member,
        amount: app_commands.Range[float, 0.01],
        method: app_commands.Choice[str],
        note: Optional[str] = None,
    ) -> None:
        if interaction.guild is None or interaction.user is None:
            await interaction.response.send_message(
                embed=error_embed("This command can only be used in a server."),
                ephemeral=True,
            )
            return

        domme_record = await self.bot.dommes_repo.get_by_user_id(interaction.guild.id, domme.id)
        if domme_record is None:
            await interaction.response.send_message(
                embed=error_embed("That user is not a registered Domme."),
                ephemeral=True,
            )
            return

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_count = await self.bot.send_requests_repo.count_since(
            guild_id=interaction.guild.id,
            sub_user_id=interaction.user.id,
            domme_user_id=domme.id,
            since=since,
        )
        if recent_count >= _SEND_REQUEST_RATE_LIMIT:
            await interaction.response.send_message(
                embed=error_embed(
                    "Rate limit reached.",
                    f"You can only request {_SEND_REQUEST_RATE_LIMIT} send reviews from the same Domme in 24 hours.",
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        request_record = await self.bot.send_requests_repo.create(
            guild_id=interaction.guild.id,
            sub_user_id=interaction.user.id,
            domme_user_id=domme.id,
            amount_cents=dollars_to_cents(float(amount)),
            currency="USD",
            method=method.value,
            note=(note or "").strip() or None,
        )

        try:
            await domme.send(
                embed=registration_embed(
                    title="Rob | Send Request",
                    summary=f"{interaction.user.display_name} asked you to log a send.",
                    details=[
                        ("Amount", format_money_from_cents(request_record.amount_cents)),
                        ("Method", request_record.method),
                        ("Suggested /add", f"/add amount:{float(amount):.2f} method:{method.value} sub:{interaction.user.display_name}"),
                        ("Note", request_record.note or "No note provided."),
                    ],
                )
            )
        except discord.HTTPException:
            await self.bot.send_requests_repo.delete(request_record.id)
            await interaction.followup.send(
                embed=error_embed("Rob couldn't DM that Domme right now."),
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            embed=registration_embed(
                title="Rob | Request Sent",
                summary=f"Your request has been sent to {domme.mention}.",
                details=[("Method", method.value)],
            ),
            ephemeral=True,
        )
