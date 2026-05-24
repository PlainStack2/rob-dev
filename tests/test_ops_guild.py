from __future__ import annotations

import asyncio
from types import SimpleNamespace

from scripts.ops import LiveGuildChannel, LiveGuildScanResult, build_parser, handle_guild


class _FakeGuildSettings:
    def __init__(self):
        self.calls: list[tuple[int, str, int | None]] = []

    async def get(self, guild_id: int):
        assert guild_id == 1
        return SimpleNamespace(
            guild_id=1,
            registration_channel_id=None,
            leaderboard_channel_id=22,
            send_track_channel_id=None,
            counting_channel_id=None,
            report_channel_id=None,
            warn_log_channel_id=None,
        )

    async def set_channel_id(self, guild_id: int, field_name: str, channel_id: int | None):
        self.calls.append((guild_id, field_name, channel_id))
        return SimpleNamespace(**{field_name: channel_id})


def test_guild_parser_accepts_scan_and_set_channel():
    parser = build_parser()

    args = parser.parse_args(["guild", "scan", "--guild-id", "1"])
    assert args.command == "guild"
    assert args.guild_command == "scan"
    assert args.guild_id == 1

    args = parser.parse_args(
        [
            "guild",
            "set-channel",
            "--guild-id",
            "1",
            "--field",
            "leaderboard_channel_id",
            "--channel-id",
            "222",
        ]
    )
    assert args.command == "guild"
    assert args.guild_command == "set-channel"
    assert args.field == "leaderboard_channel_id"
    assert args.channel_id == 222


def test_guild_scan_reports_suggested_commands(capsys, monkeypatch):
    async def _fake_live_scan(_guild_id: int):
        return LiveGuildScanResult(
            guild_id=1,
            guild_name="Rob Test Server",
            channels=(
                LiveGuildChannel(channel_id=22, name="leaderboard", kind="TextChannel"),
                LiveGuildChannel(channel_id=33, name="send-tracker", kind="TextChannel"),
                LiveGuildChannel(channel_id=44, name="counting", kind="TextChannel"),
            ),
        )

    monkeypatch.setattr("scripts.ops.fetch_live_guild_scan", _fake_live_scan)
    ctx = SimpleNamespace(guild_settings=_FakeGuildSettings())
    args = SimpleNamespace(guild_command="scan", guild_id=1)

    asyncio.run(handle_guild(ctx, args))

    out = capsys.readouterr().out
    assert "Guild Scan" in out
    assert "leaderboard_channel_id=22" in out
    assert "send_track_channel_id_suggested=33" in out
    assert "rob guild set-channel --guild-id 1 --field send_track_channel_id --channel-id 33" in out


def test_guild_set_channel_updates_db(capsys):
    guild_settings = _FakeGuildSettings()
    ctx = SimpleNamespace(guild_settings=guild_settings)
    args = SimpleNamespace(
        guild_command="set-channel",
        guild_id=1,
        field="leaderboard_channel_id",
        channel_id=222,
        clear=False,
    )

    asyncio.run(handle_guild(ctx, args))

    assert guild_settings.calls == [(1, "leaderboard_channel_id", 222)]
    out = capsys.readouterr().out
    assert "updated=true" in out
    assert "field=leaderboard_channel_id" in out
