from __future__ import annotations

import discord

from rob.ui.render import RenderedMessage
from rob.ui.cards.registration import throne_setup_card


class _DummyView(discord.ui.View):
    pass


def test_with_view_overrides_view_without_duplicate_kwargs_issue():
    base = RenderedMessage(content="hi", mode="embed_fallback")
    msg = base.with_view(_DummyView())
    kwargs = msg.send_kwargs()
    assert "view" in kwargs
    assert isinstance(kwargs["view"], discord.ui.View)


def test_v2_edit_kwargs_clear_legacy_fields():
    msg = RenderedMessage(content="x", mode="components_v2")
    kwargs = msg.edit_kwargs()
    assert kwargs["content"] is None
    assert kwargs["embed"] is None
    assert kwargs["embeds"] is None
    assert kwargs["attachments"] is None


def test_setup_success_card_accepts_image_url_in_v2_or_fallback():
    msg = throne_setup_card("ok", image_url="https://example.com/test.gif")
    if msg.mode == "embed_fallback":
        assert msg.embed is not None
        assert msg.embed.image.url == "https://example.com/test.gif"
    else:
        assert msg.embed is None
        assert msg.view is not None
