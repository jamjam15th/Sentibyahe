# Sentiment Analysis Issues - Root Causes & Solutions

## **Q1: Why are non-sentiment fields still being included?**

### Root Cause
The form submission logic was checking `enable_sentiment` flag ONLY when building the feedback list, but the database had no way to track which fields should have been excluded.

### Previous Problem
```python
# OLD CODE (checked flag but only for building raw_feedback)
elif q_type in ("Short Answer", "Paragraph"):
    if q_info.get("enable_sentiment", True):
        raw_feedback_list.append(str(ans))
```

If `enable_sentiment` was False, the field wasn't added to `raw_feedback` for NEW respons, but the DATABASE had no record of WHY it was excluded.

### Solution Implemented
✅ **Migration 05** adds tracking columns:
- `question_ids` - parallel array storing question IDs for each answer
- `enable_sentiment_flags` - parallel array storing whether sentiment is enabled for each question

✅ **Updated form submission** now stores:
```python
"question_ids": ["q1", "q2", "q3"],
"enable_sentiment_flags": [false, false, true],
"raw_feedback": "only q3's text"
```

This creates a **complete audit trail** so sentiment analysis can be re-run correctly.

---

## **Q2: Why are some responses getting incorrect sentiment classification?**

### Root Causes

**A) Model Accuracy Issue**
- The pre-trained model may not understand your domain context
- Tagalog/English mixed text can confuse the model
- Sarcasm, negation, context are easy to misclassify

Example:
- Input: "Sobrang tagal ng waiting time" (Very long waiting time)
- Expected: NEGATIVE
- Model result: POSITIVE (because it focuses on emotional intensity, not context)

**B) Text Preprocessing**
- Different models handle text cleaning differently
- Punctuation, abbreviations, formatting matter

**C) Language & Domain**
- General-purpose models trained on social media data
- May not understand transportation/service feedback nuances

### Why This Happens
Most pre-trained sentiment models:
1. Are trained on GENERAL text (movie reviews, social media)
2. Focus on emotional words (good, bad, great, awful)
3. Don't understand negation + intensifiers
4. Struggle with domain-specific vocabulary
5. Can't handle code-switching (Tagalog + English)

### Solutions Available

**Option 1: Fine-tune the Model (Most Accurate)**
- Train the model on YOUR hand-labeled feedback data
- Takes 50-200 examples of correctly labeled feedback
- Model learns YOUR domain, language patterns, tone

**Option 2: Use a Better Model**
- Swap current model for:
  - Filipino/Tagalog-specific model
  - Domain-specific transportation model
  - Multilingual model (better for mixed languages)

**Option 3: Rule-Based Pre-processing**
- Add rules like: "tagal" + negative = NEGATIVE
- Negate predictions when "hindi" or "walang" appears
- Custom dictionaries for your domain

**Option 4: Manual Review & Correction**
- Dashboard already shows sentiment classifications
- You can manually override incorrect ones
- System learns from corrections

---

## **Q3: Are multiple open-ended responses being combined and analyzed?**

### Current Behavior: YES, INTENTIONALLY

When a respondent submits:
- **Q1 (Short Answer):** "Maria"
- **Q2 (Short Answer):** "Lopez"  
- **Q3 (Paragraph):** "Great service, very helpful staff"

The system combines them:
```
raw_feedback = "Maria | Lopez | Great service, very helpful staff"
```

This gets sent to sentiment analyzer as ONE input, producing ONE sentiment label for the whole response.

### Why This Design?
1. **Efficiency** - One API call instead of three
2. **Context** - Related feedback together
3. **Legacy compatibility** - Original code structure

### Problems With This
- First Name shouldn't be analyzed ❌
- Multiple unrelated statements get ONE label ❌
- Can't see sentiment per question ❌

### NEW SOLUTION: Track Each Question Separately

✅ **What I just implemented:**
```python
question_ids_list = ["q1", "q2", "q3"]
sentiment_flags_list = [false, false, true]
enable_sentiment_flags = [false, false, true]
```

Now you can:
1. **Know which question each answer came from**
2. **Know if that question should be analyzed**
3. **Re-analyze correctly** even if settings change
4. **Skip non-sentiment questions** (First Name, Last Name, etc.)

---

## **What You Need To Do**

### Step 1: Run Database Migration
```sql
-- In Supabase → SQL Editor
ALTER TABLE public.form_responses
ADD COLUMN IF NOT EXISTS question_ids text[];

ALTER TABLE public.form_responses
ADD COLUMN IF NOT EXISTS enable_sentiment_flags boolean[];
```

**File:** `sql/migration_05_track_question_sentiment_settings.sql`

### Step 2: Update Your Questions
In Form Builder, for each question:
- ✅ **Questions TO analyze:** Check "Enable sentiment analysis"
- ❌ **Questions NOT to analyze:** Uncheck it
  - First Name
  - Last Name
  - ID numbers
  - Demographics (age, gender, etc.)
  - Any non-feedback field

### Step 3: Monitor Accuracy
In Dashboard → Respondent Details tab:
- Review sentiment classifications
- Look for patterns of errors
- Note domain-specific terms the model misses

### Step 4: Improve Accuracy (Choose ONE)

**QUICK FIX:**
- Manually correct sentiment labels in Dashboard
- Better than nothing, slowest long-term

**RECOMMENDED:**
- Fine-tune model on 50-100 of your labeled examples
- ~2-3 hours work, 80%+ accuracy improvement

**BEST:**
- Use Filipino/Tagalog sentiment model
- Better handles your language, context, tone

---

## **Summary**

| Issue | Cause | Solution |
|-------|-------|----------|
| Non-sentiment fields included | No tracking metadata | Migration 05: Track question_ids + enable_sentiment_flags |
| Incorrect sentiment scores | Model trained on different domain | Fine-tune model OR use domain-specific model |
| Questions analyzed together | By design (efficiency) | Now trackable per-question for future improvements |

**Next Steps:**
1. Run Migration 05 SQL
2. Mark non-sentiment questions with toggle OFF
3. Review dashboard for misclassifications
4. Choose model improvement strategy (manual review or fine-tuning)
