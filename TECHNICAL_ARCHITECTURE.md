# Multi-Form System — Technical Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         STREAMLIT FRONTEND                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  builder.py  │  │ dashboard.py │  │public_form.py│            │
│  │ (Form Edit)  │  │(Analytics)   │  │  (Survey)    │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│         │                │                  │                     │
└─────────┼────────────────┼──────────────────┼─────────────────────┘
          │                │                  │
          └────────────────┼──────────────────┘
                           │
                    ┌──────▼───────┐
                    │  forms.py    │  ← All form operations
                    │ (Utilities)  │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
┌─────────▼──────┐ ┌──────▼──────┐ ┌───────▼──────┐
│   Streamlit    │ │  Supabase   │ │   Database   │
│ Session State  │ │ Connection  │ │  (PostgreSQL)│
└────────────────┘ └─────────────┘ └──────────────┘
                           │
                    ┌──────▼───────────┐
                    │  form_list       │ (tracks all forms)
                    │  form_questions  │ (form_id filtering)
                    │  form_meta       │ (form_id filtering)
                    │  form_responses  │ (form_id filtering)
                    └──────────────────┘
```

## Data Flow

### Creating a New Form

```
User clicks "Create New Form"
    │
    ├──> Dialog opens for form title
    │
    ├──> forms.create_form()
    │    - Generates unique form_id (UUID)
    │    - Inserts into form_list
    │    - Links to admin_email
    │
    └──> refresh_form_list()
         - Updates session state
         - Sets current_form_id
         - Shows new form in dropdown
```

### Saving a Question

```
User enters question & clicks "Save"
    │
    ├──> forms.get_current_form_id()
    │    - Returns form_id from session state
    │
    ├──> Database INSERT into form_questions
    │    {
    │      form_id: "abc123...",    ← Links to form
    │      admin_email: "user@...",
    │      prompt: "Your question",
    │      q_type: "Multiple Choice",
    │      ...
    │    }
    │
    └──> UI updates to show new question
```

### Loading Dashboard

```
User selects form in dashboard
    │
    ├──> set_current_form(form_id)
    │    - Updates session state
    │
    ├──> fetch_dashboard_data(email, form_id)
    │    - Queries form_responses WHERE form_id = ? AND admin_email = ?
    │    - Only loads data for selected form
    │
    └──> Display analytics for that form only
```

### Public Survey Submission

```
Respondent accesses: /?form_id={form_id}
    │
    ├──> Lookup form in form_list using form_id
    │    - Get owner_email from form
    │
    ├──> Load questions from form_questions
    │    WHERE form_id = ? AND admin_email = owner_email
    │
    ├──> Load metadata from form_meta
    │    WHERE form_id = ?
    │
    ├──> Respondent submits →
    │
    └──> INSERT into form_responses
         {
           form_id: "...",              ← Links response to form
           admin_email: owner_email,
           answers: {...},
           ...
         }
```

## Module Architecture

### 1. `forms.py` — Core Utilities

**Session State Management:**
```python
init_form_session_state(admin_email)
    # Initialize or load from query params:
    # - current_form_id
    # - available_forms

get_current_form_id()        # Returns form_id
set_current_form(form_id)    # Updates session
refresh_form_list(email)     # Reload available forms
```

**Form Operations:**
```python
fetch_active_forms(email)              # Get all non-archived forms
create_form(email, title, desc)        # Create new form
get_form(form_id, email)               # Get specific form (ownership checked)
update_form(form_id, email, **updates) # Modify form metadata
archive_form(form_id, email)           # Soft-delete
delete_form_permanently(form_id, email) # Hard-delete
```

**Legacy Support:**
```python
migrate_legacy_user(email)             # Auto-migrate old users
get_legacy_form_id(email)              # Derive old form_id from email
ensure_form_exists(email, form_id)     # Ensure form exists or create
```

### 2. `builder.py` — Form Builder

**Key Changes:**
- Import `forms` module utilities
- Initialize form session state on load
- Add form selector dropdown (top of page)
- Add "Create New Form" button
- Add "Manage Forms" dialog
- Update all queries to use `form_id`

**Query Pattern:**
```python
# Before
q_res = conn.client.table("form_questions").select("*").eq("admin_email", admin_email).execute()

