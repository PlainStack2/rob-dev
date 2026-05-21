from __future__ import annotations

import discord

from rob.ui.components import add_field, make_embed
from rob.ui.copy import SUCCESS_FOOTER
from rob.ui.theme import COLOR_PRIMARY, COLOR_SUCCESS


def registration_embed(
    *,
    title: str,
    summary: str,
    details: list[tuple[str, str]] | None = None,
) -> discord.Embed:
    embed = make_embed(
        title=title,
        description=summary,
        color=COLOR_SUCCESS,
        footer=SUCCESS_FOOTER,
    )
    for name, value in details or []:
        add_field(embed, name=name, value=value, inline=False)
    return embed


def domme_registered_embed() -> discord.Embed:
    return make_embed(
        title="You're registered!",
        description=(
            "Thanks for entrusting Rob with tracking your Throne sends!\n\n"
            "Before we can fully start, there’s just one more thing I need you to do. "
            "In order for Rob to correctly receive your Throne sends, you’ll need to pop a special URL into Throne.\n\n"
            "Because that link is secret, I’ve sent you a DM to help get it sorted."
        ),
        color=COLOR_SUCCESS,
        footer=SUCCESS_FOOTER,
    )


def throne_setup_embed(description: str) -> discord.Embed:
    return make_embed(title="Throne Tracking Setup!", description=description, color=COLOR_PRIMARY)
