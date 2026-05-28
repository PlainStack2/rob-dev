-- Dev runtime grants for dev_rob_webhook on rob_dev_v2.
-- Run manually as doadmin.
-- This user is intentionally narrower than dev_rob_bot.

\connect rob_dev_v2

GRANT CONNECT ON DATABASE rob_dev_v2 TO dev_rob_webhook;
GRANT USAGE ON SCHEMA public TO dev_rob_webhook;

GRANT SELECT ON
  db_build_version,
  bot_settings,
  bot_users,
  dommes,
  subs,
  vib_settings,
  vib_leaderboard,
  user_achievements,
  achievement_events
TO dev_rob_webhook;

GRANT SELECT, INSERT, UPDATE ON
  sends,
  bot_users
TO dev_rob_webhook;

GRANT SELECT, INSERT ON
  user_achievements,
  achievement_events
TO dev_rob_webhook;

GRANT SELECT, UPDATE ON
  dommes,
  bot_settings
TO dev_rob_webhook;

GRANT USAGE, SELECT, UPDATE
ON SEQUENCE sends_id_seq
TO dev_rob_webhook;

GRANT USAGE, SELECT, UPDATE
ON SEQUENCE bot_users_id_seq
TO dev_rob_webhook;

GRANT USAGE, SELECT, UPDATE
ON SEQUENCE user_achievements_id_seq
TO dev_rob_webhook;

GRANT USAGE, SELECT, UPDATE
ON SEQUENCE achievement_events_id_seq
TO dev_rob_webhook;

REVOKE CREATE ON SCHEMA public FROM dev_rob_webhook;
REVOKE DELETE ON TABLE sends FROM dev_rob_webhook;
REVOKE DELETE ON TABLE bot_users FROM dev_rob_webhook;
REVOKE DELETE ON TABLE user_achievements FROM dev_rob_webhook;
REVOKE DELETE ON TABLE achievement_events FROM dev_rob_webhook;

-- Do not grant CREATE, ALTER, DROP, or TRUNCATE to dev_rob_webhook.
