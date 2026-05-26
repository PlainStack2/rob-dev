# Rob Web Portal (Django Superadmin)

## Overview

Rob now includes a separate Django-based superadmin portal under `portal/`.

- Framework: Django + Django Admin
- Auth: Discord OAuth (`identify`, `guilds`)
- Data store: PostgreSQL (existing Rob tables mapped as unmanaged models)
- Access: superadmin allowlist only (`ROB_PORTAL_SUPERADMIN_USER_IDS`)

This portal is intentionally separate from the Discord bot and webhook services.

## Why Django Admin

Django Admin provides a secure, mature baseline for:

- authenticated admin sessions
- model browsing and filtering
- safe CRUD controls
- admin actions for constrained workflows

This avoids rebuilding every internal page by hand while still allowing custom Rob pages for operations.

## URL Layout

All portal routes are prefixed with `/portal/`:

- `/portal/`
- `/portal/login/`
- `/portal/logout/`
- `/portal/auth/discord/`
- `/portal/auth/discord/callback/`
- `/portal/admin/`
- `/portal/dashboard/`
- `/portal/services/`
- `/portal/logs/`
- `/portal/database/`
- `/portal/leaderboards/`
- `/portal/sends/`
- `/portal/settings/`

## Environment Variables

Add these to `.env` for portal runtime:

```dotenv
ROB_PORTAL_ENABLED=false
ROB_PORTAL_ENV=dev
ROB_PORTAL_BASE_URL=https://rob-dev.barecoding.com
ROB_PORTAL_SECRET_KEY=
ROB_PORTAL_ALLOWED_HOSTS=rob-dev.barecoding.com,127.0.0.1,localhost
ROB_PORTAL_CSRF_TRUSTED_ORIGINS=https://rob-dev.barecoding.com
ROB_PORTAL_SUPERADMIN_USER_IDS=1299308718009356289

DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
DISCORD_REDIRECT_URI=https://rob-dev.barecoding.com/portal/auth/discord/callback

PORTAL_DATABASE_URL=postgresql://rob_dev_portal:<password>@<host>:<port>/rob_dev?sslmode=require
PORTAL_MIGRATION_DATABASE_URL=postgresql://rob_dev_migrator:<password>@<host>:<port>/rob_dev?sslmode=require

ROB_OPS_HOST=127.0.0.1
ROB_OPS_PORT=8811
ROB_OPS_SECRET=
ROB_PORTAL_ALLOWED_SERVICES=rob-bot-dev.service,rob-webhook-dev.service,rob-portal-dev.service
ROB_PORTAL_ENABLE_SERVICE_ACTIONS=false
```

## Authentication Model

1. User visits `/portal/login/`.
2. Portal redirects to Discord OAuth.
3. Callback validates OAuth state and exchanges `code` for identity.
4. Portal checks Discord ID against `ROB_PORTAL_SUPERADMIN_USER_IDS`.
5. Allowed users get a Django staff account (`is_staff=True`).
6. First configured superadmin ID is elevated to `is_superuser=True`.
7. User is signed in and redirected to `/portal/admin/`.

Non-allowlisted users are denied.

## Database Mapping

Portal models map to existing Rob tables with `managed = False`:

- `guild_settings`
- `dommes`
- `subs`
- `sends`
- `send_requests`
- `throne_creators`
- `public_leaderboards`
- `leaderboard_message`
- `bot_state`
- `counting_state`
- `blacklist`
- `schema_migrations`
- `portal_audit_log`

Legacy tables are surfaced as warnings in `/portal/database/`:

- `leaderboard_messages`
- `throne_wishlist_items`

## Safe Actions (Phase 1)

Available in `/portal/leaderboards/` (POST + CSRF + superadmin required):

- refresh cached Discord names (via bot-ops bridge)
- request leaderboard refresh
- toggle maintenance mode
- create public leaderboard URL
- enable/disable/rotate public leaderboard token

All actions are audit logged into `portal_audit_log`.

## Log Viewing Safety

`/portal/logs/` is restricted to allowlisted services only.

- no arbitrary service input
- no shell command execution
- uses `subprocess.run(..., shell=False, timeout=...)`
- sensitive values are redacted before rendering

## Bot Ops Bridge Connectivity

Portal action endpoints call the private bot ops bridge:

- `GET /health`
- `POST /guilds/{guild_id}/leaderboard/public/refresh-names`
- `POST /guilds/{guild_id}/leaderboard/refresh`
- `POST /maintenance`

If `ROB_OPS_SECRET` is set, requests include `X-Rob-Ops-Secret`.

## Local Run

```bash
cd portal
python -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
DJANGO_SETTINGS_MODULE=rob_portal.settings .venv/bin/python manage.py runserver 127.0.0.1:8090
```

## Systemd Example

Use `deploy/systemd/rob-portal-dev.service` as the baseline unit.

## Nginx Example

```nginx
location /portal/ {
    proxy_pass http://127.0.0.1:8090/portal/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Keep `/public/leaderboard/` and `/throne/webhook/` routed to the existing webhook service.

## Not Included Yet

Deliberately not shipped in this phase:

- deploy/update buttons
- arbitrary service restart buttons
- public exposure of bot-ops bridge
- raw `.env` rendering

## Troubleshooting

- If portal always returns 404: set `ROB_PORTAL_ENABLED=true`.
- If Discord login fails: verify OAuth client ID/secret/redirect URI and trusted origins.
- If actions fail with 403 from bot-ops: verify `ROB_OPS_SECRET` matches bot service env.
- If admin pages fail with table errors: run Rob SQL migrations (including `010_portal_audit_log`).
