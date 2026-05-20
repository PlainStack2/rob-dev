# Maintenance Mode

Maintenance mode is stored in PostgreSQL `bot_state` using:

- `maintenance_mode`
- `maintenance_reason`

It is controlled from backend shell commands, not from broad Discord admin commands.

## During Maintenance

- Incoming sends are still saved to PostgreSQL.
- Webhook sends are inserted as `queued_maintenance`.
- The bot does not post queued sends to Discord.
- Public leaderboards continue to reflect posted sends only.

## After Maintenance

When maintenance mode is disabled, the bot queue worker:

1. Releases `queued_maintenance` sends back to `pending`.
2. Processes them oldest-first.
3. Marks successful posts as `posted`.
4. Marks failures as `failed`.
5. Refreshes public leaderboards.

## Commands

```bash
scripts/robctl maintenance status
scripts/robctl maintenance on "reason"
scripts/robctl maintenance off
scripts/robctl queue status
scripts/robctl queue flush
```
