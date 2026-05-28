# Rob v2 DB Build Scripts

These are **manual DB build scripts** for Rob v2.

- Run them manually in pgAdmin4 or `psql` as `doadmin`.
- Start with `rob_dev_v2` first.

Run in order:

1. `001_core_schema.sql`
2. `002_indexes.sql`
3. `003_achievements.sql`
4. `../grants/dev_rob_bot.sql`
5. `../grants/dev_rob_webhook.sql`

Important:

- Use `../grants/dev_rehearsal_prod_roles.sql` only when intentionally validating production-style runtime roles against `rob_dev_v2` before prod cutover.
- Do not run prod grants against dev databases except the explicit rehearsal file.
- Re-run the relevant grants file after adding `003_achievements.sql` so runtime users can access achievement tables.
- Do not run manual cleanup scripts unless you are intentionally cleaning an old database.
- These are DB build scripts, not runtime migrations.
