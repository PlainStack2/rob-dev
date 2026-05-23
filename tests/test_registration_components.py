from __future__ import annotations

from datetime import datetime, timezone

import discord

from rob.database.repositories.models import SendRequestRecord
from rob.discord.cogs.sends import add_send_request_review_actions
from rob.discord.cogs.registration import add_setup_buttons
from rob.ui.cards.registration import domme_registered_card, registration_card, throne_setup_card
from rob.ui.cards.send_request import send_request_review_card
from rob.ui.copy import DOMME_REGISTERED_BODY, DOMME_REGISTERED_TITLE


def test_add_setup_buttons_creates_container_then_action_row_not_top_level_buttons():
    msg = throne_setup_card("setup")
    add_setup_buttons(msg.view, creator_id=1, webhook_url="https://example.com/webhook", send_track_channel_id=123)
    assert type(msg.view.children[0]).__name__ == "Container"
    assert type(msg.view.children[1]).__name__ == "ActionRow"
    assert all(isinstance(child, discord.ui.Button) for child in msg.view.children[1].children)
    assert all(type(child).__name__ != "Button" for child in msg.view.children)


def test_registration_card_has_no_footer_unless_explicit():
    msg = registration_card(title="Rob | Registered", summary="All set.")
    contents = "\n".join(str(getattr(ch, "content", "")) for ch in msg.view.children[0].children)
    assert "-#" not in contents

    msg = registration_card(
        title="Rob | Registered",
        summary="All set.",
        footer="Explicit footer only",
    )
    contents = "\n".join(str(getattr(ch, "content", "")) for ch in msg.view.children[0].children)
    assert "-# Explicit footer only" in contents


def test_domme_registered_card_has_no_footer_unless_explicit():
    msg = domme_registered_card()
    contents = "\n".join(str(getattr(ch, "content", "")) for ch in msg.view.children[0].children)
    assert f"## {DOMME_REGISTERED_TITLE}" in contents
    assert DOMME_REGISTERED_BODY in contents
    assert "-#" not in contents

    msg = domme_registered_card(footer="Explicit footer only")
    contents = "\n".join(str(getattr(ch, "content", "")) for ch in msg.view.children[0].children)
    assert "-# Explicit footer only" in contents


def test_send_request_review_actions_use_action_row_not_top_level_buttons():
    now = datetime.now(timezone.utc)
    request = SendRequestRecord(
        id=1,
        guild_id=1,
        sub_user_id=10,
        domme_user_id=20,
        amount_cents=1099,
        currency="USD",
        method="paypal",
        note="proof",
        status="pending",
        created_at=now,
        resolved_at=None,
    )

    msg = send_request_review_card(request, "Pat")
    add_send_request_review_actions(
        msg.view,
        bot=object(),
        request_id=request.id,
        guild_id=request.guild_id,
        domme_id=None,
    )

    assert type(msg.view.children[0]).__name__ == "Container"
    assert type(msg.view.children[1]).__name__ == "ActionRow"
    assert all(isinstance(child, discord.ui.Button) for child in msg.view.children[1].children)
    assert all(type(child).__name__ != "Button" for child in msg.view.children)
