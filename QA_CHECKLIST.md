# QA checklist — Land public transportation sentiment app

Use a **test account** or disposable data when steps delete or wipe responses. Mark each row **Pass / Fail** and note the build or git commit.

### Demo data (optional)

To fill the **Dashboard** without manual survey submissions, run `scripts/seed_dashboard_demo.py` (see the file docstring). Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`, then e.g. `python scripts/seed_dashboard_demo.py --email YOUR_LOGIN_EMAIL --count 35`. Seeded rows are **enriched** for **Demographics**, **SERVQUAL / Quantitative** (if your form has no Likert), and an extra open-text line for the **Sentiment** feedback log. Remove seeded rows with `--clear`. Open **Form Builder** once first so `form_meta` exists; if you have no questions yet, use `--force-minimal`.

---

## 1. Auth and Settings

| Step | Action | Expected |
|------|--------|----------|
| 1.1 | Open app while logged out | Login page loads; protected pages blocked or redirect to login. |
| 1.2 | Log in with valid credentials | Session holds; researcher pages accessible. |
| 1.3 | **Settings** → confirm tabs | Only **Profile & Security** and **Data Management** (no AI Model Config). |
| 1.4 | **Profile**: update **Full Name**, save | Success message; name persists after refresh. |
| 1.5 | **Profile**: **Sign out** | Session cleared; login required again. |
| 1.6 | Log in; **Change password** (valid, matching fields, ≥6 chars) | Success. |
| 1.7 | **Change password** with mismatch | Error; password unchanged. |
| 1.8 | **Data Management** → **Download Dataset** with no responses | Warning or empty-state message (no crash). |
| 1.9 | With ≥1 response → download CSV | File downloads; columns include identifiers and flattened answers. |
| 1.10 | **Wipe All Survey Responses** (check confirm, then run) | Success; responses gone; form questions still in builder. |

---

## 2. Form Builder and public link

| Step | Action | Expected |
|------|--------|----------|
| 2.1 | Open **Form Builder**; edit title / meta; **Save survey settings** | Success confirmation. |
| 2.2 | Toggle **respondent profile** / preview options | UI updates; preview shows how respondents see the form. |
| 2.3 | Copy **public survey link**; open in incognito / other browser | Form loads without researcher login. |
| 2.4 | Submit with required fields empty | Validation prevents submit or shows errors. |
| 2.5 | Submit complete valid response | Thank-you / confirmation; no server error in UI. |
| 2.6 | If **multiple responses** disabled: submit twice from same session | Second behavior matches your product rule (blocked or allowed as designed). |

---

## 3. Dashboard

| Step | Action | Expected |
|------|--------|----------|
| 3.1 | After new submission, open **Dashboard** | New row appears with plausible timestamp. |
| 3.2 | **Sentiment** on open-ended feedback | POSITIVE / NEUTRAL / NEGATIVE (or empty if no text) consistent with content. |
| 3.3 | Date filters / charts | No Python errors; charts match filtered slice. |
| 3.4 | Export actions (if any) | Files download; names and columns look correct. |

---

## 4. Analysis

| Step | Action | Expected |
|------|--------|----------|
| 4.1 | **Try one comment** — English | Label + confidence; distribution sums sensibly. |
| 4.2 | **Try one comment** — Tagalog or mixed | No crash; output appears. |
| 4.3 | **Upload a file** — CSV with `feedback` column | Batch runs; preview table; download annotated CSV. |
| 4.4 | CSV **without** `feedback` column | Clear error message. |
| 4.5 | **Our model vs baselines** while **logged out** | Warning to log in. |
| 4.6 | Logged in: set date range, pick a **baseline**, **Run comparison** | Metrics + match summary grid; optional disagreement table. |
| 4.7 | Run comparison twice with different baselines | Results change per baseline; no crash. |
| 4.8 | Reload **Dashboard** after comparison | Stored sentiment **unchanged** (comparison is read-only for stored labels). |

---

## 5. Cross-cutting

| Step | Action | Expected |
|------|--------|----------|
| 5.1 | Hard refresh (Ctrl+F5) on main pages | Layout and auth state behave correctly. |
| 5.2 | Narrow window / mobile width | Settings tabs scroll; main pages usable. |
| 5.3 | Check Streamlit / server logs during the run | No unhandled tracebacks for the steps above. |
| 5.4 | Supabase unavailable or wrong keys (staging only) | User-visible error, not a blank success. |

---

## Sign-off

- **Tester:** _______________  
- **Date:** _______________  
- **Environment:** _______________ (e.g. local / Streamlit Cloud / URL)  
- **Commit or version:** _______________  

**Notes (failures, screenshots, log excerpts):**

```




```
