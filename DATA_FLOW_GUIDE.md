# Data Flow: Per-Question Sentiment Analysis

## **Visual Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│   RESPONDENT FILLS FORM (public_form.py)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │ Question Processing (Loop through Q&A) │
         └────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │    Q1       │     │    Q2       │     │    Q3       │
    │ Last Name   │     │ First Name  │     │ Feedback    │
    │ "Mariano"   │     │ "Jamil"     │     │ "Sobrang    │
    └─────────────┘     └─────────────┘     │ tagal"      │
         │                   │               └─────────────┘
         │                   │                   │
    enable_sentiment?    enable_sentiment?   enable_sentiment?
    FALSE           ×     FALSE           ×     TRUE            ✓
         │                   │                   │
         ▼                   ▼                   ▼
  Excluded from        Excluded from       ADDED TO SENTIMENT
  raw_feedback.        raw_feedback.       ANALYSIS
  
  Still stored in      Still stored in     Added to both:
  question_sentiments  question_sentiments - raw_feedback
  with:               with:               - question_sentiments
  - text              - text              
  - enable_sentiment  - enable_sentiment  With:
  - sentiment: null   - sentiment: null   - text
                                          - enable_sentiment
                                          - sentiment: "pending"
         │                   │                   │
         └───────────────────┴───────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │  FORM SUBMISSION (public_form.py)      │
         │  Lines 501-545                         │
         └────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
   raw_feedback                          question_sentiments
   (Text only from                        (Full metadata)
    enabled questions)
   
   "Sobrang tagal"                    {
                                        "uuid-q1": {
                                          "text": "Mariano",
                                          "enable_sentiment": false,
                                          "sentiment": null
                                        },
                                        "uuid-q2": {
                                          "text": "Jamil",
                                          "enable_sentiment": false,
                                          "sentiment": null
                                        },
                                        "uuid-q3": {
                                          "text": "Sobrang tagal",
                                          "enable_sentiment": true,
                                          "sentiment": "pending"
                                        }
                                      }
        │                                           │
        └─────────────────────┬─────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │  DATABASE STORAGE (form_responses)     │
         │  raw_feedback + question_sentiments    │
         └────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │  SENTIMENT ANALYSIS (TBD)              │
         │  sentiment_analysis.py                 │
         └────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
   OLD: Analyzes combined          NEW: Should analyze
   "Mariano | Jamil |             SEPARATELY:
    Sobrang tagal"
                                   uuid-q3 text:
   Problem: Names affect            "Sobrang tagal"
   sentiment!                        ↓
                                   Sentiment = NEGATIVE ✓
        │                                           │
        └─────────────────────┬─────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │  UPDATE question_sentiments            │
         │  Set sentiment: "POSITIVE/NEGATIVE..."  │
         └────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │  DASHBOARD DISPLAY (dashboard.py)      │
         │  Lines 1295-1320                       │
         └────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                                           ▼
   Questions without                  Questions WITH
   sentiment analysis:                sentiment analysis:
   
   Q1: Last Name                      Q3: Feedback
   📝 Mariano                         📝 Sobrang tagal
   ⊘ Not marked for                  🔍 Sentiment: NEGATIVE ✓
     sentiment analysis
   
   Q2: First Name
   📝 Jamil
   ⊘ Not marked for
     sentiment analysis
```

---

## **Key Points in the Flow**

### Step 1: Decision Point (enable_sentiment flag)
```
For EACH question:
  IF enable_sentiment == true:
    → Include in raw_feedback
    → Include in question_sentiments
    → Mark for sentiment analysis
  ELSE:
    → Exclude from raw_feedback  
    → Still store text in question_sentiments
    → Mark as NOT for sentiment analysis
```

### Step 2: Database Storage
```
Stored as TWO fields:

raw_feedback (String):
  "Sobrang tagal"  ← Only enabled questions

question_sentiments (JSONB):
  {
    "q1": {..., sentiment: null},      ← Not analyzed
    "q2": {..., sentiment: null},      ← Not analyzed  
    "q3": {..., sentiment: "pending"}  ← Will be analyzed
  }
```

### Step 3: Sentiment Analysis (Currently Missing)
```
Should process:
  FOR EACH question_id, question_data IN question_sentiments:
    IF question_data["enable_sentiment"] == true:
      sentiment = analyze(question_data["text"])
      question_sentiments[question_id]["sentiment"] = sentiment
    ELSE:
      question_sentiments[question_id]["sentiment"] = null
```

### Step 4: Dashboard Display
```
For each question:
  Display answer text
  
  IF enable_sentiment == true AND sentiment != pending:
    Show emoji + sentiment label
  ELSE IF enable_sentiment == true AND sentiment == pending:
    Show waiting indicator
  ELSE:
    Show "Not marked for sentiment analysis"
