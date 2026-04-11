-- Run this once in Supabase: SQL Editor → New query → Run
-- Fixes: PGRST204 Could not find the 'allow_multiple_responses' column of 'form_meta'

ALTER TABLE public.form_meta
ADD COLUMN IF NOT EXISTS allow_multiple_responses boolean NOT NULL DEFAULT true;

COMMENT ON COLUMN public.form_meta.allow_multiple_responses IS
  'If true, public survey shows Submit another response; if false, one submission per browser session.';
