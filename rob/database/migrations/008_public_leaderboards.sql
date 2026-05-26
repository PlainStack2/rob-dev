CREATE TABLE IF NOT EXISTS public_leaderboards (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guild_settings(guild_id) ON DELETE CASCADE,
    public_token TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL DEFAULT 'Send Leaderboard',
    enabled BOOLEAN NOT NULL DEFAULT true,
    theme TEXT NOT NULL DEFAULT 'goth_red',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

