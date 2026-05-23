ALTER TABLE sends
ADD COLUMN IF NOT EXISTS public_send_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_sends_public_send_id
ON sends(public_send_id)
WHERE public_send_id IS NOT NULL;
