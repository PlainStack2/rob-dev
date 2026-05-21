from __future__ import annotations

import discord

from rob.database.repositories.models import LeaderboardEntry, LeaderboardSummary
from rob.ui.components import add_field, make_embed
from rob.ui.theme import COLOR_PRIMARY
from rob.utils.money import format_money_from_cents


def leaderboard_embed(*, title: str, entries: list[LeaderboardEntry], summary: LeaderboardSummary, footer: str) -> discord.Embed:
    top_entries = entries[:10]
    if top_entries:
        lines = [f"#{index}. {entry.label} — {format_money_from_cents(entry.total_cents)}" for index, entry in enumerate(top_entries, start=1)]
        description = "\n".join(lines)
    else:
        description = "No sends tracked yet.\n\nRun /register domme to join the leaderboard."

    embed = make_embed(title=title, description=description, color=COLOR_PRIMARY, footer=footer)
    add_field(embed, name="Total Details", value=(f"Total Dollar Amount Sent: {format_money_from_cents(summary.total_cents)}\nTotal Dom/mes: {len(top_entries)}"), inline=False)
    return embed
