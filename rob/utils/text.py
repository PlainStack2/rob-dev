from __future__ import annotations

import hashlib


def collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def normalize_sender_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = collapse_whitespace(value.strip())
    return cleaned or None


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
