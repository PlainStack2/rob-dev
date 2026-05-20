from __future__ import annotations

import discord

from rob.database.repositories.models import MaintenanceState, QueueStatus
from rob.ui.components import add_field, make_embed
from rob.ui.copy import STATUS_FOOTER
from rob.ui.theme import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING


def status_embed(
    *,
    bot_name: str,
    database_ok: bool,
    maintenance: MaintenanceState,
    queue: QueueStatus,
) -> discord.Embed:
    color = COLOR_WARNING if maintenance.enabled else COLOR_SUCCESS
    embed = make_embed(
        title=f"{bot_name} | Status",
        description="Shared PostgreSQL health and queue state.",
        color=color if database_ok else COLOR_PRIMARY,
        footer=STATUS_FOOTER,
    )
    add_field(embed, name="Database", value="Healthy" if database_ok else "Unavailable")
    add_field(embed, name="Maintenance", value="On" if maintenance.enabled else "Off")
    add_field(
        embed,
        name="Queue",
        value=(
            f"Pending: {queue.pending}\n"
            f"Queued: {queue.queued_maintenance}\n"
            f"Posted: {queue.posted}\n"
            f"Failed: {queue.failed}"
        ),
        inline=False,
    )
    if maintenance.reason:
        add_field(embed, name="Reason", value=maintenance.reason, inline=False)
    return embed
