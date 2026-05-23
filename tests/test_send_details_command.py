from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from rob.database.repositories.models import SendRecord
from rob.discord.cogs.sends import SendsCog


class _FakeResponse:
    def __init__(self):
        self.messages: list[dict] = []

    async def send_message(self, **kwargs):
        self.messages.append(kwargs)


class _FakeInteraction:
    def __init__(self, user_id: int = 10):
        self.guild = SimpleNamespace(id=1)
        self.user = SimpleNamespace(id=user_id, mention=f"<@{user_id}>")
        self.response = _FakeResponse()


class _FakeSendsRepo:
    def __init__(self, send: SendRecord):
        self.send = send

    async def get_by_public_id(self, public_id: str):
        if public_id == self.send.public_send_id:
            return self.send
        return None

    async def get_by_id(self, send_id: int):
        if send_id == self.send.id:
            return self.send
        return None

    async def ensure_public_send_id(self, send: SendRecord):
        return send

    async def list_sends_for_user(self, guild_id: int, user_id: int, *, limit: int = 5):
        del guild_id, user_id, limit
        return [self.send]


class _FakeBot:
    def __init__(self, send: SendRecord):
        self.sends_repo = _FakeSendsRepo(send)
        self.guild_settings_repo = SimpleNamespace(get=self._get_settings)
        self.settings = SimpleNamespace(throne_test_gifter_usernames=("marie_123",))

    async def _get_settings(self, guild_id: int):
        del guild_id
        return SimpleNamespace(mod_role_id=999)


def _send(*, domme_user_id: int = 10, sub_user_id: int | None = 20, sub_name: str | None = "gifter_name", is_private: bool = False) -> SendRecord:
    now = datetime.now(timezone.utc)
    return SendRecord(
        1,
        1,
        None,
        domme_user_id,
        None,
        sub_user_id,
        sub_name,
        1099,
        "USD",
        None,
        "throne_webhook",
        "Flowers",
        None,
        None,
        "evt_1",
        "hash_1",
        is_private,
        False,
        now,
        now,
        "posted",
        None,
        None,
        None,
        now,
    )


def test_send_details_single_send_is_not_ephemeral_by_default(monkeypatch):
    monkeypatch.setattr("rob.discord.cogs.sends.is_staff_member", lambda *_args, **_kwargs: False)
    send = _send()
    interaction = _FakeInteraction(user_id=10)
    cog = SendsCog(_FakeBot(send))

    asyncio.run(SendsCog.send_details.callback(cog, interaction, user=None, send_id=send.public_send_id, limit=5))

    assert interaction.response.messages[0]["ephemeral"] is False
    container = interaction.response.messages[0]["view"].children[0]
    contents = "\n".join(str(getattr(child, "content", "")) for child in container.children)
    assert "**Rob Send ID:** ROB-" in contents


def test_send_details_denies_non_staff_viewing_someone_else(monkeypatch):
    monkeypatch.setattr("rob.discord.cogs.sends.is_staff_member", lambda *_args, **_kwargs: False)
    send = _send(domme_user_id=99, sub_user_id=77)
    interaction = _FakeInteraction(user_id=10)
    cog = SendsCog(_FakeBot(send))

    asyncio.run(SendsCog.send_details.callback(cog, interaction, user=None, send_id=send.public_send_id, limit=5))

    assert interaction.response.messages[0]["ephemeral"] is True
    assert interaction.response.messages[0]["view"] is not None


def test_send_details_allows_staff_and_shows_internal_fields(monkeypatch):
    monkeypatch.setattr("rob.discord.cogs.sends.is_staff_member", lambda *_args, **_kwargs: True)
    send = _send(domme_user_id=99, sub_user_id=77)
    interaction = _FakeInteraction(user_id=10)
    cog = SendsCog(_FakeBot(send))

    asyncio.run(SendsCog.send_details.callback(cog, interaction, user=None, send_id=send.public_send_id, limit=5))

    assert interaction.response.messages[0]["ephemeral"] is True
    container = interaction.response.messages[0]["view"].children[0]
    contents = "\n".join(str(getattr(child, "content", "")) for child in container.children)
    assert "Database ID:" in contents
    assert "Event ID:" in contents


def test_send_details_allows_staff_raw_database_id_lookup(monkeypatch):
    monkeypatch.setattr("rob.discord.cogs.sends.is_staff_member", lambda *_args, **_kwargs: True)
    send = _send(domme_user_id=99, sub_user_id=77)
    interaction = _FakeInteraction(user_id=10)
    cog = SendsCog(_FakeBot(send))

    asyncio.run(SendsCog.send_details.callback(cog, interaction, user=None, send_id=str(send.id), limit=5))

    assert interaction.response.messages[0]["ephemeral"] is True
    container = interaction.response.messages[0]["view"].children[0]
    contents = "\n".join(str(getattr(child, "content", "")) for child in container.children)
    assert "**Rob Send ID:** ROB-" in contents
