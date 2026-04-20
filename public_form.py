import hashlib
import html
import uuid
import re
import streamlit as st
from st_supabase_connection import SupabaseConnection
from forms import get_form, fetch_active_forms

st.set_page_config(
    initial_sidebar_state="collapsed",
    page_title="Take Survey — Land public transportation",
    page_icon="🚌",
    layout="centered",
)

loading_screen = st.empty()

# Must go BEFORE Supabase connections and main CSS
st.markdown("""
<style>
    /* Hide Streamlit's Deploy button and toolbar */
    # [data-testid="stToolbar"] {
    #     display: none !important;
    # }
    # #MainMenu {
    #     display: none !important;
    # }
    # header[data-testid="stHeader"] {
    #     display: none !important;
    # }

    /* 1. KEEP SIDEBAR ON TOP OF LOADER */
    [data-testid="stSidebar"], 
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 999999999 !important; /* Highest priority */
    }

    /* 2. COMPLETELY HIDE THE APP ROOT */
    /* visibility: hidden is bulletproof against React hydration overrides */
    .stApp [data-testid="stAppViewBlockContainer"] {
        visibility: hidden !important;
        animation: snapVisible 0.1s forwards 1s !important; /* 2.5 seconds wait */
    }

    /* 3. OVERLAY THAT COVERS EVERYTHING ELSE */
    #nuclear-loader {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: #f0f4f8; /* Matched to your app background */
        z-index: 999999998; /* Exactly one layer BELOW the sidebar */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        animation: fadeOutNuclear 0.4s ease-out 1s forwards; /* Matches the 2.5s wait */
    }

    .spinner {
        border: 4px solid #ffffff;
        border-top: 4px solid #1a2e55;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 0.8s linear infinite;
        margin-bottom: 15px;
    }

    .loading-text {
        color: #1a2e55;
        font-weight: 600;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
    }

    /* 4. KEYFRAMES */
    @keyframes snapVisible {
        to { visibility: visible !important; }
    }

    @keyframes fadeOutNuclear {
        0% { opacity: 1; visibility: visible; }
        100% { opacity: 0; visibility: hidden; display: none; }
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>

<div id="nuclear-loader">
    <div class="spinner"></div>
    <div class="loading-text">Loading Form...</div>
</div>
""", unsafe_allow_html=True)


st.html("""
    <style>
    /* Use a partial match selector to target all keys starting with 'q_card_' */
    div[class*="st-key-q_card_"] {
        background: #fff;
        border: none;
        border-radius: 12px;
        padding: 1.8rem 2rem;
        margin-bottom: 1rem;
    }
    </style>
""")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Mulish:wght@300;400;500;600;700&display=swap');

:root {
  --gold:   rgb(255, 197, 112);
  --sand:   rgb(239, 210, 176);
  --steel:  rgb(84, 119, 146);
  --navy:   rgb(26, 50, 99);
  --navydk: rgb(18, 34, 68);
  --off:    #f0f4f8;
  --muted:  rgb(120, 148, 172);
  --bdr:    rgba(84,119,146,0.25);
  --card:   #ffffff;
}

*, *::before, *::after { box-sizing: border-box; }
html, body, p, div, span, a, button, label, input, textarea, select {
  font-family: 'Mulish', sans-serif !important;
}

/* Kept header and stToolbar visible to ensure interface accessibility */
#MainMenu, footer,
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: var(--off) !important; }

/* FADE-IN ANIMATION TO PREVENT FOUC */
.block-container {
  max-width: 760px !important;
  padding: 3rem 1.5rem 5rem !important;
  opacity: 0;
  animation: fadeIn 0.6s ease-in-out forwards;
  animation-delay: 0.1s;
}

@keyframes fadeIn {
  0% { opacity: 0; }
  100% { opacity: 1; }
}

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: var(--off) !important; }

