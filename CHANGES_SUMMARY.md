# Changes Summary - Per-Question Sentiment Analysis

## **Files Modified**

### 1. `public_form.py` - Form Submission Logic
**Lines 501-545: Answer Processing**

**Key Changes:**
- ✅ Added `question_sentiments` dictionary to track each answer separately
- ✅ Modified loop to check `enable_sentiment` flag per question
- ✅ Only adds text to `raw_feedback` if question is marked for sentiment analysis
- ✅ Stores full question_sentiments structure with text, enable_sentiment flag, and placeholder for sentiment

**What it does:**
```python
question_sentiments = {}  # Store per-question sentiment data

for uprompt, ans in user_answers.items():
    q_info = question_map[uprompt]
    q_id = q_info.get("id", uprompt)
    enable_sentiment = q_info.get("enable_sentiment", True)
    q_type = q_info.get("question_type", "")
    
    # For text-based questions
    if q_type in ("Short Answer", "Paragraph"):
        if enable_sentiment:  # ← Only if marked for analysis
            raw_feedback_list.append(str(ans))  # Add to combined feedback
            question_sentiments[q_id] = {
                "text": str(ans),
                "enable_sentiment": True,
                "sentiment": "pending"  # Will be filled by sentiment analysis
            }
        else:  # Not marked for sentiment
            question_sentiments[q_id] = {
                "text": str(ans),
                "enable_sentiment": False,
                "sentiment": None
            }
```

**Impact:**
- First Name/Last Name answers no longer mixed with feedback
- Each question stored independently
- Dashboard can display sentiment per question

---

### 2. `dashboard.py` - Respondent Details Display
**Lines 1295-1320: Per-Question Sentiment Display**

**Key Changes:**
- ✅ Updated to display sentiment per question from `question_sentiments` JSONB
- ✅ Added visual indicator: "🔍 Sentiment: ..." for sentiment-analyzed questions
- ✅ Added visual indicator: "⊘ Not marked for sentiment analysis" for disabled questions
- ✅ Changed from single overall sentiment to individual question-level sentiment

**What it does:**
```python
# Display each question's answer and its individual sentiment
st.write(f"**{question.get('prompt')}**")
st.write(f"📝 {answer}")

# Get sentiment data from question_sentiments JSONB
q_sentiment_data = response.get("question_sentiments", {}).get(q_id, {})

if q_sentiment_data.get("enable_sentiment"):
    sentiment_val = q_sentiment_data.get("sentiment")
    if sentiment_val and sentiment_val != "pending":
        st.caption(f"🔍 Sentiment: **{sentiment_val.upper()}**")
    else:
        st.caption("⏳ Sentiment analysis pending...")
else:
    st.caption(f"⊘ Not marked for sentiment analysis")
```

**Impact:**
- Users see which questions were analyzed vs excluded
- Sentiment clearly attributed to specific question, not entire response
- Clear visual distinction between analyzed and non-analyzed data

---

### 3. `sql/migration_06_per_question_sentiment.sql` - New Database Column
**Complete Migration File**

**What it does:**
```sql
ALTER TABLE public.form_responses
ADD COLUMN IF NOT EXISTS question_sentiments jsonb;

-- JSONB structure:
-- {
--   "q1_uuid": {
--     "text": "User's answer to Q1",
--     "enable_sentiment": true/false,
--     "sentiment": "POSITIVE/NEGATIVE/NEUTRAL/pending/null"
--   },
--   "q2_uuid": { ... }
-- }
```

**Key Features:**
- JSONB allows flexible nested structure
- Can store both the answer text AND metadata (enable_sentiment flag)
- Can store sentiment result per question
- Queryable with SQL `->` operator

**Migration Order:**
Run after migrations 03, 04, 05 in order:
1. migration_03_add_form_meta_unique_constraint.sql
2. migration_04_add_enable_sentiment_to_questions.sql
3. migration_05_track_question_sentiment_settings.sql
4. **migration_06_per_question_sentiment.sql** ← NEW

---

## **Code Location Reference**

