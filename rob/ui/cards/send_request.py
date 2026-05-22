from __future__ import annotations

from rob.database.repositories.models import SendRequestRecord
from rob.ui.components import make_card, render
from rob.ui.theme import COLOR_PRIMARY, COLOR_SUCCESS
from rob.utils.money import format_money_from_cents


def send_request_review_card(request: SendRequestRecord, sub_display: str):
    return render(
        make_card(
            title="Send request pending review",
            body=(
                f"**Sub:** {sub_display}\n\n"
                f"**Amount:** {format_money_from_cents(request.amount_cents)}\n\n"
                f"**Method:** {request.method}\n\n"
                f"**Note:** {request.note or 'No note provided.'}"
            ),
            color=COLOR_PRIMARY,
            variant="send",
        )
    )


def send_request_resolved_card(*, approved: bool):
    return render(
        make_card(
            title="Request approved" if approved else "Request ignored",
            body="Rob has handled the request.",
            color=COLOR_SUCCESS if approved else COLOR_PRIMARY,
            variant="status",
        )
    )
