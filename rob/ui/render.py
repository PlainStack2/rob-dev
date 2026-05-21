from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

import discord

log = logging.getLogger(__name__)


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
    content: str | None = None
    embed: discord.Embed | None = None
    embeds: list[discord.Embed] | None = None
    view: discord.ui.View | discord.ui.LayoutView | None = None
    mode: Literal["components_v2", "embed_fallback"] = "embed_fallback"

    def with_view(self, view: discord.ui.View | discord.ui.LayoutView | None) -> "RenderedMessage":
        return RenderedMessage(
            content=self.content,
            embed=self.embed,
            embeds=self.embeds,
            view=view,
            mode=self.mode,
        )

    def send_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"content": self.content, "view": self.view}
        if self.embed is not None:
            kwargs["embed"] = self.embed
        if self.embeds is not None:
            kwargs["embeds"] = self.embeds
        return kwargs

    def edit_kwargs(self) -> dict[str, Any]:
        kwargs = self.send_kwargs()
        if self.mode == "components_v2":
            kwargs["content"] = None
            kwargs["embed"] = None
            kwargs["embeds"] = None
            kwargs["attachments"] = None
        return kwargs


def supports_components_v2() -> bool:
    required = ["LayoutView", "Container", "Section", "TextDisplay", "Separator", "MediaGallery", "Thumbnail"]
    ok = all(hasattr(discord.ui, name) for name in required)
    if not ok:
        log.info("Discord Components V2 unavailable; using embed fallback renderer.")
    return ok


def _render_v2(card: RobCard, *, view: discord.ui.View | discord.ui.LayoutView | None) -> RenderedMessage:
    # Keep interactive button views stable. If a classic View is supplied,
    # use embed fallback instead of attempting to transplant children into a
    # LayoutView container.
    if view is not None and not isinstance(view, discord.ui.LayoutView):
        return _render_embed(card, view=view)

    layout = view if isinstance(view, discord.ui.LayoutView) else discord.ui.LayoutView(timeout=1800)
    items: list[Any] = [discord.ui.TextDisplay(f"# {card.title}"), discord.ui.TextDisplay(card.body)]
    items.append(discord.ui.Separator())
    for section in card.sections:
        items.append(discord.ui.TextDisplay(f"**{section.title}**\n{section.text}"))
    if card.image_url:
        items.append(discord.ui.Separator())
        try:
            items.append(discord.ui.MediaGallery(discord.MediaGalleryItem(media=card.image_url)))
        except Exception:
            items.append(discord.ui.TextDisplay(f"[Media]({card.image_url})"))
    if card.footer:
        items.append(discord.ui.Separator())
        items.append(discord.ui.TextDisplay(f"-# {card.footer}"))
    container = discord.ui.Container(*items, accent_color=card.color)
    if isinstance(layout, discord.ui.LayoutView):
        layout.add_item(container)
    return RenderedMessage(view=layout, mode="components_v2")


def _render_embed(card: RobCard, *, view: discord.ui.View | discord.ui.LayoutView | None) -> RenderedMessage:
    embed = discord.Embed(title=card.title, description=card.body, colour=card.color)
    for section in card.sections:
        embed.add_field(name=section.title, value=section.text, inline=section.inline)
    if card.footer:
        embed.set_footer(text=card.footer)
    if card.image_url:
        embed.set_image(url=card.image_url)
    return RenderedMessage(embed=embed, view=view, mode="embed_fallback")


def render_card(card: RobCard, *, view: discord.ui.View | discord.ui.LayoutView | None = None) -> RenderedMessage:
    if supports_components_v2():
        return _render_v2(card, view=view)
    return _render_embed(card, view=view)
