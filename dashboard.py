import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# 1. SETUP PAGE
st.set_page_config(page_title="Live Sentiment Dashboard", layout="wide")

# 2. CSS SHIELD (Stops flickering/dimming)
st.markdown("""
    <style>
    /* Prevents the 'seizure' flickering during refreshes */
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stFragment"]) {
        opacity: 1 !important;
    }
    
    /* Hide the default Streamlit menu buttons but KEEP the header bar */
    #MainMenu {visibility: hidden;}
    
    /* Ensure the sidebar toggle (the arrow) is visible and clickable */
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        display: flex !important;
    }
    </style>
""", unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection)

# 3. CACHED RESOURCES
@st.cache_resource(show_spinner="Loading NLP Engine...")
def load_model():
    from transformers import pipeline
    # Using your thesis-specific XLM-RoBERTa model
    model_path = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    return pipeline("sentiment-analysis", model=model_path, device=-1)

sentiment_analyzer = load_model()

@st.cache_data(ttl=5)
def fetch_data(email):
    q = conn.client.table("form_questions").select("*").eq("admin_email", email).execute()
    r = conn.client.table("form_responses").select("*").eq("admin_email", email).execute()
    return q.data, r.data

# 4. STATIC UI (WIDGETS OUTSIDE FRAGMENT)
st.title("📊 Live Sentiment Dashboard")
admin_email = st.session_state.get("user_email")

if not admin_email:
    st.error("Please log in to view the dashboard.")
    st.stop()

# Build UI structure once
schema, _ = fetch_data(admin_email)
text_qs = [q["prompt"] for q in schema if q["q_type"] in ["Short Answer", "Paragraph"] and not q.get("is_demographic")]
quant_qs = [q["prompt"] for q in schema if q["q_type"] in ["Multiple Choice", "Rating (1-5)"] and not q.get("is_demographic")]
demo_qs = [q["prompt"] for q in schema if q.get("is_demographic")]

tab1, tab2, tab3 = st.tabs(["💬 Sentiment Analysis", "📊 Quantitative Results", "👥 Demographics"])

with tab1:
    sel_text_q = st.selectbox("Select feedback question:", text_qs, key="text_static") if text_qs else None
    sentiment_spot = st.empty()

with tab2:
    sel_quant_q = st.selectbox("Select quantitative question:", quant_qs, key="quant_static") if quant_qs else None
    quant_spot = st.empty()

with tab3:
    demo_spot = st.empty()

# 5. THE LIVE FRAGMENT (UI UPDATES ONLY)
@st.fragment(run_every=5)
def live_update():
    _, responses = fetch_data(admin_email)
    
    if not responses:
        with sentiment_spot: st.info("Waiting for commuter feedback...")
        return
    
    df_all = pd.DataFrame([r.get("answers", {}) for r in responses])

    # Mapping CardiffNLP labels
    label_map = {"LABEL_0": "NEGATIVE", "LABEL_1": "NEUTRAL", "LABEL_2": "POSITIVE"}

    # --- UPDATE SENTIMENT TAB ---
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
            with sentiment_spot.container():
                c1, c2 = st.columns([2, 1])
                counts = df_sent['Sentiment'].value_counts()
                c1.bar_chart(counts, color="#4F8BF9")
                c2.metric("Total Responses", len(df_sent))
                if "POSITIVE" in counts:
                    c2.metric("Positive Rate", f"{(counts['POSITIVE']/len(df_sent))*100:.1f}%")
                
                st.dataframe(df_sent, use_container_width=True, hide_index=True)

    # --- UPDATE QUANTITATIVE TAB ---
    if sel_quant_q and sel_quant_q in df_all.columns:
        with quant_spot.container():
            counts = df_all[sel_quant_q].value_counts().sort_index()
            st.bar_chart(counts, color="#FF4B4B")
            st.dataframe(counts.reset_index(name="Votes"), hide_index=True)

    # --- UPDATE DEMOGRAPHICS TAB ---
    with demo_spot.container():
        if demo_qs:
            df_demo = df_all[demo_qs].dropna(how="all")
            st.dataframe(df_demo, use_container_width=True, hide_index=True)
            for d_q in demo_qs:
                st.caption(f"**{d_q}**")
                st.bar_chart(df_demo[d_q].value_counts(), height=150)

# Run the live update
live_update()