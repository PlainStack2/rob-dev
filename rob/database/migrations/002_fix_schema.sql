ALTER TABLE sends
DROP CONSTRAINT IF EXISTS sends_sub_id_fkey;

ALTER TABLE sends
ADD CONSTRAINT sends_sub_id_fkey
FOREIGN KEY (sub_id)
REFERENCES subs(id)
ON DELETE SET NULL;

ALTER TABLE send_requests
RENAME COLUMN methosd TO method;

ALTER TABLE leaderboard_message
RENAME TO leaderboard_messages;