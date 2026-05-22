from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from rob.database.repositories.models import SendRecord
from rob.database.repositories.send_requests import SendRequestsRepository
from rob.services.send_service import SendService


@dataclass(frozen=True)
class SendRequestDecision:
    ok: bool
    status: str
    send: SendRecord | None = None


class SendRequestService:
    RATE_LIMIT = 3

    def __init__(self, *, send_requests: SendRequestsRepository, send_service: SendService) -> None:
        self.send_requests = send_requests
        self.send_service = send_service

    async def is_rate_limited(self, *, guild_id: int, sub_user_id: int, domme_user_id: int) -> bool:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        count = await self.send_requests.count_since(
            guild_id=guild_id,
            sub_user_id=sub_user_id,
            domme_user_id=domme_user_id,
            since=since,
        )
        return count >= self.RATE_LIMIT

    async def approve(self, *, request_id: int, guild_id: int, domme_id: int | None) -> SendRequestDecision:
        request = await self.send_requests.get(request_id)
        if request is None:
            return SendRequestDecision(ok=False, status="missing")
        if request.status != "pending":
            return SendRequestDecision(ok=False, status=request.status)

        send = await self.send_service.record_manual_send(
            guild_id=guild_id,
            domme_id=domme_id,
            domme_user_id=request.domme_user_id,
            sub_name=None,
            amount_cents=request.amount_cents,
            currency=request.currency,
            method=request.method,
            note=request.note,
        )
        await self.send_requests.resolve(request.id, status="approved")
        return SendRequestDecision(ok=True, status="approved", send=send)

    async def ignore(self, *, request_id: int) -> SendRequestDecision:
        request = await self.send_requests.get(request_id)
        if request is None:
            return SendRequestDecision(ok=False, status="missing")
        if request.status != "pending":
            return SendRequestDecision(ok=False, status=request.status)
        await self.send_requests.resolve(request.id, status="ignored")
        return SendRequestDecision(ok=True, status="ignored")
