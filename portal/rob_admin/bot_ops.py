from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class BotOpsResponse:
    ok: bool
    status_code: int
    payload: dict


class BotOpsClient:
    def __init__(self, *, host: str, port: int, secret: str | None) -> None:
        self.base_url = f"http://{host}:{port}"
        self.secret = secret or ""

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.secret:
            headers["X-Rob-Ops-Secret"] = self.secret
        return headers

    def _request(self, method: str, path: str, *, json_payload: dict | None = None) -> BotOpsResponse:
        with httpx.Client(timeout=8.0) as client:
            response = client.request(
                method=method,
                url=f"{self.base_url}{path}",
                headers=self._headers(),
                json=json_payload,
            )
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}
        return BotOpsResponse(ok=response.status_code < 400, status_code=response.status_code, payload=payload)

    def health(self) -> BotOpsResponse:
        return self._request("GET", "/health")

    def refresh_public_names(self, guild_id: int) -> BotOpsResponse:
        return self._request("POST", f"/guilds/{guild_id}/leaderboard/public/refresh-names")

    def refresh_leaderboard(self, guild_id: int) -> BotOpsResponse:
        return self._request("POST", f"/guilds/{guild_id}/leaderboard/refresh")

    def set_maintenance(self, *, enabled: bool, reason: str | None = None) -> BotOpsResponse:
        payload = {"enabled": enabled, "reason": reason or ""}
        return self._request("POST", "/maintenance", json_payload=payload)

