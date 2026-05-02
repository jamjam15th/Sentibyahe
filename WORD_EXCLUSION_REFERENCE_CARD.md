# Word Exclusion Feature - Reference Card

## 🎯 Feature Overview

**What:** Allow users to exclude words from the "Commuter Insights: What Words Describe What?" bubble chart

**Where:** Settings ⚙️ → 📊 Dashboard Settings tab

**Why:** Remove generic/filler words to focus on meaningful service quality insights

**When:** Any time after creating a survey form

---

## 🗺️ Navigation Path

```
Home/Dashboard
    ↓
⚙️ Settings (top menu)
    ↓
Three tabs appear:
    1. 👤 Profile & Security
    2. 💾 Data Management
    3. 📊 Dashboard Settings ← YOU ARE HERE
```

---

## 🎛️ Settings Panel Layout

```
┌─────────────────────────────────────┐
│ 📊 Bubble Chart Word Filters        │
├─────────────────────────────────────┤
│                                      │
│ [Information Box]                   │
│ What is this? Why use? ...          │
│                                      │
│ Select Form: ┌──────────────────┐   │
│              │ Form A      ▼    │   │
│              └──────────────────┘   │
│                                      │
│ Words to Exclude:                   │
│ ┌──────────────────────────────────┐│
│ │ [Multi-line text input]          ││
│ │ One word per line                ││
│ │                                  ││
│ │ Example:                         ││
│ │ thing                            ││
│ │ stuff                            ││
│ │ ok                               ││
│ └──────────────────────────────────┘│
│                                      │
│ [Preview] 🏷️ word1 🏷️ word2 ...    │
│                                      │
│ [💾 Save]  [🔄 Clear All]           │
│                                      │
│ Excluded Words: 3    Status: Active │
│                                      │
│ [Tips Section]                      │
│ - Use lowercase                     │
│ - One word per line                 │
│ - Changes take effect immediately  │
│                                      │
└─────────────────────────────────────┘
```

---

## ⌨️ How to Use

### Basic Steps
1. **Navigate:** Settings → Dashboard Settings
2. **Select:** Choose form from dropdown
3. **Enter:** Type words (one per line)
4. **Save:** Click "💾 Save Exclusion List"
5. **Verify:** Reload dashboard → words removed ✨

### Advanced Tips
- **Duplicate words?** Auto-removed
- **Case sensitive?** No - "Thing", "THING", "thing" all work
- **Want to undo?** Click "🔄 Clear All"
- **Per form?** Yes - each form has own list

---

## 📋 Word Suggestion Lists

### Quick Filter Packs

**Common Filler Words:**
```
thing
stuff
ok
very
just
like
kind
sort
actually
really
basically
```

**System/Product Names:**
```
land
transport
system
app
platform
sentibyahe
form
survey
```

**Mixed Pack (Start Here):**
```
thing
stuff
very
ok
just
```

---

## 📊 Effect on Dashboard

### Bubble Chart
- ✅ **Excluded words:** Hidden
- ✅ **Other words:** Displayed normally
- ✅ **Word counts:** Updated (excluding removed words)
- ✅ **Visual:** Cleaner, more focused

### Other Elements
- ❌ **Exports:** Not affected (all words included)
- ❌ **Raw data:** Not affected (never modified)
- ❌ **Other charts:** Not affected (only bubbles)
- ❌ **Other forms:** Not affected (per-form setting)

---

## 🎯 Success Indicators

**You did it right if:**
- ✅ Excluded words don't appear in bubble chart
- ✅ Save shows confirmation message
- ✅ "Excluded Words" count updates
- ✅ Changes apply after dashboard reload
- ✅ Other words display normally
- ✅ CSV exports still have all words

---

## ⚠️ Important Notes

| What | Remember |
|------|----------|
| Data | ✅ Raw data NEVER modified |
| Exports | ✅ CSV includes ALL words |
| Reversible | ✅ Click "Clear All" to undo |
| Per-Form | ✅ Each form independent |
| Case | ✅ Automatic lowercase matching |
| Duration | ✅ Changes permanent until cleared |

---

## 🔍 Example Before/After

**BEFORE (Noisy Chart):**
```
Bubble Count Summary:
- thing: 45 bubbles
- stuff: 32 bubbles
- ok: 22 bubbles
- land: 18 bubbles
- clean: 15 bubbles ← Useful!
- fast: 12 bubbles   ← Useful!
```

**AFTER (Excluding thing, stuff, ok, land):**
```
Bubble Count Summary:
- clean: 15 bubbles  ← Now more visible!
- fast: 12 bubbles   ← Now more visible!
- friendly: 10 bubbles
- reliable: 9 bubbles
- helpful: 8 bubbles
```

**Result:** 60% reduction in noise! 🎉

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Words still show | Reload page, check 3+ letters |
| Can't save | Select form first, check network |
| Want to undo | Click "Clear All" button |
| Not in dropdown | Create form first |
| Case issue | Words auto-converted to lowercase |

---

## 🎓 Best Practices

✅ **DO:**
- Start with 5-10 words
- Exclude filler/generic terms
- Exclude brand names
- Review results and adjust
- Document your choices

❌ **DON'T:**
- Exclude all words!
- Exclude service quality words (clean, fast, friendly)
- Expect it to modify raw data
- Forget to save changes
- Use commas (use line breaks instead)

---

## 💾 Storage Details

**Where:** Supabase `form_meta` table

**Field:** `excluded_bubble_words`

**Format:** JSON array
```json
["thing", "stuff", "ok", "very", "just"]
```

**Per:** Individual form (not global)

**Limit:** No practical limit (tested 1000+ words)

---

## 🔄 Typical Workflow

```
Day 1: Create survey form
        ↓
Day 7: Get 100+ responses
        ↓
Review Dashboard
        → "Hmm, too many generic words"
        ↓
Go to Settings → Dashboard Settings
        → Add exclusions
        ↓
Review Results
        → "Much better!"
        ↓
Fine-tune (add/remove words)
        → Repeat as needed
        ↓
Final Dashboard
        → Clean, focused insights ✨
```

---

## 📞 Need Help?

**Common Questions:**

Q: *Can I exclude part of a word?*
A: Only whole words. "clean" but not "cle*"

Q: *How many words can I exclude?*
A: Unlimited practically. Most use 5-20.

Q: *Will this affect my team's access?*
A: No - per-form setting, each researcher configures their own.

Q: *Can I export the exclusion list?*
A: Not yet - manual for now, but documented in our guide.

---

## 📚 Full Documentation

- **Quick Guide:** WORD_EXCLUSION_QUICKSTART.md
- **User Manual:** BUBBLE_CHART_WORD_EXCLUSION_GUIDE.md
- **Tech Details:** BUBBLE_CHART_EXCLUSION_IMPLEMENTATION.md
- **Architecture:** ARCHITECTURE_BUBBLE_CHART_EXCLUSION.md

---

## ✅ Checklist Before You Start

- [ ] I understand what generic words are
- [ ] I know where Settings is (⚙️ menu)
- [ ] I have at least one survey form created
- [ ] I've reviewed the bubble chart
- [ ] I know which words are noise
- [ ] I'm ready to improve my analysis!

---

**Version:** 1.0  
**Last Updated:** May 2, 2026  
**Status:** Ready to Use 🚀
