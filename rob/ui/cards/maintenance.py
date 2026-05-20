from __future__ import annotations

import discord

from rob.ui.components import add_field, make_embed
from rob.ui.copy import MAINTENANCE_FOOTER
from rob.ui.theme import COLOR_WARNING


def maintenance_embed(reason: str | None) -> discord.Embed:
    embed = make_embed(
        title="Rob | Maintenance Mode",
        description="New sends are being saved, but Discord posting is paused.",
        color=COLOR_WARNING,
        footer=MAINTENANCE_FOOTER,
    )
    add_field(embed, name="Reason", value=reason or "No reason provided.", inline=False)
    return embed
