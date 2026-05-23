from __future__ import annotations

import asyncio
from types import SimpleNamespace

import discord

from rob.discord.cogs.registration import RegistrationCog


class _FakeResponse:
    def __init__(self):
        self.messages: list[dict] = []
        self.deferred = False

    async def send_message(self, **kwargs):
        self.messages.append(kwargs)

    async def defer(self, *, ephemeral: bool = False):
        self.deferred = ephemeral


class _FakeFollowup:
    def __init__(self):
        self.messages: list[dict] = []

    async def send(self, **kwargs):
        self.messages.append(kwargs)


class _FakeUser:
    def __init__(self, user_id: int = 123):
        self.id = user_id
        self.sent_messages: list[dict] = []

    async def send(self, **kwargs):
        self.sent_messages.append(kwargs)


class _FakeInteraction:
    def __init__(self):
        self.guild = SimpleNamespace(id=1)
        self.user = _FakeUser()
        self.response = _FakeResponse()
        self.followup = _FakeFollowup()


class _FakeRegistrationService:
    def __init__(self):
        self.sub_calls: list[dict] = []
        self.domme_calls: list[dict] = []

    async def register_sub(self, **kwargs):
        self.sub_calls.append(kwargs)
        return SimpleNamespace(sub=SimpleNamespace(send_name=kwargs["send_name"]))

    async def register_domme(self, **kwargs):
        self.domme_calls.append(kwargs)
        return SimpleNamespace(
            creator=SimpleNamespace(id=99),
            webhook_url="https://example.com/webhook",
        )


class _FakeBot:
    def __init__(self, settings):
        self.guild_settings_repo = SimpleNamespace(get=self._get_settings)
        self.registration_service = _FakeRegistrationService()
        self._settings = settings

    async def _get_settings(self, guild_id: int):
        del guild_id
        return self._settings


def test_register_domme_denied_when_role_missing_from_config(monkeypatch):
    monkeypatch.setattr("rob.discord.cogs.registration.member_has_role", lambda *_args, **_kwargs: True)
    interaction = _FakeInteraction()
    bot = _FakeBot(SimpleNamespace(domme_role_id=None, sub_role_id=22, send_track_channel_id=77))
    cog = RegistrationCog(bot)

    asyncio.run(RegistrationCog.register_domme.callback(cog, interaction, throne="pat"))

    assert interaction.response.messages[0]["ephemeral"] is True
    assert interaction.response.messages[0]["view"] is not None
    assert bot.registration_service.domme_calls == []


def test_register_domme_denied_when_member_lacks_configured_role(monkeypatch):
    monkeypatch.setattr("rob.discord.cogs.registration.member_has_role", lambda *_args, **_kwargs: False)
    interaction = _FakeInteraction()
    bot = _FakeBot(SimpleNamespace(domme_role_id=11, sub_role_id=22, send_track_channel_id=77))
    cog = RegistrationCog(bot)

    asyncio.run(RegistrationCog.register_domme.callback(cog, interaction, throne="pat"))

    assert interaction.response.messages[0]["ephemeral"] is True
    assert interaction.response.messages[0]["view"] is not None
    assert bot.registration_service.domme_calls == []


def test_register_sub_allowed_when_member_has_configured_role(monkeypatch):
    monkeypatch.setattr("rob.discord.cogs.registration.member_has_role", lambda *_args, **_kwargs: True)
    interaction = _FakeInteraction()
    bot = _FakeBot(SimpleNamespace(domme_role_id=11, sub_role_id=22, send_track_channel_id=77))
    cog = RegistrationCog(bot)

    asyncio.run(RegistrationCog.register_sub.callback(cog, interaction, send_name="gifter_name"))

    assert interaction.response.deferred is True
    assert bot.registration_service.sub_calls[0]["send_name"] == "gifter_name"
    assert interaction.followup.messages[0]["ephemeral"] is True


def test_register_sub_denied_when_role_missing_from_config(monkeypatch):
    monkeypatch.setattr("rob.discord.cogs.registration.member_has_role", lambda *_args, **_kwargs: True)
    interaction = _FakeInteraction()
    bot = _FakeBot(SimpleNamespace(domme_role_id=11, sub_role_id=None, send_track_channel_id=77))
    cog = RegistrationCog(bot)

    asyncio.run(RegistrationCog.register_sub.callback(cog, interaction, send_name="gifter_name"))

    assert interaction.response.messages[0]["ephemeral"] is True
    assert interaction.response.messages[0]["view"] is not None
    assert bot.registration_service.sub_calls == []


def test_register_sub_denied_when_member_lacks_configured_role(monkeypatch):
    monkeypatch.setattr("rob.discord.cogs.registration.member_has_role", lambda *_args, **_kwargs: False)
    interaction = _FakeInteraction()
    bot = _FakeBot(SimpleNamespace(domme_role_id=11, sub_role_id=22, send_track_channel_id=77))
    cog = RegistrationCog(bot)

    asyncio.run(RegistrationCog.register_sub.callback(cog, interaction, send_name="gifter_name"))

    assert interaction.response.messages[0]["ephemeral"] is True
    assert interaction.response.messages[0]["view"] is not None
    assert bot.registration_service.sub_calls == []


def test_register_domme_allowed_when_member_has_configured_role(monkeypatch):
    monkeypatch.setattr("rob.discord.cogs.registration.member_has_role", lambda *_args, **_kwargs: True)
    interaction = _FakeInteraction()
    bot = _FakeBot(SimpleNamespace(domme_role_id=11, sub_role_id=22, send_track_channel_id=77))
    cog = RegistrationCog(bot)

    asyncio.run(RegistrationCog.register_domme.callback(cog, interaction, throne="pat"))

    assert interaction.response.deferred is True
    assert bot.registration_service.domme_calls[0]["throne_input"] == "pat"
    assert interaction.user.sent_messages
    assert interaction.followup.messages[0]["ephemeral"] is True
    assert isinstance(interaction.followup.messages[0]["view"], discord.ui.LayoutView)
