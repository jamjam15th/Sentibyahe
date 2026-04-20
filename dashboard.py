import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import re
import json
import time
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
            model_path = "jamjam15th/land-public-transportation-model-2"
    else:
        model_path = "jamjam15th/land-public-transportation-model-2"
    
    return transformers.pipeline(
        "sentiment-analysis",
        model=model_path,
        tokenizer=model_path,
        top_k=None,
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
            label, score = analyze_text(raw)
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
                        label, score = analyze_text(text)
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
        "Physical condition of vehicles, terminal facilities, digital platforms (booking apps), and the overall commuting environment.",
        {
            "strong": "High scores here typically indicate that respondents appreciate visible physical or digital improvements.",
            "moderate": "Mixed scores suggest that conditions are acceptable but inconsistent.",
            "weak": "Negative sentiment often points to physical or digital deterioration.",
            "action_strong": "Review the specific Tangibles questions in the Quantitative tab to identify exactly which upgrades received the highest Likert ratings.",
            "action_moderate": "Check the Likert Response Log chart to separate the acceptable facilities from the lower-scoring ones.",
            "action_weak": "Prioritize a review of physical infrastructure. Look at the Quantitative breakdown to pinpoint lowest Likert scores.",
        }
    ),
    "Reliability": (
        "Consistency of routes, accuracy of app ETAs, ride availability during peak hours, and system dependability amid heavy traffic.",
        {
            "strong": "Positive scores suggest the transport system is generally meeting expectations.",
            "moderate": "Moderate scores indicate that service operates but is vulnerable.",
            "weak": "Low scores strongly suggest unpredictable service.",
            "action_strong": "Maintain current operational schedules. Check the Quantitative tab to see which specific reliability metrics contributed most.",
            "action_moderate": "Review the individual Likert scores for Reliability to spot specific bottlenecks.",
            "action_weak": "Treat system reliability as a critical issue. Check the bottom-performing questions in the Quantitative tab.",
        }
    ),
    "Responsiveness": (
        "Efficiency in managing terminal queues, swift action on commuter complaints, and agility of in-app customer support.",
        {
            "strong": "This indicates that respondents feel their immediate needs are being met.",
            "moderate": "Reactions to commuter needs occur, but may be perceived as slow.",
            "weak": "Negative sentiment usually reflects a perceived lack of urgency.",
            "action_strong": "Standardize the current queue management and support strategies.",
            "action_moderate": "Review the individual Likert scores to spot specific service gaps.",
            "action_weak": "Address queue management and customer support immediately.",
        }
    ),
    "Assurance": (
        "Road safety, driver competence, verified app profiles, strict compliance with fare matrices, and overall public trust.",
        {
            "strong": "High scores point to strong public trust.",
            "moderate": "General trust exists, but specific concerns may be dragging the score down.",
            "weak": "Low scores indicate a breakdown in trust and safety.",
            "action_strong": "Leverage this high trust factor. Review the Likert breakdown to confirm what contributed most.",
            "action_moderate": "Investigate the specific Assurance questions dragging the average down.",
            "action_weak": "Safety and fare compliance audits are urgently needed.",
        }
    ),
    "Empathy": (
        "Consideration for commuter struggles, proper implementation of discounts, polite communication, and humane policies.",
        {
            "strong": "Positive sentiment suggests that respondents feel considered and respected.",
            "moderate": "Basic courtesy is observed, but consistent empathy may be lacking.",
            "weak": "Negative scores typically mean respondents feel financially or personally disregarded.",
            "action_strong": "Acknowledge and sustain the practices driving this score.",
            "action_moderate": "Look at the individual Empathy Likert scores to see where the disconnect lies.",
            "action_weak": "Review the lowest-scoring Empathy questions in the Quantitative tab.",
        }
    ),
}

