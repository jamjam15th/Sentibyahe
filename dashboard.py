import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import re
import json
from datetime import datetime, timedelta
from st_supabase_connection import SupabaseConnection
from forms import (
    init_form_session_state,
    ensure_form_exists,
    fetch_active_forms,
    set_current_form,
    get_current_form_id,
    get_form,
)

def normalize_to_5(score, scale_max):
    if pd.isna(score):
        return score
    if scale_max <= 5:
        return score
    return (score / scale_max) * 5

# ══════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════
st.set_page_config(
    page_title="Land Public Transport Sentiment Dashboard",
    page_icon="📊",
    layout="wide",
)

# 🔥 THE NUCLEAR FULL-PAGE LOADER (WITH SIDEBAR FIX) 🔥
# Must go BEFORE Supabase connections and main CSS
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

        /* Prevent fragment re-run dimming */
    [data-testid="stFragment"] {
        opacity: 1 !important;
        transition: none !important;
    }

    .stAppDeployButton { display: none !important; }

    .stAppToolbar { background: #f0f4f8;}

    /* Target the specific overlay Streamlit adds during fragment refresh */
    [data-testid="stFragment"] > div {
        opacity: 1 !important;
    }

    /* Kill the loading/dimming overlay on fragments */
    [data-stale="true"] {
        opacity: 1 !important;
        pointer-events: none;
    }

    /* Streamlit uses this class during re-runs */
    .stSpinner,
    [data-testid="stFragment"] [data-stale] {
        opacity: 1 !important;
    }
            
    /* 1. KEEP SIDEBAR ON TOP OF LOADER */
    [data-testid="stSidebar"], 
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 999999999 !important; /* Highest priority */
    }

    /* 2. COMPLETELY HIDE THE APP ROOT */
    /* visibility: hidden is bulletproof against React hydration overrides */
    .stApp [data-testid="stAppViewBlockContainer"] {
        visibility: hidden !important;
        animation: snapVisible 0.1s forwards 2.5s !important; /* 2.5 seconds wait */
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
        animation: fadeOutNuclear 0.4s ease-out 2.5s forwards; /* Matches the 2.5s wait */
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
    <div class="loading-text">Loading Dashboard...</div>
</div>
""", unsafe_allow_html=True)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Mulish:wght@300;400;500;600;700&display=swap');

:root {
  --navy:   rgb(26, 50, 99);
  --navydk: rgb(18, 34, 68);
  --gold:   rgb(255, 197, 112);
  --sand:   rgb(239, 210, 176);
  --steel:  rgb(84, 119, 146);
  --off:    #f0f4f8;
  --card:   #ffffff;
  --bdr:    rgba(84,119,146,0.18);
  --muted:  rgb(120, 148, 172);
  --pos:    #4a7c59;
  --neu:    #8b9dc3;
  --neg:    #b03a2e;
}
*, html, body, p, span, div { font-family: 'Mulish', sans-serif !important; }
.stApp { background-color: var(--off); }

#MainMenu, footer, [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── HEADER ── */
.dash-header {
  background: linear-gradient(135deg, var(--navy) 0%, rgb(40,75,140) 100%);
  border-radius: 12px; padding: 1.8rem 2.2rem; margin-bottom: 1.5rem;
  box-shadow: 0 8px 24px rgba(26,50,99,0.18);
  display: flex; justify-content: space-between; align-items: center;
}
.dash-header h1 {
  font-family: 'Libre Baskerville', serif !important;
  color: #fff !important; margin: 0 0 .3rem !important;
  font-size: 1.9rem !important; font-weight: 700 !important;
}
.dash-header .sub { font-size: .78rem; color: rgba(239,210,176,0.8); margin: 0; }
.live-badge {
  background: rgba(255,255,255,0.12); color: var(--gold);
  padding: 6px 14px; border-radius: 20px; font-weight: 700;
  font-size: .75rem; letter-spacing: .06em;
  display: flex; align-items: center; gap: 8px;
  border: 1px solid rgba(255,197,112,0.3); white-space: nowrap;
}
.live-dot {
  height: 8px; width: 8px; background: var(--gold);
  border-radius: 50%; display: inline-block; animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0%   { opacity:1; box-shadow: 0 0 0 0 rgba(255,197,112,0.7); }
  50%  { opacity:.5; box-shadow: 0 0 0 6px rgba(255,197,112,0); }
  100% { opacity:1; box-shadow: 0 0 0 0 rgba(255,197,112,0); }
}

/* ── KPI CARDS ── */
.kpi-card {
  background: var(--card); border: 1px solid var(--bdr);
  border-radius: 10px; padding: 1.1rem 1.3rem;
  box-shadow: 0 2px 8px rgba(26,50,99,0.04);
  min-height: 110px;
}
.kpi-title {
  font-size: .68rem; font-weight: 700; color: var(--steel);
  text-transform: uppercase; letter-spacing: .08em; margin-bottom: .4rem;
}
.kpi-value {
  font-family: 'Libre Baskerville', serif !important;
  font-size: 1.9rem; font-weight: 700; color: var(--navy); line-height: 1;
}
.kpi-value.pos  { color: var(--pos); }
.kpi-value.neg  { color: var(--neg); }
.kpi-value.gold { color: rgb(180,130,50); }
.kpi-sub   { font-size: .68rem; color: var(--muted); margin-top: .3rem; }
.kpi-pending {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(255,197,112,0.15); border: 1px solid rgba(255,197,112,0.35);
  border-radius: 999px; padding: .15rem .6rem;
  font-size: .65rem; font-weight: 700; color: rgb(160,110,30); margin-top: .35rem;
}

/* ── GENERAL RATINGS CARD ── */
.gen-rating-bar {
  background: rgba(108,117,125,0.08); border: 1px solid rgba(108,117,125,0.2);
  border-left: 4px solid #6c757d; border-radius: 7px;
  padding: .7rem 1rem; margin-top: .8rem;
}
.gen-rating-bar .label { font-size: .65rem; font-weight: 700; color: #6c757d; text-transform: uppercase; letter-spacing: .1em; margin-bottom: .2rem; }
.gen-rating-bar .val   { font-size: .95rem; font-weight: 700; color: var(--navy); }

/* ── SECTION HEADING ── */
.section-head {
  font-family: 'Libre Baskerville', serif !important;
  font-size: 1rem !important; font-weight: 700 !important; color: var(--navy) !important;
  margin: 1.2rem 0 .7rem !important; padding-bottom: .3rem !important;
  border-bottom: 2px solid rgba(26,50,99,0.08) !important;
  display: flex; align-items: center; justify-content: space-between;
}

/* ── TABS ── */
[data-testid="stTabs"] [role="tablist"] { border-bottom: 2px solid var(--bdr) !important; gap: 0 !important; }
[data-testid="stTabs"] [role="tab"] {
  font-size: .78rem !important; font-weight: 700 !important;
  letter-spacing: .06em !important; color: var(--muted) !important;
  padding: .55rem 1.1rem !important; border: none !important; background: transparent !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: var(--navy) !important; }
div[data-baseweb="tab-highlight"] { background-color: var(--navy) !important; }

/* ── TABLE ── */
[data-testid="stDataFrame"] { border: 1px solid var(--bdr) !important; border-radius: 8px !important; overflow: hidden !important; }

/* ── INPUTS ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stDateInput"] input { border: 1.5px solid var(--bdr) !important; border-radius: 6px !important; background: #fff !important; color: var(--navy) !important; }
[data-testid="stSelectbox"] label,
[data-testid="stDateInput"] label { font-size: .68rem !important; font-weight: 700 !important; letter-spacing: .1em !important; text-transform: uppercase !important; color: var(--steel) !important; }

/* ── DOWNLOAD BUTTON ── */
[data-testid="stDownloadButton"] > button {
  background: var(--navy) !important; color: var(--gold) !important;
  border: none !important; border-radius: 6px !important;
  font-size: .7rem !important; font-weight: 700 !important;
  letter-spacing: .1em !important; text-transform: uppercase !important;
  padding: .45rem 1.1rem !important;
}
[data-testid="stDownloadButton"] > button:hover { background: var(--navydk) !important; transform: translateY(-1px) !important; }

/* ── CONFIDENCE BAR ── */
.conf-bar-wrap { background: rgba(84,119,146,0.12); border-radius: 999px; height: 6px; overflow: hidden; margin-top: .4rem; }
.conf-bar      { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--steel), var(--navy)); }

/* ── EMPTY STATE ── */
.empty-tab {
  text-align: center; padding: 3rem 2rem; color: var(--muted);
  background: var(--card); border: 1.5px dashed var(--bdr);
  border-radius: 10px; margin-top: 1rem;
}
.empty-tab .icon { font-size: 2.2rem; margin-bottom: .6rem; }
.empty-tab p     { font-size: .9rem; margin: 0; line-height: 1.7; }

/* 📱 MOBILE RESPONSIVENESS */
@media screen and (max-width: 768px) {
  .dash-header { flex-direction: column; align-items: flex-start; gap: 12px; padding: 1.2rem; }
  .dash-header h1 { font-size: 1.5rem !important; }
  .kpi-card { min-height: auto; padding: 0.6rem 0.8rem; }
  .kpi-value { font-size: 1.4rem; }
  .kpi-title { font-size: 0.6rem !important; margin-bottom: 0.2rem !important; }
  .kpi-sub { font-size: 0.6rem !important; margin-top: 0.2rem !important; }
  [data-testid="stTabs"] [role="tablist"] { overflow-x: auto; flex-wrap: nowrap !important; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
  [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar { display: none; }
  [data-testid="stTabs"] [role="tab"] { white-space: nowrap; padding: 0.5rem 0.8rem !important; font-size: 0.75rem !important; }
  .sentiment-guide-full { display: none; }
  .sentiment-guide-mobile { display: block !important; }
  .sentiment-rate-cards { flex-wrap: wrap !important; }
  .section-head { margin: 0.8rem 0 0.4rem !important; font-size: 0.9rem !important; }
}
@media screen and (min-width: 769px) {
  .sentiment-guide-mobile { display: none !important; }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# SETUP
# ══════════════════════════════════════════
conn        = st.connection("supabase", type=SupabaseConnection)

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
            st.session_state.local_login = True
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
    st.error("🔒 Please log in to view the dashboard.")
    st.stop()

# CRITICAL: Persist session_id in URL so it survives reloads and navigation
if session_id_from_url and "session_id" not in st.query_params:
    st.query_params["session_id"] = session_id_from_url
elif st.session_state.get("session_id") and "session_id" not in st.query_params:
    st.query_params["session_id"] = st.session_state.get("session_id")

# Track page for detecting navigation back to builder
st.session_state._prev_page = st.session_state.get("current_page", "")
st.session_state.current_page = "dashboard"

# Initialize multi-form session state
init_form_session_state(admin_email)
current_form_id = get_current_form_id()  # Get from session state, not ensure_form_exists
if not current_form_id:
    current_form_id = ensure_form_exists(admin_email)
    if current_form_id:
        st.session_state.current_form_id = current_form_id

# ══════════════════════════════════════════
# DIMENSION CONFIG — single source of truth
# ══════════════════════════════════════════
SERVQUAL_DIM_COLS = {
    "Tangibles":      "tangibles_avg",
    "Reliability":    "reliability_avg",
    "Responsiveness": "responsiveness_avg",
    "Assurance":      "assurance_avg",
    "Empathy":        "empathy_avg",
}

# General Ratings is kept SEPARATE — not mixed into SERVQUAL scoring
GENERAL_RATINGS_COL = "general_ratings_avg"

DIM_PALETTE = {
    "Tangibles":       "#547792",
    "Reliability":     "#1a3263",
    "Responsiveness":  "#ffc570",
    "Assurance":       "#3c6482",
    "Empathy":         "#d4a373",
    "General Ratings": "#6c757d",
}

# ══════════════════════════════════════════
# MODEL (cached for session lifetime)
# ══════════════════════════════════════════
@st.cache_resource(show_spinner="Initializing sentiment model…")
def load_model():
    from transformers import pipeline
    return pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
        device=-1,
    )

@st.cache_data(max_entries=5000, show_spinner=False)
def analyze_text(text: str) -> tuple[str, float]:

    analyzer = load_model()

    label_map = {
        "LABEL_0": "NEGATIVE", "negative": "NEGATIVE",
        "LABEL_1": "NEUTRAL",  "neutral":  "NEUTRAL",
        "LABEL_2": "POSITIVE", "positive": "POSITIVE",
    }
    res = analyzer(text[:512])[0]
    return label_map.get(res["label"], str(res["label"]).upper()), round(res["score"], 4)

# ══════════════════════════════════════════
# DATA FETCH
# ══════════════════════════════════════════
@st.cache_data(ttl=5)
def fetch_dashboard_data(email: str, form_id: str) -> pd.DataFrame:
    try:
        r = (conn.client.table("form_responses")
             .select("*").eq("admin_email", email).eq("form_id", form_id)
             .order("created_at").execute())
        return pd.DataFrame(r.data or [])
    except Exception as e:
        st.warning(f"Could not load responses: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def fetch_question_scale_map(email: str, form_id: str) -> dict:
    """Return latest scale_max per question prompt from form schema."""
    try:
        r = (conn.client.table("form_questions")
             .select("prompt, scale_max")
             .eq("admin_email", email)
             .eq("form_id", form_id)
             .execute())
        rows = r.data or []
        scale_map = {}
        for row in rows:
            prompt = row.get("prompt")
            scale_max = row.get("scale_max")
            if not prompt:
                continue
            if scale_max is None:
                continue
            try:
                scale_map[prompt] = int(scale_max)
            except Exception:
                pass
        return scale_map
    except Exception:
        return {}

def persist_sentiment_batch(rows: list[dict]):
    if not rows:
        return
    try:
        conn.client.table("form_responses").upsert(rows, on_conflict="id").execute()
    except Exception:
        pass

def analyze_per_question_sentiments(rows: list[dict]):
    """Analyze sentiment for each question in question_sentiments JSONB separately."""
    if not rows:
        return
    
    batch_updates = []
    for row in rows:
        response_id = row.get("id")
        question_sentiments = row.get("question_sentiments", {})
        
        if not isinstance(question_sentiments, dict):
            continue
        
        updated = False
        for q_id, q_data in question_sentiments.items():
            if not isinstance(q_data, dict):
                continue
            
            # Only analyze if marked for sentiment and currently pending
            if q_data.get("enable_sentiment") and q_data.get("sentiment") == "pending":
                text = q_data.get("text", "").strip()
                if text:
                    try:
                        label, score = analyze_text(text)
                        q_data["sentiment"] = label
                        q_data["confidence"] = score
                        updated = True
                    except Exception:
                        pass
        
        # If any updates, prepare batch save
        if updated:
            batch_updates.append({
                "id": response_id,
                "question_sentiments": question_sentiments,
            })
    
    # Save all updates
    if batch_updates:
        try:
            conn.client.table("form_responses").upsert(batch_updates, on_conflict="id").execute()
        except Exception:
            pass

# ══════════════════════════════════════════
# STATIC HEADER WITH BACK BUTTON
# ══════════════════════════════════════════
st.markdown("""
<div class="dash-header">
  <div>
    <h1>📊 Dashboard</h1>
  </div>
  <div class="live-badge"><span class="live-dot"></span> LIVE SYNC</div>
</div>
""", unsafe_allow_html=True)

btn_col1, btn_col2, btn_col3 = st.columns([0.15, 0.7, 0.15])
with btn_col1:
    if st.button("← Back", use_container_width=True):
        st.switch_page("builder.py")

st.markdown("<div style='margin:0.5rem 0'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════
# ANALYTICS DASHBOARD
# ══════════════════════════════════════════
available_forms = st.session_state.get("available_forms", [])
form_is_selected = current_form_id and len([f for f in available_forms if f["form_id"] == current_form_id]) > 0

if not form_is_selected:
    st.info("No form data available. Please create and select a form in the Form Builder.")
    st.stop()

# Get the selected form details
selected_form = next((f for f in available_forms if f["form_id"] == current_form_id), None)
if selected_form:
    form_title = selected_form['title']
    
    # Fetch question count
    questions = conn.client.table("form_questions").select("form_id").eq("form_id", current_form_id).eq("admin_email", admin_email).execute().data or []
    question_count = len(questions)

    # Fetch response count
    responses = conn.client.table("form_responses").select("form_id").eq("form_id", current_form_id).execute().data or []
    response_count = len(responses)

    # Format creation date
    created_at = selected_form.get('created_at', '')
    date_created = ""
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            date_created = dt.strftime('%b %d, %Y')
        except:
            date_created = "Unknown"

    # Mobile-friendly responsive header
    col1 = st.columns(1)[0]
    with col1:
        st.markdown(f"""
        <div style="background: rgba(26,50,99,0.03); border: 1px solid rgba(26,50,99,0.1); border-radius: 8px; padding: 0.75rem 1rem;">
            <div style="font-size: 0.65rem; color: #7c8db5; font-weight: 600; text-transform: uppercase; letter-spacing: 0.4px;">Currently Analyzing</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1a2e55; margin-top: 0.25rem;">{form_title}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

st.markdown('<div class="section-head">🗓 Filter by Date Range</div>', unsafe_allow_html=True)
cd1, cd2, _ = st.columns([2, 2, 4])
with cd1:
    date_from = st.date_input("From", value=datetime.today() - timedelta(days=30), key="df")
with cd2:
    date_to   = st.date_input("To",   value=datetime.today(), key="dt")

# Demographics keys
TRANSPORT_DEMO_KEYS = (
    "Which Land Public Transportation modes do you usually use? (Select all that apply)",
    "Which land public transportation modes do you usually use? (Select all that apply)",
    "Which PUV or transport types do you usually ride or use? (Select all that apply)",
    "What primary land public transportation mode do you usually use?",
)

def _explode_demo_series(series: pd.Series) -> pd.Series:
    rows = []
    for v in series.dropna():
        if isinstance(v, (list, tuple)):
            for x in v:
                if x is not None and str(x).strip():
                    rows.append(str(x).strip())
        elif v is not None and str(v).strip():
            rows.append(str(v).strip())
    return pd.Series(rows, dtype=str)

def _demo_chart_specs(demo_df: pd.DataFrame) -> list[tuple[str, str]]:
    """Build specs from whatever demographic columns exist in the dataframe."""
    specs: list[tuple[str, str]] = []
    for col in demo_df.columns:
        # Use the actual column name as both the column reference and display label
        label = col if len(col) <= 48 else col[:45] + "…"
        specs.append((col, label))
    return specs

def _demo_chart_specs_all(demo_df: pd.DataFrame, custom_demographic_prompts: list = None) -> list[tuple[str, str]]:
    """Build demo chart specs from all available demographic columns."""
    if custom_demographic_prompts is None:
        custom_demographic_prompts = []
    
    specs: list[tuple[str, str]] = []
    covered = set()
    
    # First: add custom demographic questions (user-tagged in form builder)
    for col in demo_df.columns:
        if col in custom_demographic_prompts:
            label = col if len(col) <= 48 else col[:45] + "…"
            specs.append((col, label))
            covered.add(col)
    
    # Second: add all remaining columns
    for col in demo_df.columns:
        if col not in covered:
            label = col if len(col) <= 48 else col[:45] + "…"
            specs.append((col, label))
    
    return specs

def _is_demographic_question(prompt: str) -> bool:
    demographic_prompts = {
        "1. Age / Edad",
        "2. Gender / Kasarian",
        "3. Occupational Status / Katayuan sa Trabaho",
        "4. Monthly Allowance or Salary / Buwanang Sahod o Allowance",
        "5. Frequency of Commuting / Gaano ka kadalas sumakay sa isang linggo?",
        "6. Most frequently used transport mode / Pinakamadalas na sinasakyan",
    }
    demographic_prompts.update(TRANSPORT_DEMO_KEYS)
    prompt_lower = prompt.lower().strip() if prompt else ""
    return any(prompt_lower == dp.lower().strip() for dp in demographic_prompts)

def _format_demo_cell(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x) for x in v if x is not None and str(x).strip())
    return str(v).strip()

