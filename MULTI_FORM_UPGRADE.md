# Multi-Form System Upgrade — Implementation Guide

## ✅ Phase 1: Database Schema Changes

### 1.1 Create `form_list` Table
```sql
CREATE TABLE IF NOT EXISTS public.form_list (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  form_id text NOT NULL UNIQUE,
  admin_email text NOT NULL,
  title text NOT NULL DEFAULT 'Untitled Form',
  description text DEFAULT '',
  created_at timestamp WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  is_archived boolean DEFAULT FALSE,
  CONSTRAINT fk_user UNIQUE(admin_email, form_id)
);

CREATE INDEX idx_form_list_admin ON public.form_list(admin_email);
CREATE INDEX idx_form_list_form_id ON public.form_list(form_id);
```

### 1.2 Migrate Existing Data
- Create a form entry for the user's existing form
- Backfill `form_id` into `form_questions`, `form_meta`, `form_responses`
- Update `public_id` to use the new `form_id`

### 1.3 Update Table Schemas
```sql
-- Add form_id columns if they don't exist
ALTER TABLE public.form_questions ADD COLUMN IF NOT EXISTS form_id text;
ALTER TABLE public.form_meta ADD COLUMN IF NOT EXISTS form_id text;
ALTER TABLE public.form_responses ADD COLUMN IF NOT EXISTS form_id text;

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_form_questions_form_id ON public.form_questions(form_id);
CREATE INDEX IF NOT EXISTS idx_form_meta_form_id ON public.form_meta(form_id);
CREATE INDEX IF NOT EXISTS idx_form_responses_form_id ON public.form_responses(form_id);
```

## ✅ Phase 2: Core Python Utilities

### 2.1 Create `forms.py` (New File)
- `generate_form_id()` - Creates unique form ID
- `fetch_all_forms()` - Lists all forms for user
- `get_current_form()` - Gets the active form (from session/param)
- `create_form()` - Creates a new form
- `delete_form()` - Soft-delete a form
- `update_form_meta()` - Updates form metadata

### 2.2 Update Query Functions
Change from:
```python
.eq("admin_email", admin_email)
```

To:
```python
.eq("admin_email", admin_email).eq("form_id", current_form_id)
```

## ✅ Phase 3: Page Updates

### 3.1 `router.py` (Main Entry Point)
- Add form selection dropdown
- Update URL routing to include `form_id` parameter
- Initialize session state for current form

### 3.2 `builder.py` (Form Builder)
- Add form management section at top
  - Create new form button
  - Form dropdown selector
  - Form settings (rename, delete, etc.)
- Update all queries to use current form_id
- Update shareable link to include form_id

### 3.3 `dashboard.py` (Analytics)
- Add form dropdown selector
- Filter all data by current form_id
- Update data fetch functions

### 3.4 `public_form.py` (Public Survey)
- Extract `form_id` from URL parameter
- Fetch questions/meta for specific form_id
- Save responses with form_id

### 3.5 `settings.py` (Admin Settings)
- Add form management section
- Allow users to manage multiple forms
- Archive/delete forms

## ✅ Phase 4: UI/UX Improvements

### 4.1 Navigation
- Add form selector in main navigation
- Show current form name
- Quick access to form creation

### 4.2 Shareable Links
- Update format: `/?form_id={form_id}` (keeping for backwards compatibility, also support just form_id)
- Display form-specific link in builder

## ✅ Phase 5: Testing & Migration

### 5.1 Backward Compatibility
- Support old `public_id` format for existing users
- Auto-create form entry for legacy data

### 5.2 Testing Checklist
- [ ] Create multiple forms
- [ ] Switch between forms
- [ ] Form-specific dashboards
- [ ] Share form links work independently
- [ ] Delete/archive forms
- [ ] Settings per form

## Implementation Order

1. Database schema changes (SQL migrations)
2. Create `forms.py` utility module
3. Update `builder.py` (form management + question builder)
4. Update `dashboard.py` (form selector + filtered data)
5. Update `public_form.py` (form_id parameter support)
6. Update `router.py` (main routing)
7. Update `settings.py` (form admin)
8. Test all flows

---

## File-by-File Changes Summary

| File | Changes |
|------|---------|
| `forms.py` | **NEW** - Form management utilities |
| `builder.py` | Add form selector, form management UI, update queries |
| `dashboard.py` | Add form selector, filter by form_id |
| `public_form.py` | Extract form_id from URL, update queries |
| `router.py` | Add form routing/selection logic |
| `settings.py` | Add form management interface |
| `sql/migration_*.sql` | **NEW** - Multiple migration scripts |

---

## Key Database Queries (Before & After)

### Before (Single Form)
```python
conn.client.table("form_questions").select("*").eq("admin_email", admin_email).order("sort_order").execute()
```

### After (Multi-Form)
```python
conn.client.table("form_questions").select("*").eq("admin_email", admin_email).eq("form_id", current_form_id).order("sort_order").execute()
```

---

## Session State Variables (New)

```python
st.session_state.current_form_id      # Active form UUID
st.session_state.available_forms      # List of forms for user
st.session_state.current_form_name    # Display name of active form
```

---

## URL Parameter Updates

### Public Form Link
- **Old**: `/?form_id={public_id}`
- **New**: `/?form_id={form_id}` (UUID-based)

### Builder/Dashboard
- **New**: Can pass `?form_id={form_id}` to pre-select a form

---

## Migration Path for Existing Users

1. On first login after upgrade:
   - Check if user has questions in `form_questions`
   - If yes, create a legacy form entry
   - Set `form_id` to their current `public_id` (for backward compatibility)
   - Backfill `form_id` into all their data

2. Existing shareable links continue to work
3. Users can then create additional forms as needed
