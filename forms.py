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
        
        forms = result.data or []
        
        # Sort: Sentibyahe sample form always first, then others by creation date (newest first)
        sample_form = next((f for f in forms if f["title"] == "Sentibyahe: System Evaluation Test Form"), None)
        other_forms = [f for f in forms if f["title"] != "Sentibyahe: System Evaluation Test Form"]
        
        if sample_form:
            return [sample_form] + other_forms
        else:
            return forms
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
                "include_standard_servqual_questions": False,
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
    st.session_state.pop("meta_allow_multi", None)
    st.session_state.pop("meta_include_demo", None)
    st.session_state.pop("meta_include_servqual", None)
    st.session_state.pop("_meta_loaded_for_form", None)
    st.session_state.pop("preview_mode", None)


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
    Create a default sample form with comprehensive demographic and SERVQUAL questions for new users.
    This is called automatically upon account creation.
    Includes bilingual (English/Tagalog) support for all questions.
    """
    try:
        conn = get_supabase_client()
        
        # Step 1: Create the form
        form = create_form(
            admin_email,
            title="Sentibyahe: System Evaluation Test Form",
            description="This is a default survey created for you to easily test the Sentibyahe platform. It contains a pre-loaded 10-item questionnaire specifically designed to measure public transport quality across five SERVQUAL dimensions: Reliability, Assurance, Tangibles, Empathy, and Responsiveness.\n\nYou do not need to create your own survey questions. Instead, please answer the form based on your actual and recent commuting experiences. Once submitted, observe how our AI reads and classifies your real-time sentiments. Your experience testing this form with your authentic feedback will serve as your basis for grading our software as an active commuter, transport stakeholder, or IT professional."
        )
        
        if not form:
            return None
        
        form_id = form.get("form_id")
        
        # Step 2: Create form metadata
        meta_payload = {
            "admin_email": admin_email,
            "form_id": form_id,
            "title": "Sentibyahe: System Evaluation Test Form",
            "description": "This is a default survey created for you to easily test the Sentibyahe platform. It contains a pre-loaded 10-item questionnaire specifically designed to measure public transport quality across five SERVQUAL dimensions: Reliability, Assurance, Tangibles, Empathy, and Responsiveness.\n\nYou do not need to create your own survey questions. Instead, please answer the form based on your actual and recent commuting experiences. Once submitted, observe how our AI reads and classifies your real-time sentiments. Your experience testing this form with your authentic feedback will serve as your basis for grading our software as an active commuter, transport stakeholder, or IT professional.",
            "include_demographics": True,
            "include_standard_servqual_questions": True,
            "allow_multiple_responses": True,
            "reach_out_contact": "We'd love your feedback! 💡\n\nThanks for testing Sentibyahe! Now that you've seen how the system processes your response into the five transport categories, it's time to tell us what you think. Please take 2 quick minutes to evaluate the platform's usability, performance, and overall design. Your feedback is crucial to our research.\n\nhttps://docs.google.com/forms/d/e/1FAIpQLSemJsPRgflhlRLTcgEKidMSfyWS6NZCA5m2CvEJUOQ-JPF3vA/viewform?usp=sharing&ouid=104216160606281095977",
            "is_sample_form": True,
        }
        conn.client.table("form_meta").upsert(meta_payload, on_conflict="admin_email,form_id").execute()
        
        # Step 3: Create SERVQUAL questions (demographic questions are now auto-added via standard template)
        questions = [
            # ════════════════════════════════════════════════════
            # PART 1: SERVQUAL SERVICE QUALITY EVALUATION (LOCKED)
            # ════════════════════════════════════════════════════
            
            # Dimension 1: Tangibles (Physical appearance and comfort) - LIKERT RATING
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How would you describe the physical condition, cleanliness, and overall seating comfort of the vehicle you rode recently? (Paano mo ilalarawan ang pisikal na kondisyon, kalinisan, at pangkalahatang komportableng pag-upo sa sasakyang sinakyan mo kamakailan lang?)",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": False,
                "servqual_dimension": "Tangibles",
                "sort_order": 7,
                "is_locked": True,
                "scale_max": 5,
                "scale_label_low": "Poor",
                "scale_label_high": "Excellent",
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "What can you say about the air ventilation, temperature, and general atmosphere inside the vehicle? (Ano ang masasabi mo sa bentilasyon ng hangin, temperatura, at pangkalahatang kapaligiran sa loob ng sasakyan?)",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": False,
                "servqual_dimension": "Tangibles",
                "sort_order": 8,
                "is_locked": True,
                "scale_max": 5,
                "scale_label_low": "Poor",
                "scale_label_high": "Excellent",
            },
            # Dimension 2: Reliability (Dependability and smooth service) - LIKERT RATING
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How would you describe the overall reliability and operation of the vehicle during your entire trip? (Paano mo ilalarawan ang pangkalahatang pagiging maaasahan at maayos na takbo ng sasakyan sa buong biyahe mo?)",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": False,
                "servqual_dimension": "Reliability",
                "sort_order": 9,
                "is_locked": True,
                "scale_max": 5,
                "scale_label_low": "Poor",
                "scale_label_high": "Excellent",
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "What are your thoughts on the affordability of the fare and how your payment and change were handled by the driver/conductor? (Ano ang iyong pananaw sa halaga ng pamasahe at kung paano inasikaso ng drayber/konduktor ang iyong ibinayad at sukli?)",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": False,
                "servqual_dimension": "Reliability",
                "sort_order": 10,
                "is_locked": True,
                "scale_max": 5,
                "scale_label_low": "Poor",
                "scale_label_high": "Excellent",
            },
            # Dimension 3: Responsiveness (Promptness and communication) - LIKERT RATING
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How would you describe your experience regarding the travel time and the promptness of the ride in reaching your destination? (Paano mo ilalarawan ang iyong karanasan patungkol sa tagal ng biyahe at ang pagiging maagap ng sasakyan patungo sa iyong destinasyon?)",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": False,
                "servqual_dimension": "Responsiveness",
                "sort_order": 11,
                "is_locked": True,
                "scale_max": 5,
                "scale_label_low": "Poor",
                "scale_label_high": "Excellent",
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "What can you say about the attentiveness of the driver or conductor when passengers needed to get off or communicate their drop-off points? (Ano ang masasabi mo sa pagiging alisto ng driver o konduktor kapag kailangan nang bumaba o makipag-usap ng mga pasahero para sa kanilang bababaan?)",
                "q_type": "Rating (Likert)",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": False,
                "servqual_dimension": "Responsiveness",
                "sort_order": 12,
                "is_locked": True,
                "scale_max": 5,
                "scale_label_low": "Poor",
                "scale_label_high": "Excellent",
            },
            # Dimension 4: Assurance (Safety, security, and competence) - PARAGRAPH SENTIMENT
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "What are your thoughts on how the driver navigated the road and followed traffic rules during your trip? (Ano ang iyong pananaw sa kung paano nagmaneho at sumunod sa batas trapiko ang driver sa iyong biyahe?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Assurance",
                "sort_order": 13,
                "is_locked": True,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "How would you describe your overall sense of safety and security against incidents like theft or harassment while inside the vehicle? (Paano mo ilalarawan ang iyong pangkalahatang pakiramdam ng kaligtasan at seguridad laban sa mga insidente tulad ng pagnanakaw o harassment habang nasa loob ng sasakyan?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Assurance",
                "sort_order": 14,
                "is_locked": True,
            },
            # Dimension 5: Empathy (Caring and individualized attention) - PARAGRAPH SENTIMENT
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "What can you say about the behavior, politeness, and overall treatment of passengers by the transport crew? (Ano ang masasabi mo sa pag-uugali, pagiging magalang, at pangkalahatang pagtrato ng mga tauhan sa mga pasahero?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Empathy",
                "sort_order": 15,
                "is_locked": True,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "What are your thoughts on the transport crew's attentiveness and care for passengers who might need extra assistance, such as Senior Citizens, PWDs, or pregnant women? (Ano ang pananaw mo sa pagiging maasikaso at pag-aalaga ng mga tauhan sa mga pasaherong maaaring mangailangan ng karagdagang tulong, tulad ng Senior Citizens, PWDs, o mga buntis?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Empathy",
                "sort_order": 16,
                "is_locked": True,
            },
            
            # Optional overall feedback
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "Additional Comments or Suggestions / Karagdagang Komento o Mungkahi",
                "q_type": "Paragraph",
                "options": [],
                "is_required": False,
                "is_demographic": False,
                "enable_sentiment": False,
                "servqual_dimension": None,
                "sort_order": 17,
                "is_locked": True,
            },
        ]
        
        # Insert all questions at once
        conn.client.table("form_questions").upsert(questions).execute()
        
        return form
    except Exception as e:
        # Log error but don't crash signup
        print(f"⚠️ Could not create sample form for new user {admin_email}: {e}")
        return None
