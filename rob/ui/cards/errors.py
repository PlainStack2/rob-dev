from __future__ import annotations

from rob.ui.components import make_card, render
from rob.ui.theme import COLOR_DANGER


def error_card(message: str, detail: str | None = None):
    description = message if detail is None else f"{message}\n\n{detail}"
    return render(make_card(title="That.. didn't... work", body=description, color=COLOR_DANGER, variant="error", callout="What to try next: check inputs or try again."))
