import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
from transformers import pipeline

st.title("📊 Live Sentiment Dashboard")

conn = st.connection("supabase", type=SupabaseConnection)

@st.cache_resource(show_spinner="Loading NLP Model...")
def load_model():
    return pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

sentiment_analyzer = load_model()

# --- 1. NIKULSINH'S TRICK: TTL CACHING ---
# Memorize the database pull for 5 seconds to protect Supabase from crashing
@st.cache_data(ttl=5)
def fetch_live_supabase_data(admin_email):
    q_res = conn.client.table("form_questions").select("*").eq("admin_email", admin_email).execute()
    r_res = conn.client.table("form_responses").select("*").eq("admin_email", admin_email).execute()
    return q_res.data, r_res.data

# --- 2. THE FRAGMENT ENGINE ---
# Automatically refresh this specific part of the screen every 5 seconds
@st.fragment(run_every=5)
def live_dashboard_view():
    
    # Calls the cached function! 
    schema, responses = fetch_live_supabase_data(st.session_state.user_email)

    if not responses:
        st.info("Waiting for commuters to submit feedback...")
        return 

    flat_responses = [r.get("answers", {}) for r in responses]
    df_all = pd.DataFrame(flat_responses)

    # (The rest of your charting and tab logic goes here exactly as before...)
    st.write("Data loaded successfully! Total responses:", len(responses))

live_dashboard_view()