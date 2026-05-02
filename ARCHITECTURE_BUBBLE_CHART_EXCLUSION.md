# Bubble Chart Word Exclusion - System Architecture

## 🏗️ Feature Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Settings Page (⚙️)                                              │
│  └─ Tab 3: "📊 Dashboard Settings"                              │
│     ├─ Form Selector Dropdown                                   │
│     ├─ Text Area: "Enter words to exclude"                      │
│     ├─ Preview: Show selected words                             │
│     ├─ Button: "💾 Save Exclusion List"                         │
│     └─ Button: "🔄 Clear All"                                   │
│                                                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ (User clicks Save)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SUPABASE DATABASE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  form_meta Table                                                │
│  ├─ form_id (PK)                                               │
│  ├─ admin_email (FK)                                           │
│  ├─ title                                                       │
│  ├─ ...other fields...                                         │
│  └─ excluded_bubble_words ← JSON: ["thing", "stuff", "ok"]    │
│                                                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ (Dashboard page loads)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  DASHBOARD PROCESSING                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Fetch form_meta.excluded_bubble_words                       │
│  2. Pass to extract_word_insights(excluded_words)               │
│  3. Convert to lowercase & parse JSON if needed                 │
│  4. Add to Built-in Stopwords Set                              │
│                                                                   │
│     STOPWORDS = load_combined_stopwords()                       │
│     + English stopwords (the, and, etc)                         │
│     + Filipino stopwords (ang, sa, etc)                         │
│     + Custom stopwords (if configured)                          │
│     + USER EXCLUDED WORDS ← NEW! ⭐                            │
│                                                                   │
│  5. Process Responses:                                          │
│     For each response → extract words → filter by STOPWORDS    │
│     (words in STOPWORDS are skipped)                            │
│                                                                   │
│  6. Count remaining words → Generate word insights             │
│                                                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BUBBLE CHART DISPLAY                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  "Commuter Insights: What Words Describe What?"                 │
│                                                                   │
│  [Visualization]                                                │
│  ● clean (18x)      ← Included (not excluded)                  │
│  ● fast (16x)       ← Included (not excluded)                  │
│  ● friendly (14x)   ← Included (not excluded)                  │
│                                                                   │
│  Excluded from display:                                         │
│  ✗ thing (would be 45x)                                        │
│  ✗ stuff (would be 32x)                                        │
│  ✗ ok (would be 22x)                                           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
Response Data                Settings Configuration
        │                            │
        │                            ▼
        │                    ┌─────────────────┐
        │                    │  Word Exclusion │
        │                    │  ["thing",      │
        │                    │   "stuff", ...]│
        │                    └────────┬────────┘
        │                             │
        ▼                             ▼
   ┌─────────────────────────────────────┐
   │  extract_word_insights()            │
   │  ├─ Load built-in stopwords         │
   │  ├─ Merge excluded words            │
   │  └─ Filter responses                │
   └──────────────┬──────────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────────┐
   │  Word Extraction & Counting         │
   │  Only keeps words NOT in STOPWORDS  │
   └──────────────┬──────────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────────┐
   │  Sentiment Analysis                 │
   │  Group by dimension & sentiment     │
   └──────────────┬──────────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────────┐
   │  Bubble Chart Generation            │
   │  SVG bubbles sized by word count    │
   └──────────────┬──────────────────────┘
                  │
                  ▼
         📊 Bubble Chart
```

---

## 🗂️ File Relationships

```
settings.py
├─ UI for word exclusion (Tab 3)
├─ Reads form_meta
├─ Writes to form_meta.excluded_bubble_words
└─ Calls Supabase to save

     │
     └──→ Supabase form_meta Table
          └─ excluded_bubble_words (JSONB)

dashboard.py
├─ Reads form_meta.excluded_bubble_words
├─ Passes to extract_word_insights()
├─ extract_word_insights() 
│  ├─ Loads excluded_words
│  ├─ Merges with STOPWORDS
│  └─ Filters response text
└─ Generates bubble chart

     │
     └──→ Supabase form_meta Table
          ├─ form_id
          ├─ excluded_bubble_words
          └─ other metadata
