# form_builder.py
import hashlib
import streamlit as st
from st_supabase_connection import SupabaseConnection

from servqual_utils import DIM_KEYS
from components import inject_css, section_head, render_dimension_cards
from forms import (
    init_form_session_state,
    get_current_form_id,
    set_current_form,
    fetch_active_forms,
    create_form,
    update_form,
    archive_form,
    delete_form_permanently,
    get_form,
    refresh_form_list,
    ensure_form_exists,
)

# Demographics dashboard uses donut-style charts: answers must come from a fixed option list.
ALLOWED_DEMOGRAPHIC_QTYPES = frozenset({"Multiple Choice", "Multiple Select"})


def demographic_qtype_ok(q_type: str | None) -> bool:
    return (q_type or "") in ALLOWED_DEMOGRAPHIC_QTYPES


# ══════════════════════════════════════════
# PAGE CONFIG & CSS
# ══════════════════════════════════════════
st.set_page_config(page_title="Form Builder", page_icon="🛠️", layout="wide")
inject_css()

# ── Force native Streamlit text colors to be dark & Add Premium Header ──
st.markdown("""
<style>
    /* Fix invisible text in Expanders */
    [data-testid="stExpander"] summary p {
        color: #1a2e55 !important;
        font-weight: 600 !important;
    }
    
    /* Fix invisible/faded text in Toggles and Checkboxes */
    [data-testid="stWidgetLabel"] p,
    [data-testid="stCheckbox"] p,
    [data-testid="stToggle"] p,
    label p {
        color: #1a2e55 !important;
        font-weight: 600 !important;
        opacity: 1 !important; 
    }
    
    /* Fix Dropdown (Selectbox) text and option lists */
    [data-baseweb="select"] span,
    [data-baseweb="select"] div,
    [data-baseweb="menu"] li,
    ul[role="listbox"] li {
        color: #1a2e55 !important;
    }

    /* 🌟 UNIQUE PREMIUM HEADER 🌟 */
    .premium-header {
        background: linear-gradient(135deg, var(--navy) 0%, rgb(40, 75, 140) 100%);
        border-radius: 12px;
        padding: 2.5rem 2.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px rgba(26,50,99,0.15);
        color: white;
    }
    .premium-header h1 { 
        font-family: 'Libre Baskerville', serif !important; 
        color: #ffffff !important; 
        margin: 0 0 0.5rem 0; 
        font-size: 2.2rem; 
    }
    .premium-header p { 
        color: #b0bcd8; 
        margin: 0; 
        font-size: 1rem; 
    }

    /* 🌟 LINK CARD 🌟 */
    .custom-link-card {
        background-color: #f0f4f8;
        border: 1px solid #dde3ef;
        border-left: 4px solid var(--navy);
        border-radius: 6px;
        padding: 1rem 1.2rem;
        margin-top: 0.5rem;
    }
    .custom-link-label { font-size: 0.75rem; font-weight: 700; color: var(--steel); text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 6px; margin-bottom: 6px;}
    .custom-link-url { font-size: 1rem; color: #1a5276; font-weight: 500; text-decoration: none; word-break: break-all; }
    .custom-link-url:hover { text-decoration: underline; }
    .custom-link-hint { font-size: 0.8rem; color: #7c8db5; margin-top: 6px; }

    /* 📱 RESPONSIVE MEDIA QUERIES 📱 */
    @media screen and (max-width: 768px) {
        .premium-header {
            padding: 1.5rem 1.2rem !important;
        }
        .premium-header h1 {
            font-size: 1.6rem !important;
        }
        .premium-header p {
            font-size: 0.9rem !important;
        }
        .custom-link-card {
            padding: 0.8rem 1rem !important;
        }
        .custom-link-url {
            font-size: 0.85rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# SUPABASE SETUP
# ══════════════════════════════════════════
conn        = st.connection("supabase", type=SupabaseConnection)
admin_email = st.session_state.user_email

# Initialize multi-form session state
init_form_session_state(admin_email)
current_form_id = get_current_form_id()  # Get from session state, not ensure_form_exists
if not current_form_id:
    current_form_id = ensure_form_exists(admin_email)
    if current_form_id:
        st.session_state.current_form_id = current_form_id

public_id   = current_form_id  # Use form_id as the public_id

try:
    host     = st.context.headers.get("Host")
    protocol = "https" if "localhost" not in host else "http"
    base_url = f"{protocol}://{host}"
except Exception:
    base_url = "http://localhost:8501"

shareable_link = f"{base_url}/?form_id={public_id}"

# ── Session state ──────────────────────────────────────────────────────
if "editing_id"     not in st.session_state: st.session_state.editing_id     = None
if "preview_mode"   not in st.session_state: st.session_state.preview_mode   = False
if "selected_ids"   not in st.session_state: st.session_state.selected_ids   = set()
if "filter_dim"     not in st.session_state: st.session_state.filter_dim     = "All"
if "filter_type"    not in st.session_state: st.session_state.filter_type    = "All"
if "filter_req"     not in st.session_state: st.session_state.filter_req     = "All"
if "_show_meta_saved" not in st.session_state: st.session_state._show_meta_saved = False
if "_confirm_delete_all_responses" not in st.session_state: st.session_state._confirm_delete_all_responses = False

# ══════════════════════════════════════════
# DB HELPERS
# ══════════════════════════════════════════
def fetch_questions(form_id: str = None):
    if form_id is None:
        form_id = current_form_id
    try:
        res = (conn.client.table("form_questions")
               .select("*").eq("admin_email", admin_email).eq("form_id", form_id)
               .order("sort_order").execute())
        return res.data or []
    except Exception:
        return []

def update_question(qid, payload: dict):
    conn.client.table("form_questions").update(payload).eq("id", qid).execute()

def delete_question(qid):
    conn.client.table("form_questions").delete().eq("id", qid).execute()

def delete_questions_bulk(qids: list):
    for qid in qids:
        conn.client.table("form_questions").delete().eq("id", qid).execute()

def apply_new_sort_order(ordered_ids: list):
    for new_order, qid in enumerate(ordered_ids, start=1):
        conn.client.table("form_questions").update({"sort_order": new_order}).eq("id", qid).execute()


@st.dialog("Delete this question?")
def dialog_delete_single_question():
    qid = st.session_state.get("_confirm_del_qid")
    qid_str = st.session_state.get("_confirm_del_qid_str") or ""
    if qid is None:
        return
    st.markdown(
        "**This removes the question from your survey builder and from the live form.**  \n\n"
        "- **Past responses stay** in the database, but the dashboard aligns charts with **today’s** question list.  \n"
        "- If you **add new questions** afterward, only **new submissions** will have answers for them."
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Delete permanently", type="primary", use_container_width=True):
            delete_question(qid)
            st.session_state.selected_ids.discard(qid_str)
            st.session_state.pop("_confirm_del_qid", None)
            st.session_state.pop("_confirm_del_qid_str", None)
            st.rerun()
    with c2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.pop("_confirm_del_qid", None)
            st.session_state.pop("_confirm_del_qid_str", None)
            st.rerun()


@st.dialog("Delete selected questions?")
def dialog_delete_bulk_questions():
    ids = st.session_state.get("_confirm_del_bulk_ids")
    if not ids:
        return
    n = len(ids)
    st.markdown(
        f"**Delete {n} question(s)?**  \n\n"
        "They will be removed from the builder and the live link. "
        "**Existing answers are not deleted**, but dashboard views follow **current** questions only. "
        "Any **new** questions you save later apply only to **new** responses."
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Delete all selected", type="primary", use_container_width=True):
            delete_questions_bulk(ids)
            st.session_state.selected_ids = set()
            st.session_state.pop("_confirm_del_bulk_ids", None)
            st.rerun()
    with c2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.pop("_confirm_del_bulk_ids", None)
            st.rerun()


@st.dialog("Demographics need a fixed list of answers")
def dialog_demographic_invalid_type():
    st.markdown(
        """
The **Demographics** tab groups answers in **donut (and similar) charts**. That only works when each
respondent picks from a **fixed set of choices** — not unique text like names, and not numeric scales.

**Allowed** when you turn on **Mark as demographic:**  
**Multiple Choice** (one option) or **Multiple Select** (several options, e.g. transport modes).

**Do not** mark as demographic: **Short Answer**, **Paragraph**, or **Likert** — those belong elsewhere
in your survey (e.g. open feedback or SERVQUAL ratings).
        """
    )
    if st.button("OK", type="primary", use_container_width=True):
        st.session_state.pop("_show_demo_type_dialog", None)
        st.rerun()


@st.dialog("Create New Form")
def dialog_create_form():
    form_title = st.text_input("Form title", placeholder="e.g. Customer Feedback Survey")
    form_desc = st.text_area("Description (optional)", placeholder="e.g. Collect feedback about our services")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create", type="primary", use_container_width=True):
            if form_title.strip():
                new_form = create_form(admin_email, form_title.strip(), form_desc.strip())
                if new_form:
                    refresh_form_list(admin_email)
                    set_current_form(new_form["form_id"])
                    st.session_state.pop("_show_create_form", None)
                    st.success(f"Form '{form_title}' created!")
                    st.rerun()
            else:
                st.error("Please enter a form title")
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.pop("_show_create_form", None)
            st.rerun()


@st.dialog("Rename Form")
def dialog_rename_form():
    form_id = st.session_state.get("_rename_form_id") or current_form_id
    forms = fetch_active_forms(admin_email)
    form = next((f for f in forms if f["form_id"] == form_id), None)
    
    if not form:
        st.error("Form not found")
        return
    
    new_name = st.text_input("Form name", value=form.get("title", ""), placeholder="Enter new form name")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", type="primary", use_container_width=True):
            if new_name.strip():
                update_form(form_id, admin_email, title=new_name.strip())
                refresh_form_list(admin_email)
                st.session_state.pop("_show_rename_form", None)
                st.success(f"Form renamed to '{new_name}'!")
                st.rerun()
            else:
                st.error("Please enter a form name")
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.pop("_show_rename_form", None)
            st.rerun()


@st.dialog("Confirm Delete Form")
def dialog_delete_form_confirmation():
    form_id = st.session_state.get("_confirm_delete_form_id")
    forms = fetch_active_forms(admin_email)
    form = next((f for f in forms if f["form_id"] == form_id), None)
    
    if not form:
        st.error("Form not found")
        return
    
    st.warning(f"⚠️ **Delete '{form['title']}'?**")
    st.markdown(f"""
    This will permanently delete:
    - The form: **{form['title']}**
    - All {len([x for x in forms if x['form_id'] == form_id])} responses
    - All form settings and questions
    
    **This cannot be undone.**
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Delete Permanently", type="primary", use_container_width=True):
            delete_form_permanently(form_id, admin_email)
            refresh_form_list(admin_email)
            st.session_state.pop("_confirm_delete_form_id", None)
            st.success(f"Form '{form['title']}' deleted.")
            st.rerun()
    
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.pop("_confirm_delete_form_id", None)
            st.rerun()


@st.dialog("Confirm Delete Multiple Forms")
def dialog_delete_multiple_forms_confirmation():
    form_ids = st.session_state.get("_confirm_delete_multiple_forms", [])
    forms = fetch_active_forms(admin_email)
    forms_to_delete = [f for f in forms if f["form_id"] in form_ids]
    
    if not forms_to_delete:
        st.error("No forms selected")
        return
    
    st.warning(f"⚠️ **Delete {len(forms_to_delete)} form(s)?**")
    st.markdown("This will permanently delete:")
    for form in forms_to_delete:
        st.markdown(f"- **{form['title']}** ({len([x for x in forms if x['form_id'] == form['form_id']])} responses)")
    
    st.markdown("**This cannot be undone.**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Delete All", type="primary", use_container_width=True):
            for form_id in form_ids:
                delete_form_permanently(form_id, admin_email)
            refresh_form_list(admin_email)
            st.session_state.pop("_confirm_delete_multiple_forms", None)
            st.success(f"{len(forms_to_delete)} form(s) deleted.")
            st.rerun()
    
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.pop("_confirm_delete_multiple_forms", None)
            st.rerun()





# ══════════════════════════════════════════
# HEADER & METADATA
# ══════════════════════════════════════════
try:
    meta_req  = conn.client.table("form_meta").select("*").eq("admin_email", admin_email).eq("form_id", current_form_id).limit(1).execute()
    form_meta = meta_req.data[0] if meta_req.data else {
        "title": "Land Public Transportation Respondent Survey",
        "description": "Please share your honest experience.",
        "include_demographics": False,
        "allow_multiple_responses": True,
        "reach_out_contact": "",
    }
except Exception:
    form_meta = {
        "title": "Land Public Transportation Respondent Survey",
        "description": "Please share your honest experience.",
        "include_demographics": False,
        "allow_multiple_responses": True,
        "reach_out_contact": "",
    }

# Always initialize form metadata - ensures values show even after tab switches
st.session_state.meta_form_name = st.session_state.get("meta_form_name") or get_form(current_form_id, admin_email).get("title", "") or ""
st.session_state.meta_title = st.session_state.get("meta_title") or form_meta.get("title", "") or ""
st.session_state.meta_desc = st.session_state.get("meta_desc") or form_meta.get("description", "") or ""
st.session_state.meta_reach_out = st.session_state.get("meta_reach_out") or form_meta.get("reach_out_contact") or ""
st.session_state.meta_allow_multi = st.session_state.get("meta_allow_multi", bool(form_meta.get("allow_multiple_responses", True)))
st.session_state.meta_include_demo = st.session_state.get("meta_include_demo", bool(form_meta.get("include_demographics", False)))

def update_meta():
    payload = {
        "admin_email": admin_email,
        "form_id": current_form_id,
        "public_id": public_id,
        "title": st.session_state.get("meta_title", form_meta.get("title", "")),
        "description": st.session_state.get("meta_desc", form_meta.get("description", "")),
        "include_demographics": st.session_state.get(
            "meta_include_demo", form_meta.get("include_demographics", False)
        ),
        "allow_multiple_responses": st.session_state.get(
            "meta_allow_multi", form_meta.get("allow_multiple_responses", True)
        ),
        "reach_out_contact": st.session_state.get(
            "meta_reach_out", form_meta.get("reach_out_contact") or ""
        ),
    }
    try:
        result = conn.client.table("form_meta").upsert(payload, on_conflict="admin_email,form_id").execute()
        st.session_state.pop("form_meta_migration_needed", None)
        st.session_state.pop("form_meta_reach_out_migration_needed", None)
        return True
    except Exception as e:
        err = str(e)
        stripped = False
        if "allow_multiple_responses" in err:
            st.session_state["form_meta_migration_needed"] = True
            payload.pop("allow_multiple_responses", None)
            stripped = True
        if "reach_out_contact" in err:
            st.session_state["form_meta_reach_out_migration_needed"] = True
            payload.pop("reach_out_contact", None)
            stripped = True
        if stripped:
            try:
                conn.client.table("form_meta").upsert(payload, on_conflict="admin_email,form_id").execute()
                return True
            except Exception as retry_e:
                st.error(f"Failed to save settings: {retry_e}")
                return False
        else:
            st.error(f"Failed to save settings: {e}")
            return False

st.markdown("""
<div class="premium-header">
    <div>
        <h1>🛠️ Form Builder</h1>
        <p>Design your surveys and manage questions — one form at a time.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Show success message if settings were just saved
if st.session_state.get("_show_meta_saved"):
    st.success("✅ Survey settings saved successfully!")
    st.session_state._show_meta_saved = False

# Clear any lingering dialog states to prevent dimming
# This ensures dialogs don't stay open when they shouldn't be
if st.session_state.get("_clear_all_dialogs"):
    st.session_state.pop("_show_create_form", None)
    st.session_state.pop("_show_manage_forms", None)
    st.session_state.pop("_confirm_delete_form_id", None)
    st.session_state.pop("_confirm_del_qid", None)
    st.session_state.pop("_confirm_del_bulk_ids", None)
    st.session_state.pop("_show_demo_type_dialog", None)
    st.session_state.pop("_clear_all_dialogs", None)

# ══════════════════════════════════════════
# FORM SELECTION SIDEBAR
# ══════════════════════════════════════════
available_forms = st.session_state.get("available_forms", [])
if not available_forms:
    st.warning("🔍 No forms found.")
    fsb1, fsb2 = st.columns(2)
    with fsb1:
        if st.button("➕ Create Your First Form", type="primary", use_container_width=True):
            st.session_state._show_create_form = True
    with fsb2:
        st.markdown("")
    
    # Trigger dialogs
    if st.session_state.get("_show_create_form"):
        dialog_create_form()
    
    st.stop()

# Form selector dropdown
sc1, sc2, sc3 = st.columns([2, 0.5, 0.5])

with sc1:
    form_options = [f["title"] for f in available_forms]
    current_form_idx = next((i for i, f in enumerate(available_forms) if f["form_id"] == current_form_id), 0)
    selected_form_name = st.selectbox(
        "📋 Select form to edit",
        form_options,
        index=current_form_idx,
        label_visibility="collapsed"
    )
    
    if selected_form_name:
        selected_form_obj = next((f for f in available_forms if f["title"] == selected_form_name), None)
        if selected_form_obj and selected_form_obj["form_id"] != current_form_id:
            set_current_form(selected_form_obj["form_id"])
            st.rerun()

with sc2:
    if st.button("➕ New", use_container_width=True, help="Create a new form"):
        st.session_state._show_create_form = True

with sc3:
    if st.button("✏️ Rename", use_container_width=True, help="Rename current form"):
        st.session_state._show_rename_form = True
        st.rerun()

# Trigger dialogs (only one at a time via if/elif)
if st.session_state.get("_show_create_form"):
    dialog_create_form()
elif st.session_state.get("_show_rename_form"):
    dialog_rename_form()
elif st.session_state.get("_confirm_delete_multiple_forms"):
    dialog_delete_multiple_forms_confirmation()
elif st.session_state.get("_confirm_delete_form_id"):
    dialog_delete_form_confirmation()
elif st.session_state.get("_show_demo_type_dialog"):
    dialog_demographic_invalid_type()
elif st.session_state.get("_confirm_del_qid") is not None:
    dialog_delete_single_question()
elif st.session_state.get("_confirm_del_bulk_ids"):
    dialog_delete_bulk_questions()

st.markdown("<div style='margin:1rem 0; border-bottom:1px solid #dde3ef'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════
# BUILDER INTERFACE (only show after form selection)
# ══════════════════════════════════════════
form_is_selected = current_form_id and len([f for f in available_forms if f["form_id"] == current_form_id]) > 0

if not form_is_selected:
    st.info("👆 **Select a form above to begin editing.**")
    st.stop()

# ══════════════════════════════════════════
# TABS: SETTINGS vs QUESTIONS vs MANAGE FORMS
# ══════════════════════════════════════════
tab_settings, tab_questions, tab_manage_forms, tab_info = st.tabs(["⚙️ Settings", "📝 Questions", "🗑️ Manage Forms", "ℹ️ SERVQUAL"])

with tab_settings:
    st.markdown("### Survey Settings")
    
    if st.session_state.get("form_meta_migration_needed"):
        st.error(
            "Database column `allow_multiple_responses` is missing on `form_meta`. "
            "Run the SQL in `sql/add_allow_multiple_responses_to_form_meta.sql` "
            "(Supabase → SQL Editor), then refresh this page."
        )

    if st.session_state.get("form_meta_reach_out_migration_needed"):
        st.error(
            "Database column `reach_out_contact` is missing on `form_meta`. "
            "Run the SQL in `sql/add_reach_out_contact_to_form_meta.sql` "
            "(Supabase → SQL Editor), then refresh this page."
        )
    
    sc1, sc2 = st.columns([1.2, 1])
    
    with sc1:
        st.subheader("📋 Survey Copy")
        st.text_input("Survey title", value=st.session_state.get("meta_title", ""), key="meta_title")
        st.text_area("Description (optional)", value=st.session_state.get("meta_desc", ""), key="meta_desc", height=80, placeholder="A few words about what you're asking")
        st.text_area(
            "Reach out / Contact",
            value=st.session_state.get("meta_reach_out", ""),
            key="meta_reach_out",
            height=80,
            placeholder="e.g. Email: research@school.edu · Office: Room 204\n\n(shown on thank-you screen)",
        )
        
        st.divider()
        
        st.subheader("🎯 Survey Behavior")
        st.toggle(
            "**Allow multiple responses** from the same user/session",
            key="meta_allow_multi",
            help="Uncheck if you want one response per person."
        )
        st.toggle(
            "**Include standard profile questions** (age, gender, transport mode, etc)",
            key="meta_include_demo",
            help="Automatically adds demographics section to your form."
        )
        
        st.divider()
        
        if st.button("💾 Save All Settings", type="primary", use_container_width=True):
            success = update_meta()
            if success:
                st.success("✅ Settings saved successfully!")
                refresh_form_list(admin_email)
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Failed to save settings. Please try again.")
    
    with sc2:
        st.subheader("🔗 Share & Preview")
        st.markdown(
            f"""
            <div class="custom-link-card">
              <div class="custom-link-label">📤 Shareable Link</div>
              <a class="custom-link-url" href="{shareable_link}" target="_blank">{shareable_link}</a>
              <div class="custom-link-hint" style="margin-top:8px;">Copy and send to respondents</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        st.subheader("🗑️ Data Management")
        if st.button("Delete all responses", type="secondary", use_container_width=True, help="Remove all submissions for this form"):
            st.session_state._confirm_delete_all_responses = True
        
        if st.session_state.get("_confirm_delete_all_responses"):
            st.warning("⚠️ This will permanently delete **ALL** responses. Cannot be undone.")
            db1, db2 = st.columns(2)
            with db1:
                if st.button("Yes, delete all", type="primary", key="confirm_delete_resp", use_container_width=True):
                    try:
                        conn.client.table("form_responses").delete().eq("form_id", current_form_id).eq("admin_email", admin_email).execute()
                        st.success("✅ All responses deleted.")
                        st.session_state._confirm_delete_all_responses = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            with db2:
                if st.button("Cancel", key="cancel_delete_resp", use_container_width=True):
                    st.session_state._confirm_delete_all_responses = False
                    st.rerun()

with tab_questions:
    st.markdown("### Manage Questions")
    
    # Preview mode toggle
    prev_col1, prev_col2 = st.columns([3, 1])
    with prev_col1:
        st.markdown("")
    with prev_col2:
        st.toggle(
            "👁 Preview",
            value=st.session_state.preview_mode,
            key="preview_toggle",
        )
        if st.session_state.get("preview_toggle") is not None:
            st.session_state.preview_mode = st.session_state.get("preview_toggle", False)
    
    questions = fetch_questions(current_form_id)

    # ══════════════════════════════════════════
    # ADD NEW QUESTION
    # ══════════════════════════════════════════
    if not st.session_state.preview_mode:
        with st.expander("➕ Add New Question", expanded=len(questions) == 0):
            qa1, qa2 = st.columns([2.5, 1.5])
            with qa1:
                new_prompt = st.text_input("Question text", placeholder="e.g. How was the driver's behavior?", label_visibility="collapsed")
            with qa2:
                selected_dim = st.selectbox("SERVQUAL dimension", ["None"] + DIM_KEYS, label_visibility="collapsed")
                servqual_dim = None if selected_dim == "None" else selected_dim

            # Determine available question types based on SERVQUAL dimension
            if servqual_dim is not None:
                # If SERVQUAL dimension is selected, only allow Likert Scale
                q_type_options = ["Rating (Likert)"]
                q_type = "Rating (Likert)"
            else:
                # If no SERVQUAL dimension, allow all question types
                q_type_options = ["Short Answer", "Paragraph", "Multiple Choice", "Multiple Select", "Rating (Likert)"]
                q_type = st.selectbox(
                    "Question type",
                    q_type_options,
                    label_visibility="collapsed",
                )

            new_options, new_scale_max, new_scale_label_low, new_scale_label_high = [], 5, "", ""

            if q_type in ("Multiple Choice", "Multiple Select"):
                st.markdown("**Options**")
                col1, col2 = st.columns([4, 1])
                with col1:
                    opt_input = st.text_input("Add option", placeholder="e.g. Mabuti", label_visibility="collapsed", key="opt_input")
                with col2:
                    if st.button("➕ Add", key="add_opt"):
                        if opt_input.strip():
                            if "new_options_list" not in st.session_state:
                                st.session_state.new_options_list = []
                            st.session_state.new_options_list.append(opt_input.strip())
                            st.rerun()
                
                # Display and manage options
                if "new_options_list" in st.session_state and st.session_state.new_options_list:
                    st.markdown("**Current options:**")
                    for i, opt in enumerate(st.session_state.new_options_list):
                        opt_col1, opt_col2 = st.columns([4, 1])
                        with opt_col1:
                            st.write(f"✓ {opt}")
                        with opt_col2:
                            if st.button("✕", key=f"del_opt_{i}"):
                                st.session_state.new_options_list.pop(i)
                                st.rerun()
                    new_options = st.session_state.new_options_list

            if q_type == "Rating (Likert)":
                st.markdown("**Scale Settings**")
                sc1, sc2, sc3 = st.columns([1, 2, 2])
                with sc1:
                    new_scale_max = st.number_input("Points", min_value=2, max_value=10, value=5, step=1, label_visibility="collapsed")
                with sc2:
                    new_scale_label_low = st.text_input("Low label", placeholder="Strongly Disagree", label_visibility="collapsed")
                with sc3:
                    new_scale_label_high = st.text_input(f"High label", placeholder="Strongly Agree", label_visibility="collapsed")

            # Inline checkboxes
            opt1, opt2, opt3 = st.columns(3)
            with opt1:
                is_required = st.checkbox("Required", value=True)
            with opt2:
                is_demographic_q = False
                if q_type in ("Multiple Choice", "Multiple Select") and servqual_dim is None:
                    is_demographic_q = st.checkbox("Mark as demographic", value=False, help="Fixed options for demographics profile")
            with opt3:
                enable_sentiment = False
                if q_type in ("Short Answer", "Paragraph"):
                    enable_sentiment = st.checkbox("Enable sentiment analysis", value=True, help="Analyze responses for sentiment")

            if st.button("💾 Save Question", use_container_width=True, type="primary"):
                if new_prompt.strip():
                    if q_type in ("Multiple Choice", "Multiple Select") and not new_options:
                        st.warning("Add at least one option for this question type.")
                    elif q_type == "Multiple Select" and len(new_options) < 2:
                        st.warning("Multiple select works best with 2+ options.")
                    else:
                        max_order = max((q.get("sort_order") or 0 for q in questions), default=0)
                        payload = {
                            "admin_email": admin_email,
                            "form_id": current_form_id,
                            "public_id": public_id,
                            "prompt": new_prompt.strip(), "q_type": q_type,
                            "options": new_options, "is_required": is_required,
                            "is_demographic": bool(is_demographic_q),
                            "servqual_dimension": servqual_dim,
                            "enable_sentiment": bool(enable_sentiment),
                            "sort_order": max_order + 1,
                        }
                        if q_type == "Rating (Likert)":
                            payload["scale_max"]        = int(new_scale_max)
                            payload["scale_label_low"]  = new_scale_label_low.strip() or None
                            payload["scale_label_high"] = new_scale_label_high.strip() or None
                        conn.client.table("form_questions").insert(payload).execute()
                        st.success("✅ Question added!")
                        if "new_options_list" in st.session_state:
                            del st.session_state.new_options_list
                        st.rerun()
                else:
                    st.warning("⚠️ Enter question text first.")

    # ══════════════════════════════════════════
    # FILTER & DISPLAY
    # ══════════════════════════════════════════
    st.markdown("---")
    
    # Compact filter bar
    fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2])
    with fcol1:
        st.selectbox("Dimension", ["All"] + DIM_KEYS + ["General / Demographic"], key="sel_fdim", label_visibility="collapsed")
        st.session_state.filter_dim = st.session_state.sel_fdim
    with fcol2:
        st.selectbox("Type", ["All", "Short Answer", "Paragraph", "Multiple Choice", "Multiple Select", "Rating (Likert)"], key="sel_ftype", label_visibility="collapsed")
        st.session_state.filter_type = st.session_state.sel_ftype
    with fcol3:
        st.selectbox("Required", ["All", "Required", "Optional"], key="sel_freq", label_visibility="collapsed")
        st.session_state.filter_req = st.session_state.sel_freq
    with fcol4:
        st.selectbox("Tag", ["All", "Demographic only", "Not demographic"], key="sel_fdemo", label_visibility="collapsed")
    with fcol5:
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

    def passes_filter(q):
        dim = q.get("servqual_dimension") or "General / Demographic"
        if st.session_state.filter_dim != "All" and dim != st.session_state.filter_dim:
            return False
        qtype = q.get("q_type", "")
        if st.session_state.filter_type != "All" and qtype != st.session_state.filter_type:
            return False
        if st.session_state.filter_req == "Required" and not q.get("is_required"):
            return False
        if st.session_state.filter_req == "Optional" and q.get("is_required"):
            return False
        fdemo = st.session_state.get("sel_fdemo", "All")
        if fdemo == "Demographic only" and not q.get("is_demographic"):
            return False
        if fdemo == "Not demographic" and q.get("is_demographic"):
            return False
        return True

    visible_questions = [q for q in questions if passes_filter(q)]
    filtered = len(visible_questions) < len(questions)
    filter_note = f"(filtered: {len(visible_questions)}/{len(questions)})" if filtered else f"({len(questions)} total)"

    # ══════════════════════════════════════════
    # QUESTIONS LIST
    # ══════════════════════════════════════════
    if st.session_state.preview_mode:
        header_text = "📋 Respondent Preview"
    else:
        header_text = f"📋 Your Questions {filter_note}"

    st.markdown(f"### {header_text}")

    if st.session_state.preview_mode:
        show_demo_block = form_meta.get("include_demographics", False)
    else:
        show_demo_block = st.session_state.get("meta_include_demo", form_meta.get("include_demographics", False))

    st.markdown("<div style='margin-bottom:1rem'></div>", unsafe_allow_html=True)

    LPT_TRANSPORT_MODE_OPTIONS = [
        "Jeepney",
        "Modern jeepney / E-jeep",
        "Bus",
        "UV Express",
        "Tricycle",
        "Train (MRT / LRT / PNR)",
        "TNVS (Grab, etc.)",
        "Other",
    ]

    STANDARD_DEMO_QUESTIONS = [
        {"prompt": "What is your age bracket?", "q_type": "Multiple Choice", "options": ["18-24", "25-34", "35-44", "45-54", "55 and above"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
        {"prompt": "What is your gender?", "q_type": "Multiple Choice", "options": ["Male", "Female", "Prefer not to say"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
        {"prompt": "What is your primary occupation?", "q_type": "Multiple Choice", "options": ["Student", "Employed", "Self-employed", "Unemployed", "Retired"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
        {
            "prompt": "Which Land Public Transportation modes do you usually use? (Select all that apply)",
            "q_type": "Multiple Select",
            "options": LPT_TRANSPORT_MODE_OPTIONS,
            "is_required": True,
            "servqual_dimension": "Commuter Profile",
            "is_demographic": True,
        },
        {"prompt": "How often do you commute?", "q_type": "Multiple Choice", "options": ["Daily", "3-4 times a week", "1-2 times a week", "Rarely"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    ]

    # ── Helper Functions for Arrow Buttons Reordering ──
    def move_question_order(q_list, target_index, direction):
        if direction == "up" and target_index > 0:
            swap_idx = target_index - 1
        elif direction == "down" and target_index < len(q_list) - 1:
            swap_idx = target_index + 1
        else:
            return
        new_list = [q["id"] for q in q_list]
        new_list[target_index], new_list[swap_idx] = new_list[swap_idx], new_list[target_index]
        apply_new_sort_order(new_list)
        st.rerun()

    def get_card_html(idx, q, q_num_label=None, is_locked=False):
        """Render a single question card."""
        def q_type_badge(q_type):
            return {"Short Answer":"✏️ Short Answer","Paragraph":"📝 Paragraph",
                    "Multiple Choice":"☑️ Multiple Choice","Multiple Select":"☑️ Multiple Select",
                    "Rating (Likert)":"⭐ Likert","Rating (1-5)":"⭐ Likert"}.get(q_type, q_type)

        def dim_pill(dim):
            if not dim: return ""
            colors = { 
                "Tangibles": ("#4a7c59","#e8f5ec"), "Reliability": ("#1a5276","#e8f0f7"), 
                "Responsiveness": ("#6c3483","#f3eaf7"), "Assurance": ("#7d6608","#fdf6d8"), 
                "Empathy": ("#922b21","#fceaea"), "Commuter Profile": ("#2a7a3b", "#e6f7eb") 
            }
            c, bg = colors.get(dim, ("#555","#eee"))
            return f'<span style="font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px;background:{bg};color:{c};margin-right:6px;">{dim}</span>'

        def likert_preview(q):
            scale_max  = int(q.get("scale_max") or 5)
            label_low  = q.get("scale_label_low")  or ""
            label_high = q.get("scale_label_high") or ""
            boxes = ""
            for i in range(1, scale_max + 1):
                lbl = label_low if i == 1 and label_low else (label_high if i == scale_max and label_high else "&nbsp;")
                boxes += f'<div style="display:flex;flex-direction:column;flex:1;min-width:40px;align-items:center;"><div style="width:100%;padding:12px 0;border:1px solid #dde3ef;border-radius:4px;display:flex;justify-content:center;font-size:13px;color:#3b5bdb;font-weight:500;">{i}</div><div style="font-size:11px;color:#7c8db5;margin-top:5px;text-align:center;min-height:15px;font-weight:600;">{lbl}</div></div>'
            # Added flex-wrap here for mobile responsiveness!
            return f'<div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:10px;width:100%; max-width:600px;">{boxes}</div>'

        display_num = q_num_label if q_num_label is not None else f"Q{idx + 1}"
        prompt   = q["prompt"].replace("<", "&lt;").replace(">", "&gt;")
        badge    = q_type_badge(q["q_type"])
        req_star = '<span style="color:#d63031;margin-left:2px;font-weight:700;">*</span>' if q.get("is_required") else ""
        dim_tag  = dim_pill(q.get("servqual_dimension"))
        demo_tag = (
            '<span style="font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px;background:#e8f4fc;color:#1565a8;margin-right:6px;">👤 Demographic</span>'
            if q.get("is_demographic")
            else ""
        )

        locked_badge = '<span style="font-size:11px;font-weight:700;color:#fff;background:#5566a0;padding:2px 6px;border-radius:4px;margin-right:4px;">🔒 Locked</span>' if is_locked else ""

        extra = ""
        if q["q_type"] in ("Rating (Likert)", "Rating (1-5)"):
            extra = likert_preview(q)
        elif q["q_type"] == "Multiple Choice" and q.get("options"):
            opts_html = ""
            for opt in q["options"]:
                safe_opt = opt.replace("<", "&lt;").replace(">", "&gt;")
                opts_html += f'<div style="display:flex;align-items:center;gap:10px;margin-top:10px;"><div style="width:14px;height:14px;border:2px solid #b0bcd8;border-radius:50%;flex-shrink:0;"></div><span style="font-size:13px;color:#1a2e55;">{safe_opt}</span></div>'
            extra = f'<div style="margin-top:8px;">{opts_html}</div>'
        elif q["q_type"] == "Multiple Select" and q.get("options"):
            opts_html = ""
            for opt in q["options"][:12]:
                safe_opt = opt.replace("<", "&lt;").replace(">", "&gt;")
                opts_html += f'<div style="display:flex;align-items:center;gap:10px;margin-top:10px;"><div style="width:14px;height:14px;border:2px solid #b0bcd8;border-radius:3px;flex-shrink:0;"></div><span style="font-size:13px;color:#1a2e55;">{safe_opt}</span></div>'
            if len(q["options"]) > 12:
                opts_html += f'<div style="font-size:12px;color:#7c8db5;margin-top:8px;">+{len(q["options"]) - 12} more options…</div>'
            extra = f'<div style="margin-top:8px;">{opts_html}</div>'
        elif q["q_type"] == "Short Answer":
            extra = '<div style="margin-top:16px;width:60%;border-bottom:1px dashed #b0bcd8;padding-bottom:6px;color:#7c8db5;font-size:13px;">Short answer text</div>'
        elif q["q_type"] == "Paragraph":
            extra = '<div style="margin-top:16px;width:100%;border-bottom:1px dashed #b0bcd8;padding-bottom:24px;color:#7c8db5;font-size:13px;">Long answer text</div>'

        border_style = "2px dashed #b0bcd8" if is_locked else "1px solid #dde3ef"

        html_str = f'<div style="background:#fff;border:{border_style};border-radius:8px;padding:14px;margin-bottom:4px;width:100%;box-shadow:0 1px 3px rgba(0,0,0,0.02);"><div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;flex-wrap:wrap;"><span style="font-size:11px;font-weight:700;color:#7c8db5;background:#eef1fa;padding:2px 6px;border-radius:4px;">{display_num}</span>{locked_badge}<span style="font-size:11px;color:#5566a0;background:#f0f3ff;padding:2px 7px;border-radius:4px;margin-right:4px;">{badge}</span>{dim_tag}{demo_tag}</div><div style="font-size:14px;font-weight:600;color:#1a2e55;line-height:1.4;word-break:break-word;">{prompt}{req_star}</div>{extra}</div>'
        
        return html_str

    # ══════════════════════════════════════════
    # DISPLAY QUESTIONS (PREVIEW & BUILDER MODES)
    # ══════════════════════════════════════════
    demo_offset = len(STANDARD_DEMO_QUESTIONS) if show_demo_block else 0

    # ── PREVIEW MODE ──
    if st.session_state.preview_mode:
        if show_demo_block:
            st.markdown("<p style='font-size:0.85rem; color:var(--steel); font-weight:600; margin-bottom: 0.5rem;'>Standard respondent profile</p>", unsafe_allow_html=True)
            for i, dq in enumerate(STANDARD_DEMO_QUESTIONS):
                st.markdown(get_card_html(i, dq, q_num_label=f"Q{i+1}", is_locked=True), unsafe_allow_html=True)
                st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 1.5rem 0; border-color: #dde3ef;'>", unsafe_allow_html=True)
                
        if len(visible_questions) > 0:
            st.markdown("<p style='font-size:0.85rem; color:var(--steel); font-weight:600; margin-bottom: 0.5rem;'>Custom Survey Questions</p>", unsafe_allow_html=True)
            for idx, q in enumerate(visible_questions):
                st.markdown(get_card_html(idx, q, q_num_label=f"Q{idx + 1 + demo_offset}"), unsafe_allow_html=True)
                st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
        elif not show_demo_block:
            st.markdown('<div style="text-align:center; padding:2rem; color:#7c8db5;">🔍 No custom questions added yet.</div>', unsafe_allow_html=True)

    # ── BUILDER MODE ──
    else:
        if show_demo_block and not filtered:
            st.markdown("<p style='font-size:0.85rem; color:var(--steel); font-weight:600; margin-bottom: 0.5rem;'>Standard respondent profile (automatically added)</p>", unsafe_allow_html=True)
            for i, dq in enumerate(STANDARD_DEMO_QUESTIONS):
                st.markdown(get_card_html(i, dq, q_num_label=f"Q{i+1}", is_locked=True), unsafe_allow_html=True)
                st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 1.5rem 0; border-color: #dde3ef;'>", unsafe_allow_html=True)

        if len(questions) == 0:
            if not show_demo_block:
                st.markdown('<div style="text-align:center; padding:2rem; color:#7c8db5; background:#fff; border:1px dashed #dde3ef; border-radius:8px;">📋 No custom questions yet — add one above.</div>', unsafe_allow_html=True)
        elif len(visible_questions) == 0:
            st.markdown('<div style="text-align:center; padding:2rem; color:#7c8db5;">🔍 No custom questions match the current filters.</div>', unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size:0.85rem; color:var(--steel); font-weight:600; margin-bottom: 0.5rem;'>Custom Survey Questions</p>", unsafe_allow_html=True)
            
            # BULK DELETE TOOLBAR
            n_selected = len(st.session_state.selected_ids)
            toolbar_left, toolbar_right = st.columns([6, 2])
            with toolbar_left:
                if n_selected:
                    st.markdown(f'<p style="margin:0;font-size:.82rem;color:var(--danger);font-weight:700;padding:6px 0;">☑ {n_selected} question{"s" if n_selected > 1 else ""} selected</p>', unsafe_allow_html=True)
                else:
                    st.markdown('<p style="margin:0;font-size:.82rem;color:var(--muted);padding:6px 0;">Check boxes to select custom questions for bulk delete.</p>', unsafe_allow_html=True)
            with toolbar_right:
                if n_selected:
                    if st.button(f"🗑️ Delete {n_selected} selected", use_container_width=True, type="primary"):
                        id_list = [qq["id"] for qq in visible_questions if str(qq["id"]) in st.session_state.selected_ids]
                        st.session_state._confirm_del_bulk_ids = id_list

            if visible_questions:
                all_visible_ids = {str(q["id"]) for q in visible_questions}
                all_selected    = all_visible_ids.issubset(st.session_state.selected_ids)
                sa_col, _ = st.columns([2, 6])
                with sa_col:
                    if st.button("☑ Select all" if not all_selected else "☐ Deselect all", use_container_width=True):
                        if not all_selected:
                            # Select all
                            st.session_state.selected_ids |= all_visible_ids
                            
                            # 🔥 IMPORTANT: Update checkbox UI states
                            for q in visible_questions:
                                st.session_state[f"chk_{q['id']}"] = True
                        else:
                            # Deselect all
                            st.session_state.selected_ids -= all_visible_ids
                            
                            # 🔥 IMPORTANT: Update checkbox UI states
                            for q in visible_questions:
                                st.session_state[f"chk_{q['id']}"] = False

                        st.rerun()
            st.markdown("<div style='margin-bottom:1rem'></div>", unsafe_allow_html=True)

            # ══════════════════════════════════════════
            # PER-QUESTION ROWS
            # ══════════════════════════════════════════
            for idx, q in enumerate(visible_questions):
                qid_str    = str(q["id"])
                is_editing = st.session_state.editing_id == qid_str
                is_checked = qid_str in st.session_state.selected_ids
                q_num_label = f"Q{idx + 1 + demo_offset}"

                if not is_editing:
                    st.markdown(get_card_html(idx, q, q_num_label=q_num_label), unsafe_allow_html=True)
                    
                    # NATIVE BUTTONS COLUMN LAYOUT
                    chk_col, up_col, down_col, spacer, edit_col, del_col = st.columns([0.5, 0.7, 0.7, 4.1, 1.5, 1.5], vertical_alignment="center")

                    with chk_col:
                        checked = st.checkbox("", value=is_checked, key=f"chk_{qid_str}", label_visibility="collapsed")
                        if checked and not is_checked:
                            st.session_state.selected_ids.add(qid_str)
                            st.rerun()
                        elif not checked and is_checked:
                            st.session_state.selected_ids.discard(qid_str)
                            st.rerun()

                    with up_col:
                        if st.button("⬆️", key=f"up_{qid_str}", help="Move Up", disabled=filtered or idx == 0):
                            move_question_order(visible_questions, idx, "up")

                    with down_col:
                        if st.button("⬇️", key=f"down_{qid_str}", help="Move Down", disabled=filtered or idx == len(visible_questions) - 1):
                            move_question_order(visible_questions, idx, "down")

                    with edit_col:
                        if st.button("✏️ EDIT", key=f"edit_btn_{qid_str}", use_container_width=True):
                            st.session_state.editing_id = qid_str
                            st.rerun()

                    with del_col:
                        if st.button("🗑️", key=f"del_btn_{qid_str}", use_container_width=True):
                            st.session_state._confirm_del_qid = q["id"]
                            st.session_state._confirm_del_qid_str = qid_str

                    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

                else:
                    st.markdown(f"**✏️ Editing {q_num_label}**")
                    with st.container():
                        ec1, ec2 = st.columns([3, 2])
                        with ec1:
                            e_prompt = st.text_input("Edit question", value=q["prompt"], key=f"ep_{qid_str}")
                        with ec2:
                            e_dim_choices = ["None"] + DIM_KEYS
                            e_dim = st.selectbox("Dimension", e_dim_choices, index=e_dim_choices.index(q["servqual_dimension"]) if q.get("servqual_dimension") in e_dim_choices else 0, key=f"ed_{qid_str}")
                        
                        # Determine available question types based on SERVQUAL dimension
                        if e_dim != "None":
                            # If SERVQUAL dimension is selected, only allow Likert Scale
                            type_opts = ["Rating (Likert)"]
                            e_type = "Rating (Likert)"
                        else:
                            # If no SERVQUAL dimension, allow all question types
                            type_opts = ["Short Answer", "Paragraph", "Multiple Choice", "Multiple Select", "Rating (Likert)"]
                            cur_type  = q["q_type"] if q["q_type"] in type_opts else "Rating (Likert)"
                            e_type    = st.selectbox("Type", type_opts, index=type_opts.index(cur_type), key=f"et_{qid_str}")

                        e_req = st.checkbox("Required", value=bool(q.get("is_required")), key=f"er_{qid_str}")
                        
                        # Mark as demographic - only show if Multiple Choice/Select and None dimension
                        e_demo = False
                        if e_type in ("Multiple Choice", "Multiple Select") and e_dim == "None":
                            e_demo = st.checkbox(
                                "Mark as demographic",
                                value=bool(q.get("is_demographic")),
                                key=f"edemo_{qid_str}",
                                help="Fixed options for demographics profile",
                            )
                        
                        # Sentiment analysis toggle - only for Short Answer and Paragraph
                        e_enable_sentiment = False
                        if e_type in ("Short Answer", "Paragraph"):
                            e_enable_sentiment = bool(q.get("enable_sentiment", True))
                            e_enable_sentiment = st.checkbox(
                                "Enable sentiment analysis for this question",
                                value=e_enable_sentiment,
                                key=f"es_{qid_str}",
                                help="If checked, responses to this question will be analyzed for sentiment.",
                            )
                        
                        e_opts_raw = []
                        if e_type in ("Multiple Choice", "Multiple Select"):
                            st.markdown("**Options**")
                            # Initialize options list from existing options
                            edit_key = f"edit_opts_{qid_str}"
                            if edit_key not in st.session_state:
                                st.session_state[edit_key] = list(q.get("options") or [])
                            
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                opt_input = st.text_input("Add option", placeholder="e.g. Mabuti", label_visibility="collapsed", key=f"edit_opt_input_{qid_str}")
                            with col2:
                                if st.button("➕ Add", key=f"add_edit_opt_{qid_str}"):
                                    if opt_input.strip():
                                        st.session_state[edit_key].append(opt_input.strip())
                                        st.rerun()
                            
                            # Display and manage options
                            if st.session_state[edit_key]:
                                st.markdown("**Current options:**")
                                for i, opt in enumerate(st.session_state[edit_key]):
                                    opt_col1, opt_col2 = st.columns([4, 1])
                                    with opt_col1:
                                        st.write(f"✓ {opt}")
                                    with opt_col2:
                                        if st.button("✕", key=f"del_edit_opt_{qid_str}_{i}"):
                                            st.session_state[edit_key].pop(i)
                                            st.rerun()
                            e_opts_raw = st.session_state[edit_key]

                        e_scale_max        = q.get("scale_max") or 5
                        e_scale_label_low  = q.get("scale_label_low")  or ""
                        e_scale_label_high = q.get("scale_label_high") or ""

                        if e_type == "Rating (Likert)":
                            st.markdown("**Likert Scale Settings**")
                            ls1, ls2, ls3 = st.columns([1, 2, 2])
                            with ls1:
                                e_scale_max = st.number_input("Points (max)", min_value=2, max_value=10, value=int(e_scale_max), step=1, key=f"esmax_{qid_str}")
                            with ls2:
                                e_scale_label_low = st.text_input("Label for 1 (lowest)", value=e_scale_label_low, placeholder="e.g. Strongly Disagree", key=f"eslow_{qid_str}")
                            with ls3:
                                e_scale_label_high = st.text_input(f"Label for {int(e_scale_max)} (highest)", value=e_scale_label_high, placeholder="e.g. Strongly Agree", key=f"eshigh_{qid_str}")

                        sv_col, cn_col = st.columns(2)
                        with sv_col:
                            if st.button("💾 Save changes", key=f"save_{qid_str}"):
                                update_payload = {
                                    "prompt":             e_prompt.strip(),
                                    "q_type":             e_type,
                                    "options":            e_opts_raw if isinstance(e_opts_raw, list) else [o.strip() for o in e_opts_raw.split(",") if o.strip()],
                                    "is_required":        e_req,
                                    "is_demographic":     bool(e_demo),
                                    "enable_sentiment":   bool(e_enable_sentiment),
                                    "servqual_dimension": None if e_dim == "None" else e_dim,
                                }
                                if e_type == "Rating (Likert)":
                                    update_payload["scale_max"]        = int(e_scale_max)
                                    update_payload["scale_label_low"]  = e_scale_label_low.strip() if e_scale_label_low else None
                                    update_payload["scale_label_high"] = e_scale_label_high.strip() if e_scale_label_high else None
                                else:
                                    update_payload["scale_max"]        = None
                                    update_payload["scale_label_low"]  = None
                                    update_payload["scale_label_high"] = None
                                update_question(q["id"], update_payload)
                                if f"edit_opts_{qid_str}" in st.session_state:
                                    del st.session_state[f"edit_opts_{qid_str}"]
                                st.session_state.editing_id = None
                                st.rerun()
                        with cn_col:
                            if st.button("✕ Cancel", key=f"cancel_{qid_str}"):
                                st.session_state.editing_id = None
                                st.rerun()

                st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)

with tab_manage_forms:
    st.markdown("### 🗑️ Manage Forms")
    
    forms = fetch_active_forms(admin_email)
    
    # Initialize selected forms list if not exists
    if "_selected_delete_forms" not in st.session_state:
        st.session_state._selected_delete_forms = []
    
    # Header with selection counter
    h1, h2 = st.columns([2, 1])
    with h1:
        st.markdown("")
    with h2:
        n_selected = len(st.session_state._selected_delete_forms)
        st.markdown(f"<div style='text-align:right;'><span style='font-weight:700; color:#3b5bdb;'>{n_selected}</span> selected</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Callback for Select All checkbox
# Callback for Select All checkbox
    def toggle_all_forms():
        if st.session_state.get("toggle_all_forms"):
            # Checkbox was just checked - select all
            st.session_state._selected_delete_forms = [f['form_id'] for f in forms]
            
            # 🛠️ FIX: Explicitly update the session state of each individual checkbox
            for form in forms:
                st.session_state[f"chk_{form['form_id']}"] = True
                
        else:
            # Checkbox was just unchecked - deselect all
            st.session_state._selected_delete_forms = []
            
            # 🛠️ FIX: Explicitly clear the session state of each individual checkbox
            for form in forms:
                st.session_state[f"chk_{form['form_id']}"] = False
    
    # Toggle all checkbox with callback
    sb1, sb2 = st.columns([1, 3])
    with sb1:
        all_checked = len(st.session_state._selected_delete_forms) == len(forms) and len(forms) > 0
        st.checkbox("Select All", value=all_checked, key="toggle_all_forms", on_change=toggle_all_forms)
    with sb2:
        st.markdown("")
    
    st.markdown("")
    
    # Form list with container key to force re-render on selection changes
    with st.container(key=f"form_list_{hash(tuple(sorted(st.session_state._selected_delete_forms)))}"):
        if forms:
            for form in forms:
                form_id = form['form_id']
                is_checked = form_id in st.session_state._selected_delete_forms
                response_count = len([x for x in forms if x['form_id'] == form_id])
                
                # Create row with checkbox, title, and response count
                row1, row2, row3 = st.columns([0.5, 2.5, 0.8])
                with row1:
                    checked = st.checkbox("", value=is_checked, key=f"chk_{form_id}", label_visibility="collapsed")
                    if checked != is_checked:
                        if checked:
                            if form_id not in st.session_state._selected_delete_forms:
                                st.session_state._selected_delete_forms.append(form_id)
                        else:
                            if form_id in st.session_state._selected_delete_forms:
                                st.session_state._selected_delete_forms.remove(form_id)
                        st.rerun()
                
                with row2:
                    st.markdown(f"**{form['title']}**", help=form.get('description', ''))
                
                with row3:
                    st.caption(f"{response_count} response{'s' if response_count != 1 else ''}")
        else:
            st.info("No forms available")
    
    st.divider()
    
    # Delete action button
    col1, col2 = st.columns([1, 3])
    with col1:
        delete_disabled = len(st.session_state._selected_delete_forms) == 0
        if st.button("🗑️ Delete Selected", type="primary" if not delete_disabled else "secondary", use_container_width=True, disabled=delete_disabled):
            st.session_state._confirm_delete_multiple_forms = st.session_state._selected_delete_forms.copy()
            st.session_state._selected_delete_forms = []
            st.rerun()
    with col2:
        st.markdown("")

with tab_info:
    st.markdown("### SERVQUAL Framework")
    st.markdown("""
The **SERVQUAL** model measures service quality across five key dimensions:
""")
    render_dimension_cards()