-- Run in Supabase SQL Editor (once).
-- Lets "one response only" survive page reload via ?cid=... in the survey URL.

-- 1) Store anonymous browser tab id on each response (from public survey)
ALTER TABLE public.form_responses
ADD COLUMN IF NOT EXISTS client_submission_id text;

CREATE INDEX IF NOT EXISTS idx_form_responses_public_client
ON public.form_responses (public_id, client_submission_id);

-- 2) RLS-safe check (Streamlit uses anon key): SECURITY DEFINER function
CREATE OR REPLACE FUNCTION public.has_form_submission(p_public_id text, p_client_id text)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.form_responses r
    WHERE r.public_id = p_public_id
      AND r.client_submission_id IS NOT NULL
      AND r.client_submission_id = p_client_id
  );
$$;

REVOKE ALL ON FUNCTION public.has_form_submission(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.has_form_submission(text, text) TO anon, authenticated, service_role;