# ══════════════════════════════════════════
# LIVE FRAGMENT (runs every 5 s)
# ══════════════════════════════════════════
@st.cache_data(ttl=5)
def fetch_form_questions_schema(email: str, form_id: str) -> dict:
    """Fetch current form question schema to get SERVQUAL dimension tags.
    Returns a dict with both 'by_prompt' and 'by_id' keys for flexible lookups.
    """
    try:
        r = (conn.client.table("form_questions")
             .select("id, prompt, servqual_dimension, q_type")
             .eq("admin_email", email)
             .eq("form_id", form_id)
             .execute())
        schema_by_prompt = {}
        schema_by_id = {}
        for row in r.data or []:
            prompt = row.get("prompt")
            q_id = row.get("id")
            dimension_info = {
                "dimension": row.get("servqual_dimension"),
                "q_type": row.get("q_type"),
                "prompt": prompt,  # Also store prompt in by_id for lookups
            }
            if prompt:
                schema_by_prompt[prompt] = dimension_info
            if q_id:
                schema_by_id[str(q_id)] = dimension_info
        return {
            "by_prompt": schema_by_prompt,
            "by_id": schema_by_id,
        }
    except Exception:
        return {"by_prompt": {}, "by_id": {}}

def recalculate_servqual_columns(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """Recalculate SERVQUAL averages based on current schema, not stored values."""
    df = df.copy()
    
    # Initialize all dimension columns
    for dim_name, col_name in SERVQUAL_DIM_COLS.items():
        df[col_name] = None
    df[GENERAL_RATINGS_COL] = None
    
    if df.empty or not schema:
        return df
    
    # For each response, recalculate based on current schema
    for idx, row in df.iterrows():
        answers = row.get("answers", {})
        if not isinstance(answers, dict):
            continue
        
        # Accumulate scores per dimension
        dim_scores = {
            "Tangibles": [],
            "Reliability": [],
            "Responsiveness": [],
            "Assurance": [],
            "Empathy": [],
        }
        general_ratings = []
        
        # Go through each answer and map to current dimensions
        for prompt, answer in answers.items():
            if prompt not in schema:
                continue
            
            question_info = schema[prompt]
            q_type = question_info.get("q_type", "")
            dimension = question_info.get("dimension")
            
            # Only process Likert-type questions
            if q_type not in ("Rating (Likert)", "Rating (1-5)"):
                continue
            
            try:
                score = float(answer)
            except (TypeError, ValueError):
                continue
            
            # Assign to dimension or general ratings
            if dimension and dimension in dim_scores:
                dim_scores[dimension].append(score)
            else:
                general_ratings.append(score)
        
        # Calculate averages
        for dim, col in SERVQUAL_DIM_COLS.items():
            if dim_scores[dim]:
                df.at[idx, col] = sum(dim_scores[dim]) / len(dim_scores[dim])
        
        if general_ratings:
            df.at[idx, GENERAL_RATINGS_COL] = sum(general_ratings) / len(general_ratings)
    
    return df

@st.fragment
def render_dashboard():
    # Show loading indicator while data loads
    with st.spinner("📊 Loading dashboard data..."):
        df_raw = fetch_dashboard_data(admin_email, current_form_id)
        question_scale_map = fetch_question_scale_map(admin_email, current_form_id)
        form_schema_full = fetch_form_questions_schema(admin_email, current_form_id)
        form_schema = form_schema_full.get("by_prompt", {})  # Keep for backwards compatibility
        
        # Recalculate SERVQUAL columns based on current schema
        df_raw = recalculate_servqual_columns(df_raw, form_schema)

    if df_raw.empty:
        st.markdown("""
        <div class="empty-tab">
          <div class="icon">☹️</div>
          <p>No responses yet. Share your survey link to start collecting data.</p>
        </div>""", unsafe_allow_html=True)
        return

    # ── Timestamps ──
    if "created_at" in df_raw.columns:
        df_raw["created_at"] = pd.to_datetime(df_raw["created_at"], format='ISO8601', utc=True).dt.tz_localize(None)
        df = df_raw[
            (df_raw["created_at"].dt.date >= date_from) &
            (df_raw["created_at"].dt.date <= date_to)
        ].copy()
    else:
        df = df_raw.copy()

    if df.empty:
        st.info("No responses in the selected date range.")
        return

    # SERVQUAL dims (pure 5-dimension model, General Ratings excluded)
    present_servqual_dims = {k: v for k, v in SERVQUAL_DIM_COLS.items() if v in df.columns}

    # General Ratings — separate tracking
    has_general_ratings = (
        GENERAL_RATINGS_COL in df.columns and
        df[GENERAL_RATINGS_COL].notna().any()
    )
    general_ratings_avg_val = float(df[GENERAL_RATINGS_COL].mean()) if has_general_ratings else None

    # All dims for charts that include General Ratings (trends, quantitative)
    all_dim_cols = {**present_servqual_dims}
    if has_general_ratings:
        all_dim_cols["General Ratings"] = GENERAL_RATINGS_COL

    # overall_avg uses ONLY the 5 SERVQUAL dims, NOT General Ratings
    has_servqual_data = bool(present_servqual_dims) and df[
        list(present_servqual_dims.values())
    ].notna().any().any()

    overall_avg = 0.0
    normalized_df = df.copy()  # Initialize for use in all code paths
    
    if has_servqual_data:
        df['overall_servqual'] = df[list(present_servqual_dims.values())].mean(axis=1)
        normalized_df = df.copy()

        observed_max = df[list(present_servqual_dims.values())].max().max()
        if pd.isna(observed_max) or observed_max <= 0:
            scale_max = 5
        else:
            scale_max = float(observed_max) if observed_max > 5 else 5

        for col in present_servqual_dims.values():
            normalized_df[col] = normalized_df[col].apply(lambda x: normalize_to_5(x, scale_max))

        overall_avg = normalized_df[list(present_servqual_dims.values())].mean().mean()
        if pd.isna(overall_avg):
            overall_avg = 0.0

    else: 
        df['overall_servqual'] = None
    has_any_rating_data = has_servqual_data or has_general_ratings

    def scoped_palette(dim_keys):
        return {k: DIM_PALETTE[k] for k in dim_keys if k in DIM_PALETTE}

    # ── Sentiment: batch-analyze pending rows ──
    sent_col = "sentiment_status"
    if "raw_feedback" in df.columns and sent_col in df.columns:
        pending_rows = df[
            (df[sent_col] == "pending") &
            df["raw_feedback"].notna() &
            (df["raw_feedback"].str.strip() != "")
        ]
        if not pending_rows.empty:
            with st.spinner(f"🤖 Analyzing sentiment for {len(pending_rows)} response(s)..."):
                batch_updates = []
                for _, row in pending_rows.iterrows():
                    label, score = analyze_text(str(row["raw_feedback"]).strip())
                    df.loc[df["id"] == row["id"], sent_col]          = label
                    df.loc[df["id"] == row["id"], "sentiment_score"] = score
                    batch_updates.append({
                        "id": row["id"],
                        "sentiment_status": label,
                        "sentiment_score": score,
                    })
                persist_sentiment_batch(batch_updates)
    
    # ── Analyze per-question sentiments ──
    if "question_sentiments" in df.columns:
        pending_q_rows = df[df["question_sentiments"].notna()].to_dict('records')
        if pending_q_rows:
            with st.spinner(f"🤖 Analyzing per-question sentiments for {len(pending_q_rows)} response(s)..."):
                analyze_per_question_sentiments(pending_q_rows)

    # ── Counts ──
    if sent_col in df.columns:
        df[sent_col] = df[sent_col].astype(str).str.strip().str.upper()
    
    sent_valid = (
        df[sent_col].isin(["POSITIVE", "NEUTRAL", "NEGATIVE"])
        if sent_col in df.columns
        else pd.Series(False, index=df.index)
    )
    df_sent   = df[sent_valid].copy() if sent_col in df.columns else pd.DataFrame()
    total     = len(df)
    
    # Calculate positivity from both sources
    all_sentiments_for_rate = []
    
    for _, row in df_sent.iterrows():
        response_level_sent = str(row.get(sent_col, "")).upper().strip() if sent_col in row else ""
        question_sentiments = row.get("question_sentiments", {})
        
        has_question_sentiments = False
        if isinstance(question_sentiments, dict) and len(question_sentiments) > 0:
            for q_id, q_data in question_sentiments.items():
                if isinstance(q_data, dict):
                    if q_data.get("enable_sentiment") is not False:
                        sentiment = str(q_data.get("sentiment", "")).upper().strip()
                        if sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
                            has_question_sentiments = True
                            all_sentiments_for_rate.append(sentiment)
        
        if not has_question_sentiments and response_level_sent and response_level_sent != "PENDING":
            all_sentiments_for_rate.append(response_level_sent)
    
    total_sentiments = len(all_sentiments_for_rate)
    pos_count = all_sentiments_for_rate.count("POSITIVE")
    pos_rate = (pos_count / total_sentiments * 100) if total_sentiments > 0 else 0
    neu_count = all_sentiments_for_rate.count("NEUTRAL")
    neu_rate = (neu_count / total_sentiments * 100) if total_sentiments > 0 else 0
    neg_count = all_sentiments_for_rate.count("NEGATIVE")
    neg_rate = (neg_count / total_sentiments * 100) if total_sentiments > 0 else 0

    # Pre-calculate SERVQUAL sentiment data for KPI
    dimension_sentiment_data_kpi = {
        "Tangibles": {"positive": 0, "neutral": 0, "negative": 0},
        "Reliability": {"positive": 0, "neutral": 0, "negative": 0},
        "Responsiveness": {"positive": 0, "neutral": 0, "negative": 0},
        "Assurance": {"positive": 0, "neutral": 0, "negative": 0},
        "Empathy": {"positive": 0, "neutral": 0, "negative": 0},
    }
    
    for _, row in df_sent.iterrows():
        question_sentiments = row.get("question_sentiments", {})
        if isinstance(question_sentiments, dict) and len(question_sentiments) > 0:
            for q_id, q_data in question_sentiments.items():
                if isinstance(q_data, dict):
                    if q_data.get("enable_sentiment") is not False:
                        sentiment = str(q_data.get("sentiment", "")).upper().strip()
                        dimension = q_data.get("dimension")
                        if sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE"] and dimension in dimension_sentiment_data_kpi:
                            dimension_sentiment_data_kpi[dimension][sentiment.lower()] += 1
    
    dimension_net_scores_kpi = {}
    dimension_totals_kpi = {}
    for dim, counts in dimension_sentiment_data_kpi.items():
        total = counts["positive"] + counts["neutral"] + counts["negative"]
        dimension_totals_kpi[dim] = total
        if total > 0:
            net_score = ((counts["positive"] - counts["negative"]) / total) * 100
            dimension_net_scores_kpi[dim] = net_score
        else:
            dimension_net_scores_kpi[dim] = 0
    
    has_dimension_sentiment_kpi = any(dimension_totals_kpi.values())

    # ══════════════════════════════════
    # INTERACTIVE FILTERS SECTION
    # ══════════════════════════════════
    st.markdown("""<style>
    .filter-container {
        background: white; border: 1px solid rgba(84,119,146,0.18);
        border-radius: 10px; padding: 1rem 1.2rem;
        margin-bottom: 1.2rem;
    }
    .filter-title {
        font-size: 0.75rem; font-weight: 700; color: rgb(26,50,99);
        text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.8rem;
    }
    </style>""", unsafe_allow_html=True)
    
    with st.expander("🔍 **Filter By Demographics & Responses**", expanded=False):
        df_filtered = df.copy()
        active_filters = []
        
        # Extract all possible filter data (demographics + other multiple choice/select fields)
        filter_data = {}
        
        # 1. Demographics from demo_answers
        if "demo_answers" in df.columns:
            demo_df_temp = pd.json_normalize(df["demo_answers"].dropna().tolist())
            if not demo_df_temp.empty:
                for col in demo_df_temp.columns:
                    sample_val = demo_df_temp[col].dropna().iloc[0] if len(demo_df_temp[col].dropna()) > 0 else None
                    
                    if isinstance(sample_val, list):
                        all_values = []
                        for val in demo_df_temp[col].dropna():
                            if isinstance(val, list):
                                all_values.extend(val)
                            else:
                                all_values.append(val)
                        filter_data[col] = sorted(list(set(all_values)))
                    else:
                        filter_data[col] = sorted(demo_df_temp[col].dropna().unique().tolist())
        
        # 2. Other form columns that are multiple choice/select (contain lists or multiple values)
        excluded_cols = {'id', 'created_at', 'updated_at', 'demo_answers', 'question_sentiments', 
                        'sentiment_status', 'sentiment_score', 'raw_feedback', 'overall_servqual'}
        
        for col in df.columns:
            if col in excluded_cols or col in filter_data:
                continue
            
            # Exclude columns with 'id' or 'sentiment' in their names
            if 'id' in col.lower() or 'sentiment' in col.lower():
                continue
            
            # Skip columns that are Likert scale (numeric, tagged to dimensions)
            if col in present_servqual_dims.values():
                continue
            if col == GENERAL_RATINGS_COL:
                continue
                
            # Check if this column contains lists or multiple values
            sample_vals = df[col].dropna()
            if len(sample_vals) > 0:
                first_val = sample_vals.iloc[0]
                
                # If it's a list, extract all values
                if isinstance(first_val, list):
                    all_values = []
                    for val in sample_vals:
                        if isinstance(val, list):
                            all_values.extend(val)
                        else:
                            all_values.append(val)
                    if all_values:
                        filter_data[col] = sorted(list(set(str(v) for v in all_values)))
                # If it's a string that might contain commas (multi-select), treat as list
                elif isinstance(first_val, str) and ',' in str(first_val):
                    all_values = []
                    for val in sample_vals:
                        if isinstance(val, str):
                            all_values.extend([v.strip() for v in str(val).split(',')])
                    if all_values:
                        filter_data[col] = sorted(list(set(all_values)))
        
        # Now create filter UI dynamically
        if not filter_data:
            st.markdown('<div style="font-size:0.85rem;color:#999;">No filter options available</div>', unsafe_allow_html=True)
        else:
            # Create columns for filters (4 per row)
            filter_cols = list(filter_data.items())
            
            for row_idx in range(0, len(filter_cols), 4):
                row_items = filter_cols[row_idx:row_idx+4]
                row_cols = st.columns(len(row_items))
                
                for col_idx, (filter_name, filter_values) in enumerate(row_items):
                    # Format the column name nicely
                    display_name = filter_name.replace('_', ' ').title()
                    
                    with row_cols[col_idx]:
                        st.markdown(f'<div class="filter-title">{display_name}</div>', unsafe_allow_html=True)
                        
                        selected_values = st.multiselect(
                            f"Filter by {filter_name}",
                            options=filter_values,
                            default=None,
                            label_visibility="collapsed",
                            key=f"filter_{filter_name}"
                        )
                        
                        if selected_values:
                            # Apply filter - check if it's a direct column or from demo_answers
                            if filter_name in df.columns:
                                # Direct column filter
                                col_data = df[filter_name]
                                mask = col_data.apply(
                                    lambda x: (
                                        (isinstance(x, list) and any(item in selected_values for item in x)) or
                                        (isinstance(x, str) and ',' in str(x) and any(v.strip() in selected_values for v in str(x).split(','))) or
                                        (str(x) in selected_values)
                                    ) if pd.notna(x) else False
                                )
                                df_filtered = df_filtered[mask]
                            else:
                                # Demo answers filter
                                def check_match(demo_dict):
                                    if not isinstance(demo_dict, dict):
                                        return False
                                    val = demo_dict.get(filter_name)
                                    if isinstance(val, list):
                                        return any(item in selected_values for item in val)
                                    return val in selected_values
                                
                                df_filtered = df_filtered[
                                    df_filtered["demo_answers"].apply(lambda x: check_match(x) if pd.notna(x) else False)
                                ]
                            
                            active_filters.append(f"{display_name}: {', '.join(selected_values)}")
        
        # Show active filters and count
        if active_filters:
            st.markdown(f"<div style='font-size:0.85rem;color:#7c8db5;padding-top:0.5rem;'>✓ {', '.join(active_filters)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.9rem;font-weight:600;color:rgb(26,50,99);margin-top:0.5rem;'>Showing {len(df_filtered)} of {total} responses</div>", unsafe_allow_html=True)
        
        # Use filtered data for all subsequent analysis
        df = df_filtered
        df_sent = df[df[sent_col].isin(["POSITIVE", "NEUTRAL", "NEGATIVE"])] if sent_col in df.columns else pd.DataFrame()
    
    # ═══════════════════════════════════════════════════════
    # RECALCULATE METRICS FOR FILTERED DATA
    # ═══════════════════════════════════════════════════════
    with st.spinner("📊 Calculating metrics..."):
        total = len(df)
        
        # Recalculate sentiment rates for filtered data
        all_sentiments_for_rate_filtered = []
        for _, row in df_sent.iterrows():
            response_level_sent = str(row.get(sent_col, "")).upper().strip() if sent_col in row else ""
            question_sentiments = row.get("question_sentiments", {})
            
            has_question_sentiments = False
            if isinstance(question_sentiments, dict) and len(question_sentiments) > 0:
                for q_id, q_data in question_sentiments.items():
                    if isinstance(q_data, dict):
                        if q_data.get("enable_sentiment") is not False:
                            sentiment = str(q_data.get("sentiment", "")).upper().strip()
                            if sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
                                has_question_sentiments = True
                                all_sentiments_for_rate_filtered.append(sentiment)
            
            if not has_question_sentiments and response_level_sent and response_level_sent != "PENDING":
                all_sentiments_for_rate_filtered.append(response_level_sent)
        
        total_sentiments_filtered = len(all_sentiments_for_rate_filtered)
        pos_count = all_sentiments_for_rate_filtered.count("POSITIVE")
        pos_rate = (pos_count / total_sentiments_filtered * 100) if total_sentiments_filtered > 0 else 0
        neu_count = all_sentiments_for_rate_filtered.count("NEUTRAL")
        neu_rate = (neu_count / total_sentiments_filtered * 100) if total_sentiments_filtered > 0 else 0
        neg_count = all_sentiments_for_rate_filtered.count("NEGATIVE")
        neg_rate = (neg_count / total_sentiments_filtered * 100) if total_sentiments_filtered > 0 else 0
        
        # Recalculate SERVQUAL averages for filtered data
        if present_servqual_dims:
            normalized_df_filtered = df[list(present_servqual_dims.values())].copy()
            observed_max_filtered = normalized_df_filtered.max().max()
            if pd.isna(observed_max_filtered) or observed_max_filtered <= 0:
                scale_max = 5
            else:
                scale_max = float(observed_max_filtered) if observed_max_filtered > 5 else 5
            
            for col in present_servqual_dims.values():
                normalized_df_filtered[col] = normalized_df_filtered[col].apply(lambda x: normalize_to_5(x, scale_max))
            
            overall_avg = normalized_df_filtered[list(present_servqual_dims.values())].mean().mean()
            if pd.isna(overall_avg):
                overall_avg = 0.0
        else:
            overall_avg = 0.0
        
        # Recalculate dimension sentiment data for filtered data
        dimension_sentiment_data_kpi = {
            "Tangibles": {"positive": 0, "neutral": 0, "negative": 0},
            "Reliability": {"positive": 0, "neutral": 0, "negative": 0},
            "Responsiveness": {"positive": 0, "neutral": 0, "negative": 0},
            "Assurance": {"positive": 0, "neutral": 0, "negative": 0},
            "Empathy": {"positive": 0, "neutral": 0, "negative": 0},
        }
        
        for _, row in df_sent.iterrows():
            question_sentiments = row.get("question_sentiments", {})
            if isinstance(question_sentiments, dict) and len(question_sentiments) > 0:
                for q_id, q_data in question_sentiments.items():
                    if isinstance(q_data, dict):
                        if q_data.get("enable_sentiment") is not False:
                            sentiment = str(q_data.get("sentiment", "")).upper().strip()
                            dimension = q_data.get("dimension")
                            if sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE"] and dimension in dimension_sentiment_data_kpi:
                                dimension_sentiment_data_kpi[dimension][sentiment.lower()] += 1
        
        dimension_net_scores_kpi = {}
        dimension_totals_kpi = {}
        for dim, counts in dimension_sentiment_data_kpi.items():
            total = counts["positive"] + counts["neutral"] + counts["negative"]
            dimension_totals_kpi[dim] = total
            if total > 0:
                net_score = ((counts["positive"] - counts["negative"]) / total) * 100
                dimension_net_scores_kpi[dim] = net_score
            else:
                dimension_net_scores_kpi[dim] = 0
        
        has_dimension_sentiment_kpi = any(dimension_totals_kpi.values())
        total = len(df)  # Update total for KPI display

    # ══════════════════════════════════
    # KPI RIBBON
    # ══════════════════════════════════
    k1, k2 = st.columns(2)

    k1.markdown(f"""<div class="kpi-card">
      <div class="kpi-title">Total Responses</div>
      <div class="kpi-value">{total}</div>
      <div class="kpi-sub">{date_from} → {date_to}</div>
    </div>""", unsafe_allow_html=True)

    # Calculate SERVQUAL Sentiment from dimension_net_scores_kpi
    if has_dimension_sentiment_kpi:
        active_sentiment_dims = [d for d in ["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy"] if dimension_totals_kpi.get(d, 0) > 0]
        if active_sentiment_dims:
            avg_sentiment = sum(dimension_net_scores_kpi.get(d, 0) for d in active_sentiment_dims) / len(active_sentiment_dims)
            sentiment_display = f"{avg_sentiment:+.1f}%"
            sentiment_subtext = "Avg sentiment across dimensions"
            sentiment_color = '#4a7c59' if avg_sentiment > 0 else '#b03a2e' if avg_sentiment < 0 else '#8b9dc3'
        else:
            sentiment_display = "N/A"
            sentiment_subtext = "No sentiment data"
            sentiment_color = '#8b9dc3'
    else:
        sentiment_display = "N/A"
        sentiment_subtext = "No open-ended responses yet"
        sentiment_color = '#8b9dc3'
    
    k2.markdown(f"""<div class="kpi-card">
      <div class="kpi-title">Overall SERVQUAL Sentiment Net Score</div>
      <div class="kpi-value" style="color:{sentiment_color};">{sentiment_display}</div>
      <div class="kpi-sub">{sentiment_subtext}</div>
    </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════
    # CREATE TABS (AFTER FILTERS & KPI)
    # ══════════════════════════════════
    tab1, tab2, tab3, = st.tabs([
        "🎯 Sentiment",
        "📊 Numerical",
        "👥 Database",
    ])

    # ══════════════════════════════════
    # TWO DICTIONARIES TO PREVENT CONFLICT
    # ══════════════════════════════════

    # 1. Likert Dictionary (Actions point to Quantitative Tab)
    likert_dimension_descriptions = {
        "Tangibles": (
            "Physical condition of vehicles, terminal facilities, digital platforms (booking apps), and the overall commuting environment.",
            {
                "strong": "High scores here typically indicate that respondents appreciate visible physical or digital improvements. This may point to well-maintained PUVs, reliable ride-hailing apps, clean terminals, or overall comfortable commuting environments.",
                "moderate": "Mixed scores suggest that conditions are acceptable but inconsistent. Respondents might be experiencing modern units and smooth apps on some routes, while dealing with dilapidated vehicles or app glitches on others.",
                "weak": "Negative sentiment often points to physical or digital deterioration. Respondents are likely highlighting uncomfortable rides, dilapidated jeepneys/buses, inadequate waiting sheds, or glitchy booking apps.",
                "action_strong": "Review the specific Tangibles questions in the Quantitative tab to identify exactly which upgrades (e.g., vehicle condition vs. terminal cleanliness) received the highest Likert ratings, and use them as benchmarks.",
                "action_moderate": "Check the Likert Response Log chart to separate the acceptable facilities from the lower-scoring ones. Targeted maintenance on the specific items with low scores can easily lift this dimension's average.",
                "action_weak": "Prioritize a review of physical infrastructure. Look at the Quantitative breakdown to pinpoint whether the lowest Likert scores belong to the vehicles themselves, terminal facilities, or app usability.",
            }
        ),
        "Reliability": (
            "Consistency of routes, accuracy of app ETAs, ride availability during peak hours, and system dependability amid heavy traffic.",
            {
                "strong": "Positive scores suggest the transport system is generally meeting expectations. Respondents likely experience consistent routes, predictable schedules, accurate ride-hailing ETAs, or manageable wait times.",
                "moderate": "Moderate scores indicate that service operates but is vulnerable. Respondents might be tolerating occasional delays, sudden driver cancellations on apps, or a lack of capacity during peak times.",
                "weak": "Low scores strongly suggest unpredictable service. Respondents are likely expressing frustration over missed schedules, severe lack of rides during rush hour, rampant app cancellations, or major disruptions.",
                "action_strong": "Maintain current operational schedules. Check the Quantitative tab to see which specific reliability metrics (e.g., wait times vs. route consistency) contributed most to this high average score.",
                "action_moderate": "Review the individual Likert scores for Reliability to spot specific bottlenecks. Adjusting dispatch schedules or app algorithms based on the lowest-rated questions could stabilize this dimension.",
                "action_weak": "Treat system reliability as a critical issue. Check the bottom-performing questions in the Quantitative tab to see if the low scores stem primarily from wait times, traffic delays, or ride availability.",
            }
        ),
        "Responsiveness": (
            "Efficiency in managing terminal queues, swift action on commuter complaints, and agility of in-app customer support.",
            {
                "strong": "This indicates that respondents feel their immediate needs are being met. It usually reflects efficient terminal dispatching, manageable queues, or quick customer service support from ride-hailing platforms.",
                "moderate": "Reactions to commuter needs occur, but may be perceived as slow. The feedback might show that while dispatchers or app support are available, the system still struggles to adapt quickly during peak hours.",
                "weak": "Negative sentiment usually reflects a perceived lack of urgency. Respondents might be complaining about chaotic terminal queues, feeling stranded without assistance, or having their in-app complaints ignored.",
                "action_strong": "Standardize the current queue management and support strategies. Review the Quantitative tab to see if terminal dispatching or app support scored higher on the 1-5 scale.",
                "action_moderate": "Review the individual Likert scores to spot specific service gaps. Check if the moderate score is driven by low ratings on terminal queues or delayed app support.",
                "action_weak": "Address queue management and customer support immediately. Review the lowest-rated Responsiveness questions in the Quantitative tab to see exactly where respondents feel the most abandoned.",
            }
        ),
        "Assurance": (
            "Road safety, driver competence, verified app profiles, strict compliance with fare matrices, and overall public trust.",
            {
                "strong": "High scores point to strong public trust. Respondents likely feel safe on the road and perceive that drivers are competent and strictly following transport laws, fare matrices, and app pricing policies.",
                "moderate": "General trust exists, but specific concerns may be dragging the score down. Respondents might be raising occasional issues about reckless driving, unverified app drivers, or confusion over sudden fare adjustments.",
                "weak": "Low scores indicate a breakdown in trust and safety. Feedback is highly likely to contain reports of reckless driving, overcharging (colorum practices or unjustified surge pricing), or a feeling of unsafety.",
                "action_strong": "Leverage this high trust factor. Review the Likert breakdown to confirm if road safety ratings or fare compliance scores contributed most to this strong public trust.",
                "action_moderate": "Investigate the specific Assurance questions dragging the average down. Use the Quantitative tab to see if respondents rated driver safety lower, or if fare transparency took the hit.",
                "action_weak": "Safety and fare compliance audits are urgently needed. Check the bottom-rated Likert questions to identify if physical safety (reckless drivers) or financial trust (overcharging) is the primary issue.",
            }
        ),
        "Empathy": (
            "Consideration for commuter struggles, proper implementation of discounts, polite communication (in-person or chat), and humane policies.",
            {
                "strong": "Positive sentiment suggests that respondents feel considered and respected. This often points to the proper honoring of discounts and generally considerate behavior from transport crews or ride-hailing partners.",
                "moderate": "Basic courtesy is observed, but consistent empathy may be lacking. Respondents might feel that while drivers are polite, the overall system (e.g., fare costs during inflation) is not sensitive to their struggles.",
                "weak": "Negative scores typically mean respondents feel financially or personally disregarded. They might be voicing frustrations over unhonored discounts, hostile driver interactions (in-person or via app chat), or heavy financial burdens.",
                "action_strong": "Acknowledge and sustain the practices driving this score. Review the Quantitative tab to see if polite communication or discount implementation scored highest among respondents.",
                "action_moderate": "Look at the individual Empathy Likert scores to see where the disconnect lies. It may require better visible enforcement of passenger rights or reminders regarding basic courtesy.",
                "action_weak": "Review the lowest-scoring Empathy questions in the Quantitative tab. Identifying the specific numeric ratings regarding staff hostility or denied discounts is crucial before deploying new policies.",
            }
        ),
    }

    # 2. Sentiment Dictionary (Actions point to Open-Ended Feedback Logs)
    sentiment_dimension_descriptions = {
        "Tangibles": (
            "Physical condition of vehicles, terminal facilities, digital platforms (booking apps), and the overall commuting environment.",
            {
                "strong": "High Net Sentiment indicates that respondents are explicitly writing praise about visible physical or digital improvements.",
                "moderate": "Mixed sentiment suggests conditions are acceptable but inconsistent. Respondents are mentioning both good and bad physical/digital experiences in their texts.",
                "neutral": "Balanced feedback indicates that physical conditions are meeting expectations on average. Respondents have mixed experiences with vehicles and facilities.",
                "weak": "Negative Net Sentiment points to physical or digital deterioration. Respondents are actively complaining about uncomfortable rides, dilapidated units, or glitchy apps.",
                "action_strong": "Review the positive feedback in the Sentiment Tab to identify exactly which upgrades (e.g., modern units, terminal cleanliness) are driving the praise.",
                "action_moderate": "Check the Sentiment Feedback Log to separate the acceptable facilities from the problematic ones mentioned by the respondents.",
                "action_neutral": "Monitor physical conditions and facilities. Maintain current standards while identifying opportunities for improvement from commuter feedback.",
                "action_weak": "Read the raw negative comments in the Sentiment Tab to pinpoint whether the main pain points are the vehicles themselves, terminal facilities, or app crashes.",
            }
        ),
        "Reliability": (
            "Consistency of routes, accuracy of app ETAs, ride availability during peak hours, and system dependability amid heavy traffic.",
            {
                "strong": "Positive sentiment suggests the transport system is meeting expectations. Respondents are writing good things about consistent routes, predictable schedules, or manageable wait times.",
                "moderate": "Moderate scores indicate that service operates but is vulnerable. Written feedback shows respondents are tolerating occasional delays but noticing capacity issues.",
                "neutral": "Balanced feedback indicates that service reliability is stable. Respondents experience both punctual arrivals and occasional delays, averaging acceptable performance.",
                "weak": "Low Net Sentiment strongly suggests unpredictable service. Commuters are actively writing frustrations over missed schedules, severe lack of rides, or major disruptions.",
                "action_strong": "Maintain current schedules. Read the positive Sentiment Log to see what commuters value most (e.g., app ETA accuracy vs. short wait times).",
                "action_moderate": "Look into the neutral and negative comments to identify the specific times or routes causing delays based on commuter stories.",
                "action_neutral": "Keep monitoring service schedules. Track whether reliability remains consistent and look for patterns in the feedback for areas to improve.",
                "action_weak": "Treat system reliability as a critical issue. Analyze the written complaints to pinpoint whether the root cause is lack of units, chokepoints, or driver cancellations.",
            }
        ),
        "Responsiveness": (
            "Efficiency in managing terminal queues, swift action on commuter complaints, and agility of in-app customer support.",
            {
                "strong": "Commuters feel their immediate needs are being met. They are explicitly writing about efficient dispatching or quick customer service support.",
                "moderate": "Reactions to commuter needs occur, but the text feedback shows the system still struggles to adapt quickly during peak hours.",
                "neutral": "Balanced feedback indicates that the system responds adequately to commuter needs overall. Response times are generally acceptable with room for improvement.",
                "weak": "Negative sentiment usually reflects a perceived lack of urgency. Commuters are writing complaints about chaotic queues, feeling stranded, or being ignored.",
                "action_strong": "Identify the terminals or app features receiving this positive written feedback and standardize those strategies.",
                "action_moderate": "Review the neutral/negative text feedback for specific bottlenecks (e.g., slow dispatching at 6 PM, delayed chat support).",
                "action_neutral": "Continue current response practices. Seek opportunities to optimize queue management and support response times based on feedback.",
                "action_weak": "Address queue management immediately. The raw text feedback will reveal exactly where commuters feel the most abandoned.",
            }
        ),
        "Assurance": (
            "Road safety, driver competence, verified app profiles, strict compliance with fare matrices, and overall public trust.",
            {
                "strong": "High Net Sentiment points to strong public trust. Commuters are writing praise about feeling safe and trusting driver competence and fare compliance.",
                "moderate": "General trust exists, but written feedback shows specific concerns dragging the perception down, like occasional reckless driving or confusion over fares.",
                "neutral": "Balanced feedback indicates that commuters feel generally safe and trust the system. Security and fair practices are being maintained adequately.",
                "weak": "Low scores indicate a breakdown in trust. Feedback is highly likely to contain angry reports of reckless driving, overcharging, or a feeling of unsafety.",
                "action_strong": "Leverage this high trust factor. Maintain strict safety checks and transparent fare implementations, as praised in the comments.",
                "action_moderate": "Investigate the text feedback to find the specific source of doubt—is it aggressive driving, or confusion over a recent fare/surge hike?",
                "action_neutral": "Maintain current safety standards and fare compliance. Monitor feedback for any emerging concerns about driver behavior or pricing.",
                "action_weak": "Safety and fare audits are urgently needed. Read the raw comments to identify if the primary issue is physical safety (reckless drivers) or financial scamming.",
            }
        ),
        "Empathy": (
            "Consideration for commuter struggles, proper implementation of discounts, polite communication (in-person or chat), and humane policies.",
            {
                "strong": "Positive sentiment suggests commuters feel respected. They are writing about the proper honoring of discounts and considerate behavior from transport crews.",
                "moderate": "Basic courtesy is observed, but consistent empathy is lacking. Written comments suggest the overall system is not fully sensitive to their struggles.",
                "neutral": "Balanced feedback indicates that commuters are experiencing adequate courtesy and consideration. Staff interactions are generally professional and fair.",
                "weak": "Negative scores mean commuters feel disregarded. They are voicing frustrations in the text over unhonored discounts, hostile driver interactions, or heavy financial burdens.",
                "action_strong": "Acknowledge and sustain the practices driving this score based on the specific positive encounters written by commuters.",
                "action_moderate": "Read the feedback to see where the disconnect lies. Is it a lack of courtesy from specific drivers or poor enforcement of passenger rights?",
                "action_neutral": "Continue training staff on courtesy and discount protocols. Use feedback to identify any gaps in policy implementation across the network.",
                "action_weak": "Review the raw feedback closely for complaints about staff hostility or denied discounts. Addressing these emotional pain points is crucial.",
            }
        ),
    }

    # ══════════════════════════════════
    # POPULATE TABS WITH CONTENT
    # ══════════════════════════════════
    
    # ─────────────────────────────────
    # TAB 1 — Sentiment
    # ─────────────────────────────────

    with tab1:
        with st.expander("💬 Sentiment Analysis", expanded=True):
            st.markdown("""
            <div style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                        border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;">
            <div style="font-size:.72rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem;">
                SERVQUAL Sentiment Guide (Open-Ended)
            </div>
            <div style="font-size:.8rem;color:rgb(60,100,130);line-height:1.6;">
                This tab analyzes <strong>sentiment from open-ended answers</strong> (short answer / paragraph) grouped by <strong>SERVQUAL dimension</strong> tags.<br>
                <strong>Net Sentiment Score:</strong> (Positive − Negative) ÷ Total × 100 — ranges from −100% (all negative) to +100% (all positive).<br>
                <strong>How to read:</strong> positive scores indicate favorable feedback on that dimension; negative scores indicate concerns.<br>
                <strong>How to use:</strong> identify which dimensions have the strongest/weakest sentiment, then review the Sentiment tab to read actual comments.
            </div>
            </div>
            """, unsafe_allow_html=True)

            dimension_sentiment_data = {
                "Tangibles": {"positive": 0, "neutral": 0, "negative": 0},
                "Reliability": {"positive": 0, "neutral": 0, "negative": 0},
                "Responsiveness": {"positive": 0, "neutral": 0, "negative": 0},
                "Assurance": {"positive": 0, "neutral": 0, "negative": 0},
                "Empathy": {"positive": 0, "neutral": 0, "negative": 0},
            }
            
            # Re-accumulate untagged sentiments (reset from pre-calculated)
            untagged_sentiment_data = {"positive": 0, "neutral": 0, "negative": 0}

            debug_info = [] 

            for _, row in df_sent.iterrows():
                question_sentiments = row.get("question_sentiments", {})
                if isinstance(question_sentiments, dict) and len(question_sentiments) > 0:
                    for q_id, q_data in question_sentiments.items():
                        if isinstance(q_data, dict):
                            if q_data.get("enable_sentiment") is not False:
                                sentiment = str(q_data.get("sentiment", "")).upper().strip()
                                dimension = q_data.get("dimension")
                                debug_info.append({
                                    "q_id": q_id,
                                    "sentiment": sentiment,
                                    "dimension": dimension,
                                    "text": q_data.get("text", "")[:30]
                                })
                                if sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
                                    if dimension in dimension_sentiment_data:
                                        dimension_sentiment_data[dimension][sentiment.lower()] += 1
                                    else:
                                        # Count as untagged if dimension is None or not in the main dimensions
                                        untagged_sentiment_data[sentiment.lower()] += 1

            dimension_net_scores = {}
            dimension_totals = {}
            
            for dim, counts in dimension_sentiment_data.items():
                total = counts["positive"] + counts["neutral"] + counts["negative"]
                dimension_totals[dim] = total
                if total > 0:
                    net_score = ((counts["positive"] - counts["negative"]) / total) * 100
                    dimension_net_scores[dim] = net_score
                else:
                    dimension_net_scores[dim] = 0

            # Calculate untagged stats
            untagged_total = sum(untagged_sentiment_data.values())
            untagged_net_score = 0
            if untagged_total > 0:
                untagged_net_score = ((untagged_sentiment_data["positive"] - untagged_sentiment_data["negative"]) / untagged_total) * 100

            has_dimension_sentiment = any(dimension_totals.values())

            if not has_dimension_sentiment and untagged_total == 0:
                st.markdown("""<div class="empty-tab"><div class="icon">🎯</div>
                <p>No open-ended sentiment data yet.<br>
                Tag your open-ended questions (Short Answer, Paragraph) with SERVQUAL dimensions in Form Builder.<br>
                Respondents' answers will then be automatically analyzed and grouped by dimension.</p>
                </div>""", unsafe_allow_html=True)
            else:
                dim_colors = {
                    "Tangibles": "#547792",
                    "Reliability": "#1a3263",
                    "Responsiveness": "#ffc570",
                    "Assurance": "#3c6482",
                    "Empathy": "#d4a373",
                    "Untagged": "#999999",
                }
                
                chart_data = []
                for dim in ["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy"]:
                    chart_data.append({
                        "Dimension": dim,
                        "Net Sentiment Score": dimension_net_scores[dim],
                        "Total Responses": dimension_totals[dim]
                    })
                
                # Add untagged data to chart if exists
                if untagged_total > 0:
                    chart_data.append({
                        "Dimension": "Untagged",
                        "Net Sentiment Score": untagged_net_score,
                        "Total Responses": untagged_total
                    })
                
                df_chart = pd.DataFrame(chart_data)
                
                c1, c2 = st.columns([1.5, 1])
                with c1:
                    st.markdown('<div class="section-head">Net Sentiment by Dimension</div>', unsafe_allow_html=True)
                    chart = alt.Chart(df_chart).mark_bar().encode(
                        x=alt.X("Net Sentiment Score:Q", scale=alt.Scale(domain=[-100, 100]), axis=alt.Axis(title="Net Sentiment Score (%)")),
                        y=alt.Y("Dimension:N", sort=["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy", "Untagged"]),
                        color=alt.Color(
                            "Dimension:N",
                            scale=alt.Scale(domain=list(dim_colors.keys()), range=list(dim_colors.values())),
                            legend=None
                        ),
                        tooltip=["Dimension", alt.Tooltip("Net Sentiment Score:Q", format=".1f"), "Total Responses"],
                    ).properties(height=550)
                    st.altair_chart(chart, use_container_width=True)
                
                with c2:
                    st.markdown('<div class="section-head">Sentiment Breakdown</div>', unsafe_allow_html=True)
                    for dim in ["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy"]:
                        total = dimension_totals[dim]
                        if total > 0:
                            pos = dimension_sentiment_data[dim]["positive"]
                            neu = dimension_sentiment_data[dim]["neutral"]
                            neg = dimension_sentiment_data[dim]["negative"]
                            net = dimension_net_scores[dim]
                            
                            if net > 0: score_color = "#4a7c59"
                            elif net < 0: score_color = "#b03a2e"
                            else: score_color = "#8b9dc3"
                            
                            st.markdown(f"""
                            <div style="margin-bottom:1rem;padding:.75rem;border:1px solid rgba(26,50,99,0.12);border-radius:8px;background:rgba(26,50,99,0.03);">
                            <div style="font-weight:700;color:rgb(26,50,99);margin-bottom:.35rem;">{dim}</div>
                            <div style="font-size:.75rem;color:rgb(84,119,146);margin-bottom:.35rem;">
                                😊 {pos} · 😐 {neu} · 😞 {neg}
                            </div>
                            <div style="font-size:.9rem;font-weight:700;color:{score_color};">
                                Net: {net:+.1f}%
                            </div>
                            </div>""", unsafe_allow_html=True)
                    
                    # Show untagged if exists
                    if untagged_total > 0:
                        untagged_color = "#999999"
                        st.markdown(f"""
                        <div style="margin-bottom:1rem;padding:.75rem;border:1px solid rgba(26,50,99,0.12);border-radius:8px;background:rgba(150,150,150,0.03);">
                        <div style="font-weight:700;color:rgb(100,100,100);margin-bottom:.35rem;">Untagged</div>
                        <div style="font-size:.75rem;color:rgb(120,120,120);margin-bottom:.35rem;">
                            😊 {untagged_sentiment_data["positive"]} · 😐 {untagged_sentiment_data["neutral"]} · 😞 {untagged_sentiment_data["negative"]}
                        </div>
                        <div style="font-size:.9rem;font-weight:700;color:{untagged_color};">
                            Net: {untagged_net_score:+.1f}%
                        </div>
                        </div>""", unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown('<div class="section-head">📋 Analysis Conclusion</div>', unsafe_allow_html=True)

                def get_tier(net_score):
                    if net_score > 20: return "strong"
                    elif net_score > 0: return "moderate"
                    elif net_score == 0: return "neutral"
                    else: return "weak"

                tier_labels = {
                    "strong":   ("✅", "Strong (Positive)",          "#4a7c59", "rgba(74,124,89,0.08)",   "#4a7c59"),
                    "moderate": ("🙂", "Mixed",            "#8b7a2e", "rgba(139,157,195,0.08)", "#8b9dc3"),
                    "neutral":  ("😐", "Neutral",          "#8b9dc3", "rgba(139,157,195,0.08)", "#8b9dc3"),
                    "weak":     ("⚠️", "Needs attention (Negative)", "#b03a2e", "rgba(176,58,46,0.08)",  "#b03a2e"),
                }

                dim_order = ["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy"]
                active_dims = [(d, dimension_net_scores[d]) for d in dim_order if dimension_totals[d] > 0]

                # Calculate overall sentiment including both tagged and untagged responses
                if active_dims and untagged_total > 0:
                    # Average of all dimension scores plus untagged
                    all_scores = [dimension_net_scores[d] for d in dim_order if dimension_totals[d] > 0] + [untagged_net_score]
                    avg_net = sum(all_scores) / len(all_scores) if all_scores else 0
                elif active_dims:
                    # Only tagged dimensions
                    avg_net = sum(dimension_net_scores.values()) / 5 if active_dims else 0
                elif untagged_total > 0:
                    # Only untagged
                    avg_net = untagged_net_score
                else:
                    avg_net = 0

                if avg_net > 20: overall_tone, overall_color = "Predominantly positive", "#4a7c59"
                elif avg_net > 0: overall_tone, overall_color = "Moderately positive", "#6ba587"
                elif avg_net == 0: overall_tone, overall_color = "Neutral (Balanced)", "#8b9dc3"
                elif avg_net > -20: overall_tone, overall_color = "Mixed with negative lean", "#8b9dc3"
                else: overall_tone, overall_color = "Predominantly negative", "#b03a2e"

                # Map tones to descriptions
                tone_descriptions = {
                    "Predominantly positive": "Respondents are expressing strong satisfaction with the service. Most feedback emphasizes improvements and positive experiences.",
                    "Moderately positive": "Respondents generally have positive experiences, though there are some areas where satisfaction could be improved.",
                    "Neutral (Balanced)": "Sentiment is perfectly balanced. Respondents are providing factual observations without strong emotions, with equal numbers of positive and negative comments.",
                    "Mixed with negative lean": "Sentiment is divided with significant concerns. Respondents highlight problems but also recognize some positive aspects.",
                    "Predominantly negative": "Respondents express significant dissatisfaction. Negative feedback dominates, indicating urgent areas requiring attention.",
                }
                overall_description = tone_descriptions.get(overall_tone, "")

                # Find dimensions that are actually struggling (below neutral or significantly lower than others)
                # Only show "persistent friction" for dimensions that actually need attention
                strong_threshold = 20
                min_score = min([s for d, s in active_dims], default=0) if active_dims else 0
                max_score = max([s for d, s in active_dims], default=0) if active_dims else 0
                
                # Only flag as "weakest" if there's a significant gap OR if the dimension is below the strong threshold
                if max_score > strong_threshold and min_score < strong_threshold:
                    # There's a gap between struggling and strong dimensions
                    weakest_dims = [d for d, s in active_dims if s < strong_threshold]
                elif min_score <= 0:
                    # Some dimensions are negative or neutral
                    weakest_dims = [d for d, s in active_dims if s <= 0]
                else:
                    # All dimensions are doing well - no "persistent friction" to report
                    weakest_dims = []
                
                weakest_text = ", ".join(weakest_dims) if weakest_dims else "areas"

                urgent  = [(d, s) for d, s in active_dims if s < 0]
                watch   = [(d, s) for d, s in active_dims if 0 <= s <= 20]
                sustain = [(d, s) for d, s in active_dims if s > 20]

                responsive_css = """
                <style>
                .sq-conclusion { border: 1px solid rgba(26,50,99,0.12); border-radius: 12px; overflow: hidden; }
                .sq-banner { background: rgba(26,50,99,0.05); padding: 1.1rem 1.3rem; border-bottom: 1px solid rgba(26,50,99,0.10); }
                .sq-banner-label { font-size: .65rem; font-weight: 700; color: rgb(120,148,172); text-transform: uppercase; letter-spacing: .08em; margin-bottom: .35rem; }
                .sq-banner-value { font-size: 1.05rem; font-weight: 700; margin-bottom: .3rem; }
                .sq-banner-desc { font-size: .8rem; color: rgb(80,110,140); line-height: 1.6; }
                .sq-dim-grid { display: grid; grid-template-columns: 1fr 1fr; }
                .sq-dim-card { padding: 1rem 1.1rem; border-bottom: 1px solid rgba(26,50,99,0.08); border-right: 1px solid rgba(26,50,99,0.08); }
                .sq-dim-card.no-right  { border-right: none; }
                .sq-dim-card.no-bottom { border-bottom: none; }
                .sq-dim-name  { font-weight: 700; color: rgb(26,50,99); font-size: .88rem; margin-bottom: .2rem; }
                .sq-dim-desc  { font-size: .68rem; color: rgb(120,148,172); margin-bottom: .5rem; }
                .sq-dim-score { font-size: 1.35rem; font-weight: 700; margin-bottom: .3rem; }
                .sq-dim-pill  { display: inline-flex; align-items: center; gap: 5px; background: rgba(255,255,255,0.6); border-radius: 999px; padding: .15rem .6rem; font-size: .65rem; font-weight: 700; margin-bottom: .6rem; }
                .sq-dim-insight { font-size: .75rem; color: rgb(80,110,140); line-height: 1.6; margin-bottom: .5rem; }
                .sq-dim-action  { font-size: .72rem; color: rgb(80,110,140); line-height: 1.55; padding-left: .6rem; font-style: italic; border-left-width: 3px; border-left-style: solid; }
                .sq-dim-counts  { font-size: .65rem; color: rgb(150,170,190); margin-top: .5rem; }
                .sq-priority { padding: 1rem 1.3rem; background: rgba(26,50,99,0.04); border-top: 1px solid rgba(26,50,99,0.10); }
                .sq-priority-label { font-size: .68rem; font-weight: 700; color: rgb(120,148,172); text-transform: uppercase; letter-spacing: .08em; margin-bottom: .7rem; }
                .sq-priority-row { display: flex; gap: 10px; align-items: flex-start; margin-bottom: .55rem; flex-wrap: wrap; }
                .sq-priority-badge { font-size: .65rem; font-weight: 700; border-radius: 4px; padding: .2rem .55rem; white-space: nowrap; flex-shrink: 0; }
                .sq-priority-text  { font-size: .75rem; color: rgb(80,110,140); line-height: 1.5; min-width: 0; }
                @media (max-width: 640px) {
                .sq-dim-grid { grid-template-columns: 1fr; }
                .sq-dim-card { border-right: none !important; }
                .sq-dim-card.no-bottom-mobile { border-bottom: none; }
                .sq-priority-row { gap: 6px; }
                .sq-priority-badge { font-size: .62rem; }
                .sq-dim-score { font-size: 1.15rem; }
                .sq-banner-value { font-size: .95rem; }
                }
                </style>
                """

                html = responsive_css + '<div class="sq-conclusion">'

                html += f"""
                <div class="sq-banner">
                <div class="sq-banner-label">Overall sentiment signal</div>
                <div class="sq-banner-value" style="color:{overall_color};">{overall_tone} ({avg_net:+.1f}% net)</div>
                <div class="sq-banner-desc">
                    <div style="margin-bottom: 0.6rem;"><strong>{overall_description}</strong></div>
                    <div>{"Specific areas of concern: <strong>" + weakest_text + "</strong>" if weakest_text and weakest_text != "areas" else "Collect more open-ended responses to deepen the analysis."}</div>
                </div>
                </div>"""

                html += '<div class="sq-dim-grid">'
                total_cards = len(active_dims)

                for i, (dim, net) in enumerate(active_dims):
                    # USE THE SENTIMENT DICTIONARY HERE
                    desc_tuple = sentiment_dimension_descriptions.get(dim)
                    if not desc_tuple: continue
                    
                    desc, insight_map = desc_tuple
                    tier = get_tier(net)
                    emoji, label, color, bg, border_color = tier_labels[tier]
                    insight = insight_map[tier]
                    action  = insight_map[f"action_{tier}"]

                    pos   = dimension_sentiment_data[dim]["positive"]
                    neu   = dimension_sentiment_data[dim]["neutral"]
                    neg   = dimension_sentiment_data[dim]["negative"]
                    total = dimension_totals[dim]

                    is_last_card    = (i == total_cards - 1)
                    is_right_col    = (i % 2 == 1)
                    last_row_start  = total_cards - (1 if total_cards % 2 != 0 else 2)
                    no_bottom       = "no-bottom" if i >= last_row_start else ""
                    no_right        = "no-right"  if is_right_col or (is_last_card and total_cards % 2 != 0) else ""
                    no_bottom_mob   = "no-bottom-mobile" if is_last_card else ""

                    html += f"""
                    <div class="sq-dim-card {no_right} {no_bottom} {no_bottom_mob}" style="background:{bg};">
                    <div class="sq-dim-name">{dim}</div>
                    <div class="sq-dim-desc">{desc}</div>
                    <div class="sq-dim-score" style="color:{color};">{net:+.1f}%</div>
                    <div class="sq-dim-pill" style="border:1px solid {border_color};color:{color};">{emoji} {label}</div>
                    <div class="sq-dim-insight">{insight}</div>
                    <div class="sq-dim-action" style="border-left-color:{border_color};">{action}</div>
                    <div class="sq-dim-counts">😊 {pos} &nbsp;·&nbsp; 😐 {neu} &nbsp;·&nbsp; 😞 {neg} &nbsp;·&nbsp; {total} total</div>
                    </div>"""

                html += '</div>'

                # ── Priority triage (UPDATED FOR OPEN-ENDED SENTIMENT) ──
                html += '<div class="sq-priority"><div class="sq-priority-label">Where to act next (Based on Commuter Comments)</div>'

                if urgent:
                    names = " · ".join(d for d, _ in urgent)
                    html += f"""<div class="sq-priority-row">
                    <span class="sq-priority-badge" style="background:rgba(176,58,46,0.12);color:#b03a2e;">Urgent — {names}</span>
                    <span class="sq-priority-text">Negative Net Sentiment Scores (-%) indicate that commuters are actively writing complaints about these areas. Review the specific negative comments in the <strong>Sentiment Tab (Feedback Log)</strong> to understand the exact context of their frustration before intervening.</span>
                    </div>"""

                if watch:
                    names = " · ".join(d for d, _ in watch)
                    html += f"""<div class="sq-priority-row">
                    <span class="sq-priority-badge" style="background:rgba(255,197,112,0.18);color:#8b5e1a;">Monitor — {names}</span>
                    <span class="sq-priority-text">Low but positive Net Sentiment Scores (0–20%) indicate mixed written feedback. Commuters are mentioning both good and bad experiences. Read the neutral and negative logs to see what specific minor issues are preventing a purely positive experience.</span>
                    </div>"""

                if sustain:
                    names = " · ".join(d for d, _ in sustain)
                    html += f"""<div class="sq-priority-row">
                    <span class="sq-priority-badge" style="background:rgba(74,124,89,0.12);color:#4a7c59;">Sustain — {names}</span>
                    <span class="sq-priority-text">High Net Sentiment Scores (+20%) show strong praise in the open-ended responses. Commuters are explicitly writing good things about these dimensions. Use their exact positive quotes in your reports to highlight system strengths.</span>
                    </div>"""

                html += '</div></div>'
                st.markdown(html, unsafe_allow_html=True)
                
                # ── Untagged Sentiments Analysis ──
                if untagged_total > 0:
                    st.markdown("---")
                    st.markdown('<div class="section-head">💬 Untagged Open-Ended Responses</div>', unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='font-size:.8rem;color:rgb(80,110,140);margin-bottom:1rem;'>"
                        f"These {untagged_total} response(s) were not tagged with a SERVQUAL dimension. "
                        f"Tag questions in Form Builder to categorize feedback automatically."
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    
                    # Display untagged sentiment distribution
                    untagged_cols = st.columns(3)
                    with untagged_cols[0]:
                        st.metric("😊 Positive", untagged_sentiment_data["positive"])
                    with untagged_cols[1]:
                        st.metric("😐 Neutral", untagged_sentiment_data["neutral"])
                    with untagged_cols[2]:
                        st.metric("😞 Negative", untagged_sentiment_data["negative"])
                    
                    # Untagged conclusion card
                    if untagged_net_score > 20:
                        untagged_tier = "strong"
                        untagged_emoji, untagged_label = "✅", "Positive"
                        untagged_color, untagged_bg = "#4a7c59", "rgba(74,124,89,0.08)"
                        untagged_meaning = "Strong praise in untagged responses. Commuters are writing positive feedback that doesn't fit neatly into SERVQUAL categories."
                        untagged_action = "📌 Recommended action: Review positive comments in the Feedback Log. Identify themes and consider adding new SERVQUAL-tagged questions if these issues are important to track."
                    elif untagged_net_score > 0:
                        untagged_tier = "moderate"
                        untagged_emoji, untagged_label = "🙂", "Mixed"
                        untagged_color, untagged_bg = "#8b7a2e", "rgba(139,157,195,0.08)"
                        untagged_meaning = "Mixed feedback in untagged responses. Commuters mention both positive and negative experiences that haven't been categorized."
                        untagged_action = "📌 Recommended action: Read both positive and negative comments in the Feedback Log. Determine if recurring themes should be tagged to a specific SERVQUAL dimension for better tracking."
                    elif untagged_net_score == 0:
                        untagged_tier = "neutral"
                        untagged_emoji, untagged_label = "😐", "Neutral"
                        untagged_color, untagged_bg = "#8b9dc3", "rgba(139,157,195,0.08)"
                        untagged_meaning = "Balanced feedback in untagged responses. Equal numbers of positive and negative comments that don't have a clear dimension tag."
                        untagged_action = "📌 Recommended action: Monitor these responses. Tag questions to categorize feedback more precisely, or review if these comments are truly out-of-scope."
                    else:
                        untagged_tier = "weak"
                        untagged_emoji, untagged_label = "⚠️", "Needs attention"
                        untagged_color, untagged_bg = "#b03a2e", "rgba(176,58,46,0.08)"
                        untagged_meaning = "Negative feedback in untagged responses. Commuters are voicing concerns that haven't been assigned to a SERVQUAL dimension."
                        untagged_action = "📌 Recommended action: Prioritize reading negative comments in the Feedback Log. Identify the topics and create SERVQUAL-tagged questions to track these issues going forward."
                    
                    st.markdown(f"""
                    <div style="border:1px solid rgba(26,50,99,0.12);border-radius:12px;padding:1rem 1.2rem;background:{untagged_bg};margin-top:1rem;">
                    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:1rem;">
                        <div style="font-size:2rem;font-weight:700;color:{untagged_color};">{untagged_net_score:+.1f}%</div>
                        <div style="flex:1;">
                        <div style="font-size:.95rem;font-weight:700;color:{untagged_color};">{untagged_emoji} Net Sentiment: {untagged_label}</div>
                        <div style="font-size:.75rem;color:rgb(80,110,140);margin-top:2px;">
                            {untagged_meaning}
                        </div>
                        </div>
                    </div>
                    <div style="padding:.8rem;background:rgba(255,255,255,0.5);border-left:3px solid {untagged_color};border-radius:4px;font-size:.8rem;color:rgb(60,80,100);line-height:1.5;">
                        {untagged_action}
                    </div>
                    </div>
                    """, unsafe_allow_html=True)

        with st.expander("📊 Sentiment Data", expanded=True):
            st.markdown("""
            <div class="sentiment-guide-full" style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                        border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;">
            <div style="font-size:.72rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem;">
                Sentiment Guide
            </div>
            <div style="font-size:.8rem;color:rgb(60,100,130);line-height:1.6;">
                This tab is for <strong>open-ended answers</strong> (short answer / paragraph), not Likert scores.<br>
                <strong>Distribution:</strong> share of positive, neutral, and negative labels from the AI model for the selected date range.<br>
                <strong>Avg confidence:</strong> average model certainty per label (higher usually means the automatic tag is more stable—still validate important quotes manually).<br>
                <strong>Feedback log:</strong> question text, respondent answer, sentiment, and time—use it to read <em>what</em> respondents said about land public transportation (experience, drivers, conditions, etc.) and to back up charts with real wording.<br>
                <strong>How to use:</strong> spot themes in negative or positive comments, quote in reports or briefings when helpful, and cross-check against your quantitative SERVQUAL results.
            </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="sentiment-guide-mobile" style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                        border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.6rem .8rem;margin-bottom:1rem;">
            <div style="font-size:.65rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.25rem;">
                Sentiment Analysis
            </div>
            <div style="font-size:.75rem;color:rgb(60,100,130);line-height:1.5;">
                AI analysis of open-ended responses. <strong>Distribution</strong> shows sentiment breakdown. <strong>Confidence</strong> indicates prediction certainty.
            </div>
            </div>
            """, unsafe_allow_html=True)

            # Sentiment Rate Cards
            r1, r2, r3 = st.columns(3)

            r1.markdown(f"""<div class="kpi-card">
            <div class="kpi-title">Positive Rate</div>
            <div class="kpi-value pos">{pos_rate:.1f}%</div>
            <div class="kpi-sub">{pos_count} responses</div>
            </div>""", unsafe_allow_html=True)

            r2.markdown(f"""<div class="kpi-card">
            <div class="kpi-title">Neutral Rate</div>
            <div class="kpi-value neu" style="color: var(--neu);">{neu_rate:.1f}%</div>
            <div class="kpi-sub">{neu_count} responses</div>
            </div>""", unsafe_allow_html=True)

            r3.markdown(f"""<div class="kpi-card">
            <div class="kpi-title">Negative Rate</div>
            <div class="kpi-value neg" style="color: var(--neg);">{neg_rate:.1f}%</div>
            <div class="kpi-sub">{neg_count} responses</div>
            </div>""", unsafe_allow_html=True)

            # Sentiment Insights
            st.markdown("""
            <div style="background:rgba(139,157,195,0.08);border:1px solid rgba(139,157,195,0.2);border-radius:8px;padding:1rem;margin-bottom:0.5rem;">
            <div style="font-size:.75rem;font-weight:700;color:rgb(60,100,130);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem;">
                📊 What These Rates Mean
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem;font-size:.8rem;color:rgb(80,110,140);line-height:1.5;">
                <div>
                <span style="font-weight:700;color:#4a7c59;">Positive:</span> Respondents are satisfied and writing praise. They experience good service, reliability, or satisfaction with aspects of public transportation.
                </div>
                <div>
                <span style="font-weight:700;color:#8b9dc3;">Neutral:</span> Respondents are providing factual observations without strong emotions. They describe experiences matter-of-factly.
                </div>
                <div>
                <span style="font-weight:700;color:#b03a2e;">Negative:</span> Respondents are expressing complaints, frustrations, or concerns. These are priority areas for improvement.
                </div>
            </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="height: 0.5rem;"></div>
            """, unsafe_allow_html=True)

            if df_sent.empty:
                st.markdown("""<div class="empty-tab"><div class="icon">💬</div>
                <p>No analyzed responses yet.<br>
                The AI model processes open-text answers automatically on submission.<br>
                Make sure your form has at least one Short Answer or Paragraph question.</p>
                </div>""", unsafe_allow_html=True)
            else:
                all_sentiments_list = []
                all_confidence_scores = []
                
                for _, row in df_sent.iterrows():
                    response_level_sent = str(row.get(sent_col, "")).upper().strip() if sent_col in row else ""
                    response_level_score = row.get("sentiment_score")
                    question_sentiments = row.get("question_sentiments", {})
                    
                    has_question_sentiments = False
                    if isinstance(question_sentiments, dict) and len(question_sentiments) > 0:
                        for q_id, q_data in question_sentiments.items():
                            if isinstance(q_data, dict):
                                if q_data.get("enable_sentiment") is not False:
                                    sentiment = str(q_data.get("sentiment", "")).upper().strip()
                                    if sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
                                        has_question_sentiments = True
                                        all_sentiments_list.append(sentiment)
                                        
                                        confidence = q_data.get("confidence")
                                        if confidence is None:
                                            confidence = q_data.get("sentiment_score")
                                        
                                        if confidence is None:
                                            confidence = response_level_score
                                        
                                        if pd.notna(confidence):
                                            try:
                                                all_confidence_scores.append({
                                                    "sentiment": sentiment,
                                                    "confidence": float(confidence)
                                                })
                                            except:
                                                pass
                    
                    if not has_question_sentiments and response_level_sent and response_level_sent != "PENDING":
                        all_sentiments_list.append(response_level_sent)
                        if pd.notna(response_level_score):
                            try:
                                all_confidence_scores.append({
                                    "sentiment": response_level_sent,
                                    "confidence": float(response_level_score)
                                })
                            except:
                                pass
                
                sentiment_counts = {
                    "POSITIVE": all_sentiments_list.count("POSITIVE"),
                    "NEUTRAL": all_sentiments_list.count("NEUTRAL"),
                    "NEGATIVE": all_sentiments_list.count("NEGATIVE"),
                }
                
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown('<div class="section-head">Distribution</div>', unsafe_allow_html=True)
                    
                    sc = pd.DataFrame([
                        {"Sentiment": "POSITIVE", "Count": sentiment_counts.get("POSITIVE", 0)},
                        {"Sentiment": "NEUTRAL", "Count": sentiment_counts.get("NEUTRAL", 0)},
                        {"Sentiment": "NEGATIVE", "Count": sentiment_counts.get("NEGATIVE", 0)},
                    ])
                    
                    st.altair_chart(
                        alt.Chart(sc)
                        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                        .encode(
                            x=alt.X("Sentiment:N", sort=["POSITIVE", "NEUTRAL", "NEGATIVE"], axis=alt.Axis(labelAngle=0)),
                            y="Count:Q",
                            color=alt.Color(
                                "Sentiment:N",
                                scale=alt.Scale(
                                    domain=["POSITIVE", "NEUTRAL", "NEGATIVE"],
                                    range=["#4a7c59", "#8b9dc3", "#b03a2e"],
                                ),
                                legend=None,
                            ),
                            tooltip=["Sentiment", "Count"],
                        )
                        .properties(height=200),
                        use_container_width=True,
                    )
                    
                    st.caption(f"Positive: {sentiment_counts.get('POSITIVE', 0)} | Neutral: {sentiment_counts.get('NEUTRAL', 0)} | Negative: {sentiment_counts.get('NEGATIVE', 0)}")

                    st.markdown('<div class="section-head">Avg Confidence</div>', unsafe_allow_html=True)
                    
                    confidence_by_sentiment = {
                        "POSITIVE": [],
                        "NEUTRAL": [],
                        "NEGATIVE": [],
                    }
                    
                    for score_data in all_confidence_scores:
                        sentiment = score_data["sentiment"]
                        confidence = score_data["confidence"]
                        if sentiment in confidence_by_sentiment:
                            confidence_by_sentiment[sentiment].append(confidence)
                    
                    sentiment_list = [("POSITIVE", "#4a7c59"), ("NEUTRAL", "#8b9dc3"), ("NEGATIVE", "#b03a2e")]
                    for s, color in sentiment_list:
                        scores = confidence_by_sentiment.get(s, [])
                        if scores:
                            pct = (sum(scores) / len(scores)) * 100
                        else:
                            pct = 0
                        st.markdown(f"""
                        <div style="margin-bottom:.5rem;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:.15rem;">
                            <span style="font-size:.72rem;font-weight:700;color:{color};">{s}</span>
                            <span style="font-size:.72rem;color:rgb(120,148,172);">{pct:.1f}%</span>
                        </div>
                        <div class="conf-bar-wrap">
                            <div class="conf-bar" style="width:{pct:.1f}%;background:{color};"></div>
                        </div>
                        </div>""", unsafe_allow_html=True)

                with c2:
                    st.markdown('<div class="section-head">Feedback Log</div>', unsafe_allow_html=True)

                    demo_question_set = {
                        "What is your age bracket?",
                        "What is your gender?",
                        "What is your primary occupation?",
                        "What primary land public transportation mode do you usually use?",
                        "Which PUV or transport types do you usually ride or use? (Select all that apply)",
                        "Which land public transportation modes do you usually use? (Select all that apply)",
                        "How often do you commute?",
                    }
                    log_rows = []
                    
                    try:
                        q_text_to_id = {}
                        q_res = conn.client.table("form_questions").select("id, prompt").eq("admin_email", admin_email).eq("form_id", current_form_id).execute()
                        for q_row in (q_res.data or []):
                            q_text_to_id[q_row.get("prompt", "")] = str(q_row.get("id", ""))
                    except Exception:
                        q_text_to_id = {}
                    
                    for _, row in df_sent.iterrows():
                        ans_map = row.get("answers", {})
                        question_sentiments = row.get("question_sentiments", {})
                        response_level_confidence = row.get("sentiment_score", None)
                        submitted  = row.get("created_at", None)
                        if not isinstance(ans_map, dict):
                            continue

                        idx = 0
                        for question, answer in ans_map.items():
                            answer_text = str(answer).strip() if answer is not None else ""
                            if not answer_text:
                                continue
                            if question in demo_question_set:
                                continue
                            if pd.notna(pd.to_numeric(answer_text, errors="coerce")):
                                continue
                            
                            q_id = q_text_to_id.get(question)
                            
                            if isinstance(question_sentiments, dict):
                                # Try to look up by ID first (primary key in question_sentiments)
                                # Then fall back to question text
                                q_data = None
                                if q_id:
                                    q_data = question_sentiments.get(q_id, {})
                                if not q_data or not isinstance(q_data, dict) or not q_data.get("sentiment"):
                                    q_data = question_sentiments.get(question, {})
                                
                                if isinstance(q_data, dict):
                                    if q_data.get("enable_sentiment") is False:
                                        continue
                                    
                                    q_sentiment = q_data.get("sentiment")
                                    q_sentiment_upper = str(q_sentiment).upper().strip() if q_sentiment else ""
                                    
                                    if not q_sentiment_upper or q_sentiment_upper == "PENDING":
                                        continue
                                    
                                    idx += 1
                                    sentiment_display = q_sentiment_upper
                                    
                                    # Use per-question confidence if available, otherwise fall back to response-level
                                    q_confidence = q_data.get("confidence")
                                    if q_confidence is None:
                                        q_confidence = response_level_confidence
                                    
                                    # Get SERVQUAL dimension for this question
                                    # First check if dimension is already in question_sentiments (from public_form.py)
                                    q_dimension = q_data.get("dimension")
                                    # If not found there, try looking up from form schema by ID or text
                                    if not q_dimension:
                                        if q_id:
                                            # Try both string and non-string formats
                                            q_dimension = form_schema_full.get("by_id", {}).get(str(q_id), {}).get("dimension")
                                            if not q_dimension:
                                                q_dimension = form_schema_full.get("by_id", {}).get(q_id, {}).get("dimension")
                                        if not q_dimension:
                                            q_dimension = form_schema.get(question, {}).get("dimension")
                                    dimension_display = q_dimension if q_dimension else "Untagged"
                                    
                                    log_rows.append({
                                        "Response #": f"#{idx}",
                                        "Question": str(question),
                                        "Dimension": dimension_display,
                                        "Answer": answer_text,
                                        "Sentiment": sentiment_display,
                                        "Confidence": f"{q_confidence*100:.1f}%" if pd.notna(q_confidence) else "N/A",
                                        "Submitted": submitted,
                                    })

                    if log_rows:
                        log_df = pd.DataFrame(log_rows)
                        
                        # Add filters for feedback log
                        st.markdown('<div style="font-size:0.75rem;font-weight:700;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:0.8rem;">Filter Feedback</div>', unsafe_allow_html=True)
                        
                        filter_col1, filter_col2, filter_col3 = st.columns(3)
                        
                        with filter_col1:
                            sentiment_filter = st.multiselect(
                                "Filter by Sentiment",
                                options=["POSITIVE", "NEUTRAL", "NEGATIVE"],
                                default=[],
                                key="log_sentiment_filter"
                            )
                        
                        with filter_col2:
                            dimension_options = sorted(log_df["Dimension"].unique().tolist())
                            dimension_filter = st.multiselect(
                                "Filter by Dimension",
                                options=dimension_options,
                                default=[],
                                key="log_dimension_filter"
                            )
                        
                        with filter_col3:
                            question_options = sorted(log_df["Question"].unique().tolist())
                            question_filter = st.multiselect(
                                "Filter by Question",
                                options=question_options,
                                default=[],
                                key="log_question_filter"
                            )
                        
                        # Apply filters - if nothing selected, show all
                        if sentiment_filter or dimension_filter or question_filter:
                            filtered_log_df = log_df[
                                (log_df["Sentiment"].isin(sentiment_filter) if sentiment_filter else True) &
                                (log_df["Dimension"].isin(dimension_filter) if dimension_filter else True) &
                                (log_df["Question"].isin(question_filter) if question_filter else True)
                            ]
                        else:
                            filtered_log_df = log_df

                        def color_sent(val):
                            val_upper = str(val).upper().strip() if val else ""
                            return {
                                "POSITIVE": "color:#4a7c59;font-weight:700",
                                "NEGATIVE": "color:#b03a2e;font-weight:700",
                                "NEUTRAL":  "color:#8b9dc3;font-weight:700",
                                "⏳ PENDING": "color:#ffc570;font-weight:700",
                            }.get(val_upper if "PENDING" not in str(val) else "⏳ PENDING", "")

                        st.markdown(f'<div style="font-size:0.8rem;color:rgb(120,148,172);margin-bottom:0.8rem;">Showing {len(filtered_log_df)} of {len(log_df)} feedback entries</div>', unsafe_allow_html=True)
                        
                        st.dataframe(
                            filtered_log_df[["Response #", "Question", "Dimension", "Answer", "Sentiment", "Confidence"]].style.map(color_sent, subset=["Sentiment"]),
                            use_container_width=True,
                            hide_index=True,
                            height=300,
                        )
                    else:
                        st.info("No open-text feedback in the selected range.")
                
                # Sentiment Conclusion
                # Generate dynamic conclusion based on rates
                if total_sentiments > 0:
                    sentiment_summary = ""
                    
                    if pos_rate > 60:
                        sentiment_summary = f"<strong style=\"color:#4a7c59;\">✅ Strongly Positive Sentiment:</strong> With {pos_rate:.1f}% positive responses, respondents are generally satisfied with public transportation services. This indicates good operational performance and customer satisfaction. Focus on maintaining these positive aspects while addressing the {neg_rate:.1f}% negative feedback."
                    elif pos_rate > 40:
                        sentiment_summary = f"<strong style=\"color:#6ba587;\">🙂 Moderately Positive Sentiment:</strong> With {pos_rate:.1f}% positive and {neg_rate:.1f}% negative responses, there's a mixed but overall favorable sentiment. Respondents appreciate certain aspects but have concerns about others. Investigate the {neg_rate:.1f}% negative comments to identify specific pain points for improvement."
                    elif neu_rate >= 80 or (pos_rate < 5 and neg_rate < 5):
                        # Pure neutral: most responses are neutral with minimal positive/negative
                        sentiment_summary = f"<strong style=\"color:#8b9dc3;\">😐 Neutral Sentiment:</strong> With {neu_rate:.1f}% neutral responses, respondents are providing factual observations without strong emotions. They describe experiences matter-of-factly without expressing significant satisfaction or dissatisfaction. This suggests respondents view the service as adequate but unremarkable."
                    elif pos_rate > neg_rate:
                        sentiment_summary = f"<strong style=\"color:#8b9dc3;\">😐 Balanced Sentiment:</strong> Responses are divided between positive ({pos_rate:.1f}%), neutral ({neu_rate:.1f}%), and negative ({neg_rate:.1f}%). This suggests varied experiences across respondents. Review the detailed feedback log to understand specific issues and successes."
                    else:
                        sentiment_summary = f"<strong style=\"color:#b03a2e;\">⚠️ Negative Sentiment Concern:</strong> With {neg_rate:.1f}% negative responses compared to {pos_rate:.1f}% positive, there are significant concerns about public transportation services. This requires immediate attention. Review negative comments in the feedback log to identify and prioritize issues for resolution."
                    
                    st.markdown(f"""
                    <div style="background:rgba(84,119,146,0.06);border:1px solid rgba(84,119,146,0.15);border-left:4px solid rgb(84,119,146);border-radius:8px;padding:1.2rem;margin:1rem 0;">
                    <div style="font-size:.75rem;font-weight:700;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:0.75rem;display:flex;align-items:center;gap:8px;">
                        <span>📊 Sentiment Analysis Conclusion</span>
                    </div>
                    
                    <div style="font-size:.85rem;color:rgb(60,100,130);line-height:1.7;margin-bottom:0.75rem;">
                        {sentiment_summary}
                    </div>
                    
                    <div style="margin-top:0.75rem;padding-top:0.75rem;border-top:1px solid rgba(84,119,146,0.1);">
                        <div style="font-size:.75rem;color:rgb(100,130,160);margin-bottom:0.5rem;"><strong>Key Recommendations:</strong></div>
                        <ul style="font-size:.8rem;color:rgb(80,110,140);margin:0;padding-left:1.5rem;">
                        <li>Review and quote negative feedback in reports to drive action on service improvements</li>
                        <li>Identify recurring themes in positive responses to replicate successful practices</li>
                        <li>Use dimension sentiment (below) to pinpoint which SERVQUAL areas need attention</li>
                        <li>Monitor sentiment trends over time to measure the impact of improvements</li>
                        </ul>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background:rgba(84,119,146,0.06);border:1px solid rgba(84,119,146,0.15);border-left:4px solid rgb(84,119,146);border-radius:8px;padding:1.2rem;margin:1rem 0;">
                    <div style="font-size:.75rem;font-weight:700;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:0.75rem;display:flex;align-items:center;gap:8px;">
                        <span>📊 Sentiment Analysis Conclusion</span>
                    </div>
                    <div style="font-size:.85rem;color:rgb(100,130,160);">
                        No sentiment data available yet. Collect responses with open-ended questions to analyze sentiment and identify service improvement opportunities.
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('<div class="section-head">Sentiment by Question</div>', unsafe_allow_html=True)
                st.caption("Shows how many positive, negative, and neutral responses each question received.")
                
                q_sentiment_data = []
                
                if "question_sentiments" in df_sent.columns:
                    # Build ID-to-prompt mapping from form schema for lookups
                    id_to_prompt = form_schema_full.get("by_id", {})
                    
                    for _, row in df_sent.iterrows():
                        question_sentiments = row.get("question_sentiments", {})
                        
                        if isinstance(question_sentiments, dict):
                            # question_sentiments is keyed by question ID, so we need to look up the prompt
                            for question_id, q_data in question_sentiments.items():
                                if isinstance(q_data, dict):
                                    if q_data.get("enable_sentiment") is False:
                                        continue
                                    
                                    sentiment = q_data.get("sentiment")
                                    if sentiment:
                                        sentiment_upper = str(sentiment).upper().strip()
                                        if sentiment_upper != "PENDING" and sentiment_upper in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
                                            # Look up question prompt by ID, trying both formats
                                            q_info = id_to_prompt.get(str(question_id), {})
                                            if not q_info:
                                                q_info = id_to_prompt.get(question_id, {})
                                            question_prompt = q_info.get("prompt", str(question_id))
                                            
                                            q_sentiment_data.append({
                                                "Question": question_prompt,
                                                "Sentiment": sentiment_upper
                                            })
                
                if q_sentiment_data:
                    q_sent_df = pd.DataFrame(q_sentiment_data)
                    
                    q_pivot = q_sent_df.groupby(["Question", "Sentiment"]).size().reset_index(name="Count")
                    
                    all_questions = q_pivot["Question"].unique()
                    all_sentiments = ["POSITIVE", "NEUTRAL", "NEGATIVE"]
                    
                    full_pivot = []
                    for q in all_questions:
                        for s in all_sentiments:
                            count = q_pivot[(q_pivot["Question"] == q) & (q_pivot["Sentiment"] == s)]["Count"].values
                            full_pivot.append({
                                "Question": q,
                                "Sentiment": s,
                                "Count": int(count[0]) if len(count) > 0 else 0
                            })
                    
                    full_pivot_df = pd.DataFrame(full_pivot)
                    
                    if not full_pivot_df.empty:
                        chart = (
                            alt.Chart(full_pivot_df)
                            .mark_bar()
                            .encode(
                                x=alt.X("Count:Q", title="Number of Responses"),
                                y=alt.Y("Question:N", title="", sort="-x"),
                                color=alt.Color(
                                    "Sentiment:N",
                                    scale=alt.Scale(
                                        domain=["POSITIVE", "NEUTRAL", "NEGATIVE"],
                                        range=["#4a7c59", "#8b9dc3", "#b03a2e"],
                                    ),
                                    legend=alt.Legend(title="Sentiment")
                                ),
                                tooltip=["Question:N", "Sentiment:N", "Count:Q"],
                            )
                            .properties(height=max(300, len(all_questions) * 40))
                        )
                        st.altair_chart(chart, use_container_width=True)
                        
                        st.markdown('<div class="section-head">Sentiment Counts by Question</div>', unsafe_allow_html=True)
                        pivot_table = full_pivot_df.pivot(index="Question", columns="Sentiment", values="Count").fillna(0).astype(int)
                        pivot_table["Total"] = pivot_table.sum(axis=1)
                        pivot_table = pivot_table[["POSITIVE", "NEUTRAL", "NEGATIVE", "Total"]]
                        st.dataframe(pivot_table, use_container_width=True)
                    else:
                        st.info("No per-question sentiment data available.")
                else:
                    st.info("No per-question sentiment analysis available. Enable sentiment analysis for questions in Form Builder.")

    # ─────────────────────────────────
    # TAB 2 — Numerical
    # ─────────────────────────────────

    with tab2:
        # Overall SERVQUAL KPI Card
        col_servqual = st.columns(1)[0]
        servqual_display = (
            f"{overall_avg:.2f}<span style='font-size:1rem'> /5</span>"
            if has_servqual_data else "N/A"
        )
        servqual_subtext = "Avg of 5 SERVQUAL dimensions" if has_servqual_data else "No SERVQUAL tags yet"
        col_servqual.markdown(f"""<div class="kpi-card">
          <div class="kpi-title">Overall SERVQUAL</div>
          <div class="kpi-value gold">{servqual_display}</div>
          <div class="kpi-sub">{servqual_subtext}</div>
        </div>""", unsafe_allow_html=True)
        
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
        
        with st.expander("🕸 Servqual Radar", expanded=True):
            st.markdown("""
            <div style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                        border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;">
            <div style="font-size:.72rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem;">
                SERVQUAL Guide (Likert Scale Only)
            </div>
            <div style="font-size:.8rem;color:rgb(60,100,130);line-height:1.6;">
                This radar summarizes <strong>land public transportation</strong> feedback from your survey—broadly:
                <strong>service experience</strong>, <strong>vehicles and facilities</strong>, <strong>people involved</strong> (e.g. crew and passengers),
                and how riders see the <strong>current situation</strong> (e.g. delays, travel conditions, or how <strong>cost and operating pressures</strong> affect the trip).
                Your exact topics depend on how you wrote your Likert items; the radar only groups them under SERVQUAL.<br>
                Scores come only from <strong>Likert averages</strong> tagged to SERVQUAL dimensions
                (Tangibles, Reliability, Responsiveness, Assurance, Empathy).<br>
                <strong>Scale conversion:</strong> any Likert scale with values above <strong>5</strong>
                is normalized to a <strong>1 to 5</strong> scale for consistent SERVQUAL computation.<br>
                <strong>How to read:</strong> each spoke is one dimension on a <strong>1 to 5</strong> scale;
                farther from the center means stronger perceived quality on that dimension.<br>
                <strong>How to use:</strong> use this chart to see what dimension-level data you already have from discussions
                about land public transportation in your responses.
            </div>
            </div>
            """, unsafe_allow_html=True)

            if not has_servqual_data and not has_general_ratings:
                st.markdown("""<div class="empty-tab"><div class="icon">🕸</div>
                <p>No SERVQUAL dimension scores or General Ratings yet.<br><br>
                In <strong>Form Builder</strong>, add Likert questions to your form.
                Assign them to SERVQUAL dimensions (Tangibles, Reliability, Responsiveness, Assurance, Empathy)
                for dimension-specific tracking, or leave them untagged for <em>General Ratings</em>.</p>
                </div>""", unsafe_allow_html=True)
            else:
                # Recalculate radar data using FILTERED data
                normalized_df_filtered = df[list(present_servqual_dims.values())].copy()
                
                observed_max_filtered = normalized_df_filtered.max().max()
                if pd.isna(observed_max_filtered) or observed_max_filtered <= 0:
                    scale_max_filtered = 5
                else:
                    scale_max_filtered = float(observed_max_filtered) if observed_max_filtered > 5 else 5
                
                for col in present_servqual_dims.values():
                    normalized_df_filtered[col] = normalized_df_filtered[col].apply(lambda x: normalize_to_5(x, scale_max_filtered))
                
                # Build radar data from SERVQUAL dimensions and/or General Ratings
                dim_means = {}
                
                # Add SERVQUAL dimensions if present
                if has_servqual_data:
                    dim_means.update({
                        k: float(normalized_df_filtered[v].mean())
                        for k, v in present_servqual_dims.items()
                        if not pd.isna(normalized_df_filtered[v].mean())
                    })
                
                # Add General Ratings if present
                if has_general_ratings:
                    general_ratings_filtered = []
                    for _, row in df.iterrows():
                        if GENERAL_RATINGS_COL in row and pd.notna(row[GENERAL_RATINGS_COL]):
                            general_ratings_filtered.append(row[GENERAL_RATINGS_COL])
                    if general_ratings_filtered:
                        gen_ratings_avg = sum(general_ratings_filtered) / len(general_ratings_filtered)
                        dim_means["General Ratings"] = gen_ratings_avg
                
                labels = list(dim_means.keys())
                values = list(dim_means.values())

                if not values or len(values) == 0:
                    st.markdown("""<div class="empty-tab"><div class="icon">🕸</div>
                    <p>No dimension scores match the current filters.<br>
                    Try adjusting your filters to see the SERVQUAL radar.</p>
                    </div>""", unsafe_allow_html=True)
                else:
                    col_r1, col_r2 = st.columns([3, 2])
                    
                    with col_r1:
                        st.markdown('<div class="section-head">SERVQUAL Dimension Averages</div>', unsafe_allow_html=True)
                        v_closed = values + [values[0]]
                        l_closed = labels + [labels[0]]

                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(
                            r=v_closed,
                            theta=l_closed,
                            fill="toself",
                            fillcolor="rgba(26,50,99,0.25)",
                            line=dict(color="rgb(26,50,99)", width=3),
                            marker=dict(size=8, color="#ffc570"),
                            name="Likert (Tagged)",
                            showlegend=True,
                        ))
                        
                        # No longer need separate untagged overlay since it's now in dim_means
                        
                        fig.update_layout(
                            polar=dict(
                                bgcolor="rgba(0,0,0,0)",
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 5],
                                    tickvals=[1, 2, 3, 4, 5],
                                    tickfont=dict(size=10, color="rgb(120,148,172)"),
                                gridcolor="rgba(84,119,146,0.2)",
                                linecolor="rgba(84,119,146,0.2)",
                            ),
                            angularaxis=dict(
                                tickfont=dict(size=12, color="rgb(26,50,99)", family="Mulish"),
                                gridcolor="rgba(84,119,146,0.15)",
                            ),
                        ),
                            showlegend=True,
                            legend=dict(x=1.05, y=1, font=dict(size=10)),
                            margin=dict(t=40, b=40, l=60, r=100),
                            paper_bgcolor="rgba(0,0,0,0)",
                            height=360,
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with col_r2:
                        st.markdown('<div class="section-head">Dimension Scores</div>', unsafe_allow_html=True)
                        for dim, mean_val in dim_means.items():
                            # Rename "General Ratings" to "Untagged Ratings" for clarity
                            display_dim = "Untagged Ratings" if dim == "General Ratings" else dim
                            pct   = (mean_val / 5) * 100
                            color = "#4a7c59" if mean_val >= 4 else "#8b9dc3" if mean_val >= 3 else "#b03a2e"
                            st.markdown(f"""
                            <div style="margin-bottom:.7rem;">
                            <div style="display:flex;justify-content:space-between;margin-bottom:.2rem;">
                                <span style="font-size:.78rem;font-weight:700;color:rgb(26,50,99);">{display_dim}</span>
                                <span style="font-size:.78rem;font-weight:700;color:{color};">{mean_val:.2f}/5</span>
                            </div>
                            <div style="background:rgba(84,119,146,0.12);border-radius:999px;height:7px;overflow:hidden;">
                                <div style="width:{pct:.1f}%;height:100%;border-radius:999px;background:{color};transition:width .4s;"></div>
                            </div>
                            </div>""", unsafe_allow_html=True)
                    
                    # ── CONCLUSION FOR SERVQUAL RADAR (LIKERT SCORES) ──
                    st.markdown("---")
                    st.markdown('<div class="section-head">📋 Analysis Conclusion</div>', unsafe_allow_html=True)

                    def get_likert_tier(score):
                        if score >= 4:
                            return "strong"
                        elif score >= 3:
                            return "moderate"
                        else:
                            return "weak"

                    tier_config = {
                        "strong":   ("✅", "Strong (Positive)",          "#4a7c59", "rgba(74,124,89,0.08)",   "rgba(74,124,89,0.25)"),
                        "moderate": ("🔶", "Needs monitoring", "#8b6914", "rgba(255,197,112,0.10)", "rgba(255,197,112,0.35)"),
                        "weak":     ("🚨", "Needs attention (Negative)",  "#b03a2e", "rgba(176,58,46,0.08)",   "rgba(176,58,46,0.3)"),
                    }

                    all_scores = list(dim_means.values())
                    # Note: General Ratings is already included in dim_means, no need to append again

                    avg_satisfaction = sum(all_scores) / len(all_scores) if all_scores else 0

                    if avg_satisfaction >= 4:
                        overall_tier = "strong"
                        overall_label = "Strong overall satisfaction"
                    elif avg_satisfaction >= 3:
                        overall_tier = "moderate"
                        overall_label = "Moderate overall satisfaction"
                    else:
                        overall_tier = "weak"
                        overall_label = "Low overall satisfaction"

                    overall_emoji, _, overall_color, overall_bg, _ = tier_config[overall_tier]

                    sorted_dims = sorted(dim_means.items(), key=lambda x: x[1])
                    weakest_dims = [(d, s) for d, s in sorted_dims if s < 3]
                    watch_dims   = [(d, s) for d, s in sorted_dims if 3 <= s < 4]
                    strong_dims  = [(d, s) for d, s in sorted_dims if s >= 4]

                    overall_desc_parts = []
                    if strong_dims:
                        overall_desc_parts.append(
                            f"<strong>{', '.join(d for d,_ in strong_dims)}</strong> "
                            f"{'are' if len(strong_dims) > 1 else 'is'} performing well."
                        )
                    if watch_dims:
                        overall_desc_parts.append(
                            f"<strong>{', '.join(d for d,_ in watch_dims)}</strong> "
                            f"{'show' if len(watch_dims) > 1 else 'shows'} room for improvement."
                        )
                    if weakest_dims:
                        overall_desc_parts.append(
                            f"<strong>{', '.join(d for d,_ in weakest_dims)}</strong> "
                            f"{'require' if len(weakest_dims) > 1 else 'requires'} urgent attention."
                        )
                    overall_desc = " ".join(overall_desc_parts) if overall_desc_parts else "Collect more responses to generate a detailed signal."

                    st.markdown(f"""
                    <div style="border:1px solid rgba(26,50,99,0.12);border-radius:12px;overflow:hidden;margin-bottom:1.2rem;">
                    <div style="background:{overall_bg};padding:1.1rem 1.3rem;border-bottom:1px solid rgba(26,50,99,0.08);">
                        <div style="font-size:0.65rem;font-weight:700;color:rgb(120,148,172);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.4rem;">Overall SERVQUAL Signal</div>
                        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                        <div style="font-size:2rem;font-weight:700;color:{overall_color};line-height:1;">{avg_satisfaction:.2f}<span style="font-size:1rem;color:rgb(120,148,172);font-weight:400;">/5</span></div>
                        <div>
                            <div style="font-size:1rem;font-weight:700;color:{overall_color};">{overall_emoji} {overall_label}</div>
                            <div style="font-size:0.78rem;color:rgb(80,110,140);margin-top:2px;">{overall_desc}</div>
                        </div>
                        </div>
                    </div>

                    <div style="display:flex;gap:0;border-bottom:1px solid rgba(26,50,99,0.08);">
                        <div style="flex:1;padding:.5rem .9rem;background:rgba(176,58,46,0.05);border-right:1px solid rgba(26,50,99,0.06);">
                        <div style="font-size:.6rem;font-weight:700;color:#b03a2e;text-transform:uppercase;letter-spacing:.08em;">Below 3.0</div>
                        <div style="font-size:.7rem;color:rgb(120,148,172);">Needs attention</div>
                        </div>
                        <div style="flex:1;padding:.5rem .9rem;background:rgba(255,197,112,0.07);border-right:1px solid rgba(26,50,99,0.06);">
                        <div style="font-size:.6rem;font-weight:700;color:#8b6914;text-transform:uppercase;letter-spacing:.08em;">3.0 – 3.99</div>
                        <div style="font-size:.7rem;color:rgb(120,148,172);">Monitor</div>
                        </div>
                        <div style="flex:1;padding:.5rem .9rem;background:rgba(74,124,89,0.05);">
                        <div style="font-size:.6rem;font-weight:700;color:#4a7c59;text-transform:uppercase;letter-spacing:.08em;">4.0 – 5.0</div>
                        <div style="font-size:.7rem;color:rgb(120,148,172);">Performing well</div>
                        </div>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div style="font-size:0.72rem;font-weight:700;color:rgb(120,148,172);text-transform:uppercase;letter-spacing:.08em;margin-bottom:0.8rem;">Dimension-by-dimension breakdown</div>', unsafe_allow_html=True)

                    likert_cols = st.columns(len(dim_means))
                    for col_idx, (dim, score) in enumerate(dim_means.items()):
                        tier = get_likert_tier(score)
                        emoji_t, label_t, color_t, bg_t, border_color_t = tier_config[tier]
                        
                        # USE THE LIKERT DICTIONARY HERE
                        desc_tuple = likert_dimension_descriptions.get(dim)
                        desc = desc_tuple[0] if desc_tuple else ""
                        insight_map = desc_tuple[1] if desc_tuple else {}
                        insight = insight_map.get(tier, "")
                        action = insight_map.get(f"action_{tier}", "")

                        pct = (score / 5) * 100

                        with likert_cols[col_idx]:
                            st.markdown(f"""
                            <div style="border:1px solid rgba(26,50,99,0.10);border-top:3px solid {color_t};border-radius:10px;padding:0.9rem 1rem;background:{bg_t};height:100%;">
                            <div style="font-weight:700;color:rgb(26,50,99);font-size:0.88rem;margin-bottom:0.2rem;">{dim}</div>
                            <div style="font-size:0.63rem;color:rgb(120,148,172);margin-bottom:0.6rem;line-height:1.4;">{desc}</div>
                            <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:0.4rem;">
                            <span style="font-size:1.55rem;font-weight:700;color:{color_t};line-height:1;">{score:.2f}</span>
                            <span style="font-size:0.75rem;color:rgb(120,148,172);">/5</span>
                        </div>
                        <div style="background:rgba(84,119,146,0.12);border-radius:999px;height:5px;overflow:hidden;margin-bottom:0.55rem;">
                            <div style="width:{pct:.1f}%;height:100%;border-radius:999px;background:{color_t};"></div>
                        </div>
                        <div style="display:inline-flex;align-items:center;gap:4px;border:1px solid {border_color_t};border-radius:999px;padding:.15rem .6rem;font-size:.62rem;font-weight:700;color:{color_t};margin-bottom:.65rem;">{emoji_t} {label_t}</div>
                        <div style="font-size:.72rem;color:rgb(60,90,120);line-height:1.55;margin-bottom:.5rem;">{insight}</div>
                        <div style="border-left:3px solid {border_color_t};padding-left:.6rem;font-size:.7rem;color:rgb(80,110,140);line-height:1.5;font-style:italic;">{action}</div>
                        </div>""", unsafe_allow_html=True)

                    if weakest_dims or watch_dims or strong_dims:
                        st.markdown('<div style="margin-top:1.2rem;"></div>', unsafe_allow_html=True)
                        st.markdown('<div style="font-size:0.72rem;font-weight:700;color:rgb(120,148,172);text-transform:uppercase;letter-spacing:.08em;margin-bottom:0.7rem;">Action priority</div>', unsafe_allow_html=True)

                        triage_html = '<div style="display:flex;flex-direction:column;gap:8px;">'

                        if weakest_dims:
                            names = ", ".join(f"{d} ({s:.2f})" for d, s in weakest_dims)
                            triage_html += f"""
                            <div style="display:flex;gap:10px;align-items:flex-start;padding:.75rem 1rem;background:rgba(176,58,46,0.06);border:1px solid rgba(176,58,46,0.2);border-radius:8px;">
                            <span style="font-size:.65rem;font-weight:700;background:rgba(176,58,46,0.12);color:#b03a2e;border-radius:4px;padding:.2rem .55rem;white-space:nowrap;flex-shrink:0;margin-top:1px;">🚨 Urgent</span>
                            <div>
                                <div style="font-size:.78rem;font-weight:700;color:#b03a2e;margin-bottom:2px;">{names}</div>
                                <div style="font-size:.72rem;color:rgb(80,110,140);line-height:1.5;">Scores below 3.0 suggest critical service gaps. Check the <strong>Quantitative Tab (Likert Response Log)</strong> to pinpoint exactly which Likert metric is pulling the dimension down before planning remediation.</div>
                            </div>
                            </div>"""

                        if watch_dims:
                            names = ", ".join(f"{d} ({s:.2f})" for d, s in watch_dims)
                            triage_html += f"""
                            <div style="display:flex;gap:10px;align-items:flex-start;padding:.75rem 1rem;background:rgba(255,197,112,0.08);border:1px solid rgba(255,197,112,0.3);border-radius:8px;">
                            <span style="font-size:.65rem;font-weight:700;background:rgba(255,197,112,0.2);color:#8b6914;border-radius:4px;padding:.2rem .55rem;white-space:nowrap;flex-shrink:0;margin-top:1px;">🔶 Monitor</span>
                            <div>
                                <div style="font-size:.78rem;font-weight:700;color:#8b6914;margin-bottom:2px;">{names}</div>
                                <div style="font-size:.72rem;color:rgb(80,110,140);line-height:1.5;">Borderline scores (3.0–3.99) signal acceptable but inconsistent service. These dimensions are vulnerable to operational disruptions. Targeted improvements in scheduling, communication, or facilities could push these above 4.0.</div>
                            </div>
                            </div>"""

                        if strong_dims:
                            names = ", ".join(f"{d} ({s:.2f})" for d, s in strong_dims)
                            triage_html += f"""
                            <div style="display:flex;gap:10px;align-items:flex-start;padding:.75rem 1rem;background:rgba(74,124,89,0.06);border:1px solid rgba(74,124,89,0.2);border-radius:8px;">
                            <span style="font-size:.65rem;font-weight:700;background:rgba(74,124,89,0.12);color:#4a7c59;border-radius:4px;padding:.2rem .55rem;white-space:nowrap;flex-shrink:0;margin-top:1px;">✅ Sustain</span>
                            <div>
                                <div style="font-size:.78rem;font-weight:700;color:#4a7c59;margin-bottom:2px;">{names}</div>
                                <div style="font-size:.72rem;color:rgb(80,110,140);line-height:1.5;">Scores at 4.0 or above indicate genuine commuter satisfaction. Document what is driving these high scores and replicate those practices across weaker dimensions and underperforming routes.</div>
                            </div>
                            </div>"""

                        triage_html += '</div>'
                        st.markdown(triage_html, unsafe_allow_html=True)
            
        # ── Quantitative Analysis Data ──
        st.markdown("""<div style="height: 2rem;"></div>""", unsafe_allow_html=True)
        with st.expander("📊 Quantitative Data", expanded=True):
            st.markdown("""
            <div style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                        border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;">
              <div style="font-size:.72rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem;">
                Quantitative Guide
              </div>
              <div style="font-size:.8rem;color:rgb(60,100,130);line-height:1.6;">
                This tab is for <strong>numeric (Likert) ratings</strong> about land public transportation—service quality, vehicles, experience, or anything you asked on a scale.<br><br>
                <strong>Score by Selected Context:</strong> average SERVQUAL (and general) scores grouped by a field from the respondent profile (e.g. how often they ride, mode type, etc.).<br>
                <strong>How to use:</strong> pick a grouping that fits your research question, then see which segments score higher or lower on each dimension.<br><br>
                <strong>How to use:</strong> name strengths and problem areas in your analysis and tie them to the SERVQUAL framework.<br><br>
                <strong>Likert Response Log:</strong> each numeric answer with question text and time.<br>
                <strong>How to use:</strong> audit the data, spot outliers, and support tables or appendices with raw-scale answers.
              </div>
            </div>
            """, unsafe_allow_html=True)
            if not has_any_rating_data:
                st.markdown("""<div class="empty-tab"><div class="icon">📊</div>
                  <p>No rating scores available yet.<br>
                  Assign SERVQUAL dimensions or leave questions untagged
                  (they appear as General Ratings) in Form Builder.</p>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div class="section-head">Likert Response Log</div>', unsafe_allow_html=True)
                likert_rows = []
                for _, row in df.iterrows():
                    ans_map = row.get("answers", {})
                    submitted = row.get("created_at", None)
                    if not isinstance(ans_map, dict):
                        continue
                    for question, answer in ans_map.items():
                        score = pd.to_numeric(answer, errors="coerce")
                        if pd.Series(score).isna().all():
                            continue
                        question_text = str(question)
                        base_question = re.sub(r"\s\(\d+\)$", "", question_text).strip()
                        schema_scale = question_scale_map.get(question_text)
                        if schema_scale is None:
                            schema_scale = question_scale_map.get(base_question)
                        if schema_scale is not None and schema_scale > 1:
                            q_scale_max = float(schema_scale)
                        else:
                            q_scores = pd.to_numeric(
                                df["answers"].apply(
                                    lambda a: a.get(question) if isinstance(a, dict) else None
                                ),
                                errors="coerce",
                            )
                            q_max = q_scores.max()
                            q_scale_max = float(q_max) if pd.notna(q_max) and q_max > 5 else 5
                        score_norm = normalize_to_5(float(score), q_scale_max)
                        scale_max_int = int(q_scale_max) if float(q_scale_max).is_integer() else round(float(q_scale_max), 2)
                        
                        # Get SERVQUAL dimension for this question
                        q_dimension = form_schema.get(question_text, {}).get("dimension")
                        if q_dimension is None:
                            q_dimension = form_schema.get(base_question, {}).get("dimension")
                        dimension_display = q_dimension if q_dimension else "Untagged"
                        
                        likert_rows.append({
                            "Question": str(question),
                            "Dimension": dimension_display,
                            "Score": int(score) if float(score).is_integer() else float(score),
                            "Score (Selected Scale)": f"{int(score) if float(score).is_integer() else round(float(score), 2)}/{scale_max_int}",
                            "ScoreNormalized": round(float(score_norm), 2),
                            "Submitted": submitted,
                        })

                if likert_rows:
                    likert_df = pd.DataFrame(likert_rows)
                    likert_df["Submitted"] = pd.to_datetime(likert_df["Submitted"], errors="coerce")
                    likert_df["Submitted Date"] = likert_df["Submitted"].dt.date

                    q_avg = (
                        likert_df.groupby("Question", as_index=False)["ScoreNormalized"]
                        .mean()
                        .rename(columns={"ScoreNormalized": "Average Score"})
                    )
                    q_avg["Responses"] = likert_df.groupby("Question").size().values
                    q_avg = q_avg.sort_values("Average Score", ascending=False)
                    top_n = q_avg.head(5)
                    bottom_n = q_avg.tail(5)
                    top_bottom = pd.concat([top_n, bottom_n], ignore_index=True).drop_duplicates(subset=["Question"])
                    top_bottom["Category"] = top_bottom["Question"].isin(top_n["Question"]).map({True: "Top", False: "Bottom"})

                    tb_chart = (
                        alt.Chart(top_bottom)
                        .mark_bar(cornerRadiusEnd=4)
                        .encode(
                            y=alt.Y("Question:N", sort="-x", title="Question"),
                            x=alt.X("Average Score:Q", scale=alt.Scale(domain=[0, 5]), title="Average Score (/5)"),
                            color=alt.Color(
                                "Average Score:Q",
                                scale=alt.Scale(domain=[0, 5], range=["#b03a2e", "#ffc570", "#4a7c59"]),
                                legend=alt.Legend(title="Score (/5)"),
                            ),
                            tooltip=[
                                alt.Tooltip("Question:N"),
                                alt.Tooltip("Average Score:Q", format=".2f"),
                                alt.Tooltip("Responses:Q"),
                                alt.Tooltip("Category:N", title="Group"),
                            ],
                        )
                        .properties(height=280)
                    )
                    st.altair_chart(tb_chart, use_container_width=True)
                    
                    st.markdown('<div class="section-head">Score Distribution</div>', unsafe_allow_html=True)
                    st.caption("Breakdown of how many respondents gave each score for each question.")
                    
                    # Create score distribution table
                    score_dist = []
                    for question in likert_df["Question"].unique():
                        q_data = likert_df[likert_df["Question"] == question]
                        q_dimension = q_data["Dimension"].iloc[0] if len(q_data) > 0 else "Untagged"
                        
                        # Get the scale max for this question
                        scale_str = q_data["Score (Selected Scale)"].iloc[0] if len(q_data) > 0 else "0/5"
                        scale_max = int(scale_str.split("/")[1]) if "/" in scale_str else 5
                        
                        # Count scores
                        score_counts = q_data["Score"].value_counts().sort_index()
                        
                        row = {
                            "Question": question,
                            "Dimension": q_dimension,
                            "Total Responses": len(q_data)
                        }
                        
                        # Add count for each score
                        for score in range(1, int(scale_max) + 1):
                            row[f"Score {score}"] = int(score_counts.get(score, 0))
                        
                        score_dist.append(row)
                    
                    if score_dist:
                        dist_df = pd.DataFrame(score_dist)
                        st.dataframe(
                            dist_df,
                            use_container_width=True,
                            hide_index=True,
                            height=300,
                        )
                else:
                    st.info("No Likert responses found in the selected date range.")

    # ─────────────────────────────────
    # TAB 3 — DATABASE
    # ─────────────────────────────────
    with tab3:
        with st.expander("👥 Demographics", expanded=True):
            st.markdown("""
            <div style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                        border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;">
            <div style="font-size:.72rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem;">
                Demographics Guide
            </div>
            <div style="font-size:.8rem;color:rgb(60,100,130);line-height:1.6;">
                Data comes from the <strong>respondent profile</strong> block and/or any questions you marked as <strong>demographic</strong> in Form Builder.<br>
                <strong style="color:rgb(26,50,99);">Custom demographic questions</strong> (questions you tagged as demographic) appear first in charts, followed by standard profile fields.<br>
            </div>
            </div>
            """, unsafe_allow_html=True)

            if "demo_answers" not in df.columns or df["demo_answers"].isna().all():
                # No separate demo_answers field - extract demographics from answers field instead
                
                # First, try to identify demographic questions from form_questions
                demographic_prompts = set()
                for q in all_questions:
                    if q.get("is_demographic"):
                        demographic_prompts.add(q.get("prompt"))
                
                # If form_questions is empty or has no demographic markers, use standard demographic patterns
                if not demographic_prompts and df.shape[0] > 0:
                    # Fallback: extract common demographic fields from responses
                    try:
                        first_row_answers = df.iloc[0]["answers"]
                    except:
                        first_row_answers = None
                    
                    # Handle both dict and JSON string formats
                    if isinstance(first_row_answers, str):
                        try:
                            first_row_answers = json.loads(first_row_answers)
                        except:
                            first_row_answers = {}
                    elif not isinstance(first_row_answers, dict):
                        first_row_answers = {}
                    
                    if first_row_answers:
                        # Look for standard demographic question names
                        standard_demo_keywords = [
                            "Age", "Gender", "Occupational", "Allowance", "Salary",
                            "transport mode", "Commuting", "Frequency"
                        ]
                        for ans_key in first_row_answers.keys():
                            for keyword in standard_demo_keywords:
                                if keyword.lower() in ans_key.lower():
                                    demographic_prompts.add(ans_key)
                                    break
                
                # Extract demographics from answers using identified prompts
                demo_rows = []
                for idx, row in df.iterrows():
                    try:
                        ans_map = row["answers"] if "answers" in row else None
                    except:
                        ans_map = None
                    
                    # Handle both dict and JSON string formats
                    if isinstance(ans_map, str):
                        try:
                            ans_map = json.loads(ans_map)
                        except:
                            ans_map = {}
                    elif not isinstance(ans_map, dict):
                        ans_map = {}
                    
                    if ans_map:
                        demo_row = {}
                        for prompt in demographic_prompts:
                            if prompt in ans_map:
                                demo_row[prompt] = ans_map[prompt]
                        if demo_row:
                            demo_rows.append(demo_row)
                
                if demo_rows:
                    demo_df = pd.DataFrame(demo_rows)
                else:
                    demo_df = pd.DataFrame()
            else:
                demo_df = pd.json_normalize(df["demo_answers"].dropna().tolist())
                if demo_df.empty:
                    st.markdown("""<div class="empty-tab"><div class="icon">👥</div>
                    <p>No demographic data available.<br>
                    Mark questions as <strong>demographic</strong> in Form Builder and collect responses to see charts.</p>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown('<div class="section-head">📊 Choose Visualization Type</div>', unsafe_allow_html=True)
                    chart_type = st.radio(
                        "Select how to view demographic data:",
                        options=["donut", "bar", "stacked", "table"],
                        format_func=lambda x: {
                            "donut": "🍩 Donut Charts",
                            "bar": "📊 Horizontal Bar Chart",
                            "stacked": "📈 Stacked Bar Chart",
                            "table": "📋 Table with Counts",
                        }[x],
                        horizontal=True,
                        key="demo_chart_type"
                    )
                    
                    st.markdown("---")
                    
                    # Collect custom demographic questions from responses
                    custom_demographic_all = set()
                    if "custom_demographic_questions" in df.columns:
                        for custom_list in df["custom_demographic_questions"].dropna():
                            if isinstance(custom_list, list):
                                custom_demographic_all.update(custom_list)
                    
                    demo_specs = _demo_chart_specs_all(demo_df, list(custom_demographic_all))
                    
                    # Show indicator if custom demographics exist
                    if custom_demographic_all:
                        st.markdown(f"""
                        <div style="background:rgba(255,197,112,0.1);border:1px solid rgba(255,197,112,0.3);border-radius:8px;padding:0.75rem 1rem;margin-bottom:1rem;">
                            <div style="font-size:0.75rem;font-weight:700;color:rgb(139,106,20);text-transform:uppercase;letter-spacing:.08em;margin-bottom:0.4rem;">
                                ⭐ Custom Demographic Questions
                            </div>
                            <div style="font-size:0.8rem;color:rgb(100,85,50);margin-bottom:0.5rem;">
                                Your form has <strong>{len(custom_demographic_all)} custom demographic field(s)</strong> that will appear first in the charts below:
                            </div>
                            <div style="font-size:0.75rem;color:rgb(120,100,60);display:flex;flex-wrap:wrap;gap:0.5rem;">
                                {' '.join([f'<span style="background:rgba(255,197,112,0.2);padding:0.25rem 0.6rem;border-radius:4px;white-space:nowrap;">📊 {q}</span>' for q in sorted(custom_demographic_all)])}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    if not demo_specs:
                        st.dataframe(demo_df, use_container_width=True, hide_index=True)
                    else:
                        if chart_type == "donut":
                            st.markdown('<div class="section-head">Individual Demographics</div>', unsafe_allow_html=True)
                            st.caption("Single-select fields shown as donut charts. For transport (select all that apply), one person can count in multiple slices.")
                            
                            pairs = [
                                (demo_specs[i], demo_specs[i + 1] if i + 1 < len(demo_specs) else None)
                                for i in range(0, len(demo_specs), 2)
                            ]
                            for spec_l, spec_r in pairs:
                                cl, cr = st.columns(2)
                                for col_w, spec in [(cl, spec_l), (cr, spec_r)]:
                                    if spec is None:
                                        continue
                                    q, label = spec[0], spec[1]
                                    with col_w:
                                        series_data = _explode_demo_series(demo_df[q])
                                        vc = series_data.value_counts().reset_index()
                                        # Use simple column names for Altair compatibility
                                        vc.columns = ["Value", "Count"]
                                        
                                        st.altair_chart(
                                            alt.Chart(vc)
                                            .mark_arc(innerRadius=40)
                                            .encode(
                                                theta="Count:Q",
                                                color=alt.Color(
                                                    "Value:N",
                                                    scale=alt.Scale(scheme="blues"),
                                                    legend=alt.Legend(orient="bottom", labelFontSize=10),
                                                ),
                                                tooltip=["Value:N", "Count:Q"],
                                            )
                                            .properties(title=label, height=200),
                                            use_container_width=True,
                                        )
                        
                        elif chart_type == "bar":
                            st.markdown('<div class="section-head">Demographics Overview (Horizontal Bar)</div>', unsafe_allow_html=True)
                            st.caption("Best for multiple choice/select demographics. Easy to compare across categories.")
                            
                            for q, label in demo_specs:
                                vc = _explode_demo_series(demo_df[q]).value_counts().reset_index()
                                # Use simple column names for Altair compatibility
                                vc.columns = ["Value", "Count"]
                                vc = vc.sort_values("Count", ascending=True) 
                                
                                bar_chart = (
                                    alt.Chart(vc)
                                    .mark_bar(color="#1a3263")
                                    .encode(
                                        y=alt.Y("Value:N", sort="-x", title=None),
                                        x=alt.X("Count:Q", title="Number of Responses"),
                                        tooltip=["Value:N", "Count:Q"],
                                    )
                                    .properties(
                                        title=label,
                                        height=max(200, len(vc) * 30)
                                    )
                                )
                                st.altair_chart(bar_chart, use_container_width=True)
                        
                        elif chart_type == "stacked":
                            st.markdown('<div class="section-head">Demographics Comparison (Stacked)</div>', unsafe_allow_html=True)
                            st.caption("Shows composition and distribution of demographic categories.")
                            
                            if len(demo_specs) >= 2:
                                primary_q, primary_label = demo_specs[0]
                                st.markdown(f"**Comparing other demographics by {primary_label}:**")
                                
                                for q, label in demo_specs[1:]:
                                    primary_series = _explode_demo_series(demo_df[primary_q])
                                    secondary_series = _explode_demo_series(demo_df[q])
                                    
                                    combined_data = []
                                    for idx, prim_val in enumerate(primary_series):
                                        if idx < len(secondary_series):
                                            combined_data.append({
                                                "Primary": str(prim_val),
                                                "Secondary": str(secondary_series.iloc[idx]),
                                            })
                                    
                                    if combined_data:
                                        combined_df = pd.DataFrame(combined_data)
                                        grouped = combined_df.groupby(["Primary", "Secondary"]).size().reset_index(name="Count")
                                        
                                        stacked_chart = (
                                            alt.Chart(grouped)
                                            .mark_bar()
                                            .encode(
                                                x=alt.X("Primary:N", title=primary_label),
                                                y=alt.Y("Count:Q", title="Count"),
                                                color=alt.Color("Secondary:N", title=label, scale=alt.Scale(scheme="blues")),
                                                tooltip=["Primary:N", "Secondary:N", "Count:Q"],
                                            )
                                            .properties(title=f"{label} by {primary_label}", height=250)
                                        )
                                        st.altair_chart(stacked_chart, use_container_width=True)
                            else:
                                st.info("Stacked bar chart requires at least 2 demographic questions. Add more demographic questions to use this view.")
                        
                        elif chart_type == "table":
                            st.markdown('<div class="section-head">Demographics Frequency Table</div>', unsafe_allow_html=True)
                            st.caption("Detailed counts for each demographic option.")
                            
                            for q, label in demo_specs:
                                vc = _explode_demo_series(demo_df[q]).value_counts().reset_index()
                                vc.columns = ["Value", "Count"]
                                vc["Percentage"] = (vc["Count"] / vc["Count"].sum() * 100).round(1)
                                vc = vc.sort_values("Count", ascending=False)
                                
                                st.markdown(f"**{label}**")
                                st.dataframe(
                                    vc.reset_index(drop=True),
                                    use_container_width=True,
                                    hide_index=True,
                                )
                                st.markdown("---")

        with st.expander("👤 Respondent Details", expanded=True):
            st.markdown("### 👤 Respondent Details")
            st.caption("View all responses. Each row is one respondent.")
            
            try:
                all_responses = (
                    conn.client.table("form_responses")
                    .select("*")
                    .eq("admin_email", admin_email)
                    .eq("form_id", current_form_id)
                    .order("created_at", desc=True)
                    .execute()
                )
                
                if not all_responses.data:
                    st.info("No responses yet for this form.")
                else:
                    q_query = (
                        conn.client.table("form_questions")
                        .select("id, prompt, q_type, is_demographic")
                        .eq("admin_email", admin_email)
                        .eq("form_id", current_form_id)
                        .order("sort_order")
                        .execute()
                    )
                    all_questions = q_query.data or []
                    
                    try:
                        form_meta_query = (
                            conn.client.table("form_meta")
                            .select("include_demographics")
                            .eq("admin_email", admin_email)
                            .eq("form_id", current_form_id)
                            .single()
                            .execute()
                        )
                        form_meta_data = form_meta_query.data if form_meta_query else {}
                    except Exception:
                        form_meta_data = {}
                    
                    show_demo_block = form_meta_data.get("include_demographics", False) if form_meta_data else False
                    show_servqual_block = form_meta_data.get("include_standard_servqual_questions", True) if form_meta_data else True
                    
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
                        {"prompt": "Additional Comments or Suggestions / Karagdagang Komento o Mungkahi", "q_type": "Paragraph", "options": [], "is_required": False, "is_demographic": False, "enable_sentiment": True, "servqual_dimension": None, "is_locked": True},
                    ]
                    
                    existing_prompts = {q.get("prompt") for q in all_questions}
                    
                    # Always include standard demographics in the table for display (even if toggle is off, show if data exists)
                    for std_q in STANDARD_DEMO_QUESTIONS:
                        if std_q.get("prompt") not in existing_prompts:
                            all_questions.append(std_q)
                            existing_prompts.add(std_q.get("prompt"))
                    
                    # Always include standard SERVQUAL questions in the respondent table for complete visibility
                    for std_q in STANDARD_SERVQUAL_QUESTIONS:
                        if std_q.get("prompt") not in existing_prompts:
                            all_questions.append(std_q)
                            existing_prompts.add(std_q.get("prompt"))
                    
                    demo_questions = [q for q in all_questions if q.get("is_demographic")]
                    non_demo_questions = [q for q in all_questions if not q.get("is_demographic")]
                    
                    possible_answer_keys = []
                    prompt_counts = {}
                    for q in non_demo_questions:
                        prompt = q.get("prompt", "")
                        if prompt not in prompt_counts:
                            prompt_counts[prompt] = 0
                            possible_answer_keys.append((q, prompt)) 
                        else:
                            prompt_counts[prompt] += 1
                            possible_answer_keys.append((q, f"{prompt} ({prompt_counts[prompt]})")) 
                    
                    table_data = []
                    for response in all_responses.data:
                        row = {
                            "Respondent ID": str(response.get("id", ""))[:8],
                            "Submitted": response.get("created_at", "")[:10],
                            "Time": response.get("created_at", "")[11:19],
                        }
                        
                        demo_ans_map = response.get("demo_answers", {})
                        if isinstance(demo_ans_map, dict):
                            for demo_q in demo_questions:
                                demo_prompt = demo_q.get("prompt", "Unknown")
                                demo_answer = demo_ans_map.get(demo_prompt, "")
                                if not demo_answer and "Land Public Transportation" in demo_prompt:
                                    demo_answer = demo_ans_map.get("Which land public transportation modes do you usually use? (Select all that apply)", "")
                                
                                if demo_answer is None:
                                    demo_answer = ""
                                elif isinstance(demo_answer, list):
                                    demo_answer = ", ".join(str(a) for a in demo_answer)
                                else:
                                    demo_answer = str(demo_answer)
                                
                                row[f"👥 {demo_prompt}"] = demo_answer
                        
                        ans_map = response.get("answers", {})
                        
                        for q, answer_key in possible_answer_keys:
                            q_prompt = q.get("prompt", "Unknown")
                            q_type = q.get("q_type", "")
                            
                            answer = ans_map.get(answer_key, "")
                            if answer is None:
                                answer = ""
                            elif isinstance(answer, list):
                                answer = ", ".join(str(a) for a in answer)
                            else:
                                answer = str(answer)
                            
                            if q_type in ("Multiple Choice", "Multiple Select"):
                                col_name = f"{q_prompt} [{q_type}]"
                            else:
                                col_name = q_prompt
                            
                            row[col_name] = answer
                        
                        table_data.append(row)
                    
                    df_responses = pd.DataFrame(table_data)
                    
                    st.markdown(f"### Respondent Responses Table ({len(all_responses.data)} total)")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        search_text = st.text_input(
                            "🔍 Search responses",
                            placeholder="Type to search all columns...",
                            key="respondent_search"
                        )
                    
                    with col2:
                        if "Submitted" in df_responses.columns:
                            min_date = pd.to_datetime(df_responses["Submitted"]).min().date()
                            max_date = pd.to_datetime(df_responses["Submitted"]).max().date()
                            
                            date_range = st.date_input(
                                "📅 Filter by date",
                                value=(min_date, max_date),
                                key="respondent_date_range"
                            )
                            
                            if isinstance(date_range, tuple) and len(date_range) == 2:
                                df_filtered = df_responses[
                                    (pd.to_datetime(df_responses["Submitted"]).dt.date >= date_range[0]) &
                                    (pd.to_datetime(df_responses["Submitted"]).dt.date <= date_range[1])
                                ]
                            else:
                                df_filtered = df_responses
                        else:
                            df_filtered = df_responses
                    
                    if search_text:
                        mask = df_filtered.astype(str).apply(
                            lambda x: x.str.contains(search_text, case=False, na=False).any(),
                            axis=1
                        )
                        df_filtered = df_filtered[mask]
                    
                    st.markdown(f"**Showing {len(df_filtered)} of {len(df_responses)} responses**")
                    
                    demo_cols = [c for c in df_filtered.columns if c.startswith("👥 ")]
                    other_cols = [c for c in df_filtered.columns if not c.startswith("👥 ") and c not in ("Respondent ID", "Submitted", "Time")]
                    col_order = ["Respondent ID", "Submitted", "Time"] + demo_cols + other_cols
                    col_order = [c for c in col_order if c in df_filtered.columns] 
                    
                    st.dataframe(
                        df_filtered[col_order],
                        use_container_width=True,
                        hide_index=True,
                        height=min(600, 80 + 36 * max(1, len(df_filtered))),
                    )
                    
                    csv = df_filtered[col_order].to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"respondents_{current_form_id}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )
            
            except Exception as e:
                st.error(f"Error loading respondent data: {str(e)}")

        with st.expander("📊 Multiple Choice & Multiple Select Responses", expanded=True):
            st.markdown("### 📊 Multiple Choice & Multiple Select Responses")
            st.caption("Bar charts showing answer counts for each multiple choice/select question. For multiple select questions, respondents can select more than one answer, so totals may exceed the number of responses.")
            
            try:
                mc_questions = [q for q in all_questions if q.get("q_type") in ("Multiple Choice", "Multiple Select") and not _is_demographic_question(q.get("prompt", ""))]
                
                if not mc_questions:
                    st.info("No multiple choice or multiple select questions in this form.")
                else:
                    seen_prompts = {}
                    
                    for q in mc_questions:
                        q_prompt = q.get("prompt", "Unknown")
                        q_type = q.get("q_type", "")
                        
                        if q_prompt not in seen_prompts:
                            seen_prompts[q_prompt] = 0
                            unique_key = q_prompt
                        else:
                            seen_prompts[q_prompt] += 1
                            unique_key = f"{q_prompt} ({seen_prompts[q_prompt]})"
                        
                        answers = []
                        for response in all_responses.data:
                            ans_map = response.get("answers", {})
                            ans = ans_map.get(unique_key)
                            if ans:
                                if isinstance(ans, list):
                                    answers.extend([str(a).strip() for a in ans if a])
                                elif isinstance(ans, str):
                                    if "," in ans:
                                        answers.extend([a.strip() for a in ans.split(",") if a.strip()])
                                    else:
                                        answers.append(ans.strip())
                                else:
                                    answers.append(str(ans).strip())
                        
                        if answers:
                            answer_counts = pd.Series(answers).value_counts().reset_index()
                            answer_counts.columns = ["Answer", "Count"]
                            answer_counts = answer_counts.sort_values("Count", ascending=False)
                            
                            type_label = "Multiple Select" if q_type == "Multiple Select" else "Multiple Choice"
                            max_count = answer_counts["Count"].max()
                            chart = alt.Chart(answer_counts).mark_bar(color="#1a3263").encode(
                                x=alt.X("Count:Q", title="Number of Responses", 
                                        axis=alt.Axis(format="d", tickMinStep=1),
                                        scale=alt.Scale(domain=[0, max(max_count, 1)], nice=False)),
                                y=alt.Y("Answer:N", sort="-x", title=""),
                                tooltip=["Answer:N", "Count:Q"],
                            ).properties(
                                title=f"{q_prompt} [{type_label}]",
                                height=200 + max(0, (len(answer_counts) - 5) * 20)
                            )
                            
                            st.altair_chart(chart, use_container_width=True)
                        else:
                            st.info(f"No responses for: {q_prompt} [{q_type}]")
            
            except Exception as e:
                st.error(f"Error loading multiple choice data: {str(e)}")
                
        with st.expander("📈 Response Trends", expanded=True):
            if "created_at" not in df.columns:
                st.markdown("""<div class="empty-tab"><div class="icon">📈</div>
                <p>Response trend chart requires timestamps.<br>
                Submit responses first to see daily counts.</p>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                            border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;">
                <div style="font-size:.72rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem;">
                    Responses Per Day Guide
                </div>
                <div style="font-size:.8rem;color:rgb(60,100,130);line-height:1.6;">
                    This tab shows <strong>how many survey responses are submitted each day</strong> within your selected date range.<br>
                    <strong>Bars and line</strong> represent daily response count (including days with zero responses for continuity).<br>
                    Use this view to quickly identify <strong>peak days</strong>, <strong>low-activity days</strong>, and overall response activity trend.
                </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown('<div class="section-head">Responses Per Day</div>', unsafe_allow_html=True)
                daily_responses = (
                    df.assign(date=df["created_at"].dt.date)
                    .groupby("date")
                    .size()
                    .reset_index(name="Responses")
                )
                
                if daily_responses.empty:
                    st.markdown('<div style="font-size:0.9rem;color:#999;">No responses to display for the selected filters.</div>', unsafe_allow_html=True)
                else:
                    daily_responses["date"] = pd.to_datetime(daily_responses["date"])
                    daily_responses = daily_responses.sort_values("date")

                    min_date = daily_responses["date"].min()
                    max_date = daily_responses["date"].max()
                    
                    if pd.notna(min_date) and pd.notna(max_date):
                        full_dates = pd.date_range(
                            start=min_date,
                            end=max_date,
                            freq="D",
                        )
                        daily_responses = (
                            daily_responses.set_index("date")
                            .reindex(full_dates, fill_value=0)
                            .rename_axis("date")
                            .reset_index()
                        )
                    
                    peak_row = daily_responses.loc[daily_responses["Responses"].idxmax()]

                    c2, c3 = st.columns(2)
                    c2.markdown(f"""<div class="kpi-card">
                    <div class="kpi-title">Peak Day</div>
                    <div class="kpi-value pos">{int(peak_row["Responses"])}</div>
                    <div class="kpi-sub">{peak_row["date"].strftime("%b %d, %Y")}</div>
                    </div>""", unsafe_allow_html=True)
                    c3.markdown(f"""<div class="kpi-card">
                    <div class="kpi-title">Total Responses (Range)</div>
                    <div class="kpi-value gold">{int(daily_responses["Responses"].sum())}</div>
                    <div class="kpi-sub">Daily trend view</div>
                    </div>""", unsafe_allow_html=True)

                    responses_chart = (
                        alt.Chart(daily_responses)
                        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#1a3263")
                        .encode(
                            x=alt.X(
                                "date:T",
                                axis=alt.Axis(format="%b %d", title="Date", labelAngle=-25),
                            ),
                            y=alt.Y(
                                "Responses:Q",
                                title="Number of Responses",
                                axis=alt.Axis(format=".0f", tickMinStep=1),
                                scale=alt.Scale(domainMin=0, nice=True),
                            ),
                            tooltip=[
                                alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
                                alt.Tooltip("Responses:Q", title="Responses", format=",.0f"),
                            ],
                        )
                        .properties(height=320)
                    )
                    trend_line = (
                        alt.Chart(daily_responses)
                        .mark_line(color="#ffc570", strokeWidth=2.5, point=True)
                        .encode(
                            x="date:T",
                            y="Responses:Q",
                            tooltip=[
                                alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
                                alt.Tooltip("Responses:Q", title="Responses", format=",.0f"),
                            ],
                        )
                    )
                    st.altair_chart(responses_chart + trend_line, use_container_width=True)
    
    # ── EXPORT ──
    st.markdown("---")
    st.markdown('<div class="section-head">📥 Export Data</div>', unsafe_allow_html=True)
    ex1, ex2, ex3, _ = st.columns([2, 2, 2, 2])

    with ex1:
        st.download_button(
            "⬇ All Responses (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"land_public_transport_responses_{date_from}_{date_to}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with ex2:
        if not df_sent.empty and "raw_feedback" in df_sent.columns:
            cols_to_export = ["raw_feedback", sent_col] + [
                s for s in ["sentiment_score", "created_at"] if s in df_sent.columns
            ]
            st.download_button(
                "⬇ Sentiment Log (CSV)",
                data=df_sent[cols_to_export].to_csv(index=False).encode("utf-8"),
                file_name=f"land_public_transport_sentiment_{date_from}_{date_to}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with ex3:
        if has_any_rating_data:
            summary_rows_export = []
            for k, v in all_dim_cols.items():
                if v in df.columns and df[v].notna().any():
                    summary_rows_export.append({
                        "Dimension": k,
                        "Type": "SERVQUAL" if k != "General Ratings" else "General",
                        "Average": round(normalized_df[v].mean(), 4),
                        "Min": round(df[v].min(), 4),
                        "Max": round(df[v].max(), 4),
                        "Responses": int(df[v].notna().sum()),
                    })
            if summary_rows_export:
                st.download_button(
                    "⬇ SERVQUAL Summary (CSV)",
                    data=pd.DataFrame(summary_rows_export).to_csv(index=False).encode("utf-8"),
                    file_name=f"land_public_transport_servqual_summary_{date_from}_{date_to}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

# Mark dashboard as initialized and hide loading screen
st.session_state.dashboard_initialized = True

render_dashboard()

# Hide loading overlay on page complete
st.html("""
<script>
    const loadingOverlay = document.querySelector('.loading-overlay');
    if (loadingOverlay) {
        setTimeout(() => {
            loadingOverlay.style.display = 'none';
        }, 300);
    }
</script>
""")