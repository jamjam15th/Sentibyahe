-- Run once in Supabase SQL Editor.
-- Optional text shown to respondents after they submit (who to contact).

ALTER TABLE public.form_meta
ADD COLUMN IF NOT EXISTS reach_out_contact text;

COMMENT ON COLUMN public.form_meta.reach_out_contact IS
  'Shown on the public survey after a response (e.g. email or org to contact).';
