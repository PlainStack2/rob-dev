from __future__ import annotations

import discord

from rob.ui.components import make_embed
from rob.ui.copy import ERROR_FOOTER
from rob.ui.theme import COLOR_DANGER


def error_embed(message: str, detail: str | None = None) -> discord.Embed:
    description = message if detail is None else f"{message}\n\n{detail}"
    return make_embed(
        title="Rob | Error",
        description=description,
        color=COLOR_DANGER,
        footer=ERROR_FOOTER,
    )
