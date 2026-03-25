import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
from datetime import datetime, timedelta
from st_supabase_connection import SupabaseConnection

# ══════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════
st.set_page_config(
    page_title="PUV Sentiment Dashboard",
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

/* Do not hide the header here so the sidebar toggle remains visible! */
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
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  color: var(--navy) !important;
}
/* Recolor the native animated Streamlit line to navy instead of red */
div[data-baseweb="tab-highlight"] {
  background-color: var(--navy) !important;
}

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
.empty-tab p     { font-size: .9rem; margin: 0; }

/* 📱 MOBILE RESPONSIVENESS 📱 */
@media screen and (max-width: 768px) {
  .dash-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 1.2rem;
  }
  .dash-header h1 { font-size: 1.5rem !important; }
  
  .kpi-card {
    min-height: auto;
    padding: 0.8rem 1rem;
  }
  .kpi-value { font-size: 1.6rem; }
  
  /* Make Tabs swipeable horizontally on mobile */
  [data-testid="stTabs"] [role="tablist"] {
    overflow-x: auto;
    flex-wrap: nowrap !important;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none; /* Firefox */
  }
  [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar { 
    display: none; /* Safari and Chrome */
  }
  [data-testid="stTabs"] [role="tab"] {
    white-space: nowrap;
    padding: 0.5rem 0.8rem !important;
    font-size: 0.75rem !important;
  }
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
        "LABEL_0":"NEGATIVE","negative":"NEGATIVE",
        "LABEL_1":"NEUTRAL", "neutral": "NEUTRAL",
        "LABEL_2":"POSITIVE","positive":"POSITIVE",
    }
    res = sentiment_analyzer(text[:512])[0]
    return label_map.get(res["label"], res["label"].upper()), round(res["score"], 4)

# ══════════════════════════════════════════
# DATA FETCH
# ══════════════════════════════════════════
@st.cache_data(ttl=30)
def fetch_dashboard_data(email: str) -> pd.DataFrame:
    try:
        r = (conn.client.table("form_responses")
             .select("*").eq("admin_email", email)
             .order("created_at").execute())
        return pd.DataFrame(r.data or [])
    except Exception as e:
        st.warning(f"Could not load responses: {e}")
        return pd.DataFrame()

def persist_sentiment_batch(rows: list[dict]):
    if not rows:
        return
    try:
        conn.client.table("form_responses").upsert(rows, on_conflict="id").execute()
    except Exception as e:
        pass   # non-critical — cache covers display

