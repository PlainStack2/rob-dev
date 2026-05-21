from __future__ import annotations

from dataclasses import dataclass, field

import discord


@dataclass(frozen=True)
class CardSection:
    title: str
    text: str
    inline: bool = False


@dataclass(frozen=True)
class CardAction:
    label: str
    style: discord.ButtonStyle = discord.ButtonStyle.secondary
    custom_id: str | None = None
    url: str | None = None
    row: int | None = None


@dataclass(frozen=True)
class RobCard:
    title: str
    body: str
    sections: list[CardSection] = field(default_factory=list)
    footer: str | None = None
    image_url: str | None = None
    actions: list[CardAction] = field(default_factory=list)
    color: discord.Colour | None = None


@dataclass(frozen=True)
class RenderedMessage:
    embed: discord.Embed
    view: discord.ui.View | None
    mode: str


def _supports_components_v2() -> bool:
    # TODO: Switch to true Discord Components V2 payload rendering once discord.py exposes stable APIs.
    return False


def render_card(card: RobCard, *, view: discord.ui.View | None = None) -> RenderedMessage:
    embed = discord.Embed(title=card.title, description=card.body, colour=card.color)
    for section in card.sections:
        embed.add_field(name=section.title, value=section.text, inline=section.inline)
    if card.footer:
        embed.set_footer(text=card.footer)
    if card.image_url:
        embed.set_image(url=card.image_url)

    mode = "components_v2" if _supports_components_v2() else "embed_fallback"
    return RenderedMessage(embed=embed, view=view, mode=mode)
