DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'leaderboard_messages'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'leaderboard_message'
    ) THEN
        ALTER TABLE leaderboard_messages RENAME TO leaderboard_message;
    END IF;
END $$;
