-- Rob DB Grants (Production)
-- Run after schema migrations have been applied to rob_prod.
-- Recommended execution:
--   psql "$ADMIN_DATABASE_URL" -f scripts/db/04_grant_prod_permissions.sql

\connect rob_prod

-- Database-level connectivity
GRANT CONNECT ON DATABASE rob_prod TO rob_prod_migrator;
GRANT CONNECT ON DATABASE rob_prod TO rob_prod_bot;
GRANT CONNECT ON DATABASE rob_prod TO rob_prod_webhook;
GRANT CONNECT ON DATABASE rob_prod TO rob_prod_portal;

-- Schema usage
GRANT USAGE, CREATE ON SCHEMA public TO rob_prod_migrator;
GRANT USAGE ON SCHEMA public TO rob_prod_bot;
GRANT USAGE ON SCHEMA public TO rob_prod_webhook;
GRANT USAGE ON SCHEMA public TO rob_prod_portal;

-- Runtime users should not create schema objects.
REVOKE CREATE ON SCHEMA public FROM rob_prod_bot;
REVOKE CREATE ON SCHEMA public FROM rob_prod_webhook;
REVOKE CREATE ON SCHEMA public FROM rob_prod_portal;

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
TO rob_prod_bot;

GRANT SELECT ON TABLE schema_migrations TO rob_prod_bot;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO rob_prod_bot;

-- Webhook runtime grants (narrower)
GRANT SELECT ON TABLE
    guild_settings,
    dommes,
    subs,
    public_leaderboards,
    leaderboard_message,
    schema_migrations
TO rob_prod_webhook;

GRANT SELECT, UPDATE ON TABLE
    throne_creators,
    bot_state
TO rob_prod_webhook;

GRANT SELECT, INSERT, UPDATE ON TABLE sends TO rob_prod_webhook;
REVOKE DELETE ON TABLE sends FROM rob_prod_webhook;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE public.sends_id_seq TO rob_prod_webhook;

-- Portal runtime grants
GRANT SELECT ON TABLE
    schema_migrations,
    sends,
    leaderboard_message,
    counting_state
TO rob_prod_portal;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    guild_settings,
    dommes,
    subs,
    send_requests,
    throne_creators,
    public_leaderboards,
    bot_state,
    blacklist
TO rob_prod_portal;

GRANT SELECT, INSERT ON TABLE portal_audit_log TO rob_prod_portal;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO rob_prod_portal;

-- Default privileges for future objects created by the prod migrator.
ALTER DEFAULT PRIVILEGES FOR ROLE rob_prod_migrator IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rob_prod_bot;

ALTER DEFAULT PRIVILEGES FOR ROLE rob_prod_migrator IN SCHEMA public
GRANT SELECT ON TABLES TO rob_prod_webhook;

ALTER DEFAULT PRIVILEGES FOR ROLE rob_prod_migrator IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO rob_prod_bot;

ALTER DEFAULT PRIVILEGES FOR ROLE rob_prod_migrator IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO rob_prod_webhook;

ALTER DEFAULT PRIVILEGES FOR ROLE rob_prod_migrator IN SCHEMA public
GRANT SELECT ON TABLES TO rob_prod_portal;

ALTER DEFAULT PRIVILEGES FOR ROLE rob_prod_migrator IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO rob_prod_portal;
