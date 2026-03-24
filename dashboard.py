import streamlit as st
import pandas as pd
import altair as alt
from st_supabase_connection import SupabaseConnection

# ══════════════════════════════════════════
# 1. SETUP & CSS SHIELD (Daanalytics Theme)
# ══════════════════════════════════════════
st.set_page_config(page_title="Live Sentiment Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Mulish:wght@300;400;500;600;700&display=swap');

:root {
    --navy:   rgb(26, 50, 99);
    --gold:   rgb(255, 197, 112);
    --steel:  rgb(84, 119, 146);
    --card:   #ffffff;
    --bdr:    rgba(84,119,146,0.2);
    --pos:    #4a7c59; 
    --neu:    #8b9dc3; 
    --neg:    #b03a2e; 
}

*, html, body, p, span, div { font-family: 'Mulish', sans-serif !important; }
.stApp { background-color: #f0f4f8; }

/* 🌟 UNIQUE PREMIUM HEADER 🌟 */
.premium-header {
    background: linear-gradient(135deg, var(--navy) 0%, rgb(40, 75, 140) 100%);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 25px rgba(26,50,99,0.15);
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.premium-header h1 { 
    font-family: 'Libre Baskerville', serif !important; 
    color: #ffffff !important; 
    margin: 0; 
    font-size: 2.2rem; 
}
.live-badge { 
    background: rgba(255, 255, 255, 0.15); 
    color: var(--gold); 
    padding: 6px 14px; 
    border-radius: 20px; 
    font-weight: 700; 
    font-size: 0.8rem; 
    letter-spacing: 0.05em; 
    display: flex; 
    align-items: center; 
    gap: 8px;
    border: 1px solid rgba(255, 197, 112, 0.3);
}
.live-dot { 
    height: 8px; width: 8px; 
    background-color: var(--gold); 
    border-radius: 50%; 
    display: inline-block; 
    animation: pulse 1.5s infinite; 
}
@keyframes pulse { 0% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,197,112,0.7); } 50% { opacity: 0.5; box-shadow: 0 0 0 6px rgba(255,197,112,0); } 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,197,112,0); } }