sentiment_dimension_descriptions = {
    "Tangibles": (
        "Physical condition of vehicles, terminal facilities, digital platforms (booking apps), and the overall commuting environment.",
        {
            "strong": "High Net Sentiment indicates respondents are explicitly writing praise about visible physical or digital improvements.",
            "moderate": "Mixed sentiment suggests conditions are acceptable but inconsistent.",
            "neutral": "Balanced feedback indicates physical conditions are meeting expectations on average.",
            "weak": "Negative Net Sentiment points to physical or digital deterioration.",
            "action_strong": "Review the positive feedback in the Sentiment Tab to identify exactly which upgrades are driving the praise.",
            "action_moderate": "Check the Sentiment Feedback Log to separate the acceptable facilities from the problematic ones.",
            "action_neutral": "Monitor physical conditions and facilities. Maintain current standards.",
            "action_weak": "Read the raw negative comments in the Sentiment Tab to pinpoint main pain points.",
        }
    ),
    "Reliability": (
        "Consistency of routes, accuracy of app ETAs, ride availability during peak hours, and system dependability amid heavy traffic.",
        {
            "strong": "Positive sentiment suggests the transport system is meeting expectations.",
            "moderate": "Moderate scores indicate service operates but is vulnerable.",
            "neutral": "Balanced feedback indicates service reliability is stable.",
            "weak": "Low Net Sentiment strongly suggests unpredictable service.",
            "action_strong": "Maintain current schedules. Read the positive Sentiment Log.",
            "action_moderate": "Look into neutral and negative comments to identify specific delay sources.",
            "action_neutral": "Keep monitoring service schedules and track patterns in feedback.",
            "action_weak": "Treat system reliability as a critical issue. Analyze written complaints.",
        }
    ),
    "Responsiveness": (
        "Efficiency in managing terminal queues, swift action on commuter complaints, and agility of in-app customer support.",
        {
            "strong": "Commuters feel their immediate needs are being met.",
            "moderate": "Reactions to commuter needs occur, but the text feedback shows the system still struggles during peak hours.",
            "neutral": "Balanced feedback indicates the system responds adequately overall.",
            "weak": "Negative sentiment usually reflects a perceived lack of urgency.",
            "action_strong": "Identify the terminals or app features receiving positive written feedback and standardize those strategies.",
            "action_moderate": "Review neutral/negative text feedback for specific bottlenecks.",
            "action_neutral": "Continue current response practices. Seek opportunities to optimize.",
            "action_weak": "Address queue management immediately. Raw text feedback will reveal where commuters feel most abandoned.",
        }
    ),
    "Assurance": (
        "Road safety, driver competence, verified app profiles, strict compliance with fare matrices, and overall public trust.",
        {
            "strong": "High Net Sentiment points to strong public trust.",
            "moderate": "General trust exists, but written feedback shows specific concerns.",
            "neutral": "Balanced feedback indicates commuters feel generally safe and trust the system.",
            "weak": "Low scores indicate a breakdown in trust.",
            "action_strong": "Leverage this high trust factor. Maintain strict safety checks.",
            "action_moderate": "Investigate text feedback to find the specific source of doubt.",
            "action_neutral": "Maintain current safety standards and fare compliance.",
            "action_weak": "Safety and fare audits are urgently needed. Read the raw comments.",
        }
    ),
    "Empathy": (
        "Consideration for commuter struggles, proper implementation of discounts, polite communication, and humane policies.",
        {
            "strong": "Positive sentiment suggests commuters feel respected.",
            "moderate": "Basic courtesy is observed, but consistent empathy is lacking.",
            "neutral": "Balanced feedback indicates commuters are experiencing adequate courtesy.",
            "weak": "Negative scores mean commuters feel disregarded.",
            "action_strong": "Acknowledge and sustain practices driving this score based on positive comments.",
            "action_moderate": "Read the feedback to see where the disconnect lies.",
            "action_neutral": "Continue training staff on courtesy and discount protocols.",
            "action_weak": "Review raw feedback closely for complaints about staff hostility or denied discounts.",
        }
    ),
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
            net_scores[dim] = ((counts["positive"] - counts["negative"]) / t * 100) if t > 0 else 0
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
            sentiment_display = f"{avg_sentiment:+.1f}%"
            sentiment_subtext = "Avg sentiment across dimensions"
            sentiment_color = '#4a7c59' if avg_sentiment > 0 else '#b03a2e' if avg_sentiment < 0 else '#8b9dc3'
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
                (untagged_sentiment_data["positive"] - untagged_sentiment_data["negative"]) / untagged_total * 100
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
                        x=alt.X("Net Sentiment Score:Q", scale=alt.Scale(domain=[-100, 100]),
                                axis=alt.Axis(title="Net Sentiment Score (%)")),
                        y=alt.Y("Dimension:N", sort=["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy", "Untagged"]),
                        color=alt.Color("Dimension:N",
                                        scale=alt.Scale(domain=list(dim_colors.keys()), range=list(dim_colors.values())),
                                        legend=None),
                        tooltip=["Dimension", alt.Tooltip("Net Sentiment Score:Q", format=".1f"), "Total Responses"],
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
                            sc = "#4a7c59" if net > 0 else "#b03a2e" if net < 0 else "#8b9dc3"
                            st.markdown(f"""
                            <div style="margin-bottom:1rem;padding:.75rem;border:1px solid rgba(26,50,99,0.12);border-radius:8px;background:rgba(26,50,99,0.03);">
                            <div style="font-weight:700;color:rgb(26,50,99);margin-bottom:.35rem;">{dim}</div>
                            <div style="font-size:.75rem;color:rgb(84,119,146);margin-bottom:.35rem;">😊 {pos} · 😐 {neu} · 😞 {neg}</div>
                            <div style="font-size:.9rem;font-weight:700;color:{sc};">Net: {net:+.1f}%</div>
                            </div>""", unsafe_allow_html=True)

                    if untagged_total > 0:
                        st.markdown(f"""
                        <div style="margin-bottom:1rem;padding:.75rem;border:1px solid rgba(26,50,99,0.12);border-radius:8px;background:rgba(150,150,150,0.03);">
                        <div style="font-weight:700;color:rgb(100,100,100);margin-bottom:.35rem;">Untagged</div>
                        <div style="font-size:.75rem;color:rgb(120,120,120);margin-bottom:.35rem;">
                            😊 {untagged_sentiment_data["positive"]} · 😐 {untagged_sentiment_data["neutral"]} · 😞 {untagged_sentiment_data["negative"]}
                        </div>
                        <div style="font-size:.9rem;font-weight:700;color:#999999;">Net: {untagged_net_score:+.1f}%</div>
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
                    "moderate": ("🙂", "Mixed",                       "#8b7a2e", "rgba(139,157,195,0.08)", "#8b9dc3"),
                    "neutral":  ("😐", "Neutral",                     "#8b9dc3", "rgba(139,157,195,0.08)", "#8b9dc3"),
                    "weak":     ("⚠️", "Needs attention (Negative)", "#b03a2e", "rgba(176,58,46,0.08)",  "#b03a2e"),
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

                if avg_net > 20: overall_tone, overall_color = "Predominantly positive", "#4a7c59"
                elif avg_net > 0: overall_tone, overall_color = "Moderately positive", "#6ba587"
                elif avg_net == 0: overall_tone, overall_color = "Neutral (Balanced)", "#8b9dc3"
                elif avg_net > -20: overall_tone, overall_color = "Mixed with negative lean", "#8b9dc3"
                else: overall_tone, overall_color = "Predominantly negative", "#b03a2e"

                tone_descriptions = {
                    "Predominantly positive": "Respondents are expressing strong satisfaction with the service.",
                    "Moderately positive": "Respondents generally have positive experiences, though some areas could improve.",
                    "Neutral (Balanced)": "Sentiment is perfectly balanced with equal positive and negative comments.",
                    "Mixed with negative lean": "Sentiment is divided with significant concerns but some positive aspects.",
                    "Predominantly negative": "Respondents express significant dissatisfaction requiring urgent attention.",
                }
                overall_description = tone_descriptions.get(overall_tone, "")

                max_score = max([s for d, s in active_dims], default=0)
                min_score = min([s for d, s in active_dims], default=0)
                if max_score > 20 and min_score < 20:
                    weakest_dims = [d for d, s in active_dims if s < 20]
                elif min_score <= 0:
                    weakest_dims = [d for d, s in active_dims if s <= 0]
                else:
                    weakest_dims = []
                weakest_text = ", ".join(weakest_dims) if weakest_dims else ""

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
                    <div class="sq-dim-score" style="color:{color};">{net:+.1f}%</div>
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
                    <span class="sq-priority-text">Low but positive. Read neutral and negative logs to see what prevents a purely positive experience.</span>
                    </div>"""
                if sustain:
                    names = " · ".join(d for d, _ in sustain)
                    html += f"""<div class="sq-priority-row">
                    <span class="sq-priority-badge" style="background:rgba(74,124,89,0.12);color:#4a7c59;">Sustain — {names}</span>
                    <span class="sq-priority-text">Strong praise. Use exact positive quotes in reports to highlight system strengths.</span>
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

    # ─────────────────────────────────
    # TAB 2 — Numerical
    # ─────────────────────────────────
    with tab2:
        col_sq = st.columns(1)[0]
        sq_display = (
            f"{overall_avg:.2f}<span style='font-size:1rem'> /5</span>"
            if has_servqual_data else "N/A"
        )
        col_sq.markdown(f"""<div class="kpi-card">
          <div class="kpi-title">Overall SERVQUAL</div>
          <div class="kpi-value gold">{sq_display}</div>
          <div class="kpi-sub">{"Avg of 5 SERVQUAL dimensions" if has_servqual_data else "No SERVQUAL tags yet"}</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

        with st.expander("🕸 Servqual Radar", expanded=True):
            st.markdown("""
            <div style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                        border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;">
            <div style="font-size:.72rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem;">SERVQUAL Guide (Likert Scale Only)</div>
            <div style="font-size:.8rem;color:rgb(60,100,130);line-height:1.6;">
                This radar summarizes <strong>land public transportation</strong> feedback from Likert questions tagged to SERVQUAL dimensions.<br>
                <strong>Scale conversion:</strong> any Likert scale above <strong>5</strong> is normalized to a <strong>1–5</strong> scale.<br>
                <strong>How to read:</strong> each spoke is one dimension; farther from center means stronger perceived quality.
            </div>
            </div>
            """, unsafe_allow_html=True)

            if not has_servqual_data and not has_general_ratings:
                st.markdown("""<div class="empty-tab"><div class="icon">🕸</div>
                <p>No SERVQUAL dimension scores yet.<br>
                In <strong>Form Builder</strong>, add Likert questions and assign them to SERVQUAL dimensions.</p>
                </div>""", unsafe_allow_html=True)
            else:
                ndf_f = df[list(present_servqual_dims.values())].copy()
                obs_max_f = ndf_f.max().max()
                sm_f = float(obs_max_f) if (not pd.isna(obs_max_f) and obs_max_f > 5) else 5
                for col in present_servqual_dims.values():
                    ndf_f[col] = ndf_f[col].apply(lambda x: normalize_to_5(x, sm_f))

                dim_means = {}
                if has_servqual_data:
                    dim_means.update({
                        k: float(ndf_f[v].mean())
                        for k, v in present_servqual_dims.items()
                        if not pd.isna(ndf_f[v].mean())
                    })
                if has_general_ratings:
                    gr = [row[GENERAL_RATINGS_COL] for _, row in df.iterrows()
                          if GENERAL_RATINGS_COL in row and pd.notna(row[GENERAL_RATINGS_COL])]
                    if gr:
                        dim_means["General Ratings"] = sum(gr) / len(gr)

                labels = list(dim_means.keys())
                values = list(dim_means.values())

                if not values:
                    st.markdown("""<div class="empty-tab"><div class="icon">🕸</div>
                    <p>No dimension scores match the current filters.</p>
                    </div>""", unsafe_allow_html=True)
                else:
                    col_r1, col_r2 = st.columns([3, 2])
                    with col_r1:
                        st.markdown('<div class="section-head">SERVQUAL Dimension Averages</div>', unsafe_allow_html=True)
                        v_closed = values + [values[0]]
                        l_closed = labels + [labels[0]]
                        fig = go.Figure()
                        fig.add_trace(go.Scatterpolar(
                            r=v_closed, theta=l_closed, fill="toself",
                            fillcolor="rgba(26,50,99,0.25)",
                            line=dict(color="rgb(26,50,99)", width=3),
                            marker=dict(size=8, color="#ffc570"),
                            name="Likert (Tagged)", showlegend=True,
                        ))
                        fig.update_layout(
                            polar=dict(
                                bgcolor="rgba(0,0,0,0)",
                                radialaxis=dict(visible=True, range=[0, 5], tickvals=[1, 2, 3, 4, 5],
                                                tickfont=dict(size=10, color="rgb(120,148,172)"),
                                                gridcolor="rgba(84,119,146,0.2)", linecolor="rgba(84,119,146,0.2)"),
                                angularaxis=dict(tickfont=dict(size=12, color="rgb(26,50,99)", family="Mulish"),
                                                 gridcolor="rgba(84,119,146,0.15)"),
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
                            display_dim = "Untagged Ratings" if dim == "General Ratings" else dim
                            pct = (mean_val / 5) * 100
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

                    st.markdown("---")
                    st.markdown('<div class="section-head">📋 Analysis Conclusion</div>', unsafe_allow_html=True)

                    def get_likert_tier(score):
                        return "strong" if score >= 4 else "moderate" if score >= 3 else "weak"

                    tier_config = {
                        "strong":   ("✅", "Strong (Positive)",          "#4a7c59", "rgba(74,124,89,0.08)",   "rgba(74,124,89,0.25)"),
                        "moderate": ("🔶", "Needs monitoring",            "#8b6914", "rgba(255,197,112,0.10)", "rgba(255,197,112,0.35)"),
                        "weak":     ("🚨", "Needs attention (Negative)",  "#b03a2e", "rgba(176,58,46,0.08)",   "rgba(176,58,46,0.3)"),
                    }

                    all_scores = list(dim_means.values())
                    avg_satisfaction = sum(all_scores) / len(all_scores) if all_scores else 0
                    overall_tier = "strong" if avg_satisfaction >= 4 else "moderate" if avg_satisfaction >= 3 else "weak"
                    overall_label_t = {"strong": "Strong overall satisfaction", "moderate": "Moderate overall satisfaction", "weak": "Low overall satisfaction"}[overall_tier]
                    overall_emoji_t, _, overall_color_t, overall_bg_t, _ = tier_config[overall_tier]

                    sorted_dims = sorted(dim_means.items(), key=lambda x: x[1])
                    weakest_dims_l = [(d, s) for d, s in sorted_dims if s < 3]
                    watch_dims_l = [(d, s) for d, s in sorted_dims if 3 <= s < 4]
                    strong_dims_l = [(d, s) for d, s in sorted_dims if s >= 4]

                    overall_desc_parts = []
                    if strong_dims_l:
                        overall_desc_parts.append(f"<strong>{', '.join(d for d,_ in strong_dims_l)}</strong> {'are' if len(strong_dims_l)>1 else 'is'} performing well.")
                    if watch_dims_l:
                        overall_desc_parts.append(f"<strong>{', '.join(d for d,_ in watch_dims_l)}</strong> {'show' if len(watch_dims_l)>1 else 'shows'} room for improvement.")
                    if weakest_dims_l:
                        overall_desc_parts.append(f"<strong>{', '.join(d for d,_ in weakest_dims_l)}</strong> {'require' if len(weakest_dims_l)>1 else 'requires'} urgent attention.")
                    overall_desc_l = " ".join(overall_desc_parts) if overall_desc_parts else "Collect more responses to generate a detailed signal."

                    st.markdown(f"""
                    <div style="border:1px solid rgba(26,50,99,0.12);border-radius:12px;overflow:hidden;margin-bottom:1.2rem;">
                    <div style="background:{overall_bg_t};padding:1.1rem 1.3rem;border-bottom:1px solid rgba(26,50,99,0.08);">
                        <div style="font-size:0.65rem;font-weight:700;color:rgb(120,148,172);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.4rem;">Overall SERVQUAL Signal</div>
                        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                        <div style="font-size:2rem;font-weight:700;color:{overall_color_t};line-height:1;">{avg_satisfaction:.2f}<span style="font-size:1rem;color:rgb(120,148,172);font-weight:400;">/5</span></div>
                        <div>
                            <div style="font-size:1rem;font-weight:700;color:{overall_color_t};">{overall_emoji_t} {overall_label_t}</div>
                            <div style="font-size:0.78rem;color:rgb(80,110,140);margin-top:2px;">{overall_desc_l}</div>
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
                        tier_k = get_likert_tier(score)
                        emoji_t, label_t, color_t, bg_t, border_t = tier_config[tier_k]
                        desc_tuple = likert_dimension_descriptions.get(dim)
                        desc_l = desc_tuple[0] if desc_tuple else ""
                        insight_l = desc_tuple[1].get(tier_k, "") if desc_tuple else ""
                        action_l = desc_tuple[1].get(f"action_{tier_k}", "") if desc_tuple else ""
                        pct = (score / 5) * 100
                        with likert_cols[col_idx]:
                            st.markdown(f"""
                            <div style="border:1px solid rgba(26,50,99,0.10);border-top:3px solid {color_t};border-radius:10px;padding:0.9rem 1rem;background:{bg_t};height:100%;">
                            <div style="font-weight:700;color:rgb(26,50,99);font-size:0.88rem;margin-bottom:0.2rem;">{dim}</div>
                            <div style="font-size:0.63rem;color:rgb(120,148,172);margin-bottom:0.6rem;line-height:1.4;">{desc_l}</div>
                            <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:0.4rem;">
                            <span style="font-size:1.55rem;font-weight:700;color:{color_t};line-height:1;">{score:.2f}</span>
                            <span style="font-size:0.75rem;color:rgb(120,148,172);">/5</span>
                            </div>
                            <div style="background:rgba(84,119,146,0.12);border-radius:999px;height:5px;overflow:hidden;margin-bottom:0.55rem;">
                            <div style="width:{pct:.1f}%;height:100%;border-radius:999px;background:{color_t};"></div>
                            </div>
                            <div style="display:inline-flex;align-items:center;gap:4px;border:1px solid {border_t};border-radius:999px;padding:.15rem .6rem;font-size:.62rem;font-weight:700;color:{color_t};margin-bottom:.65rem;">{emoji_t} {label_t}</div>
                            <div style="font-size:.72rem;color:rgb(60,90,120);line-height:1.55;margin-bottom:.5rem;">{insight_l}</div>
                            <div style="border-left:3px solid {border_t};padding-left:.6rem;font-size:.7rem;color:rgb(80,110,140);line-height:1.5;font-style:italic;">{action_l}</div>
                            </div>""", unsafe_allow_html=True)

                    if weakest_dims_l or watch_dims_l or strong_dims_l:
                        st.markdown('<div style="margin-top:1.2rem;"></div>', unsafe_allow_html=True)
                        st.markdown('<div style="font-size:0.72rem;font-weight:700;color:rgb(120,148,172);text-transform:uppercase;letter-spacing:.08em;margin-bottom:0.7rem;">Action priority</div>', unsafe_allow_html=True)
                        triage_html = '<div style="display:flex;flex-direction:column;gap:8px;">'
                        if weakest_dims_l:
                            names = ", ".join(f"{d} ({s:.2f})" for d, s in weakest_dims_l)
                            triage_html += f"""<div style="display:flex;gap:10px;align-items:flex-start;padding:.75rem 1rem;background:rgba(176,58,46,0.06);border:1px solid rgba(176,58,46,0.2);border-radius:8px;">
                            <span style="font-size:.65rem;font-weight:700;background:rgba(176,58,46,0.12);color:#b03a2e;border-radius:4px;padding:.2rem .55rem;white-space:nowrap;flex-shrink:0;margin-top:1px;">🚨 Urgent</span>
                            <div><div style="font-size:.78rem;font-weight:700;color:#b03a2e;margin-bottom:2px;">{names}</div>
                            <div style="font-size:.72rem;color:rgb(80,110,140);line-height:1.5;">Scores below 3.0 suggest critical service gaps. Check the Quantitative Tab to pinpoint which metric is pulling the dimension down.</div></div></div>"""
                        if watch_dims_l:
                            names = ", ".join(f"{d} ({s:.2f})" for d, s in watch_dims_l)
                            triage_html += f"""<div style="display:flex;gap:10px;align-items:flex-start;padding:.75rem 1rem;background:rgba(255,197,112,0.08);border:1px solid rgba(255,197,112,0.3);border-radius:8px;">
                            <span style="font-size:.65rem;font-weight:700;background:rgba(255,197,112,0.2);color:#8b6914;border-radius:4px;padding:.2rem .55rem;white-space:nowrap;flex-shrink:0;margin-top:1px;">🔶 Monitor</span>
                            <div><div style="font-size:.78rem;font-weight:700;color:#8b6914;margin-bottom:2px;">{names}</div>
                            <div style="font-size:.72rem;color:rgb(80,110,140);line-height:1.5;">Borderline scores (3.0–3.99). Targeted improvements in scheduling, communication, or facilities could push these above 4.0.</div></div></div>"""
                        if strong_dims_l:
                            names = ", ".join(f"{d} ({s:.2f})" for d, s in strong_dims_l)
                            triage_html += f"""<div style="display:flex;gap:10px;align-items:flex-start;padding:.75rem 1rem;background:rgba(74,124,89,0.06);border:1px solid rgba(74,124,89,0.2);border-radius:8px;">
                            <span style="font-size:.65rem;font-weight:700;background:rgba(74,124,89,0.12);color:#4a7c59;border-radius:4px;padding:.2rem .55rem;white-space:nowrap;flex-shrink:0;margin-top:1px;">✅ Sustain</span>
                            <div><div style="font-size:.78rem;font-weight:700;color:#4a7c59;margin-bottom:2px;">{names}</div>
                            <div style="font-size:.72rem;color:rgb(80,110,140);line-height:1.5;">Scores at 4.0+ indicate genuine commuter satisfaction. Document what drives these scores and replicate across weaker dimensions.</div></div></div>"""
                        triage_html += '</div>'
                        st.markdown(triage_html, unsafe_allow_html=True)

        st.markdown("""<div style="height: 2rem;"></div>""", unsafe_allow_html=True)
        with st.expander("📊 Quantitative Data", expanded=True):
            st.markdown("""
            <div style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                        border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;">
            <div style="font-size:.72rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem;">Quantitative Guide</div>
            <div style="font-size:.8rem;color:rgb(60,100,130);line-height:1.6;">
                This tab is for <strong>numeric (Likert) ratings</strong> about land public transportation.<br>
                <strong>Likert Response Log:</strong> each numeric answer with question text and time.
            </div>
            </div>
            """, unsafe_allow_html=True)

            if not has_any_rating_data:
                st.markdown("""<div class="empty-tab"><div class="icon">📊</div>
                  <p>No rating scores available yet.</p>
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
                        schema_scale = question_scale_map.get(question_text) or question_scale_map.get(base_question)
                        if schema_scale is not None and schema_scale > 1:
                            q_scale_max = float(schema_scale)
                        else:
                            q_scores = pd.to_numeric(
                                df["answers"].apply(lambda a: a.get(question) if isinstance(a, dict) else None),
                                errors="coerce",
                            )
                            q_max = q_scores.max()
                            q_scale_max = float(q_max) if pd.notna(q_max) and q_max > 5 else 5
                        score_norm = normalize_to_5(float(score), q_scale_max)
                        scale_max_int = int(q_scale_max) if float(q_scale_max).is_integer() else round(float(q_scale_max), 2)
                        q_dimension = form_schema.get(question_text, {}).get("dimension") or form_schema.get(base_question, {}).get("dimension")
                        likert_rows.append({
                            "Question": question_text,
                            "Dimension": q_dimension if q_dimension else "Untagged",
                            "Score": int(score) if float(score).is_integer() else float(score),
                            "Score (Selected Scale)": f"{int(score) if float(score).is_integer() else round(float(score), 2)}/{scale_max_int}",
                            "ScoreNormalized": round(float(score_norm), 2),
                            "Submitted": submitted,
                        })

                if likert_rows:
                    likert_df = pd.DataFrame(likert_rows)
                    likert_df["Submitted"] = pd.to_datetime(likert_df["Submitted"], errors="coerce")

                    q_avg = (
                        likert_df.groupby("Question", as_index=False)["ScoreNormalized"]
                        .mean().rename(columns={"ScoreNormalized": "Average Score"})
                    )
                    q_avg["Responses"] = likert_df.groupby("Question").size().values
                    q_avg = q_avg.sort_values("Average Score", ascending=False)
                    top_n = q_avg.head(5)
                    bottom_n = q_avg.tail(5)
                    top_bottom = pd.concat([top_n, bottom_n], ignore_index=True).drop_duplicates(subset=["Question"])
                    top_bottom["Category"] = top_bottom["Question"].isin(top_n["Question"]).map({True: "Top", False: "Bottom"})

                    st.altair_chart(
                        alt.Chart(top_bottom).mark_bar(cornerRadiusEnd=4).encode(
                            y=alt.Y("Question:N", sort="-x", title="Question"),
                            x=alt.X("Average Score:Q", scale=alt.Scale(domain=[0, 5]), title="Average Score (/5)"),
                            color=alt.Color("Average Score:Q",
                                            scale=alt.Scale(domain=[0, 5], range=["#b03a2e", "#ffc570", "#4a7c59"]),
                                            legend=alt.Legend(title="Score (/5)")),
                            tooltip=["Question:N", alt.Tooltip("Average Score:Q", format=".2f"), "Responses:Q", "Category:N"],
                        ).properties(height=280),
                        use_container_width=True,
                    )

                    st.markdown('<div class="section-head">Score Distribution</div>', unsafe_allow_html=True)
                    st.caption("Breakdown of how many respondents gave each score per question.")
                    score_dist = []
                    for question in likert_df["Question"].unique():
                        q_data = likert_df[likert_df["Question"] == question]
                        q_dim = q_data["Dimension"].iloc[0] if len(q_data) > 0 else "Untagged"
                        scale_str = q_data["Score (Selected Scale)"].iloc[0] if len(q_data) > 0 else "0/5"
                        sm_v = int(scale_str.split("/")[1]) if "/" in scale_str else 5
                        sc_counts = q_data["Score"].value_counts().sort_index()
                        row_d = {"Question": question, "Dimension": q_dim, "Total Responses": len(q_data)}
                        for sc_v in range(1, int(sm_v) + 1):
                            row_d[f"Score {sc_v}"] = int(sc_counts.get(sc_v, 0))
                        score_dist.append(row_d)
                    if score_dist:
                        st.dataframe(pd.DataFrame(score_dist), use_container_width=True, hide_index=True, height=300)
                else:
                    st.info("No Likert responses found in the selected date range.")

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
                        .select("id, prompt, q_type, is_demographic")
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

                    existing_prompts = {q.get("prompt") for q in all_questions}
                    for std_q in STANDARD_DEMO_QUESTIONS:
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
                    col_order_r = ["Respondent ID", "Submitted", "Time"] + demo_cols_r + other_cols_r
                    col_order_r = [c for c in col_order_r if c in df_resp_f.columns]
                    st.dataframe(df_resp_f[col_order_r], use_container_width=True, hide_index=True,
                                 height=min(600, 80 + 36 * max(1, len(df_resp_f))))
                    csv_data = df_resp_f[col_order_r].to_csv(index=False)
                    st.download_button(
                        "📥 Download as CSV", data=csv_data,
                        file_name=f"respondents_{current_form_id}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )
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