.block-container {
  max-width: 760px !important;
  padding: 3rem 1.5rem 5rem !important;
}

/* ── HEADER CARD ── */
.gf-header {
  background: var(--card);
  border-radius: 12px;
  border: 1px solid var(--bdr);
  border-top: 12px solid var(--navy);
  padding: 2.5rem 2.4rem 2rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 6px rgba(26,50,99,0.04);
}
.gf-header .badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(26,50,99,0.07); border-radius: 999px;
  padding: .25rem .8rem; margin-bottom: 1.2rem;
  font-size: .65rem; font-weight: 700; letter-spacing: .12em;
  text-transform: uppercase; color: var(--navy);
}

/* ── VERTICAL RADIO (Multiple Choice) ── */
[data-testid="stRadio"] div[aria-orientation="vertical"] label div:first-child {
    border-left: none !important;
}
[data-testid="stRadio"] div[aria-orientation="vertical"] label p {
    font-size: .95rem !important; color: var(--steel) !important;
    margin-left: 8px !important;
}
[data-testid="stRadio"] div[aria-orientation="vertical"] label:has(input:checked) p {
    color: var(--navy) !important; font-weight: 600 !important;
}

# .st-e2 {
#     background-color: var(--navy) !important;
# }

/* ── HORIZONTAL RADIO (Likert Scale Squares) ── */
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] {
    display: flex !important;
    flex-direction: row !important;
    width: 100% !important;
    gap: 12px !important;
    flex-wrap: nowrap !important;
}
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] > label,
[data-testid="stRadio"] div[aria-orientation="horizontal"] > label {
    flex: 1 1 0 !important;
    height: 52px !important;
    min-width: 0 !important;
    background: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    cursor: pointer !important;
    transition: all .15s ease !important;
    position: relative !important;
}
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] > label > div:first-child,
[data-testid="stRadio"] div[aria-orientation="horizontal"] > label > div:first-child {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
    pointer-events: none !important;
}
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] > label p,
[data-testid="stRadio"] div[aria-orientation="horizontal"] > label p {
    color: #2f4fd1 !important;
    font-weight: 600 !important;
    font-size: .98rem !important;
    margin: 0 !important;
    padding: 0 !important;
    text-align: center !important;
    line-height: 1 !important;
}
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] > label:hover,
[data-testid="stRadio"] div[aria-orientation="horizontal"] > label:hover {
    border-color: #9fb2dc !important;
    background: #f8faff !important;
}
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] > label:has(input:checked),
[data-testid="stRadio"] div[aria-orientation="horizontal"] > label:has(input:checked) {
    border-color: #2f4fd1 !important;
    background: #eef3ff !important;
    box-shadow: 0 0 0 1px #2f4fd1 !important;
}

/* ── INPUTS ── */
/* 1. Strip the default Streamlit wrapper borders and glow */
[data-testid="stTextInput"] div[data-baseweb="base-input"],
[data-testid="stTextArea"] div[data-baseweb="textarea"] {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    border-radius: 10px !important;
}

[data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within,
[data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within {
    border: none !important;
    box-shadow: none !important;
    border-radius: 10px !important;
}

/* 2. Apply our custom bottom border directly to the input elements */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    border: 1px solid rgba(84,119,146,0.35) !important;
    border-radius: 0 !important;
    background: transparent !important;
    transition: border-color 0.2s ease !important;
    border-radius: 10px !important;
}

/* 3. The clean Blue Focus State */
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border: 1px solid var(--navy) !important; 
    box-shadow: none !important; 
    outline: none !important;
    border-radius: 10px !important;
}

/* This applies the blue color and strips away Streamlit's default red glow when typing */
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-bottom: 1px solid var(--navy) !important; 
  box-shadow: none !important; 
  outline: none !important;
}
            
/* ── SUBMIT BUTTON ── */
div.stFormSubmitButton > button {
  background: var(--navy) !important; color: var(--gold) !important;
  border-radius: 6px !important; padding: .65rem 2.2rem !important;
}

