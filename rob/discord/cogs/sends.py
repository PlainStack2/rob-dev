from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands
from discord.ext import commands

from rob.discord.permissions import is_staff_member
from rob.services.send_display import build_sub_display, format_send_source
from rob.ui.cards.errors import error_card, error_permission
from rob.ui.cards.registration import registration_card
from rob.ui.cards.send import send_details_card, send_details_list_card
from rob.ui.copy import PERMISSION_ROLE_MISSING
from rob.utils.money import dollars_to_cents, format_money_from_cents

if TYPE_CHECKING:
    from rob.discord.client import RobBot

_MANUAL_METHODS = ["cashapp", "venmo", "paypal", "onlyfans", "loyalfans", "youpay", "other"]
_REQUEST_METHODS = ["cashapp", "venmo", "paypal", "onlyfans", "loyalfans", "youpay", "other"]


class _SendRequestReviewView(discord.ui.LayoutView):
    def __init__(self, *, bot: "RobBot", request_id: int, guild_id: int, domme_id: int | None) -> None:
        super().__init__(timeout=86400)
        self.bot = bot
        self.request_id = request_id
        self.guild_id = guild_id
        self.domme_id = domme_id

    @discord.ui.button(label="Approve & Log", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        out = await self.bot.send_request_service.approve(
            request_id=self.request_id,
            guild_id=self.guild_id,
            domme_id=self.domme_id,
        )
        await interaction.response.send_message(
            **registration_card(
                title="Send request approved",
                summary="Rob logged the send.",
                details=[("Status", out.status)],
            ).send_kwargs(),
            ephemeral=True,
        )

    @discord.ui.button(label="Ignore", style=discord.ButtonStyle.secondary)
    async def ignore(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        out = await self.bot.send_request_service.ignore(request_id=self.request_id)
        await interaction.response.send_message(
            **registration_card(
                title="Send request ignored",
                summary="Rob marked the request as ignored.",
                details=[("Status", out.status)],
            ).send_kwargs(),
            ephemeral=True,
        )


class SendsCog(commands.Cog):
    send_group = app_commands.Group(name="send", description="Inspect send details.")

    def __init__(self, bot: RobBot) -> None:
        self.bot = bot

    @staticmethod
    def _is_involved_user(user_id: int, send) -> bool:
        return user_id in {send.domme_user_id, send.sub_user_id}

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
                **error_card("This command can only be used in a server.").send_kwargs(),
                ephemeral=True,
            )
            return

        domme = await self.bot.dommes_repo.get_by_user_id(
            interaction.guild.id,
            interaction.user.id,
        )
        if domme is None:
            await interaction.response.send_message(
                **error_card("Only registered Dommes can use `/add`.").send_kwargs(),
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
                **error_card("That send could not be recorded.").send_kwargs(),
                ephemeral=True,
            )
            return

        queue_label = (
            "queued for after maintenance"
            if send.discord_post_status == "queued_maintenance"
            else "queued for posting"
        )
        await interaction.followup.send(
            **registration_card(
                title="Rob | Send Logged",
                summary=f"Recorded {format_money_from_cents(send.amount_cents)} and {queue_label}.",
                details=[
                    ("Method", method.value),
                    ("Sender", send.sub_name or "Unclaimed"),
                ],
            ).send_kwargs(),
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
                **error_card("This command can only be used in a server.").send_kwargs(),
                ephemeral=True,
            )
            return

        domme_record = await self.bot.dommes_repo.get_by_user_id(interaction.guild.id, domme.id)
        if domme_record is None:
            await interaction.response.send_message(
                **error_card("That user is not a registered Domme.").send_kwargs(),
                ephemeral=True,
            )
            return

        if await self.bot.send_request_service.is_rate_limited(
            guild_id=interaction.guild.id,
            sub_user_id=interaction.user.id,
            domme_user_id=domme.id,
        ):
            await interaction.response.send_message(
                **error_card(
                    "Rate limit reached.",
                    "You can only request 3 send reviews from the same Domme in 24 hours.",
                ).send_kwargs(),
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
                **registration_card(
                    title="Rob | Send Request",
                    summary=f"{interaction.user.display_name} asked you to log a send.",
                    details=[
                        ("Amount", format_money_from_cents(request_record.amount_cents)),
                        ("Method", request_record.method),
                        (
                            "Suggested /add",
                            f"/add amount:{float(amount):.2f} method:{method.value} sub:{interaction.user.display_name}",
                        ),
                        ("Note", request_record.note or "No note provided."),
                    ],
                    view=_SendRequestReviewView(
                        bot=self.bot,
                        request_id=request_record.id,
                        guild_id=interaction.guild.id,
                        domme_id=domme_record.id,
                    ),
                ).send_kwargs()
            )
        except discord.HTTPException:
            await self.bot.send_requests_repo.delete(request_record.id)
            await interaction.followup.send(
                **error_card("Rob couldn't DM that Domme right now.").send_kwargs(),
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            **registration_card(
                title="Rob | Request Sent",
                summary=f"Your request has been sent to {domme.mention}.",
                details=[("Method", method.value)],
            ).send_kwargs(),
            ephemeral=True,
        )

    @send_group.command(name="details", description="Show public send details or recent sends.")
    @app_commands.describe(
        user="Optional user to inspect.",
        send_id="Optional public Rob Send ID such as ROB-000151-8FECFB24.",
        limit="How many sends to show when listing recent sends.",
    )
    async def send_details(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None,
        send_id: Optional[str] = None,
        limit: app_commands.Range[int, 1, 10] = 5,
    ) -> None:
        if interaction.guild is None or interaction.user is None:
            await interaction.response.send_message(
                **error_card("This command can only be used in a server.").send_kwargs(),
                ephemeral=True,
            )
            return

        if send_id and user is not None:
            await interaction.response.send_message(
                **error_card("Choose either `send_id` or `user`, not both.").send_kwargs(),
                ephemeral=True,
            )
            return

        settings = await self.bot.guild_settings_repo.get(interaction.guild.id)
        staff = is_staff_member(interaction.user, settings)

        if send_id:
            send = await self.bot.sends_repo.get_by_public_id(send_id)
            if send is None and staff and send_id.strip().isdigit():
                send = await self.bot.sends_repo.get_by_id(int(send_id.strip()))
            if send is None:
                await interaction.response.send_message(
                    **error_card("Rob could not find that send ID.").send_kwargs(),
                    ephemeral=True,
                )
                return
            send = await self.bot.sends_repo.ensure_public_send_id(send)
            if not staff and not self._is_involved_user(interaction.user.id, send):
                await interaction.response.send_message(
                    **error_permission(PERMISSION_ROLE_MISSING).send_kwargs(),
                    ephemeral=True,
                )
                return

            rendered = send_details_card(
                send=send,
                domme_label=f"<@{send.domme_user_id}>",
                sub_display=build_sub_display(
                    send,
                    test_gifter_usernames=self.bot.settings.throne_test_gifter_usernames,
                ),
                source_label=format_send_source(send),
                include_internal=staff,
            )
            await interaction.response.send_message(
                **rendered.send_kwargs(),
                ephemeral=staff or send.is_private,
            )
            return

        target_user = user or interaction.user
        if target_user.id != interaction.user.id and not staff:
            await interaction.response.send_message(
                **error_permission(PERMISSION_ROLE_MISSING).send_kwargs(),
                ephemeral=True,
            )
            return

        sends = await self.bot.sends_repo.list_sends_for_user(
            interaction.guild.id,
            target_user.id,
            limit=int(limit),
        )
        if not staff and target_user.id != interaction.user.id:
            sends = [send for send in sends if not send.is_private]

        domme_lookup = {send.domme_user_id: f"<@{send.domme_user_id}>" for send in sends}
        rendered = send_details_list_card(
            title_label=target_user.mention,
            sends=sends,
            domme_lookup=domme_lookup,
        )
        await interaction.response.send_message(
            **rendered.send_kwargs(),
            ephemeral=(staff and target_user.id != interaction.user.id)
            or any(send.is_private for send in sends),
        )
