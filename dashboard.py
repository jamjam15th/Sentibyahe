import streamlit as st
import pandas as pd
import altair as alt
import plotly.graph_objects as go
from datetime import datetime, timedelta
from st_supabase_connection import SupabaseConnection

# ══════════════════════════════════════════
# 1. SETUP & THEME (Minimalist Design)
# ══════════════════════════════════════════
st.set_page_config(page_title="PUV Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
    /* Main Background & Font */
    .stApp { background-color: #f8f9fa; }
    
    /* Clean Card Design */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #edf2f7;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-label { color: #64748b; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; }
    .metric-value { color: #1e293b; font-size: 1.8rem; font-weight: 800; margin: 5px 0; }
    
    /* Status Badges */
    .badge { padding: 4px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }
    .badge-pos { background: #dcfce7; color: #166534; }
    .badge-neg { background: #fee2e2; color: #991b1b; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# 2. DATA ENGINE
# ══════════════════════════════════════════
conn = st.connection("supabase", type=SupabaseConnection)
admin_email = st.session_state.get("user_email")

if not admin_email:
    st.error("🔒 Please log in to continue.")
    st.stop()

@st.cache_data(ttl=60)
def get_data(email):
    try:
        res = conn.client.table("form_responses").select("*").eq("admin_email", email).execute()
        return pd.DataFrame(res.data or [])
    except: return pd.DataFrame()

# ══════════════════════════════════════════
# 3. UI HELPERS (Para hindi magulo ang main code)
# ══════════════════════════════════════════
def create_kpi(label, value, subtext="", color="#1e293b"):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color: {color}">{value}</div>
            <div style="color: #94a3b8; font-size: 0.75rem;">{subtext}</div>
        </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# 4. MAIN DASHBOARD
# ══════════════════════════════════════════
def main():
    # Header Section
    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.title("📊 PUV Insights")
        st.caption("Commuter Sentiment & Service Quality Monitor")
    
    with col_h2:
        # Simplified Date Filter
        date_range = st.date_input("Analysis Period", [datetime.now() - timedelta(30), datetime.now()])

    df_raw = get_data(admin_email)
    if df_raw.empty:
        st.info("Waiting for data... Share your survey link to begin.")
        return

    # Processing (Simple filtering)
    df_raw['created_at'] = pd.to_datetime(df_raw['created_at']).dt.tz_localize(None)
    df = df_raw.copy() # Apply date filters here if date_range has 2 values

    # --- KPI RIBBON ---
    k1, k2, k3, k4 = st.columns(4)
    with k1: create_kpi("Total Responses", len(df), "Captured feedback")
    with k2: 
        pos_pct = (df['sentiment_status'] == 'POSITIVE').mean() * 100
        create_kpi("Positivity Rate", f"{pos_pct:.1f}%", "Overall satisfaction", "#059669")
    with k3:
        avg_score = df[['tangibles_avg', 'reliability_avg', 'assurance_avg']].mean().mean()
        create_kpi("Service Score", f"{avg_score:.2f}/5", "SERVQUAL average", "#d97706")
    with k4:
        pending = (df['sentiment_status'] == 'pending').sum()
        create_kpi("Pending AI", pending, "Queue for analysis", "#dc2626")

    st.write("---")

    # --- MAIN ANALYTICS ---
    tab_service, tab_sentiment, tab_raw = st.tabs(["🏗 Service Quality", "🧠 AI Sentiment", "📄 Raw Data"])

    with tab_service:
        col_s1, col_s2 = st.columns([1.5, 1])
        
        with col_s1:
            st.subheader("SERVQUAL Dimension Radar")
            # Logic for radar chart (Simplified)
            dims = ["Tangibles", "Reliability", "Responsiveness", "Assurance", "Empathy"]
            scores = [df[f"{d.lower()}_avg"].mean() for d in dims if f"{d.lower()}_avg" in df.columns]
            
            fig = go.Figure(data=go.Scatterpolar(r=scores, theta=dims, fill='toself', line_color='#1e293b'))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), height=400, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col_s2:
            st.subheader("Quick Breakdown")
            for d in dims:
                col_name = f"{d.lower()}_avg"
                if col_name in df.columns:
                    val = df[col_name].mean()
                    st.write(f"**{d}**")
                    st.progress(val/5)

    with tab_sentiment:
        st.subheader("Commuter Mood Tracker")
        sent_trend = df.groupby(df['created_at'].dt.date)['sentiment_status'].value_counts().unstack().fillna(0)
        st.area_chart(sent_trend)

    with tab_raw:
        st.subheader("Feedback Log")
        # Cleaner Table View
        st.dataframe(
            df[['created_at', 'raw_feedback', 'sentiment_status', 'sentiment_score']],
            column_config={
                "sentiment_status": st.column_config.TextColumn("Verdict"),
                "sentiment_score": st.column_config.ProgressColumn("AI Confidence", min_value=0, max_value=1)
            },
            hide_index=True, use_container_width=True
        )

if __name__ == "__main__":
    main()