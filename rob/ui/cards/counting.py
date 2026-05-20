from __future__ import annotations

import discord

from rob.ui.components import add_field, make_embed
from rob.ui.copy import COUNTING_FOOTER, SUCCESS_FOOTER
from rob.ui.theme import COLOR_INFO, COLOR_SUCCESS


def counting_status_embed(*, current_number: int, enabled: bool) -> discord.Embed:
    embed = make_embed(
        title="Rob | Counting",
        description="Current counting channel state.",
        color=COLOR_INFO,
        footer=COUNTING_FOOTER,
    )
    add_field(embed, name="Enabled", value="Yes" if enabled else "No")
    add_field(embed, name="Current Number", value=str(current_number))
    return embed


def counting_updated_embed(number: int) -> discord.Embed:
    return make_embed(
        title="Rob | Count Updated",
        description=f"Counting has been set to **{number}**.",
        color=COLOR_SUCCESS,
        footer=SUCCESS_FOOTER,
    )
