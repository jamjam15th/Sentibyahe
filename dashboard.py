import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# 1. Page Config
st.set_page_config(page_title="Live Sentiment Dashboard", layout="wide")

# 2. CSS Shield: This stops the 'seizure' flicker and the gray overlay
st.markdown("""
    <style>
    /* Keeps the app from dimming during fragment refreshes */
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stFragment"]) {
        opacity: 1 !important;
    }
    /* Optional: Hides the 'Running...' spinner in the top right for a cleaner look */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection)

# --- 3. PROTECTIVE CACHING ---
@st.cache_resource(show_spinner="Initializing AI Engine...")
def load_model():
    from transformers import pipeline
    # Use your XLM-RoBERTa path here later
    return pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

sentiment_analyzer = load_model()

@st.cache_data(ttl=5)
def fetch_live_supabase_data(admin_email):
    q_res = conn.client.table("form_questions").select("*").eq("admin_email", admin_email).execute()
    r_res = conn.client.table("form_responses").select("*").eq("admin_email", admin_email).execute()
    return q_res.data, r_res.data

# --- 4. STATIC UI ELEMENTS (These do not flicker) ---
st.title("📊 Live Sentiment Dashboard")
st.write("Real-time commuter analytics. Tables and charts update seamlessly.")

admin_email = st.session_state.get("user_email")

# Fetch schema once to build the tabs/selectors
schema, initial_responses = fetch_live_supabase_data(admin_email)

# TABS stay OUTSIDE the fragment so they don't reset
tab1, tab2, tab3 = st.tabs(["💬 Sentiment Analysis", "📊 Quantitative Results", "👥 Demographics"])

# --- 5. THE SMOOTH FRAGMENT ENGINE ---
@st.fragment(run_every=5)
def live_dashboard_view():
    # Fetch fresh data
    _, responses = fetch_live_supabase_data(admin_email)

    if not responses:
        st.info("Waiting for commuters to submit feedback...")
        return 

    flat_responses = [r.get("answers", {}) for r in responses]
    df_all = pd.DataFrame(flat_responses)

    # Sorting logic
    demo_questions = [q["prompt"] for q in schema if q.get("is_demographic")]
    text_questions = [q["prompt"] for q in schema if q["q_type"] in ["Short Answer", "Paragraph"] and not q.get("is_demographic")]
    quant_questions = [q["prompt"] for q in schema if q["q_type"] in ["Multiple Choice", "Rating (1-5)"] and not q.get("is_demographic")]

    # --- TAB 1: SENTIMENT (Smooth) ---
    with tab1:
        if text_questions:
            target_text_q = st.selectbox("Select question to analyze:", text_questions, key="sent_q_static")
            
            # Use placeholders for the visuals so they don't jump
            chart_placeholder = st.empty()
            table_placeholder = st.empty()

            valid_texts = df_all[target_text_q].dropna().astype(str)
            valid_texts = valid_texts[valid_texts.str.strip() != ""]
            
            if not valid_texts.empty:
                analysis_results = []
                for text in valid_texts:
                    ai_result = sentiment_analyzer(text)[0]
                    analysis_results.append({
                        "Commuter Feedback": text,
                        "Sentiment": ai_result['label'].upper(),
                        "Confidence": round(ai_result['score'], 4)
                    })
                
                df_sentiment = pd.DataFrame(analysis_results)
                
                with chart_placeholder.container():
                    col1, col2 = st.columns([1, 1])
                    sentiment_counts = df_sentiment['Sentiment'].value_counts()
                    col1.bar_chart(sentiment_counts, color="#4F8BF9")
                    col2.metric("Total Analyzed", len(df_sentiment))
                
                with table_placeholder.container():
                    st.dataframe(df_sentiment, use_container_width=True, hide_index=True, key="sent_table_smooth")

    # --- TAB 2: QUANTITATIVE (Smooth) ---
    with tab2:
        if quant_questions:
            target_quant_q = st.selectbox("Select question to visualize:", quant_questions, key="quant_q_static")
            quant_placeholder = st.empty()
            
            if target_quant_q in df_all.columns:
                quant_data = df_all[target_quant_q].dropna()
                with quant_placeholder.container():
                    val_counts = quant_data.value_counts().sort_index()
                    st.bar_chart(val_counts, color="#FF4B4B")
                    st.dataframe(val_counts.reset_index(name="Votes"), hide_index=True, key="quant_table_smooth")

    # --- TAB 3: DEMOGRAPHICS (Smooth) ---
    with tab3:
        if demo_questions:
            demo_placeholder = st.empty()
            with demo_placeholder.container():
                df_demo = df_all[demo_questions].dropna(how="all")
                st.dataframe(df_demo, use_container_width=True, hide_index=True, key="demo_table_smooth")
                
                st.divider()
                # Draw small charts for demographics
                for demo_q in demo_questions:
                    st.caption(f"**{demo_q}**")
                    st.bar_chart(df_demo[demo_q].value_counts(), height=150)

# Run the smooth view
live_dashboard_view()