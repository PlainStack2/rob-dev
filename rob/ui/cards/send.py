from __future__ import annotations

import discord

from rob.database.repositories.models import SendRecord
from rob.ui.components import add_field, make_embed
from rob.ui.theme import COLOR_INFO
from rob.utils.money import format_money_from_cents
from rob.utils.time import format_timestamp


def send_embed(
    *,
    send: SendRecord,
    domme_label: str,
    sub_label: str | None,
) -> discord.Embed:
    amount_text = (
        "Private / hidden"
        if send.is_private and send.amount_cents == 0
        else format_money_from_cents(send.amount_cents, send.currency)
    )
    embed = make_embed(
        title="Rob | New Send",
        description=send.item_name or "A new send was logged.",
        color=COLOR_INFO,
        footer="Posted from the shared send queue.",
    )
    add_field(embed, name="Domme", value=domme_label)
    add_field(embed, name="Sender", value=sub_label or "Unclaimed")
    add_field(embed, name="Amount", value=amount_text)
    add_field(embed, name="Method", value=send.method or send.source)
    add_field(embed, name="Sent At", value=format_timestamp(send.sent_at), inline=False)
    if send.item_image_url:
        embed.set_thumbnail(url=send.item_image_url)
    return embed