# After
q_res = conn.client.table("form_questions").select("*").eq("admin_email", admin_email).eq("form_id", current_form_id).execute()
```

### 3. `dashboard.py` — Analytics

**Key Changes:**
- Import `forms` module utilities
- Initialize form session state on load
- Add form selector dropdown in header
- Update fetch functions to accept `form_id` parameter

**Query Pattern:**
```python
# Before
@st.cache_data(ttl=5)
def fetch_dashboard_data(email: str) -> pd.DataFrame:
    r = conn.client.table("form_responses").select("*").eq("admin_email", email).execute()

# After
@st.cache_data(ttl=5)
def fetch_dashboard_data(email: str, form_id: str) -> pd.DataFrame:
    r = conn.client.table("form_responses").select("*").eq("admin_email", email).eq("form_id", form_id).execute()
```

### 4. `public_form.py` — Public Survey

**Key Changes:**
- Extract `form_id` from URL query params
- Lookup form owner via `form_list` table
- Load questions and metadata using `form_id`
- Save responses with both `form_id` and `admin_email`

**Flow:**
```python
# Get form_id from URL
form_id = st.query_params.get("form_id")

# Lookup form owner
form = get_form(form_id, admin_email=None)  # Public access
owner_email = form['admin_email']

# Load questions for this form
questions = fetch_questions(admin_email=owner_email, form_id=form_id)

# Save response with form_id
response_data = {
    'form_id': form_id,
    'admin_email': owner_email,
    'answers': {...},
    ...
}
```

## Database Schema Changes

### New Table: `form_list`

```sql
CREATE TABLE public.form_list (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id text NOT NULL UNIQUE,           -- Unique identifier (UUID)
    admin_email text NOT NULL,              -- Form owner
    title text NOT NULL DEFAULT 'Untitled',
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    is_archived boolean DEFAULT FALSE,      -- Soft-delete
    CONSTRAINT unique_user_form UNIQUE(admin_email, form_id)
);
```

**Indexes:**
```sql
CREATE INDEX idx_form_list_admin ON public.form_list(admin_email);
CREATE INDEX idx_form_list_form_id ON public.form_list(form_id);
CREATE INDEX idx_form_list_admin_active ON public.form_list(admin_email, is_archived);
```

### Modified Tables

**`form_questions`:**
```sql
ALTER TABLE public.form_questions ADD COLUMN form_id text;
CREATE INDEX idx_form_questions_form_id ON public.form_questions(form_id);
CREATE INDEX idx_form_questions_admin_form ON public.form_questions(admin_email, form_id);
```

**`form_meta`:**
```sql
ALTER TABLE public.form_meta ADD COLUMN form_id text;
CREATE INDEX idx_form_meta_form_id ON public.form_meta(form_id);
CREATE INDEX idx_form_meta_admin_form ON public.form_meta(admin_email, form_id);
```

**`form_responses`:**
```sql
ALTER TABLE public.form_responses ADD COLUMN form_id text;
CREATE INDEX idx_form_responses_form_id ON public.form_responses(form_id);
CREATE INDEX idx_form_responses_admin_form ON public.form_responses(admin_email, form_id);
```

## Session State Variables

```python
st.session_state.current_form_id
    # Type: str (UUID)
    # Set: init_form_session_state(), set_current_form()
    # Used: All pages to filter by form

st.session_state.available_forms
    # Type: list[dict]
    # Fields: [{'form_id', 'title', 'description', 'created_at', ...}]
    # Updated: refresh_form_list()
    # Used: Form dropdown selectors

st.session_state.editing_id
st.session_state.preview_mode
    # Existing state, unchanged
```

## URL Parameters

### Public Survey Link
```
/?form_id={form_id}

