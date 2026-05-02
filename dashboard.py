import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import re
import json
import emoji
import time
import urllib.request           
import nltk                     
from nltk.corpus import stopwords
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

st.markdown("""
<style>
    [data-testid="stFragment"] {
        opacity: 1 !important;
        transition: none !important;
    }

    .stAppDeployButton { display: none !important; }
    .stAppToolbar { background: #f0f4f8;}

    [data-testid="stFragment"] > div {
        opacity: 1 !important;
    }

    [data-stale="true"] {
        opacity: 1 !important;
        pointer-events: none;
    }

    .stSpinner,
    [data-testid="stFragment"] [data-stale] {
        opacity: 1 !important;
    }
            
    [data-testid="stSidebar"], 
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 999999999 !important;
    }

    .stApp [data-testid="stAppViewBlockContainer"] {
        visibility: hidden !important;
        animation: snapVisible 0.1s forwards 2.5s !important;
    }

    #nuclear-loader {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: #f0f4f8;
        z-index: 999999998;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        animation: fadeOutNuclear 0.4s ease-out 2.5s forwards;
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

.gen-rating-bar {
  background: rgba(108,117,125,0.08); border: 1px solid rgba(108,117,125,0.2);
  border-left: 4px solid #6c757d; border-radius: 7px;
  padding: .7rem 1rem; margin-top: .8rem;
}
.gen-rating-bar .label { font-size: .65rem; font-weight: 700; color: #6c757d; text-transform: uppercase; letter-spacing: .1em; margin-bottom: .2rem; }
.gen-rating-bar .val   { font-size: .95rem; font-weight: 700; color: var(--navy); }

.section-head {
  font-family: 'Libre Baskerville', serif !important;
  font-size: 1rem !important; font-weight: 700 !important; color: var(--navy) !important;
  margin: 1.2rem 0 .7rem !important; padding-bottom: .3rem !important;
  border-bottom: 2px solid rgba(26,50,99,0.08) !important;
  display: flex; align-items: center; justify-content: space-between;
}

[data-testid="stTabs"] [role="tablist"] { border-bottom: 2px solid var(--bdr) !important; gap: 0 !important; }
[data-testid="stTabs"] [role="tab"] {
  font-size: .78rem !important; font-weight: 700 !important;
  letter-spacing: .06em !important; color: var(--muted) !important;
  padding: .55rem 1.1rem !important; border: none !important; background: transparent !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: var(--navy) !important; }
div[data-baseweb="tab-highlight"] { background-color: var(--navy) !important; }

[data-testid="stDataFrame"] { border: 1px solid var(--bdr) !important; border-radius: 8px !important; overflow: hidden !important; }

[data-testid="stSelectbox"] > div > div,
[data-testid="stDateInput"] input { border: 1.5px solid var(--bdr) !important; border-radius: 6px !important; background: #fff !important; color: var(--navy) !important; }
[data-testid="stSelectbox"] label,
[data-testid="stDateInput"] label { font-size: .68rem !important; font-weight: 700 !important; letter-spacing: .1em !important; text-transform: uppercase !important; color: var(--steel) !important; }

[data-testid="stDownloadButton"] > button {
  background: var(--navy) !important; color: var(--gold) !important;
  border: none !important; border-radius: 6px !important;
  font-size: .7rem !important; font-weight: 700 !important;
  letter-spacing: .1em !important; text-transform: uppercase !important;
  padding: .45rem 1.1rem !important;
}
[data-testid="stDownloadButton"] > button:hover { background: var(--navydk) !important; transform: translateY(-1px) !important; }

.conf-bar-wrap { background: rgba(84,119,146,0.12); border-radius: 999px; height: 6px; overflow: hidden; margin-top: .4rem; }
.conf-bar      { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--steel), var(--navy)); }

.empty-tab {
  text-align: center; padding: 3rem 2rem; color: var(--muted);
  background: var(--card); border: 1.5px dashed var(--bdr);
  border-radius: 10px; margin-top: 1rem;
}
.empty-tab .icon { font-size: 2.2rem; margin-bottom: .6rem; }
.empty-tab p     { font-size: .9rem; margin: 0; line-height: 1.7; }

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
conn = st.connection("supabase", type=SupabaseConnection)

admin_email = None
session_id_from_url = st.query_params.get("session_id")

if session_id_from_url:
    try:
        result = conn.client.table("active_sessions").select("user_email").eq("session_id", session_id_from_url).execute()
        if result.data:
            admin_email = result.data[0].get("user_email")
            st.session_state.user_email = admin_email
            st.session_state.session_id = session_id_from_url
            st.session_state.logged_in = True
            st.session_state.local_login = True
    except Exception:
        pass

if not admin_email:
    admin_email = st.session_state.get("user_email")
    session_id = st.session_state.get("session_id")
    
    if session_id and not admin_email:
        try:
            result = conn.client.table("active_sessions").select("user_email").eq("session_id", session_id).execute()
            if result.data:
                admin_email = result.data[0].get("user_email")
                st.session_state.user_email = admin_email
                st.query_params["session_id"] = session_id
        except Exception:
            pass

if not admin_email:
    st.error("🔒 Please log in to view the dashboard.")
    st.stop()

if session_id_from_url and "session_id" not in st.query_params:
    st.query_params["session_id"] = session_id_from_url
elif st.session_state.get("session_id") and "session_id" not in st.query_params:
    st.query_params["session_id"] = st.session_state.get("session_id")

st.session_state._prev_page = st.session_state.get("current_page", "")
st.session_state.current_page = "dashboard"

init_form_session_state(admin_email)
current_form_id = get_current_form_id()
if not current_form_id:
    current_form_id = ensure_form_exists(admin_email)
    if current_form_id:
        st.session_state.current_form_id = current_form_id

# ══════════════════════════════════════════
# DIMENSION CONFIG
# ══════════════════════════════════════════
SERVQUAL_DIM_COLS = {
    "Tangibles":      "tangibles_avg",
    "Reliability":    "reliability_avg",
    "Responsiveness": "responsiveness_avg",
    "Assurance":      "assurance_avg",
    "Empathy":        "empathy_avg",
}

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
    import transformers
    import os
    
    use_online = os.getenv("USE_ONLINE_MODEL", "false").lower() == "true"
    
    if not use_online:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        local_model_path = os.path.join(script_dir, "model")
        
        if os.path.exists(local_model_path) and os.path.exists(os.path.join(local_model_path, "model.safetensors")):
            model_path = local_model_path
        else:
            model_path = "jamjam15th/chelles-model"
    else:
        model_path = "jamjam15th/chelles-model"
    
    return transformers.pipeline(
        "sentiment-analysis",
        model=model_path,
        tokenizer=model_path,
        top_k=None,
        device=-1,
    )

def demojize_text(text: str) -> str:
    """
    Convert emojis to their text descriptions for better sentiment analysis.
    
    WHY THIS MATTERS:
    When someone submits feedback with emojis like "Great service! 👍", the AI sentiment
    analyzer struggles to understand the emoji because it reads it as a symbol, not words.
    
    WHAT IT DOES:
    This function converts emojis to text so the AI can understand them:
    - Before: "MRT was late 😭" 
    - After:  "MRT was late :loudly_crying_face:"
    
    Now the AI sees the word "crying_face" and understands the emotional context (sadness).
    This makes sentiment analysis more accurate.
    
    REAL EXAMPLES:
    - 👍 becomes :thumbs_up: → AI knows it's positive
    - 😭 becomes :loudly_crying_face: → AI knows it's negative/sad
    - ❤️ becomes :red_heart: → AI knows it's affectionate
    - 😤 becomes :angry_face: → AI knows it's frustrated
    
    USED IN:
    - Overall response sentiment analysis
    - Per-question sentiment analysis
    Before analyzing any feedback, emojis are converted to text so the model understands
    the emotional tone.
    """
    return emoji.demojize(text, delimiters=(':', ':'))

@st.cache_data(max_entries=5000, show_spinner=False)
def analyze_text(text: str) -> tuple[str, float]:
    analyzer = load_model()

    label_map = {
        "LABEL_0": "NEGATIVE", "negative": "NEGATIVE",
        "LABEL_1": "NEUTRAL",  "neutral":  "NEUTRAL",
        "LABEL_2": "POSITIVE", "positive": "POSITIVE",
    }
    
    results = analyzer(text[:512])
    if isinstance(results, list) and len(results) > 0:
        if isinstance(results[0], list):
            res = results[0][0]
        else:
            res = results[0]
    else:
        raise ValueError("Unexpected model output format")
    
    return label_map.get(res["label"], str(res["label"]).upper()), round(res["score"], 4)

# ══════════════════════════════════════════
# DATA FETCH — increased TTL to 30s to avoid
# hammering the DB and triggering crashes
# ══════════════════════════════════════════
@st.cache_data(ttl=30)
def fetch_dashboard_data(email: str, form_id: str) -> pd.DataFrame:
    try:
        r = (conn.client.table("form_responses")
             .select("*").eq("admin_email", email).eq("form_id", form_id)
             .order("created_at").execute())
        return pd.DataFrame(r.data or [])
    except Exception as e:
        st.warning(f"Could not load responses: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def fetch_question_scale_map(email: str, form_id: str) -> dict:
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
            if not prompt or scale_max is None:
                continue
            try:
                scale_map[prompt] = int(scale_max)
            except Exception:
                pass
        return scale_map
    except Exception:
        return {}

@st.cache_data(ttl=30)
def fetch_form_questions_schema(email: str, form_id: str) -> dict:
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
                "prompt": prompt,
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

# ── Fetch only rows that still need sentiment analysis ──
@st.cache_data(ttl=30)
def fetch_pending_sentiment_count(email: str, form_id: str) -> int:
    """Cheap count-only query to check if sentiment work is needed."""
    try:
        result = (conn.client.table("form_responses")
                  .select("id", count="exact")
                  .eq("admin_email", email)
                  .eq("form_id", form_id)
                  .eq("sentiment_status", "pending")
                  .execute())
        return result.count or 0
    except Exception:
        return 0

@st.cache_data(ttl=30)
def fetch_pending_response_sentiment_rows(email: str, form_id: str) -> list[dict]:
    """Fetch only response-level pending rows (raw_feedback sentiment)."""
    try:
        r = (conn.client.table("form_responses")
             .select("id, raw_feedback, sentiment_status, sentiment_score")
             .eq("admin_email", email)
             .eq("form_id", form_id)
             .eq("sentiment_status", "pending")
             .execute())
        return r.data or []
    except Exception:
        return []

@st.cache_data(ttl=30)
def fetch_pending_question_sentiment_rows(email: str, form_id: str) -> list[dict]:
    """Fetch only rows that have pending per-question sentiments."""
    try:
        r = (conn.client.table("form_responses")
             .select("id, question_sentiments")
             .eq("admin_email", email)
             .eq("form_id", form_id)
             .not_.is_("question_sentiments", "null")
             .execute())
        result = []
        for row in (r.data or []):
            qs = row.get("question_sentiments", {})
            if isinstance(qs, dict):
                if any(
                    isinstance(v, dict) and v.get("sentiment") == "pending"
                    for v in qs.values()
                ):
                    result.append(row)
        return result
    except Exception:
        return []

def persist_sentiment_batch(rows: list[dict]):
    if not rows:
        return
    try:
        conn.client.table("form_responses").upsert(rows, on_conflict="id").execute()
    except Exception:
        pass

def run_pending_response_sentiment(email: str, form_id: str):
    """
    Analyze response-level sentiment only for pending rows.
    Invalidates cache after writing so the next render sees fresh data.
    """
    pending_count = fetch_pending_sentiment_count(email, form_id)
    if pending_count == 0:
        return

    pending_rows = fetch_pending_response_sentiment_rows(email, form_id)
    if not pending_rows:
        return

    batch_updates = []
    for row in pending_rows:
        raw = str(row.get("raw_feedback", "")).strip()
        if not raw:
            continue
        try:
            # Convert emojis to text for better sentiment understanding
            processed_raw = demojize_text(raw)
            label, score = analyze_text(processed_raw)
            batch_updates.append({
                "id": row["id"],
                "sentiment_status": label,
                "sentiment_score": score,
            })
        except Exception:
            pass

    if batch_updates:
        persist_sentiment_batch(batch_updates)
        # Invalidate caches so next render picks up the new values
        fetch_dashboard_data.clear()
        fetch_pending_sentiment_count.clear()
        fetch_pending_response_sentiment_rows.clear()

def run_pending_question_sentiment(email: str, form_id: str):
    """
    Analyze per-question sentiments only for rows that still have pending items.
    Invalidates cache after writing.
    """
    pending_rows = fetch_pending_question_sentiment_rows(email, form_id)
    if not pending_rows:
        return

    batch_updates = []
    for row in pending_rows:
        response_id = row.get("id")
        question_sentiments = row.get("question_sentiments", {})

        if not isinstance(question_sentiments, dict):
            continue

        updated = False
        for q_id, q_data in question_sentiments.items():
            if not isinstance(q_data, dict):
                continue
            if q_data.get("enable_sentiment") and q_data.get("sentiment") == "pending":
                text = q_data.get("text", "").strip()
                if text:
                    try:
                        # Convert emojis to text for better sentiment understanding
                        processed_text = demojize_text(text)
                        label, score = analyze_text(processed_text)
                        q_data["sentiment"] = label
                        q_data["confidence"] = score
                        updated = True
                    except Exception:
                        pass

        if updated:
            batch_updates.append({
                "id": response_id,
                "question_sentiments": question_sentiments,
            })

    if batch_updates:
        try:
            conn.client.table("form_responses").upsert(batch_updates, on_conflict="id").execute()
        except Exception:
            pass
        fetch_dashboard_data.clear()
        fetch_pending_question_sentiment_rows.clear()

def recalculate_servqual_columns(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    df = df.copy()

    for dim_name, col_name in SERVQUAL_DIM_COLS.items():
        df[col_name] = None
    df[GENERAL_RATINGS_COL] = None

    if df.empty or not schema:
        return df

    for idx, row in df.iterrows():
        answers = row.get("answers", {})
        if not isinstance(answers, dict):
            continue

        dim_scores = {
            "Tangibles": [],
            "Reliability": [],
            "Responsiveness": [],
            "Assurance": [],
            "Empathy": [],
        }
        general_ratings = []

        for prompt, answer in answers.items():
            if prompt not in schema:
                continue
            question_info = schema[prompt]
            q_type = question_info.get("q_type", "")
            dimension = question_info.get("dimension")

            if q_type not in ("Rating (Likert)", "Rating (1-5)"):
                continue

            try:
                score = float(answer)
            except (TypeError, ValueError):
                continue

            if dimension and dimension in dim_scores:
                dim_scores[dimension].append(score)
            else:
                general_ratings.append(score)

        for dim, col in SERVQUAL_DIM_COLS.items():
            if dim_scores[dim]:
                df.at[idx, col] = sum(dim_scores[dim]) / len(dim_scores[dim])

        if general_ratings:
            df.at[idx, GENERAL_RATINGS_COL] = sum(general_ratings) / len(general_ratings)

    return df

# ══════════════════════════════════════════
# STATIC HEADER
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
# FORM SELECTION GUARD
# ══════════════════════════════════════════
available_forms = st.session_state.get("available_forms", [])
form_is_selected = current_form_id and len([f for f in available_forms if f["form_id"] == current_form_id]) > 0

if not form_is_selected:
    st.info("No form data available. Please create and select a form in the Form Builder.")
    st.stop()

selected_form = next((f for f in available_forms if f["form_id"] == current_form_id), None)
if selected_form:
    form_title = selected_form['title']
    questions_q = conn.client.table("form_questions").select("form_id").eq("form_id", current_form_id).eq("admin_email", admin_email).execute().data or []
    question_count = len(questions_q)
    responses_q = conn.client.table("form_responses").select("form_id").eq("form_id", current_form_id).execute().data or []
    response_count = len(responses_q)
    created_at = selected_form.get('created_at', '')
    date_created = ""
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            date_created = dt.strftime('%b %d, %Y')
        except Exception:
            date_created = "Unknown"

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
    date_to = st.date_input("To", value=datetime.today(), key="dt")

# ══════════════════════════════════════════
# DEMOGRAPHICS HELPERS
# ══════════════════════════════════════════
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

def _demo_chart_specs_all(demo_df: pd.DataFrame, custom_demographic_prompts: list = None) -> list[tuple[str, str]]:
    if custom_demographic_prompts is None:
        custom_demographic_prompts = []
    specs: list[tuple[str, str]] = []
    covered = set()
    for col in demo_df.columns:
        if col in custom_demographic_prompts:
            label = col if len(col) <= 48 else col[:45] + "…"
            specs.append((col, label))
            covered.add(col)
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

# ══════════════════════════════════════════
# DIMENSION DESCRIPTION DICTIONARIES
# ══════════════════════════════════════════
likert_dimension_descriptions = {
    "Tangibles": (
        "Cleanliness, seating comfort, ventilation, and overall physical condition of the vehicle.",
        {
            "strong": "Shows strong passenger satisfaction regarding the vehicle's overall physical condition, including cleanliness, comfortable seats, and good ventilation.",
            "moderate": "Score shows mixed passenger satisfaction regarding the vehicle's overall physical condition, with some aspects meeting expectations and others needing improvement.",
            "weak": "Shows general passenger dissatisfaction regarding the vehicle's physical upkeep, highlighting widespread issues with cleanliness, seat comfort, or ventilation.",
        }
    ),
    "Reliability": (
        "Smooth vehicle operation, fare affordability, and proper handling of payments and change by the crew.",
        {
            "strong": "Shows strong passenger satisfaction regarding overall operational reliability, including smooth vehicle operation, fair pricing, and proper handling of fares.",
            "moderate": "Score shows mixed passenger satisfaction regarding overall operational reliability, with some aspects meeting expectations and others needing improvement.",
            "weak": "Shows general passenger dissatisfaction regarding operational reliability, highlighting widespread issues with vehicle breakdowns, fare affordability, or improper change handling.",
        }
    ),
    "Responsiveness": (
        "Promptness of travel time and the crew's alertness when passengers need to get off.",
        {
            "strong": "Shows strong passenger satisfaction regarding overall responsiveness, including prompt travel times and highly alert crews during passenger drop-offs.",
            "moderate": "Score shows mixed passenger satisfaction regarding overall responsiveness, with some aspects meeting expectations and others needing improvement.",
            "weak": "Shows general passenger dissatisfaction regarding overall responsiveness, highlighting widespread issues with prolonged travel times or missed passenger drop-off points.",
        }
    ),
    "Assurance": (
        "Driver compliance with traffic rules, road safety, and security against theft or harassment.",
        {
            "strong": "Shows strong passenger satisfaction regarding overall passenger assurance, including safe driving, traffic compliance, and security against threats.",
            "moderate": "Score shows mixed passenger satisfaction regarding overall passenger assurance, with some aspects meeting expectations and others needing improvement.",
            "weak": "Shows general passenger dissatisfaction regarding overall passenger assurance, highlighting widespread issues with reckless driving, traffic violations, or internal security.",
        }
    ),
    "Empathy": (
        "Crew politeness, general behavior, and special care given to Seniors, PWDs, and pregnant women.",
        {
            "strong": "Shows strong passenger satisfaction regarding overall crew empathy, including politeness, good behavior, and special care for vulnerable passengers.",
            "moderate": "Score shows mixed passenger satisfaction regarding overall crew empathy, with some aspects meeting expectations and others needing improvement.",
            "weak": "Shows general passenger dissatisfaction regarding overall crew empathy, highlighting widespread issues with rude behavior or neglect towards Seniors, PWDs, or pregnant women.",
        }
    )
}

sentiment_dimension_descriptions = {
    "Tangibles": (
        "Cleanliness, seating comfort, ventilation, and overall physical condition of the vehicle.",
        {
            "strong": "Shows a majority positive response regarding the vehicle's overall physical condition, including cleanliness, comfortable seats, and good ventilation.",
            "moderate": "Shows a mixed response regarding the vehicle's overall physical condition, with some responses meeting expectations and others needing improvement.",
            "weak": "Shows a majority negative response regarding the vehicle's physical upkeep, highlighting widespread issues with cleanliness, seat comfort, or ventilation.",
            "action_strong": "Check the positive feedback to see which vehicle types or routes are getting top marks to sustain these high standards and maintain overall physical comfort.",
            "action_moderate": "Look at the neutral feedback to identify which specific physical responses—like cleanliness, seating, or ventilation—need maintenance to address these gaps and improve overall physical comfort.",
            "action_weak": "Examine negative feedback to identify which vehicles or routes receive complaints regarding their physical condition, cleanliness, comfort, and ventilation, and use this information to address issues and implement necessary improvements."
        }
    ),
    "Reliability": (
        "Smooth vehicle operation, fare affordability, and proper handling of payments and change by the crew.",
        {
            "strong": "Shows a majority positive response regarding overall operational reliability, including smooth vehicle operation, fair pricing, and proper handling of fares.",
            "moderate": "Shows a mixed response regarding overall operational reliability, with some responses meeting expectations and others needing improvement.",
            "weak": "Shows a majority negative response regarding operational reliability, highlighting widespread issues with vehicle breakdowns, fare affordability, or improper change handling.",
            "action_strong": "Check the positive feedback to see which routes or crews are getting top marks to sustain these high standards and maintain service reliability.",
            "action_moderate": "Look at the neutral feedback to identify which specific operational responses—like ride smoothness, fare pricing, or payment handling—need attention to address these inconsistencies and improve service reliability.",
            "action_weak": "Examine the negative feedback to pinpoint exactly which routes or crews are receiving complaints regarding their overall operational reliability to address these issues and improve service consistency."
        }
    ),
    "Responsiveness": (
        "Promptness of travel time and the crew's alertness when passengers need to get off.",
        {
            "strong": "Shows a majority positive response regarding overall responsiveness, including prompt travel times and highly alert crews during passenger drop-offs.",
            "moderate": "Shows a mixed response regarding overall responsiveness, with some responses meeting expectations and others needing improvement.",
            "weak": "Shows a majority negative response regarding overall responsiveness, highlighting widespread issues with prolonged travel times or missed passenger drop-off points.",
            "action_strong": "Check the positive feedback to see which routes or crews are getting top marks to sustain these high standards and maintain service promptness.",
            "action_moderate": "Look at the neutral feedback to identify which specific service responses—like travel speed or drop-off alertness—need coaching to address these delays and improve overall service speed.",
            "action_weak": "Examine the negative feedback to pinpoint exactly which routes or crews are receiving complaints regarding their overall responsiveness to passenger needs to address these gaps and improve service promptness."
        }
    ),
    "Assurance": (
        "Driver compliance with traffic rules, road safety, and security against theft or harassment.",
        {
            "strong": "Shows a majority positive response regarding overall passenger assurance, including safe driving, traffic compliance, and security against threats.",
            "moderate": "Shows a mixed response regarding overall passenger assurance, with some responses meeting expectations and others needing improvement.",
            "weak": "Shows a majority negative response regarding overall passenger assurance, highlighting widespread issues with reckless driving, traffic violations, or internal security.",
            "action_strong": "Check the positive feedback to see which routes or drivers are getting top marks to sustain these high standards and maintain passenger safety.",
            "action_moderate": "Look at the neutral feedback to identify which specific assurance responses—like driving habits, traffic compliance, or internal security—need reinforcement to address these concerns and improve passenger confidence.",
            "action_weak": "Examine the negative feedback to pinpoint exactly which drivers or routes are receiving complaints regarding their overall safety and security practices to address these hazards and improve passenger safety."
        }
    ),
    "Empathy": (
        "Crew politeness, general behavior, and special care given to Seniors, PWDs, and pregnant women.",
        {
            "strong": "Shows a majority positive response regarding overall crew empathy, including politeness, good behavior, and special care for vulnerable passengers.",
            "moderate": "Shows a mixed response regarding overall crew empathy, with some responses meeting expectations and others needing improvement.",
            "weak": "Shows a majority negative response regarding overall crew empathy, highlighting widespread issues with rude behavior or neglect towards Seniors, PWDs, or pregnant women.",
            "action_strong": "Check the positive feedback to see which crews or routes are getting top marks to sustain these high standards and maintain excellent commuter relations.",
            "action_moderate": "Look at the neutral feedback to identify which specific commuter relations aspects—like general politeness or specialized care for vulnerable passengers—need improvement to address these interactions and elevate passenger care.",
            "action_weak": "Examine the negative feedback to pinpoint exactly which crews or routes are receiving complaints regarding their overall empathetic treatment of passengers to address these behaviors and improve commuter relations."
        }
    )
}


# ══════════════════════════════════════════
# MAIN DASHBOARD FRAGMENT
# ══════════════════════════════════════════
@st.fragment
def render_dashboard():
    # ── Show loading indicator while processing sentiment analysis ──
    with st.spinner("⏳ Processing sentiment analysis... This may take a moment."):
        # Run sentiment analysis for any pending rows BEFORE loading display data
        # These calls are cheap (count-only first), and only do real work when needed.
        run_pending_response_sentiment(admin_email, current_form_id)
        run_pending_question_sentiment(admin_email, current_form_id)

        df_raw = fetch_dashboard_data(admin_email, current_form_id)
        question_scale_map = fetch_question_scale_map(admin_email, current_form_id)
        form_schema_full = fetch_form_questions_schema(admin_email, current_form_id)
        form_schema = form_schema_full.get("by_prompt", {})

        df_raw = recalculate_servqual_columns(df_raw, form_schema)

    if df_raw.empty:
        st.markdown("""
        <div class="empty-tab">
          <div class="icon">☹️</div>
          <p>No responses yet. Share your survey link to start collecting data.</p>
        </div>""", unsafe_allow_html=True)
        return

    # ── Timestamps + date filter ──
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

    # ── SERVQUAL dims ──
    present_servqual_dims = {k: v for k, v in SERVQUAL_DIM_COLS.items() if v in df.columns}

    has_general_ratings = (
        GENERAL_RATINGS_COL in df.columns and
        df[GENERAL_RATINGS_COL].notna().any()
    )
    general_ratings_avg_val = float(df[GENERAL_RATINGS_COL].mean()) if has_general_ratings else None

    all_dim_cols = {**present_servqual_dims}
    if has_general_ratings:
        all_dim_cols["General Ratings"] = GENERAL_RATINGS_COL

    # Define tier classification function (used throughout display)
    def get_tier(net_score):
        """Classify sentiment score into tier: strong (>0.5), weak (<-0.5), or moderate"""
        if net_score > 0.5:
            return "strong"
        elif net_score < -0.5:
            return "weak"
        else:
            return "moderate"

    has_servqual_data = bool(present_servqual_dims) and df[
        list(present_servqual_dims.values())
    ].notna().any().any()

    overall_avg = 0.0
    normalized_df = df.copy()

    if has_servqual_data:
        df['overall_servqual'] = df[list(present_servqual_dims.values())].mean(axis=1)
        normalized_df = df.copy()

        observed_max = df[list(present_servqual_dims.values())].max().max()
        scale_max = float(observed_max) if (not pd.isna(observed_max) and observed_max > 5) else 5

        for col in present_servqual_dims.values():
            normalized_df[col] = normalized_df[col].apply(lambda x: normalize_to_5(x, scale_max))

        overall_avg = normalized_df[list(present_servqual_dims.values())].mean().mean()
        if pd.isna(overall_avg):
            overall_avg = 0.0
    else:
        df['overall_servqual'] = None

    has_any_rating_data = has_servqual_data or has_general_ratings

    # ── Sentiment column sanity ──
    sent_col = "sentiment_status"
    if sent_col in df.columns:
        df[sent_col] = df[sent_col].astype(str).str.strip().str.upper()

    sent_valid = (
        df[sent_col].isin(["POSITIVE", "NEUTRAL", "NEGATIVE"])
        if sent_col in df.columns
        else pd.Series(False, index=df.index)
    )
    df_sent = df[sent_valid].copy() if sent_col in df.columns else pd.DataFrame()
    total = len(df)

    # ── Pre-calculate sentiment rates ──
    def _calc_sentiment_rates(df_sent_local):
        all_s = []
        for _, row in df_sent_local.iterrows():
            rl = str(row.get(sent_col, "")).upper().strip() if sent_col in row else ""
            qs = row.get("question_sentiments", {})
            has_qs = False
            if isinstance(qs, dict):
                for q_data in qs.values():
                    if isinstance(q_data, dict) and q_data.get("enable_sentiment") == True:
                        s = str(q_data.get("sentiment", "")).upper().strip()
                        if s in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
                            has_qs = True
                            all_s.append(s)
        tot = len(all_s)
        pos = all_s.count("POSITIVE")
        neu = all_s.count("NEUTRAL")
        neg = all_s.count("NEGATIVE")
        return (
            (pos / tot * 100) if tot > 0 else 0,
            (neu / tot * 100) if tot > 0 else 0,
            (neg / tot * 100) if tot > 0 else 0,
            pos, neu, neg, tot,
        )

    pos_rate, neu_rate, neg_rate, pos_count, neu_count, neg_count, total_sentiments = _calc_sentiment_rates(df_sent)

    # ── Pre-calculate dimension sentiment KPI ──
    def _calc_dim_sentiment(df_sent_local):
        data = {d: {"positive": 0, "neutral": 0, "negative": 0}
                for d in ["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy"]}
        for _, row in df_sent_local.iterrows():
            qs = row.get("question_sentiments", {})
            if isinstance(qs, dict):
                for q_data in qs.values():
                    if isinstance(q_data, dict) and q_data.get("enable_sentiment") == True:
                        s = str(q_data.get("sentiment", "")).upper().strip()
                        d = q_data.get("dimension")
                        if s in ["POSITIVE", "NEUTRAL", "NEGATIVE"] and d in data:
                            data[d][s.lower()] += 1
        net_scores = {}
        totals = {}
        for dim, counts in data.items():
            t = counts["positive"] + counts["neutral"] + counts["negative"]
            totals[dim] = t
            net_scores[dim] = ((counts["positive"] - counts["negative"]) / t) if t > 0 else 0
        return data, net_scores, totals

    dimension_sentiment_data_kpi, dimension_net_scores_kpi, dimension_totals_kpi = _calc_dim_sentiment(df_sent)
    has_dimension_sentiment_kpi = any(dimension_totals_kpi.values())

    # ══════════════════════════════════
    # INTERACTIVE FILTERS
    # ══════════════════════════════════
    st.markdown("""<style>
    .filter-container {
        background: white; border: 1px solid rgba(84,119,146,0.18);
        border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 1.2rem;
    }
    .filter-title {
        font-size: 0.75rem; font-weight: 700; color: rgb(26,50,99);
        text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.8rem;
    }
    </style>""", unsafe_allow_html=True)

    with st.expander("🔍 **Filter By Demographics & Responses**", expanded=False):
        df_filtered = df.copy()
        active_filters = []
        filter_data = {}

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

        excluded_cols = {'id', 'created_at', 'updated_at', 'demo_answers', 'question_sentiments',
                         'sentiment_status', 'sentiment_score', 'raw_feedback', 'overall_servqual'}

        for col in df.columns:
            if col in excluded_cols or col in filter_data:
                continue
            if 'id' in col.lower() or 'sentiment' in col.lower():
                continue
            if col in present_servqual_dims.values() or col == GENERAL_RATINGS_COL:
                continue
            sample_vals = df[col].dropna()
            if len(sample_vals) > 0:
                first_val = sample_vals.iloc[0]
                if isinstance(first_val, list):
                    all_values = []
                    for val in sample_vals:
                        if isinstance(val, list):
                            all_values.extend(val)
                        else:
                            all_values.append(val)
                    if all_values:
                        filter_data[col] = sorted(list(set(str(v) for v in all_values)))
                elif isinstance(first_val, str) and ',' in str(first_val):
                    all_values = []
                    for val in sample_vals:
                        if isinstance(val, str):
                            all_values.extend([v.strip() for v in str(val).split(',') if v.strip()])
                    if all_values:
                        filter_data[col] = sorted(list(set(all_values)))

        if not filter_data:
            st.markdown('<div style="font-size:0.85rem;color:#999;">No filter options available</div>', unsafe_allow_html=True)
        else:
            filter_cols = list(filter_data.items())
            for row_idx in range(0, len(filter_cols), 4):
                row_items = filter_cols[row_idx:row_idx + 4]
                row_cols = st.columns(len(row_items))
                for col_idx, (filter_name, filter_values) in enumerate(row_items):
                    display_name = filter_name.replace('_', ' ').title()
                    with row_cols[col_idx]:
                        st.markdown(f'<div class="filter-title">{display_name}</div>', unsafe_allow_html=True)
                        selected_values = st.multiselect(
                            f"Filter by {filter_name}", options=filter_values, default=None,
                            label_visibility="collapsed", key=f"filter_{filter_name}"
                        )
                        if selected_values:
                            if filter_name in df.columns:
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

        if active_filters:
            st.markdown(f"<div style='font-size:0.85rem;color:#7c8db5;padding-top:0.5rem;'>✓ {', '.join(active_filters)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.9rem;font-weight:600;color:rgb(26,50,99);margin-top:0.5rem;'>Showing {len(df_filtered)} of {total} responses</div>", unsafe_allow_html=True)

        df = df_filtered
        df_sent = df[df[sent_col].isin(["POSITIVE", "NEUTRAL", "NEGATIVE"])] if sent_col in df.columns else pd.DataFrame()

    # ── Recalculate metrics for filtered data ──
    total = len(df)
    pos_rate, neu_rate, neg_rate, pos_count, neu_count, neg_count, total_sentiments = _calc_sentiment_rates(df_sent)

    if present_servqual_dims:
        normalized_df_f = df[list(present_servqual_dims.values())].copy()
        obs_max_f = normalized_df_f.max().max()
        scale_max_f = float(obs_max_f) if (not pd.isna(obs_max_f) and obs_max_f > 5) else 5
        for col in present_servqual_dims.values():
            normalized_df_f[col] = normalized_df_f[col].apply(lambda x: normalize_to_5(x, scale_max_f))
        overall_avg = normalized_df_f[list(present_servqual_dims.values())].mean().mean()
        if pd.isna(overall_avg):
            overall_avg = 0.0
    else:
        overall_avg = 0.0

    dimension_sentiment_data_kpi, dimension_net_scores_kpi, dimension_totals_kpi = _calc_dim_sentiment(df_sent)
    has_dimension_sentiment_kpi = any(dimension_totals_kpi.values())

    # ══════════════════════════════════
    # KPI RIBBON
    # ══════════════════════════════════
    k1, k2 = st.columns(2)

    k1.markdown(f"""<div class="kpi-card">
      <div class="kpi-title">Total Responses</div>
      <div class="kpi-value">{total}</div>
      <div class="kpi-sub">{date_from} → {date_to}</div>
    </div>""", unsafe_allow_html=True)

    if has_dimension_sentiment_kpi:
        active_sent_dims = [d for d in ["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy"]
                            if dimension_totals_kpi.get(d, 0) > 0]
        if active_sent_dims:
            avg_sentiment = sum(dimension_net_scores_kpi.get(d, 0) for d in active_sent_dims) / len(active_sent_dims)
            sentiment_display = f"{avg_sentiment * 100:+.1f}%"
            sentiment_subtext = "Avg sentiment across dimensions"
            avg_tier = get_tier(avg_sentiment)
            tier_color_map = {"strong": "#4a7c59", "weak": "#b03a2e", "moderate": "#999999"}
            sentiment_color = tier_color_map[avg_tier]
        else:
            sentiment_display, sentiment_subtext, sentiment_color = "N/A", "No sentiment data", '#8b9dc3'
    else:
        sentiment_display, sentiment_subtext, sentiment_color = "N/A", "No open-ended responses yet", '#8b9dc3'

    k2.markdown(f"""<div class="kpi-card">
      <div class="kpi-title">Overall SERVQUAL Sentiment Net Score</div>
      <div class="kpi-value" style="color:{sentiment_color};">{sentiment_display}</div>
      <div class="kpi-sub">{sentiment_subtext}</div>
    </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════
    # TABS
    # ══════════════════════════════════
    tab1, tab2, tab3 = st.tabs([
        "🎯 Sentiment",
        "📊 Numerical",
        "👥 Database",
    ])

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
                This tab analyzes <strong>sentiment from open-ended answers</strong> grouped by <strong>SERVQUAL dimension</strong> tags.<br>
                <strong>Net Sentiment Score:</strong> (Positive − Negative) ÷ Total × 100 — ranges from −100% to +100%.<br>
                <strong>How to read:</strong> positive scores indicate favorable feedback; negative scores indicate concerns.<br>
                <strong>How to use:</strong> identify which dimensions have strongest/weakest sentiment, then review the Sentiment tab to read actual comments.
            </div>
            </div>
            """, unsafe_allow_html=True)

            dimension_sentiment_data, dimension_net_scores, dimension_totals = _calc_dim_sentiment(df_sent)

            untagged_sentiment_data = {"positive": 0, "neutral": 0, "negative": 0}
            for _, row in df_sent.iterrows():
                qs = row.get("question_sentiments", {})
                if isinstance(qs, dict):
                    for q_data in qs.values():
                        if isinstance(q_data, dict) and q_data.get("enable_sentiment") == True:
                            s = str(q_data.get("sentiment", "")).upper().strip()
                            d = q_data.get("dimension")
                            if s in ["POSITIVE", "NEUTRAL", "NEGATIVE"] and (not d or d not in dimension_sentiment_data):
                                untagged_sentiment_data[s.lower()] += 1

            untagged_total = sum(untagged_sentiment_data.values())
            untagged_net_score = (
                (untagged_sentiment_data["positive"] - untagged_sentiment_data["negative"]) / untagged_total
            ) if untagged_total > 0 else 0

            has_dimension_sentiment = any(dimension_totals.values())

            if not has_dimension_sentiment and untagged_total == 0:
                st.markdown("""<div class="empty-tab"><div class="icon">🎯</div>
                <p>No open-ended sentiment data yet.<br>
                Tag your open-ended questions with SERVQUAL dimensions in Form Builder.</p>
                </div>""", unsafe_allow_html=True)
            else:
                dim_colors = {
                    "Tangibles": "#547792", "Reliability": "#1a3263",
                    "Responsiveness": "#ffc570", "Assurance": "#3c6482",
                    "Empathy": "#d4a373", "Untagged": "#999999",
                }

                chart_data = []
                for dim in ["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy"]:
                    chart_data.append({
                        "Dimension": dim,
                        "Net Sentiment Score": dimension_net_scores[dim],
                        "Total Responses": dimension_totals[dim]
                    })
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
                        x=alt.X("Net Sentiment Score:Q", scale=alt.Scale(domain=[-1, 1]),
                                axis=alt.Axis(title="Net Sentiment Score (-1 to +1)")),
                        y=alt.Y("Dimension:N", sort=["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy", "Untagged"]),
                        color=alt.Color("Dimension:N",
                                        scale=alt.Scale(domain=list(dim_colors.keys()), range=list(dim_colors.values())),
                                        legend=None),
                        tooltip=["Dimension", alt.Tooltip("Net Sentiment Score:Q", format=".2f"), "Total Responses"],
                    ).properties(height=550)
                    st.altair_chart(chart, use_container_width=True)

                with c2:
                    st.markdown('<div class="section-head">Sentiment Breakdown</div>', unsafe_allow_html=True)
                    for dim in ["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy"]:
                        t = dimension_totals[dim]
                        if t > 0:
                            pos = dimension_sentiment_data[dim]["positive"]
                            neu = dimension_sentiment_data[dim]["neutral"]
                            neg = dimension_sentiment_data[dim]["negative"]
                            net = dimension_net_scores[dim]
                            tier = get_tier(net)
                            tier_color_map = {"strong": "#4a7c59", "weak": "#b03a2e", "moderate": "#999999"}
                            sc = tier_color_map[tier]
                            st.markdown(f"""
                            <div style="margin-bottom:1rem;padding:.75rem;border:1px solid rgba(26,50,99,0.12);border-radius:8px;background:rgba(26,50,99,0.03);">
                            <div style="font-weight:700;color:rgb(26,50,99);margin-bottom:.35rem;">{dim}</div>
                            <div style="font-size:.75rem;color:rgb(84,119,146);margin-bottom:.35rem;">😊 {pos} · 😐 {neu} · 😞 {neg}</div>
                            <div style="font-size:.9rem;font-weight:700;color:{sc};">Net: {net * 100:+.1f}%</div>
                            </div>""", unsafe_allow_html=True)

                    if untagged_total > 0:
                        untagged_tier = get_tier(untagged_net_score)
                        tier_color_map = {"strong": "#4a7c59", "weak": "#b03a2e", "moderate": "#999999"}
                        untagged_color = tier_color_map[untagged_tier]
                        st.markdown(f"""
                        <div style="margin-bottom:1rem;padding:.75rem;border:1px solid rgba(26,50,99,0.12);border-radius:8px;background:rgba(150,150,150,0.03);">
                        <div style="font-weight:700;color:rgb(100,100,100);margin-bottom:.35rem;">Untagged</div>
                        <div style="font-size:.75rem;color:rgb(120,120,120);margin-bottom:.35rem;">
                            😊 {untagged_sentiment_data["positive"]} · 😐 {untagged_sentiment_data["neutral"]} · 😞 {untagged_sentiment_data["negative"]}
                        </div>
                        <div style="font-size:.9rem;font-weight:700;color:{untagged_color};">Net: {untagged_net_score * 100:+.1f}%</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown("---")
                st.markdown('<div class="section-head">📋 Analysis Conclusion</div>', unsafe_allow_html=True)

                tier_labels = {
                    "strong":   ("✅", "Positive",  "#4a7c59", "rgba(74,124,89,0.08)",   "#4a7c59"),
                    "moderate": ("😐", "Neutral",   "#8b9dc3", "rgba(139,157,195,0.08)", "#8b9dc3"),
                    "weak":     ("⚠️", "Negative",  "#b03a2e", "rgba(176,58,46,0.08)",  "#b03a2e"),
                }

                dim_order = ["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy"]
                active_dims = [(d, dimension_net_scores[d]) for d in dim_order if dimension_totals[d] > 0]

                if active_dims and untagged_total > 0:
                    all_scores = [dimension_net_scores[d] for d in dim_order if dimension_totals[d] > 0] + [untagged_net_score]
                    avg_net = sum(all_scores) / len(all_scores)
                elif active_dims:
                    avg_net = sum(dimension_net_scores.values()) / 5
                elif untagged_total > 0:
                    avg_net = untagged_net_score
                else:
                    avg_net = 0

                if avg_net > 0.5: overall_tone, overall_color = "Positive", "#4a7c59"
                elif avg_net >= -0.5: overall_tone, overall_color = "Neutral", "#8b9dc3"
                else: overall_tone, overall_color = "Negative", "#b03a2e"

                tone_descriptions = {
                    "Positive": "Respondents are expressing satisfaction with the service.",
                    "Neutral": "Feedback is balanced with both positive and negative aspects.",
                    "Negative": "Respondents express concerns requiring attention.",
                }
                overall_description = tone_descriptions.get(overall_tone, "")

                max_score = max([s for d, s in active_dims], default=0)
                min_score = min([s for d, s in active_dims], default=0)
                if max_score > 0.5 and min_score < 0.5:
                    weakest_dims = [d for d, s in active_dims if s < 0.5]
                elif min_score <= -0.5:
                    weakest_dims = [d for d, s in active_dims if s <= -0.5]
                else:
                    weakest_dims = []
                weakest_text = ", ".join(weakest_dims) if weakest_dims else ""

                urgent  = [(d, s) for d, s in active_dims if s < -0.5]
                watch   = [(d, s) for d, s in active_dims if -0.5 <= s <= 0.5]
                sustain = [(d, s) for d, s in active_dims if s > 0.5]

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
                }
                </style>
                """

                html = responsive_css + '<div class="sq-conclusion">'
                html += f"""
                <div class="sq-banner">
                <div class="sq-banner-label">Overall sentiment signal</div>
                <div class="sq-banner-value" style="color:{overall_color};">{overall_tone} ({avg_net * 100:+.1f}% net)</div>
                <div class="sq-banner-desc">
                    <div style="margin-bottom: 0.6rem;"><strong>{overall_description}</strong></div>
                    <div>{"Areas of concern: <strong>" + weakest_text + "</strong>" if weakest_text else "Collect more responses to deepen analysis."}</div>
                </div>
                </div>"""

                html += '<div class="sq-dim-grid">'
                total_cards = len(active_dims)

                for i, (dim, net) in enumerate(active_dims):
                    desc_tuple = sentiment_dimension_descriptions.get(dim)
                    if not desc_tuple:
                        continue
                    desc, insight_map = desc_tuple
                    tier = get_tier(net)
                    emoji, label, color, bg, border_color = tier_labels[tier]
                    insight = insight_map[tier]
                    action = insight_map[f"action_{tier}"]
                    pos = dimension_sentiment_data[dim]["positive"]
                    neu_d = dimension_sentiment_data[dim]["neutral"]
                    neg = dimension_sentiment_data[dim]["negative"]
                    tot = dimension_totals[dim]
                    last_row_start = total_cards - (1 if total_cards % 2 != 0 else 2)
                    no_bottom = "no-bottom" if i >= last_row_start else ""
                    no_right = "no-right" if (i % 2 == 1) or (i == total_cards - 1 and total_cards % 2 != 0) else ""
                    html += f"""
                    <div class="sq-dim-card {no_right} {no_bottom}" style="background:{bg};">
                    <div class="sq-dim-name">{dim}</div>
                    <div class="sq-dim-desc">{desc}</div>
                    <div class="sq-dim-score" style="color:{color};">{net * 100:+.1f}%</div>
                    <div class="sq-dim-pill" style="border:1px solid {border_color};color:{color};">{emoji} {label}</div>
                    <div class="sq-dim-insight">{insight}</div>
                    <div class="sq-dim-action" style="border-left-color:{border_color};">{action}</div>
                    <div class="sq-dim-counts">😊 {pos} &nbsp;·&nbsp; 😐 {neu_d} &nbsp;·&nbsp; 😞 {neg} &nbsp;·&nbsp; {tot} total</div>
                    </div>"""

                html += '</div>'
                html += '<div class="sq-priority"><div class="sq-priority-label">Where to act next</div>'
                if urgent:
                    names = " · ".join(d for d, _ in urgent)
                    html += f"""<div class="sq-priority-row">
                    <span class="sq-priority-badge" style="background:rgba(176,58,46,0.12);color:#b03a2e;">Urgent — {names}</span>
                    <span class="sq-priority-text">Negative Net Sentiment. Review specific negative comments in the <strong>Feedback Log</strong> before intervening.</span>
                    </div>"""
                if watch:
                    names = " · ".join(d for d, _ in watch)
                    html += f"""<div class="sq-priority-row">
                    <span class="sq-priority-badge" style="background:rgba(255,197,112,0.18);color:#8b5e1a;">Monitor — {names}</span>
                    <span class="sq-priority-text">Neutral Net Sentiment. Read neutral and negative logs to see what prevents a purely positive experience.</span>
                    </div>"""
                if sustain:
                    names = " · ".join(d for d, _ in sustain)
                    html += f"""<div class="sq-priority-row">
                    <span class="sq-priority-badge" style="background:rgba(74,124,89,0.12);color:#4a7c59;">Sustain — {names}</span>
                    <span class="sq-priority-text">Positive Net Sentiment. Use exact positive reports to highlight strengths.</span>
                    </div>"""
                html += '</div></div>'
                st.markdown(html, unsafe_allow_html=True)

                if untagged_total > 0:
                    st.markdown("---")
                    st.markdown('<div class="section-head">💬 Untagged Open-Ended Responses</div>', unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='font-size:.8rem;color:rgb(80,110,140);margin-bottom:1rem;'>"
                        f"These {untagged_total} response(s) were not tagged with a SERVQUAL dimension. "
                        f"Tag questions in Form Builder to categorize feedback automatically.</div>",
                        unsafe_allow_html=True
                    )
                    uc1, uc2, uc3 = st.columns(3)
                    uc1.metric("😊 Positive", untagged_sentiment_data["positive"])
                    uc2.metric("😐 Neutral", untagged_sentiment_data["neutral"])
                    uc3.metric("😞 Negative", untagged_sentiment_data["negative"])

        with st.expander("📊 Sentiment Data", expanded=True):
            st.markdown("""
            <div class="sentiment-guide-full" style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                        border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;">
            <div style="font-size:.72rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem;">Sentiment Guide</div>
            <div style="font-size:.8rem;color:rgb(60,100,130);line-height:1.6;">
                This tab is for <strong>open-ended answers</strong> (short answer / paragraph), not Likert scores.<br>
                <strong>Distribution:</strong> share of positive, neutral, and negative labels from the AI model.<br>
                <strong>Avg confidence:</strong> average model certainty per label.<br>
                <strong>Feedback log:</strong> question text, respondent answer, sentiment, and time.
            </div>
            </div>
            """, unsafe_allow_html=True)

            r1, r2, r3 = st.columns(3)
            r1.markdown(f"""<div class="kpi-card">
            <div class="kpi-title">Positive Rate</div>
            <div class="kpi-value pos">{pos_rate:.1f}%</div>
            <div class="kpi-sub">{pos_count} responses</div>
            </div>""", unsafe_allow_html=True)
            r2.markdown(f"""<div class="kpi-card">
            <div class="kpi-title">Neutral Rate</div>
            <div class="kpi-value" style="color: var(--neu);">{neu_rate:.1f}%</div>
            <div class="kpi-sub">{neu_count} responses</div>
            </div>""", unsafe_allow_html=True)
            r3.markdown(f"""<div class="kpi-card">
            <div class="kpi-title">Negative Rate</div>
            <div class="kpi-value neg">{neg_rate:.1f}%</div>
            <div class="kpi-sub">{neg_count} responses</div>
            </div>""", unsafe_allow_html=True)

            # ─────────────────────────────────────────────────────────────────────────────
            # DEFINE VOCABULARY & CONFIGURATION (outside if/else for proper scope)
            # ─────────────────────────────────────────────────────────────────────────────

            DESCRIPTIVE_WORDS = {
                "positive": [
                    "maganda","magaan","clean","comfortable","mabilis","fast","kind","mabait",
                    "helpful","tumutulong","polite","educated","professional","cozy",
                    "excellent","good","nice","efficient","safe","secure","reliable","consistent",
                    "organized","tidy","punctual","courteous","friendly","accommodating","smooth",
                    "pleasant","affordable","fair","honest","caring","attentive",
                ],
                "negative": [
                    "masama","masikip","dirty","uncomfortable","mabagal","slow","rude","bastos",
                    "unhelpful","unprofessional","poor","bad","awful",
                    "unsafe","dangerous","unreliable","late","broken","damaged","old","rusty",
                    "crowded","messy","impolite","unfriendly","disrespectful","annoying",
                    "overpriced","expensive","cramped","smelly","noisy","delayed",
                ],
            }

            SUBJECTS = {
                "vehicle":     ["bus","jeep","sasakyan","vehicle","biyahe","coach"],
                "driver":      ["driver","conductor","mandirigma","operator","kuya"],
                "seats":       ["seat","chair","upuan","cushion","legroom"],
                "cleanliness": ["clean","dirty","hygiene","linis","garbage","trash"],
                "service":     ["service","serbisyo","experience","ride","trip"],
                "speed":       ["speed","time","duration","mabilis","mabagal","bilis","fast","slow"],
                "staff":       ["staff","crew","attendant","personnel","workers"],
                "route":       ["route","stop","station","destination"],
                "safety":      ["safety","secure","safe","ligtas","accident","reckless"],
                "fare":        ["fare","bayad","pamasahe","change","sukli","payment"],
                "comfort":     ["comfort","comfortable","uncomfortable","ginhawa","cramped","masikip"],
                "ventilation": ["air","aircon","fan","ventilation","hangin","temperatura","smell"],
            }

            DEMO_QUESTION_SET = {
                "What is your age bracket?","What is your gender?",
                "What is your primary occupation?",
                "What primary land public transportation mode do you usually use?",
                "Which PUV or transport types do you usually ride or use? (Select all that apply)",
                "Which land public transportation modes do you usually use? (Select all that apply)",
                "How often do you commute?",
            }

            DIMENSION_ORDER = ["Tangibles","Reliability","Responsiveness","Assurance","Empathy"]

            DIM_THEME = {
                "Tangibles":      {"accent":"#818cf8","bg":"#eef2ff","icon":"🚌","dark":"#4f46e5"},
                "Reliability":    {"accent":"#22d3ee","bg":"#e0f7fa","icon":"⏰","dark":"#0891b2"},
                "Responsiveness": {"accent":"#a78bfa","bg":"#ede9fe","icon":"⚡","dark":"#7c3aed"},
                "Assurance":      {"accent":"#f472b6","bg":"#fce7f3","icon":"🛡️","dark":"#db2777"},
                "Empathy":        {"accent":"#34d399","bg":"#d1fae5","icon":"❤️","dark":"#059669"},
            }

            SENT_COLOR  = {"Positive":"#4ade80","Negative":"#f87171","Neutral":"#94a3b8"}
            SENT_DARK   = {"Positive":"#16a34a","Negative":"#dc2626","Neutral":"#6b7280"}
            SENT_BG     = {"Positive":"#dcfce7","Negative":"#fee2e2","Neutral":"#f3f4f6"}
            SENT_EMOJI  = {"Positive":"😊","Negative":"😞","Neutral":"😐"}

            if df_sent.empty:
                st.markdown("""<div class="empty-tab"><div class="icon">💬</div>
                <p>No analyzed responses yet.<br>
                The AI model processes open-text answers automatically on submission.</p>
                </div>""", unsafe_allow_html=True)
            else:
                all_sentiments_list = []
                all_confidence_scores = []

                for _, row in df_sent.iterrows():
                    rl = str(row.get(sent_col, "")).upper().strip() if sent_col in row else ""
                    rl_score = row.get("sentiment_score")
                    qs = row.get("question_sentiments", {})
                    has_qs = False
                    if isinstance(qs, dict):
                        for q_data in qs.values():
                            if isinstance(q_data, dict) and q_data.get("enable_sentiment") == True:
                                s = str(q_data.get("sentiment", "")).upper().strip()
                                if s in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
                                    has_qs = True
                                    all_sentiments_list.append(s)
                                    conf = q_data.get("confidence") or q_data.get("sentiment_score") or rl_score
                                    if pd.notna(conf):
                                        try:
                                            all_confidence_scores.append({"sentiment": s, "confidence": float(conf)})
                                        except Exception:
                                            pass

                sentiment_counts = {
                    "POSITIVE": all_sentiments_list.count("POSITIVE"),
                    "NEUTRAL":  all_sentiments_list.count("NEUTRAL"),
                    "NEGATIVE": all_sentiments_list.count("NEGATIVE"),
                }

                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown('<div class="section-head">Distribution</div>', unsafe_allow_html=True)
                    sc = pd.DataFrame([
                        {"Sentiment": "POSITIVE", "Count": sentiment_counts["POSITIVE"]},
                        {"Sentiment": "NEUTRAL",  "Count": sentiment_counts["NEUTRAL"]},
                        {"Sentiment": "NEGATIVE", "Count": sentiment_counts["NEGATIVE"]},
                    ])
                    st.altair_chart(
                        alt.Chart(sc).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                            x=alt.X("Sentiment:N", sort=["POSITIVE", "NEUTRAL", "NEGATIVE"], axis=alt.Axis(labelAngle=0)),
                            y="Count:Q",
                            color=alt.Color("Sentiment:N",
                                            scale=alt.Scale(domain=["POSITIVE", "NEUTRAL", "NEGATIVE"],
                                                            range=["#4a7c59", "#8b9dc3", "#b03a2e"]),
                                            legend=None),
                            tooltip=["Sentiment", "Count"],
                        ).properties(height=200),
                        use_container_width=True,
                    )
                    st.caption(f"Positive: {sentiment_counts['POSITIVE']} | Neutral: {sentiment_counts['NEUTRAL']} | Negative: {sentiment_counts['NEGATIVE']}")

                    st.markdown('<div class="section-head">Avg Confidence</div>', unsafe_allow_html=True)
                    conf_by_s = {"POSITIVE": [], "NEUTRAL": [], "NEGATIVE": []}
                    for sc_d in all_confidence_scores:
                        if sc_d["sentiment"] in conf_by_s:
                            conf_by_s[sc_d["sentiment"]].append(sc_d["confidence"])
                    for s, color in [("POSITIVE", "#4a7c59"), ("NEUTRAL", "#8b9dc3"), ("NEGATIVE", "#b03a2e")]:
                        scores = conf_by_s[s]
                        pct = (sum(scores) / len(scores) * 100) if scores else 0
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
                        "What is your age bracket?", "What is your gender?",
                        "What is your primary occupation?",
                        "What primary land public transportation mode do you usually use?",
                        "Which PUV or transport types do you usually ride or use? (Select all that apply)",
                        "Which land public transportation modes do you usually use? (Select all that apply)",
                        "How often do you commute?",
                    }

                    try:
                        q_res = conn.client.table("form_questions").select("id, prompt").eq("admin_email", admin_email).eq("form_id", current_form_id).execute()
                        q_text_to_id = {row.get("prompt", ""): str(row.get("id", "")) for row in (q_res.data or [])}
                    except Exception:
                        q_text_to_id = {}

                    log_rows = []
                    for _, row in df_sent.iterrows():
                        ans_map = row.get("answers", {})
                        qs = row.get("question_sentiments", {})
                        rl_confidence = row.get("sentiment_score", None)
                        submitted = row.get("created_at", None)
                        if not isinstance(ans_map, dict):
                            continue

                        idx = 0
                        for question, answer in ans_map.items():
                            answer_text = str(answer).strip() if answer is not None else ""
                            if not answer_text or question in demo_question_set:
                                continue
                            if pd.notna(pd.to_numeric(answer_text, errors="coerce")):
                                continue

                            q_id = q_text_to_id.get(question)
                            q_data = None
                            if isinstance(qs, dict):
                                if q_id:
                                    q_data = qs.get(q_id, {})
                                if not q_data or not isinstance(q_data, dict) or not q_data.get("sentiment"):
                                    q_data = qs.get(question, {})

                            if isinstance(q_data, dict):
                                if q_data.get("enable_sentiment") is False:
                                    continue
                                q_sentiment = str(q_data.get("sentiment", "")).upper().strip()
                                if not q_sentiment or q_sentiment == "PENDING":
                                    continue
                                idx += 1
                                q_conf = q_data.get("confidence") or q_data.get("sentiment_score") or rl_confidence
                                q_dimension = q_data.get("dimension")
                                if not q_dimension and q_id:
                                    q_dimension = form_schema_full.get("by_id", {}).get(str(q_id), {}).get("dimension")
                                if not q_dimension:
                                    q_dimension = form_schema.get(question, {}).get("dimension")
                                log_rows.append({
                                    "Response #": f"#{idx}",
                                    "Question": str(question),
                                    "Dimension": q_dimension if q_dimension else "Untagged",
                                    "Answer": answer_text,
                                    "Sentiment": q_sentiment,
                                    "Confidence": f"{q_conf*100:.1f}%" if pd.notna(q_conf) else "N/A",
                                    "Submitted": submitted,
                                })

                    if log_rows:
                        log_df = pd.DataFrame(log_rows)
                        fc1, fc2, fc3 = st.columns(3)
                        with fc1:
                            s_filter = st.multiselect("Filter by Sentiment", ["POSITIVE", "NEUTRAL", "NEGATIVE"], default=[], key="log_sentiment_filter")
                        with fc2:
                            d_filter = st.multiselect("Filter by Dimension", sorted(log_df["Dimension"].unique().tolist()), default=[], key="log_dimension_filter")
                        with fc3:
                            q_filter = st.multiselect("Filter by Question", sorted(log_df["Question"].unique().tolist()), default=[], key="log_question_filter")

                        filt_log = log_df
                        if s_filter or d_filter or q_filter:
                            filt_log = log_df[
                                (log_df["Sentiment"].isin(s_filter) if s_filter else True) &
                                (log_df["Dimension"].isin(d_filter) if d_filter else True) &
                                (log_df["Question"].isin(q_filter) if q_filter else True)
                            ]

                        def color_sent(val):
                            return {
                                "POSITIVE": "color:#4a7c59;font-weight:700",
                                "NEGATIVE": "color:#b03a2e;font-weight:700",
                                "NEUTRAL":  "color:#8b9dc3;font-weight:700",
                            }.get(str(val).upper().strip(), "")

                        st.markdown(f'<div style="font-size:0.8rem;color:rgb(120,148,172);margin-bottom:0.8rem;">Showing {len(filt_log)} of {len(log_df)} entries</div>', unsafe_allow_html=True)
                        st.dataframe(
                            filt_log[["Response #", "Question", "Dimension", "Answer", "Sentiment", "Confidence"]].style.map(color_sent, subset=["Sentiment"]),
                            use_container_width=True, hide_index=True, height=300,
                        )
                    else:
                        st.info("No open-text feedback in the selected range.")

                st.markdown('<div class="section-head">Sentiment by Question</div>', unsafe_allow_html=True)
                st.caption("Shows how many positive, negative, and neutral responses each question received.")

                q_sentiment_data = []
                if "question_sentiments" in df_sent.columns:
                    id_to_prompt = form_schema_full.get("by_id", {})
                    for _, row in df_sent.iterrows():
                        qs = row.get("question_sentiments", {})
                        if isinstance(qs, dict):
                            for q_id_k, q_data in qs.items():
                                if isinstance(q_data, dict) and q_data.get("enable_sentiment") == True:
                                    s = q_data.get("sentiment")
                                    if s:
                                        su = str(s).upper().strip()
                                        if su not in ("PENDING",) and su in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
                                            q_info = id_to_prompt.get(str(q_id_k), {}) or id_to_prompt.get(q_id_k, {})
                                            q_prompt = q_info.get("prompt", str(q_id_k))
                                            q_sentiment_data.append({"Question": q_prompt, "Sentiment": su})

                if q_sentiment_data:
                    q_sent_df = pd.DataFrame(q_sentiment_data)
                    q_pivot = q_sent_df.groupby(["Question", "Sentiment"]).size().reset_index(name="Count")
                    all_qs = q_pivot["Question"].unique()
                    full_pivot = []
                    for q in all_qs:
                        for s in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
                            cnt = q_pivot[(q_pivot["Question"] == q) & (q_pivot["Sentiment"] == s)]["Count"].values
                            full_pivot.append({"Question": q, "Sentiment": s, "Count": int(cnt[0]) if len(cnt) > 0 else 0})
                    full_pivot_df = pd.DataFrame(full_pivot)
                    if not full_pivot_df.empty:
                        st.altair_chart(
                            alt.Chart(full_pivot_df).mark_bar().encode(
                                x=alt.X("Count:Q", title="Number of Responses"),
                                y=alt.Y("Question:N", title="", sort="-x"),
                                color=alt.Color("Sentiment:N",
                                                scale=alt.Scale(domain=["POSITIVE", "NEUTRAL", "NEGATIVE"],
                                                                range=["#4a7c59", "#8b9dc3", "#b03a2e"]),
                                                legend=alt.Legend(title="Sentiment")),
                                tooltip=["Question:N", "Sentiment:N", "Count:Q"],
                            ).properties(height=max(300, len(all_qs) * 40)),
                            use_container_width=True,
                        )
                else:
                    st.info("No per-question sentiment analysis available.")

                st.markdown("---")

                @st.cache_data(show_spinner=False)
                def load_combined_stopwords():
                    # 1. Load English stopwords via NLTK
                    try:
                        nltk.data.find('corpora/stopwords')
                    except LookupError:
                        nltk.download('stopwords', quiet=True)
                    
                    eng_stops = set(stopwords.words('english'))
                    
                    # 2. Fetch Tagalog stopwords direct from the stopwords-iso GitHub repo
                    tl_stops = set()
                    github_url = "https://raw.githubusercontent.com/stopwords-iso/stopwords-tl/master/stopwords-tl.txt"
                    
                    try:
                        req = urllib.request.Request(github_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req) as response:
                            content = response.read().decode('utf-8')
                            tl_stops = set(word.strip().lower() for word in content.splitlines() if word.strip())
                    except Exception as e:
                        st.warning(f"⚠️ Hindi ma-fetch ang Tagalog stopwords mula sa GitHub: {e}")
                    
                    # 3. Custom filler words sa chat/text na madalas gamitin ng Pinoy
                    custom_stops = {
                        # Tagalog Fillers & Variations
                        "po", "opo", "yung", "ung", "iyong", "yong", "yon", "yun",
                        "lng", "lang", "lamang", "namn", "naman", "man",
                        "nyo", "nya", "niya", "nila", "sila", "siya", "kayo", "tayo", "kami",
                        "namin", "natin", "kanila", "kanya", "ninyo", "niyo",
                        "eh", "ah", "oh", "nga", "ng", "nang", "mga", "ang",
                        "din", "rin", "pang", "pa", "na", "ba", "kasi", "kase", "dahil",
                        "para", "kaya", "tas", "tapos", "tsaka", "chaka", "saka",
                        "ito", "yan", "iyan", "iyon", "doon", "dun", "dito", "diyan", "jan", "dyan",
                        "daw", "raw", "talaga", "masyado", "sobra", "medyo", "halos",
                        "kahit", "pero", "sana", "pati", "tulad", "gaya", "parang",
                        "ano", "sino", "saan", "bakit", "bat", "paano", "pano", "kailan",
                        "nito", "niyan", "niyon", "pag", "kapag", "kung", "habang", "kundi",
                        "maging", "bilang", "ayon", "kay", "kina", "muna", "pala", "paki",
                        "ganun", "ganyan", "ganito", "ganoon", "bale", "nawa",
                        "yata", "ata", "siguro", "baka", "ewan", "pwede", "pede", "wala", "lalo", "mas"
                        
                        # English Chat Fillers & Common Slangs (that NLTK might miss)
                        "ok", "okay", "alright", "yeah", "yes", "no", "nah", "pls", "plz", "please",
                        "thx", "thanks", "ty", "very", "too", "so", "much", "really", "just", 
                        "like", "literally", "basically", "actually", "anyway", "btw", "fyi",
                        "omg", "idk", "lol", "tbh", "imho", "kinda", "sorta", "maybe", "perhaps",
                        "always", "never", "sometimes", "often", "usually", "also", "then", "than",
                        "now", "later", "today", "tomorrow", "yesterday", "here", "there",
                        "anything", "everything", "nothing", "something", "someone", "anyone",
                        "everyone", "nobody", "anybody", "somebody", "everybody",
                        "well", "hmm", "uhm", "uh", "wow", "asap"
                    }
                    
                    # Pagsamahin lahat ng lists!
                    return eng_stops.union(tl_stops).union(custom_stops)

                def extract_word_insights(df_sent, sent_col, q_text_to_id, form_schema, form_schema_full, excluded_words=None):
                    insight_raw      = {}
                    bubble_resp_map  = {}

                    # Tawagin ang auto-fetcher natin
                    STOPWORDS = load_combined_stopwords()
                    
                    # Add user-excluded words to stopwords
                    if excluded_words:
                        if isinstance(excluded_words, str):
                            try:
                                excluded_words = json.loads(excluded_words)
                            except:
                                excluded_words = [w.strip().lower() for w in excluded_words.split(",") if w.strip()]
                        if isinstance(excluded_words, list):
                            STOPWORDS = STOPWORDS.union(set(w.lower() for w in excluded_words))

                    for _, row in df_sent.iterrows():
                        ans_map = row.get("answers", {})
                        qs      = row.get("question_sentiments", {})
                        if not isinstance(ans_map, dict) or not isinstance(qs, dict):
                            continue

                        for question, answer in ans_map.items():
                            answer_text = str(answer).strip() if answer is not None else ""
                            if not answer_text or len(answer_text) < 5 or question in DEMO_QUESTION_SET:
                                continue
                            if pd.notna(pd.to_numeric(answer_text, errors="coerce")):
                                continue

                            q_id   = q_text_to_id.get(question)
                            q_data = None
                            if q_id:
                                q_data = qs.get(q_id, {})
                            if not q_data or not isinstance(q_data, dict):
                                q_data = qs.get(question, {})
                            if not isinstance(q_data, dict):
                                continue
                            if q_data.get("enable_sentiment") is False:
                                continue
                            q_sentiment = str(q_data.get("sentiment", "")).upper().strip()
                            if not q_sentiment or q_sentiment == "PENDING":
                                continue

                            q_dimension = q_data.get("dimension")
                            if not q_dimension and q_id:
                                q_dimension = form_schema_full.get("by_id", {}).get(str(q_id), {}).get("dimension")
                            if not q_dimension:
                                q_dimension = form_schema.get(question, {}).get("dimension")
                            if not q_dimension:
                                q_dimension = "Untagged"

                            answer_lower = answer_text.lower()
                            # Kunin lahat ng words na may 3 o higit pang letters
                            words = re.findall(r'\b[a-z]{3,}\b', answer_lower)

                            # Filter out stopwords (Awtomatikong natatanggal lahat ng nasa GitHub list)
                            meaningful_words = [w for w in words if w not in STOPWORDS]

                            if not meaningful_words:
                                continue

                            # set() is used so a word is only counted once per response
                            for word in set(meaningful_words): 
                                insight_key = word
                                bubble_key  = f"{word}|{q_dimension}" 

                                dim_bucket = insight_raw.setdefault(q_dimension, {})
                                if insight_key not in dim_bucket:
                                    dim_bucket[insight_key] = {
                                        "positive":0, "negative":0, "neutral":0,
                                        "word": word,
                                    }
                                
                                sk = q_sentiment.lower() if q_sentiment in ("POSITIVE","NEGATIVE") else "neutral"
                                if sk in ("positive","negative","neutral"):
                                    dim_bucket[insight_key][sk] += 1

                                q_conf = q_data.get("confidence") or q_data.get("sentiment_score")
                                created_at = row.get("created_at")
                                resp_entry = {
                                    "Question":   question,
                                    "Answer":     answer_text,
                                    "Sentiment":  q_sentiment,
                                    "Confidence": f"{q_conf*100:.1f}%" if pd.notna(q_conf) else "N/A",
                                    "Submitted":  created_at.strftime("%Y-%m-%d %H:%M") 
                                                  if hasattr(created_at, "strftime") else str(created_at),
                                    "Dimension":  q_dimension,
                                }
                                
                                bucket = bubble_resp_map.setdefault(bubble_key, [])
                                if resp_entry not in bucket:
                                    bucket.append(resp_entry)

                    dimension_insights = {}
                    for dim in DIMENSION_ORDER:
                        if dim not in insight_raw:
                            continue
                        bubbles = []
                        for ik, counts in insight_raw[dim].items():
                            total = counts["positive"] + counts["negative"] + counts["neutral"]
                            
                            if total < 1: 
                                continue
                                
                            # NET SENTIMENT SCORE LOGIC: (Pos - Neg) / Total * 100
                            net_score = ((counts["positive"] - counts["negative"]) / total) * 100
                            
                            if net_score > 50:
                                sentiment = "Positive"
                            elif net_score < -50:
                                sentiment = "Negative"
                            else:
                                sentiment = "Neutral"
                                
                            bubbles.append({
                                "word":       counts["word"],
                                "total":      total,
                                "positive":   counts["positive"],
                                "negative":   counts["negative"],
                                "neutral":    counts["neutral"],
                                "sentiment":  sentiment,
                                "bubble_key": f"{counts['word']}|{dim}",
                            })
                        
                        bubbles.sort(key=lambda x: x["total"], reverse=True)
                        if bubbles:
                            dimension_insights[dim] = bubbles[:15]

                    return dimension_insights, bubble_resp_map


                # ─────────────────────────────────────────────────────────────────────────────
                # SVG BUBBLE CHART
                # ─────────────────────────────────────────────────────────────────────────────

                def build_svg_bubble_chart(dimension_insights):
                    W, H     = 1200, 500
                    PAD_L    = 68
                    PAD_T    = 48
                    PAD_B    = 86
                    PAD_R    = 28
                    CHART_W  = W - PAD_L - PAD_R
                    CHART_H  = H - PAD_T - PAD_B

                    active_dims = [d for d in DIMENSION_ORDER if d in dimension_insights]
                    n_dims      = len(active_dims)
                    col_w       = CHART_W / n_dims

                    all_totals = [b["total"] for d in active_dims for b in dimension_insights[d]]
                    max_total  = max(all_totals) if all_totals else 10
                    y_max      = max(max_total + 2, 10)

                    def y_to_px(val):
                        return PAD_T + CHART_H - (val / y_max) * CHART_H

                    L = []

                    # ── defs ──────────────────────────────────────────────────────────────────
                    L.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
                            f'style="width:100%;height:auto;display:block;border-radius:16px;'
                            f'box-shadow:0 24px 64px rgba(0,0,0,.38);">')
                    L.append('<defs>')
                    L.append(
                        "<style>"
                        "@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap');"
                        ".bc { font-family:'DM Sans',sans-serif; }"
                        ".bc-grp:hover .bc-tip  { opacity:1; }"
                        ".bc-grp:hover .bc-main { filter:brightness(1.18) drop-shadow(0 0 12px currentColor); }"
                        ".bc-tip  { opacity:0; pointer-events:none; transition:opacity .18s ease; }"
                        ".bc-main { transition:filter .2s ease; }"
                        "@keyframes bc-pop { 0%  { transform:scale(0); opacity:0; } 68% { transform:scale(1.1); } 100%{ transform:scale(1); opacity:1; } }"
                        ".bc-anim { animation:bc-pop .55s cubic-bezier(.34,1.56,.64,1) both; }"
                        "</style>"
                    )

                    # Radial gradients
                    for sent, c1, c2 in [
                        ("Positive","#86efac","#16a34a"),
                        ("Negative","#fca5a5","#dc2626"),
                        ("Neutral", "#cbd5e1","#64748b"),
                    ]:
                        L.append(f'<radialGradient id="rg-{sent}" cx="32%" cy="28%" r="68%">')
                        L.append(f'  <stop offset="0%" stop-color="{c1}"/>')
                        L.append(f'  <stop offset="100%" stop-color="{c2}" stop-opacity=".7"/>')
                        L.append(f'</radialGradient>')

                    # Drop-shadow / glow filters
                    for sent, gc in [("Positive","74,222,128"),("Negative","248,113,113"),("Neutral","148,163,184")]:
                        L.append(f'<filter id="gf-{sent}" x="-60%" y="-60%" width="220%" height="220%">')
                        L.append(f'  <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="b"/>')
                        L.append(f'  <feFlood flood-color="rgb({gc})" flood-opacity=".5" result="c"/>')
                        L.append(f'  <feComposite in="c" in2="b" operator="in" result="g"/>')
                        L.append(f'  <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>')
                        L.append(f'</filter>')

                    # Tooltip drop shadow
                    L.append('<filter id="tshadow" x="-10%" y="-10%" width="120%" height="130%">')
                    L.append('  <feDropShadow dx="0" dy="4" stdDeviation="6" flood-opacity=".25"/>')
                    L.append('</filter>')

                    L.append('</defs>')

                    # ── Background ─────────────────────────────────────────────────────────────
                    L.append(f'<rect width="{W}" height="{H}" rx="16" fill="#0d1526"/>')
                    # Subtle dot grid
                    L.append('<pattern id="dots" x="0" y="0" width="28" height="28" patternUnits="userSpaceOnUse">')
                    L.append('  <circle cx="14" cy="14" r=".9" fill="#1a2744"/>')
                    L.append('</pattern>')
                    L.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#dots)"/>')
                    # Top gradient highlight
                    L.append(f'<rect width="{W}" height="100" rx="16" '
                            f'fill="url(#topshine)" opacity=".4"/>')
                    L.append('<linearGradient id="topshine" x1="0" y1="0" x2="0" y2="1">')
                    L.append('  <stop offset="0%" stop-color="#ffffff" stop-opacity=".04"/>')
                    L.append('  <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>')
                    L.append('</linearGradient>')

                    # ── Y-axis ─────────────────────────────────────────────────────────────────
                    L.append(f'<line x1="{PAD_L}" y1="{PAD_T-4}" x2="{PAD_L}" y2="{PAD_T+CHART_H+4}" '
                            f'stroke="#2d3f66" stroke-width="1.5"/>')

                    for i in range(6):
                        val = round(y_max * i / 5)
                        py  = y_to_px(val)
                        L.append(f'<line x1="{PAD_L+1}" y1="{py:.1f}" x2="{W-PAD_R}" y2="{py:.1f}" '
                                f'stroke="#1a2744" stroke-width="1" stroke-dasharray="5 4"/>')
                        L.append(f'<text x="{PAD_L-8}" y="{py+4:.1f}" text-anchor="end" font-size="11" '
                                f'fill="#4a6fa5" class="bc">{val}</text>')

                    L.append(f'<text transform="rotate(-90 20 {PAD_T+CHART_H//2})" '
                            f'x="20" y="{PAD_T+CHART_H//2}" text-anchor="middle" '
                            f'font-size="11" font-weight="700" fill="#4a6fa5" letter-spacing="1" class="bc">'
                            f'MENTIONS</text>')

                    # ── Dimension columns ──────────────────────────────────────────────────────
                    for ci, dim in enumerate(active_dims):
                        theme   = DIM_THEME[dim]
                        bubbles = dimension_insights[dim]
                        x0      = PAD_L + ci * col_w
                        xc      = x0 + col_w / 2

                        # Column divider
                        if ci > 0:
                            L.append(f'<line x1="{x0:.1f}" y1="{PAD_T}" x2="{x0:.1f}" y2="{PAD_T+CHART_H}" '
                                    f'stroke="#1a2744" stroke-width="1"/>')

                        # Subtle column bg on hover (always slight tint)
                        L.append(f'<rect x="{x0+1:.1f}" y="{PAD_T}" width="{col_w-2:.1f}" height="{CHART_H}" '
                                f'fill="{theme["accent"]}" opacity=".025" rx="4"/>')

                        # Bottom accent bar + dimension label
                        bar_w = min(col_w * 0.55, 90)
                        L.append(f'<rect x="{xc - bar_w/2:.1f}" y="{PAD_T+CHART_H+6}" '
                                f'width="{bar_w:.1f}" height="3" rx="2" fill="{theme["accent"]}"/>')
                        L.append(f'<text x="{xc:.1f}" y="{PAD_T+CHART_H+26}" text-anchor="middle" '
                                f'font-size="12.5" font-weight="800" fill="{theme["accent"]}" class="bc">'
                                f'{theme["icon"]} {dim}</text>')

                        # ── Bubbles ───────────────────────────────────────────────────────────
                        n      = len(bubbles)
                        max_r  = min(36, (col_w * 0.38))
                        min_r  = 13

                        for bi, b in enumerate(bubbles):
                            sent  = b["sentiment"]
                            total = b["total"]
                            word  = b["word"] # <-- pinalitan ang desc at subj
                            pos   = b["positive"]
                            neg   = b["negative"]
                            neu   = b["neutral"]

                            ratio = (total - 2) / max(y_max - 2, 1)
                            r     = min_r + ratio * (max_r - min_r)
                            cy    = y_to_px(total)
                            cy    = max(PAD_T + r + 3, min(PAD_T + CHART_H - r - 3, cy))

                            # Horizontal spread
                            spread = col_w * 0.68
                            if n == 1:
                                offset = 0.0
                            else:
                                offset = spread * (bi / (n - 1) - 0.5)
                            cx = xc + offset
                            cx = max(x0 + r + 4, min(x0 + col_w - r - 4, cx))

                            delay = f"{ci*0.07 + bi*0.055:.2f}s"
                            gf    = f"gf-{sent}"

                            L.append(f'<g class="bc-grp" style="transform-origin:{cx:.1f}px {cy:.1f}px;">')

                            # Outer glow halo & Main bubble
                            L.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r+7:.1f}" fill="{SENT_COLOR[sent]}" opacity=".10"/>')
                            L.append(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#rg-{sent})" filter="url(#{gf})" opacity=".92" class="bc-main bc-anim" style="animation-delay:{delay};transform-origin:{cx:.1f}px {cy:.1f}px;"/>')
                            L.append(f'  <ellipse cx="{cx - r*0.27:.1f}" cy="{cy - r*0.3:.1f}" rx="{r*0.28:.1f}" ry="{r*0.17:.1f}" fill="white" opacity=".28" class="bc-anim" style="animation-delay:{delay};"/>')

                            # Single Word Label (Centered)
                            fs_w = max(9, min(14, int(r * 0.55)))
                            L.append(f'  <text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" '
                                    f'dominant-baseline="middle" font-size="{fs_w}" font-weight="800" '
                                    f'fill="white" class="bc" '
                                    f'style="pointer-events:none;text-shadow:0 1px 4px rgba(0,0,0,.7);">'
                                    f'{word[:8].upper()}</text>')

                            # Frequency badge
                            bx = cx + r * 0.65
                            by_ = cy - r * 0.65
                            L.append(f'  <circle cx="{bx:.1f}" cy="{by_:.1f}" r="10.5" fill="#0d1526" opacity=".88"/>')
                            L.append(f'  <text x="{bx:.1f}" y="{by_+1:.1f}" text-anchor="middle" dominant-baseline="middle" font-size="8.5" font-weight="800" fill="{SENT_COLOR[sent]}" class="bc">{total}</text>')

                            # ── Hover tooltip ─────────────────────────────────────────────────
                            TW, TH = 192, 80 # Made slightly shorter since no subject
                            tx = min(cx - TW/2, W - TW - 6)
                            tx = max(tx, PAD_L + 4)
                            ty = cy - r - TH - 14
                            if ty < PAD_T - 4:
                                ty = cy + r + 10

                            sc = SENT_COLOR[sent]
                            L.append(f'  <g class="bc-tip">')
                            L.append(f'    <rect x="{tx:.1f}" y="{ty:.1f}" width="{TW}" height="{TH}" rx="11" fill="#1a2236" stroke="{sc}" stroke-width="1.5" filter="url(#tshadow)"/>')
                            L.append(f'    <polygon points="{cx:.1f},{ty+TH+1} {cx-7:.1f},{ty+TH-7} {cx+7:.1f},{ty+TH-7}" fill="#1a2236" stroke="{sc}" stroke-width="1"/>')
                            L.append(f'    <polygon points="{cx:.1f},{ty+TH} {cx-6:.1f},{ty+TH-7} {cx+6:.1f},{ty+TH-7}" fill="#1a2236"/>')

                            L.append(f'    <text x="{tx+11}" y="{ty+18}" font-size="12" font-weight="800" fill="#f1f5f9" class="bc">{word.capitalize()}</text>')
                            L.append(f'    <line x1="{tx+9}" y1="{ty+27}" x2="{tx+TW-9}" y2="{ty+27}" stroke="#2d3f66" stroke-width="1"/>')
                            L.append(f'    <text x="{tx+11}" y="{ty+43}" font-size="10" fill="#94a3b8" class="bc">Mentioned <tspan fill="{sc}" font-weight="800">{total}×</tspan></text>')
                            L.append(f'    <text x="{tx+11}" y="{ty+59}" font-size="10" fill="#94a3b8" class="bc">😊 {pos}  😐 {neu}  😞 {neg}</text>')
                            L.append(f'  </g>')
                            L.append('</g>')  # bubble group

                    L.append('</svg>')
                    return "".join(L).replace("\n", "")

                # ─────────────────────────────────────────────────────────────────────────────
                # MAIN RENDERER
                # ─────────────────────────────────────────────────────────────────────────────

                def render_word_insights(df_sent, sent_col, q_text_to_id, form_schema, form_schema_full):
                    # ── CSS ────────────────────────────────────────────────────────────────────
                    st.markdown("""
                    <style>
                    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&display=swap');
                    .wi { font-family:'DM Sans','Mulish',sans-serif; }

                    .wi-legend {
                        display:flex; gap:1.3rem; flex-wrap:wrap; align-items:center;
                        background:#0d1526; border:1px solid #1e2f4a; border-radius:10px;
                        padding:.65rem 1.1rem; margin:.5rem 0 1rem; font-size:.78rem;
                    }
                    .wi-legend-lbl { font-size:.68rem; font-weight:700; color:#4a6fa5;
                                    text-transform:uppercase; letter-spacing:.08em; }
                    .wi-li { display:flex; align-items:center; gap:.4rem; font-weight:600; color:#94a3b8; }
                    .wi-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }

                    /* chip panel */
                    .wi-dim-hdr {
                        display:flex; align-items:center; gap:.5rem;
                        padding:.6rem .9rem; font-weight:800; font-size:.75rem;
                        border-radius:10px 10px 0 0; border-bottom:2px solid;
                        text-transform:uppercase; letter-spacing:.07em;
                    }
                    .wi-chip-area { padding:.65rem .65rem .65rem; display:flex; flex-direction:column; gap:.38rem; }

                    .wi-panel {
                        background:#fff; border:2px solid #e0e7ff; border-radius:14px;
                        padding:1.2rem 1.4rem; margin-top:1rem;
                        box-shadow:0 4px 20px rgba(26,50,99,.09);
                        animation:wi-slide .22s ease;
                    }
                    @keyframes wi-slide{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
                    .wi-ptitle { font-size:.98rem; font-weight:800; color:#1e293b; margin-bottom:.22rem; }
                    .wi-psub   { font-size:.76rem; color:#64748b; margin-bottom:.85rem; }

                    .wi-quote {
                        background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px;
                        padding:.78rem .95rem; margin-bottom:.5rem; border-left:4px solid;
                    }
                    .wi-qtxt  { font-size:.87rem; color:#1e293b; line-height:1.65; margin-bottom:.42rem; }
                    .wi-qmeta { font-size:.68rem; color:#94a3b8; display:flex; gap:.85rem; flex-wrap:wrap; }
                    .wi-sbadge{
                        display:inline-flex;align-items:center;gap:.3rem;
                        font-size:.65rem;font-weight:700;padding:.1rem .48rem;border-radius:999px;
                    }

                    .wi-statbar {
                        display:flex; gap:1.8rem; flex-wrap:wrap; margin-top:.85rem;
                        padding:.6rem .9rem; background:#f8fafc;
                        border-radius:10px; border:1px solid #e2e8f0;
                        font-size:.76rem; color:#64748b;
                    }

                    @media(max-width:680px){
                        .wi-legend { gap:.7rem; }
                    }
                    </style>
                    """, unsafe_allow_html=True)

                    # ── Section header ─────────────────────────────────────────────────────────
                    st.markdown("""
                    <div class="section-head wi" style="margin-top:1.4rem;">
                        📊 Frequently Used Words
                    </div>
                    <p class="wi" style="font-size:.82rem;color:#64748b;margin:-.15rem 0 .5rem;">
                        Words commuters use most, grouped by SERVQUAL dimension.
                        <strong>Hover</strong> a bubble for a quick summary.
                        <strong>Click</strong> a word chip below to read the exact quotes.
                    </p>
                    """, unsafe_allow_html=True)

                    # ── Data ───────────────────────────────────────────────────────────────────
                    # Get excluded words from form_meta
                    excluded_words = []
                    try:
                        meta_res = conn.client.table("form_meta").select("excluded_bubble_words").eq("form_id", current_form_id).eq("admin_email", admin_email).limit(1).execute()
                        if meta_res.data:
                            excluded_words = meta_res.data[0].get("excluded_bubble_words", [])
                    except:
                        pass
                    
                    dimension_insights, bubble_resp_map = extract_word_insights(
                        df_sent, sent_col, q_text_to_id, form_schema, form_schema_full, excluded_words
                    )

                    if not dimension_insights:
                        st.markdown("""<div class="empty-tab">
                            <div class="icon">💬</div>
                            <p>No word patterns found yet.<br>Minimum 2 mentions per word required.</p>
                        </div>""", unsafe_allow_html=True)
                        return

                    active_dims = [dim for dim in DIMENSION_ORDER if dim in dimension_insights and len(dimension_insights[dim]) > 0]

                    # If no dimensions have enough words, stop rendering the chart
                    if not active_dims:
                        st.markdown("""<div class="empty-tab">
                            <div class="icon">💬</div>
                            <p>No word patterns found yet.<br>Minimum 2 mentions per word required.</p>
                        </div>""", unsafe_allow_html=True)
                        return
                    # ══════════════════════════════════════════════════════════════════════════
                    # PART 1 — SVG BUBBLE CHART
                    # ══════════════════════════════════════════════════════════════════════════
                    st.markdown("""
                    <div class="wi-legend wi">
                        <span class="wi-legend-lbl">Reading guide:</span>
                        <div class="wi-li">
                            <div class="wi-dot" style="background:#4ade80;box-shadow:0 0 6px #4ade8077;"></div>
                            Overall Positive
                        </div>
                        <div class="wi-li">
                            <div class="wi-dot" style="background:#f87171;box-shadow:0 0 6px #f8717177;"></div>
                            Overall Negative
                        </div>
                        <div class="wi-li">
                            <div class="wi-dot" style="background:#94a3b8;"></div>Overall Neutral
                        </div>
                        <div class="wi-li" style="border-left:1px solid #1e2f4a;padding-left:1.2rem;">
                            📏 Higher and Bigger = mentioned more often
                        </div>
                        <div class="wi-li">🔢 Badge = exact count</div>
                        <div class="wi-li">🖱️ Hover for breakdown</div>
                    </div>
                    """, unsafe_allow_html=True)

                    svg = build_svg_bubble_chart(dimension_insights)
                    st.markdown(f"<div>{svg}</div>", unsafe_allow_html=True)

                    # ══════════════════════════════════════════════════════════════════════════
                    # PART 2 — INTERACTIVE WORD CHIPS
                    # ══════════════════════════════════════════════════════════════════════════
                    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
                    st.markdown("""
                    <div class="section-head wi" style="margin-top:.5rem;">
                        🔍 Click a Word to Read Respondent Quotes
                    </div>
                    <p class="wi" style="font-size:.82rem;color:#64748b;margin:-.15rem 0 .8rem;">
                        Each pill is a word + the aspect it describes.
                        Tap one to expand the exact feedback behind it.
                    </p>
                    """, unsafe_allow_html=True)

                    if "wi_selected_bubble" not in st.session_state:
                        st.session_state.wi_selected_bubble = None

                    cols = st.columns(len(active_dims), gap="small")

                    for ci, dim in enumerate(active_dims):
                        theme   = DIM_THEME[dim]
                        bubbles = dimension_insights[dim]
                        with cols[ci]:
                            st.markdown(f"""
                            <div class="wi wi-dim-hdr"
                                style="background:{theme['bg']};color:{theme['dark']};
                                        border-color:{theme['accent']};">
                                {theme['icon']} {dim}
                            </div>""", unsafe_allow_html=True)

                            # ... (sa loob ng render_word_insights, after st.markdown ng Click a Word header)
                            for b in bubbles:
                                bk   = b["bubble_key"]
                                sent = b["sentiment"]
                                word = b["word"].capitalize()
                                cnt  = b["total"]
                                em   = SENT_EMOJI[sent]
                                is_s = st.session_state.wi_selected_bubble == bk

                                clicked = st.button(
                                    f"{em} **{word}** &nbsp;`{cnt}×`", # Tinanggal yung subject arrow
                                    key=f"wi_btn_{bk}",
                                    use_container_width=True,
                                    help=f"{cnt} mention(s) · {sent} · Click to read quotes",
                                )
# (Ito yung dulo nung loop para sa buttons)
                                if clicked:
                                    st.session_state.wi_selected_bubble = None if is_s else bk
                                    st.rerun()

                    # ══════════════════════════════════════════════════════════════════════════
                    # 👇 PANSININ ANG SPACING DITO: Naka-align na dapat 'to pabalik sa kaliwa
                    # ══════════════════════════════════════════════════════════════════════════
                    
                    # ── Quote panel ────────────────────────────────────────────────────────────
                    sel = st.session_state.wi_selected_bubble
                    if sel and sel in bubble_resp_map:
                        parts    = sel.split("|")
                        sel_word = parts[0].capitalize() 
                        sel_dim  = parts[1] if len(parts) > 1 else ""
                        resps    = bubble_resp_map[sel]
                        theme    = DIM_THEME.get(sel_dim, {"accent":"#6366f1","bg":"#eef2ff","dark":"#4f46e5","icon":"💬"})

                        sc = {"POSITIVE":0,"NEGATIVE":0,"NEUTRAL":0}
                        for r in resps:
                            s = r.get("Sentiment","NEUTRAL").upper()
                            if s in sc: sc[s] += 1

                        # NET SENTIMENT SCORE LOGIC PARA SA QUOTE PANEL
                        total_quotes = sc["POSITIVE"] + sc["NEGATIVE"] + sc["NEUTRAL"]
                        if total_quotes > 0:
                            net_score_quotes = ((sc["POSITIVE"] - sc["NEGATIVE"]) / total_quotes) * 100
                            if net_score_quotes > 50:
                                dom_cap = "Positive"
                            elif net_score_quotes < -50:
                                dom_cap = "Negative"
                            else:
                                dom_cap = "Neutral"
                        else:
                            dom_cap = "Neutral"

                        st.markdown(f"""
                        <div class="wi-panel wi">
                            <div class="wi-ptitle">
                                {theme['icon']} Word: "{sel_word}"
                                &nbsp;<span style="background:{theme['bg']};color:{theme['dark']};
                                            padding:.08rem .52rem;border-radius:999px;font-size:.7rem;
                                            font-weight:800;border:1px solid {theme['accent']}44;">{sel_dim}</span>
                                &nbsp;<span style="background:{SENT_BG[dom_cap]};color:{SENT_DARK[dom_cap]};
                                            padding:.08rem .52rem;border-radius:999px;font-size:.7rem;
                                            font-weight:800;">{SENT_EMOJI[dom_cap]} {dom_cap} overall</span>
                            </div>
                            <div class="wi-psub">
                                {len(resps)} quote{"s" if len(resps)!=1 else ""} —
                                😊 {sc["POSITIVE"]} pos &nbsp;·&nbsp;
                                😐 {sc["NEUTRAL"]} neu &nbsp;·&nbsp;
                                😞 {sc["NEGATIVE"]} neg
                            </div>
                        """, unsafe_allow_html=True)

                        for resp in resps[:15]:
                            raw_s    = resp.get("Sentiment","NEUTRAL").upper()
                            sent_cap = raw_s.capitalize() if raw_s.lower() in ("positive","negative","neutral") else "Neutral"
                            sc2      = SENT_DARK[sent_cap]
                            sb       = SENT_BG[sent_cap]
                            se       = SENT_EMOJI[sent_cap]
                            ans      = resp.get("Answer","")
                            q        = resp.get("Question","")
                            conf     = resp.get("Confidence","N/A")
                            sub      = resp.get("Submitted","")

                            # I-highlight yung nahanap na word
                            hi = re.sub(
                                rf'\b({re.escape(sel_word.lower())})\b',
                                r'<mark style="background:#fef9c3;border-radius:3px;padding:0 2px;">\1</mark>',
                                ans, flags=re.IGNORECASE
                            )

                            st.markdown(f"""
                            <div class="wi-quote" style="border-left-color:{sc2};">
                                <div class="wi-qtxt">"{hi}"</div>
                                <div class="wi-qmeta">
                                    <span class="wi-sbadge" style="background:{sb};color:{sc2};">{se} {sent_cap}</span>
                                    <span>📊 {conf} confidence</span>
                                    <span>🕒 {sub}</span>
                                </div>
                                <div class="wi-qmeta" style="margin-top:.3rem;padding-top:.28rem;border-top:1px solid #f1f5f9;">
                                    <span><strong>Q:</strong> {q[:130]}{"…" if len(q)>130 else ""}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)
                        if len(resps) > 15:
                            st.caption(f"Showing 15 of {len(resps)} quotes.")

                        if st.button("✖ Close quotes", key=f"wi_close_{sel}"):
                            st.session_state.wi_selected_bubble = None
                            st.rerun()

                    # ── Stats footer ───────────────────────────────────────────────────────────
                    tp = sum(len(v) for v in dimension_insights.values())
                    tm = sum(b["total"] for v in dimension_insights.values() for b in v)
                    st.markdown(f"""
                    <div class="wi-statbar wi">
                        <span>📊 <strong>{tp}</strong> word patterns found</span>
                        <span>🔢 <strong>{tm}</strong> total mentions analysed</span>
                        <span>📐 Words with ≥ 2 mentions shown</span>
                    </div>
                    """, unsafe_allow_html=True)

                # ══════════════════════════════════════════════════════════════════════════
                # 👇 PANSININ ANG SPACING DITO: Naka-align dapat ito sa "def render_word_insights"
                # ══════════════════════════════════════════════════════════════════════════
                render_word_insights(df_sent, sent_col, q_text_to_id, form_schema, form_schema_full)

    # ─────────────────────────────────
    # TAB 3 — Database
    # ─────────────────────────────────
    with tab3:
        with st.expander("👥 Demographics", expanded=True):
            st.markdown("""
            <div style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                        border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;">
            <div style="font-size:.72rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem;">Demographics Guide</div>
            <div style="font-size:.8rem;color:rgb(60,100,130);line-height:1.6;">
                Data comes from the <strong>respondent profile</strong> block and questions marked as <strong>demographic</strong> in Form Builder.
            </div>
            </div>
            """, unsafe_allow_html=True)

            if "demo_answers" not in df.columns or df["demo_answers"].isna().all():
                st.markdown("""<div class="empty-tab"><div class="icon">👥</div>
                <p>No demographic data available.<br>
                Mark questions as <strong>demographic</strong> in Form Builder.</p>
                </div>""", unsafe_allow_html=True)
            else:
                demo_df = pd.json_normalize(df["demo_answers"].dropna().tolist())
                if demo_df.empty:
                    st.markdown("""<div class="empty-tab"><div class="icon">👥</div>
                    <p>No demographic data available.</p>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown('<div class="section-head">📊 Choose Visualization Type</div>', unsafe_allow_html=True)
                    chart_type = st.radio(
                        "Select how to view demographic data:",
                        options=["donut", "bar", "stacked", "table"],
                        format_func=lambda x: {"donut": "🍩 Donut Charts", "bar": "📊 Horizontal Bar Chart",
                                                "stacked": "📈 Stacked Bar Chart", "table": "📋 Table with Counts"}[x],
                        horizontal=True, key="demo_chart_type"
                    )
                    st.markdown("---")

                    custom_demographic_all = set()
                    if "custom_demographic_questions" in df.columns:
                        for custom_list in df["custom_demographic_questions"].dropna():
                            if isinstance(custom_list, list):
                                custom_demographic_all.update(custom_list)

                    demo_specs = _demo_chart_specs_all(demo_df, list(custom_demographic_all))

                    if not demo_specs:
                        st.dataframe(demo_df, use_container_width=True, hide_index=True)
                    else:
                        if chart_type == "donut":
                            pairs = [(demo_specs[i], demo_specs[i+1] if i+1 < len(demo_specs) else None)
                                     for i in range(0, len(demo_specs), 2)]
                            for spec_l, spec_r in pairs:
                                cl, cr = st.columns(2)
                                for col_w, spec in [(cl, spec_l), (cr, spec_r)]:
                                    if spec is None:
                                        continue
                                    q, label = spec[0], spec[1]
                                    with col_w:
                                        vc = _explode_demo_series(demo_df[q]).value_counts().reset_index()
                                        vc.columns = ["Value", "Count"]
                                        st.altair_chart(
                                            alt.Chart(vc).mark_arc(innerRadius=40).encode(
                                                theta="Count:Q",
                                                color=alt.Color("Value:N", scale=alt.Scale(scheme="blues"),
                                                                legend=alt.Legend(orient="bottom", labelFontSize=10)),
                                                tooltip=["Value:N", "Count:Q"],
                                            ).properties(title=label, height=200),
                                            use_container_width=True,
                                        )
                        elif chart_type == "bar":
                            for q, label in demo_specs:
                                vc = _explode_demo_series(demo_df[q]).value_counts().reset_index()
                                vc.columns = ["Value", "Count"]
                                st.altair_chart(
                                    alt.Chart(vc).mark_bar(color="#1a3263").encode(
                                        y=alt.Y("Value:N", sort="-x", title=None),
                                        x=alt.X("Count:Q", title="Number of Responses"),
                                        tooltip=["Value:N", "Count:Q"],
                                    ).properties(title=label, height=max(200, len(vc) * 30)),
                                    use_container_width=True,
                                )
                        elif chart_type == "stacked":
                            if len(demo_specs) >= 2:
                                primary_q, primary_label = demo_specs[0]
                                for q, label in demo_specs[1:]:
                                    primary_series = _explode_demo_series(demo_df[primary_q])
                                    secondary_series = _explode_demo_series(demo_df[q])
                                    combined_data = [
                                        {"Primary": str(p), "Secondary": str(secondary_series.iloc[i])}
                                        for i, p in enumerate(primary_series) if i < len(secondary_series)
                                    ]
                                    if combined_data:
                                        combined_df = pd.DataFrame(combined_data)
                                        grouped = combined_df.groupby(["Primary", "Secondary"]).size().reset_index(name="Count")
                                        st.altair_chart(
                                            alt.Chart(grouped).mark_bar().encode(
                                                x=alt.X("Primary:N", title=primary_label),
                                                y=alt.Y("Count:Q"),
                                                color=alt.Color("Secondary:N", title=label, scale=alt.Scale(scheme="blues")),
                                                tooltip=["Primary:N", "Secondary:N", "Count:Q"],
                                            ).properties(title=f"{label} by {primary_label}", height=250),
                                            use_container_width=True,
                                        )
                            else:
                                st.info("Stacked bar chart requires at least 2 demographic questions.")
                        elif chart_type == "table":
                            for q, label in demo_specs:
                                vc = _explode_demo_series(demo_df[q]).value_counts().reset_index()
                                vc.columns = ["Value", "Count"]
                                vc["Percentage"] = (vc["Count"] / vc["Count"].sum() * 100).round(1)
                                st.markdown(f"**{label}**")
                                st.dataframe(vc.sort_values("Count", ascending=False).reset_index(drop=True),
                                             use_container_width=True, hide_index=True)
                                st.markdown("---")

        with st.expander("👤 Respondent Details", expanded=True):
            st.markdown("### 👤 Respondent Details")
            st.caption("View all responses. Each row is one respondent.")
            try:
                all_responses = (
                    conn.client.table("form_responses")
                    .select("*").eq("admin_email", admin_email).eq("form_id", current_form_id)
                    .order("created_at", desc=True).execute()
                )
                if not all_responses.data:
                    st.info("No responses yet for this form.")
                else:
                    q_query = (
                        conn.client.table("form_questions")
                        .select("id, prompt, q_type, is_demographic, servqual_dimension")
                        .eq("admin_email", admin_email).eq("form_id", current_form_id)
                        .order("sort_order").execute()
                    )
                    all_questions = q_query.data or []

                    STANDARD_DEMO_QUESTIONS = [
                        {"prompt": "1. Age / Edad", "q_type": "Multiple Choice", "is_required": True, "is_demographic": True},
                        {"prompt": "2. Gender / Kasarian", "q_type": "Multiple Choice", "is_required": True, "is_demographic": True},
                        {"prompt": "3. Occupational Status / Katayuan sa Trabaho", "q_type": "Multiple Choice", "is_required": True, "is_demographic": True},
                        {"prompt": "4. Monthly Allowance or Salary / Buwanang Sahod o Allowance", "q_type": "Multiple Choice", "is_required": True, "is_demographic": True},
                        {"prompt": "5. Frequency of Commuting / Gaano ka kadalas sumakay sa isang linggo?", "q_type": "Multiple Choice", "is_required": True, "is_demographic": True},
                        {"prompt": "6. Most frequently used transport mode / Pinakamadalas na sinasakyan", "q_type": "Multiple Choice", "is_required": True, "is_demographic": True},
                    ]

                    # Standard SERVQUAL questionnaire questions (matches exact prompts from public_form.py)
                    STANDARD_SERVQUAL_QUESTIONS = [
                        {"prompt": "How would you describe the physical condition, cleanliness, and overall seating comfort of the vehicle you rode recently? (Paano mo ilalarawan ang pisikal na kondisyon, kalinisan, at pangkalahatang komportableng pag-upo sa sasakyang sinakyan mo kamakailan lang?)", "q_type": "Paragraph", "is_demographic": False, "servqual_dimension": "Tangibles"},
                        {"prompt": "What can you say about the air ventilation, temperature, and general atmosphere inside the vehicle? (Ano ang masasabi mo sa bentilasyon ng hangin, temperatura, at pangkalahatang kapaligiran sa loob ng sasakyan?)", "q_type": "Paragraph", "is_demographic": False, "servqual_dimension": "Tangibles"},
                        {"prompt": "How would you describe the overall reliability and operation of the vehicle during your entire trip? (Paano mo ilalarawan ang pangkalahatang pagiging maaasahan at maayos na takbo ng sasakyan sa buong biyahe mo?)", "q_type": "Paragraph", "is_demographic": False, "servqual_dimension": "Reliability"},
                        {"prompt": "What are your thoughts on the affordability of the fare and how your payment and change were handled by the driver/conductor? (Ano ang iyong pananaw sa halaga ng pamasahe at kung paano inasikaso ng drayber/konduktor ang iyong ibinayad at sukli?)", "q_type": "Paragraph", "is_demographic": False, "servqual_dimension": "Reliability"},
                        {"prompt": "How would you describe your experience regarding the travel time and the promptness of the ride in reaching your destination? (Paano mo ilalarawan ang iyong karanasan patungkol sa tagal ng biyahe at ang pagiging maagap ng sasakyan patungo sa iyong destinasyon?)", "q_type": "Paragraph", "is_demographic": False, "servqual_dimension": "Responsiveness"},
                        {"prompt": "What can you say about the attentiveness of the driver or conductor when passengers needed to get off or communicate their drop-off points? (Ano ang masasabi mo sa pagiging alisto ng driver o konduktor kapag kailangan nang bumaba o makipag-usap ng mga pasahero para sa kanilang bababaan?)", "q_type": "Paragraph", "is_demographic": False, "servqual_dimension": "Responsiveness"},
                        {"prompt": "What are your thoughts on how the driver navigated the road and followed traffic rules during your trip? (Ano ang iyong pananaw sa kung paano nagmaneho at sumunod sa batas trapiko ang driver sa iyong biyahe?)", "q_type": "Paragraph", "is_demographic": False, "servqual_dimension": "Assurance"},
                        {"prompt": "How would you describe your overall sense of safety and security against incidents like theft or harassment while inside the vehicle? (Paano mo ilalarawan ang iyong pangkalahatang pakiramdam ng kaligtasan at seguridad laban sa mga insidente tulad ng pagnanakaw o harassment habang nasa loob ng sasakyan?)", "q_type": "Paragraph", "is_demographic": False, "servqual_dimension": "Assurance"},
                        {"prompt": "What can you say about the behavior, politeness, and overall treatment of passengers by the transport crew? (Ano ang masasabi mo sa pag-uugali, pagiging magalang, at pangkalahatang pagtrato ng mga tauhan sa mga pasahero?)", "q_type": "Paragraph", "is_demographic": False, "servqual_dimension": "Empathy"},
                        {"prompt": "What are your thoughts on the transport crew's attentiveness and care for passengers who might need extra assistance, such as Senior Citizens, PWDs, or pregnant woman? (Ano ang pananaw mo sa pagiging maasikaso at pag-aalaga ng mga tauhan sa mga pasaherong maaaring mangailangan ng karagdagang tulong, tulad ng Senior Citizens, PWDs, o mga buntis?)", "q_type": "Paragraph", "is_demographic": False, "servqual_dimension": "Empathy"},
                        {"prompt": "Additional Comments or Suggestions / Karagdagang Komento o Mungkahi", "q_type": "Paragraph", "is_demographic": False, "servqual_dimension": None},
                    ]

                    existing_prompts = {q.get("prompt") for q in all_questions}
                    for std_q in STANDARD_DEMO_QUESTIONS:
                        if std_q.get("prompt") not in existing_prompts:
                            all_questions.append(std_q)
                            existing_prompts.add(std_q.get("prompt"))
                    
                    # Always add SERVQUAL questions to respondent detail view
                    for servqual_q in STANDARD_SERVQUAL_QUESTIONS:
                        if servqual_q.get("prompt") not in existing_prompts:
                            all_questions.append(servqual_q)
                            existing_prompts.add(servqual_q.get("prompt"))

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
                        row_t = {
                            "Respondent ID": str(response.get("id", ""))[:8],
                            "Submitted": response.get("created_at", "")[:10],
                            "Time": response.get("created_at", "")[11:19],
                        }
                        demo_ans_map = response.get("demo_answers", {})
                        if isinstance(demo_ans_map, dict):
                            for demo_q in demo_questions:
                                dp = demo_q.get("prompt", "")
                                da = demo_ans_map.get(dp, "")
                                if da is None:
                                    da = ""
                                elif isinstance(da, list):
                                    da = ", ".join(str(a) for a in da)
                                else:
                                    da = str(da)
                                row_t[f"👥 {dp}"] = da
                        ans_map = response.get("answers", {})
                        for q, answer_key in possible_answer_keys:
                            q_type = q.get("q_type", "")
                            answer = ans_map.get(answer_key, "")
                            if answer is None:
                                answer = ""
                            elif isinstance(answer, list):
                                answer = ", ".join(str(a) for a in answer)
                            else:
                                answer = str(answer)
                            col_name = f"{q.get('prompt', '')} [{q_type}]" if q_type in ("Multiple Choice", "Multiple Select") else q.get("prompt", "")
                            row_t[col_name] = answer
                        table_data.append(row_t)

                    df_responses = pd.DataFrame(table_data)
                    st.markdown(f"### Respondent Responses Table ({len(all_responses.data)} total)")

                    rc1, rc2 = st.columns(2)
                    with rc1:
                        search_text = st.text_input("🔍 Search responses", placeholder="Type to search all columns...", key="respondent_search")
                    with rc2:
                        if "Submitted" in df_responses.columns:
                            min_d = pd.to_datetime(df_responses["Submitted"]).min().date()
                            max_d = pd.to_datetime(df_responses["Submitted"]).max().date()
                            date_range = st.date_input("📅 Filter by date", value=(min_d, max_d), key="respondent_date_range")
                            if isinstance(date_range, tuple) and len(date_range) == 2:
                                df_resp_f = df_responses[(pd.to_datetime(df_responses["Submitted"]).dt.date >= date_range[0]) &
                                                         (pd.to_datetime(df_responses["Submitted"]).dt.date <= date_range[1])]
                            else:
                                df_resp_f = df_responses
                        else:
                            df_resp_f = df_responses

                    if search_text:
                        mask = df_resp_f.astype(str).apply(lambda x: x.str.contains(search_text, case=False, na=False).any(), axis=1)
                        df_resp_f = df_resp_f[mask]

                    st.markdown(f"**Showing {len(df_resp_f)} of {len(df_responses)} responses**")
                    
                    demo_cols_r = [c for c in df_resp_f.columns if c.startswith("👥 ")]
                    other_cols_r = [c for c in df_resp_f.columns if not c.startswith("👥 ") and c not in ("Respondent ID", "Submitted", "Time")]
                    
                    # Filter columns to only show those with at least one non-empty value
                    cols_with_data = ["Respondent ID", "Submitted", "Time"]
                    for col in demo_cols_r + other_cols_r:
                        if df_resp_f[col].astype(str).str.strip().ne("").any():
                            cols_with_data.append(col)
                    
                    col_order_r = [c for c in cols_with_data if c in df_resp_f.columns]
                    st.dataframe(df_resp_f[col_order_r], use_container_width=True, hide_index=True,
                                 height=min(600, 80 + 36 * max(1, len(df_resp_f))))
                    csv_data = df_resp_f[col_order_r].to_csv(index=False)
                    st.download_button(
                        "📥 Download as CSV", data=csv_data,
                        file_name=f"respondents_{current_form_id}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )
                    
                    # Add respondent selection to view detailed responses (shown AFTER table)
                    st.markdown("---")
                    col_select, col_blank = st.columns([2, 3])
                    with col_select:
                        respondent_options = df_resp_f["Respondent ID"].tolist()
                        if respondent_options:
                            selected_respondent = st.selectbox(
                                "📋 View full details for respondent:",
                                options=respondent_options,
                                key="respondent_select",
                                index=None,
                                placeholder="Select a respondent ID from table above..."
                            )
                            
                            if selected_respondent:
                                # Find the full response data for this respondent
                                selected_resp_data = next((r for r in all_responses.data if str(r.get("id", ""))[:8] == selected_respondent), None)
                                if selected_resp_data:
                                    st.markdown(f"### 📝 Detailed Response - Respondent {selected_respondent}")
                                    st.markdown(f"**Submitted:** {selected_resp_data.get('created_at', '')}")
                                    
                                    # Display demographics if available
                                    demo_ans = selected_resp_data.get("demo_answers", {})
                                    if isinstance(demo_ans, dict) and demo_ans:
                                        with st.expander("👥 Demographics", expanded=True):
                                            for q_prompt, answer in demo_ans.items():
                                                if isinstance(answer, list):
                                                    answer_str = ", ".join(str(a) for a in answer)
                                                else:
                                                    answer_str = str(answer) if answer else "—"
                                                st.markdown(f"**{q_prompt}**  \n{answer_str}")
                                    
                                    # Display all answers to questions (only those with responses)
                                    answers = selected_resp_data.get("answers", {})
                                    answered_questions = {k: v for k, v in answers.items() if v}
                                    if isinstance(answers, dict) and answered_questions:
                                        with st.expander("❓ Responses to Questions", expanded=True):
                                            for q_prompt, answer in answered_questions.items():
                                                if isinstance(answer, list):
                                                    answer_str = ", ".join(str(a) for a in answer)
                                                else:
                                                    answer_str = str(answer) if answer else "—"
                                                st.markdown(f"**{q_prompt}**  \n{answer_str}")
                                                st.divider()
            except Exception as e:
                st.error(f"Error loading respondent data: {str(e)}")

        with st.expander("📊 Multiple Choice & Multiple Select Responses", expanded=True):
            st.markdown("### 📊 Multiple Choice & Multiple Select Responses")
            st.caption("Bar charts showing answer counts for each multiple choice/select question.")
            try:
                mc_questions = [q for q in all_questions if q.get("q_type") in ("Multiple Choice", "Multiple Select")
                                and not _is_demographic_question(q.get("prompt", ""))]
                if not mc_questions:
                    st.info("No multiple choice or multiple select questions in this form.")
                else:
                    seen_mc = {}
                    for q in mc_questions:
                        q_prompt = q.get("prompt", "Unknown")
                        q_type = q.get("q_type", "")
                        if q_prompt not in seen_mc:
                            seen_mc[q_prompt] = 0
                            unique_key = q_prompt
                        else:
                            seen_mc[q_prompt] += 1
                            unique_key = f"{q_prompt} ({seen_mc[q_prompt]})"
                        answers = []
                        for response in all_responses.data:
                            ans = response.get("answers", {}).get(unique_key)
                            if ans:
                                if isinstance(ans, list):
                                    answers.extend([str(a).strip() for a in ans if a])
                                elif isinstance(ans, str) and ',' in ans:
                                    answers.extend([a.strip() for a in ans.split(',') if a.strip()])
                                elif ans:
                                    answers.append(str(ans).strip())
                        if answers:
                            ac = pd.Series(answers).value_counts().reset_index()
                            ac.columns = ["Answer", "Count"]
                            max_c = ac["Count"].max()
                            st.altair_chart(
                                alt.Chart(ac).mark_bar(color="#1a3263").encode(
                                    x=alt.X("Count:Q", axis=alt.Axis(format="d", tickMinStep=1),
                                            scale=alt.Scale(domain=[0, max(max_c, 1)], nice=False)),
                                    y=alt.Y("Answer:N", sort="-x"),
                                    tooltip=["Answer:N", "Count:Q"],
                                ).properties(title=f"{q_prompt} [{q_type}]", height=200 + max(0, (len(ac)-5)*20)),
                                use_container_width=True,
                            )
                        else:
                            st.info(f"No responses for: {q_prompt}")
            except Exception as e:
                st.error(f"Error loading multiple choice data: {str(e)}")

        with st.expander("📈 Response Trends", expanded=True):
            if "created_at" not in df.columns:
                st.markdown("""<div class="empty-tab"><div class="icon">📈</div>
                <p>Response trend chart requires timestamps.</p>
                </div>""", unsafe_allow_html=True)
            else:
                daily_responses = (
                    df.assign(date=df["created_at"].dt.date)
                    .groupby("date").size().reset_index(name="Responses")
                )
                if daily_responses.empty:
                    st.info("No responses to display for the selected filters.")
                else:
                    daily_responses["date"] = pd.to_datetime(daily_responses["date"])
                    daily_responses = daily_responses.sort_values("date")
                    min_d = daily_responses["date"].min()
                    max_d = daily_responses["date"].max()
                    if pd.notna(min_d) and pd.notna(max_d):
                        full_dates = pd.date_range(start=min_d, end=max_d, freq="D")
                        daily_responses = (daily_responses.set_index("date").reindex(full_dates, fill_value=0)
                                           .rename_axis("date").reset_index())
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
                    bar_c = alt.Chart(daily_responses).mark_bar(
                        cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#1a3263"
                    ).encode(
                        x=alt.X("date:T", axis=alt.Axis(format="%b %d", title="Date", labelAngle=-25)),
                        y=alt.Y("Responses:Q", axis=alt.Axis(format=".0f", tickMinStep=1),
                                scale=alt.Scale(domainMin=0, nice=True)),
                        tooltip=[alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
                                 alt.Tooltip("Responses:Q", format=",.0f")],
                    ).properties(height=320)
                    line_c = alt.Chart(daily_responses).mark_line(
                        color="#ffc570", strokeWidth=2.5, point=True
                    ).encode(
                        x="date:T", y="Responses:Q",
                        tooltip=[alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
                                 alt.Tooltip("Responses:Q", format=",.0f")],
                    )
                    st.altair_chart(bar_c + line_c, use_container_width=True)

    # ── EXPORT ──
    # ── EXPORT ──
    st.markdown("---")
    st.markdown('<div class="section-head">📥 Export Data</div>', unsafe_allow_html=True)
    ex1, ex2, ex3, _ = st.columns([2, 2, 2, 2])
    with ex1:
        # Export all responses with questions expanded into separate rows
        responses_expanded = []
        for _, response in df.iterrows():
            respondent_id = str(response.get("id", ""))[:8]
            submitted_date = response.get("created_at", "")
            
            # Add demographics
            demo_ans = response.get("demo_answers", {})
            if isinstance(demo_ans, dict):
                for demo_q, demo_ans_val in demo_ans.items():
                    if isinstance(demo_ans_val, list):
                        demo_ans_val = ", ".join(str(x) for x in demo_ans_val)
                    responses_expanded.append({
                        "Respondent ID": respondent_id,
                        "Submitted": submitted_date,
                        "Question Type": "Demographic",
                        "Question": demo_q,
                        "Answer": str(demo_ans_val) if demo_ans_val else "",
                    })
            
            # Add regular questions
            ans = response.get("answers", {})
            if isinstance(ans, dict):
                for question_key, answer_val in ans.items():
                    if isinstance(answer_val, list):
                        answer_val = ", ".join(str(x) for x in answer_val)
                    responses_expanded.append({
                        "Respondent ID": respondent_id,
                        "Submitted": submitted_date,
                        "Question Type": "Standard",
                        "Question": question_key,
                        "Answer": str(answer_val) if answer_val else "",
                    })
        
        if responses_expanded:
            df_expanded = pd.DataFrame(responses_expanded)
            st.download_button(
                "⬇ All Responses",
                data=df_expanded.to_csv(index=False).encode("utf-8"),
                file_name=f"land_public_transport_responses_{date_from}_{date_to}.csv",
                mime="text/csv", use_container_width=True,
            )
        else:
            st.download_button(
                "⬇ All Responses (CSV)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"land_public_transport_responses_{date_from}_{date_to}.csv",
                mime="text/csv", use_container_width=True,
            )
    with ex2:
        if not df_sent.empty and "raw_feedback" in df_sent.columns:
            # Build sentiment log with each question-answer pair on separate row
            sentiment_log_rows = []
            for _, row in df_sent.iterrows():
                created_date = row.get("created_at", "")
                response_sentiment = row.get(sent_col, "")
                response_score = row.get("sentiment_score", "")
                qs = row.get("question_sentiments", {})
                answers = row.get("answers", {})
                
                # Handle malformed data - if qs is a string, parse it
                if isinstance(qs, str):
                    try:
                        import json
                        qs = json.loads(qs) if qs.startswith('{') else {}
                    except:
                        qs = {}
                
                if isinstance(answers, str):
                    try:
                        import json
                        answers = json.loads(answers) if answers.startswith('{') else {}
                    except:
                        answers = {}
                
                # Expand to one row per question-answer pair
                if isinstance(qs, dict) and qs and isinstance(answers, dict) and answers:
                    for q_id, q_data in qs.items():
                        if isinstance(q_data, dict) and q_data.get("enable_sentiment") == True:
                            # Find the corresponding answer for this question
                            answer_text = answers.get(str(q_id), "") or answers.get(q_id, "")
                            
                            # Clean up answer if it's a list
                            if isinstance(answer_text, list):
                                answer_text = ", ".join(str(x) for x in answer_text)
                            else:
                                answer_text = str(answer_text)
                            
                            sentiment = q_data.get("sentiment", "")
                            # Clean up sentiment value
                            if isinstance(sentiment, str):
                                sentiment = sentiment.split("|")[0].strip()
                            
                            sentiment_log_rows.append({
                                "Question ID": str(q_id),
                                "Answer": answer_text,
                                "Sentiment": sentiment,
                                "Confidence": q_data.get("confidence", ""),
                                "Dimension": q_data.get("dimension", ""),
                                "Created At": created_date,
                            })
                else:
                    # No question sentiments enabled - show response-level only
                    if isinstance(answers, dict) and answers:
                        for q_id, answer_text in answers.items():
                            if isinstance(answer_text, list):
                                answer_text = ", ".join(str(x) for x in answer_text)
                            else:
                                answer_text = str(answer_text)
                            
                            sentiment_log_rows.append({
                                "Question ID": str(q_id),
                                "Answer": answer_text,
                                "Sentiment": response_sentiment,
                                "Confidence": response_score,
                                "Dimension": "",
                                "Created At": created_date,
                            })
            
            if sentiment_log_rows:
                df_sent_export = pd.DataFrame(sentiment_log_rows)
                st.download_button(
                    "⬇ Sentiment Log",
                    data=df_sent_export.to_csv(index=False).encode("utf-8"),
                    file_name=f"land_public_transport_sentiment_{date_from}_{date_to}.csv",
                    mime="text/csv", use_container_width=True,
                )
    with ex3:
        if has_any_rating_data:
            summary_rows_export = []
            for k, v in all_dim_cols.items():
                if v in df.columns and df[v].notna().any():
                    summary_rows_export.append({
                        "Dimension": k,
                        "Type": "SERVQUAL" if k != "General Ratings" else "General",
                        "Average": round(normalized_df[v].mean(), 4) if v in normalized_df.columns else None,
                        "Min": round(df[v].min(), 4),
                        "Max": round(df[v].max(), 4),
                        "Responses": int(df[v].notna().sum()),
                    })
            if summary_rows_export:
                st.download_button(
                    "⬇ SERVQUAL Summary (CSV)",
                    data=pd.DataFrame(summary_rows_export).to_csv(index=False).encode("utf-8"),
                    file_name=f"land_public_transport_servqual_summary_{date_from}_{date_to}.csv",
                    mime="text/csv", use_container_width=True,
                )


st.session_state.dashboard_initialized = True
render_dashboard()

# ══════════════════════════════════════════
# AUTO-REFRESH LOGIC (Live Dashboard)
# ══════════════════════════════════════════
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Auto-refresh every 5 seconds
current_time = time.time()
if current_time - st.session_state.last_refresh >= 5:
    st.session_state.last_refresh = current_time
    # Clear all caches to fetch fresh data
    fetch_dashboard_data.clear()
    fetch_question_scale_map.clear()
    fetch_form_questions_schema.clear()
    fetch_pending_sentiment_count.clear()
    fetch_pending_response_sentiment_rows.clear()
    fetch_pending_question_sentiment_rows.clear()
    st.rerun()