.st-emotion-cache-1cl4umz {
    border: none !important;
}

.stElementContainer { width: 100%; }

.st-ai { display: flex; justify-content: space-around; }


/* Remove borders from question containers in public form */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"],
.stContainer { border: none !important; }

.st-emotion-cache-1bcyifm { border: none !important; }

            
</style>
""", unsafe_allow_html=True)

# ── JS: forcibly hide radio circles ──
st.markdown("""
<script>
(function() {
    const hideRadioCircles = () => {
        document.querySelectorAll(
            '[data-testid="stRadio"] div[aria-orientation="horizontal"] > label > div:first-child'
        ).forEach(el => {
            el.style.cssText = [
                'display:none!important',
                'width:0!important',
                'height:0!important',
                'overflow:hidden!important',
                'position:absolute!important',
                'pointer-events:none!important'
            ].join(';');
        });
    };
    hideRadioCircles();
    setTimeout(hideRadioCircles, 100);
    setTimeout(hideRadioCircles, 500);
    const observer = new MutationObserver(() => hideRadioCircles());
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection)

# ── CACHED QUERY HELPERS ──
def _fetch_form_meta(form_id: str):
    """Fetch form metadata by form_id (public access, always fresh)."""
    meta_res = conn.client.table("form_meta").select("*").eq("form_id", form_id).limit(1).execute()
    return meta_res.data[0] if meta_res.data else None

@st.cache_data(ttl=5)  # Short TTL so changes appear within 5 seconds
def _fetch_form_meta_by_email(form_id: str, admin_email: str):
    """Fetch form metadata by form_id and admin_email (preview mode, short cache)."""
    meta_res = conn.client.table("form_meta").select("*").eq("admin_email", admin_email).eq("form_id", form_id).execute()
    return meta_res.data[0] if meta_res.data else None

@st.cache_data(ttl=5)
def _fetch_form_questions(form_id: str, admin_email: str):
    """Fetch form questions (short cache)."""
    q_res = conn.client.table("form_questions").select("*").eq("admin_email", admin_email).eq("form_id", form_id).order("sort_order").execute()
    return q_res.data or []

# ── 1. FETCH LOGIC ──
is_preview = False
target_form_id = None
owner_email = None

if st.session_state.get("logged_in") and st.session_state.get("user_email"):
    owner_email = st.session_state.user_email
    from forms import get_legacy_form_id
    target_form_id = st.query_params.get("form_id") or get_legacy_form_id(owner_email)
    is_preview = True
else:
    query_params = st.query_params
    if "form_id" not in query_params:
        st.error("⚠️ Invalid survey link.")
        st.stop()
    target_form_id = query_params["form_id"]

# Use a spinner so the UI doesn't hang blankly during Supabase queries
with st.spinner("Loading survey data..."):
    try:
        if not is_preview:
            meta_res = conn.client.table("form_meta").select("*").eq("form_id", target_form_id).limit(1).execute()
            form_meta = meta_res.data[0] if meta_res.data else None
            if form_meta:
                owner_email = form_meta.get("admin_email")
            else:
                st.error("⚠️ Survey not found.")
                st.stop()
        else:
            form_meta = _fetch_form_meta_by_email(target_form_id, owner_email)
            if not form_meta:
                form_meta = {
                    "title": "Land public transportation survey",
                    "description": "",
                    "include_demographics": False,
                    "allow_multiple_responses": True,
                    "reach_out_contact": "",
                    "include_standard_servqual_questions": True,
                }
        
        if form_meta.get("title") == "Sentibyahe: System Evaluation Test Form":
            form_meta["include_demographics"] = True
            form_meta["include_standard_servqual_questions"] = True
            if not form_meta.get("reach_out_contact"):
                form_meta["reach_out_contact"] = "We'd love your feedback! 💡\n\nThanks for testing Sentibyahe! Now that you've seen how the system processes your response into the five transport categories, it's time to tell us what you think. Please take 2 quick minutes to evaluate the platform's usability, performance, and overall design. Your feedback is crucial to our research.\n\nhttps://docs.google.com/forms/d/e/1FAIpQLSemJsPRgflhlRLTcgEKidMSfyWS6NZCA5m2CvEJUOQ-JPF3vA/viewform?usp=sharing&ouid=104216160606281095977"
        
        custom_questions = _fetch_form_questions(target_form_id, owner_email)
    except Exception as e:
        st.error(f"⚠️ Could not load survey: {str(e)}")
        st.stop()
# Stable browser-tab id in URL so "one response" survives reload (not just session_state).
client_cid = None
if not is_preview:
    qp = st.query_params
    if "cid" not in qp or not str(qp.get("cid", "")).strip():
        qp["cid"] = str(uuid.uuid4())
        st.rerun()
    client_cid = str(qp["cid"]).strip()


def _already_submitted_for_client(public_id: str, cid: str) -> bool:
    if not cid:
        return False
    try:
        r = conn.client.rpc(
            "has_form_submission",
            {"p_public_id": public_id, "p_client_id": cid},
        ).execute()
        if r.data is True or r.data is False:
            return bool(r.data)
        if isinstance(r.data, list) and len(r.data) > 0:
            return bool(r.data[0])
    except Exception:
        pass
    try:
        chk = (
            conn.client.table("form_responses")
            .select("id")
            .eq("public_id", public_id)
            .eq("client_submission_id", cid)
            .limit(1)
            .execute()
        )
        return bool(chk.data)
    except Exception:
        return False
    
loading_screen.empty()

# ── 2. SCHEMA ──
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
    {"prompt": "How would you describe the physical condition, cleanliness, and overall seating comfort of the vehicle you rode recently? (Paano mo ilalarawan ang pisikal na kondisyon, kalinisan, at pangkalahatang komportableng pag-upo sa sasakyang sinakyan mo kamakailan lang?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Tangibles", "is_locked": True},
    {"prompt": "What can you say about the air ventilation, temperature, and general atmosphere inside the vehicle? (Ano ang masasabi mo sa bentilasyon ng hangin, temperatura, at pangkalahatang kapaligiran sa loob ng sasakyan?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Tangibles", "is_locked": True},
    {"prompt": "How would you describe the overall reliability and operation of the vehicle during your entire trip? (Paano mo ilalarawan ang pangkalahatang pagiging maaasahan at maayos na takbo ng sasakyan sa buong biyahe mo?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Reliability", "is_locked": True},
    {"prompt": "What are your thoughts on the affordability of the fare and how your payment and change were handled by the driver/conductor? (Ano ang iyong pananaw sa halaga ng pamasahe at kung paano inasikaso ng drayber/konduktor ang iyong ibinayad at sukli?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Reliability", "is_locked": True},
    {"prompt": "How would you describe your experience regarding the travel time and the promptness of the ride in reaching your destination? (Paano mo ilalarawan ang iyong karanasan patungkol sa tagal ng biyahe at ang pagiging maagap ng sasakyan patungo sa iyong destinasyon?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Responsiveness", "is_locked": True},
    {"prompt": "What can you say about the attentiveness of the driver or conductor when passengers needed to get off or communicate their drop-off points? (Ano ang masasabi mo sa pagiging alisto ng driver o konduktor kapag kailangan nang bumaba o makipag-usap ng mga pasahero para sa kanilang bababaan?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Responsiveness", "is_locked": True},
    {"prompt": "What are your thoughts on how the driver navigated the road and followed traffic rules during your trip? (Ano ang iyong pananaw sa kung paano nagmaneho at sumunod sa batas trapiko ang driver sa iyong biyahe?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Assurance", "is_locked": True},
    {"prompt": "How would you describe your overall sense of safety and security against incidents like theft or harassment while inside the vehicle? (Paano mo ilalarawan ang iyong pangkalahatang pakiramdam ng kaligtasan at seguridad laban sa mga insidente tulad ng pagnanakaw o harassment habang nasa loob ng sasakyan?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Assurance", "is_locked": True},
    {"prompt": "What can you say about the behavior, politeness, and overall treatment of passengers by the transport crew? (Ano ang masasabi mo sa pag-uugali, pagiging magalang, at pangkalahatang pagtrato ng mga tauhan sa mga pasahero?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Empathy", "is_locked": True},
    {"prompt": "What are your thoughts on the transport crew's attentiveness and care for passengers who might need extra assistance, such as Senior Citizens, PWDs, or pregnant women? (Ano ang pananaw mo sa pagiging maasikaso at pag-aalaga ng mga tauhan sa mga pasaherong maaaring mangailangan ng karagdagang tulong, tulad ng Senior Citizens, PWDs, o mga buntis?)", "q_type": "Paragraph", "options": [], "is_required": True, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": "Empathy", "is_locked": True},
    {"prompt": "Additional Comments or Suggestions / Karagdagang Komento o Mungkahi", "q_type": "Paragraph", "options": [], "is_required": False, "is_demographic": False, "enable_sentiment": False, "servqual_dimension": None, "is_locked": True},
]

form_schema = []
if form_meta.get("include_demographics", False):
    form_schema.extend(STANDARD_DEMO_QUESTIONS)

# Add standard SERVQUAL questions if toggle is enabled
include_servqual = form_meta.get("include_standard_servqual_questions", True)
if include_servqual:
    form_schema.extend(STANDARD_SERVQUAL_QUESTIONS)

# Add custom questions (excluding locked SERVQUAL if they exist in custom questions)
for q in custom_questions:
    if q.get("is_locked"):
        # Skip locked SERVQUAL questions since we already added them above
        continue
    form_schema.append(q)

allow_multiple_responses = form_meta.get("allow_multiple_responses", True)


def _make_clickable(text: str) -> str:
    """Convert email addresses and URLs to clickable links."""
    # Email pattern
    email_pattern = r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b'
    text = re.sub(email_pattern, r'<a href="mailto:\1" style="color:#2f4fd1;text-decoration:underline;">\1</a>', text)
    
    # URL pattern (http, https, www)
    url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
    text = re.sub(url_pattern, r'<a href="\1" target="_blank" style="color:#2f4fd1;text-decoration:underline;">\1</a>', text)
    
    return text

def _render_reach_out_contact():
    txt = (form_meta.get("reach_out_contact") or "").strip()
    if not txt:
        return
    
    # Extract Google Forms URL
    google_forms_pattern = r'(https://docs\.google\.com/forms[^\s]+)'
    match = re.search(google_forms_pattern, txt)
    
    if match:
        forms_url = match.group(1)
        # Remove the URL from the text
        text_without_url = re.sub(google_forms_pattern, '', txt).strip()
        
        # Escape HTML and make emails/URLs clickable for remaining text
        safe = html.escape(text_without_url)
        clickable = _make_clickable(safe)
        
        st.markdown(
            f"""
            <div style="margin-top:1rem;padding:12px 14px;border-radius:8px;background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.12);">
              <div style="font-size:.7rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">How to reach us</div>
              <div style="font-size:.9rem;color:rgb(60,85,120);white-space:pre-wrap;word-break:break-word;margin-bottom:12px;">{clickable}</div>
              <a href="{forms_url}" target="_blank" style="display:inline-block;padding:10px 20px;background:rgb(26,50,99);color:#ffffff;text-decoration:none;border-radius:6px;font-weight:600;font-size:0.9rem;">📋 Share Your Feedback</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Fallback to original rendering if no Google Forms URL found
        safe = html.escape(txt)
        clickable = _make_clickable(safe)
        st.markdown(
            f"""
            <div style="margin-top:1rem;padding:12px 14px;border-radius:8px;background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.12);">
              <div style="font-size:.7rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">How to reach us</div>
              <div style="font-size:.9rem;color:rgb(60,85,120);white-space:pre-wrap;word-break:break-word;">{clickable}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
submitted_key = f"submitted_once_{target_form_id}"
just_submitted_key = f"just_submitted_{target_form_id}"
if submitted_key not in st.session_state:
    st.session_state[submitted_key] = False
if just_submitted_key not in st.session_state:
    st.session_state[just_submitted_key] = False

# Add the counter initialization here!
if "form_reset_counter" not in st.session_state:
    st.session_state.form_reset_counter = 0

# ── 3. HEADER ──
st.markdown(f"""
<div class="gf-header">
  <div class="badge">🚌 Land public transportation feedback</div>
  <h1 style="color:var(--navy);">{form_meta.get('title')}</h1>
  <p class="desc">{form_meta.get('description')}</p>
</div>
""", unsafe_allow_html=True)

# ── 4. FORM ──
locked_one_response = (
    (not allow_multiple_responses)
    and (not is_preview)
    and client_cid
    and _already_submitted_for_client(target_form_id, client_cid)
)

if allow_multiple_responses and st.session_state.get(just_submitted_key):
    st.success("✅ Response submitted successfully.")
    st.info("Thank you for your feedback.")
    _render_reach_out_contact()
    if st.button("Submit another response", type="secondary", key=f"submit_again_{target_form_id}"):
        st.session_state[just_submitted_key] = False
        st.rerun()
elif (not allow_multiple_responses) and (
    locked_one_response or st.session_state.get(submitted_key)
):
    st.success("✅ Thank you — we have already received your response.")
    st.info("This survey allows only one submission.")
    _render_reach_out_contact()
    if not (form_meta.get("reach_out_contact") or "").strip():
        st.info("If you need to follow up, please contact the survey organizer.")
elif len(form_schema) > 0:
    question_map = {} 
    with st.form("public_survey_form", clear_on_submit=False):
        user_answers = {}
        for i, q in enumerate(form_schema):
            q_type, prompt, is_req = q["q_type"], q["prompt"], q.get("is_required", False)
            req_star = '<span style="color:#d63031;">*</span>' if is_req else ""
            
            # Update the key to include the counter!
            key = f"ans_{q.get('id', f'demo_{i}')}_{st.session_state.form_reset_counter}"

            unique_prompt = prompt
            counter = 1
            while unique_prompt in user_answers:
                unique_prompt = f"{prompt} ({counter})"
                counter += 1
            
            question_map[unique_prompt] = q

            q_badge = {
                "Short Answer":     "✏️ Short Answer",
                "Paragraph":        "📝 Paragraph",
                "Multiple Choice":  "☑️ Multiple Choice",
                "Multiple Select":  "☑️ Multiple Select",
                "Rating (Likert)":  "⭐ Likert",
            }.get(q_type, q_type)

            dim = q.get("servqual_dimension")
            dim_tag = (
                f'<span style="font-size:11px;font-weight:700;padding:2px 7px;border-radius:4px;'
                f'background:#e6f7eb;color:#2a7a3b;margin-right:6px;">{dim}</span>'
            ) if dim else ""

            with st.container(key=f"q_card_{i}"):
                st.markdown(f"""
                <div style="display:flex;gap:6px;margin-bottom:8px;">
                  <span style="font-size:11px;font-weight:700;color:#7c8db5;background:#eef1fa;padding:2px 6px;border-radius:4px;">Q{i+1}</span>
                  <span style="font-size:11px;color:#5566a0;background:#f0f3ff;padding:2px 7px;border-radius:4px;">{q_badge}</span>
                  {dim_tag}
                </div>
                <div style="font-size:1.05rem;font-weight:600;color:#1a3263;margin-bottom:1.2rem;">
                  {prompt}{req_star}
                </div>
                """, unsafe_allow_html=True)

                if q_type == "Short Answer":
                    user_answers[unique_prompt] = st.text_input(prompt, key=key, placeholder="Your answer", label_visibility="collapsed")
                elif q_type == "Paragraph":
                    user_answers[unique_prompt] = st.text_area(prompt, key=key, placeholder="Your answer", label_visibility="collapsed")
                elif q_type == "Multiple Choice":
                    ans_mc = st.radio(
                        prompt,
                        q.get("options", []),
                        key=key,
                        index=None,
                        label_visibility="collapsed",
                    )
                    user_answers[unique_prompt] = ans_mc
                elif q_type == "Multiple Select":
                    opts = q.get("options") or []
                    picked = []
                    st.markdown(
                        "<div style='font-size:0.8rem;color:#7c8db5;margin:0 0 6px 0;'>Select all that apply.</div>",
                        unsafe_allow_html=True,
                    )
                    for j, opt in enumerate(opts):
                        if st.checkbox(opt, key=f"{key}_ms_{j}", label_visibility="visible"):
                            picked.append(opt)
                    user_answers[unique_prompt] = picked
                elif q_type in ("Rating (Likert)", "Rating (1-5)"):
                    scale_max = int(q.get("scale_max") or 5)
                    lbl_low  = q.get("scale_label_low", "Strongly Disagree")
                    lbl_high = q.get("scale_label_high", "Strongly Agree")
                    

                    # 2. Render the radio buttons
                    ans_likert = st.radio(
                        prompt,
                        [str(x) for x in range(1, scale_max + 1)],
                        key=key,
                        index=None,
                        horizontal=True,
                        label_visibility="collapsed",
                    )

                    # 1. Display the Prompt labels in a flex container above or around the radio
                    st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px; px: 5px;">
                            <span style="font-size: 0.85rem; color: #7c8db5; font-weight: 600;">{lbl_low}</span>
                            <span style="font-size: 0.85rem; color: #7c8db5; font-weight: 600;">{lbl_high}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    user_answers[unique_prompt] = ans_likert

        if st.form_submit_button("Submit Response →", type="primary"):
            try:
                missing_required = []
                for uprompt, q_info in question_map.items():
                    if not q_info.get("is_required", False):
                        continue
                    ans = user_answers.get(uprompt)
                    q_type = q_info.get("q_type")
                    if q_type in ("Short Answer", "Paragraph"):
                        if ans is None or str(ans).strip() == "":
                            missing_required.append(q_info.get("prompt", uprompt))
                    elif q_type == "Multiple Select":
                        if not ans or not isinstance(ans, list) or len(ans) == 0:
                            missing_required.append(q_info.get("prompt", uprompt))
                    else:
                        if ans is None or str(ans).strip() == "":
                            missing_required.append(q_info.get("prompt", uprompt))

                if missing_required:
                    st.error("⚠️ Please answer all required questions before submitting.")
                elif (
                    (not allow_multiple_responses)
                    and (not is_preview)
                    and client_cid
                    and _already_submitted_for_client(target_form_id, client_cid)
                ):
                    st.warning("We already have a response from this session. Thank you.")
                    st.session_state[submitted_key] = True
                    st.rerun()
                else:
                    demo_answers = {}
                    custom_demographic_questions = []  # Track which demo_answers are from custom demographic questions
                    raw_feedback_list = []
                    question_ids_list = []
                    sentiment_flags_list = []
                    question_sentiments = {}  # Store per-question sentiment analysis
                    dim_scores = { "Tangibles": [], "Reliability": [], "Responsiveness": [], "Assurance": [], "Empathy": [] }
                    general_ratings = []
                    
                    for uprompt, ans in user_answers.items():
                        if ans is None:
                            continue
                        if isinstance(ans, list) and len(ans) == 0:
                            continue
                        if not isinstance(ans, list) and str(ans).strip() == "":
                            continue

                        q_info = question_map[uprompt]
                        q_id = q_info.get("id", uprompt)
                        dim = q_info.get("servqual_dimension")
                        q_type = q_info.get("q_type")
                        enable_sentiment = q_info.get("enable_sentiment", True)

                        if dim == "Commuter Profile" or q_info.get("is_demographic"):
                            demo_answers[q_info["prompt"]] = ans
                            # Track custom demographic questions (those marked as demographic, not from standard "Commuter Profile")
                            if q_info.get("is_demographic") and dim != "Commuter Profile":
                                custom_demographic_questions.append(q_info["prompt"])
                        elif q_type in ("Rating (Likert)", "Rating (1-5)"):
                            if dim in dim_scores:
                                dim_scores[dim].append(int(ans))
                            else:
                                general_ratings.append(int(ans))
                        elif q_type in ("Short Answer", "Paragraph"):
                            # Only include if marked for sentiment analysis
                            if enable_sentiment:
                                question_ids_list.append(q_id)
                                sentiment_flags_list.append(True)
                                raw_feedback_list.append(str(ans))
                                
                                # Store per-question data for individual analysis
                                # Dimension is pre-assigned in form schema, not auto-classified
                                question_sentiments[q_id] = {
                                    "text": str(ans),
                                    "enable_sentiment": True,
                                    "sentiment": "pending",  # Will be filled by sentiment analysis
                                    "dimension": dim  # Pre-assigned dimension from form schema
                                }
                            else:
                                # Still store it but marked as not for analysis
                                question_sentiments[q_id] = {
                                    "text": str(ans),
                                    "enable_sentiment": False,
                                    "sentiment": None,
                                    "dimension": None
                                }

                    payload = {
                        "public_id": target_form_id,
                        "form_id": target_form_id,
                        "admin_email": owner_email or form_meta.get("admin_email", ""),
                        **({"client_submission_id": client_cid} if client_cid else {}),
                        "answers": user_answers,
                        "demo_answers": demo_answers,
                        "question_ids": question_ids_list,  # Only sentiment-enabled questions
                        "enable_sentiment_flags": sentiment_flags_list,
                        "question_sentiments": question_sentiments,  # Per-question analysis data
                        "raw_feedback": " | ".join(raw_feedback_list) if raw_feedback_list else None,
                        "sentiment_status": "pending",
                        "tangibles_avg": sum(dim_scores["Tangibles"])/len(dim_scores["Tangibles"]) if dim_scores["Tangibles"] else None,
                        "reliability_avg": sum(dim_scores["Reliability"])/len(dim_scores["Reliability"]) if dim_scores["Reliability"] else None,
                        "responsiveness_avg": sum(dim_scores["Responsiveness"])/len(dim_scores["Responsiveness"]) if dim_scores["Responsiveness"] else None,
                        "assurance_avg": sum(dim_scores["Assurance"])/len(dim_scores["Assurance"]) if dim_scores["Assurance"] else None,
                        "empathy_avg": sum(dim_scores["Empathy"])/len(dim_scores["Empathy"]) if dim_scores["Empathy"] else None,
                        "general_ratings_avg": sum(general_ratings)/len(general_ratings) if general_ratings else None,

                    }
                    
                    conn.client.table("form_responses").insert(payload).execute()
                    
                    # Clear dashboard cache to ensure fresh data displays immediately
                    st.cache_data.clear()
                    
                    st.session_state[submitted_key] = True
                    st.session_state[just_submitted_key] = True
                    
                    # Increment the counter right before the rerun!
                    st.session_state.form_reset_counter += 1
                    
                    st.rerun()
            except Exception as e:
                st.error(f"⚠️ Error saving response: {e}")