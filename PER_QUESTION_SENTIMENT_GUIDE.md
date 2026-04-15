# Per-Question Sentiment Analysis - Implementation Guide

## **What Changed**

### BEFORE (Combined Analysis)
```
Response 1:
- Q1 (Last Name): "Mariano"
- Q2 (First Name): "Jamil"
- Q3 (Feedback): "Great service, very helpful"

COMBINED into single analysis:
"Mariano | Jamil | Great service, very helpful" → ONE sentiment = POSITIVE
```

### AFTER (Individual Analysis) ✅
```
Response 1:
- Q1 (Last Name): "Mariano"
  - enable_sentiment: FALSE → NOT ANALYZED
  
- Q2 (First Name): "Jamil"
  - enable_sentiment: FALSE → NOT ANALYZED
  
- Q3 (Feedback): "Great service, very helpful"
  - enable_sentiment: TRUE → ANALYZED SEPARATELY → POSITIVE

Result: Only Q3 analyzed with sentiment = POSITIVE
```

---

## **Database Changes**

### New Table Structure

**Column: `question_sentiments` (JSONB)**
```json
{
  "q1_uuid": {
    "text": "Mariano",
    "enable_sentiment": false,
    "sentiment": null
  },
  "q2_uuid": {
    "text": "Jamil", 
    "enable_sentiment": false,
    "sentiment": null
  },
  "q3_uuid": {
    "text": "Great service, very helpful",
    "enable_sentiment": true,
    "sentiment": "POSITIVE"
  }
}
```

This structure means:
- ✅ Q1 & Q2 NOT included in sentiment analysis (enable_sentiment = false)
- ✅ Q3 analyzed SEPARATELY (enable_sentiment = true)
- ✅ Each question gets its OWN sentiment label
- ✅ If settings change later, we can re-analyze correctly

---

## **Implementation Steps**

### Step 1: Run Database Migration
```sql
-- File: sql/migration_06_per_question_sentiment.sql
-- Run in Supabase → SQL Editor

ALTER TABLE public.form_responses
ADD COLUMN IF NOT EXISTS question_sentiments jsonb;
```

### Step 2: Configure Questions in Form Builder
For **EACH question**, decide:

| Question Type | Should Analyze? | Action |
|---|---|---|
| First Name | ❌ NO | Uncheck "Enable sentiment analysis" |
| Last Name | ❌ NO | Uncheck it |
| Age | ❌ NO | Uncheck it |
| Gender | ❌ NO | Uncheck it |
| "How was the service?" | ✅ YES | **Leave CHECKED** |
| "Any suggestions?" | ✅ YES | **Leave CHECKED** |
| "How frequent do you commute?" | ❌ NO | Uncheck it |

### Step 3: Test with New Responses
1. Submit a test response
2. Check Dashboard → Respondent Details
3. Verify:
   - Last Name/First Name → Shows "⊘ Not marked for sentiment analysis"
   - Feedback questions → Shows "🔍 Sentiment: POSITIVE/NEGATIVE/NEUTRAL"

---

## **What Happens Now**

### Form Submission Flow
```
User fills form:
├─ Q1: "Mariano" → NOT added to sentiment_sentiments (enable_sentiment=false)
├─ Q2: "Jamil" → NOT added to sentiment_sentiments (enable_sentiment=false)  
└─ Q3: "Sobrang tagal waiting" → ADDED with enable_sentiment=true, sentiment=pending

Stored in database:
├─ question_sentiments = {q1: {text: "Mariano", enable_sentiment: false, sentiment: null},
│                         q2: {text: "Jamil", enable_sentiment: false, sentiment: null},
│                         q3: {text: "Sobrang tagal...", enable_sentiment: true, sentiment: "pending"}}
└─ raw_feedback = "Sobrang tagal waiting" (ONLY q3, not q1/q2)
```

### Dashboard Display
**Respondent Details Tab:**
```
Q1: Last Name
Answer: Mariano
⊘ Not marked for sentiment analysis

Q2: First Name
Answer: Jamil
⊘ Not marked for sentiment analysis

Q3: Any problems?
Answer: Sobrang tagal waiting
🔍 Sentiment: NEGATIVE
```

---

## **How Sentiment Analysis Now Works**

### Individual Processing
```python
# EACH question analyzed SEPARATELY
for question_id, q_data in question_sentiments.items():
    if q_data["enable_sentiment"] == true:
        # Analyze ONLY this question's text
        sentiment = analyze_text(q_data["text"])
        question_sentiments[question_id]["sentiment"] = sentiment
```

Benefits:
- ✅ "Sobrang tagal" → Correctly identified as NEGATIVE
- ✅ "Medyo maayos" → Correctly identified as POSITIVE
- ✅ "Mariano" → Not analyzed (it's a name)
- ✅ "Jamil" → Not analyzed (it's a name)

---

## **FAQ**

### Q: What about old responses (before this change)?
**A:** Old responses will still have `raw_feedback` with combined text. They'll show "Pending analysis" or won't display sentiment without `question_sentiments` column. Consider re-processing them once sentiment analysis is updated.

### Q: Can I change settings after responses are saved?
**A:** Yes! Since we now store WHY each field was included/excluded, you can:
1. Change question's `enable_sentiment` setting
2. System will know what was the original setting
3. Can re-analyze responses with new settings

### Q: Why still keep `raw_feedback`?
**A:** For backward compatibility and as a fallback. It contains the combined text used for legacy sentiment analysis.

### Q: How do I disable sentiment for existing questions?
**A:** 
1. Go to Form Builder
2. Click "✏️ Edit" on the question
3. Uncheck "Enable sentiment analysis for this question"
4. Click "💾 Save changes"
5. Future responses for that question won't be analyzed

### Q: What if I want to re-analyze all responses?
**A:** You'll need to:
1. Write a script to loop through all form_responses
2. For each response, extract question_sentiments
3. Re-run sentiment analysis on questions where enable_sentiment=true
4. Update question_sentiments[q_id]["sentiment"] with new result

(I can help write this script if needed)

---

## **Technical Details**

### Data Structure Examples

**Response with Mixed Questions:**
```json
{
  "question_sentiments": {
    "uuid-q1": {
      "text": "Maria",
      "enable_sentiment": false,
      "sentiment": null
    },
    "uuid-q2": {
      "text": "Lopez",
      "enable_sentiment": false,
      "sentiment": null
    },
    "uuid-q3": {
      "text": "Pwede pa mas mabilis service",
      "enable_sentiment": true,
      "sentiment": "NEGATIVE"
    },
    "uuid-q4": {
      "text": "Kuryente ay stable naman",
      "enable_sentiment": true,
      "sentiment": "POSITIVE"
    }
  },
  "raw_feedback": "Pwede pa mas mabilis service | Kuryente ay stable naman"
}
```

### Query Example
```sql
-- Find all responses where Q3 has NEGATIVE sentiment
SELECT response_id, question_sentiments->'uuid-q3' as q3_sentiment
FROM form_responses
WHERE question_sentiments->'uuid-q3'->>'sentiment' = 'NEGATIVE'
AND form_id = 'your-form-id';
```

---

## **Next: Update Sentiment Analysis Script**

Once you confirm this is working, we need to update the sentiment analysis engine to:
1. Read `question_sentiments` column
2. Only process questions where `enable_sentiment = true`
3. Write sentiment labels back to `question_sentiments[q_id]["sentiment"]`
4. NOT use combined `raw_feedback` anymore

Would you like me to update the sentiment analysis script after you test this?
