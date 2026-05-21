from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from rob.ui.cards.errors import error_embed
from rob.ui.cards.registration import domme_registered_embed, registration_embed, throne_setup_embed

if TYPE_CHECKING:
    from rob.discord.client import RobBot


class ThroneSetupView(discord.ui.View):
    def __init__(self, *, creator_id: int, webhook_url: str, send_track_channel_id: int | None) -> None:
        super().__init__(timeout=1800)
        self.creator_id = creator_id
        self.webhook_url = webhook_url
        self.send_track_channel_id = send_track_channel_id

    @discord.ui.button(label="Continue Setup", style=discord.ButtonStyle.primary)
    async def continue_setup(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        body = (
            "To make sure Rob gets the right information, you'll need to set up the Webhook Integration in your Throne settings.\n\n"
            "Here's how:\n\n"
            "1. Head to https://throne.com/ and sign in.\n2. Go to Settings, then click Integrations.\n3. Scroll until you see Webhooks.\n"
            "4. Click Enable Webhooks.\n5. Under Subscriber URLs, click Add URL.\n6. Enter the almighty link below.\n"
            "7. Click Save Settings, then click Test Webhook and wait for the success message.\n\n"
            "Once done, come back here and I'll let you know if it worked.\n\n"
            f"The almighty link:\n```\n{self.webhook_url}\n```\nDid it work?"
        )
        await interaction.response.edit_message(
            embed=throne_setup_embed(body),
            view=ThroneVerifyView(self.creator_id, self.send_track_channel_id),
        )

    @discord.ui.button(label="Not Now", style=discord.ButtonStyle.secondary)
    async def not_now(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(
            embed=throne_setup_embed(
                "No worries — your Throne profile is linked, but tracking won't start until the webhook URL is added to Throne.\n\n"
                "You can run /register domme again when you're ready."
            ),
            view=None,
        )


class ThroneVerifyView(discord.ui.View):
    def __init__(self, creator_id: int, send_track_channel_id: int | None) -> None:
        super().__init__(timeout=1800)
        self.creator_id = creator_id
        self.send_track_channel_id = send_track_channel_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        bot = interaction.client
        creator = await bot.throne_creators_repo.get(self.creator_id)
        if creator and creator.last_successful_event_at:
            destination = f"<#{self.send_track_channel_id}>" if self.send_track_channel_id else "the send tracking channel"
            embed = throne_setup_embed(
                "That worked!\n\n"
                f"Your Throne sends will now appear in {destination} as soon as you receive them.\n\n"
                "Please read the information below so you know what Rob collects and how it's used."
            )
            embed.set_image(url="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExMDN5OW9vZTYyODl4MnRmd3A5aGVxeWVkNWF2eTY4ZnhwdXVpeW4wYyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/uLiEXaouJVkuA/giphy.gif")
            await interaction.response.edit_message(embed=embed, view=None)
            await interaction.followup.send(
                embed=registration_embed(
                    title="What Rob Collects",
                    summary="Rob only stores the information needed to track and display Throne sends inside this Discord server.",
                    details=[
                        ("Collected information", "- Your Discord user ID\n- Your Throne handle and creator ID\n- Public wishlist item names\n- Public wishlist item prices\n- Public wishlist item images, when available\n- Send/purchase amounts provided by Throne webhook events\n- Item names and item images from send events\n- Sender/display names provided by Throne, when available\n- Webhook status details, such as when Rob last received a successful event"),
                        ("How it is used", "- To post send notifications in the configured send tracking channel\n- To update Domme/Sub leaderboards\n- To prevent duplicate webhook events being counted twice\n- To help server staff troubleshoot tracking issues\n- To let you rebuild your webhook URL if it needs to be rotated"),
                        ("Important notes", "- Rob does not need your Throne password.\n- Rob cannot access private Throne account settings.\n- Your webhook URL should be treated like a secret.\n- If you think your webhook URL was shared accidentally, ask staff to rebuild it."),
                    ],
                )
            )
            return
        await interaction.response.edit_message(
            embed=throne_setup_embed(
                "Not seeing it yet.\n\nPlease make sure you clicked Save Settings in Throne, then click Test Webhook again. "
                "Once Throne shows a success message, press Yes here again."
            ),
            view=self,
        )

    @discord.ui.button(label="Not Yet", style=discord.ButtonStyle.secondary)
    async def not_yet(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.defer()


class RegistrationCog(commands.Cog):
    register_group = app_commands.Group(name="register", description="Register as a Domme or Sub.")

    def __init__(self, bot: RobBot) -> None:
        self.bot = bot

    @register_group.command(name="domme", description="Register a Domme Throne profile.")
    @app_commands.describe(throne="Your Throne profile URL or username.")
    async def register_domme(self, interaction: discord.Interaction, throne: str) -> None:
        if interaction.guild is None or interaction.user is None:
            await interaction.response.send_message(embed=error_embed("This command can only be used in a server."), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            result = await self.bot.registration_service.register_domme(
                guild_id=interaction.guild.id,
                discord_user_id=interaction.user.id,
                throne_input=throne,
            )
        except ValueError as exc:
            await interaction.followup.send(embed=error_embed("Domme registration could not be completed.", str(exc)), ephemeral=True)
            return

        if not result.webhook_url:
            await interaction.followup.send(embed=error_embed("Webhook URL setup is unavailable.", "Ask staff to verify THRONE_WEBHOOK_BASE_URL on the bot server."), ephemeral=True)
            return

        settings = await self.bot.guild_settings_repo.get(interaction.guild.id)
        try:
            await interaction.user.send(
                embed=throne_setup_embed(
                    "Howdy Partner!\n\nYou've received this DM because you've enabled Throne tracking for yourself. Before we can continue, we'll need you to do some extra steps inside Throne first."
                ),
                view=ThroneSetupView(
                    creator_id=result.creator.id,
                    webhook_url=result.webhook_url,
                    send_track_channel_id=settings.send_track_channel_id if settings else None,
                ),
            )
        except discord.HTTPException:
            await interaction.followup.send(
                embed=error_embed(
                    "You're registered, but Rob couldn't DM you.",
                    "Please enable Direct Messages, then run /register domme again.",
                ),
                ephemeral=True,
            )
            return

        await interaction.followup.send(embed=domme_registered_embed(), ephemeral=True)

    @register_group.command(name="sub", description="Register a sending name to claim sends.")
    @app_commands.describe(send_name="The exact name you use on Throne sends.")
    async def register_sub(self, interaction: discord.Interaction, send_name: str) -> None:
        if interaction.guild is None or interaction.user is None:
            await interaction.response.send_message(embed=error_embed("This command can only be used in a server."), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        try:
            result = await self.bot.registration_service.register_sub(
                guild_id=interaction.guild.id,
                discord_user_id=interaction.user.id,
                send_name=send_name,
            )
        except ValueError as exc:
            await interaction.followup.send(embed=error_embed("Sub registration could not be completed.", str(exc)), ephemeral=True)
            return

        await interaction.followup.send(
            embed=registration_embed(
                title="Rob | Sub Registered",
                summary="Your send-claim name is now active.",
                details=[("Tracked Name", result.sub.send_name)],
            ),
            ephemeral=True,
        )
