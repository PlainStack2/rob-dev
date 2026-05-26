from __future__ import annotations

import json
import logging
from datetime import datetime, UTC
from html import escape
from typing import Any

from aiohttp import web

from rob.config.settings import WebhookSettings
from rob.database.connection import Database
from rob.database.repositories.bot_state import BotStateRepository
from rob.database.repositories.leaderboards import LeaderboardsRepository
from rob.database.repositories.public_leaderboards import PublicLeaderboardsRepository
from rob.database.repositories.sends import SendsRepository
from rob.database.repositories.throne_creators import ThroneCreatorsRepository
from rob.services.maintenance_service import MaintenanceService
from rob.services.send_service import SendService
from rob.services.throne_service import ThroneService
from rob.throne.payloads import is_explicit_test_webhook_payload, is_known_test_sender, is_supported_event_type, parse_throne_send_payload
from rob.throne.security import (
    build_signed_message,
    secret_matches,
    validate_timestamp_header,
    verify_ed25519_signature,
)

log = logging.getLogger(__name__)


def _public_leaderboard_html(*, title: str, entries: list[dict[str, str]], updated: str) -> str:
    rows = "\n".join(
        f'<section class="entry"><div class="rank">#{i}</div><div class="name">{escape(e["name"])}</div><div class="meta">{escape(e["amount"])} sent</div><div class="meta">{escape(e["count"])}</div></section>'
        for i, e in enumerate(entries, 1)
    )
    return f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>{escape(title)}</title><style>html,body{{margin:0;padding:0;background:#000;color:#b00000;font-family:\"Times New Roman\",Times,serif;}}.leaderboard{{width:100%;box-sizing:border-box;padding:24px;background:#000;color:#b00000;}}h1{{margin:0 0 18px;font-size:32px;font-weight:bold;color:#cc0000;}}.entry{{border-top:1px solid #5a0000;padding:12px 0;}}.rank{{font-size:22px;font-weight:bold;}}.name{{font-size:22px;font-weight:bold;}}.meta{{font-size:16px;margin-top:4px;}}.updated{{border-top:1px solid #5a0000;margin-top:18px;padding-top:10px;font-size:13px;}}</style></head><body><main class=\"leaderboard\"><h1>{escape(title)}</h1>{rows}<div class=\"updated\">Last updated: {escape(updated)} UTC</div></main></body></html>"""


async def handle_public_leaderboard(request: web.Request) -> web.Response:
    token = request.match_info["public_token"]
    database: Database = request.app["database"]
    settings: WebhookSettings = request.app["settings"]
    public_repo = PublicLeaderboardsRepository(database)
    row = await public_repo.get_by_token(token)
    if row is None or not row.enabled:
        return web.Response(status=404, text="Not found", content_type="text/plain")
    leaderboards = LeaderboardsRepository(database)
    top = await leaderboards.get_top_dommes_public(
        row.guild_id,
        limit=settings.leaderboard_limit,
        include_test_sends=settings.throne_parse_test_sends_as_real_sends,
        test_gifter_usernames=settings.throne_test_gifter_usernames,
        owner_test_user_id=settings.throne_test_send_leaderboard_owner_user_id,
    )
    entries = [
        {"name": item.label or "Registered Dom/me", "amount": f"${(item.total_cents / 100):,.2f}", "count": f"{item.send_count} sends"}
        for item in top
    ]
    html = _public_leaderboard_html(title=row.title, entries=entries, updated=datetime.now(UTC).strftime("%Y-%m-%d %H:%M"))
    response = web.Response(text=html, content_type="text/html")
    response.headers["Cache-Control"] = "public, max-age=60"
    return response


async def handle_health(request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def handle_throne_webhook(request: web.Request) -> web.Response:
    database: Database = request.app["database"]
    settings: WebhookSettings = request.app["settings"]
    throne: ThroneService = request.app["throne_service"]

    creator_id = request.match_info["creator_id"]
    provided_secret = request.match_info["secret"]

    raw_body = await request.read()

    timestamp_header = request.headers.get(settings.throne_webhook_timestamp_header)
    signature_header = request.headers.get(settings.throne_webhook_signature_header, "").strip()

    if settings.throne_webhook_require_signature:
        if not validate_timestamp_header(
            timestamp_header,
            max_skew_seconds=settings.throne_webhook_max_timestamp_skew_seconds,
        ):
            return web.json_response({"ok": False, "error": "invalid_timestamp"}, status=401)
        if not settings.throne_public_key_pem:
            return web.json_response({"ok": False, "error": "signature_not_configured"}, status=401)
        message = build_signed_message(
            timestamp=timestamp_header or "",
            raw_body=raw_body,
            signed_message_format=settings.throne_webhook_signed_message_format,
        )
        if not verify_ed25519_signature(
            public_key_pem=settings.throne_public_key_pem,
            signature_hex=signature_header,
            message=message,
        ):
            return web.json_response({"ok": False, "error": "invalid_signature"}, status=401)

    try:
        payload: dict[str, Any] = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return web.json_response({"ok": False, "error": "invalid_json"}, status=400)

    if settings.throne_webhook_debug_log_payload:
        log.info("Throne webhook payload for %s: %s", creator_id, payload)

    creators = ThroneCreatorsRepository(database)
    matching_creators = await creators.get_by_creator_id(creator_id)

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

    parsed = parse_throne_send_payload(creator_id=creator_id, payload=payload)
    explicit_test = is_explicit_test_webhook_payload(payload, parsed)
    known_test_sender = is_known_test_sender(parsed.gifter_username, test_gifter_usernames=set(settings.throne_test_gifter_usernames))
    if explicit_test:
        await creators.mark_setup_verified(matched_creator.id)
        return web.json_response({"ok": True, "setup_verified": True})
    if known_test_sender and not settings.throne_parse_test_sends_as_real_sends:
        await creators.mark_setup_verified(matched_creator.id)
    if known_test_sender and settings.throne_parse_test_sends_as_real_sends:
        log.warning("Known Throne test sender accepted as real send due to THRONE_PARSE_TEST_SENDS_AS_REAL_SENDS=true. creator_id=%s gifter_username=%s", creator_id, parsed.gifter_username)

    if not is_supported_event_type(parsed.event_type):
        await creators.touch_successful_event(matched_creator.id)
        return web.json_response(
            {
                "ok": True,
                "ignored": True,
                "event_type": parsed.event_type,
            }
        )

    maintenance = MaintenanceService(BotStateRepository(database))
    send_service = SendService(
        sends=SendsRepository(database),
        subs=request.app["subs_repository"],
        maintenance=maintenance,
        throne=throne,
        throne_test_gifter_usernames=settings.throne_test_gifter_usernames,
    )
    send = await send_service.record_throne_send(
        creator=matched_creator,
        payload=parsed,
    )
    await creators.touch_successful_event(matched_creator.id)

    if send is None:
        return web.json_response({"ok": True, "duplicate": True})

    response: dict[str, Any] = {"ok": True, "inserted": True, "send_id": send.id}
    if known_test_sender and not settings.throne_parse_test_sends_as_real_sends:
        response["setup_verified"] = True
    return web.json_response(response)


def create_webhook_app(
    *,
    settings: WebhookSettings,
    database: Database,
) -> web.Application:
    from rob.database.repositories.subs import SubsRepository

    app = web.Application()
    app["settings"] = settings
    app["database"] = database
    app["throne_service"] = ThroneService()
    app["subs_repository"] = SubsRepository(database)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/public/leaderboard/{public_token}", handle_public_leaderboard)
    app.router.add_post("/throne/webhook/{creator_id}/{secret}", handle_throne_webhook)

    async def close_throne_service(_app: web.Application) -> None:
        await _app["throne_service"].close()

    app.on_cleanup.append(close_throne_service)
    return app
