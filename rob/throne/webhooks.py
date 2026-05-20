from __future__ import annotations

import json
import logging
from typing import Any

from aiohttp import web

from rob.config.settings import Settings
from rob.database.connection import Database
from rob.database.repositories.throne_creators import ThroneCreatorsRepository
from rob.services.send_service import SendService
from rob.throne.payloads import parse_throne_send_payload
from rob.throne.security import secret_matches

log = logging.getLogger(__name__)


ACCEPTED_EVENT_TYPES = {
    "gift_purchased",
    "contribution_purchased",
    "gift_crowdfunded",
    "item_purchased",
}


async def handle_health(request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def handle_throne_webhook(request: web.Request) -> web.Response:
    database: Database = request.app["database"]
    settings: Settings = request.app["settings"]

    creator_id = request.match_info["creator_id"]
    provided_secret = request.match_info["secret"]

    raw_body = await request.read()

    try:
        payload: dict[str, Any] = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return web.json_response(
            {"ok": False, "error": "invalid_json"},
            status=400,
        )

    if settings.throne_webhook_debug_log_payload:
        log.info("Throne webhook payload for %s: %s", creator_id, payload)

    async with database.transaction() as connection:
        creators = ThroneCreatorsRepository(connection)
        matching_creators = await creators.get_by_creator_id(
            throne_creator_id=creator_id,
        )

        matched_creator = None

        for creator in matching_creators:
            if secret_matches(
                provided_secret=provided_secret,
                stored_secret=creator.webhook_secret,
                stored_secret_hash=creator.webhook_secret_hash,
            ):
                matched_creator = creator
                break

        if matched_creator is None:
            return web.json_response(
                {"ok": False, "error": "creator_not_found_or_secret_invalid"},
                status=403,
            )

        parsed = parse_throne_send_payload(
            creator_id=creator_id,
            payload=payload,
        )

        if parsed.event_type and parsed.event_type not in ACCEPTED_EVENT_TYPES:
            return web.json_response(
                {
                    "ok": True,
                    "ignored": True,
                    "event_type": parsed.event_type,
                }
            )

        send_service = SendService(connection)

        send_id = await send_service.record_throne_send(
            guild_id=matched_creator.guild_id,
            domme_id=matched_creator.domme_id,
            domme_user_id=matched_creator.discord_user_id,
            payload=parsed,
        )

        await creators.mark_webhook_success(
            creator_id=matched_creator.id,
            when=parsed.purchased_at,
        )

    if send_id is None:
        return web.json_response(
            {
                "ok": True,
                "duplicate": True,
            }
        )

    return web.json_response(
        {
            "ok": True,
            "inserted": True,
            "send_id": send_id,
        }
    )


def create_webhook_app(
    *,
    settings: Settings,
    database: Database,
) -> web.Application:
    app = web.Application()

    app["settings"] = settings
    app["database"] = database

    app.router.add_get("/health", handle_health)
    app.router.add_post(
        "/throne/webhook/{creator_id}/{secret}",
        handle_throne_webhook,
    )

    return app