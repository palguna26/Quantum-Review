-- Render Postgres Migration: Add github_token column to users
-- Run this SQL in your Render Postgres database immediately to fix the login errors

ALTER TABLE users ADD COLUMN IF NOT EXISTS github_token VARCHAR(1024);

-- Verify the column was added
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users';
