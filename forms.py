# forms.py — Multi-form management utilities
import uuid
import hashlib
import streamlit as st
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# ══════════════════════════════════════════
# FORM ID GENERATION
# ══════════════════════════════════════════
def generate_form_id() -> str:
    """Generate a unique form ID using UUID."""
    return str(uuid.uuid4())[:12]

def get_legacy_form_id(admin_email: str) -> str:
    """
    For backward compatibility, derive a form_id from admin_email
    This is used to migrate existing single-form users.
    """
    return hashlib.md5(admin_email.encode()).hexdigest()[:12]


# ══════════════════════════════════════════
# SUPABASE CONNECTION HELPER
# ══════════════════════════════════════════
def get_supabase_client():
    """Get Supabase connection."""
    return st.connection("supabase", type=SupabaseConnection)


# ══════════════════════════════════════════
# FORM LIST OPERATIONS
# ══════════════════════════════════════════
def fetch_all_forms(admin_email: str) -> list:
    """Fetch all forms for a user (including archived)."""
    try:
        conn = get_supabase_client()
        result = (conn.client.table("form_list")
                  .select("*")
                  .eq("admin_email", admin_email)
                  .order("created_at", desc=True)
                  .execute())
        return result.data or []
    except Exception as e:
        st.warning(f"Could not fetch forms: {e}")
        return []


def fetch_active_forms(admin_email: str) -> list:
    """Fetch active (non-archived) forms for a user."""
    try:
        conn = get_supabase_client()
        result = (conn.client.table("form_list")
                  .select("*")
                  .eq("admin_email", admin_email)
                  .eq("is_archived", False)
                  .order("created_at", desc=True)
                  .execute())
        return result.data or []
    except Exception as e:
        st.warning(f"Could not fetch forms: {e}")
        return []


def create_form(admin_email: str, title: str = "Untitled Form", description: str = "") -> dict | None:
    """Create a new form for the user."""
    try:
        conn = get_supabase_client()
        form_id = generate_form_id()
        
        payload = {
            "form_id": form_id,
            "admin_email": admin_email,
            "title": title or "Untitled Form",
            "description": description,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_archived": False,
        }
        
        result = conn.client.table("form_list").insert(payload).execute()
        form = result.data[0] if result.data else None
        
        # Also create form_meta entry so public link works immediately
        if form:
            meta_payload = {
                "form_id": form_id,
                "admin_email": admin_email,
                "title": title or "Untitled Form",
                "description": description,
                "include_demographics": False,
                "allow_multiple_responses": True,
                "reach_out_contact": "",
            }
            try:
                conn.client.table("form_meta").upsert(meta_payload, on_conflict="admin_email,form_id").execute()
            except Exception as meta_e:
                # Log but don't fail the form creation if meta fails
                st.warning(f"Could not create form metadata: {meta_e}")
        
        return form
    except Exception as e:
        st.error(f"Could not create form: {e}")
        return None


def get_form(form_id: str, admin_email: str) -> dict | None:
    """Get a specific form (ownership verified via admin_email)."""
    try:
        conn = get_supabase_client()
        result = (conn.client.table("form_list")
                  .select("*")
                  .eq("form_id", form_id)
                  .eq("admin_email", admin_email)
                  .limit(1)
                  .execute())
        return result.data[0] if result.data else None
    except Exception:
        return None


def update_form(form_id: str, admin_email: str, **updates) -> bool:
    """Update form metadata (title, description, etc.)."""
    try:
        conn = get_supabase_client()
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        conn.client.table("form_list").update(updates).eq("form_id", form_id).eq("admin_email", admin_email).execute()
        return True
    except Exception as e:
        st.error(f"Could not update form: {e}")
        return False


def archive_form(form_id: str, admin_email: str) -> bool:
    """Archive (soft-delete) a form."""
    try:
        conn = get_supabase_client()
        conn.client.table("form_list").update({"is_archived": True}).eq("form_id", form_id).eq("admin_email", admin_email).execute()
        return True
    except Exception as e:
        st.error(f"Could not archive form: {e}")
        return False


def restore_form(form_id: str, admin_email: str) -> bool:
    """Restore an archived form."""
    try:
        conn = get_supabase_client()
        conn.client.table("form_list").update({"is_archived": False}).eq("form_id", form_id).eq("admin_email", admin_email).execute()
        return True
    except Exception as e:
        st.error(f"Could not restore form: {e}")
        return False


