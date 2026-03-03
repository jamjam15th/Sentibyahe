import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# 1. SETUP PAGE
st.set_page_config(page_title="Live Sentiment Dashboard", layout="wide")

# 2. CSS SHIELD (Stops flickering/dimming)
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

# Initialize a counter in session state
if "last_response_count" not in st.session_state:
    st.session_state.last_response_count = 0

# 3. CACHED RESOURCES
@st.cache_resource(show_spinner="Loading NLP Engine...")
def load_model():
    from transformers import pipeline
    model_path = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    return pipeline("sentiment-analysis", model=model_path, device=-1)

sentiment_analyzer = load_model()

# We set TTL to 0 here because the Fragment will handle the timing
@st.cache_data(ttl=2) 
def fetch_data(email):
    q = conn.client.table("form_questions").select("*").eq("admin_email", email).execute()
    r = conn.client.table("form_responses").select("*").eq("admin_email", email).execute()
    return q.data, r.data

# 4. STATIC UI
st.title("📊 Smart Sentiment Dashboard")
admin_email = st.session_state.get("user_email")

if not admin_email:
    st.error("Please log in.")
    st.stop()

schema, _ = fetch_data(admin_email)
text_qs = [q["prompt"] for q in schema if q["q_type"] in ["Short Answer", "Paragraph"] and not q.get("is_demographic")]
quant_qs = [q["prompt"] for q in schema if q["q_type"] in ["Multiple Choice", "Rating (1-5)"] and not q.get("is_demographic")]
demo_qs = [q["prompt"] for q in schema if q.get("is_demographic")]

tab1, tab2, tab3 = st.tabs(["💬 Sentiment Analysis", "📊 Quantitative Results", "👥 Demographics"])

# Create permanent placeholders for the content
with tab1:
    sel_text_q = st.selectbox("Select feedback question:", text_qs, key="text_static") if text_qs else None
    sentiment_spot = st.empty()

with tab2:
    sel_quant_q = st.selectbox("Select quantitative question:", quant_qs, key="quant_static") if quant_qs else None
    quant_spot = st.empty()

with tab3:
    demo_spot = st.empty()

# 5. THE SMART FRAGMENT
@st.fragment(run_every=5)
def live_update():
    # 1. Quick fetch to check the count
    _, responses = fetch_data(admin_email)
    current_count = len(responses)
    
    # 2. ONLY proceed if the count has changed
    if current_count == st.session_state.last_response_count:
        # No new data? Do nothing and wait for next 5s check.
        return
    
    # 3. If data is new, update the counter and process
    st.session_state.last_response_count = current_count
    
    df_all = pd.DataFrame([r.get("answers", {}) for r in responses])
    label_map = {"LABEL_0": "NEGATIVE", "LABEL_1": "NEUTRAL", "LABEL_2": "POSITIVE"}

    # --- UPDATE UI (Using your existing logic) ---
    with sentiment_spot.container():
        if sel_text_q and sel_text_q in df_all.columns:
            valid_texts = df_all[sel_text_q].dropna().astype(str)
            valid_texts = valid_texts[valid_texts.str.strip() != ""]
            if not valid_texts.empty:
                results = []
                for text in valid_texts:
                    res = sentiment_analyzer(text)[0]
                    results.append({
                        "Feedback": text, 
                        "Sentiment": label_map.get(res['label'], res['label']), 
                        "Confidence": round(res['score'], 4)
                    })
                df_sent = pd.DataFrame(results)
                c1, c2 = st.columns([2, 1])
                counts = df_sent['Sentiment'].value_counts()
                c1.bar_chart(counts, color="#4F8BF9")
                c2.metric("Total Responses", len(df_sent), delta=len(df_sent) - st.session_state.get('prev_total', 0))
                st.session_state.prev_total = len(df_sent)
                st.dataframe(df_sent, use_container_width=True, hide_index=True)

    with quant_spot.container():
        if sel_quant_q and sel_quant_q in df_all.columns:
            counts = df_all[sel_quant_q].value_counts().sort_index()
            st.bar_chart(counts, color="#FF4B4B")

    with demo_spot.container():
        if demo_qs:
            st.dataframe(df_all[demo_qs].dropna(how="all"), use_container_width=True, hide_index=True)

live_update()