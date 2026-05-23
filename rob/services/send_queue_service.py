from __future__ import annotations

import asyncio
import logging

import discord

from rob.database.repositories.guild_settings import GuildSettingsRepository
from rob.database.repositories.sends import SendsRepository
from rob.services.leaderboard_service import LeaderboardService
from rob.services.maintenance_service import MaintenanceService
from rob.services.send_display import build_sub_display
from rob.ui.cards.send import send_card

log = logging.getLogger(__name__)


class SendQueueService:
    def __init__(
        self,
        *,
        bot: discord.Client,
        sends: SendsRepository,
        guild_settings: GuildSettingsRepository,
        maintenance: MaintenanceService,
        leaderboard_service: LeaderboardService,
        test_gifter_usernames: tuple[str, ...] = (),
        poll_interval_seconds: float = 5.0,
    ) -> None:
        self.bot = bot
        self.sends = sends
        self.guild_settings = guild_settings
        self.maintenance = maintenance
        self.leaderboard_service = leaderboard_service
        self.test_gifter_usernames = test_gifter_usernames
        self.poll_interval_seconds = poll_interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._stopping = False

    async def start(self) -> None:
        if self._task is not None:
            return
        self._stopping = False
        self._task = asyncio.create_task(self._run(), name="rob-send-queue")

    async def stop(self) -> None:
        self._stopping = True
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def _run(self) -> None:
        await self.bot.wait_until_ready()
        while not self._stopping:
            try:
                await self.process_cycle()
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Send queue cycle failed.")
            await asyncio.sleep(self.poll_interval_seconds)

    async def process_cycle(self) -> None:
        if not await self.maintenance.is_enabled():
            released = await self.sends.release_queued_maintenance()
            if released:
                log.info("Released %s queued maintenance send(s).", released)

        pending = await self.sends.fetch_for_status("pending", limit=50)
        refreshed_guild_ids: set[int] = set()

        for send in pending:
            ok = await self._post_send(send)
            if ok:
                refreshed_guild_ids.add(send.guild_id)

        if await self.maintenance.consume_leaderboard_refresh_request():
            await self.leaderboard_service.refresh_all_guilds()
            return

        for guild_id in sorted(refreshed_guild_ids):
            await self.leaderboard_service.refresh_guild(guild_id)

    async def _post_send(self, send) -> bool:
        settings = await self.guild_settings.get(send.guild_id)
        if settings is None or settings.send_track_channel_id is None:
            await self.sends.mark_failed(send.id, error="Missing send tracking channel configuration.")
            return False

        guild = self.bot.get_guild(send.guild_id)
        if guild is None:
            await self.sends.mark_failed(send.id, error="Guild not available to bot.")
            return False

        channel = guild.get_channel(settings.send_track_channel_id)
        if channel is None:
            try:
                channel = await guild.fetch_channel(settings.send_track_channel_id)
            except (discord.NotFound, discord.HTTPException) as exc:
                await self.sends.mark_failed(send.id, error=f"Send tracking channel unavailable: {exc}")
                return False

        if not isinstance(channel, discord.TextChannel):
            await self.sends.mark_failed(send.id, error="Configured send tracking channel is not a text channel.")
            return False

        previous_leader = await self.leaderboard_service.get_current_leader(send.guild_id)
        try:
            msg = send_card(
                send=send,
                domme_label=f"<@{send.domme_user_id}>",
                sub_display=build_sub_display(
                    send,
                    test_gifter_usernames=self.test_gifter_usernames,
                ),
            )
            message = await channel.send(**msg.send_kwargs())
        except discord.HTTPException as exc:
            await self.sends.mark_failed(send.id, error=f"Discord post failed: {exc}")
            return False

        await self.sends.mark_posted(send.id, message_id=message.id)
        await self.leaderboard_service.maybe_post_leader_alert(
            send.guild_id,
            previous_leader_user_id=previous_leader.user_id if previous_leader is not None else None,
        )
        return True