def delete_form_permanently(form_id: str, admin_email: str) -> bool:
    """
    Permanently delete a form and all its data.
    WARNING: This is irreversible.
    """
    try:
        conn = get_supabase_client()
        
        # Delete in order: responses → questions → metadata → form
        conn.client.table("form_responses").delete().eq("form_id", form_id).eq("admin_email", admin_email).execute()
        conn.client.table("form_questions").delete().eq("form_id", form_id).eq("admin_email", admin_email).execute()
        conn.client.table("form_meta").delete().eq("form_id", form_id).eq("admin_email", admin_email).execute()
        conn.client.table("form_list").delete().eq("form_id", form_id).eq("admin_email", admin_email).execute()
        
        return True
    except Exception as e:
        st.error(f"Could not delete form: {e}")
        return False


# ══════════════════════════════════════════
# SESSION STATE MANAGEMENT
# ══════════════════════════════════════════
def init_form_session_state(admin_email: str):
    """Initialize form-related session state variables."""
    if "current_form_id" not in st.session_state:
        # Try to get form_id from URL query params
        form_id_param = st.query_params.get("form_id")
        
        if form_id_param:
            # Verify ownership
            form = get_form(form_id_param, admin_email)
            if form:
                st.session_state.current_form_id = form_id_param
            else:
                # Invalid form, fall back to first active form
                forms = fetch_active_forms(admin_email)
                st.session_state.current_form_id = forms[0]["form_id"] if forms else None
        else:
            # No form_id param, use first active form
            forms = fetch_active_forms(admin_email)
            st.session_state.current_form_id = forms[0]["form_id"] if forms else None
    
    # Always refresh available_forms on each page load
    st.session_state.available_forms = fetch_active_forms(admin_email)


def get_current_form_id() -> str | None:
    """Get the current active form ID from session state."""
    return st.session_state.get("current_form_id")


def set_current_form(form_id: str):
    """Set the current active form in session state."""
    st.session_state.current_form_id = form_id
    # Clear form metadata from session state so new form loads fresh
    st.session_state.pop("meta_title", None)
    st.session_state.pop("meta_desc", None)
    st.session_state.pop("meta_form_name", None)
    st.session_state.pop("meta_reach_out", None)


def refresh_form_list(admin_email: str):
    """Refresh the list of available forms in session state."""
    st.session_state.available_forms = fetch_active_forms(admin_email)


# ══════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════
def check_user_has_forms(admin_email: str) -> bool:
    """Check if user has at least one form."""
    forms = fetch_active_forms(admin_email)
    return len(forms) > 0


def get_form_count(admin_email: str) -> int:
    """Get total number of active forms for user."""
    forms = fetch_active_forms(admin_email)
    return len(forms)


def get_form_response_count(form_id: str, admin_email: str) -> int:
    """Get the number of responses for a specific form."""
    try:
        conn = get_supabase_client()
        result = (conn.client.table("form_responses")
                  .select("id", count="exact")
                  .eq("form_id", form_id)
                  .eq("admin_email", admin_email)
                  .execute())
        return result.count if hasattr(result, "count") else 0
    except Exception:
        return 0


def ensure_form_exists(admin_email: str, form_id: str = None) -> str:
    """
    Ensure a form exists for the user.
    If form_id is provided, verify it exists and belongs to user.
    If not, create a new form.
    Returns the form_id to use.
    """
    if form_id:
        form = get_form(form_id, admin_email)
        if form:
            return form_id
    
    # Check if user has any forms
    forms = fetch_active_forms(admin_email)
    if forms:
        return forms[0]["form_id"]
    
    # Create default form
    new_form = create_form(admin_email, "My First Form")
    return new_form["form_id"] if new_form else None


# ══════════════════════════════════════════
# MIGRATION HELPERS (for backward compatibility)
# ══════════════════════════════════════════
def migrate_legacy_user(admin_email: str) -> str:
    """
    Migrate a single-form user to multi-form system.
    Creates a form entry using their legacy form_id.
    Returns the legacy form_id.
    """
    legacy_form_id = get_legacy_form_id(admin_email)
    
    # Check if already migrated
    form = get_form(legacy_form_id, admin_email)
    if form:
        return legacy_form_id
    
    # Create legacy form entry
    try:
        conn = get_supabase_client()
        payload = {
            "form_id": legacy_form_id,
            "admin_email": admin_email,
            "title": "Land Public Transportation Respondent Survey",
            "description": "Your original survey (migrated from single-form system)",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_archived": False,
        }
        conn.client.table("form_list").insert(payload).execute()
        
        # Backfill form_id into existing data
        conn.client.table("form_questions").update({"form_id": legacy_form_id}).eq("admin_email", admin_email).is_("form_id", "null").execute()
        conn.client.table("form_meta").update({"form_id": legacy_form_id}).eq("admin_email", admin_email).is_("form_id", "null").execute()
        conn.client.table("form_responses").update({"form_id": legacy_form_id}).eq("admin_email", admin_email).is_("form_id", "null").execute()
        
        return legacy_form_id
    except Exception as e:
        st.warning(f"Migration note: {e}")
        return legacy_form_id


