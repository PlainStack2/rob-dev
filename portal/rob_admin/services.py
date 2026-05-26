from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Any

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.utils import timezone

from .models import PortalAuditLog

log = logging.getLogger(__name__)

SENSITIVE_ENV_TOKENS = (
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "DATABASE_URL",
    "CLIENT_SECRET",
    "WEBHOOK",
)


def is_sensitive_key(key: str) -> bool:
    upper = key.upper()
    return any(token in upper for token in SENSITIVE_ENV_TOKENS)


def mask_value(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "***"
    return f"{value[:3]}***{value[-2:]}"


def redacted_env_pairs(values: dict[str, str]) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    for key in sorted(values):
        value = values[key]
        output.append((key, mask_value(value) if is_sensitive_key(key) else value))
    return output


@dataclass(frozen=True)
class ServiceStatus:
    name: str
    active_state: str
    sub_state: str
    start_timestamp: str
    fragment_path: str
    git_commit: str | None
    summary: str

    @property
    def health(self) -> str:
        if self.active_state == "active":
            return "Healthy"
        if self.active_state == "inactive":
            return "Warning"
        if self.active_state in {"failed", "deactivating"}:
            return "Error"
        return "Unknown"


def run_subprocess(command: list[str], *, timeout_seconds: int = 5) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
        timeout=timeout_seconds,
    )


def _parse_systemctl_show(output: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def get_service_status(service_name: str, *, allowed_services: tuple[str, ...]) -> ServiceStatus:
    if service_name not in allowed_services:
        raise ValueError(f"Service {service_name} is not allowlisted.")

    git_commit = os.getenv("GIT_COMMIT_SHA") or None
    try:
        active = run_subprocess(["systemctl", "is-active", service_name], timeout_seconds=3)
        show = run_subprocess(
            [
                "systemctl",
                "show",
                service_name,
                "--property=ActiveState,SubState,ExecMainStartTimestamp,FragmentPath",
            ],
            timeout_seconds=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        log.warning("Unable to read systemd state for %s: %s", service_name, exc)
        return ServiceStatus(
            name=service_name,
            active_state="unknown",
            sub_state="unknown",
            start_timestamp="",
            fragment_path="",
            git_commit=git_commit,
            summary="systemctl unavailable",
        )

    show_data = _parse_systemctl_show(show.stdout)
    active_state = show_data.get("ActiveState") or active.stdout.strip() or "unknown"
    sub_state = show_data.get("SubState", "unknown")
    start_timestamp = show_data.get("ExecMainStartTimestamp", "")
    fragment_path = show_data.get("FragmentPath", "")
    summary = (active.stderr or show.stderr).strip()

    return ServiceStatus(
        name=service_name,
        active_state=active_state,
        sub_state=sub_state,
        start_timestamp=start_timestamp,
        fragment_path=fragment_path,
        git_commit=git_commit,
        summary=summary,
    )


def _request_actor(request: HttpRequest) -> tuple[int, str]:
    discord_id = request.session.get("portal_discord_user_id")
    username = ""
    if not isinstance(request.user, AnonymousUser):
        username = request.user.get_username()
    if isinstance(discord_id, int):
        return discord_id, username
    if isinstance(discord_id, str) and discord_id.isdigit():
        return int(discord_id), username
    if username.startswith("discord_") and username.removeprefix("discord_").isdigit():
        return int(username.removeprefix("discord_")), username
    return 0, username


def audit_action(
    *,
    request: HttpRequest | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    payload = metadata or {}
    actor_discord_user_id = 0
    actor_username = ""
    if request is not None:
        actor_discord_user_id, actor_username = _request_actor(request)
    if actor_discord_user_id == 0:
        actor_discord_user_id = -1
    try:
        PortalAuditLog.objects.create(
            actor_discord_user_id=actor_discord_user_id,
            actor_username=actor_username,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata=payload,
            created_at=timezone.now(),
        )
    except Exception:  # pragma: no cover - table may not exist during early rollout
        log.exception("Failed to write portal audit log for action=%s", action)

