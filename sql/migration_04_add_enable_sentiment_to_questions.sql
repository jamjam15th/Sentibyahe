-- Multi-Form System Migration — Part 4
-- Add enable_sentiment column to form_questions for selective sentiment analysis
-- Run this in Supabase → SQL Editor

-- Add enable_sentiment column to form_questions
-- Default to true for backward compatibility (existing questions get sentiment analysis)
ALTER TABLE public.form_questions
ADD COLUMN IF NOT EXISTS enable_sentiment boolean DEFAULT true;

-- Create index for filtering sentiment questions
CREATE INDEX IF NOT EXISTS idx_form_questions_sentiment ON public.form_questions(admin_email, form_id, enable_sentiment);

-- Add comment for clarity
COMMENT ON COLUMN public.form_questions.enable_sentiment IS
'If true, sentiment analysis will be applied to this question. If false, question is treated as non-sentiment (e.g., short answer, demographics).';
