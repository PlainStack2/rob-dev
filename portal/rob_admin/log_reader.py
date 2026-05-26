from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass


MAX_LOG_LINES = 500

_REDACTION_PATTERNS = (
    re.compile(r"(DATABASE_URL\s*=\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(POSTGRES(?:QL)?[A-Z0-9_]*\s*=\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(DISCORD_TOKEN\s*=\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(THRONE_PUBLIC_KEY(?:_PEM)?\s*=\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(THRONE_WEBHOOK[A-Z0-9_]*\s*=\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(ROB_OPS_SECRET\s*=\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(CLIENT_SECRET\s*=\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(WEBHOOK_SECRET\s*=\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(password\s*=\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(secret\s*=\s*)(\S+)", re.IGNORECASE),
    re.compile(r"(token\s*=\s*)(\S+)", re.IGNORECASE),
)


@dataclass(frozen=True)
class ServiceLogs:
    service: str
    lines: int
    body: str
    error: str | None = None


def redact_secrets(value: str) -> str:
    output = value
    for pattern in _REDACTION_PATTERNS:
        output = pattern.sub(r"\1***REDACTED***", output)
    return output


def read_service_logs(
    service_name: str,
    *,
    lines: int = 200,
    allowed_services: tuple[str, ...],
) -> ServiceLogs:
    if service_name not in allowed_services:
        raise ValueError(f"Service {service_name} is not allowlisted.")

    clamped_lines = max(1, min(lines, MAX_LOG_LINES))
    try:
        result = subprocess.run(
            ["journalctl", "-u", service_name, "-n", str(clamped_lines), "--no-pager"],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=8,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return ServiceLogs(
            service=service_name,
            lines=clamped_lines,
            body="",
            error=str(exc),
        )

    body = redact_secrets(result.stdout)
    error = redact_secrets(result.stderr.strip()) if result.stderr.strip() else None
    return ServiceLogs(
        service=service_name,
        lines=clamped_lines,
        body=body,
        error=error,
    )

