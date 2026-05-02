-- Migration 08: Add excluded_bubble_words column to form_meta
-- Purpose: Store user-defined list of words to exclude from bubble chart visualization
-- Usage: Users can configure which words they want to filter out from the 
--        "Commuter Insights: What Words Describe What?" visualization

ALTER TABLE form_meta
ADD COLUMN excluded_bubble_words JSONB DEFAULT '[]'::jsonb;

-- Add index for faster queries (optional, but recommended if you filter frequently)
-- CREATE INDEX idx_form_meta_excluded_words ON form_meta USING GIN (excluded_bubble_words);

-- Comment for clarity
COMMENT ON COLUMN form_meta.excluded_bubble_words IS 
'JSON array of words to exclude from bubble chart visualization. 
Example: ["thing", "stuff", "ok", "very"]. 
Words are matched case-insensitively during filtering.';
