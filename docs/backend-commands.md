# Backend Commands

Use [`scripts/robctl`](/Users/patfaint/Documents/New%20project/scripts/robctl) from the server checkout, or install a shell alias that points to it.

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

scripts/robctl count status
scripts/robctl count set 123
```

## Notes

- `maintenance on/off`, `queue status`, `queue flush`, `leaderboard refresh`, and `count` commands talk directly to PostgreSQL through `scripts.ops`.
- `logs` and `restart` use `journalctl` and `systemctl`, so they are meant for the server where the service is installed.
- `queue flush` refuses to run while maintenance mode is still enabled.
