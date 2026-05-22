from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime

from rob.database.repositories.models import SendRecord, SendRequestRecord
from rob.services.send_request_service import SendRequestService


class _FakeSendRequestsRepo:
    def __init__(self, record: SendRequestRecord):
        self.record = record
        self.resolved: list[str] = []
        self.count = 0

    async def count_since(self, **kwargs):
        return self.count

    async def get(self, request_id: int):
        if self.record.id != request_id:
            return None
        return self.record

    async def resolve(self, request_id: int, *, status: str):
        self.resolved.append(status)
        self.record = replace(self.record, status=status)


class _FakeSendService:
    async def record_manual_send(self, **kwargs):
        return SendRecord(1, kwargs['guild_id'], kwargs.get('domme_id'), kwargs['domme_user_id'], None, None, None, kwargs['amount_cents'], kwargs['currency'], kwargs['method'], 'manual', kwargs['note'], None, None, None, None, False, False, datetime.now(UTC), datetime.now(UTC), 'pending', None, None, None, datetime.now(UTC))


def _request() -> SendRequestRecord:
    now = datetime.now(UTC)
    return SendRequestRecord(11, 1, 2, 3, 1099, 'USD', 'paypal', 'proof', 'pending', now, None)


def test_sendrequest_rate_limit_works():
    repo = _FakeSendRequestsRepo(_request())
    svc = SendRequestService(send_requests=repo, send_service=_FakeSendService())
    repo.count = 3
    assert asyncio.run(svc.is_rate_limited(guild_id=1, sub_user_id=2, domme_user_id=3)) is True


def test_sendrequest_approve_inserts_send_and_resolves():
    repo = _FakeSendRequestsRepo(_request())
    svc = SendRequestService(send_requests=repo, send_service=_FakeSendService())
    out = asyncio.run(svc.approve(request_id=11, guild_id=1, domme_id=7))
    assert out.ok is True
    assert out.send is not None
    assert repo.resolved == ['approved']


def test_sendrequest_ignore_resolves():
    repo = _FakeSendRequestsRepo(_request())
    svc = SendRequestService(send_requests=repo, send_service=_FakeSendService())
    out = asyncio.run(svc.ignore(request_id=11))
    assert out.ok is True
    assert repo.resolved == ['ignored']
