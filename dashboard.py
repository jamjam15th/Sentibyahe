import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from transformers import pipeline

st.title("📊 Complete Survey Dashboard")
st.write("Analyze sentiment, view quantitative ratings, and review commuter demographics.")

conn = st.connection("supabase", type=SupabaseConnection)

@st.cache_resource(show_spinner="Loading NLP Model...")
def load_model():
    return pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

sentiment_analyzer = load_model()

def fetch_data():
    # Grab the currently logged-in admin's email
    admin_email = st.session_state.user_email
    
    # FILTER: Only pull questions and responses belonging to this specific admin
    questions = conn.client.table("form_questions").select("*").eq("admin_email", admin_email).execute()
    responses = conn.client.table("form_responses").select("*").eq("admin_email", admin_email).execute()
    
    return questions.data, responses.data

schema, responses = fetch_data()

if not responses:
    st.info("No commuter feedback has been submitted yet.")
    st.stop()

flat_responses = [r.get("answers", {}) for r in responses]
df_all = pd.DataFrame(flat_responses)

# --- SMART SORTING FROM THE DATABASE ---
# We read the "is_demographic" flag directly from Supabase!
demo_questions = [q["prompt"] for q in schema if q.get("is_demographic") == True]
text_questions = [q["prompt"] for q in schema if q["q_type"] in ["Short Answer", "Paragraph"] and not q.get("is_demographic")]
quant_questions = [q["prompt"] for q in schema if q["q_type"] in ["Multiple Choice", "Rating (1-5)"] and not q.get("is_demographic")]

# --- THE TABS ---
tab1, tab2, tab3 = st.tabs(["💬 Sentiment Analysis", "📊 Quantitative Results", "👥 Demographics"])

# ==========================================
# TAB 1: SENTIMENT ANALYSIS 
# ==========================================
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
            with st.spinner("Running AI Sentiment Analysis..."):
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
                st.subheader("Sentiment Distribution")
                sentiment_counts = df_sentiment['Sentiment'].value_counts()
                st.bar_chart(sentiment_counts, color="#4F8BF9")
            with col2:
                st.subheader("Metrics")
                st.metric("Total Analyzed", len(df_sentiment))
                if "POSITIVE" in sentiment_counts:
                    pct = (sentiment_counts["POSITIVE"] / len(df_sentiment)) * 100
                    st.metric("Positive Rate", f"{pct:.1f}%")
            
            st.divider()
            st.subheader("Raw AI Results")
            st.dataframe(df_sentiment, use_container_width=True, hide_index=True)


# ==========================================
# TAB 2: QUANTITATIVE RESULTS
# ==========================================
with tab2:
    st.header("Quantitative Data")
    if not quant_questions:
        st.info("No multiple choice or rating questions available.")
    else:
        target_quant_q = st.selectbox("Select question to visualize:", quant_questions, key="quant_q")
        quant_data = df_all[target_quant_q].dropna()
        
        if quant_data.empty:
            st.warning("No answers submitted for this question yet.")
        else:
            st.subheader("Response Distribution")
            val_counts = quant_data.value_counts().sort_index()
            st.bar_chart(val_counts, color="#FF4B4B")
            st.dataframe(val_counts.reset_index(name="Votes"), hide_index=True)


# ==========================================
# TAB 3: DEMOGRAPHICS
# ==========================================
with tab3:
    st.header("Commuter Profile")
    if not demo_questions:
        st.info("No demographic questions have been created yet.")
    else:
        st.write("Overview of respondent demographics:")
        df_demo = df_all[demo_questions].dropna(how="all")
        st.dataframe(df_demo, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("Demographic Breakdown")
        cols = st.columns(len(demo_questions))
        for i, demo_q in enumerate(demo_questions):
            with cols[i]:
                st.caption(f"**{demo_q}**")
                demo_counts = df_demo[demo_q].value_counts()
                if len(demo_counts) < 20: 
                    st.bar_chart(demo_counts)
                else:
                    st.write("*(Too many unique entries to graph)*")