-- Add status column to user_exam_attempts table if it doesn't exist
ALTER TABLE user_exam_attempts ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT NULL;