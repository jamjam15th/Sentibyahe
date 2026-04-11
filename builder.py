# form_builder.py
import hashlib
import streamlit as st
from st_supabase_connection import SupabaseConnection

from servqual_utils import DIM_KEYS
from components import inject_css, section_head, render_dimension_cards

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
public_id   = hashlib.md5(admin_email.encode()).hexdigest()[:12]

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

# ══════════════════════════════════════════
# DB HELPERS
# ══════════════════════════════════════════
def fetch_questions():
    try:
        res = (conn.client.table("form_questions")
               .select("*").eq("admin_email", admin_email)
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


# ══════════════════════════════════════════
# HEADER & METADATA
# ══════════════════════════════════════════
try:
    meta_req  = conn.client.table("form_meta").select("*").eq("admin_email", admin_email).limit(1).execute()
    form_meta = meta_req.data[0] if meta_req.data else {
        "title": "Land public transportation respondent survey",
        "description": "Please share your honest experience.",
        "include_demographics": False,
        "allow_multiple_responses": True,
        "reach_out_contact": "",
    }
except Exception:
    form_meta = {
        "title": "Land public transportation respondent survey",
        "description": "Please share your honest experience.",
        "include_demographics": False,
        "allow_multiple_responses": True,
        "reach_out_contact": "",
    }

_meta_init_flag = f"_builder_meta_ss_{public_id}"
if _meta_init_flag not in st.session_state:
    st.session_state.meta_title = form_meta.get("title", "") or ""
    st.session_state.meta_desc = form_meta.get("description", "") or ""
    st.session_state.meta_reach_out = form_meta.get("reach_out_contact") or ""
    st.session_state.meta_allow_multi = bool(form_meta.get("allow_multiple_responses", True))
    st.session_state.meta_include_demo = bool(form_meta.get("include_demographics", False))
    st.session_state[_meta_init_flag] = True

def update_meta():
    payload = {
        "admin_email": admin_email,
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
        conn.client.table("form_meta").upsert(payload, on_conflict="admin_email").execute()
        st.session_state.pop("form_meta_migration_needed", None)
        st.session_state.pop("form_meta_reach_out_migration_needed", None)
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
            conn.client.table("form_meta").upsert(payload, on_conflict="admin_email").execute()
        else:
            raise

st.markdown("""
<div class="premium-header">
    <div>
        <h1>🛠️ Form Builder</h1>
        <p>Design your land public transportation respondent survey and manage question logic.</p>
    </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.get("form_meta_migration_needed"):
    st.error(
        "Database column `allow_multiple_responses` is missing on `form_meta`. "
        "Run the SQL in `sql/add_allow_multiple_responses_to_form_meta.sql` "
        "(Supabase → SQL Editor), then refresh this page. "
        "Other form settings still save; this toggle will work after the migration."
    )

if st.session_state.get("form_meta_reach_out_migration_needed"):
    st.error(
        "Database column `reach_out_contact` is missing on `form_meta`. "
        "Run the SQL in `sql/add_reach_out_contact_to_form_meta.sql` "
        "(Supabase → SQL Editor), then refresh this page."
    )

col_settings, col_share = st.columns([1.14, 0.86], gap="large")

with col_settings:
    st.markdown("##### Survey copy & behavior")
    st.caption("Changes apply after **Save survey settings**.")
    st.text_input("Survey title", key="meta_title")
    st.text_area("Survey description", key="meta_desc", height=72)
    st.text_area(
        "Reach out / contact (thank-you screen)",
        key="meta_reach_out",
        placeholder="e.g. Email: research@school.edu · Office: Room 204",
        height=76,
        help="Optional. Shown after someone submits.",
    )
    st.toggle(
        "Allow multiple responses from the same user/session",
        key="meta_allow_multi",
    )
    if st.button("💾 Save survey settings", type="primary"):
        update_meta()
        st.success("Survey settings saved.")
    st.checkbox(
        "Include standard respondent profile (age, gender, occupation, transport, commute frequency)",
        key="meta_include_demo",
    )
    st.caption(
        "Turn this off if you only use **your own** questions marked as demographic below. "
        "Either way, click **Save survey settings** after editing."
    )

with col_share:
    st.markdown("##### Share & preview")
    st.markdown(
        f"""
        <div class="custom-link-card" style="margin-top:0;">
          <div class="custom-link-label">🔗 YOUR SURVEY LINK</div>
          <a class="custom-link-url" href="{shareable_link}" target="_blank">{shareable_link}</a>
          <div class="custom-link-hint">Copy and send to respondents.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.preview_mode = st.toggle(
        "👁 Respondent preview mode",
        value=st.session_state.preview_mode,
    )
    if st.session_state.preview_mode:
        st.markdown(
            '<div style="background:#eef1fa;color:#3b5bdb;padding:10px;border-radius:6px;font-weight:700;text-align:center;margin-top:10px;">'
            "Preview — this is how respondents see the form</div>",
            unsafe_allow_html=True,
        )

st.markdown('<div style="height:1.1rem"></div>', unsafe_allow_html=True)
questions = fetch_questions()

# ══════════════════════════════════════════
# ADD NEW QUESTION
# ══════════════════════════════════════════
if not st.session_state.preview_mode:
    with st.expander("➕ Add Question", expanded=True): 

        c1, c2 = st.columns([3, 2])
        with c1:
            new_prompt = st.text_input("Question text", placeholder="e.g. How was the driver's behavior?")
        with c2:
            q_type = st.selectbox(
                "Question type",
                ["Short Answer", "Paragraph", "Multiple Choice", "Multiple Select", "Rating (Likert)"],
            )

        new_options, new_scale_max, new_scale_label_low, new_scale_label_high = [], 5, "", ""

        if q_type in ("Multiple Choice", "Multiple Select"):
            opts_raw = st.text_input("Options (comma-separated)", placeholder="e.g. Mabuti, Okay, Masama")
            if opts_raw:
                new_options = [o.strip() for o in opts_raw.split(",") if o.strip()]

        if q_type == "Rating (Likert)":
            st.markdown("**Likert Scale Settings**")
            sc1, sc2, sc3 = st.columns([1, 2, 2])
            with sc1:
                new_scale_max = st.number_input("Points (max)", min_value=2, max_value=10, value=5, step=1)
            with sc2:
                new_scale_label_low = st.text_input("Label for 1 (lowest)", placeholder="e.g. Strongly Disagree")
            with sc3:
                new_scale_label_high = st.text_input(f"Label for {int(new_scale_max)} (highest)", placeholder="e.g. Strongly Agree")

        c3, c4 = st.columns(2)
        with c3:
            selected_dim = st.selectbox("SERVQUAL dimension", ["None"] + DIM_KEYS)
            servqual_dim = None if selected_dim == "None" else selected_dim
        with c4:
            st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
            is_required = st.checkbox("Required question", value=True)
        is_demographic_q = st.checkbox(
            "Mark as demographic (saved with profile data for the Demographics tab)",
            value=False,
            key="add_q_is_demo",
            help="Use if you skip the standard respondent profile and ask your own profile fields, or to add extra items (e.g. barangay, income bracket).",
        )

        st.caption(
            "Saving adds this question to your **live survey link** and to the **dashboard** for **new** responses only. "
            "If you delete a question later, old rows stay in the database but charts follow **current** questions."
        )
        st.markdown("<div style='margin-top:.5rem'></div>", unsafe_allow_html=True)
        if st.button("💾 Save question to form", use_container_width=True, type="primary"):
            if new_prompt.strip():
                if q_type in ("Multiple Choice", "Multiple Select") and not new_options:
                    st.warning("Add at least one option for this question type.")
                elif q_type == "Multiple Select" and len(new_options) < 2:
                    st.warning("Multiple select works best with two or more options.")
                else:
                    max_order = max((q.get("sort_order") or 0 for q in questions), default=0)
                    payload = {
                        "admin_email": admin_email, "public_id": public_id,
                        "prompt": new_prompt.strip(), "q_type": q_type,
                        "options": new_options, "is_required": is_required,
                        "is_demographic": bool(is_demographic_q),
                        "servqual_dimension": servqual_dim,
                        "sort_order": max_order + 1,
                    }
                    if q_type == "Rating (Likert)":
                        payload["scale_max"]        = int(new_scale_max)
                        payload["scale_label_low"]  = new_scale_label_low.strip() or None
                        payload["scale_label_high"] = new_scale_label_high.strip() or None
                    conn.client.table("form_questions").insert(payload).execute()
                    st.success("Question saved to your form.")
                    st.rerun()
            else:
                st.warning("⚠️ Please enter a question first.")

    with st.expander("ℹ️ What is SERVQUAL?"):
        render_dimension_cards()

# ══════════════════════════════════════════
# FILTER BAR
# ══════════════════════════════════════════
with st.expander("🔍 Filter questions", expanded=False):
    fa, fb, fc, fd = st.columns(4)
    with fa:
        st.session_state.filter_dim = st.selectbox(
            "By dimension", ["All"] + DIM_KEYS + ["General / Demographic"], key="sel_fdim"
        )
    with fb:
        st.session_state.filter_type = st.selectbox(
            "By type",
            ["All", "Short Answer", "Paragraph", "Multiple Choice", "Multiple Select", "Rating (Likert)"],
            key="sel_ftype",
        )
    with fc:
        st.session_state.filter_req = st.selectbox("By required", ["All", "Required", "Optional"], key="sel_freq")
    with fd:
        st.session_state.filter_demo = st.selectbox(
            "By tag",
            ["All", "Demographic only", "Not demographic"],
            key="sel_fdemo",
        )

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
filter_note = f" (filtered: {len(visible_questions)} of {len(questions)})" if filtered else f" · {len(questions)} total"

# ══════════════════════════════════════════
# QUESTIONS LIST & DISPLAY
# ══════════════════════════════════════════
section_head("👁 Respondent preview" if st.session_state.preview_mode else "Your Form", right=filter_note)

if st.session_state.preview_mode:
    show_demo_block = form_meta.get("include_demographics", False)
else:
    show_demo_block = st.session_state.get("meta_include_demo", form_meta.get("include_demographics", False))
st.markdown("<div style='margin-bottom:1rem'></div>", unsafe_allow_html=True)

LPT_TRANSPORT_MODE_OPTIONS = [
    "Jeepney",
    "Modern jeepney / E-jeep",
    "Ordinary bus",
    "Air-conditioned bus",
    "UV Express",
    "Van pool (UV-style)",
    "Tricycle",
    "Motorcycle taxi (habal-habal)",
    "Train (MRT / LRT / PNR)",
    "Taxi",
    "TNVS (Grab, etc.)",
    "Ferry / boat",
    "Walking / cycling",
    "Company or school service",
    "Private car (as passenger)",
    "Other",
]

STANDARD_DEMO_QUESTIONS = [
    {"prompt": "What is your age bracket?", "q_type": "Multiple Choice", "options": ["18-24", "25-34", "35-44", "45-54", "55 and above"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    {"prompt": "What is your gender?", "q_type": "Multiple Choice", "options": ["Male", "Female", "Prefer not to say"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    {"prompt": "What is your primary occupation?", "q_type": "Multiple Choice", "options": ["Student", "Employed", "Self-employed", "Unemployed", "Retired"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    {
        "prompt": "Which land public transportation modes do you usually use? (Select all that apply)",
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
                        st.session_state.selected_ids |= all_visible_ids
                    else:
                        st.session_state.selected_ids -= all_visible_ids
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
                        type_opts = ["Short Answer", "Paragraph", "Multiple Choice", "Multiple Select", "Rating (Likert)"]
                        cur_type  = q["q_type"] if q["q_type"] in type_opts else "Rating (Likert)"
                        e_type    = st.selectbox("Type", type_opts, index=type_opts.index(cur_type), key=f"et_{qid_str}")
                        e_dim_choices = ["None"] + DIM_KEYS
                        e_dim = st.selectbox("Dimension", e_dim_choices, index=e_dim_choices.index(q["servqual_dimension"]) if q.get("servqual_dimension") in e_dim_choices else 0, key=f"ed_{qid_str}")

                    e_req = st.checkbox("Required", value=bool(q.get("is_required")), key=f"er_{qid_str}")
                    e_demo = st.checkbox(
                        "Mark as demographic",
                        value=bool(q.get("is_demographic")),
                        key=f"edemo_{qid_str}",
                        help="Saves answers with profile data for the Demographics dashboard tab.",
                    )
                    e_opts_raw = ""
                    if e_type in ("Multiple Choice", "Multiple Select"):
                        e_opts_raw = st.text_input("Options (comma-separated)", value=", ".join(q.get("options") or []), key=f"eo_{qid_str}")

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
                                "options":            [o.strip() for o in e_opts_raw.split(",") if o.strip()] if e_opts_raw else [],
                                "is_required":        e_req,
                                "is_demographic":     bool(e_demo),
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
                            st.session_state.editing_id = None
                            st.rerun()
                    with cn_col:
                        if st.button("✕ Cancel", key=f"cancel_{qid_str}"):
                            st.session_state.editing_id = None
                            st.rerun()

            st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)

        if st.session_state.get("_confirm_del_qid") is not None:
            dialog_delete_single_question()
        if st.session_state.get("_confirm_del_bulk_ids"):
            dialog_delete_bulk_questions()