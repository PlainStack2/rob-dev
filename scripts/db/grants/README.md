# Runtime Grants

These SQL files are environment-specific runtime grants.

- `dev_rob_bot.sql`
- `dev_rob_webhook.sql`
- `prod_rob_bot.sql`
- `prod_rob_webhook.sql`
- `dev_rehearsal_prod_roles.sql` (optional rehearsal only)

Run manually as `doadmin`.

`dev_rehearsal_prod_roles.sql` grants production-style roles access to `rob_dev_v2` for controlled rehearsal only; production runtime should normally use `rob_prod`.

These are intentionally separate from required DB build versions.  
`scripts/check_db.py` validates runtime permissions from the active runtime user.
