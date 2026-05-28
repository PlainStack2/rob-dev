# Database Build (Manual SQL)

Rob v2 schema build is manual and admin-driven.

## Important terminology

- **DB build scripts**: SQL files that create/alter schema.
- **Data migration**: moving legacy SQLite data into PostgreSQL.

Only SQLite -> PostgreSQL transfer should be called a migration.

## Run order

Execute as `doadmin` in pgAdmin4 or `psql`:

1. `scripts/db/build/001_core_schema.sql`
2. `scripts/db/build/002_indexes.sql`
3. `scripts/db/build/003_achievements.sql`
4. `scripts/db/build/003_runtime_grants_template.sql` (optional reference template)

Then apply runtime grants:

- Dev bot: `scripts/db/grants/dev_rob_bot.sql`
- Dev webhook: `scripts/db/grants/dev_rob_webhook.sql`
- Prod bot: `scripts/db/grants/prod_rob_bot.sql`
- Prod webhook: `scripts/db/grants/prod_rob_webhook.sql`
- Optional prod-role rehearsal on dev: `scripts/db/grants/dev_rehearsal_prod_roles.sql`

Required `db_build_version` rows are:

- `001_core_schema`
- `002_indexes`
- `003_achievements`

`dev_rehearsal_prod_roles.sql` is for controlled rehearsal/testing only. It grants `prod_rob_bot` and `prod_rob_webhook` access to `rob_dev_v2` so prod-style credentials and permissions can be validated before creating/using `rob_prod`; it should not be used as a normal prod runtime target.

Runtime grants are environment-specific and are validated by `scripts/check_db.py` from runtime credentials.

## Target tables

- `db_build_version`
- `bot_settings`
- `bot_users`
- `dommes`
- `subs`
- `sends`
- `vib_settings`
- `vib_leaderboard`
- `the_count`
- `inactive_users`
- `user_achievements`
- `achievement_events`

## Runtime safety

Runtime users (`dev_rob_bot`, `dev_rob_webhook`, `prod_rob_bot`, `prod_rob_webhook`) must not receive:

- `CREATE`
- `ALTER`
- `DROP`
- `TRUNCATE`

Use `scripts/check_db.py` from runtime credentials to validate permissions and table/column shape.
