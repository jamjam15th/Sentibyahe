# Multi-Form System Implementation Guide

## 🎯 Quick Start (5-10 minutes)

### Step 1: Run Database Migrations

1. Open **Supabase** → **SQL Editor**
2. Copy and run **each** migration script in order:
   - [`sql/migration_01_create_form_list.sql`](sql/migration_01_create_form_list.sql)
   - [`sql/migration_02_backfill_legacy_forms.sql`](sql/migration_02_backfill_legacy_forms.sql)

3. Wait for each to complete (you'll see "Query successful")

### Step 2: Update Code

Your codebase has been updated with:
- ✅ New `forms.py` utility module
- ✅ Updated `builder.py` with form management UI
- ✅ Updated `dashboard.py` with form selector
- ✅ Updated `public_form.py` for multi-form support

**No additional code changes needed!** The system automatically handles migration.

### Step 3: Test It

1. Log in to your application
2. Go to **Form Builder** (🛠️)
3. You'll see a new section: **📋 Forms & Surveys**
4. Your existing survey is now listed
5. Click **➕ Create New Form** to add more surveys

---

## 🔄 What Changed?

### Before (Single-Form)
```
Database:
├── form_questions (all questions for one user)
├── form_meta (title, description)
└── form_responses (all responses)

URL: /?form_id={public_id} (derived from email)
```

### After (Multi-Form)
```
Database:
├── form_list (tracks all forms per user) ← NEW
├── form_questions (all questions, grouped by form_id)
├── form_meta (metadata per form)
└── form_responses (responses per form)

URL: /?form_id={form_id} (UUID-based)
```

---

## 🎯 New Features

### Form Management
- **Create multiple forms** - Click "➕ Create New Form" in the builder
- **Switch between forms** - Use the dropdown selector in builder & dashboard
- **Manage forms** - Click "⚙️ Manage Forms" to see all your surveys
- **Archive forms** - Soft-delete forms without losing data
- **Unique shareable links** - Each form has its own link

### User Experience
- Form selector in **Form Builder** 💾
- Form selector in **Sentiment Dashboard** 📊
- Each form has independent:
  - Questions
  - Form settings (title, description, allow multiple responses, etc.)
  - Responses and analytics
  - Shareable link

---

## 📊 Backward Compatibility

**Existing surveys are preserved!**

When you first log in after the upgrade:
1. Your existing survey is automatically migrated
2. All historical data is preserved
3. Your current shareable link **may change** (see note below)
4. Your form appears in the "Select a form" dropdown

**Note on URLs:** 
- Old links using your email-derived ID work during the migration period
- New forms get UUID-based IDs
- Eventually, your legacy form ID will be fully replaced

---

## 🚀 Usage Examples

### Creating a New Form

1. Go to "Form Builder" 🛠️
2. Click **➕ Create New Form**
3. Enter form title (e.g., "Q4 Commuter Satisfaction")
4. Click **Create**
5. You're now editing the new form
6. Add questions as usual
7. Share the unique link for this form

### Switching Between Forms

**In Form Builder:**
- Select a form from the dropdown under "📋 Forms & Surveys"
- All questions and settings change to that form

**In Dashboard:**
- Select a form from the "📋 View dashboard for" dropdown
- Analytics switch to show data for that form

### Viewing All Forms

1. Go to Form Builder
2. Click **⚙️ Manage Forms**
3. See all active forms with response counts
4. Archive forms you no longer use

---

## ⚙️ Database Schema

### `form_list` Table (New)
Tracks all forms per user:
```sql
form_id         text        -- Unique form identifier (UUID)
admin_email     text        -- Form owner
title           text        -- Form name
description     text        -- Form description
created_at      timestamp   -- Creation date
updated_at      timestamp   -- Last modified
is_archived     boolean     -- Soft-delete flag
```

### Updated Tables
- **`form_questions`**: Added `form_id` column
- **`form_meta`**: Added `form_id` column  
- **`form_responses`**: Added `form_id` column

---

## 🛡️ FAQ

### Can I still access my old survey?
**Yes!** Your existing survey is automatically preserved and migrated. It appears as your first form.

### What happens to my shareable links?
Your old links may need to be updated. The new system uses `?form_id={form_id}` where `form_id` is a UUID. See "Upgrade Path" section for details.

### Can I delete a form?
Yes, use **⚙️ Manage Forms** → **Archive** to soft-delete. This preserves all historical data. Archived forms don't appear in your main form selector but you can restore them if needed.

### Will my historical data be lost?
**No!** All existing responses are preserved. Your dashboard continues to show all historical data, now organized by form.

### Do respondents need to know about the change?
**No!** The public survey form works the same way. Just generate new shareable links for new forms.

### Can I have forms with the same title?
Yes, each form has a unique `form_id` internally, so you can have multiple forms with similar names.

---

## 🔧 Custom Configuration

### For Developers

The `forms.py` utility module provides:
```python
from forms import (
    generate_form_id,           # Create new form ID
    fetch_all_forms(email),     # List all forms
    create_form(email, title),  # Create new form
    get_form(form_id, email),   # Get specific form
    archive_form(form_id, email),  # Archive a form
    migrate_legacy_user(email),    # Auto-migrate old User
)
```

### Session State Variables
```python
st.session_state.current_form_id    # Active form (UUID)
st.session_state.available_forms    # List of user's forms
```

---

## 📈 Upgrade Benefits

| Feature | Before | After |
|---------|--------|-------|
| Surveys per user | 1 | Unlimited ✅ |
| Independent responses | N/A | Per form ✅ |
| Separate dashboards | No | Yes ✅ |
| Shareable links | 1 | Per form ✅ |
| Form archival | No | Yes ✅ |
| Historical data | Single timeline | Organized by form ✅ |

---

## ⚠️ Troubleshooting

### "No forms found. Create one below."
- This shouldn't happen, but if it does, click **➕ Create New Form** to create your first form.

### Shareable link returns "Invalid survey link"
- Make sure the `form_id` in the URL matches a form you own
- Generate a new link from the Form Builder

### Form data appears empty  
- Verify you're on the correct form (check the dropdown selector)
- Data is organized per form after the migration

### Responses not showing in dashboard
- Ensure you've selected the correct form in the dashboard form selector
- New responses for the new form appear in the dashboard immediately

---

## 🎓 Next Steps

1. ✅ **Run database migrations** (Step 1 above)
2. ✅ **Test creating a new form** in the builder
3. ✅ **Share a form link** with someone
4. ✅ **View responses** in the dashboard
5. 🎉 **Enjoy unlimited forms!**

---

## 📞 Support

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Verify all SQL migrations completed successfully
3. Clear browser cache and refresh
4. Check your Supabase logs in the dashboard

---

## 📝 Files Modified

| File | Changes |
|------|---------|
| `forms.py` | **NEW**: Form management utilities |
| `builder.py` | Form selector, create/manage UI, form_id filtering |
| `dashboard.py` | Form selector, form_id filtering in data fetches |
| `public_form.py` | Multi-form support, form_id handling |
| `sql/migration_01_*.sql` | **NEW**: Create form_list table |
| `sql/migration_02_*.sql` | **NEW**: Backfill data, create indexes |

---

## ✨ What's Next? (Optional Enhancements)

Future improvements you can add:
- [ ] Form templates (save common questions as templates)
- [ ] Form duplication (clone an existing form)
- [ ] Batch operations (delete multiple forms)
- [ ] Export all forms as ZIP
- [ ] Form versioning/history

---

Last updated: April 2026
Migration supported: Streamlit + Supabase
