-- Migration 07: Add is_locked field to form_questions and include_standard_servqual_questions to form_meta
-- This migration adds support for locked SERVQUAL questions and a toggle to include/exclude them

-- Step 1: Add is_locked column to form_questions (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'form_questions' AND column_name = 'is_locked'
    ) THEN
        ALTER TABLE form_questions ADD COLUMN is_locked BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Step 2: Add include_standard_servqual_questions column to form_meta (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'form_meta' AND column_name = 'include_standard_servqual_questions'
    ) THEN
        ALTER TABLE form_meta ADD COLUMN include_standard_servqual_questions BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- Step 3: Mark existing SERVQUAL dimension questions as locked
-- This assumes standard SERVQUAL questions have dimension names: Tangibles, Reliability, Responsiveness, Assurance, Empathy
UPDATE form_questions 
SET is_locked = TRUE 
WHERE servqual_dimension IN ('Tangibles', 'Reliability', 'Responsiveness', 'Assurance', 'Empathy')
AND is_locked = FALSE;

-- Step 4: Also lock "Additional Comments" questions (questions without a servqual_dimension but are not demographic)
UPDATE form_questions 
SET is_locked = TRUE 
WHERE prompt LIKE 'Additional Comments%' 
AND is_demographic = FALSE 
AND servqual_dimension IS NULL
AND is_locked = FALSE;

-- Verification: Show counts of locked vs unlocked questions per form
-- SELECT admin_email, form_id, COUNT(*) as total, SUM(CASE WHEN is_locked THEN 1 ELSE 0 END) as locked_count
-- FROM form_questions
-- GROUP BY admin_email, form_id
-- ORDER BY admin_email, form_id;