/* KPI Cards */
.kpi-container { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.kpi-card {
    flex: 1; background: var(--card); border: 1px solid var(--bdr); border-radius: 8px;
    padding: 1.2rem; box-shadow: 0 2px 8px rgba(26,50,99,0.04);
}
.kpi-title { font-size: 0.8rem; font-weight: 700; color: var(--steel); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
.kpi-value { font-family: 'Libre Baskerville', serif !important; font-size: 2rem; font-weight: 700; color: var(--navy); }

/* Fix fragment flashing */
div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stFragment"]) { opacity: 1 !important; transition: none !important; }
#MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection)

# ══════════════════════════════════════════
# 2. CACHED AI & DATA RESOURCES
# ══════════════════════════════════════════
@st.cache_resource(show_spinner="Initializing XLM-RoBERTa...")
def load_model():
    from transformers import pipeline
    model_path = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    return pipeline("sentiment-analysis", model=model_path, device=-1)

sentiment_analyzer = load_model()

@st.cache_data(ttl=2)
def fetch_live_data(email):
    try:
        q = conn.client.table("form_questions").select("*").eq("admin_email", email).order("sort_order").execute()
        r = conn.client.table("form_responses").select("*").eq("admin_email", email).execute()
        return q.data, r.data
    except Exception:
        return [], []

@st.cache_data(max_entries=5000, show_spinner=False)
def analyze_single_text(text):
    raw_res = sentiment_analyzer(text)[0]
    label_map = {"LABEL_0": "NEGATIVE", "negative": "NEGATIVE", "LABEL_1": "NEUTRAL", "neutral": "NEUTRAL", "LABEL_2": "POSITIVE", "positive": "POSITIVE"}
    clean_label = label_map.get(raw_res['label'], str(raw_res['label']).upper())
    return clean_label, round(raw_res['score'], 4)

def color_sentiment(val):
    if val == "POSITIVE": return 'color: #4a7c59; font-weight: bold;'
    elif val == "NEGATIVE": return 'color: #b03a2e; font-weight: bold;'
    elif val == "NEUTRAL": return 'color: #8b9dc3; font-weight: bold;'
    return ''

# ══════════════════════════════════════════
# 3. STATIC UI SETUP
# ══════════════════════════════════════════
admin_email = st.session_state.get("user_email")
if not admin_email:
    st.error("🔒 Please log in to view the dashboard.")
    st.stop()

st.markdown("""
<div class="premium-header">
    <div>
        <h1>Smart Sentiment Dashboard</h1>
    </div>
    <div class="live-badge"><span class="live-dot"></span> LIVE SYNC ACTIVE</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# 4. THE LIVE FRAGMENT (Auto-Updates)
# ══════════════════════════════════════════
@st.fragment(run_every=5)
def render_live_dashboard():
    schema, current_responses = fetch_live_data(admin_email)
    
    seen_prompts = set()
    def make_unique(p):
        unique_p = p
        counter = 1
        while unique_p in seen_prompts:
            unique_p = f"{p} ({counter})"
            counter += 1
        seen_prompts.add(unique_p)
        return unique_p

    text_qs, quant_qs, demo_qs = [], [], []

    for q in schema:
        unique_p = make_unique(q["prompt"])
        if q.get("is_demographic"): demo_qs.append(unique_p)
        elif q.get("q_type") in ["Short Answer", "Paragraph"]: text_qs.append(unique_p)
        elif q.get("q_type") in ["Multiple Choice", "Rating (Likert)", "Rating (1-5)"]: quant_qs.append(unique_p)

    standard_demos = [
        "What is your age bracket?", "What is your gender?", 
        "What is your primary occupation?", "What primary PUV type do you usually ride?", 
        "How often do you commute?"
    ]
    for d in standard_demos:
        if d not in demo_qs: demo_qs.append(make_unique(d))

    answers_list = [r.get("answers", {}) for r in current_responses if isinstance(r.get("answers", {}), dict)]
    df_all = pd.DataFrame(answers_list)
    
    # --- KPI RIBBON ---
    k1, k2, k3 = st.columns(3)
    k1.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Commuters</div><div class="kpi-value">{len(current_responses)}</div></div>', unsafe_allow_html=True)
    
    pos_rate_spot = k2.empty()
    top_concern_spot = k3.empty()

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["💬 Sentiment Analysis", "📊 Quantitative Results", "👥 Demographics"])

    if df_all.empty:
        with tab1: st.info("Waiting for commuters to submit feedback...")
        with tab2: st.info("Waiting for commuters to submit feedback...")
        with tab3: st.info("Waiting for commuters to submit feedback...")
        return

    with tab1:
        valid_text_qs = [q for q in text_qs if q in df_all.columns]
        if not valid_text_qs:
            st.info("No open-ended feedback received for these questions yet.")
        else:
            sel_text_q = st.selectbox("Filter by Feedback Question:", valid_text_qs, key="tq")
            valid_texts = df_all[sel_text_q].dropna().astype(str)
            valid_texts = valid_texts[valid_texts.str.strip() != ""]
            
            if valid_texts.empty:
                st.info("No valid text responses for this question yet.")
            else:
                results = [{"Feedback": t, "Sentiment": l, "Confidence": s} for t in valid_texts for l, s in [analyze_single_text(t)]]
                
                if results:
                    df_sent = pd.DataFrame(results)
                    sentiment_counts = df_sent['Sentiment'].value_counts()
                    
                    if "POSITIVE" in sentiment_counts:
                        rate = (sentiment_counts["POSITIVE"] / len(df_sent)) * 100
                        pos_rate_spot.markdown(f'<div class="kpi-card"><div class="kpi-title">Overall Positivity</div><div class="kpi-value" style="color:var(--pos);">{rate:.1f}%</div></div>', unsafe_allow_html=True)
                    else:
                        pos_rate_spot.markdown('<div class="kpi-card"><div class="kpi-title">Overall Positivity</div><div class="kpi-value">0.0%</div></div>', unsafe_allow_html=True)
                        
                    top_val = sentiment_counts.idxmax() if not sentiment_counts.empty else "N/A"
                    top_concern_spot.markdown(f'<div class="kpi-card"><div class="kpi-title">Most Common Sentiment</div><div class="kpi-value">{top_val}</div></div>', unsafe_allow_html=True)

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown("**Sentiment Distribution**")
                        # ⭐️ ALTAIR FIX IS HERE: No more StreamlitColorLengthError! ⭐️
                        plot_df = sentiment_counts.reset_index()
                        plot_df.columns = ['Sentiment', 'Count']
                        
                        chart = alt.Chart(plot_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                            x=alt.X('Sentiment:N', sort=['POSITIVE', 'NEUTRAL', 'NEGATIVE'], axis=alt.Axis(labelAngle=0)),
                            y=alt.Y('Count:Q'),
                            color=alt.Color('Sentiment:N', scale=alt.Scale(
                                domain=['POSITIVE', 'NEUTRAL', 'NEGATIVE'],
                                range=['#4a7c59', '#8b9dc3', '#b03a2e']
                            ), legend=None),
                            tooltip=['Sentiment', 'Count']
                        )
                        st.altair_chart(chart, use_container_width=True)
                    
                    with c2:
                        st.markdown("**Recent Feedback Log**")
                        styled_df = df_sent.style.map(color_sentiment, subset=['Sentiment'])
                        st.dataframe(styled_df, use_container_width=True, hide_index=True, height=350)
                else:
                    st.info("No feedback could be processed by the AI.")

    with tab2:
        valid_quant_qs = [q for q in quant_qs if q in df_all.columns]
        if not valid_quant_qs:
            st.info("No ratings or multiple choice answers received yet.")
        else:
            sel_quant_q = st.selectbox("Analyze Quantitative Question:", valid_quant_qs, key="qq")
            q_counts = df_all[sel_quant_q].value_counts().sort_index()
            
            c1, c2 = st.columns([2, 1])
            with c1:
                # Upgraded to Altair for better visuals
                plot_df2 = q_counts.reset_index()
                plot_df2.columns = ['Answer', 'Votes']
                chart2 = alt.Chart(plot_df2).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#ffc570").encode(
                    x=alt.X('Answer:N', axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('Votes:Q'),
                    tooltip=['Answer', 'Votes']
                )
                st.altair_chart(chart2, use_container_width=True)
                
            with c2:
                st.dataframe(q_counts.reset_index(name="Votes").rename(columns={sel_quant_q: "Answer"}), hide_index=True, use_container_width=True)

    with tab3:
        valid_demo_qs = [q for q in demo_qs if q in df_all.columns]
        if not valid_demo_qs:
            st.info("No demographic responses received yet.")
        else:
            st.markdown("**Commuter Demographics Database**")
            df_demo = df_all[valid_demo_qs].dropna(how="all")
            st.dataframe(df_demo, use_container_width=True, hide_index=True)

render_live_dashboard()