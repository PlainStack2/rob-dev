### `docs/maintenance-mode.md`

````markdown
# Maintenance Mode

Maintenance mode prevents Rob from posting new send notifications to Discord while maintenance is active.

## During Maintenance

- Incoming sends are still saved to PostgreSQL.
- Sends are marked as queued.
- Discord send notifications are not posted.
- Public leaderboards are not refreshed.

## After Maintenance

When maintenance mode is disabled:

1. Rob finds queued sends.
2. Rob posts send notifications oldest-first.
3. Rob marks each send as posted.
4. Rob refreshes leaderboards once.
5. Rob reports any failures through backend logs.

Maintenance mode should be controlled from the backend, not Discord.