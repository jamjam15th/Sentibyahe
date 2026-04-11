import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
import re
from datetime import datetime, timedelta
from st_supabase_connection import SupabaseConnection

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
  padding: 6px 14px; border-radius: 20px; font-weight: 700;format
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
  .kpi-card { min-height: auto; padding: 0.8rem 1rem; }
  .kpi-value { font-size: 1.6rem; }
  [data-testid="stTabs"] [role="tablist"] { overflow-x: auto; flex-wrap: nowrap !important; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
  [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar { display: none; }
  [data-testid="stTabs"] [role="tab"] { white-space: nowrap; padding: 0.5rem 0.8rem !important; font-size: 0.75rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# SETUP
# ══════════════════════════════════════════
conn        = st.connection("supabase", type=SupabaseConnection)
admin_email = st.session_state.get("user_email")

if not admin_email:
    st.error("🔒 Please log in to view the dashboard.")
    st.stop()

# ══════════════════════════════════════════
# DIMENSION CONFIG — single source of truth
# Adding/removing a dimension only needs a change here.
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

sentiment_analyzer = load_model()

@st.cache_data(max_entries=5000, show_spinner=False)
def analyze_text(text: str) -> tuple[str, float]:
    label_map = {
        "LABEL_0": "NEGATIVE", "negative": "NEGATIVE",
        "LABEL_1": "NEUTRAL",  "neutral":  "NEUTRAL",
        "LABEL_2": "POSITIVE", "positive": "POSITIVE",
    }
    res = sentiment_analyzer(text[:512])[0]
    return label_map.get(res["label"], str(res["label"]).upper()), round(res["score"], 4)

# ══════════════════════════════════════════
# DATA FETCH
# FIX #4: Removed cache.clear() from inside the fragment.
# Short TTL matches fragment interval so data re-fetches each live cycle.
# ══════════════════════════════════════════
@st.cache_data(ttl=5)
def fetch_dashboard_data(email: str) -> pd.DataFrame:
    try:
        r = (conn.client.table("form_responses")
             .select("*").eq("admin_email", email)
             .order("created_at").execute())
        return pd.DataFrame(r.data or [])
    except Exception as e:
        st.warning(f"Could not load responses: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=120)
def fetch_question_scale_map(email: str) -> dict:
    """Return latest scale_max per question prompt from form schema."""
    try:
        r = (conn.client.table("form_questions")
             .select("prompt, scale_max")
             .eq("admin_email", email)
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
        pass  # non-critical — TTL cache will pick it up next cycle

# ══════════════════════════════════════════
# STATIC HEADER
# ══════════════════════════════════════════
st.markdown("""
<div class="dash-header">
  <div>
    <h1>📊 Sentiment Dashboard</h1>
    <p class="sub">Land Public Transportation Experience · SERVQUAL Analysis</p>
  </div>
  <div class="live-badge"><span class="live-dot"></span> LIVE SYNC</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-head">🗓 Filter by Date Range</div>', unsafe_allow_html=True)
cd1, cd2, _ = st.columns([2, 2, 4])
with cd1:
    date_from = st.date_input("From", value=datetime.today() - timedelta(days=30), key="df")
with cd2:
    date_to   = st.date_input("To",   value=datetime.today(), key="dt")

# Demographics: standard respondent profile column keys (transport supports legacy + multi-select prompt)
TRANSPORT_DEMO_KEYS = (
    "Which land public transportation modes do you usually use? (Select all that apply)",
    "Which PUV or transport types do you usually ride or use? (Select all that apply)",
    "What primary land public transportation mode do you usually use?",
    "What primary PUV type do you usually ride?",
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
    specs: list[tuple[str, str]] = []
    for col, lab in [
        ("What is your age bracket?", "Age Bracket"),
        ("What is your gender?", "Gender"),
        ("What is your primary occupation?", "Occupation"),
    ]:
        if col in demo_df.columns:
            specs.append((col, lab))
    for tk in TRANSPORT_DEMO_KEYS:
        if tk in demo_df.columns:
            specs.append((tk, "Land public transportation mode"))
            break
    commute_c = "How often do you commute?"
    if commute_c in demo_df.columns:
        specs.append((commute_c, "Commute Frequency"))
    return specs


def _demo_chart_specs_all(demo_df: pd.DataFrame) -> list[tuple[str, str]]:
    """Known respondent-profile order first, then any extra keys (custom demographic prompts)."""
    specs = _demo_chart_specs(demo_df)
    covered = {c for c, _ in specs}
    for col in sorted(demo_df.columns):
        if col not in covered:
            lab = col if len(col) <= 48 else col[:45] + "…"
            specs.append((col, lab))
    return specs


def _format_demo_cell(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x) for x in v if x is not None and str(x).strip())
    return str(v).strip()


# ══════════════════════════════════════════
# LIVE FRAGMENT (runs every 5 s)
# ══════════════════════════════════════════
@st.fragment(run_every=timedelta(seconds=5))
def render_dashboard():
    df_raw = fetch_dashboard_data(admin_email)
    question_scale_map = fetch_question_scale_map(admin_email)

    if df_raw.empty:
        st.markdown("""
        <div class="empty-tab">
          <div class="icon">⏳</div>
          <p>No responses yet. Share your survey link to start collecting data.</p>
        </div>""", unsafe_allow_html=True)
        return

    # ── Timestamps ──
    if "created_at" in df_raw.columns:
        df_raw["created_at"] = pd.to_datetime(df_raw["created_at"], utc=True).dt.tz_localize(None)
        df = df_raw[
            (df_raw["created_at"].dt.date >= date_from) &
            (df_raw["created_at"].dt.date <= date_to)
        ].copy()
    else:
        df = df_raw.copy()

    if df.empty:
        st.info("No responses in the selected date range.")
        return

    # ── FIX #1 & #2: Build present_dims only from actual DB columns ──
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

    # FIX #5: overall_avg uses ONLY the 5 SERVQUAL dims, NOT General Ratings
    has_servqual_data = bool(present_servqual_dims) and df[
        list(present_servqual_dims.values())
    ].notna().any().any()

    overall_avg = 0.0
    if has_servqual_data:
        df['overall_servqual'] = df[list(present_servqual_dims.values())].mean(axis=1)
        normalized_df = df.copy()

        observed_max = df[list(present_servqual_dims.values())].max().max()
        if pd.isna(observed_max) or observed_max <= 0:
            scale_max = 5
        else:
            # Any Likert scale above 5 is normalized down to a 1-5 scale.
            scale_max = float(observed_max) if observed_max > 5 else 5

        for col in present_servqual_dims.values():
            normalized_df[col] = normalized_df[col].apply(lambda x: normalize_to_5(x, scale_max))

        overall_avg = normalized_df[list(present_servqual_dims.values())].mean().mean()
        if pd.isna(overall_avg):
            overall_avg = 0.0

    else: 
        df['overall_servqual'] = None
    has_any_rating_data = has_servqual_data or has_general_ratings

    # ── Palette scoped only to what's present (FIX #1 /#2) ──
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
            # FIX #4: do NOT call fetch_dashboard_data.clear() here.
            # The TTL cache will refresh on the next fragment cycle.

    # ── Counts ──
    sent_valid = (
        df[sent_col].isin(["POSITIVE", "NEUTRAL", "NEGATIVE"])
        if sent_col in df.columns
        else pd.Series(False, index=df.index)
    )
    df_sent   = df[sent_valid].copy() if sent_col in df.columns else pd.DataFrame()
    total     = len(df)
    pos_count = int((df_sent[sent_col] == "POSITIVE").sum()) if not df_sent.empty else 0
    pos_rate  = (pos_count / len(df_sent) * 100) if len(df_sent) > 0 else 0

    # ══════════════════════════════════
    # KPI RIBBON
    # ══════════════════════════════════
    k1, k2, k3 = st.columns(3)

    k1.markdown(f"""<div class="kpi-card">
      <div class="kpi-title">Total Responses</div>
      <div class="kpi-value">{total}</div>
      <div class="kpi-sub">{date_from} → {date_to}</div>
    </div>""", unsafe_allow_html=True)

    k2.markdown(f"""<div class="kpi-card">
      <div class="kpi-title">Positivity Rate</div>
      <div class="kpi-value pos">{pos_rate:.1f}%</div>
      <div class="kpi-sub">{pos_count} positive responses</div>
    </div>""", unsafe_allow_html=True)

    # FIX #5: Overall SERVQUAL shows only the 5 SERVQUAL dims
    servqual_display = (
        f"{overall_avg:.2f}<span style='font-size:1rem'> /5</span>"
        if has_servqual_data else "N/A"
    )
    servqual_subtext = "Avg of 5 SERVQUAL dimensions" if has_servqual_data else "No SERVQUAL tags yet"
    k3.markdown(f"""<div class="kpi-card">
      <div class="kpi-title">Overall SERVQUAL</div>
      <div class="kpi-value gold">{servqual_display}</div>
      <div class="kpi-sub">{servqual_subtext}</div>
    </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════
    # TABS
    # ══════════════════════════════════
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🕸 SERVQUAL Radar",
        "📈 Trends",
        "💬 Sentiment",
        "📊 Quantitative",
        "👥 Demographics",
    ])

    # ─────────────────────────────────
    # TAB 1 — SERVQUAL RADAR
    # FIX #9: General Ratings is NOT in the radar polygon.
    # It appears as a separate bar below the radar.
    # ─────────────────────────────────
    with tab1:
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

        if not has_servqual_data:
            # FIX #10: More helpful empty state message
            st.markdown("""<div class="empty-tab"><div class="icon">🕸</div>
              <p>No SERVQUAL dimension scores yet.<br><br>
              In <strong>Form Builder</strong>, assign a SERVQUAL dimension
              (Tangibles, Reliability, Responsiveness, Assurance, or Empathy)
              to your Likert questions. Untagged Likert questions are tracked
              separately as <em>General Ratings</em> below.</p>
            </div>""", unsafe_allow_html=True)
        else:
            # dim_means uses ONLY the 5 SERVQUAL dims
            dim_means = {
                k: float(normalized_df[v].mean())
                for k, v in present_servqual_dims.items()
                if not pd.isna(normalized_df[v].mean())
            }
            labels = list(dim_means.keys())
            values = list(dim_means.values())

            col_r1, col_r2 = st.columns([3, 2])
            with col_r1:
                st.markdown('<div class="section-head">SERVQUAL Dimension Averages</div>', unsafe_allow_html=True)
                v_closed = values + [values[0]]
                l_closed = labels + [labels[0]]

                fig = go.Figure()

                # SERVQUAL-only radar polygon
                fig.add_trace(go.Scatterpolar(
                    r=v_closed,
                    theta=l_closed,
                    fill="toself",
                    fillcolor="rgba(26,50,99,0.25)",
                    line=dict(color="rgb(26,50,99)", width=3),
                    marker=dict(size=8, color="#ffc570"),
                    showlegend=False,
                ))

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
                    showlegend=False,
                    margin=dict(t=40, b=40, l=60, r=60),
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=360,
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_r2:
                st.markdown('<div class="section-head">Dimension Scores</div>', unsafe_allow_html=True)
                for dim, mean_val in dim_means.items():
                    pct   = (mean_val / 5) * 100
                    color = "#4a7c59" if mean_val >= 4 else "#8b9dc3" if mean_val >= 3 else "#b03a2e"
                    st.markdown(f"""
                    <div style="margin-bottom:.7rem;">
                      <div style="display:flex;justify-content:space-between;margin-bottom:.2rem;">
                        <span style="font-size:.78rem;font-weight:700;color:rgb(26,50,99);">{dim}</span>
                        <span style="font-size:.78rem;font-weight:700;color:{color};">{mean_val:.2f}/5</span>
                      </div>
                      <div style="background:rgba(84,119,146,0.12);border-radius:999px;height:7px;overflow:hidden;">
                        <div style="width:{pct:.1f}%;height:100%;border-radius:999px;background:{color};transition:width .4s;"></div>
                      </div>
                    </div>""", unsafe_allow_html=True)

                # FIX #6: "Needs Attention" only flags actual SERVQUAL dims
                servqual_only_means = {k: v for k, v in dim_means.items() if k != "General Ratings"}
                if servqual_only_means:
                    weakest = min(servqual_only_means, key=servqual_only_means.get)
                    st.markdown(f"""
                    <div style="background:rgba(176,58,46,0.07);border:1px solid rgba(176,58,46,0.2);
                                border-left:4px solid #b03a2e;border-radius:7px;padding:.7rem 1rem;margin-top:.8rem;">
                      <div style="font-size:.65rem;font-weight:700;color:#b03a2e;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.2rem;">⚠ Needs Attention</div>
                      <div style="font-size:.85rem;font-weight:700;color:rgb(26,50,99);">{weakest}</div>
                      <div style="font-size:.72rem;color:rgb(120,148,172);">Lowest SERVQUAL dimension score</div>
                    </div>""", unsafe_allow_html=True)

                # FIX #9: General Ratings shown separately below, not in radar
                if has_general_ratings and general_ratings_avg_val is not None:
                    gr_color = "#4a7c59" if general_ratings_avg_val >= 4 else "#8b9dc3" if general_ratings_avg_val >= 3 else "#b03a2e"
                    st.markdown(f"""
                    <div style="margin-top:1rem;padding-top:.8rem;border-top:1px solid rgba(84,119,146,0.15);">
                      <div style="font-size:.65rem;font-weight:700;color:#6c757d;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.4rem;">📋 General Ratings</div>
                      <div style="display:flex;justify-content:space-between;margin-bottom:.2rem;">
                        <span style="font-size:.78rem;font-weight:700;color:rgb(26,50,99);">Untagged questions</span>
                        <span style="font-size:.78rem;font-weight:700;color:{gr_color};">{general_ratings_avg_val:.2f}/5</span>
                      </div>
                      <div style="background:rgba(108,117,125,0.12);border-radius:999px;height:7px;overflow:hidden;">
                        <div style="width:{(general_ratings_avg_val/5)*100:.1f}%;height:100%;border-radius:999px;background:{gr_color};"></div>
                      </div>
                    </div>""", unsafe_allow_html=True)

    # ─────────────────────────────────
    # TAB 2 — TRENDS
    # FIX #7: Safe column rename using dict mapping instead of positional rename
    # ─────────────────────────────────
    with tab2:
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
            daily_responses["date"] = pd.to_datetime(daily_responses["date"])
            daily_responses = daily_responses.sort_values("date")

            # Keep timeline continuous by filling missing dates with zero responses.
            full_dates = pd.date_range(
                start=daily_responses["date"].min(),
                end=daily_responses["date"].max(),
                freq="D",
            )
            daily_responses = (
                daily_responses.set_index("date")
                .reindex(full_dates, fill_value=0)
                .rename_axis("date")
                .reset_index()
            )

            if daily_responses.empty:
                st.info("No responses available for the selected date range.")
            else:
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

    # ─────────────────────────────────
    # TAB 3 — SENTIMENT
    # FIX #11: Feedback log splits the "|" separator so each answer
    # is shown on its own row with an index number for context.
    # ─────────────────────────────────
    with tab3:
        st.markdown("""
        <div style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
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

        if df_sent.empty:
            # FIX #10: Clearer empty state
            st.markdown("""<div class="empty-tab"><div class="icon">💬</div>
              <p>No analyzed responses yet.<br>
              The AI model processes open-text answers automatically on submission.<br>
              Make sure your form has at least one Short Answer or Paragraph question.</p>
            </div>""", unsafe_allow_html=True)
        else:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown('<div class="section-head">Distribution</div>', unsafe_allow_html=True)
                sc = df_sent[sent_col].value_counts().reset_index()
                sc.columns = ["Sentiment", "Count"]
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
                    .properties(height=220),
                    use_container_width=True,
                )

                st.markdown('<div class="section-head">Avg Confidence</div>', unsafe_allow_html=True)
                if "sentiment_score" in df_sent.columns:
                    for s, color in [("POSITIVE", "#4a7c59"), ("NEUTRAL", "#8b9dc3"), ("NEGATIVE", "#b03a2e")]:
                        subset = df_sent[df_sent[sent_col] == s]["sentiment_score"]
                        if not subset.empty:
                            pct = float(subset.mean()) * 100
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

                # Show sentiment-related Q&A pairs for clearer traceability.
                demo_question_set = {
                    "What is your age bracket?",
                    "What is your gender?",
                    "What is your primary occupation?",
                    "What primary PUV type do you usually ride?",
                    "What primary land public transportation mode do you usually use?",
                    "Which PUV or transport types do you usually ride or use? (Select all that apply)",
                    "Which land public transportation modes do you usually use? (Select all that apply)",
                    "How often do you commute?",
                }
                log_rows = []
                for _, row in df_sent.iterrows():
                    ans_map = row.get("answers", {})
                    sentiment  = row.get(sent_col, "")
                    confidence = row.get("sentiment_score", None)
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
                        # Skip numeric-only answers (typically Likert); keep open-text answers.
                        if pd.notna(pd.to_numeric(answer_text, errors="coerce")):
                            continue
                        idx += 1
                        log_rows.append({
                            "Response #": f"#{idx}",
                            "Question": str(question),
                            "Answer": answer_text,
                            "Sentiment": sentiment,
                            "Confidence": f"{confidence*100:.1f}%" if pd.notna(confidence) else "Pending",
                            "Submitted": submitted,
                        })

                if log_rows:
                    log_df = pd.DataFrame(log_rows)

                    def color_sent(val):
                        return {
                            "POSITIVE": "color:#4a7c59;font-weight:700",
                            "NEGATIVE": "color:#b03a2e;font-weight:700",
                            "NEUTRAL":  "color:#8b9dc3;font-weight:700",
                        }.get(val, "")

                    st.dataframe(
                        log_df.style.map(color_sent, subset=["Sentiment"]),
                        use_container_width=True,
                        hide_index=True,
                        height=360,
                    )
                else:
                    st.info("No open-text feedback in the selected range.")

    # ─────────────────────────────────
    # TAB 4 — QUANTITATIVE
    # FIX #3: dropna on Dimension after melt to remove None entries
    # ─────────────────────────────────
    with tab4:
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
            <strong>Top and Bottom Questions:</strong> which Likert items have the highest vs lowest average scores (after normalizing scales where needed).<br>
            <strong>How to use:</strong> name strengths and problem areas in your analysis and tie them to the SERVQUAL framework.<br><br>
            <strong>Likert Response Log:</strong> each numeric answer with question text and time.<br>
            <strong>How to use:</strong> audit the data, spot outliers, and support tables or appendices with raw-scale answers.
          </div>
        </div>
        """, unsafe_allow_html=True)

        if not has_any_rating_data:
            # FIX #10: Clearer empty state
            st.markdown("""<div class="empty-tab"><div class="icon">📊</div>
              <p>No rating scores available yet.<br>
              Assign SERVQUAL dimensions or leave questions untagged
              (they appear as General Ratings) in Form Builder.</p>
            </div>""", unsafe_allow_html=True)
        else:
            if "demo_answers" in df.columns:
                context_keys = sorted({
                    k
                    for ans in df["demo_answers"].dropna()
                    if isinstance(ans, dict)
                    for k in ans.keys()
                })
                usable_context_keys = []
                for key in context_keys:
                    vals = df["demo_answers"].apply(
                        lambda x: x.get(key) if isinstance(x, dict) else None
                    )
                    if vals.dropna().nunique() >= 2:
                        usable_context_keys.append(key)

                if usable_context_keys:
                    st.markdown('<div class="section-head">Score by Selected Context</div>', unsafe_allow_html=True)
                    selected_context = st.selectbox(
                        "Group scores by",
                        options=usable_context_keys,
                        key="quant_context_group",
                    )
                    df["context_group"] = df["demo_answers"].apply(
                        lambda x: x.get(selected_context) if isinstance(x, dict) else None
                    )
                    df_grouped = df.dropna(subset=["context_group"])
                    avail_cols = [v for v in all_dim_cols.values() if v in df_grouped.columns]

                    if not df_grouped.empty and avail_cols:
                        grp_agg = df_grouped.groupby("context_group")[avail_cols].mean().reset_index()
                        grp_long = grp_agg.melt("context_group", var_name="dim_col", value_name="Score")
                        inv_map = {v: k for k, v in all_dim_cols.items()}
                        grp_long["Dimension"] = grp_long["dim_col"].map(inv_map)
                        grp_long = grp_long.dropna(subset=["Dimension", "Score"])

                        if not grp_long.empty:
                            pal = scoped_palette(grp_long["Dimension"].unique().tolist())
                            st.altair_chart(
                                alt.Chart(grp_long)
                                .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
                                .encode(
                                    x=alt.X("context_group:N", axis=alt.Axis(labelAngle=-20), title="Group"),
                                    y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 5])),
                                    color=alt.Color(
                                        "Dimension:N",
                                        scale=alt.Scale(
                                            domain=list(pal.keys()),
                                            range=list(pal.values()),
                                        ),
                                    ),
                                    xOffset="Dimension:N",
                                    tooltip=["context_group:N", "Dimension:N", alt.Tooltip("Score:Q", format=".2f")],
                                )
                                .properties(height=280),
                                use_container_width=True,
                            )

            st.markdown('<div class="section-head">Likert Response Log</div>', unsafe_allow_html=True)
            likert_rows = []
            for _, row in df.iterrows():
                ans_map = row.get("answers", {})
                submitted = row.get("created_at", None)
                if not isinstance(ans_map, dict):
                    continue
                for question, answer in ans_map.items():
                    score = pd.to_numeric(answer, errors="coerce")
                    if pd.isna(score):
                        continue  # keep only numeric answers (Likert-like)
                    question_text = str(question)
                    base_question = re.sub(r"\s\(\d+\)$", "", question_text).strip()
                    schema_scale = question_scale_map.get(question_text)
                    if schema_scale is None:
                        schema_scale = question_scale_map.get(base_question)
                    if schema_scale is not None and schema_scale > 1:
                        q_scale_max = float(schema_scale)
                    else:
                        # Fallback when question is missing in schema snapshot.
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
                    likert_rows.append({
                        "Question": str(question),
                        "Score": int(score) if float(score).is_integer() else float(score),
                        "Score (Selected Scale)": f"{int(score) if float(score).is_integer() else round(float(score), 2)}/{scale_max_int}",
                        "ScoreNormalized": round(float(score_norm), 2),
                        "Submitted": submitted,
                    })

            if likert_rows:
                likert_df = pd.DataFrame(likert_rows)
                likert_df["Submitted"] = pd.to_datetime(likert_df["Submitted"], errors="coerce")
                likert_df["Submitted Date"] = likert_df["Submitted"].dt.date

                # Top/Bottom question chart
                st.markdown('<div class="section-head">Top and Bottom Questions</div>', unsafe_allow_html=True)
                st.caption("`Bottom` = lowest-rated questions based on average score. These highlight areas that may need improvement first.")
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

                st.dataframe(
                    likert_df[["Question", "Score", "Score (Selected Scale)", "Submitted"]],
                    use_container_width=True,
                    hide_index=True,
                    height=320,
                )
            else:
                st.info("No Likert responses found in the selected date range.")

    # ─────────────────────────────────
    # TAB 5 — DEMOGRAPHICS
    # ─────────────────────────────────
    with tab5:
        st.markdown("""
        <div style="background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.18);
                    border-left:4px solid rgb(26,50,99);border-radius:8px;padding:.85rem 1rem;margin-bottom:1rem;">
          <div style="font-size:.72rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.35rem;">
            Demographics Guide
          </div>
          <div style="font-size:.8rem;color:rgb(60,100,130);line-height:1.6;">
            Data comes from the <strong>respondent profile</strong> block and/or any questions you marked as <strong>demographic</strong> in Form Builder.<br>
            <strong>Donuts:</strong> how often each option was chosen. For <strong>transport (select all that apply)</strong>, one person can count in several slices.<br>
            <strong>Table below:</strong> each row is one respondent—profile answers beside their <strong>feedback text</strong>, <strong>sentiment</strong>, and <strong>rating averages</strong> so you can read answers in context.
          </div>
        </div>
        """, unsafe_allow_html=True)

        if "demo_answers" not in df.columns:
            st.markdown("""<div class="empty-tab"><div class="icon">👥</div>
              <p>No demographic data available.<br>
              Turn on <strong>respondent profile</strong> and/or mark your own questions as <strong>demographic</strong> in Form Builder, then collect responses.</p>
            </div>""", unsafe_allow_html=True)
        else:
            demo_df = pd.json_normalize(df["demo_answers"].dropna().tolist())
            if demo_df.empty:
                st.markdown("""<div class="empty-tab"><div class="icon">👥</div>
                  <p>No demographic responses recorded yet.</p>
                </div>""", unsafe_allow_html=True)
            else:
                demo_specs = _demo_chart_specs_all(demo_df)
                if not demo_specs:
                    st.dataframe(demo_df, use_container_width=True, hide_index=True)
                else:
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
                                vc = _explode_demo_series(demo_df[q]).value_counts().reset_index()
                                vc.columns = [label, "Count"]
                                st.altair_chart(
                                    alt.Chart(vc)
                                    .mark_arc(innerRadius=40)
                                    .encode(
                                        theta="Count:Q",
                                        color=alt.Color(
                                            f"{label}:N",
                                            scale=alt.Scale(scheme="blues"),
                                            legend=alt.Legend(orient="bottom", labelFontSize=10),
                                        ),
                                        tooltip=[f"{label}:N", "Count:Q"],
                                    )
                                    .properties(title=label, height=200),
                                    use_container_width=True,
                                )

                st.markdown(
                    '<div class="section-head" style="margin-top:1.2rem;">💬 Profile and responses (same person)</div>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    "Each row is one submission: demographic answers (including custom profile questions) next to that respondent’s open feedback, sentiment label, and SERVQUAL / general rating averages when present."
                )
                has_demo_row = df["demo_answers"].apply(
                    lambda x: isinstance(x, dict) and bool(x)
                )
                view = df[has_demo_row].copy()
                if view.empty:
                    st.info("No rows with filled profile data in this date range.")
                else:
                    dnorm = pd.json_normalize(view["demo_answers"].tolist())
                    for c in dnorm.columns:
                        dnorm[c] = dnorm[c].map(_format_demo_cell)
                    dnorm.columns = [
                        (f"Profile: {c}" if len(c) <= 56 else f"Profile: {c[:53]}…") for c in dnorm.columns
                    ]
                    resp_cols = [c for c in ("created_at", "sentiment_status", "raw_feedback") if c in view.columns]
                    for c in present_servqual_dims.values():
                        if c in view.columns:
                            resp_cols.append(c)
                    if has_general_ratings and GENERAL_RATINGS_COL in view.columns:
                        resp_cols.append(GENERAL_RATINGS_COL)
                    resp_part = view[resp_cols].reset_index(drop=True)
                    merged_view = pd.concat([resp_part, dnorm.reset_index(drop=True)], axis=1)
                    table_kw = dict(
                        data=merged_view,
                        use_container_width=True,
                        hide_index=True,
                        height=min(520, 80 + 36 * max(1, len(merged_view))),
                    )
                    if "raw_feedback" in merged_view.columns:
                        table_kw["column_config"] = {
                            "raw_feedback": st.column_config.TextColumn(
                                "Open feedback",
                                width="large",
                            )
                        }
                    st.dataframe(**table_kw)

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

    # FIX #12: New SERVQUAL summary export
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


render_dashboard()