from __future__ import annotations

import hashlib
import hmac


def hash_webhook_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()

def secret_matches(
        *,
        provided_secret: str,
        stored_secret: str | None,
        stored_secret_hash: str | None,
) -> bool:
    provided_hash = hash_webhook_secret(provided_secret)

    if stored_secret_hash and hmac.compare_digest(provided_hash, stored_secret_hash):
        return True
    
    if stored_secret and hmac.compare_digest(provided_secret, stored_secret):
        return True
    
    return False