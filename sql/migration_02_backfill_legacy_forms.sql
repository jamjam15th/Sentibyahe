-- Multi-Form System Migration — Part 2
-- Backfill legacy form_id for existing users (backward compatibility)
-- Run this AFTER migration_01_create_form_list.sql
-- Run this in Supabase → SQL Editor

-- Step 1: Create form entries for users with existing data
INSERT INTO public.form_list (form_id, admin_email, title, description, created_at, is_archived)
SELECT 
  -- Use MD5 hash of admin_email as legacy form_id (same as old public_id calculation)
  SUBSTRING(md5(COALESCE(admin_email, '')), 1, 12),
  admin_email,
  'My First Form (Migrated)',
  'Your original survey from the single-form system',
  NOW(),
  FALSE
FROM (
  SELECT DISTINCT admin_email FROM public.form_questions WHERE admin_email IS NOT NULL
) users
WHERE NOT EXISTS (
  SELECT 1 FROM public.form_list fl 
  WHERE fl.admin_email = users.admin_email
)
ON CONFLICT (admin_email, form_id) DO NOTHING;

-- Step 2: Backfill form_id into form_questions
UPDATE public.form_questions q
SET form_id = SUBSTRING(md5(q.admin_email), 1, 12)
WHERE q.form_id IS NULL AND q.admin_email IS NOT NULL;

-- Step 3: Backfill form_id into form_meta
UPDATE public.form_meta m
SET form_id = SUBSTRING(md5(m.admin_email), 1, 12)
WHERE m.form_id IS NULL AND m.admin_email IS NOT NULL;

-- Step 4: Backfill form_id into form_responses
UPDATE public.form_responses r
SET form_id = SUBSTRING(md5(r.admin_email), 1, 12)
WHERE r.form_id IS NULL AND r.admin_email IS NOT NULL;

-- Verify the migration
SELECT 'form_questions' as table_name, COUNT(*) as total, COUNT(form_id) as with_form_id FROM public.form_questions
UNION ALL
SELECT 'form_meta', COUNT(*), COUNT(form_id) FROM public.form_meta
UNION ALL
SELECT 'form_responses', COUNT(*), COUNT(form_id) FROM public.form_responses
UNION ALL
SELECT 'form_list', COUNT(*), COUNT(form_id) FROM public.form_list;
