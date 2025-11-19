-- Fix sequence synchronization for email_verifications and other converted tables
-- This fixes the issue where sequences are out of sync with actual data
-- Run this script directly against your PostgreSQL database if you encounter
-- "duplicate key value violates unique constraint" errors

-- Fix email_verifications sequence
SELECT setval(
    'email_verifications_id_seq',
    COALESCE((SELECT MAX(id) FROM email_verifications), 0) + 1,
    false
);

-- Fix registration_data sequence (if it exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'registration_data_id_seq') THEN
        PERFORM setval(
            'registration_data_id_seq',
            COALESCE((SELECT MAX(id) FROM registration_data), 0) + 1,
            false
        );
    END IF;
END $$;

-- Fix password_reset_tokens sequence (if it exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'password_reset_tokens_id_seq') THEN
        PERFORM setval(
            'password_reset_tokens_id_seq',
            COALESCE((SELECT MAX(id) FROM password_reset_tokens), 0) + 1,
            false
        );
    END IF;
END $$;

-- Fix users sequence (if needed)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'users_id_seq') THEN
        PERFORM setval(
            'users_id_seq',
            COALESCE((SELECT MAX(id) FROM users), 0) + 1,
            false
        );
    END IF;
END $$;

-- Fix products sequence (if needed)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'products_id_seq') THEN
        PERFORM setval(
            'products_id_seq',
            COALESCE((SELECT MAX(id) FROM products), 0) + 1,
            false
        );
    END IF;
END $$;

-- Fix orders sequence (if needed)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'orders_id_seq') THEN
        PERFORM setval(
            'orders_id_seq',
            COALESCE((SELECT MAX(id) FROM orders), 0) + 1,
            false
        );
    END IF;
END $$;

-- Verify the fix
SELECT 
    'email_verifications' as table_name,
    (SELECT MAX(id) FROM email_verifications) as max_id,
    (SELECT last_value FROM email_verifications_id_seq) as sequence_value;

