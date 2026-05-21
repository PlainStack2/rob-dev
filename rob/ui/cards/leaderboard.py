from __future__ import annotations

import discord

from rob.database.repositories.models import LeaderboardEntry, LeaderboardSummary
from rob.ui.components import make_card, render
from rob.ui.render import CardSection, RenderedMessage
from rob.ui.theme import COLOR_PRIMARY
from rob.utils.money import format_money_from_cents


def leaderboard_card(*, title: str, entries: list[LeaderboardEntry], summary: LeaderboardSummary, footer: str) -> RenderedMessage:
    top_entries = entries[:10]
    description = "\n".join([f"#{i}. {e.label} — {format_money_from_cents(e.total_cents)}" for i, e in enumerate(top_entries, 1)]) if top_entries else "No sends tracked yet.\n\nRun /register domme to join the leaderboard."
    return render(
        make_card(
            title=title,
            body=description,
            color=COLOR_PRIMARY,
            footer=footer,
            sections=[CardSection(title="Total Details", text=f"Total Dollar Amount Sent: {format_money_from_cents(summary.total_cents)}\nTotal Dom/mes: {len(top_entries)}")],
        )
    )


def leaderboard_embed(*, title: str, entries: list[LeaderboardEntry], summary: LeaderboardSummary, footer: str) -> discord.Embed:
    return leaderboard_card(title=title, entries=entries, summary=summary, footer=footer).embed  # type: ignore[return-value]
