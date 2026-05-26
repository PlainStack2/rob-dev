-- Rob DB Grants (Development)
-- Run after schema migrations have been applied to rob_dev.
-- Recommended execution:
--   psql "$ADMIN_DATABASE_URL" -f scripts/db/03_grant_dev_permissions.sql

\connect rob_dev

-- Database-level connectivity
GRANT CONNECT ON DATABASE rob_dev TO rob_dev_migrator;
GRANT CONNECT ON DATABASE rob_dev TO rob_dev_bot;
GRANT CONNECT ON DATABASE rob_dev TO rob_dev_webhook;
GRANT CONNECT ON DATABASE rob_dev TO rob_dev_portal;

-- Schema usage
GRANT USAGE, CREATE ON SCHEMA public TO rob_dev_migrator;
GRANT USAGE ON SCHEMA public TO rob_dev_bot;
GRANT USAGE ON SCHEMA public TO rob_dev_webhook;
GRANT USAGE ON SCHEMA public TO rob_dev_portal;

-- Runtime users should not create schema objects.
REVOKE CREATE ON SCHEMA public FROM rob_dev_bot;
REVOKE CREATE ON SCHEMA public FROM rob_dev_webhook;
REVOKE CREATE ON SCHEMA public FROM rob_dev_portal;

-- Bot runtime grants
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    blacklist,
    bot_state,
    counting_state,
    dommes,
    guild_settings,
    leaderboard_message,
    public_leaderboards,
    send_requests,
    sends,
    subs,
    throne_creators
TO rob_dev_bot;

GRANT SELECT ON TABLE schema_migrations TO rob_dev_bot;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO rob_dev_bot;

-- Webhook runtime grants (narrower)
GRANT SELECT ON TABLE
    guild_settings,
    dommes,
    subs,
    public_leaderboards,
    leaderboard_message,
    schema_migrations
TO rob_dev_webhook;

GRANT SELECT, UPDATE ON TABLE
    throne_creators,
    bot_state
TO rob_dev_webhook;

GRANT SELECT, INSERT, UPDATE ON TABLE sends TO rob_dev_webhook;
REVOKE DELETE ON TABLE sends FROM rob_dev_webhook;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.sends_id_seq TO rob_dev_webhook;

-- Portal runtime grants
GRANT SELECT ON TABLE
    schema_migrations,
    sends,
    leaderboard_message,
    counting_state
TO rob_dev_portal;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    guild_settings,
    dommes,
    subs,
    send_requests,
    throne_creators,
    public_leaderboards,
    bot_state,
    blacklist
TO rob_dev_portal;

GRANT SELECT, INSERT ON TABLE portal_audit_log TO rob_dev_portal;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO rob_dev_portal;

-- Default privileges for future objects created by the dev migrator.
ALTER DEFAULT PRIVILEGES FOR ROLE rob_dev_migrator IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rob_dev_bot;

ALTER DEFAULT PRIVILEGES FOR ROLE rob_dev_migrator IN SCHEMA public
GRANT SELECT ON TABLES TO rob_dev_webhook;

ALTER DEFAULT PRIVILEGES FOR ROLE rob_dev_migrator IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO rob_dev_bot;

ALTER DEFAULT PRIVILEGES FOR ROLE rob_dev_migrator IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO rob_dev_webhook;

ALTER DEFAULT PRIVILEGES FOR ROLE rob_dev_migrator IN SCHEMA public
GRANT SELECT ON TABLES TO rob_dev_portal;

ALTER DEFAULT PRIVILEGES FOR ROLE rob_dev_migrator IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO rob_dev_portal;
