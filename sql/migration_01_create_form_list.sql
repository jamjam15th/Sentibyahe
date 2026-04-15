-- Multi-Form System Migration — Part 1
-- Create the form_list table to track all forms per user
-- Run this in Supabase → SQL Editor

CREATE TABLE IF NOT EXISTS public.form_list (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  form_id text NOT NULL,
  admin_email text NOT NULL,
  title text NOT NULL DEFAULT 'Untitled Form',
  description text DEFAULT '',
  created_at timestamp WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  is_archived boolean DEFAULT FALSE,
  
  -- Constraints
  CONSTRAINT unique_user_form UNIQUE(admin_email, form_id)
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_form_list_admin ON public.form_list(admin_email);
CREATE INDEX IF NOT EXISTS idx_form_list_form_id ON public.form_list(form_id);
CREATE INDEX IF NOT EXISTS idx_form_list_admin_active ON public.form_list(admin_email, is_archived);

-- Add form_id columns to existing tables
ALTER TABLE public.form_questions ADD COLUMN IF NOT EXISTS form_id text;
ALTER TABLE public.form_meta ADD COLUMN IF NOT EXISTS form_id text;
ALTER TABLE public.form_responses ADD COLUMN IF NOT EXISTS form_id text;

-- Create indexes on form_id columns
CREATE INDEX IF NOT EXISTS idx_form_questions_form_id ON public.form_questions(form_id);
CREATE INDEX IF NOT EXISTS idx_form_meta_form_id ON public.form_meta(form_id);
CREATE INDEX IF NOT EXISTS idx_form_responses_form_id ON public.form_responses(form_id);

-- Combined indexes for common queries
CREATE INDEX IF NOT EXISTS idx_form_questions_admin_form ON public.form_questions(admin_email, form_id);
CREATE INDEX IF NOT EXISTS idx_form_meta_admin_form ON public.form_meta(admin_email, form_id);
CREATE INDEX IF NOT EXISTS idx_form_responses_admin_form ON public.form_responses(admin_email, form_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON public.form_list TO anon, authenticated, service_role;
