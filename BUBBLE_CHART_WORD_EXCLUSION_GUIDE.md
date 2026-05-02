# Bubble Chart Word Exclusion Feature

## Overview
The **Word Exclusion Filter** allows researchers to exclude specific words from appearing in the "Commuter Insights: What Words Describe What?" bubble chart visualization. This helps focus analysis on meaningful insights by filtering out generic, repetitive, or irrelevant terms.

---

## 📊 Where to Use It

**Location:** Settings → 📊 Dashboard Settings

**Affects:** The bubble chart in the Dashboard, specifically the visualization titled **"Commuter Insights: What Words Describe What?"**

---

## 💡 Why Would You Use This?

### 1. **Remove Generic Filler Words**
   - Words like "thing", "stuff", "ok", "very", "just" often don't add analytical value
   - These words appear frequently but don't describe service quality meaningfully
   - Filtering them out makes the chart cleaner and more focused

### 2. **Eliminate Brand-Specific Noise**
   - Company names, system names, or internal jargon that don't reflect actual service feedback
   - Example: If your survey is about "Land Public Transport", exclude "land" to focus on actual feedback

### 3. **Reduce Redundancy**
   - Sometimes multiple forms of the same word appear (e.g., "clean", "clean", "cleaning")
   - Filter out duplicates or less meaningful variants to highlight core themes

### 4. **Focus on Service Dimensions**
   - SERVQUAL dimensions include: Tangibles, Reliability, Responsiveness, Assurance, Empathy
   - Remove words that don't meaningfully describe these dimensions

### 5. **Improve Stakeholder Presentations**
   - Cleaner visualizations are easier to present to non-technical audiences
   - Removes "noise" that might distract from key insights

---

## 🎯 How to Use It

### Step 1: Navigate to Dashboard Settings
1. Go to **Settings** page (⚙️)
2. Click on the **"📊 Dashboard Settings"** tab

### Step 2: Select a Form
- Choose which form you want to configure from the dropdown
- Each form can have its own unique word exclusion list

### Step 3: Add Words to Exclude
1. In the text area labeled **"Enter words to exclude (one per line)"**, type each word on a separate line
2. Examples:
   ```
   thing
   stuff
   ok
   very
   just
   land
   transport
   ```

### Step 4: Review Your List
- The system shows a preview of words to be excluded
- No duplicates are allowed (automatically removed)
- All words are converted to lowercase for matching

### Step 5: Save Changes
- Click **"💾 Save Exclusion List"**
- You'll see a confirmation message with the number of excluded words
- The changes take effect immediately on the next dashboard page reload

### Step 6: Clear (Optional)
- To remove all exclusions, click **"🔄 Clear All"**
- This will restore all words to the bubble chart

---

## 📝 Important Notes

### Case Insensitivity
- Words are matched regardless of case
- "Thing", "THING", and "thing" will all be excluded
- You only need to type lowercase words

### One Word Per Line
- Each word must be on a separate line
- The system automatically trims whitespace

### Minimum Word Length
- Only words with 3 or more letters are shown in the bubble chart anyway
- Shorter words are already filtered by the algorithm
- Exclusion works on top of this existing filter

### Duplicate Removal
- If you accidentally add the same word twice, it's automatically removed
- The system keeps order and removes duplicates while preserving your list order

### No Impact on Raw Data
- Excluded words are **NOT** removed from your actual data
- Only the bubble chart visualization is affected
- Your export data and other analyses remain complete

### Changes Apply Only to This Form
- Each form has its own independent exclusion list
- Excluding words in Form A doesn't affect Form B

---

## 🔍 How It Works Behind the Scenes

### Word Extraction Process
1. System extracts all words with 3+ letters from open-ended responses
2. Built-in stopwords (English & Filipino) are automatically removed
3. **Your excluded words** are added to this stopword list
4. Remaining words are counted and displayed as bubbles

### Exclusion List Storage
- Your word exclusion list is stored in the `form_meta` table
- Format: JSON array (e.g., `["thing", "stuff", "ok"]`)
- Saved per form for maximum flexibility

### When Words Are Filtered
- **✅ During dashboard visualization** – excluded words don't appear in the bubble chart
- **✅ During word sentiment calculation** – excluded words aren't counted
- **❌ NOT during export** – full raw data is exported with all words intact

---

## 🎓 Example Scenario

### Scenario: Land Public Transport Survey

**Initial Bubble Chart shows:**
- "thing" (45 mentions) ❌ Generic, not useful
- "stuff" (32 mentions) ❌ Vague filler word
- "land" (28 mentions) ❌ Just repeating system name
- "transport" (25 mentions) ❌ Repeating form topic
- "clean" (18 mentions) ✅ Tangibles dimension
- "fast" (16 mentions) ✅ Reliability dimension
- "friendly" (14 mentions) ✅ Empathy dimension

**After Excluding "thing", "stuff", "land", "transport":**
- "clean" (18 mentions) ✅ Now more prominent
- "fast" (16 mentions) ✅ Now more prominent
- "friendly" (14 mentions) ✅ Now more prominent
- Plus other meaningful words become visible

**Result:** Cleaner, more focused insights that better represent actual service feedback

---

## 💻 Technical Details

### Database Storage
- Field: `form_meta.excluded_bubble_words`
- Type: JSONB array
- Example value: `["thing", "stuff", "ok", "very"]`

### Code Implementation
- **Settings:** `settings.py` – UI for managing exclusions
- **Filter Logic:** `dashboard.py` – `extract_word_insights()` function
- **Storage:** Supabase `form_meta` table

### How to Reset
- Individual form: Use **"🔄 Clear All"** button in Dashboard Settings
- Full reset: Delete the `excluded_bubble_words` field via database

---

## ⚠️ Common Mistakes to Avoid

❌ **Mistake:** Excluding too many words and losing insights
- ✅ **Solution:** Start with 5-10 common filler words, then adjust

❌ **Mistake:** Excluding dimension-related words (clean, fast, friendly)
- ✅ **Solution:** Only exclude generic/filler words, not service quality descriptors

❌ **Mistake:** Expecting exclusion to affect CSV exports
- ✅ **Solution:** Remember that raw data exports include all words (feature doesn't modify your source data)

❌ **Mistake:** Forgetting one word per line
- ✅ **Solution:** Use line breaks, not commas or spaces

---

## 🔄 Workflow Tips

### Iterative Refinement
1. **Review** the bubble chart and identify problematic words
2. **Add** those words to your exclusion list
3. **Reload** the dashboard to see the changes
4. **Adjust** if needed (add more or remove from list)

### Form-Specific Optimization
- Each survey form gets its own optimized exclusion list
- Different forms may need different exclusions
- Customize per research context

### Collaboration
- If multiple researchers use the account, coordinate on the exclusion list
- Share best practices for which words to exclude

---

## 📞 Need Help?

- **Words not being excluded?** Check if they're actually appearing in responses (words need 3+ letters)
- **Want to undo changes?** Click "Clear All" or just remove specific words
- **Data concerns?** Remember: Raw data is never modified, only visualization is affected

---

## ✅ Summary Checklist

- [ ] Understand which words are generic/filler in your context
- [ ] Go to Settings → Dashboard Settings
- [ ] Select your form
- [ ] Add words one per line
- [ ] Preview the exclusion list
- [ ] Click "Save"
- [ ] Reload the dashboard to see changes
- [ ] Refine your list as needed

---

**Last Updated:** May 2, 2026  
**Feature:** Bubble Chart Word Exclusion Filter v1.0