| Task | File | Lines | Status |
|------|------|-------|--------|
| Question sentiment toggle | `builder.py` | 714-720, 1078-1085 | ✅ Existing |
| Form submission logic | `public_form.py` | 501-545 | ✅ **UPDATED** |
| Dashboard sentiment display | `dashboard.py` | 1295-1320 | ✅ **UPDATED** |
| Database schema | `sql/migration_06_...sql` | All | ✅ **CREATED** |
| Sentiment analysis engine | `sentiment_analysis.py` | TBD | ⏳ PENDING |

---

## **What Still Needs to be Done**

### Priority 1: Update Sentiment Analysis Script
File: `sentiment_analysis.py`

**Current behavior:** Analyzes combined `raw_feedback` as single input
```python
# OLD - Analyzes "Maria | Jamil | Great service" as ONE input
sentiment = analyze_text(raw_feedback)
```

**Needed behavior:** Analyze each question separately
```python
# NEW - Should analyze each question independently
for q_id, q_data in question_sentiments.items():
    if q_data["enable_sentiment"]:
        sentiment = analyze_text(q_data["text"])  # Just this question's text
        question_sentiments[q_id]["sentiment"] = sentiment
```

**Why this matters:**
- Currently "Maria | Jamil | Sobrang tagal service" gets analyzed as one blob
- Should be: Only "Sobrang tagal service" analyzed for sentiment
- Prevents unrelated names/attributes from affecting sentiment classification

### Priority 2: Test End-to-End
1. Run migration_06 in Supabase
2. Uncheck sentiment toggle for First Name & Last Name in Form Builder
3. Submit test response
4. Check Dashboard → Respondent Details
5. Verify:
   - First Name/Last Name show "⊘ Not marked for sentiment analysis"
   - Feedback questions show sentiment or "⏳ Pending..."

### Priority 3: Model Accuracy (Optional but Recommended)
Current issues:
- "Sobrang tagal" (Very long) → Misclassified as POSITIVE instead of NEGATIVE
- Mixed Tagalog/English not well understood
- Named entity recognition sees "Maria" as positive sentiment

Solutions:
- Fine-tune model on transportation feedback data
- Add Tagalog/Filipino language support
- Pre-process to remove names before sentiment analysis

---

## **Testing Checklist**

### Before Running sentiments_analysis.py
- [ ] Migration 06 executed in Supabase
- [ ] First Name question has sentiment toggle → **UNCHECKED**
- [ ] Last Name question has sentiment toggle → **UNCHECKED**  
- [ ] Feedback questions have sentiment toggle → **CHECKED**
- [ ] Submit test response with all field types

### After Running sentiment_analysis.py (Once Updated)
- [ ] Check Respondent Details tab
- [ ] Verify First Name & Last Name show "⊘ Not marked..."
- [ ] Verify Feedback shows "🔍 Sentiment: POSITIVE/NEGATIVE/NEUTRAL"
- [ ] Verify each question has DIFFERENT sentiment (not all same)

### Database Verification
```sql
-- Check new column exists
SELECT column_name FROM information_schema.columns 
WHERE table_name='form_responses' AND column_name='question_sentiments';

-- Check data structure
SELECT response_id, question_sentiments 
FROM form_responses 
LIMIT 1;

-- Should see structure like:
-- {
--   "uuid-q1": {"text": "Maria", "enable_sentiment": false, "sentiment": null},
--   ...
-- }
```

---

## **Rollback Instructions**

If something goes wrong:

```sql
-- Remove the new column
ALTER TABLE public.form_responses DROP COLUMN question_sentiments;

-- Revert to old form_meta primary key (if needed)
ALTER TABLE public.form_meta 
DROP CONSTRAINT form_meta_pkey;
ALTER TABLE public.form_meta 
ADD PRIMARY KEY (admin_email);
```

---

## **Next Steps**

1. **Immediate:** Run migration_06 in Supabase
2. **Then:** Test form submission with updated settings
3. **Then:** Update sentiment_analysis.py to use question_sentiments structure
4. **Then:** Test end-to-end with dashboard display
5. **Optional:** Address model accuracy for better classifications

Need any help with sentiment_analysis.py update? Let me know!
