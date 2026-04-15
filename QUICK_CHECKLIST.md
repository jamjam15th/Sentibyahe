# Quick Implementation Checklist

## **Phase 1: Database Setup** ⏳

- [ ] Open Supabase → SQL Editor
- [ ] Copy contents from: `sql/migration_06_per_question_sentiment.sql`
- [ ] Paste into SQL Editor
- [ ] Click "Run"
- [ ] Verify success (no errors)

**Verification Query:**
```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name='form_responses' AND column_name='question_sentiments';
```
Should return: `question_sentiments` exists

---

## **Phase 2: Configure Questions** ⚙️

Go to Form Builder and for each form:

### Questions to UNCHECK sentiment:
- [ ] First Name
- [ ] Last Name
- [ ] Age
- [ ] Gender
- [ ] Occupation
- [ ] Frequency of commute
- [ ] Transport modes
- [ ] Any other demographics

Steps for each question:
1. Click "✏️ Edit" button next to question
2. **UNCHECK** "Enable sentiment analysis for this question"
3. Click "💾 Save changes"

### Questions to KEEP CHECKED:
- [x] Feedback/Comment questions (usually already checked)
- [x] "Any suggestions?" or similar open-ended questions
- [x] Service quality feedback questions
- [x] Any question you want sentiment analysis for

---

## **Phase 3: Test Form Submission** 🧪

1. [ ] Go to your public form URL
2. [ ] Fill out form with test data:
   - First Name: "Test First" (SHOULD NOT be analyzed)
   - Last Name: "Test Last" (SHOULD NOT be analyzed)
   - Feedback: "Great service" (SHOULD be analyzed)
3. [ ] Submit form
4. [ ] ✅ No errors should occur

---

## **Phase 4: Verify Dashboard Display** 📊

1. [ ] Log in to dashboard
2. [ ] Select your form
3. [ ] Go to "👤 Respondent Details" tab
4. [ ] Click on latest response
5. [ ] Verify display shows:

```
✓ First Name: "Test First" + "⊘ Not marked for sentiment analysis"
✓ Last Name: "Test Last" + "⊘ Not marked for sentiment analysis"  
✓ Feedback: "Great service" + "⏳ Sentiment analysis pending..."
```

If you see this, **Phase 4 is COMPLETE** ✅

---

## **Phase 5: Update Sentiment Analysis Script** 🤖

**Status:** This needs to be done next

File to update: `sentiment_analysis.py`

What needs to change:
- [ ] Instead of analyzing `raw_feedback` string
- [ ] Loop through `question_sentiments` dictionary
- [ ] For each question where `enable_sentiment = true`
- [ ] Analyze just that question's text
- [ ] Store result in `question_sentiments[q_id]["sentiment"]`

**Will write this in next step** (just let me know when Phase 4 is working)

---

## **Phase 6: Test Sentiment Analysis** 🎯

Once phase 5 is done:

1. [ ] Run sentiment analysis script
2. [ ] Check dashboard again
3. [ ] Should now show:

```
First Name: "Test First"
⊘ Not marked for sentiment analysis

Last Name: "Test Last"  
⊘ Not marked for sentiment analysis

Feedback: "Great service"
🔍 Sentiment: POSITIVE  ✅
```

---

## **Troubleshooting**

### ❌ Migration fails
**Error:** "column already exists"
→ Column was already added, can safely ignore

**Error:** "syntax error near migration_06"
→ Copy-paste the SQL file content again, check for special characters

### ❌ Form submission shows error
**Error:** "Key error: 'question_sentiments'"
→ Old question_sentiments column doesn't exist yet, run migration first

### ❌ Dashboard shows "⏳ Sentiment analysis pending..." even after running script
→ Sentiment analysis script hasn't been updated yet (Phase 5 not done)

### ❌ First Name still shows sentiment when it shouldn't
**Steps to fix:**
1. Go to Form Builder
2. Edit that question to UNCHECK sentiment toggle
3. Submit NEW response (old ones won't be reanalyzed automatically)

---

## **Quick Reference: Sentiment Toggle Locations**

### Form Builder Settings
- **File:** `builder.py`
- **Lines:** 714-720 (Create mode), 1078-1085 (Edit mode)
- **What it does:** Shows checkbox "Enable sentiment analysis for this question"
- **Users interact:** Check/uncheck for each question type

### Public Form Submission
- **File:** `public_form.py`  
- **Lines:** 501-545
- **What it does:** Builds `question_sentiments` JSON with enable_sentiment flag
- **Status:** ✅ Already updated

### Dashboard Display  
- **File:** `dashboard.py`
- **Lines:** 1295-1320
- **What it does:** Shows "⊘ Not marked..." or "🔍 Sentiment: ..." based on flag
- **Status:** ✅ Already updated

### Sentiment Analysis Engine
- **File:** `sentiment_analysis.py`
- **Lines:** TBD
- **What it does:** Analyzes text and fills in sentiment values
- **Status:** ⏳ NEEDS UPDATE

---

## **Success Criteria**

✅ **You'll know it's working when:**
1. Form submission doesn't error
2. Dashboard shows individual questions with different sentiments
3. Demographic fields show "⊘ Not marked for sentiment analysis"
4. Feedback fields show actual sentiment (POSITIVE/NEGATIVE/NEUTRAL)
5. Different responses have different sentiments for same question

❌ **It's NOT working if:**
- All demographic fields show sentiment (means they're being analyzed)
- All responses show same sentiment (means combined analysis still happening)
- No "⊘ Not marked..." indicators (means toggle isn't being saved)
- Errors when submitting form (migration not applied)

---

## **Questions Before Starting?**

Re-read these for context:
- `PER_QUESTION_SENTIMENT_GUIDE.md` - Implementation guide  
- `CHANGES_SUMMARY.md` - What changed where
- `DATA_FLOW_GUIDE.md` - Visual flow of data

**Ready?** Start with Phase 1! 🚀

Let me know when you finish each phase and I can help with the next one!
