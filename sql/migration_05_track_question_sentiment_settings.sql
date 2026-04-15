-- Multi-Form System Migration — Part 5
-- Enhance form_responses to track question-level sentiment settings
-- This allows proper filtering of which questions should be analyzed

-- Add question_ids column to track which questions were answered
ALTER TABLE public.form_responses
ADD COLUMN IF NOT EXISTS question_ids text[];

-- Add enable_sentiment_flags column to track which questions have sentiment enabled
ALTER TABLE public.form_responses
ADD COLUMN IF NOT EXISTS enable_sentiment_flags boolean[];

-- This allows us to reconstruct: answer[i] belongs to question_ids[i] with sentiment setting enable_sentiment_flags[i]
-- Example: 
-- answers: {"Q1": "Maria", "Q2": "Lopez", "Q3": "Great service"}
-- question_ids: ["Q1", "Q2", "Q3"]
-- enable_sentiment_flags: [false, false, true]
-- raw_feedback should only include: "Great service" (where enable_sentiment_flags[i] = true)

COMMENT ON COLUMN public.form_responses.question_ids IS 
'Parallel array to answers - stores question IDs in the same order as the answers being stored';

COMMENT ON COLUMN public.form_responses.enable_sentiment_flags IS 
'Parallel array to answers - stores whether sentiment analysis is enabled for each question (true/false)';
