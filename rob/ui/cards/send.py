from __future__ import annotations

from rob.database.repositories.models import SendRecord
from rob.ui.components import make_card, render
from rob.ui.theme import COLOR_INFO
from rob.utils.money import format_money_with_currency_name


def send_card(*, send: SendRecord, domme_label: str, sub_label: str | None, rank: int | None = None):
    sub_display = "The Flying Dutchman" if not sub_label else (f"{sub_label} with no nickname claimed" if sub_label and sub_label.startswith("@") is False and "<@" not in sub_label and "nickname claimed" not in sub_label else sub_label)
    rank_line = f"{domme_label}'s rank after this send: #{rank}" if rank else "Rob is still doing the rank maths."
    return render(make_card(
        title=f"💸 {domme_label} just got a new send! 💸",
        body=(
            f"**Item:** {send.item_name or 'Mystery send'}\n\n"
            f"**Amount:** {format_money_with_currency_name(send.amount_cents, send.currency)}\n\n"
            f"**Sub:** {sub_display}\n\n"
            f"{rank_line}"
        ),
        color=COLOR_INFO,
        variant="send",
        sections=[],
        image_url=send.item_image_url,
    ))
