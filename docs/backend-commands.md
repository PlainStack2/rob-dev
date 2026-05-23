# Backend Commands

Use [`scripts/robctl`](../scripts/robctl) from the server checkout, or install a shell alias that points to it.

## Supported commands

```bash
scripts/robctl status
scripts/robctl logs bot
scripts/robctl logs webhook
scripts/robctl restart bot
scripts/robctl restart webhook
scripts/robctl restart all

scripts/robctl maintenance status
scripts/robctl maintenance on "Deploying schema changes"
scripts/robctl maintenance off

scripts/robctl queue status
scripts/robctl queue flush

scripts/robctl leaderboard refresh
scripts/robctl throne invalidate-test-sends
scripts/robctl sends backfill-public-ids

scripts/robctl count status
scripts/robctl count set 123
```

## Notes

- `maintenance on/off`, `queue status`, `queue flush`, `leaderboard refresh`, and `count` commands talk directly to PostgreSQL through `scripts.ops`.
- `maintenance on` now requests a leaderboard refresh automatically so the main leaderboard status switches to `🟠 Paused (Maintenance)` on the next bot refresh cycle.
- `maintenance off` now clears maintenance mode, releases queued maintenance sends back to `pending`, and requests a leaderboard refresh so the main leaderboard can return to `🟢 Live`.
- `throne invalidate-test-sends` marks previously recorded sends from usernames in `THRONE_TEST_GIFTER_USERNAMES` as `is_test_send=true` so they stop affecting leaderboard totals when test parsing is disabled again.
- `sends backfill-public-ids` generates and stores missing `public_send_id` values for older rows so `/send details send_id:ROB-...` can use indexed DB lookups.
- `logs` and `restart` use `journalctl` and `systemctl`, so they are meant for the server where the service is installed.
- `restart` uses `sudo systemctl restart ...`, so the deploy or operator user should have passwordless sudo for the specific Rob services.
- A minimal sudoers entry is usually enough, for example:

```sudoers
Cmnd_Alias ROB_BOT_CTL = /bin/systemctl restart rob-bot-dev.service, /usr/bin/systemctl restart rob-bot-dev.service
Cmnd_Alias ROB_WEBHOOK_CTL = /bin/systemctl restart rob-webhook-dev.service, /usr/bin/systemctl restart rob-webhook-dev.service
deployuser ALL=(root) NOPASSWD: ROB_BOT_CTL, ROB_WEBHOOK_CTL
```

- `queue flush` refuses to run while maintenance mode is still enabled.

- 2026-05-23: Public send card now uses compact Components V2 layout with real `discord.ui.Separator()`, item thumbnails, friendly currency names, and purple accent constants from `rob/ui/theme.py`; rank lines/footer/timestamps removed.
- 2026-05-23: Added `scripts/robctl throne invalidate-test-sends` so historical known test sends can be backfilled as `is_test_send=true`.
- 2026-05-23: Added `scripts/robctl sends backfill-public-ids` and a stored `sends.public_send_id` column for indexed `/send details` lookups.
- 2026-05-23: NEW LEADER ALERT posting is now live in the leaderboard/send-tracker channel flow with bot-state dedupe.
- 2026-05-23: Leaderboard refreshes now show dynamic status text: `🟢 Live` normally and `🟠 Paused (Maintenance)` when maintenance mode is enabled. `🔴 Offline` is supported at the card layer for an explicit future offline source.
- 2026-05-22: Leaderboard and stats cards now use explicit separator components; stats include Unclaimed Sends section.
- 2026-05-23: `/send details` now supports public Rob Send IDs for receipt-style lookups without exposing raw database IDs on public send cards.