# ══════════════════════════════════════════
# STATIC HEADER
# ══════════════════════════════════════════
st.markdown("""
<div class="dash-header">
  <div>
    <h1>📊 Sentiment Dashboard</h1>
    <p class="sub">PUV Commuter Experience · SERVQUAL Analysis</p>
  </div>
  <div class="live-badge"><span class="live-dot"></span> LIVE SYNC</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-head">🗓 Filter by Date Range</div>', unsafe_allow_html=True)
cd1, cd2, _ = st.columns([2, 2, 4])
with cd1:
    date_from = st.date_input("From", value=datetime.today() - timedelta(days=30), key="df")
with cd2:
    date_to   = st.date_input("To",   value=datetime.today(),                      key="dt")

# ══════════════════════════════════════════
# LIVE FRAGMENT  (runs every 30 s)
# ══════════════════════════════════════════
@st.fragment(run_every=30)
def render_dashboard():
    df_raw = fetch_dashboard_data(admin_email)

    if df_raw.empty:
        st.markdown("""
        <div class="empty-tab">
          <div class="icon">⏳</div>
          <p>No responses yet. Share your survey link to start collecting data.</p>
        </div>""", unsafe_allow_html=True)
        return

    # ── timestamps ──
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

    # ── SERVQUAL dim columns ──
    DIM_COLS = {
        "Tangibles":      "tangibles_avg",
        "Reliability":    "reliability_avg",
        "Responsiveness": "responsiveness_avg",
        "Assurance":      "assurance_avg",
        "Empathy":        "empathy_avg",
    }
    present_dims = {k: v for k, v in DIM_COLS.items() if v in df.columns}
    
    # Safely check if there is actual SERVQUAL data to plot
    has_servqual_data = False
    if present_dims:
        has_servqual_data = df[[v for v in present_dims.values()]].notna().any().any()

    dim_palette = {
        "Tangibles":      "#547792",
        "Reliability":    "#1a3263",
        "Responsiveness": "#ffc570",
        "Assurance":      "#3c6482",
        "Empathy":        "#d4a373",
    }

    # ── Sentiment analysis — batch pending rows, then bulk upsert ──
    sent_col = "sentiment_status"
    if "raw_feedback" in df.columns and sent_col in df.columns:
        pending_mask = df[sent_col] == "pending"
        pending_rows = df[pending_mask & df["raw_feedback"].notna() & (df["raw_feedback"].str.strip() != "")]

        if not pending_rows.empty:
            batch_updates = []
            for _, row in pending_rows.iterrows():
                label, score = analyze_text(str(row["raw_feedback"]).strip())
                df.loc[df["id"] == row["id"], sent_col]            = label
                df.loc[df["id"] == row["id"], "sentiment_score"]   = score
                batch_updates.append({"id": row["id"], "sentiment_status": label, "sentiment_score": score})
            persist_sentiment_batch(batch_updates)
            fetch_dashboard_data.clear()

    # ── counts ──
    sent_valid = df[sent_col].isin(["POSITIVE","NEUTRAL","NEGATIVE"]) if sent_col in df.columns else pd.Series(False, index=df.index)
    df_sent    = df[sent_valid].copy() if sent_col in df.columns else pd.DataFrame()
    pending_n  = int((df[sent_col] == "pending").sum()) if sent_col in df.columns else 0

    total       = len(df)
    pos_count   = int((df_sent[sent_col] == "POSITIVE").sum())   if not df_sent.empty else 0
    pos_rate    = (pos_count / len(df_sent) * 100)               if len(df_sent) > 0  else 0
    avg_conf    = float(df_sent["sentiment_score"].mean())       if ("sentiment_score" in df_sent.columns and not df_sent.empty) else 0
    
    # Safely calculate overall_avg to prevent NaN
    overall_avg = df[[v for v in present_dims.values()]].mean().mean() if has_servqual_data else 0
    if pd.isna(overall_avg): overall_avg = 0
    if pd.isna(avg_conf): avg_conf = 0

    # ══════════════════════════════════
    # KPI RIBBON
    # ══════════════════════════════════
    k1, k2, k3, k4, k5 = st.columns(5)
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

    # Dynamic SERVQUAL display
    servqual_display = f"{overall_avg:.2f}<span style='font-size:1rem'> /5</span>" if has_servqual_data else "N/A"
    servqual_subtext = "Average across all dimensions" if has_servqual_data else "No SERVQUAL tags"
    k3.markdown(f"""<div class="kpi-card">
      <div class="kpi-title">Overall SERVQUAL</div>
      <div class="kpi-value gold">{servqual_display}</div>
      <div class="kpi-sub">{servqual_subtext}</div>
    </div>""", unsafe_allow_html=True)

    k4.markdown(f"""<div class="kpi-card">
      <div class="kpi-title">AI Confidence</div>
      <div class="kpi-value">{avg_conf*100:.1f}%</div>
      <div class="conf-bar-wrap"><div class="conf-bar" style="width:{avg_conf*100:.1f}%"></div></div>
    </div>""", unsafe_allow_html=True)

    k5.markdown(f"""<div class="kpi-card">
      <div class="kpi-title">Analysis Queue</div>
      <div class="kpi-value">{total - pending_n}<span style="font-size:1rem"> analyzed</span></div>
      <div class="kpi-pending">⏳ {pending_n} pending</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:1.2rem'></div>", unsafe_allow_html=True)

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
    # ─────────────────────────────────
    with tab1:
        if not has_servqual_data:
            st.markdown("""<div class="empty-tab"><div class="icon">🕸</div>
              <p>No SERVQUAL dimension scores found yet.<br>Make sure responses include Likert questions mapped to dimensions.</p>
            </div>""", unsafe_allow_html=True)
        else:
            dim_means = {k: float(df[v].mean()) for k, v in present_dims.items() if not pd.isna(df[v].mean())}
            labels    = list(dim_means.keys())
            values    = list(dim_means.values())

            col_r1, col_r2 = st.columns([3, 2])
            with col_r1:
                st.markdown('<div class="section-head">SERVQUAL Dimension Averages</div>', unsafe_allow_html=True)
                if len(labels) >= 3:
                    v_closed = values + [values[0]]
                    l_closed = labels + [labels[0]]
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=v_closed, theta=l_closed, fill="toself",
                        fillcolor="rgba(26,50,99,0.15)",
                        line=dict(color="rgb(26,50,99)", width=2),
                        marker=dict(color="rgb(255,197,112)", size=7),
                    ))
                    fig.update_layout(
                        polar=dict(
                            bgcolor="rgba(0,0,0,0)",
                            radialaxis=dict(visible=True, range=[0,5],
                                tickfont=dict(size=10, color="rgb(120,148,172)"),
                                gridcolor="rgba(84,119,146,0.2)", linecolor="rgba(84,119,146,0.2)"),
                            angularaxis=dict(
                                tickfont=dict(size=12, color="rgb(26,50,99)", family="Mulish"),
                                gridcolor="rgba(84,119,146,0.15)"),
                        ),
                        showlegend=False, margin=dict(t=30,b=30,l=60,r=60),
                        paper_bgcolor="rgba(0,0,0,0)", height=340,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    bar_data = pd.DataFrame({"Dimension": labels, "Score": values})
                    bar = (alt.Chart(bar_data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                        .encode(
                            x=alt.X("Dimension:N", axis=alt.Axis(labelAngle=0)),
                            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0,5])),
                            color=alt.Color("Dimension:N",
                                scale=alt.Scale(domain=list(dim_palette.keys()), range=list(dim_palette.values())),
                                legend=None),
                        ).properties(height=300))
                    st.altair_chart(bar, use_container_width=True)

            with col_r2:
                st.markdown('<div class="section-head">Dimension Scores</div>', unsafe_allow_html=True)
                for dim, mean_val in dim_means.items():
                    pct      = (mean_val / 5) * 100
                    color    = "#4a7c59" if mean_val >= 4 else "#8b9dc3" if mean_val >= 3 else "#b03a2e"
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

                if dim_means:
                    weakest = min(dim_means, key=dim_means.get)
                    st.markdown(f"""
                    <div style="background:rgba(176,58,46,0.07);border:1px solid rgba(176,58,46,0.2);
                                border-left:4px solid #b03a2e;border-radius:7px;padding:.7rem 1rem;margin-top:.8rem;">
                      <div style="font-size:.65rem;font-weight:700;color:#b03a2e;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.2rem;">⚠ Needs Attention</div>
                      <div style="font-size:.85rem;font-weight:700;color:rgb(26,50,99);">{weakest}</div>
                      <div style="font-size:.72rem;color:rgb(120,148,172);">Lowest average score</div>
                    </div>""", unsafe_allow_html=True)

    # ─────────────────────────────────
    # TAB 2 — TRENDS
    # ─────────────────────────────────
    with tab2:
        if "created_at" not in df.columns or not has_servqual_data:
            st.markdown("""<div class="empty-tab"><div class="icon">📈</div>
              <p>Trend data requires timestamps and SERVQUAL dimension scores.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="section-head">Dimension Scores Over Time</div>', unsafe_allow_html=True)
            df_trend      = df.copy()
            df_trend["date"] = df_trend["created_at"].dt.date
            daily         = (df_trend.groupby("date")[[v for v in present_dims.values()]].mean().reset_index())
            daily.columns = ["date"] + list(present_dims.keys())
            daily_long    = daily.melt("date", var_name="Dimension", value_name="Score")

            trend_chart = (
                alt.Chart(daily_long).mark_line(point=True, strokeWidth=2)
                .encode(
                    x=alt.X("date:T", axis=alt.Axis(format="%b %d", title="Date")),
                    y=alt.Y("Score:Q", scale=alt.Scale(domain=[1,5]), title="Avg Score"),
                    color=alt.Color("Dimension:N",
                        scale=alt.Scale(domain=list(dim_palette.keys()), range=list(dim_palette.values()))),
                    tooltip=["date:T","Dimension:N", alt.Tooltip("Score:Q", format=".2f")],
                ).properties(height=300)
            )
            st.altair_chart(trend_chart, use_container_width=True)

            if sent_col in df.columns:
                st.markdown('<div class="section-head">Daily Sentiment Distribution</div>', unsafe_allow_html=True)
                df_s = df[df[sent_col].isin(["POSITIVE","NEUTRAL","NEGATIVE"])].copy()
                if not df_s.empty:
                    df_s["date"] = df_s["created_at"].dt.date
                    sent_daily   = df_s.groupby(["date", sent_col]).size().reset_index(name="Count")
                    st.altair_chart(
                        alt.Chart(sent_daily).mark_bar()
                        .encode(
                            x=alt.X("date:T", axis=alt.Axis(format="%b %d")),
                            y=alt.Y("Count:Q", stack="normalize", axis=alt.Axis(format="%")),
                            color=alt.Color(f"{sent_col}:N",
                                scale=alt.Scale(domain=["POSITIVE","NEUTRAL","NEGATIVE"],
                                                range=["#4a7c59","#8b9dc3","#b03a2e"]),
                                legend=alt.Legend(title="Sentiment")),
                            tooltip=["date:T", f"{sent_col}:N", "Count:Q"],
                        ).properties(height=220),
                        use_container_width=True,
                    )

    # ─────────────────────────────────
    # TAB 3 — SENTIMENT
    # ─────────────────────────────────
    with tab3:
        if df_sent.empty:
            st.markdown("""<div class="empty-tab"><div class="icon">💬</div>
              <p>No analyzed responses yet.<br>The AI model processes submissions automatically.</p>
            </div>""", unsafe_allow_html=True)
        else:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown('<div class="section-head">Distribution</div>', unsafe_allow_html=True)
                sc = df_sent[sent_col].value_counts().reset_index()
                sc.columns = ["Sentiment", "Count"]
                st.altair_chart(
                    alt.Chart(sc).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(
                        x=alt.X("Sentiment:N", sort=["POSITIVE","NEUTRAL","NEGATIVE"], axis=alt.Axis(labelAngle=0)),
                        y="Count:Q",
                        color=alt.Color("Sentiment:N",
                            scale=alt.Scale(domain=["POSITIVE","NEUTRAL","NEGATIVE"],
                                            range=["#4a7c59","#8b9dc3","#b03a2e"]), legend=None),
                        tooltip=["Sentiment","Count"],
                    ).properties(height=220),
                    use_container_width=True,
                )

                st.markdown('<div class="section-head">Avg Confidence</div>', unsafe_allow_html=True)
                if "sentiment_score" in df_sent.columns:
                    for s, color in [("POSITIVE","#4a7c59"),("NEUTRAL","#8b9dc3"),("NEGATIVE","#b03a2e")]:
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
                log_cols = ["raw_feedback", sent_col]
                if "sentiment_score" in df_sent.columns: log_cols.append("sentiment_score")
                if "created_at"      in df_sent.columns: log_cols.append("created_at")

                log_df = df_sent[log_cols].copy().rename(columns={
                    "raw_feedback":    "Feedback",
                    sent_col:          "Sentiment",
                    "sentiment_score": "Confidence",
                    "created_at":      "Submitted",
                })
                if "Confidence" in log_df.columns:
                    log_df["Confidence"] = pd.to_numeric(log_df["Confidence"], errors="coerce")
                    log_df["Confidence"] = (log_df["Confidence"] * 100).round(1).astype(str) + "%"
                    log_df.loc[log_df["Confidence"] == "nan%", "Confidence"] = "Pending"

                def color_sent(val):
                    return {"POSITIVE":"color:#4a7c59;font-weight:700","NEGATIVE":"color:#b03a2e;font-weight:700",
                            "NEUTRAL":"color:#8b9dc3;font-weight:700"}.get(val,"")

                st.dataframe(
                    log_df.style.map(color_sent, subset=["Sentiment"]),
                    use_container_width=True, hide_index=True, height=360,
                )

    # ─────────────────────────────────
    # TAB 4 — QUANTITATIVE
    # ─────────────────────────────────
    with tab4:
        if not has_servqual_data:
            st.markdown("""<div class="empty-tab"><div class="icon">📊</div>
              <p>No SERVQUAL scores available yet.</p>
            </div>""", unsafe_allow_html=True)
        else:
            if "demo_answers" in df.columns:
                puv_key = "What primary PUV type do you usually ride?"
                df["puv_type"] = df["demo_answers"].apply(
                    lambda x: x.get(puv_key) if isinstance(x, dict) else None
                )
                df_puv = df.dropna(subset=["puv_type"])

                if not df_puv.empty:
                    st.markdown('<div class="section-head">Score by PUV Type</div>', unsafe_allow_html=True)
                    puv_agg  = df_puv.groupby("puv_type")[[v for v in present_dims.values()]].mean().reset_index()
                    puv_long = puv_agg.melt("puv_type", var_name="dim_col", value_name="Score")
                    inv_map  = {v: k for k, v in present_dims.items()}
                    puv_long["Dimension"] = puv_long["dim_col"].map(inv_map)
                    st.altair_chart(
                        alt.Chart(puv_long).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
                        .encode(
                            x=alt.X("puv_type:N", axis=alt.Axis(labelAngle=-20), title="PUV Type"),
                            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0,5])),
                            color=alt.Color("Dimension:N",
                                scale=alt.Scale(domain=list(dim_palette.keys()), range=list(dim_palette.values()))),
                            xOffset="Dimension:N",
                            tooltip=["puv_type:N","Dimension:N", alt.Tooltip("Score:Q", format=".2f")],
                        ).properties(height=280),
                        use_container_width=True,
                    )

            st.markdown('<div class="section-head">All SERVQUAL Averages</div>', unsafe_allow_html=True)
            summary = [{"Dimension": k, "Average": f"{df[v].mean():.2f}",
                        "Min": f"{df[v].min():.2f}", "Max": f"{df[v].max():.2f}",
                        "Responses": int(df[v].notna().sum())}
                       for k, v in present_dims.items()]
            st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)

    # ─────────────────────────────────
    # TAB 5 — DEMOGRAPHICS
    # ─────────────────────────────────
    with tab5:
        if "demo_answers" not in df.columns:
            st.markdown("""<div class="empty-tab"><div class="icon">👥</div>
              <p>No demographic data available. Enable the Commuter Profile in Form Builder.</p>
            </div>""", unsafe_allow_html=True)
        else:
            demo_df = pd.json_normalize(df["demo_answers"].dropna().tolist())
            if demo_df.empty:
                st.markdown("""<div class="empty-tab"><div class="icon">👥</div>
                  <p>No demographic responses recorded yet.</p>
                </div>""", unsafe_allow_html=True)
            else:
                DEMO_Q_LABELS = {
                    "What is your age bracket?":                    "Age Bracket",
                    "What is your gender?":                         "Gender",
                    "What is your primary occupation?":             "Occupation",
                    "What primary PUV type do you usually ride?":   "PUV Type",
                    "How often do you commute?":                    "Commute Frequency",
                }
                present_demo = [q for q in DEMO_Q_LABELS if q in demo_df.columns]
                if not present_demo:
                    st.dataframe(demo_df, use_container_width=True, hide_index=True)
                else:
                    pairs = [(present_demo[i], present_demo[i+1] if i+1 < len(present_demo) else None)
                             for i in range(0, len(present_demo), 2)]
                    for q_l, q_r in pairs:
                        cl, cr = st.columns(2)
                        for col_w, q in [(cl, q_l), (cr, q_r)]:
                            if q is None: continue
                            with col_w:
                                label = DEMO_Q_LABELS.get(q, q)
                                vc    = demo_df[q].value_counts().reset_index()
                                vc.columns = [label, "Count"]
                                st.altair_chart(
                                    alt.Chart(vc).mark_arc(innerRadius=40)
                                    .encode(
                                        theta="Count:Q",
                                        color=alt.Color(f"{label}:N",
                                            scale=alt.Scale(scheme="blues"),
                                            legend=alt.Legend(orient="bottom", labelFontSize=10)),
                                        tooltip=[f"{label}:N","Count:Q"],
                                    ).properties(title=label, height=200),
                                    use_container_width=True,
                                )

    # ── EXPORT ──
    st.markdown("---")
    st.markdown('<div class="section-head">📥 Export Data</div>', unsafe_allow_html=True)
    ex1, ex2, _ = st.columns([2, 2, 4])
    with ex1:
        st.download_button(
            "⬇ All Responses (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"puv_responses_{date_from}_{date_to}.csv",
            mime="text/csv", use_container_width=True,
        )
    with ex2:
        if not df_sent.empty and "raw_feedback" in df_sent.columns:
            cols_to_export = ["raw_feedback", sent_col] + [s for s in ["sentiment_score", "created_at"] if s in df_sent.columns]
            sent_export = df_sent[cols_to_export].copy()
            
            st.download_button(
                "⬇ Sentiment Log (CSV)",
                data=sent_export.to_csv(index=False).encode("utf-8"),
                file_name=f"puv_sentiment_{date_from}_{date_to}.csv",
                mime="text/csv", use_container_width=True,
            )

render_dashboard()