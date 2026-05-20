from __future__ import annotations

import asyncpg

from rob.database.repositories.sends import SendInsert, SendsRepository
from rob.services.maintenance_service import MaintenanceService
from rob.throne.payloads import ThroneSendPayload


class SendService:
    def __init__(self, connection: asyncpg.Connection) -> None:
        self.connection = connection
        self.sends = SendsRepository(connection)
        self.maintenance = MaintenanceService(connection)

    async def record_throne_send(
        self,
        *,
        guild_id: int,
        domme_id: int | None,
        domme_user_id: int,
        payload: ThroneSendPayload,
    ) -> int | None:
        maintenance_enabled = await self.maintenance.is_enabled()

        post_status = "queued_maintenance" if maintenance_enabled else "pending"

        return await self.sends.insert_send(
            SendInsert(
                guild_id=guild_id,
                domme_id=domme_id,
                domme_user_id=domme_user_id,
                sub_id=None,
                sub_user_id=None,
                sub_name=payload.gifter_username,
                amount_cents=payload.amount_cents,
                currency=payload.currency,
                method="throne",
                source="webhook",
                item_name=payload.item_name,
                item_image_url=payload.item_image_url,
                external_id=None,
                event_id=payload.event_id,
                fallback_event_hash=payload.fallback_event_hash,
                is_private=payload.is_private,
                seeded=False,
                sent_at=payload.purchased_at,
                discord_post_status=post_status,
            )
        )