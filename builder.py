# form_builder.py
import uuid
import hashlib
import streamlit as st
from st_supabase_connection import SupabaseConnection
import streamlit.components.v1 as components

from servqual_utils import DIM_KEYS
from components import inject_css
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
st.set_page_config(page_title="Create Form", page_icon="🛠️", layout="wide")

# 🔥 DYNAMIC NUCLEAR LOADER 🔥
def render_nuclear_loader(duration="2.5s", text="Loading Workspace..."):
    if duration == "0s":
        return  # Do not inject loader if no transition is happening

    loader_id = f"loader_{uuid.uuid4().hex[:8]}"
    
    st.markdown(f"""
    <style>
        [data-testid="stSidebar"], 
        [data-testid="stSidebarCollapsedControl"] {{
            z-index: 999999999 !important;
        }}

        .stApp [data-testid="stAppViewBlockContainer"] {{
            visibility: hidden !important;
            animation: snapVisible_{loader_id} 0.1s forwards {duration} !important;
        }}

        #{loader_id} {{
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-color: #f0f4f8; z-index: 999999998;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            animation: fadeOutNuclear_{loader_id} 0.4s ease-out {duration} forwards;
        }}

        .spinner_{loader_id} {{
            border: 4px solid #ffffff; border-top: 4px solid #1a2e55; border-radius: 50%;
            width: 50px; height: 50px; margin-bottom: 15px;
            animation: spin_{loader_id} 0.8s linear infinite;
        }}

        .loading-text_{loader_id} {{
            color: #1a2e55; font-weight: 600; font-family: 'Source Sans Pro', sans-serif;
            font-size: 1.1rem; letter-spacing: 0.5px;
        }}

        @keyframes snapVisible_{loader_id} {{ to {{ visibility: visible !important; }} }}
        @keyframes fadeOutNuclear_{loader_id} {{
            0% {{ opacity: 1; visibility: visible; }}
            100% {{ opacity: 0; visibility: hidden; display: none; }}
        }}
        @keyframes spin_{loader_id} {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>

    <div id="{loader_id}">
        <div class="spinner_{loader_id}"></div>
        <div class="loading-text_{loader_id}">{text}</div>
    </div>
    """, unsafe_allow_html=True)

inject_css()

# ══════════════════════════════════════════
# PAGE NAVIGATION STATE CLEANUP & LOADER LOGIC
# ══════════════════════════════════════════
if st.session_state.get("current_page") != "form_builder":
    st.session_state.current_page = "form_builder"
    prev_page = st.session_state.get("_prev_page", "")

    # Show loader whether coming from login (initial) OR from another page
    st.session_state._page_initial_load = False
    st.session_state._trigger_transition_loader = True
    st.session_state._transition_loader_text = "Loading Workspace..."

    dialog_keys = [
        "_show_create_form", "_show_rename_form", "_confirm_delete_form_id",
        "_confirm_delete_multiple_forms", "_show_demo_type_dialog",
        "_confirm_del_qid", "_confirm_del_qid_str", "_confirm_del_bulk_ids",
        "_confirm_delete_all_responses"
    ]
    for key in dialog_keys:
        st.session_state.pop(key, None)

# Determine if we need to show the loader on this specific rerun
load_duration = "0s"
load_text = ""

if st.session_state.get("_page_initial_load"):
    load_duration = "2.0s"
    load_text = "Loading Workspace..."
    st.session_state._page_initial_load = False
elif st.session_state.get("_trigger_transition_loader"):
    load_duration = "1.0s"  # Shorter wait for transitions
    load_text = st.session_state.get("_transition_loader_text", "Loading...")
    st.session_state._trigger_transition_loader = False

render_nuclear_loader(load_duration, load_text)

