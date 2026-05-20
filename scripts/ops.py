from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass

from rob.config.settings import configure_logging, load_base_settings
from rob.database.connection import Database
from rob.database.repositories import (
    BotStateRepository,
    CountingRepository,
    GuildSettingsRepository,
    SendsRepository,
)
from rob.services.maintenance_service import MaintenanceService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rob backend operations.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show database, maintenance, and queue status.")

    maintenance = subparsers.add_parser("maintenance", help="Manage maintenance mode.")
    maintenance_subparsers = maintenance.add_subparsers(dest="maintenance_command", required=True)
    maintenance_subparsers.add_parser("status", help="Show maintenance mode state.")
    maintenance_on = maintenance_subparsers.add_parser("on", help="Enable maintenance mode.")
    maintenance_on.add_argument("reason", nargs="?", default="", help="Optional maintenance reason.")
    maintenance_subparsers.add_parser("off", help="Disable maintenance mode.")

    queue = subparsers.add_parser("queue", help="Inspect or release queued sends.")
    queue_subparsers = queue.add_subparsers(dest="queue_command", required=True)
    queue_subparsers.add_parser("status", help="Show queue counts.")
    queue_subparsers.add_parser("flush", help="Release queued maintenance sends to pending.")

    leaderboard = subparsers.add_parser("leaderboard", help="Leaderboard operations.")
    leaderboard_subparsers = leaderboard.add_subparsers(dest="leaderboard_command", required=True)
    leaderboard_subparsers.add_parser("refresh", help="Request a leaderboard refresh from the bot.")

    count = subparsers.add_parser("count", help="Counting operations.")
    count_subparsers = count.add_subparsers(dest="count_command", required=True)
    count_status = count_subparsers.add_parser("status", help="Show counting state.")
    count_status.add_argument("--guild-id", type=int, default=None)
    count_set = count_subparsers.add_parser("set", help="Set the current counting number.")
    count_set.add_argument("number", type=int)
    count_set.add_argument("--guild-id", type=int, default=None)

    return parser


@dataclass(frozen=True)
class OperationsContext:
    database: Database
    bot_state: BotStateRepository
    maintenance: MaintenanceService
    sends: SendsRepository
    guild_settings: GuildSettingsRepository
    counting: CountingRepository


async def create_context() -> OperationsContext:
    settings = load_base_settings()
    configure_logging(settings.log_level)
    database = Database(settings.database_url)
    await database.connect()
    bot_state = BotStateRepository(database)
    return OperationsContext(
        database=database,
        bot_state=bot_state,
        maintenance=MaintenanceService(bot_state),
        sends=SendsRepository(database),
        guild_settings=GuildSettingsRepository(database),
        counting=CountingRepository(database),
    )


async def resolve_guild_id(ctx: OperationsContext, guild_id: int | None) -> int:
    if guild_id is not None:
        return guild_id
    guild_ids = await ctx.guild_settings.list_guild_ids()
    if len(guild_ids) == 1:
        return guild_ids[0]
    if not guild_ids:
        raise RuntimeError("No guild_settings rows exist yet. Add one first or pass --guild-id.")
    raise RuntimeError("Multiple guilds exist. Pass --guild-id explicitly.")


async def handle_status(ctx: OperationsContext) -> None:
    healthy = await ctx.database.health_check()
    maintenance = await ctx.maintenance.get_state()
    queue = await ctx.sends.count_statuses()
    print(f"database_ok={healthy}")
    print(f"maintenance_mode={'on' if maintenance.enabled else 'off'}")
    print(f"maintenance_reason={maintenance.reason or ''}")
    print(
        "queue_counts="
        f"pending:{queue.pending},"
        f"queued_maintenance:{queue.queued_maintenance},"
        f"posted:{queue.posted},"
        f"failed:{queue.failed},"
        f"ignored:{queue.ignored}"
    )


async def handle_maintenance(ctx: OperationsContext, args: argparse.Namespace) -> None:
    if args.maintenance_command == "status":
        state = await ctx.maintenance.get_state()
        print(f"maintenance_mode={'on' if state.enabled else 'off'}")
        print(f"maintenance_reason={state.reason or ''}")
        return
    if args.maintenance_command == "on":
        await ctx.maintenance.enable(reason=args.reason or "")
        print("maintenance_mode=on")
        if args.reason:
            print(f"maintenance_reason={args.reason}")
        return
    if args.maintenance_command == "off":
        await ctx.maintenance.disable()
        print("maintenance_mode=off")
        return
    raise RuntimeError(f"Unsupported maintenance command: {args.maintenance_command}")


async def handle_queue(ctx: OperationsContext, args: argparse.Namespace) -> None:
    if args.queue_command == "status":
        queue = await ctx.sends.count_statuses()
        print(f"pending={queue.pending}")
        print(f"queued_maintenance={queue.queued_maintenance}")
        print(f"posted={queue.posted}")
        print(f"failed={queue.failed}")
        print(f"ignored={queue.ignored}")
        return
    if args.queue_command == "flush":
        if await ctx.maintenance.is_enabled():
            raise RuntimeError("Maintenance mode is still on. Disable it before flushing the queue.")
        released = await ctx.sends.release_queued_maintenance()
        print(f"released={released}")
        return
    raise RuntimeError(f"Unsupported queue command: {args.queue_command}")


async def handle_leaderboard(ctx: OperationsContext, args: argparse.Namespace) -> None:
    if args.leaderboard_command == "refresh":
        await ctx.maintenance.request_leaderboard_refresh()
        print("leaderboard_refresh=requested")
        return
    raise RuntimeError(f"Unsupported leaderboard command: {args.leaderboard_command}")


async def handle_count(ctx: OperationsContext, args: argparse.Namespace) -> None:
    guild_id = await resolve_guild_id(ctx, getattr(args, "guild_id", None))
    if args.count_command == "status":
        state = await ctx.counting.get(guild_id)
        if state is None:
            print(f"guild_id={guild_id}")
            print("counting_state=missing")
            return
        print(f"guild_id={guild_id}")
        print(f"enabled={state.is_enabled}")
        print(f"channel_id={state.channel_id or 0}")
        print(f"current_number={state.current_number}")
        print(f"last_user_id={state.last_user_id or 0}")
        return
    if args.count_command == "set":
        existing = await ctx.counting.get(guild_id)
        channel_id = existing.channel_id if existing is not None else None
        is_enabled = existing.is_enabled if existing is not None else channel_id is not None
        await ctx.counting.upsert(
            guild_id=guild_id,
            channel_id=channel_id,
            current_number=max(0, int(args.number)),
            last_user_id=None,
            is_enabled=is_enabled,
            pending_restore=False,
        )
        print(f"guild_id={guild_id}")
        print(f"current_number={max(0, int(args.number))}")
        return
    raise RuntimeError(f"Unsupported count command: {args.count_command}")


async def main_async() -> None:
    parser = build_parser()
    args = parser.parse_args()
    ctx = await create_context()
    try:
        if args.command == "status":
            await handle_status(ctx)
        elif args.command == "maintenance":
            await handle_maintenance(ctx, args)
        elif args.command == "queue":
            await handle_queue(ctx, args)
        elif args.command == "leaderboard":
            await handle_leaderboard(ctx, args)
        elif args.command == "count":
            await handle_count(ctx, args)
        else:
            raise RuntimeError(f"Unsupported command: {args.command}")
    finally:
        await ctx.database.close()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
