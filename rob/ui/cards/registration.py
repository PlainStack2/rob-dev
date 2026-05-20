from __future__ import annotations

import discord

from rob.ui.components import add_field, make_embed
from rob.ui.copy import SUCCESS_FOOTER
from rob.ui.theme import COLOR_SUCCESS


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
