from __future__ import annotations

import discord

from rob.database.repositories.models import LeaderboardEntry, LeaderboardSummary
from rob.ui.components import add_field, make_embed
from rob.ui.copy import LEADERBOARD_FOOTER
from rob.ui.theme import COLOR_PRIMARY
from rob.utils.money import format_money_from_cents


def leaderboard_embed(
    *,
    title: str,
    entries: list[LeaderboardEntry],
    summary: LeaderboardSummary,
) -> discord.Embed:
    lines: list[str] = []
    for index, entry in enumerate(entries, start=1):
        lines.append(
            f"**{index}.** {entry.label}  |  {format_money_from_cents(entry.total_cents)}  |  {entry.send_count} sends"
        )
    if not lines:
        lines.append("No posted sends yet.")

    embed = make_embed(
        title=title,
        description="\n".join(lines),
        color=COLOR_PRIMARY,
        footer=LEADERBOARD_FOOTER,
    )
    add_field(embed, name="Total Posted", value=format_money_from_cents(summary.total_cents))
    add_field(embed, name="Send Count", value=str(summary.send_count))
    return embed