# ── Force native Streamlit text colors to be dark & Add Premium Header ──
st.markdown("""
<style>
    # /* Hide Streamlit's Deploy button and toolbar */
    # [data-testid="stToolbar"] {
    #     display: none !important;
    # }
    # #MainMenu {
    #     display: none !important;
    # }
    # header[data-testid="stHeader"] {
    #     display: none !important;
    # }
            
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

    /* 🎴 FORM CARD BUTTON STYLING 🎴 */
    .form-card-button {
        background: white !important;
        border: 1px solid #dde3ef !important;
        border-radius: 8px !important;
        padding: 1.5rem !important;
        box-shadow: 0 2px 8px rgba(26, 50, 99, 0.08) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        color: #1a2e55 !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        line-height: 1.3 !important;
        word-break: break-word !important;
        min-height: 140px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .form-card-button:hover {
        border-color: #284b8c !important;
        box-shadow: 0 8px 16px rgba(26, 50, 99, 0.12) !important;
        transform: translateY(-2px) !important;
    }
    
    .form-card-button:focus {
        outline: none !important;
        border-color: #284b8c !important;
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

    /* 🎴 FORM CARDS GRID 🎴 */
    .form-cards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    .form-card {
        background: white;
        border: 1px solid #dde3ef;
        border-radius: 8px;
        padding: 1.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(26, 50, 99, 0.05);
        position: relative;
    }
    .form-card:hover {
        border-color: #284b8c;
        box-shadow: 0 8px 16px rgba(26, 50, 99, 0.12);
        transform: translateY(-2px);
    }
    .form-card.active {
        border-color: #284b8c;
        background: linear-gradient(135deg, #f0f3ff 0%, #f5f8ff 100%);
        border-width: 2px;
    }
    .form-card-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1a2e55;
        margin: 0 0 0.5rem 0;
        word-break: break-word;
        padding-right: 2.5rem;
    }
    .form-card-date {
        font-size: 0.8rem;
        color: #7c8db5;
        margin: 0;
    }
    .form-card-menu {
        position: absolute;
        top: 1rem;
        right: 1rem;
    }
            

/* 📱 RESPONSIVE MEDIA QUERIES 📱 */
    @media screen and (max-width: 768px) {
        .premium-header { padding: 1.5rem 1.2rem !important; }
        .premium-header h1 { font-size: 1.6rem !important; }
        .premium-header p { font-size: 0.9rem !important; }
        .custom-link-card { padding: 0.8rem 1rem !important; }
        .custom-link-url { font-size: 0.85rem !important; }
        .form-cards-grid { grid-template-columns: 1fr; }

        [data-testid="stHorizontalBlock"]:has(button[key*="rename_"]) button {
            padding: 5px !important;
            min-height: 35px !important;
        }
            
        /* 🔥 MOBILE FIX FOR QUESTION TOOLBAR (5-Column Row) 🔥 */
        /* Tina-target natin ang 5 columns na WALANG selectbox para hindi masira yung Filter Bar sa taas */
        div[data-testid="stColumns"]:has(> div:nth-child(5):last-child):not(:has(div[data-baseweb="select"])),
        div[data-testid="stHorizontalBlock"]:has(> div:nth-child(5):last-child):not(:has(div[data-baseweb="select"])) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            align-items: center !important;
            gap: 4px !important;
            padding-bottom: 5px !important;
        }

        /* Tanggalin ang 100% width ni Streamlit sa loob ng columns na 'to */
        div[data-testid="stColumns"]:has(> div:nth-child(5):last-child):not(:has(div[data-baseweb="select"])) > div,
        div[data-testid="stHorizontalBlock"]:has(> div:nth-child(5):last-child):not(:has(div[data-baseweb="select"])) > div {
            min-width: 0 !important;
            width: auto !important;
            flex: 0 0 auto !important; 
        }

        /* 1. Checkbox (Unang Column) -> Hahayaan nating humaba para itulak yung buttons sa kanan */
        div[data-testid="stColumns"]:has(> div:nth-child(5):last-child):not(:has(div[data-baseweb="select"])) > div:nth-child(1),
        div[data-testid="stHorizontalBlock"]:has(> div:nth-child(5):last-child):not(:has(div[data-baseweb="select"])) > div:nth-child(1) {
            flex: 1 1 auto !important;
            padding-top: 10px !important; /* I-align ng konti pababa para pumantay sa buttons */
        }
        
        /* 1. Force the parent container to allow wrapping and row direction */
        div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4):last-child), 
        div[data-testid="stColumns"]:has(> div:nth-child(4):last-child) {
            display: flex !important;
            flex-wrap: wrap !important;
            flex-direction: row !important;
            gap: 10px !important;
        }

        /* 2. KILL STREAMLIT'S DEFAULT 100% WIDTH ON COLUMNS (The Culprit!) */
        div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4):last-child) > div[data-testid="column"], 
        div[data-testid="stColumns"]:has(> div:nth-child(4):last-child) > div[data-testid="column"] {
            min-width: 0 !important; 
            width: auto !important;
        }

        /* 3. FORM NAME BUTTON (Col 2) -> Pop to top row, full width */
        div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4):last-child) > div:nth-child(2),
        div[data-testid="stColumns"]:has(> div:nth-child(4):last-child) > div:nth-child(2) {
            order: 1 !important; 
            flex: 0 0 100% !important; 
            min-width: 100% !important;
            margin-bottom: 5px !important;
        }

        /* 4. CHECKBOX (Col 1) -> Bottom left */
        div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4):last-child) > div:nth-child(1),
        div[data-testid="stColumns"]:has(> div:nth-child(4):last-child) > div:nth-child(1) {
            order: 2 !important;
            flex: 0 0 40px !important; 
            display: flex !important;
            align-items: center !important;
        }

        /* 5. RENAME BUTTON (Col 3) -> Bottom middle */
        div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4):last-child) > div:nth-child(3),
        div[data-testid="stColumns"]:has(> div:nth-child(4):last-child) > div:nth-child(3) {
            order: 3 !important;
            flex: 1 1 auto !important; 
        }

        /* 6. DELETE BUTTON (Col 4) -> Bottom right */
        div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4):last-child) > div:nth-child(4),
        div[data-testid="stColumns"]:has(> div:nth-child(4):last-child) > div:nth-child(4) {
            order: 4 !important;
            flex: 1 1 auto !important; 
        }
    }
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# SUPABASE SETUP & SESSION RECOVERY
# ══════════════════════════════════════════
conn = st.connection("supabase", type=SupabaseConnection)

# Priority 1: Check URL query params (survives reload)
admin_email = None
session_id_from_url = st.query_params.get("session_id")

if session_id_from_url:
    try:
        # Restore user from database using session_id from URL
        result = conn.client.table("active_sessions").select("user_email").eq("session_id", session_id_from_url).execute()
        if result.data:
            admin_email = result.data[0].get("user_email")
            st.session_state.user_email = admin_email
            st.session_state.session_id = session_id_from_url
            st.session_state.logged_in = True
    except Exception:
        pass

# Priority 2: Check session state (cache from previous interaction)
if not admin_email:
    admin_email = st.session_state.get("user_email")
    session_id = st.session_state.get("session_id")
    
    # If we have session_id in state but not email, try to restore from DB
    if session_id and not admin_email:
        try:
            result = conn.client.table("active_sessions").select("user_email").eq("session_id", session_id).execute()
            if result.data:
                admin_email = result.data[0].get("user_email")
                st.session_state.user_email = admin_email
                # Add to URL for future reloads
                st.query_params["session_id"] = session_id
        except Exception:
            pass

# If no email found, redirect to login
if not admin_email:
    st.error("🔒 Please log in to access the form builder.")
    st.stop()

# CRITICAL: Persist session_id in URL so it survives reloads and navigation
if session_id_from_url and "session_id" not in st.query_params:
    st.query_params["session_id"] = session_id_from_url
elif st.session_state.get("session_id") and "session_id" not in st.query_params:
    st.query_params["session_id"] = st.session_state.get("session_id")

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
if "question_just_added" not in st.session_state: st.session_state.question_just_added = False
if "viewing_form_editor" not in st.session_state: st.session_state.viewing_form_editor = False

# ══════════════════════════════════════════
# DB HELPERS
# ══════════════════════════════════════════
@st.cache_data(ttl=300) # Keeps data in memory for 5 mins
def fetch_questions(form_id: str = None, admin_email: str = None):
    if form_id is None:
        return []
    try:
        res = (conn.client.table("form_questions")
               .select("*").eq("admin_email", admin_email).eq("form_id", form_id)
               .order("sort_order").execute())
        return res.data or []
    except Exception:
        return []

def update_question(qid, payload: dict):
    conn.client.table("form_questions").update(payload).eq("id", qid).execute()
    fetch_questions.clear() # Clear cache so UI updates

def delete_question(qid):
    conn.client.table("form_questions").delete().eq("id", qid).execute()
    fetch_questions.clear()

def delete_questions_bulk(qids: list):
    for qid in qids:
        conn.client.table("form_questions").delete().eq("id", qid).execute()
    fetch_questions.clear()

def apply_new_sort_order(ordered_ids: list):
    for new_order, qid in enumerate(ordered_ids, start=1):
        conn.client.table("form_questions").update({"sort_order": new_order}).eq("id", qid).execute()
    fetch_questions.clear()


@st.dialog("Delete this question?")
def dialog_delete_single_question():
    qid = st.session_state.get("_confirm_del_qid")
    qid_str = st.session_state.get("_confirm_del_qid_str") or ""
    if qid is None:
        return
    st.markdown(
        "**This removes the question from your survey builder and from the live form.** \n\n"
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
        f"**Delete {n} question(s)?** \n\n"
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

**Allowed** when you turn on **Mark as demographic:** **Multiple Choice** (one option) or **Multiple Select** (several options, e.g. transport modes).

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
    # Inside dialog_create_form()
    with col1:
        if st.button("Create", type="primary", use_container_width=True):
            if form_title.strip():
                new_form = create_form(admin_email, form_title.strip(), form_desc.strip())
                if new_form:
                    refresh_form_list(admin_email)
                    set_current_form(new_form["form_id"])
                    st.session_state.viewing_form_editor = True
                    # TRIGGER LOADER HERE
                    st.session_state._trigger_transition_loader = True
                    st.session_state._transition_loader_text = f"Opening '{form_title}'..."
                    
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
            st.session_state._selected_gallery_forms.discard(form_id)  # Remove from gallery selection
            st.session_state.viewing_form_editor = False
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
        # Get actual response count from database
        try:
            resp = conn.client.table("form_responses").select("id").eq("form_id", form["form_id"]).execute()
            response_count = len(resp.data) if resp.data else 0
        except:
            response_count = 0
        
        st.markdown(f"- **{form['title']}** ({response_count} response{'s' if response_count != 1 else ''})")
    
    st.markdown("**This cannot be undone.**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Delete All", type="primary", use_container_width=True):
            for form_id in form_ids:
                delete_form_permanently(form_id, admin_email)
            refresh_form_list(admin_email)
            st.session_state.pop("_confirm_delete_multiple_forms", None)
            st.session_state._selected_gallery_forms = set()  # Clear gallery selection
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
    
    # For sample forms, ensure reach_out_contact is populated even if it was empty in the database
    if form_meta.get("title") == "Sentibyahe: System Evaluation Test Form" and not form_meta.get("reach_out_contact"):
        form_meta["reach_out_contact"] = "We'd love your feedback! 💡\n\nThanks for testing Sentibyahe! Now that you've seen how the system processes your response into the five transport categories, it's time to tell us what you think. Please take 2 quick minutes to evaluate the platform's usability, performance, and overall design. Your feedback is crucial to our research.\n\nhttps://docs.google.com/forms/d/e/1FAIpQLSemJsPRgflhlRLTcgEKidMSfyWS6NZCA5m2CvEJUOQ-JPF3vA/viewform?usp=sharing&ouid=104216160606281095977"
except Exception:
    form_meta = {
        "title": "Land Public Transportation Respondent Survey",
        "description": "Please share your honest experience.",
        "include_demographics": False,
        "allow_multiple_responses": True,
        "reach_out_contact": "",
    }

# Check if this is the sample form (first form created on new account)
# Primary check: is_sample_form flag
is_sample_form = bool(form_meta.get("is_sample_form", False))

# Fallback: if title matches, it's the sample form (regardless of number of forms)
if not is_sample_form and form_meta.get("title") == "Sentibyahe: System Evaluation Test Form":
    is_sample_form = True
    form_meta["include_demographics"] = True
    form_meta["include_standard_servqual_questions"] = True

if is_sample_form:
    st.session_state.preview_mode = True  # Force preview mode for sample form

# Only initialize form metadata for non-form-creation flows
# Don't prefill title/description to keep form creation UI clean
if "meta_form_name" not in st.session_state:
    st.session_state.meta_form_name = form_meta.get("title", "") or ""
if "meta_desc" not in st.session_state:
    st.session_state.meta_desc = form_meta.get("description", "") or ""
if "meta_title" not in st.session_state:
    st.session_state.meta_title = form_meta.get("title", "") or ""
st.session_state.meta_reach_out = st.session_state.get("meta_reach_out") or form_meta.get("reach_out_contact") or ""
st.session_state.meta_allow_multi = st.session_state.get("meta_allow_multi", bool(form_meta.get("allow_multiple_responses", True)))
st.session_state.meta_include_demo = st.session_state.get("meta_include_demo", bool(form_meta.get("include_demographics", False)))
st.session_state.meta_include_servqual = st.session_state.get("meta_include_servqual", bool(form_meta.get("include_standard_servqual_questions", True)))

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
        "include_standard_servqual_questions": st.session_state.get(
            "meta_include_servqual", form_meta.get("include_standard_servqual_questions", True)
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
        <h1><svg style="display: inline-block; width: 2.2rem; height: 2.2rem; margin-right: 10px; vertical-align: middle;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>Create Form</h1>
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
    st.session_state.pop("_confirm_delete_multiple_forms", None)
    st.session_state.pop("_confirm_del_qid", None)
    st.session_state.pop("_confirm_del_bulk_ids", None)
    st.session_state.pop("_show_demo_type_dialog", None)
    st.session_state.pop("_clear_all_dialogs", None)

# ══════════════════════════════════════════
# FORM SELECTION MODE vs EDITING MODE
# ══════════════════════════════════════════
# Check if we should show form gallery or editor
available_forms = st.session_state.get("available_forms", [])

# Use flag to determine view mode (not auto-creation)
viewing_editor = st.session_state.viewing_form_editor and current_form_id and len([f for f in available_forms if f["form_id"] == current_form_id]) > 0

# ══════════════════════════════════════════
# FORM GALLERY (Show when not in editor)
# ══════════════════════════════════════════
if not viewing_editor:
    if not available_forms:
        st.warning("🔍 No forms found.")
        fsb1, fsb2 = st.columns(2)
        with fsb1:
            if st.button("➕ Create Your First Form", type="primary", use_container_width=True):
                dialog_create_form()  # 🔥 CALL DIALOG DIRECTLY
        with fsb2:
            st.markdown("")
        st.stop()

    # ── CLEAN "START A NEW FORM" LAYOUT ──
    top_col1, top_col2 = st.columns([4, 1.5], vertical_alignment="center")
    
    with top_col1:
        st.markdown("### ✨ Start a New Form")
        st.markdown("<p style='color: #7c8db5; margin-top: -15px; margin-bottom: 0px;'>Create a brand new blank survey from scratch.</p>", unsafe_allow_html=True)
        
    with top_col2:
        if st.button("➕ Create Blank Form", use_container_width=True, type="primary"):
            dialog_create_form()
            
    st.markdown("---")
    
    # 🔥 FIX 1: Compute selection state dynamically BEFORE rendering the toolbar!
    # This guarantees the count is perfectly synced with the checkboxes.
    # Exclude sample form from selection
    selected_forms = []
    selectable_forms = []
    for idx, form in enumerate(available_forms):
        is_sample = form["title"] == "Sentibyahe: System Evaluation Test Form"
        if not is_sample:
            selectable_forms.append((idx, form))
            chk_key = f"gallery_chk_{form['form_id']}_{idx}"
            if st.session_state.get(chk_key, False):
                selected_forms.append(form["form_id"])
    
    st.session_state._selected_gallery_forms = set(selected_forms)
    n_selected = len(selected_forms)
    all_checked = (n_selected == len(selectable_forms)) and (len(selectable_forms) > 0)
    
    # Header on the left, Bulk selection on the right
    toolbar_left, toolbar_right = st.columns([4, 1.5], vertical_alignment="bottom")
    
    with toolbar_left:
        st.markdown("### 📋 Your Forms")
        
    with toolbar_right:
        # 1. Selection count (Top)
        st.markdown(f"<div style='text-align:right; margin-bottom: 8px;'><span style='font-weight:700; color:#3b5bdb;'>{n_selected}</span> selected</div>", unsafe_allow_html=True)
        
        # 2. Select / Deselect All Button (Middle)
        if st.button("☑ Select All" if not all_checked else "☐ Deselect All", use_container_width=True):
            # 🔥 FIX 2: Updates only selectable (non-sample) forms
            for idx, form in enumerate(available_forms):
                is_sample = form["title"] == "Sentibyahe: System Evaluation Test Form"
                if not is_sample:
                    chk_key = f"gallery_chk_{form['form_id']}_{idx}"
                    st.session_state[chk_key] = not all_checked 
            st.rerun()
            
        # 3. Delete Button (Appears Below when items are selected)
        if n_selected > 0:
            if st.button(f"🗑️ Delete ({n_selected})", use_container_width=True, type="primary"):
                st.session_state._confirm_delete_multiple_forms = list(st.session_state._selected_gallery_forms)
                dialog_delete_multiple_forms_confirmation()

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("")
    
    num_cols = 2
    cols = st.columns(num_cols)
    
    for idx, form in enumerate(available_forms):
        form_id = form["form_id"]
        form_title = form["title"]
        is_sample = form_title == "Sentibyahe: System Evaluation Test Form"

        with cols[idx % num_cols]:
            with st.container(border=True):
                
                # 1. Main Button
                if st.button(f"📄 {form_title}", key=f"form_select_{form_id}_{idx}", use_container_width=True, type="primary"):
                    set_current_form(form_id)
                    st.session_state.viewing_form_editor = True
                    # TRIGGER LOADER HERE
                    st.session_state._trigger_transition_loader = True
                    st.session_state._transition_loader_text = f"Loading Editor..."
                    st.rerun()
                
                # 2. Secondary actions (hidden for sample form)
                if not is_sample:
                    chk_col, rename_col, delete_col = st.columns([1.2, 1, 1], vertical_alignment="center")

                    with chk_col:
                        st.checkbox("Select", key=f"gallery_chk_{form_id}_{idx}")

                    with rename_col:
                        if st.button("✏️", key=f"rename_{form_id}_{idx}", use_container_width=True):
                            st.session_state._rename_form_id = form_id
                            dialog_rename_form()

                    with delete_col:
                        if st.button("🗑️", key=f"delete_{form_id}_{idx}", use_container_width=True):
                            st.session_state._confirm_delete_form_id = form_id
                            dialog_delete_form_confirmation()
    
    st.stop()
# ══════════════════════════════════════════
# FORM EDITOR (Show when editing a form)
# ══════════════════════════════════════════

# Back button and Dashboard button
btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    if st.button("← Back", use_container_width=True):
        st.session_state.viewing_form_editor = False
        # TRIGGER LOADER HERE
        st.session_state._trigger_transition_loader = True
        st.session_state._transition_loader_text = "Returning to Gallery..."
        st.rerun()

with btn_col2:
    if st.button("Sentiment Dashboard", icon=":material/bar_chart:", use_container_width=True):        
        st.session_state._trigger_transition_loader = True
        st.session_state._transition_loader_text = "Loading Dashboard..."
        st.session_state._page_initial_load = False
        st.switch_page("dashboard.py")

# Get current form details and display as title header
current_form = next((f for f in available_forms if f["form_id"] == current_form_id), None)
if current_form:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f0f3ff 0%, #f5f8ff 100%); border-left: 4px solid #284b8c; border-radius: 8px; padding: 1.5rem 2rem; margin-bottom: 2rem;">
        <h2 style="margin: 0; color: #1a2e55; font-size: 1.8rem; font-weight: 700;">{current_form['title']}</h2>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# SURVEY SETTINGS
# ══════════════════════════════════════════
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
    st.text_input("Survey title", key="meta_title", disabled=is_sample_form)
    st.text_area("Description (optional)", key="meta_desc", height=80, placeholder="A few words about what you're asking", disabled=is_sample_form)
    st.text_area(
        "Reach out / Contact",
        key="meta_reach_out",
        height=80,
        placeholder="e.g. Email: research@school.edu · Office: Room 204\n\n(shown on thank-you screen)",
        disabled=is_sample_form,
    )
    
    st.divider()
    
    st.subheader("🎯 Survey Behavior")
    st.toggle(
        "**Allow multiple responses**",
        key="meta_allow_multi",
        help="Uncheck if you want one response per person."
    )
    if not is_sample_form:
        st.toggle(
            "**Include standard profile questions** (age, gender, transport mode, etc)",
            key="meta_include_demo",
            help="Automatically adds demographics section to your form.",
        )
        st.toggle(
            "**Include standard questionnaires** (SERVQUAL evaluation)",
            key="meta_include_servqual",
            help="Includes the standard service quality evaluation questions (locked - cannot be edited).",
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
    
    copy_card_html = f"""
    <div style="background-color: #f0f4f8; border: 1px solid #dde3ef; border-left: 4px solid #1a2e55; border-radius: 6px; padding: 1rem 1.2rem; margin-top: 0.5rem; font-family: 'Source Sans Pro', sans-serif;">
        <div style="font-size: 0.75rem; font-weight: 700; color: #7c8db5; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
            📤 Shareable Link
        </div>
        
        <a href="{shareable_link}" target="_blank" style="font-size: 0.95rem; color: #1a5276; font-weight: 500; text-decoration: none; word-break: break-all; display: block; margin-bottom: 12px; line-height: 1.4;">
            {shareable_link}
        </a>
        
        <div style="display: flex; align-items: center; gap: 10px;">
            <button onclick="copyToClipboard()" style="background-color: white; border: 1px solid #dde3ef; border-radius: 4px; padding: 6px 12px; cursor: pointer; color: #1a2e55; font-weight: 600; font-size: 0.85rem; display: flex; align-items: center; gap: 6px; box-shadow: 0 1px 2px rgba(26, 50, 99, 0.05); transition: all 0.2s ease;">
                📋 Copy Link
            </button>
            <span id="copy-status" style="color: #2a7a3b; font-size: 0.8rem; font-weight: 700; opacity: 0; transition: opacity 0.3s ease;">
                ✓ Copied!
            </span>
        </div>
    </div>

    <script>
    function copyToClipboard() {{
        navigator.clipboard.writeText("{shareable_link}").then(function() {{
            var status = document.getElementById("copy-status");
            status.style.opacity = "1";
            
            // Fade out the success message after 2 seconds
            setTimeout(function() {{
                status.style.opacity = "0";
            }}, 2000);
        }}).catch(function(err) {{
            console.error('Failed to copy: ', err);
        }});
    }}
    </script>
    """

    components.html(copy_card_html, height=160)
    
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

st.markdown("---")

# Get current form details
current_form = next((f for f in available_forms if f["form_id"] == current_form_id), None)

# Fetch questions first
questions = fetch_questions(current_form_id, admin_email)

# ══════════════════════════════════════════
# MANAGE QUESTIONS SECTION
# ══════════════════════════════════════════
if not is_sample_form:
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
            disabled=is_sample_form,
        )
        if st.session_state.get("preview_toggle") is not None:
            st.session_state.preview_mode = st.session_state.get("preview_toggle", False)
else:
    # For sample form, still need to handle preview_toggle to avoid errors
    if st.session_state.get("preview_toggle") is not None:
        st.session_state.preview_mode = st.session_state.get("preview_toggle", False)

# ══════════════════════════════════════════
# ADD NEW QUESTION
# ══════════════════════════════════════════
if not st.session_state.preview_mode and not is_sample_form:
    # Keep expander open if question was just added (for confirmation feedback)
    should_expand = (len(questions) == 0) or st.session_state.get("question_just_added", False)
    with st.expander("➕ Add New Question", expanded=should_expand):
        qa1, qa2 = st.columns([2.5, 1.5])
        with qa1:
            st.markdown("**Question**")
            new_prompt = st.text_input("", placeholder="e.g. How was the driver's behavior?", label_visibility="collapsed")
        with qa2:
            st.markdown("**Type**")
            q_type_options = ["Short Answer", "Paragraph", "Multiple Choice", "Multiple Select", "Rating (Likert)"]
            q_type = st.selectbox(
                "",
                q_type_options,
                label_visibility="collapsed",
            )

        # SERVQUAL dimension tagging (available for ANY question type)
        st.markdown("**SERVQUAL Dimension (optional)**")
        selected_dim = st.selectbox(
            "",
            ["None"] + DIM_KEYS,
            label_visibility="collapsed"
        )
        servqual_dim = None if selected_dim == "None" else selected_dim

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
            if q_type in ("Multiple Choice", "Multiple Select"):
                is_demographic_q = st.checkbox("Mark as demographic", value=False, help="Tag this question's responses to appear in the Demographics chart on the Sentiment Dashboard")
        with opt3:
            enable_sentiment = False
            if q_type in ("Short Answer", "Paragraph"):
                enable_sentiment = st.checkbox("Enable sentiment analysis", value=True, help="Analyze responses for sentiment & SERVQUAL dimension")

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
                    if "new_options_list" in st.session_state:
                        del st.session_state.new_options_list
                    st.session_state.question_just_added = True  # Flag to show success message after reload
                    # Clear cache and force immediate session state update
                    fetch_questions.clear()
                    # Force refresh of questions in session state
                    st.session_state._force_refresh_questions = True
                    st.rerun()
            else:
                st.warning("⚠️ Enter question text first.")
        
        # Show success message if question was just added
        if st.session_state.get("question_just_added"):
            st.success("✅ New question added! It will appear below after you close this form.")
            # Keep flag for one more render cycle to show message, then clear it
            st.session_state.question_just_added = False  # Clear flag

# ══════════════════════════════════════════
# FILTER & DISPLAY
# ══════════════════════════════════════════


# 🔥 ADDED THE FILTER TITLE HERE
st.markdown("#### 🔍 Filter")

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

st.markdown("---")

def passes_filter(q):
    # Exclude locked questions from custom questions list
    if q.get("is_locked"):
        return False
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

if is_sample_form:
    show_demo_block = True  # Always show demo block for sample form
elif st.session_state.preview_mode:
    show_demo_block = form_meta.get("include_demographics", False)
else:
    show_demo_block = st.session_state.get("meta_include_demo", form_meta.get("include_demographics", False))

st.markdown("<div style='margin-bottom:1rem'></div>", unsafe_allow_html=True)

# Set up the header text for questions section
visible_questions = [q for q in questions if passes_filter(q)]
filtered = len(visible_questions) < len(questions)
filter_note = f"(filtered: {len(visible_questions)}/{len(questions)})" if filtered else f"({len(questions)} total)"

if is_sample_form:
    header_text = "📋 Your Questions"
elif st.session_state.preview_mode:
    header_text = "📋 Respondent Preview"
else:
    header_text = f"📋 Your Questions {filter_note}"

st.markdown(f"### {header_text}")

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
    {"prompt": "1. Age / Edad", "q_type": "Multiple Choice", "options": ["Below / Mababa sa 18", "18-25", "26-35", "36-45", "46-55", "Above / Mataas sa 55"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    {"prompt": "2. Gender / Kasarian", "q_type": "Multiple Choice", "options": ["Male (Lalaki)", "Female (Babae)", "Prefer not to say (Mas pinipiling huwag sabihin)"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    {"prompt": "3. Occupational Status / Katayuan sa Trabaho", "q_type": "Multiple Choice", "options": ["Student (Estudyante)", "Employee / Self-employed (Empleyado / may sariling pinagkikitaan)", "Employer / Business-owner (May-ari ng Negosyo)", "Unemployed (Walang trabaho)"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    {"prompt": "4. Monthly Allowance or Salary / Buwanang Sahod o Allowance", "q_type": "Multiple Choice", "options": ["Below / Mababa sa Php 5,000", "Php 5,001 - 10,000", "Php 10,001 - 20,000", "Php 20,001 - 30,000", "Php 30,001 - 40,000", "Php 40,001 - 50,000", "Above / Mataas sa Php 50,001"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    {"prompt": "5. Frequency of Commuting / Gaano ka kadalas sumakay sa isang linggo?", "q_type": "Multiple Choice", "options": ["Once a week (Isang beses sa isang linggo)", "2-3 times a week (2-3 beses sa isang linggo)", "4-5 times a week (4-5 beses sa isang linggo)", "Everyday (Araw-araw)"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    {"prompt": "6. Most frequently used transport mode / Pinakamadalas na sinasakyan", "q_type": "Multiple Choice", "options": ["Traditional Jeepney (Tradisyunal na Jeepney)", "Modern Jeepney (Modernong Jeepney)", "Bus", "Taxi (Taksi)", "UV Express", "Ride-hailing services (e.g., Angkas, Grab, Move It)", "LRT-1", "LRT-2", "MRT-3", "Others"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
]

STANDARD_SERVQUAL_QUESTIONS = [
    {"prompt": "DIMENSION 1: TANGIBLES (Physical appearance and comfort)\n\nQuestion 1: How would you describe the physical condition and cleanliness of the vehicle or train you rode, as well as the seating comfort? (Paano mo ilalarawan ang pisikal na kondisyon at kalinisan ng sasakyan o tren na sinakyan mo, pati na rin ang komportableng pag-upo?)", "q_type": "Rating (Likert)", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": False, "servqual_dimension": "Tangibles", "is_locked": True, "scale_max": 5, "scale_label_low": "Poor", "scale_label_high": "Excellent"},
    {"prompt": "Question 2: What can you say about the air ventilation and temperature (coldness or heat) inside the vehicle? (Ano ang masasabi mo sa bentilasyon ng hangin at temperatura (lamig o init) sa loob ng sasakyan?)", "q_type": "Rating (Likert)", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": False, "servqual_dimension": "Tangibles", "is_locked": True, "scale_max": 5, "scale_label_low": "Poor", "scale_label_high": "Excellent"},
    {"prompt": "DIMENSION 2: RELIABILITY (Dependability and smooth service)\n\nQuestion 3: What is your experience regarding the vehicle's reliability, specifically in avoiding mechanical failures mid-journey and adhering to the correct passenger capacity? (Ano ang karanasan mo pagdating sa pag-iwas ng sasakyan sa pagtirik o pagkasira sa gitna ng byahe, pati na rin sa pagsunod sa tamang bilang ng pasahero?)", "q_type": "Rating (Likert)", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": False, "servqual_dimension": "Reliability", "is_locked": True, "scale_max": 5, "scale_label_low": "Poor", "scale_label_high": "Excellent"},
    {"prompt": "Question 4: What are your thoughts on the fare price and whether the driver or conductor gives the exact change? (Ano ang pananaw mo sa presyo ng pamasahe at sa pagbibigay ng tamang sukli ng driver o konduktor?)", "q_type": "Rating (Likert)", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": False, "servqual_dimension": "Reliability", "is_locked": True, "scale_max": 5, "scale_label_low": "Poor", "scale_label_high": "Excellent"},
    {"prompt": "DIMENSION 3: RESPONSIVENESS (Promptness and communication)\n\nQuestion 5: What can you say about the promptness or speed of the trip in helping you reach your destination on time? (Ano ang masasabi mo sa bilis ng biyahe upang makarating ka sa tamang oras sa iyong destinasyon?)", "q_type": "Rating (Likert)", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": False, "servqual_dimension": "Responsiveness", "is_locked": True, "scale_max": 5, "scale_label_low": "Poor", "scale_label_high": "Excellent"},
    {"prompt": "Question 6: How would you describe the attentiveness of the driver or conductor when communicating or when you need to alight at the correct drop-off point? (Paano mo ilalarawan ang pagiging alisto ng driver o konduktor kapag kinakausap o kapag kailangan mo nang bumaba sa tamang babaan?)", "q_type": "Rating (Likert)", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": False, "servqual_dimension": "Responsiveness", "is_locked": True, "scale_max": 5, "scale_label_low": "Poor", "scale_label_high": "Excellent"},
    {"prompt": "DIMENSION 4: ASSURANCE (Safety, security, and competence)\n\nQuestion 7: What can you say about the carefulness of the driver in driving and their compliance with traffic laws? (Ano ang masasabi mo sa pagiging maingat ng driver sa pagmamaneho at sa pagsunod niya sa mga batas trapiko?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Assurance", "is_locked": True},
    {"prompt": "Question 8: How would you describe your sense of safety or feeling \"safe from crimes\" (such as theft or harassment) inside the vehicle? (Paano mo ilalarawan ang iyong pakiramdam ng kaligtasan o pagiging ligtas sa mga krimen (tulad ng pagnanakaw o harassment) sa loob ng sasakyan?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Assurance", "is_locked": True},
    {"prompt": "DIMENSION 5: EMPATHY (Caring and individualized attention)\n\nQuestion 9: What can you say about the politeness, behavior, and care shown by the driver or conductor towards the passengers? (Ano ang masasabi mo sa pagiging magalang, pag-uugali, at pag-aalaga ng driver o konduktor sa mga pasahero?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Empathy", "is_locked": True},
    {"prompt": "Question 10: How would you evaluate the assistance provided and the designated areas for those in need, such as Senior Citizens, PWDs, and pregnant women? (Paano mo susuriin ang ibinibigay na tulong at mga nakalaang pwesto para sa mga nangangailangan tulad ng Senior Citizens, PWDs, at mga buntis?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Empathy", "is_locked": True},
    {"prompt": "Additional Comments or Suggestions / Karagdagang Komento o Mungkahi", "q_type": "Paragraph", "options": [], "is_required": False, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": None, "is_locked": True},
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

    # 🔥 FIX: Tinanggal ang heavy solid borders para bumagay sa st.container natin
    border_style = "2px dashed #b0bcd8" if is_locked else "none"
    bg_style = "#fafbfc" if is_locked else "transparent"

    html_str = f'<div style="background:{bg_style};border:{border_style};border-radius:8px;padding:8px 4px;width:100%;"><div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;flex-wrap:wrap;"><span style="font-size:11px;font-weight:700;color:#7c8db5;background:#eef1fa;padding:2px 6px;border-radius:4px;">{display_num}</span><span style="font-size:11px;color:#5566a0;background:#f0f3ff;padding:2px 7px;border-radius:4px;margin-right:4px;">{badge}</span>{dim_tag}{demo_tag}</div><div style="font-size:14px;font-weight:600;color:#1a2e55;line-height:1.4;word-break:break-word;">{prompt}{req_star}</div>{extra}</div>'
    
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
        if not is_sample_form:
            st.markdown("<hr style='margin: 1.5rem 0; border-color: #dde3ef;'>", unsafe_allow_html=True)
    
    # Show locked SERVQUAL questions if enabled in preview mode
    show_servqual = st.session_state.get("meta_include_servqual", form_meta.get("include_standard_servqual_questions", True))
    if show_servqual:
        if not is_sample_form:
            st.markdown("<hr style='margin: 1.5rem 0; border-color: #dde3ef;'>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.85rem; color:var(--steel); font-weight:600; margin-bottom: 0.5rem;'>Standard SERVQUAL Evaluation Questions</p>", unsafe_allow_html=True)
        for i, sq in enumerate(STANDARD_SERVQUAL_QUESTIONS):
            q_num = len(STANDARD_DEMO_QUESTIONS) + i + 1 if show_demo_block else i + 1
            st.markdown(get_card_html(i, sq, q_num_label=f"Q{q_num}", is_locked=True), unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
            
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
        if not is_sample_form:
            st.markdown("<hr style='margin: 1.5rem 0; border-color: #dde3ef;'>", unsafe_allow_html=True)

    # Show locked SERVQUAL questions if enabled
    show_servqual = st.session_state.get("meta_include_servqual", form_meta.get("include_standard_servqual_questions", True))
    if show_servqual and not filtered:
        if not is_sample_form:
            st.markdown("<hr style='margin: 1.5rem 0; border-color: #dde3ef;'>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.85rem; color:var(--steel); font-weight:600; margin-bottom: 0.5rem;'>Standard SERVQUAL Evaluation Questions</p>", unsafe_allow_html=True)
        for i, sq in enumerate(STANDARD_SERVQUAL_QUESTIONS):
            q_num = len(STANDARD_DEMO_QUESTIONS) + i + 1 if show_demo_block else i + 1
            st.markdown(get_card_html(i, sq, q_num_label=f"Q{q_num}", is_locked=True), unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:0.8rem;'></div>", unsafe_allow_html=True)
        if not is_sample_form:
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
                # 🔥 WRAP THE WHOLE QUESTION IN A NATIVE CARD CONTAINER
                with st.container(border=True):
                    
                    st.markdown(get_card_html(idx, q, q_num_label=q_num_label), unsafe_allow_html=True)
                    
                    # Linya na naghihiwalay sa question at sa toolbar buttons
                    st.markdown("<hr style='margin: 1rem 0 0.8rem 0; border-color: #dde3ef;'>", unsafe_allow_html=True)
                    
                    # NATIVE BUTTONS COLUMN LAYOUT (Inayos natin para magmukhang toolbar!)
                    chk_col, up_col, down_col, edit_col, del_col = st.columns([2.5, 0.8, 0.8, 1, 1], vertical_alignment="center")

                    with chk_col:
                        checked = st.checkbox("Select", value=is_checked, key=f"chk_{qid_str}")
                        if checked and not is_checked:
                            st.session_state.selected_ids.add(qid_str)
                            st.rerun()
                        elif not checked and is_checked:
                            st.session_state.selected_ids.discard(qid_str)
                            st.rerun()

                    with up_col:
                        if st.button("⬆️", key=f"up_{qid_str}", help="Move Up", disabled=filtered or idx == 0 or q.get("is_locked"), use_container_width=True):
                            move_question_order(visible_questions, idx, "up")

                    with down_col:
                        if st.button("⬇️", key=f"down_{qid_str}", help="Move Down", disabled=filtered or idx == len(visible_questions) - 1 or q.get("is_locked"), use_container_width=True):
                            move_question_order(visible_questions, idx, "down")

                    with edit_col:
                        if st.button("✏️", key=f"edit_btn_{qid_str}", use_container_width=True, help="Edit", disabled=q.get("is_locked")):
                            st.session_state.editing_id = qid_str
                            st.rerun()

                    with del_col:
                        if st.button("🗑️", key=f"del_btn_{qid_str}", use_container_width=True, help="Delete", disabled=q.get("is_locked")):
                            st.session_state._confirm_del_qid = q["id"]
                            st.session_state._confirm_del_qid_str = qid_str

            else:
                # Pag ine-edit ang question, nakapaloob rin sa Card para pareho ang hitsura
                with st.container(border=True):
                    st.markdown(f"**✏️ Editing {q_num_label}**")
                    
                    ec1, ec2 = st.columns([3, 2])
                    with ec1:
                        e_prompt = st.text_input("Edit question", value=q["prompt"], key=f"ep_{qid_str}")
                    with ec2:
                        e_dim_choices = ["None"] + DIM_KEYS
                        e_dim = st.selectbox("Dimension", e_dim_choices, index=e_dim_choices.index(q["servqual_dimension"]) if q.get("servqual_dimension") in e_dim_choices else 0, key=f"ed_{qid_str}")
                    
                    # Determine available question types
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
                            help="Tag this question's responses to appear in the Demographics chart on the Sentiment Dashboard",
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

# ══════════════════════════════════════════
# DIALOG TRIGGERS (when editing a form)
# ══════════════════════════════════════════
# Trigger dialogs (only one at a time via if/elif)
if st.session_state.get("_show_demo_type_dialog"):
    dialog_demographic_invalid_type()
elif st.session_state.get("_confirm_del_qid") is not None:
    dialog_delete_single_question()
elif st.session_state.get("_confirm_del_bulk_ids"):
    dialog_delete_bulk_questions()