```

---

## 📊 Function Call Sequence

```
1. render_word_insights()
   ↓
2. Fetch form_meta from Supabase
   ├─ SELECT excluded_bubble_words
   └─ WHERE form_id = X AND admin_email = Y
   ↓
3. extract_word_insights(
     df_sent, 
     sent_col, 
     q_text_to_id, 
     form_schema, 
     form_schema_full,
     excluded_words ← NEW PARAMETER
   )
   ↓
4. Inside extract_word_insights():
   ├─ Load built-in stopwords
   ├─ Parse excluded_words (JSON string → list)
   ├─ Add excluded_words to stopwords set
   ├─ For each response:
   │  ├─ Extract all words
   │  ├─ Filter: only keep if NOT in stopwords
   │  └─ Count remaining words
   └─ Return dimension_insights, bubble_resp_map
   ↓
5. build_svg_bubble_chart()
   ├─ Uses dimension_insights (already filtered)
   └─ Renders SVG visualization
   ↓
6. Display bubble chart
```

---

## 💾 Database Schema

```sql
-- form_meta table structure (relevant columns)
CREATE TABLE form_meta (
    form_id TEXT PRIMARY KEY,
    admin_email TEXT NOT NULL,
    title TEXT,
    description TEXT,
    is_sample_form BOOLEAN,
    include_demographics BOOLEAN,
    enable_sentiment BOOLEAN,
    include_standard_servqual_questions BOOLEAN,
    
    -- NEW COLUMN ⭐
    excluded_bubble_words JSONB DEFAULT '[]'::jsonb,
    
    -- Other fields...
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Example data
INSERT INTO form_meta (form_id, admin_email, excluded_bubble_words)
VALUES (
    'form_123',
    'researcher@example.com',
    '["thing", "stuff", "ok", "very", "just"]'
);
```

---

## 🔐 Access Control

```
User Authentication
    ↓
    ├─ Settings page: Check admin_email in URL/session
    ├─ Form selection: Only show forms for current admin_email
    └─ Save operation: Only update form_meta where admin_email matches

     This ensures:
     ✅ Users can only manage their own forms
     ✅ Users cannot see other users' forms
     ✅ Data isolation per researcher
```

---

## 🎯 Use Case Flow

```
Researcher has a form with 500 responses

Step 1: Review Bubble Chart
        → Notices "thing", "stuff", "ok" are noise
        
Step 2: Go to Settings
        → Dashboard Settings tab
        
Step 3: Add Exclusions
        → Type "thing"
        → Type "stuff"
        → Type "ok"
        
Step 4: Save
        → Data saved to form_meta
        
Step 5: Reload Dashboard
        → extract_word_insights() gets excluded_words
        → Those words filtered out
        → Bubble chart shows cleaner results

Result: Better insights focused on meaningful service quality feedback
```

---

## 🚀 Performance Considerations

- **One-time merge:** Excluded words merged with stopwords once per dashboard load
- **No database queries per word:** Filtering happens in Python, not SQL
- **Efficient set operations:** Python set intersection/union is O(n)
- **Cached stopwords:** Built-in stopwords loaded once
- **Typical exclusion list:** 5-20 words (minimal overhead)

**Performance Impact:** Negligible (~1ms added per chart render)

---

## ✅ Testing Checklist

- [ ] Can add words to exclusion list in Settings
- [ ] Words saved to form_meta correctly
- [ ] Excluded words don't appear in bubble chart
- [ ] Non-excluded words still display
- [ ] Can clear all exclusions with one click
- [ ] Different forms have independent lists
- [ ] Case-insensitive matching works
- [ ] JSON parsing handles edge cases
- [ ] Export data still includes all words
- [ ] Reload dashboard applies filters

---

**Last Updated:** May 2, 2026  
**Version:** 1.0