def create_sample_form_for_new_user(admin_email: str) -> dict | None:
    """
    Create a default sample form with SERVQUAL questions for new users.
    This is called automatically upon account creation.
    """
    try:
        conn = get_supabase_client()
        
        # Step 1: Create the form
        form = create_form(
            admin_email,
            title="Land Public Transportation Feedback Form",
            description="Please share your experience with public transportation services."
        )
        
        if not form:
            return None
        
        form_id = form.get("form_id")
        
        # Step 2: Create form metadata
        meta_payload = {
            "admin_email": admin_email,
            "form_id": form_id,
            "title": "Land Public Transportation Feedback Form",
            "description": "Please share your experience with public transportation services.",
            "include_demographics": True,  # Enable standard demographics
            "allow_multiple_responses": True,
            "reach_out_contact": "",
        }
        conn.client.table("form_meta").upsert(meta_payload, on_conflict="admin_email,form_id").execute()
        
        # Step 3: Create default questions covering all 5 SERVQUAL dimensions
        questions = [
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How would you rate your overall experience?",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "scale_max": 5,
                "scale_label_low": "Very Unsatisfied",
                "scale_label_high": "Very Satisfied",
                "servqual_dimension": None,
                "sort_order": 1,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How would you rate the cleanliness of the vehicle?",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "scale_max": 5,
                "scale_label_low": "Very Dirty",
                "scale_label_high": "Very Clean",
                "servqual_dimension": "Tangibles",
                "sort_order": 2,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How reliable was the schedule/timeliness?",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "scale_max": 5,
                "scale_label_low": "Very Unreliable",
                "scale_label_high": "Very Reliable",
                "servqual_dimension": "Reliability",
                "sort_order": 3,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How responsive was the driver to your needs?",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "scale_max": 5,
                "scale_label_low": "Not Responsive",
                "scale_label_high": "Very Responsive",
                "servqual_dimension": "Responsiveness",
                "sort_order": 4,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How safe did you feel during the trip?",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "scale_max": 5,
                "scale_label_low": "Very Unsafe",
                "scale_label_high": "Very Safe",
                "servqual_dimension": "Assurance",
                "sort_order": 5,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How courteous was the driver?",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "scale_max": 5,
                "scale_label_low": "Very Rude",
                "scale_label_high": "Very Courteous",
                "servqual_dimension": "Empathy",
                "sort_order": 6,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "What transport mode did you use?",
                "q_type": "Multiple Choice",
                "options": ["Bus", "Jeepney", "Tricycle", "E-trike", "Train (MRT/LRT)", "TNVS (Grab, etc.)", "Other"],
                "is_required": True,
                "is_demographic": True,
                "enable_sentiment": False,
                "servqual_dimension": None,
                "sort_order": 7,
            },
            # Open-ended questions with SERVQUAL dimensions for detailed feedback
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "Tell us about the vehicle condition and facilities (cleanliness, comfort, etc.)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": False,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Tangibles",
                "sort_order": 8,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How would you describe your experience with schedule reliability and wait times?",
                "q_type": "Paragraph",
                "options": [],
                "is_required": False,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Reliability",
                "sort_order": 9,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "What could the driver or staff do to better address your needs?",
                "q_type": "Paragraph",
                "options": [],
                "is_required": False,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Responsiveness",
                "sort_order": 10,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How safe do you feel using this service? Any safety concerns?",
                "q_type": "Paragraph",
                "options": [],
                "is_required": False,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Assurance",
                "sort_order": 11,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "Tell us about your experience with the politeness and helpfulness of staff or driver.",
                "q_type": "Paragraph",
                "options": [],
                "is_required": False,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Empathy",
                "sort_order": 12,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "Any other comments or suggestions?",
                "q_type": "Paragraph",
                "options": [],
                "is_required": False,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": None,
                "sort_order": 13,
            },
        ]
        
        # Insert all questions at once
        conn.client.table("form_questions").upsert(questions).execute()
        
        return form
    except Exception as e:
        # Log error but don't crash signup
        print(f"⚠️ Could not create sample form for new user {admin_email}: {e}")
        return None
