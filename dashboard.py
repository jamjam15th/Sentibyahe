import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

st.title("📊 Live Sentiment Dashboard")
st.write("Monitoring commuter feedback in real-time. Updates every 5 seconds.")

conn = st.connection("supabase", type=SupabaseConnection)

# --- 1. PROTECTIVE CACHING ---
# We cache the model so it doesn't reload on every fragment refresh
@st.cache_resource(show_spinner="Initializing AI Engine...")
def load_model():
    from transformers import pipeline
    return pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

sentiment_analyzer = load_model()

# We cache the database pull for 5 seconds to prevent overloading Supabase
@st.cache_data(ttl=5)
def fetch_live_supabase_data(admin_email):
    q_res = conn.client.table("form_questions").select("*").eq("admin_email", admin_email).execute()
    r_res = conn.client.table("form_responses").select("*").eq("admin_email", admin_email).execute()
    return q_res.data, r_res.data

# --- 2. THE FRAGMENT ENGINE ---
@st.fragment(run_every=5)
def live_dashboard_view():
    # Fetch Data
    admin_email = st.session_state.get("user_email")
    schema, responses = fetch_live_supabase_data(admin_email)

    if not responses:
        st.info("Waiting for commuters to submit feedback...")
        return 

    # Process Data
    flat_responses = [r.get("answers", {}) for r in responses]
    df_all = pd.DataFrame(flat_responses)

    # Smart Sorting based on Schema
    demo_questions = [q["prompt"] for q in schema if q.get("is_demographic")]
    text_questions = [q["prompt"] for q in schema if q["q_type"] in ["Short Answer", "Paragraph"] and not q.get("is_demographic")]
    quant_questions = [q["prompt"] for q in schema if q["q_type"] in ["Multiple Choice", "Rating (1-5)"] and not q.get("is_demographic")]

    # --- THE TABS (Inside the Fragment) ---
    tab1, tab2, tab3 = st.tabs(["💬 Sentiment Analysis", "📊 Quantitative Results", "👥 Demographics"])

    # TAB 1: SENTIMENT
    with tab1:
        st.header("Sentiment Analysis")
        if not text_questions:
            st.info("No text-based questions available.")
        else:
            target_text_q = st.selectbox("Select question to analyze:", text_questions, key="sent_q")
            valid_texts = df_all[target_text_q].dropna().astype(str)
            valid_texts = valid_texts[valid_texts.str.strip() != ""]
            
            if valid_texts.empty:
                st.warning("No answers submitted for this question yet.")
            else:
                analysis_results = []
                for text in valid_texts:
                    ai_result = sentiment_analyzer(text)[0]
                    analysis_results.append({
                        "Commuter Feedback": text,
                        "Sentiment": ai_result['label'].upper(),
                        "Confidence": round(ai_result['score'], 4)
                    })
                
                df_sentiment = pd.DataFrame(analysis_results)
                col1, col2 = st.columns([1, 1])
                with col1:
                    sentiment_counts = df_sentiment['Sentiment'].value_counts()
                    st.bar_chart(sentiment_counts, color="#4F8BF9")
                with col2:
                    st.metric("Total Responses", len(df_sentiment))
                    if "POSITIVE" in sentiment_counts:
                        pct = (sentiment_counts["POSITIVE"] / len(df_sentiment)) * 100
                        st.metric("Positive Rate", f"{pct:.1f}%")
                
                st.dataframe(df_sentiment, use_container_width=True, hide_index=True)

    # TAB 2: QUANTITATIVE
    with tab2:
        st.header("Quantitative Data")
        if not quant_questions:
            st.info("No multiple choice or rating questions available.")
        else:
            target_quant_q = st.selectbox("Select question to visualize:", quant_questions, key="quant_q")
            if target_quant_q in df_all.columns:
                quant_data = df_all[target_quant_q].dropna()
                val_counts = quant_data.value_counts().sort_index()
                st.bar_chart(val_counts, color="#FF4B4B")
                st.dataframe(val_counts.reset_index(name="Votes"), hide_index=True)

    # TAB 3: DEMOGRAPHICS
    with tab3:
        st.header("Commuter Profile")
        if not demo_questions:
            st.info("No demographic questions created.")
        else:
            df_demo = df_all[demo_questions].dropna(how="all")
            st.dataframe(df_demo, use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("Demographic Breakdown")
            # Create a simple grid for demographic charts
            for demo_q in demo_questions:
                st.write(f"**{demo_q}**")
                counts = df_demo[demo_q].value_counts()
                st.bar_chart(counts, height=200)

# --- 3. RUN THE VIEW ---
live_dashboard_view()