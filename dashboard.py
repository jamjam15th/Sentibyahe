import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# 1. SETUP PAGE
st.set_page_config(page_title="Live Sentiment Dashboard", layout="wide")

# 2. CSS SHIELD
st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stFragment"]) {
        opacity: 1 !important;
    }
    #MainMenu {visibility: hidden;}
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        display: flex !important;
    }
    </style>
""", unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection)

# 3. CACHED RESOURCES
@st.cache_resource(show_spinner="Initializing AI Engine...")
def load_model():
    from transformers import pipeline
    model_path = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    return pipeline("sentiment-analysis", model=model_path, device=-1)

sentiment_analyzer = load_model()

@st.cache_data(ttl=2)
def fetch_live_data(email):
    q = conn.client.table("form_questions").select("*").eq("admin_email", email).execute()
    r = conn.client.table("form_responses").select("*").eq("admin_email", email).execute()
    return q.data, r.data

# 4. STATIC UI SETUP
st.title("📊 Smart Sentiment Dashboard")
admin_email = st.session_state.get("user_email")

if not admin_email:
    st.error("Please log in to view the dashboard.")
    st.stop()

# --- INITIAL DATA FETCH ---
schema, initial_responses = fetch_live_data(admin_email)
text_qs = [q["prompt"] for q in schema if q["q_type"] in ["Short Answer", "Paragraph"] and not q.get("is_demographic")]
quant_qs = [q["prompt"] for q in schema if q["q_type"] in ["Multiple Choice", "Rating (1-5)"] and not q.get("is_demographic")]
demo_qs = [q["prompt"] for q in schema if q.get("is_demographic")]

# Initialize the counter to the current database state immediately
st.session_state.last_total_responses = len(initial_responses)

tab1, tab2, tab3 = st.tabs(["💬 Sentiment Analysis", "📊 Quantitative Results", "👥 Demographics"])

# Placeholders
with tab1:
    sel_text_q = st.selectbox("Select feedback question:", text_qs, key="text_static") if text_qs else None
    sentiment_spot = st.container() # Using container instead of empty for better persistence

with tab2:
    sel_quant_q = st.selectbox("Select quantitative question:", quant_qs, key="quant_static") if quant_qs else None
    quant_spot = st.container()

with tab3:
    demo_spot = st.container()

# --- 5. THE DRAWING FUNCTION (Used by both Initial Load and Fragment) ---
def render_dashboard_content(responses):
    if not responses:
        st.info("Waiting for commuter feedback...")
        return

    df_all = pd.DataFrame([r.get("answers", {}) for r in responses])
    label_map = {"LABEL_0": "NEGATIVE", "LABEL_1": "NEUTRAL", "LABEL_2": "POSITIVE"}

    # TAB 1: SENTIMENT
    with sentiment_spot:
        if sel_text_q and sel_text_q in df_all.columns:
            valid_texts = df_all[sel_text_q].dropna().astype(str)
            valid_texts = valid_texts[valid_texts.str.strip() != ""]
            if not valid_texts.empty:
                results = [
                    {"Feedback": t, "Sentiment": label_map.get(sentiment_analyzer(t)[0]['label']), "Score": round(sentiment_analyzer(t)[0]['score'], 4)}
                    for t in valid_texts
                ]
                df_sent = pd.DataFrame(results)
                c1, c2 = st.columns([2, 1])
                c1.bar_chart(df_sent['Sentiment'].value_counts(), color="#4F8BF9")
                c2.metric("Total", len(df_sent))
                st.dataframe(df_sent, use_container_width=True, hide_index=True)

    # TAB 2: QUANTITATIVE
    with quant_spot:
        if sel_quant_q and sel_quant_q in df_all.columns:
            st.bar_chart(df_all[sel_quant_q].value_counts().sort_index(), color="#FF4B4B")

    # TAB 3: DEMOGRAPHICS
    with demo_spot:
        if demo_qs:
            st.dataframe(df_all[demo_qs].dropna(how="all"), use_container_width=True, hide_index=True)

# --- 6. EXECUTION LOGIC ---
# First Draw: Happens immediately on page switch
render_dashboard_content(initial_responses)

# Smart Refresh: Only updates if new data arrives
@st.fragment(run_every=5)
def auto_refresh_fragment():
    _, current_responses = fetch_live_data(admin_email)
    if len(current_responses) != st.session_state.last_total_responses:
        st.session_state.last_total_responses = len(current_responses)
        render_dashboard_content(current_responses)

auto_refresh_fragment()