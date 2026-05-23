from __future__ import annotations

import discord

from rob.database.repositories.models import SendRecord
from rob.ui.render import RenderedMessage, require_components_v2
from rob.ui.theme import COLOR_SEND
from rob.utils.money import format_money_with_currency_name


def send_card(*, send: SendRecord, domme_label: str, sub_display: str, rank: int | None = None):
    del rank
    require_components_v2()
    view = discord.ui.LayoutView(timeout=1800)
    body = (
        f"**Sub:** {sub_display}\n\n"
        f"**Amount:** {format_money_with_currency_name(send.amount_cents, send.currency)}\n\n"
        f"**Item:** {send.item_name or 'Mystery send'}"
    )
    children: list[discord.ui.Item] = [
        discord.ui.TextDisplay(f"## 💸 New Send to {domme_label}! 💸"),
        discord.ui.Separator(),
    ]
    if send.item_image_url:
        children.append(
            discord.ui.Section(
                discord.ui.TextDisplay(body),
                accessory=discord.ui.Thumbnail(send.item_image_url),
            )
        )
    else:
        children.append(discord.ui.TextDisplay(body))
    view.add_item(discord.ui.Container(*children, accent_color=COLOR_SEND))
    return RenderedMessage(view=view)


def send_details_card(
    *,
    send: SendRecord,
    domme_label: str,
    sub_display: str,
    source_label: str,
    include_internal: bool = False,
) -> RenderedMessage:
    require_components_v2()
    view = discord.ui.LayoutView(timeout=1800)
    sent_unix = int(send.sent_at.timestamp())
    body = (
        f"**Recipient:** {domme_label}\n"
        f"**Sub:** {sub_display}\n"
        f"**Amount:** {format_money_with_currency_name(send.amount_cents, send.currency)}\n"
        f"**Item:** {send.item_name or 'Mystery send'}\n"
        f"**Source:** {source_label}\n"
        f"**Sent:** <t:{sent_unix}:R> / <t:{sent_unix}:f>\n"
        f"**Rob Send ID:** {send.public_send_id}"
    )
    children: list[discord.ui.Item] = [
        discord.ui.TextDisplay("## Send Details"),
        discord.ui.Separator(),
        discord.ui.TextDisplay(body),
    ]
    if include_internal:
        children.extend(
            [
                discord.ui.Separator(),
                discord.ui.TextDisplay(
                    f"**Database ID:** {send.id}\n"
                    f"**Event ID:** {send.event_id or 'Not available'}"
                ),
            ]
        )
    view.add_item(discord.ui.Container(*children, accent_color=COLOR_SEND))
    return RenderedMessage(view=view)


def send_details_list_card(
    *,
    title_label: str,
    sends: list[SendRecord],
    domme_lookup: dict[int, str],
) -> RenderedMessage:
    require_components_v2()
    view = discord.ui.LayoutView(timeout=1800)
    if not sends:
        body = "Rob checked the receipts drawer and found nothing public to show."
    else:
        lines = []
        for index, send in enumerate(sends, 1):
            sent_unix = int(send.sent_at.timestamp())
            lines.append(
                f"{index}. **{format_money_with_currency_name(send.amount_cents, send.currency)}** to **{domme_lookup.get(send.domme_user_id, f'<@{send.domme_user_id}>')}**\n"
                f"   Item: {send.item_name or 'Mystery send'}\n"
                f"   Sent: <t:{sent_unix}:R>"
            )
        body = "\n\n".join(lines)
    view.add_item(
        discord.ui.Container(
            discord.ui.TextDisplay(f"## Send Details for {title_label}"),
            discord.ui.Separator(),
            discord.ui.TextDisplay(body),
            accent_color=COLOR_SEND,
        )
    )
    return RenderedMessage(view=view)
