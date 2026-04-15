-- Multi-Form System Migration — Part 3
-- Reconstruct PRIMARY KEY for form_meta to support multiple forms per user
-- Run this AFTER migration_02_backfill_legacy_forms.sql
-- Run this in Supabase → SQL Editor

-- Step 1: Drop the old PRIMARY KEY constraint
ALTER TABLE public.form_meta
DROP CONSTRAINT form_meta_pkey;

-- Step 2: Create a new composite PRIMARY KEY on (admin_email, form_id)
ALTER TABLE public.form_meta
ADD PRIMARY KEY (admin_email, form_id);

-- Step 3: Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_form_meta_admin_form ON public.form_meta(admin_email, form_id);
