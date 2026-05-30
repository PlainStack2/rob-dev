from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

from rob.database.repositories.models import Domme, SendChangeRequest
from rob.services.send_change_request_service import SendChangeRequestService


def _now() -> datetime:
    return datetime.now(timezone.utc)


class _FakeRequestsRepo:
    def __init__(self, request: SendChangeRequest):
        self.request = request
        self.delivery_calls: list[tuple[int, int, int]] = []
        self.failed_calls: list[dict] = []

    async def set_delivery(
        self,
        *,
        request_id: int,
        request_channel_id: int,
        request_message_id: int,
    ) -> SendChangeRequest:
        self.delivery_calls.append((request_id, request_channel_id, request_message_id))
        self.request = SendChangeRequest(
            **{
                **self.request.__dict__,
                "request_channel_id": request_channel_id,
                "request_message_id": request_message_id,
            }
        )
        return self.request

    async def mark_failed(self, **kwargs) -> None:
        self.failed_calls.append(kwargs)


class _FakeUser:
    def __init__(self):
        self.messages: list[dict] = []

    async def send(self, **kwargs):
        self.messages.append(kwargs)
        return SimpleNamespace(channel=SimpleNamespace(id=321), id=654)


class _FakeBot:
    def __init__(self, user):
        self._user = user
        self.bound_views: list[tuple[object, int]] = []

    def get_user(self, _discord_user_id: int):
        return self._user

    async def fetch_user(self, _discord_user_id: int):
        return self._user

    def add_view(self, view, *, message_id: int):
        self.bound_views.append((view, message_id))


def test_deliver_request_renders_send_change_card_with_action_buttons():
    now = _now()
    request = SendChangeRequest(
        id=11,
        guild_id=99,
        domme_user_id=555,
        action="send_add",
        status="pending",
        requested_by="rob@test",
        requested_sub_name="pat",
        amount_cents=2550,
        currency="USD",
        method="manual",
        note=None,
        target_send_id=None,
        decision_reason=None,
        request_channel_id=None,
        request_message_id=None,
        approved_by_user_id=None,
        approved_send_id=None,
        created_at=now,
        updated_at=now,
        decided_at=None,
    )
    domme = Domme(
        id=1,
        bot_user_id=2,
        guild_id=99,
        discord_user_id=555,
        throne_url=None,
        throne_handle="missadore",
        throne_creator_id=None,
        tracking_status="active",
        profile_status="active",
        hide_own_purchases=None,
        webhook_secret=None,
        webhook_secret_hash=None,
        webhook_connected_at=None,
        overlay_detected=False,
        last_overlay_check_at=None,
        last_successful_event_at=None,
        public_display_name="Miss Adore",
        public_display_name_updated_at=None,
        registered_at=now,
        created_at=now,
        updated_at=now,
    )
    requests_repo = _FakeRequestsRepo(request)
    user = _FakeUser()
    bot = _FakeBot(user)
    service = SendChangeRequestService(
        bot=bot,  # type: ignore[arg-type]
        requests=requests_repo,
        dommes=SimpleNamespace(),
        sends=SimpleNamespace(),
        send_service=SimpleNamespace(),
        send_queue_service=None,
        leaderboard_service=None,
    )

    delivered = asyncio.run(service._deliver_request(request, domme=domme, target_send=None))

    assert delivered.request_channel_id == 321
    assert delivered.request_message_id == 654
    assert requests_repo.delivery_calls == [(11, 321, 654)]
    assert len(user.messages) == 1
    sent_payload = user.messages[0]
    assert sent_payload["view"] is not None
    assert len(sent_payload["view"].children) >= 2
    assert bot.bound_views
