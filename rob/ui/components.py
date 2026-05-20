from __future__ import annotations

import discord

from rob.ui.theme import COLOR_INFO


def make_embed(
    *,
    title: str,
    description: str | None = None,
    color: discord.Colour | None = None,
    footer: str | None = None,
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        colour=color or COLOR_INFO,
    )
    if footer:
        embed.set_footer(text=footer)
    return embed


def add_field(embed: discord.Embed, *, name: str, value: str, inline: bool = True) -> discord.Embed:
    embed.add_field(name=name, value=value, inline=inline)
    return embed
