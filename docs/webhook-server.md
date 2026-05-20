# Webhook Server

The webhook server is the HTTP-only side of Rob.

## Responsibilities

- Receives Throne webhook events.
- Validates the URL secret against `webhook_secret` and `webhook_secret_hash`.
- Optionally validates Throne Ed25519 signatures and timestamps.
- Normalises accepted Throne purchase payloads.
- Writes sends into PostgreSQL.
- Respects maintenance mode by inserting `queued_maintenance` instead of `pending`.
- Never connects to Discord.

## Runtime

- Entry point: `python -m apps.webhook.main`
- Host/port: `THRONE_WEBHOOK_HOST` / `THRONE_WEBHOOK_PORT`
- Health check: `GET /health`
- Webhook route: `POST /throne/webhook/{creator_id}/{secret}`

## Required environment

- `APP_ENV`
- `LOG_LEVEL`
- `DATABASE_URL`
- `THRONE_WEBHOOK_HOST`
- `THRONE_WEBHOOK_PORT`
- `THRONE_WEBHOOK_BASE_URL`
- `THRONE_WEBHOOK_REQUIRE_SIGNATURE`
- `THRONE_PUBLIC_KEY_PEM`
- `THRONE_WEBHOOK_DEBUG_LOG_PAYLOAD`
- `THRONE_WEBHOOK_TIMESTAMP_HEADER`
- `THRONE_WEBHOOK_SIGNATURE_HEADER`
- `THRONE_WEBHOOK_SIGNED_MESSAGE_FORMAT`
- `THRONE_WEBHOOK_MAX_TIMESTAMP_SKEW_SECONDS`

`DISCORD_TOKEN` is not required here.
