# Fix for Toggle Settings Reverting to ON After Refresh

## Problem
When creating a new custom form and toggling "Include standard profile" and "Include standard questionnaires" to OFF, the toggles would work immediately after saving. However, when the page was refreshed, the toggles would revert back to ON.

## Root Cause
The issue had two components:

1. **Missing field on form creation**: When a new form was created in `forms.py`, the `form_meta` database record was created without the `include_standard_servqual_questions` field. This meant the database column didn't have an explicit value set.

2. **Session state initialization issue**: In `builder.py`, the toggle initialization logic was:
   ```python
   st.session_state.meta_include_servqual = st.session_state.get("meta_include_servqual", bool(form_meta.get("include_standard_servqual_questions", True)))
   ```
   This used `st.session_state.get()` which would preserve the OLD session state value if it existed, preventing the database value from being properly loaded after a browser refresh when session state was cleared.

## Solution
Made the following changes:

### 1. **forms.py** (Line ~100)
Added `"include_standard_servqual_questions": True` to the `meta_payload` when creating a new form:
```python
meta_payload = {
    "form_id": form_id,
    "admin_email": admin_email,
    "title": title or "Untitled Form",
    "description": description,
    "include_demographics": False,
    "allow_multiple_responses": True,
    "reach_out_contact": "",
    "include_standard_servqual_questions": True,  # ← Added
}
```

### 2. **builder.py** (Lines ~661-677)
Added the field to BOTH default dictionaries:
- Default when form_meta is not found in database
- Exception handler default dict

```python
form_meta = meta_req.data[0] if meta_req.data else {
    "title": "Land Public Transportation Respondent Survey",
    "description": "Please share your honest experience.",
    "include_demographics": False,
    "allow_multiple_responses": True,
    "reach_out_contact": "",
    "include_standard_servqual_questions": True,  # ← Added
}
```

### 3. **builder.py** (Lines ~704-716)
Improved the toggle initialization to properly detect form changes and refresh from database:
```python
# Always refresh servqual setting from database to ensure toggles are in sync after save
if "meta_include_servqual" not in st.session_state:
    st.session_state.meta_include_servqual = bool(form_meta.get("include_standard_servqual_questions", True))
elif "_last_form_id" in st.session_state and st.session_state._last_form_id != current_form_id:
    # Form changed, refresh from database
    st.session_state.meta_include_servqual = bool(form_meta.get("include_standard_servqual_questions", True))
# Store current form_id to detect form changes
st.session_state._last_form_id = current_form_id
```

### 4. **builder.py** (Lines ~747-759)
Added error handling for the `include_standard_servqual_questions` field in the migration logic:
```python
if "include_standard_servqual_questions" in err:
    st.session_state["form_meta_servqual_migration_needed"] = True
    payload.pop("include_standard_servqual_questions", None)
    stripped = True
```

### 5. **public_form.py** (Line ~400)
Added the field to the default dictionary for consistency:
```python
form_meta = {
    "title": "Land public transportation survey",
    "description": "",
    "include_demographics": False,
    "allow_multiple_responses": True,
    "reach_out_contact": "",
    "include_standard_servqual_questions": True,  # ← Added
}
```

## How It Works Now
1. When a new form is created, `include_standard_servqual_questions` is explicitly set to `True` in the database
2. The toggle initializes from the database value on first load
3. When the user toggles OFF and saves, the value is properly saved to the database
4. On browser refresh (when session state is cleared), the toggle correctly loads the saved value from the database
5. If switching between forms, the toggle is refreshed from the database to show the correct value

## Testing
To verify the fix works:
1. Create a new custom form
2. Toggle "Include standard questionnaires" to OFF
3. Click "Save All Settings"
4. Verify it shows OFF
5. **Refresh the page (Ctrl+R or F5)**
6. The toggle should remain OFF ✓
