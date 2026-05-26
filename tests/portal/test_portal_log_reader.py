from __future__ import annotations

import subprocess

import pytest

from rob_admin import log_reader


def test_log_reader_allows_allowlisted_service_and_redacts_secrets(monkeypatch):
    def _fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="DATABASE_URL=postgresql://secret\nDISCORD_TOKEN=abc\nok-line\n",
            stderr="",
        )

    monkeypatch.setattr(log_reader.subprocess, "run", _fake_run)
    result = log_reader.read_service_logs(
        "rob-bot-dev.service",
        lines=200,
        allowed_services=("rob-bot-dev.service",),
    )
    assert result.service == "rob-bot-dev.service"
    assert "***REDACTED***" in result.body
    assert "postgresql://secret" not in result.body
    assert "DISCORD_TOKEN=abc" not in result.body


def test_log_reader_rejects_non_allowlisted_service():
    with pytest.raises(ValueError):
        log_reader.read_service_logs(
            "postgresql.service",
            lines=200,
            allowed_services=("rob-bot-dev.service",),
        )


def test_log_reader_uses_shell_false(monkeypatch):
    observed = {"shell": None}

    def _fake_run(*_args, **kwargs):
        observed["shell"] = kwargs.get("shell")
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(log_reader.subprocess, "run", _fake_run)
    log_reader.read_service_logs(
        "rob-bot-dev.service",
        lines=200,
        allowed_services=("rob-bot-dev.service",),
    )
    assert observed["shell"] is False