Examples:
- /?form_id=abc123def456
- http://localhost:8501/?form_id=xyz789
```

### Builder/Dashboard (Optional)
```
/builder?form_id={form_id}

Examples:
- Deep-link to specific form
- Default: Uses first active form if not specified
```

## Query Ownership Verification

All queries verify user ownership:

```python
# Pattern 1: Get user's forms
forms = fetch_active_forms(admin_email)
    # WHERE admin_email = ?

# Pattern 2: Access specific form
form = get_form(form_id, admin_email)
    # WHERE form_id = ? AND admin_email = ?

# Pattern 3: Query data for form
questions = conn.client.table("form_questions") \
    .select("*") \
    .eq("admin_email", admin_email) \
    .eq("form_id", form_id) \
    .execute()
    # WHERE admin_email = ? AND form_id = ?
```

**Security:**
- User email comes from `st.session_state.user_email` (authenticated)
- All queries filter by both `admin_email` and `form_id`
- Form ownership verified before operations
- Public survey access only via form lookup

## Backward Compatibility

### Legacy Form ID
```python
# Before: form_id = md5(email)[:12]
legacy_form_id = get_legacy_form_id(admin_email)

# After: form_id = UUID
new_form_id = generate_form_id()
```

### Migration Path
```
Old User (Single Form)
    ├─ Check for existing form_questions with admin_email
    ├─ Create form_list entry with legacy_form_id
    ├─ Backfill form_id into all existing tables
    └─ Preserve all historical data

    Result: User has one form with their legacy form_id
            Can create additional forms with UUID form_ids
```

### URL Compatibility
```
Old: /?form_id={legacy_public_id}
New: /?form_id={uuid_form_id} or /?form_id={legacy_public_id}

Both work during transition period
```

## Performance Considerations

### Caching
- `@st.cache_data(ttl=5)` for fetch_dashboard_data → keyed by (email, form_id)
- `@st.cache_data(ttl=120)` for fetch_question_scale_map → keyed by (email, form_id)
- Cache invalidation happens when form_id changes

### Indexes
- `(admin_email, form_id)` composite indexes for common queries
- `form_id` index for public form lookups
- `(admin_email, is_archived)` for active form queries

### Query Optimization
```sql
-- Good (uses composite index)
SELECT * FROM form_questions
WHERE admin_email = ? AND form_id = ?

-- Not ideal (full table scan)
SELECT * FROM form_questions
WHERE form_id = ?
```

## Error Handling

### Missing Form
```python
try:
    form = get_form(form_id, admin_email)
    if not form:
        st.error("Form not found")
except Exception as e:
    st.error(f"Error loading form: {e}")
```

### Access Denied
```python
form = get_form(form_id, admin_email)
if not form:
    # User doesn't own this form
    st.error("Access denied")
```

## Future Enhancements

### Potential Features
1. **Form Templates** - Save/reuse question sets
2. **Form Versioning** - Track question changes
3. **Form Collaboration** - Share editing with other users
4. **Bulk Operations** - Delete/archive multiple forms
5. **Form Import/Export** - JSON/CSV form definitions
6. **Advanced Permissions** - View-only, edit-only roles

### Implementation Hooks
```python
# New functions would go in forms.py:
- duplicate_form(form_id, admin_email)
- export_form(form_id, admin_email, format='json')
- import_form(admin_email, import_data)
- share_form(form_id, admin_email, shared_with_email, permission='view')
```

---

## Deployment Checklist

- [ ] Database migrations applied (both SQL files)
- [ ] `forms.py` deployed to project
- [ ] `builder.py`, `dashboard.py`, `public_form.py` updated
- [ ] Test creating new form
- [ ] Test switching between forms
- [ ] Test shareable links work
- [ ] Test dashboard filtering
- [ ] Verify historical data preserved
- [ ] Monitor for errors in logs

---

**Document Version:** 1.0  
**Last Updated:** April 2026  
**System:** Streamlit + Supabase PostgreSQL
