import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from transformers import pipeline

st.title("📊 Live Sentiment Dashboard")
st.write("Monitoring code-switched commuter feedback in real-time. Updates every 5 seconds.")

conn = st.connection("supabase", type=SupabaseConnection)

# --- 1. LOAD THE AI MODEL (CACHED ONCE) ---
# We keep the cache here so the heavy AI doesn't reload every 5 seconds!
@st.cache_resource(show_spinner="Loading NLP Model...")
def load_model():
    return pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

sentiment_analyzer = load_model()

# --- 2. THE REAL-TIME FRAGMENT ---
# This decorator makes this specific function loop silently in the background
@st.fragment(run_every=5)
def live_dashboard_view():
    
    # 1. Fetch fresh data from Supabase directly
    admin_email = st.session_state.get("user_email")
    questions_res = conn.client.table("form_questions").select("*").eq("admin_email", admin_email).execute()
    responses_res = conn.client.table("form_responses").select("*").eq("admin_email", admin_email).execute()
    
    schema = questions_res.data
    responses = responses_res.data

    if not responses:
        st.info("Waiting for commuters to submit feedback...")
        return # Stops the function here and tries again in 5 seconds

    # 2. Process the data
    flat_responses = [r.get("answers", {}) for r in responses]
    df_all = pd.DataFrame(flat_responses)

    demo_questions = [q["prompt"] for q in schema if q.get("is_demographic") == True]
    text_questions = [q["prompt"] for q in schema if q["q_type"] in ["Short Answer", "Paragraph"] and not q.get("is_demographic")]
    quant_questions = [q["prompt"] for q in schema if q["q_type"] in ["Multiple Choice", "Rating (1-5)"] and not q.get("is_demographic")]

    # 3. Draw the UI
    tab1, tab2, tab3 = st.tabs(["💬 Sentiment Analysis", "📊 Quantitative Results", "👥 Demographics"])

    with tab1:
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
                    st.metric("Total Analyzed", len(df_sentiment))
                    if "POSITIVE" in sentiment_counts:
                        pct = (sentiment_counts["POSITIVE"] / len(df_sentiment)) * 100
                        st.metric("Positive Rate", f"{pct:.1f}%")
                
                st.dataframe(df_sentiment, use_container_width=True, hide_index=True)

    with tab2:
        if not quant_questions:
            st.info("No quantitative questions available.")
        else:
            target_quant_q = st.selectbox("Select question to visualize:", quant_questions, key="quant_q")
            if target_quant_q in df_all.columns:
                quant_data = df_all[target_quant_q].dropna()
                if not quant_data.empty:
                    val_counts = quant_data.value_counts().sort_index()
                    st.bar_chart(val_counts, color="#FF4B4B")
                else:
                    st.warning("No answers yet.")

    with tab3:
        if not demo_questions:
            st.info("No demographic questions created.")
        else:
            df_demo = df_all[demo_questions].dropna(how="all")
            st.dataframe(df_demo, use_container_width=True, hide_index=True)

# --- 3. EXECUTE THE FRAGMENT ---
live_dashboard_view()