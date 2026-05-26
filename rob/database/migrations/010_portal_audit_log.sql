CREATE TABLE IF NOT EXISTS portal_audit_log (
    id BIGSERIAL PRIMARY KEY,
    actor_discord_user_id BIGINT NOT NULL,
    actor_username TEXT,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_portal_audit_log_created_at
ON portal_audit_log (created_at DESC);