```

---

## **Data Example: Complete Journey**

### Step 1: Form Response Submitted
```
User inputs:
  Last Name: "Mariano"
  First Name: "Jamil"  
  Feedback: "Sobrang tagal ang waiting, staff not helpful"
```

### Step 2: public_form.py Processes
```python
question_sentiments = {
  "q1_uuid": {
    "text": "Mariano",
    "enable_sentiment": false,     # ← Unchecked in builder
    "sentiment": null
  },
  "q2_uuid": {
    "text": "Jamil",
    "enable_sentiment": false,     # ← Unchecked in builder
    "sentiment": null
  },
  "q3_uuid": {
    "text": "Sobrang tagal ang waiting, staff not helpful",
    "enable_sentiment": true,      # ← Checked in builder  
    "sentiment": "pending"
  }
}

raw_feedback = "Sobrang tagal ang waiting, staff not helpful"
# NOTE: No "Mariano | Jamil |" prefix!
```

### Step 3: Database Stores
```sql
INSERT INTO form_responses (
  response_id, form_id, admin_email, 
  raw_feedback, question_sentiments
) VALUES (
  'resp123', 'form456', 'admin@example.com',
  'Sobrang tagal ang waiting, staff not helpful',
  {
    "q1_uuid": {"text": "Mariano", "enable_sentiment": false, "sentiment": null},
    "q2_uuid": {"text": "Jamil", "enable_sentiment": false, "sentiment": null},
    "q3_uuid": {"text": "Sobrang tagal...", "enable_sentiment": true, "sentiment": "pending"}
  }
);
```

### Step 4: Sentiment Analysis (NEEDS UPDATE)
```python
# Should do this for each question:
for q_id in ["q1_uuid", "q2_uuid", "q3_uuid"]:
  q_data = question_sentiments[q_id]
  
  if q_data["enable_sentiment"]:  # Only for enabled
    text = q_data["text"]
    sentiment = model.analyze(text)
    question_sentiments[q_id]["sentiment"] = sentiment
  # else: leave sentiment as null

# Result:
question_sentiments = {
  "q1_uuid": {..., sentiment: null},           # Not analyzed
  "q2_uuid": {..., sentiment: null},           # Not analyzed
  "q3_uuid": {..., sentiment: "NEGATIVE"}      # Analyzed! ✓
};
```

### Step 5: Dashboard Displays
```
Q1: Last Name
📝 Mariano
⊘ Not marked for sentiment analysis

Q2: First Name  
📝 Jamil
⊘ Not marked for sentiment analysis

Q3: Feedback
📝 Sobrang tagal ang waiting, staff not helpful
🔍 Sentiment: NEGATIVE ✓
```

---

## **What Happens vs What Should Happen**

| Aspect | OLD (Before Changes) | NEW (After Changes) | BETTER (After sentiment_analysis.py update) |
|--------|---|---|---|
| Input to sentiment | "Mariano\|Jamil\|Sobrang tagal..." | Stored separately per question | Analyzed separately per question |
| Names included? | YES → affects sentiment ❌ | NO → stored but not analyzed ✓ | NO → not analyzed ✓ |
| Sentiment result | One label for all text | Pending in question_sentiments | One label PER question ✓ |
| Dashboard shows | Overall sentiment | Pending (waiting for analysis) | Per-question sentiment ✓ |

---

## **Files Involved in This Flow**

| Stage | File | Lines | Responsibility |
|-------|------|-------|-----------------|
| Form Submission | public_form.py | 501-545 | Build question_sentiments JSON |
| Database | migration_06.sql | All | Store question_sentiments column |
| Sentiment Analysis | sentiment_analysis.py | TBD | Process question_sentiments |
| Display | dashboard.py | 1295-1320 | Show per-question sentiment |

---

## **Why This Structure Works**

1. **Flexible:** Can re-analyze with different settings without losing original data
2. **Traceable:** Know which questions were analyzed vs excluded at submission time
3. **Separate:** Each question's sentiment independent from others
4. **Queryable:** SQL queries can filter by sentiment: `WHERE question_sentiments->'q3'->>'sentiment' = 'NEGATIVE'`
5. **Fallback:** Still have raw_feedback for backward compatibility

---

## **Testing This Flow**

```bash
# 1. Run migration
# 2. Fill form with:
#    - Last Name (sentiment OFF)
#    - First Name (sentiment OFF)
#    - Feedback (sentiment ON)
# 3. Check database:
SELECT question_sentiments FROM form_responses LIMIT 1;
# Should see above structure

# 4. Check dashboard:
# After sentiment analysis updates, should show individual sentiments per question
```

All clear? Ready to update sentiment_analysis.py next?
