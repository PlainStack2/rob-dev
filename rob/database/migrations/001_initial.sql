CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY,
    registration_channel_id BIGINT,
    leaderboard_channel_id BIGINT,
    send_track_channel_id BIGINT,
    counting_channel_id BIGINT,
    domme_role_id BIGINT,
    sub_role_id BIGINT,
    mod_role_id BIGINT,
    warn_log_channel_id BIGINT,
    carlbot_user_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bot_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dommes (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guild_settings(guild_id) ON DELETE CASCADE,
    discord_user_id BIGINT NOT NULL,
    throne_url TEXT NOT NULL,
    registered_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (guild_id, discord_user_id)
);

CREATE TABLE IF NOT EXISTS subs (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guild_settings(guild_id) ON DELETE CASCADE,
    discord_user_id BIGINT NOT NULL,
    send_name TEXT NOT NULL,
    registered_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (guild_id, discord_user_id),
    UNIQUE (guild_id, lower(send_name))
);

CREATE TABLE IF NOT EXISTS throne_creators (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guild_settings(guild_id) ON DELETE CASCADE,
    domme_id BIGINT REFERENCES dommes(id) ON DELETE SET NULL,
    discord_user_id BIGINT NOT NULL,
    throne_handle TEXT NOT NULL,
    throne_creator_id TEXT NOT NULL,
    hide_own_purchases BOOLEAN,
    tracking_mode TEXT NOT NULL DEFAULT 'webhook',
    -- Legacy to be deleted: webhook_secret
    webhook_secret TEXT,
    webhook_secret_hash TEXT,
    webhook_connected_at TIMESTAMPTZ,
    overlay_detected BOOLEAN NOT NULL DEFAULT false,
    last_overlay_check_at TIMESTAMPTZ,
    last_successful_event_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (guild_id, discord_user_id),
    UNIQUE (guild_id, throne_handle),
    UNIQUE (guild_id, throne_creator_id)
);

CREATE INDEX IF NOT EXISTS idx_throne_creators_creator_id
ON throne_creators (throne_creator_id);

CREATE TABLE IF NOT EXISTS throne_wishlist_items (
    id BIGSERIAL PRIMARY KEY,
    creator_id TEXT NOT NULL,
    wishlist_item_id TEXT NOT NULL,
    item_name TEXT,
    item_image_url TEXT,
    amount_cents INTEGER NOT NULL DEFAULT 0,
    currency TEXT,
    is_available BOOLEAN,
    last_seen_at TIMESTAMPTZ NOT NULL,
    UNIQUE (creator_id, wishlist_item_id)
);

CREATE INDEX IF NOT EXISTS idx_throne_wishlist_items_creator
ON throne_wishlist_items (creator_id);

CREATE TABLE IF NOT EXISTS sends (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guild_settings(guild_id) ON DELETE CASCADE,
    domme_id BIGINT REFERENCES dommes(id) ON DELETE SET NULL,
    domme_user_id BIGINT NOT NULL,
    sub_id BIGINT REFERENCES dommes(id) ON DELETE SET NULL,
    sub_user_id BIGINT,
    sub_name TEXT,
    amount_cents INTEGER NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'USD',
    method TEXT,
    source TEXT NOT NULL DEFAULT 'unknown',
    item_name TEXT,
    item_image_url TEXT,
    external_id TEXT,
    event_id TEXT,
    fallback_event_hash TEXT,
    is_private BOOLEAN NOT NULL DEFAULT false,
    seeded BOOLEAN NOT NULL DEFAULT false,
    sent_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    discord_post_status TEXT NOT NULL DEFAULT 'pending',
    discord_posted_at TIMESTAMPTZ,
    discord_message_id BIGINT,
    discord_post_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (external_id),
    UNIQUE (event_id),
    UNIQUE (fallback_event_hash)
);

CREATE INDEX IF NOT EXISTS idx_sends_guild_received_at
ON sends (guild_id, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_sends_discord_post_status
ON sends (discord_post_status);

CREATE INDEX IF NOT EXISTS idx_sends_domme_user_id
ON sends (domme_user_id);

CREATE INDEX IF NOT EXISTS idx_sends_sub_user_id
ON sends (sub_user_id);

CREATE INDEX IF NOT EXISTS idx_sends_sub_name
ON sends (sub_name);

CREATE TABLE IF NOT EXISTS send_requests (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guild_settings(guild_id) ON DELETE CASCADE,
    sub_user_id BIGINT NOT NULL,
    domme_user_id BIGINT NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    methosd TEXT NOT NULL,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXSITS idx_send_requests_rate_limit
ON send_requests (sub_user_id, domme_user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_send_requests_status
ON send_requests (guild_id, status);

CREATE TABLE IF NOT EXISTS leaderboard_message (
    id BIGSERIAL PRIMARY KEY
    guild_id BIGINT NOT NULL REFERENCE guild_settings(guild_id) ON DELETE CASCADE,
    message_key TEXT NOT NULL,
    leaderboard_type TEXT,
    channel_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (guild_id, message_key)
);

CREATE TABLE IF NOT EXISTS counting_state (
    guild_id BIGINT PRIMARY KEY REFERENCE guild_settings(guild_id) ON DELETE CASCADE,
    channel_id BIGINT,
    current_number BIGINT NOT NULL DEFAULT 0,
    last_user_id BIGINT,
    is_enabled BOOLEAN NOT NULL DEFAULT false,
    pending_restore BOOLEAN NOT NULL DEFAULT false,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS blacklist (
    discord_user_id BIGINT PRIMARY KEY,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    created_by BIGINT
);