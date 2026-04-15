# Three New Features Added

## 1. ✅ Delete All Responses Per Form

**Location:** Form Builder → Survey copy & behavior section

**How it works:**
- Click **"🗑️ Delete all responses for this form"** button in the danger zone
- Confirm the deletion (cannot be undone)
- All responses for that form are permanently deleted
- Historical data is completely removed from the database

**Note:** This only affects the selected form, not other forms.

---

## 2. ✅ Separate Sentiment Analysis Toggle

**Location:** Form Builder → When adding/editing questions

**How it works:**
- When you add a **Short Answer** or **Paragraph** question, a new toggle appears:
  - **"Enable sentiment analysis for this question"** (enabled by default)
  - Uncheck to mark this question as non-sentiment analysis
  - Useful for questions that shouldn't be analyzed (e.g., "What's your name?")

**In the Database:**
- Each question now has an `enable_sentiment` column
- Only questions with `enable_sentiment = true` will be analyzed
- Run the migration: `migration_04_add_enable_sentiment_to_questions.sql`

**Benefits:**
- Separate sentiment questions from non-sentiment questions
- Short answers that need sentiment analysis vs. those that don't
- Better control over which responses get analyzed

---

## 3. ✅ View Individual Respondent Answers

**Location:** Dashboard → **"👤 Respondent Details"** tab (NEW)

**How it works:**
1. Go to your Sentiment Dashboard
2. Click the new **"👤 Respondent Details"** tab
3. Select a respondent from the dropdown (shows submission date + timestamp)
4. View ALL their answers to all questions in the form
5. See sentiment status for each text-based question (if enabled)

**What you see:**
- Question number and type
- The respondent's exact answer
- Sentiment status (if sentiment analysis was enabled for that question)

---

## 🔧 Setup Required

Run this SQL migration in Supabase SQL Editor:

```sql
-- Add enable_sentiment column to form_questions
ALTER TABLE public.form_questions
ADD COLUMN IF NOT EXISTS enable_sentiment boolean DEFAULT true;

CREATE INDEX IF NOT EXISTS idx_form_questions_sentiment ON public.form_questions(admin_email, form_id, enable_sentiment);

COMMENT ON COLUMN public.form_questions.enable_sentiment IS
'If true, sentiment analysis will be applied. If false, question is non-sentiment.';
```

**File:** `sql/migration_04_add_enable_sentiment_to_questions.sql`

---

## 💡 Use Cases

### Delete Responses
- Monthly data cleanup
- Removing test responses
- GDPR/privacy compliance
- Starting fresh for a round of surveys

### Sentiment Toggle
- Mark demographic questions as non-sentiment
- Mark instructions/free text as non-sentiment
- Keep only actual feedback for analysis
- Reduce noise in sentiment analysis

### View Respondent Details
- Quality check individual responses
- Verify data integrity
- Follow up with specific respondents
- See patterns in particular responses
- Audit suspicious responses
