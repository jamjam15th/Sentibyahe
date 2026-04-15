-- Multi-Form System Migration — Part 6
-- Enable per-question sentiment analysis (each answer analyzed separately)
-- This allows storing individual sentiment for each question, not combined

-- Add columns to store per-question sentiment analysis
ALTER TABLE public.form_responses
ADD COLUMN IF NOT EXISTS question_sentiments jsonb;

-- Example structure:
-- {
--   "q1_id": {"text": "Maria", "enable_sentiment": false, "sentiment": null},
--   "q2_id": {"text": "Lopez", "enable_sentiment": false, "sentiment": null},
--   "q3_id": {"text": "Great service", "enable_sentiment": true, "sentiment": "POSITIVE"}
-- }

COMMENT ON COLUMN public.form_responses.question_sentiments IS 
'JSON object storing per-question sentiment analysis. 
Structure: {question_id: {text: string, enable_sentiment: boolean, sentiment: POSITIVE|NEUTRAL|NEGATIVE}}
This allows each answer to be analyzed SEPARATELY with its own sentiment label.';

-- Create index for querying sentiments
CREATE INDEX IF NOT EXISTS idx_form_responses_question_sentiments ON public.form_responses USING gin (question_sentiments);
