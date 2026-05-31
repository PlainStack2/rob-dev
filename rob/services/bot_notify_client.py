from __future__ import annotations

import logging

from aiohttp import ClientError, ClientSession, ClientTimeout

log = logging.getLogger(__name__)


async def notify_bot_send(
    *,
    notify_url: str | None,
    secret: str | None,
    send_id: int,
    guild_id: int,
    timeout_seconds: float = 5.0,
) -> bool:
    if not notify_url:
        return False

    headers: dict[str, str] = {}
    if secret:
        headers["X-Rob-Ops-Secret"] = secret

    payload = {"send_id": int(send_id), "guild_id": int(guild_id)}
    timeout = ClientTimeout(total=timeout_seconds)
    try:
        async with ClientSession(timeout=timeout) as session:
            async with session.post(notify_url, json=payload, headers=headers) as response:
                if 200 <= response.status < 300:
                    return True
                body = await response.text()
                log.warning(
                    "Bot send notification failed status=%s send_id=%s guild_id=%s response=%s",
                    response.status,
                    send_id,
                    guild_id,
                    body[:200],
                )
                return False
    except (ClientError, TimeoutError):
        log.exception(
            "Bot send notification failed send_id=%s guild_id=%s.",
            send_id,
            guild_id,
        )
        return False


async def notify_bot_achievement(
    *,
    notify_url: str | None,
    secret: str | None,
    guild_id: int,
    discord_user_id: int,
    achievement_key: str,
    display_name: str | None = None,
    timeout_seconds: float = 5.0,
) -> bool:
    if not notify_url:
        return False

    base_url = notify_url
    if "/ops/sends/process" in base_url:
        base_url = base_url.replace("/ops/sends/process", "")
    elif "/sends/process" in base_url:
        base_url = base_url.replace("/sends/process", "")
    base_url = base_url.rstrip("/")

    headers: dict[str, str] = {}
    if secret:
        headers["X-Rob-Ops-Secret"] = secret

    payload = {
        "discord_user_id": int(discord_user_id),
        "achievement_key": str(achievement_key),
    }
    if display_name:
        payload["display_name"] = str(display_name)

    url = f"{base_url}/guilds/{int(guild_id)}/achievements/announce"
    timeout = ClientTimeout(total=timeout_seconds)
    try:
        async with ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if 200 <= response.status < 300:
                    return True
                body = await response.text()
                log.warning(
                    "Bot achievement notification failed status=%s guild_id=%s user_id=%s key=%s response=%s",
                    response.status,
                    guild_id,
                    discord_user_id,
                    achievement_key,
                    body[:200],
                )
                return False
    except (ClientError, TimeoutError):
        log.exception(
            "Bot achievement notification failed guild_id=%s user_id=%s key=%s.",
            guild_id,
            discord_user_id,
            achievement_key,
        )
        return False
