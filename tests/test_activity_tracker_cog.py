from __future__ import annotations

import asyncio
from types import SimpleNamespace

from rob.discord.cogs.activity_tracker import ActivityTrackerCog


class _FakeBotState:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def set_value(self, key: str, value: str) -> None:
        self.values[key] = value


def test_activity_tracker_records_last_active_timestamp():
    bot_state = _FakeBotState()
    bot = SimpleNamespace(bot_state_repo=bot_state)
    cog = ActivityTrackerCog(bot)
    author = SimpleNamespace(id=42, bot=False)
    guild = SimpleNamespace(id=99)
    message = SimpleNamespace(author=author, guild=guild)

    asyncio.run(cog.on_message(message))

    key = "activity:99:user:42:last_active"
    assert key in bot_state.values
    assert "T" in bot_state.values[key]


def test_activity_tracker_ignores_bots_and_dms():
    bot_state = _FakeBotState()
    bot = SimpleNamespace(bot_state_repo=bot_state)
    cog = ActivityTrackerCog(bot)

    asyncio.run(cog.on_message(SimpleNamespace(author=SimpleNamespace(id=1, bot=True), guild=SimpleNamespace(id=1))))
    asyncio.run(cog.on_message(SimpleNamespace(author=SimpleNamespace(id=2, bot=False), guild=None)))

    assert bot_state.values == {}
