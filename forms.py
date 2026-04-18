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
    Create a default sample form with comprehensive demographic and SERVQUAL questions for new users.
    This is called automatically upon account creation.
    Includes bilingual (English/Tagalog) support for all questions.
    """
    try:
        conn = get_supabase_client()
        
        # Step 1: Create the form
        form = create_form(
            admin_email,
            title="Land Public Transportation Service Quality Survey",
            description="PART 1: Demographics | PART 2: Service Quality Evaluation (SERVQUAL)\nPlease answer in pure English, pure Tagalog, or Taglish"
        )
        
        if not form:
            return None
        
        form_id = form.get("form_id")
        
        # Step 2: Create form metadata
        meta_payload = {
            "admin_email": admin_email,
            "form_id": form_id,
            "title": "Land Public Transportation Service Quality Survey",
            "description": "PART 1: Demographics | PART 2: Service Quality Evaluation (SERVQUAL)\nPlease answer in pure English, pure Tagalog, or Taglish",
            "include_demographics": True,
            "allow_multiple_responses": True,
            "reach_out_contact": "",
        }
        conn.client.table("form_meta").upsert(meta_payload, on_conflict="admin_email,form_id").execute()
        
        # Step 3: Create comprehensive demographic and SERVQUAL questions
        questions = [
            # ════════════════════════════════════════════════════
            # PART 1: DEMOGRAPHICS (Questions 1-6)
            # ════════════════════════════════════════════════════
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "1. Age / Edad",
                "q_type": "Multiple Choice",
                "options": ["Below / Mababa sa 18", "18-25", "26-35", "36-45", "46-55", "Above / Mataas sa 55"],
                "is_required": True,
                "is_demographic": True,
                "enable_sentiment": False,
                "servqual_dimension": None,
                "sort_order": 1,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "2. Gender / Kasarian",
                "q_type": "Multiple Choice",
                "options": ["Male (Lalaki)", "Female (Babae)", "Prefer not to say (Mas pinipiling huwag sabihin)"],
                "is_required": True,
                "is_demographic": True,
                "enable_sentiment": False,
                "servqual_dimension": None,
                "sort_order": 2,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "3. Occupational Status / Katayuan sa Trabaho",
                "q_type": "Multiple Choice",
                "options": ["Student (Estudyante)", "Employee / Self-employed (Empleyado / may sariling pinagkikitaan)", "Employer / Business-owner (May-ari ng Negosyo)", "Unemployed (Walang trabaho)"],
                "is_required": True,
                "is_demographic": True,
                "enable_sentiment": False,
                "servqual_dimension": None,
                "sort_order": 3,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "4. Monthly Allowance or Salary / Buwanang Sahod o Allowance",
                "q_type": "Multiple Choice",
                "options": ["Below / Mababa sa Php 5,000", "Php 5,001 - 10,000", "Php 10,001 - 20,000", "Php 20,001 - 30,000", "Php 30,001 - 40,000", "Php 40,001 - 50,000", "Above / Mataas sa Php 50,001"],
                "is_required": True,
                "is_demographic": True,
                "enable_sentiment": False,
                "servqual_dimension": None,
                "sort_order": 4,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "5. Frequency of Commuting / Gaano ka kadalas sumakay sa isang linggo?",
                "q_type": "Multiple Choice",
                "options": ["Once a week (Isang beses sa isang linggo)", "2-3 times a week (2-3 beses sa isang linggo)", "4-5 times a week (4-5 beses sa isang linggo)", "Everyday (Araw-araw)"],
                "is_required": True,
                "is_demographic": True,
                "enable_sentiment": False,
                "servqual_dimension": None,
                "sort_order": 5,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "6. Most frequently used transport mode / Pinakamadalas na sinasakyan",
                "q_type": "Multiple Choice",
                "options": ["Traditional Jeepney (Tradisyunal na Jeepney)", "Modern Jeepney (Modernong Jeepney)", "Bus", "Taxi (Taksi)", "UV Express", "Ride-hailing services (e.g., Angkas, Grab, Move It)", "LRT-1", "LRT-2", "MRT-3", "Others"],
                "is_required": True,
                "is_demographic": True,
                "enable_sentiment": False,
                "servqual_dimension": None,
                "sort_order": 6,
            },
            
            # ════════════════════════════════════════════════════
            # PART 2: SERVQUAL SERVICE QUALITY EVALUATION
            # ════════════════════════════════════════════════════
            
            # Dimension 1: Tangibles (Physical appearance and comfort)
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "DIMENSION 1: TANGIBLES (Physical appearance and comfort)\n\nQuestion 1: How would you describe the physical condition and cleanliness of the vehicle or train you rode, as well as the seating comfort? (Paano mo ilalarawan ang pisikal na kondisyon at kalinisan ng sasakyan o tren na sinakyan mo, pati na rin ang komportableng pag-upo?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Tangibles",
                "sort_order": 7,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "Question 2: What can you say about the air ventilation and temperature (coldness or heat) inside the vehicle? (Ano ang masasabi mo sa bentilasyon ng hangin at temperatura (lamig o init) sa loob ng sasakyan?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Tangibles",
                "sort_order": 8,
            },
            
            # Dimension 2: Reliability (Dependability and smooth service)
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "DIMENSION 2: RELIABILITY (Dependability and smooth service)\n\nQuestion 3: What is your experience regarding the vehicle's reliability, specifically in avoiding mechanical failures mid-journey and adhering to the correct passenger capacity? (Ano ang karanasan mo pagdating sa pag-iwas ng sasakyan sa pagtirik o pagkasira sa gitna ng byahe, pati na rin sa pagsunod sa tamang bilang ng pasahero?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Reliability",
                "sort_order": 9,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "Question 4: What are your thoughts on the fare price and whether the driver or conductor gives the exact change? (Ano ang pananaw mo sa presyo ng pamasahe at sa pagbibigay ng tamang sukli ng driver o konduktor?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Reliability",
                "sort_order": 10,
            },
            
            # Dimension 3: Responsiveness (Promptness and communication)
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "DIMENSION 3: RESPONSIVENESS (Promptness and communication)\n\nQuestion 5: What can you say about the promptness or speed of the trip in helping you reach your destination on time? (Ano ang masasabi mo sa bilis ng biyahe upang makarating ka sa tamang oras sa iyong destinasyon?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Responsiveness",
                "sort_order": 11,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "Question 6: How would you describe the attentiveness of the driver or conductor when communicating or when you need to alight at the correct drop-off point? (Paano mo ilalarawan ang pagiging alisto ng driver o konduktor kapag kinakausap o kapag kailangan mo nang bumaba sa tamang babaan?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Responsiveness",
                "sort_order": 12,
            },
            
            # Dimension 4: Assurance (Safety, security, and competence)
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "DIMENSION 4: ASSURANCE (Safety, security, and competence)\n\nQuestion 7: What can you say about the carefulness of the driver in driving and their compliance with traffic laws? (Ano ang masasabi mo sa pagiging maingat ng driver sa pagmamaneho at sa pagsunod niya sa mga batas trapiko?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Assurance",
                "sort_order": 13,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "Question 8: How would you describe your sense of safety or feeling \"safe from crimes\" (such as theft or harassment) inside the vehicle? (Paano mo ilalarawan ang iyong pakiramdam ng kaligtasan o pagiging ligtas sa mga krimen (tulad ng pagnanakaw o harassment) sa loob ng sasakyan?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Assurance",
                "sort_order": 14,
            },
            
            # Dimension 5: Empathy (Caring and individualized attention)
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "DIMENSION 5: EMPATHY (Caring and individualized attention)\n\nQuestion 9: What can you say about the politeness, behavior, and care shown by the driver or conductor towards the passengers? (Ano ang masasabi mo sa pagiging magalang, pag-uugali, at pag-aalaga ng driver o konduktor sa mga pasahero?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Empathy",
                "sort_order": 15,
            },
            {
                "form_id": form_id,
                "admin_email": admin_email,
                "prompt": "Question 10: How would you evaluate the assistance provided and the designated areas for those in need, such as Senior Citizens, PWDs, and pregnant women? (Paano mo susuriin ang ibinibigay na tulong at mga nakalaang pwesto para sa mga nangangailangan tulad ng Senior Citizens, PWDs, at mga buntis?)",
                "q_type": "Paragraph",
                "options": [],
                "is_required": True,
                "is_demographic": False,
                "enable_sentiment": True,
                "servqual_dimension": "Empathy",
                "sort_order": 16,
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
                "enable_sentiment": True,
                "servqual_dimension": None,
                "sort_order": 17,
            },
        ]
        
        # Insert all questions at once
        conn.client.table("form_questions").upsert(questions).execute()
        
        return form
    except Exception as e:
        # Log error but don't crash signup
        print(f"⚠️ Could not create sample form for new user {admin_email}: {e}")
        return None
