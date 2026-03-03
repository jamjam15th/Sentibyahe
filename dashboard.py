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
    # Specific model for Taglish Sentiment
    model_path = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    return pipeline("sentiment-analysis", model=model_path, device=-1)

sentiment_analyzer = load_model()

@st.cache_data(ttl=2)
def fetch_live_data(email):
    try:
        q = conn.client.table("form_questions").select("*").eq("admin_email", email).execute()
        r = conn.client.table("form_responses").select("*").eq("admin_email", email).execute()
        return q.data, r.data
    except:
        return [], []

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

# Track the last count to prevent unnecessary AI re-processing
if "last_total_responses" not in st.session_state:
    st.session_state.last_total_responses = len(initial_responses)

tab1, tab2, tab3 = st.tabs(["💬 Sentiment Analysis", "📊 Quantitative Results", "👥 Demographics"])

# Containers to hold the content
with tab1:
    sel_text_q = st.selectbox("Select feedback question:", text_qs, key="text_static") if text_qs else None
    sentiment_spot = st.empty()

with tab2:
    sel_quant_q = st.selectbox("Select quantitative question:", quant_qs, key="quant_static") if quant_qs else None
    quant_spot = st.empty()

with tab3:
    demo_spot = st.empty()

# --- 5. THE DRAWING FUNCTION ---
def render_dashboard_content(responses):
    if not responses:
        return

    df_all = pd.DataFrame([r.get("answers", {}) for r in responses])
    
    # SAFER LABEL MAPPING
    # This handles both 'LABEL_0' and 'negative' formats
    label_map = {
        "LABEL_0": "NEGATIVE", "negative": "NEGATIVE",
        "LABEL_1": "NEUTRAL", "neutral": "NEUTRAL",
        "LABEL_2": "POSITIVE", "positive": "POSITIVE"
    }

    # --- TAB 1: SENTIMENT ---
    with sentiment_spot.container():
        if sel_text_q and sel_text_q in df_all.columns:
            valid_texts = df_all[sel_text_q].dropna().astype(str)
            valid_texts = valid_texts[valid_texts.str.strip() != ""]
            
            if not valid_texts.empty:
                results = []
                for t in valid_texts:
                    raw_res = sentiment_analyzer(t)[0]
                    # Fallback to the raw label if it's not in our map
                    clean_label = label_map.get(raw_res['label'], raw_res['label'].upper())
                    results.append({
                        "Feedback": t, 
                        "Sentiment": clean_label, 
                        "Score": round(raw_res['score'], 4)
                    })
                
                df_sent = pd.DataFrame(results)
                
                c1, c2 = st.columns([2, 1])
                sentiment_counts = df_sent['Sentiment'].value_counts()
                
                # Plot the graph
                c1.bar_chart(sentiment_counts, color="#4F8BF9")
                
                # Show metrics
                c2.metric("Total Analyzed", len(df_sent))
                if "POSITIVE" in sentiment_counts:
                    rate = (sentiment_counts["POSITIVE"] / len(df_sent)) * 100
                    c2.metric("Positive Rate", f"{rate:.1f}%")
                
                # Show the stable table
                st.dataframe(df_sent, use_container_width=True, hide_index=True, key=f"df_{len(responses)}")

    # --- TAB 2: QUANTITATIVE ---
    with quant_spot:
        if sel_quant_q and sel_quant_q in df_all.columns:
            q_counts = df_all[sel_quant_q].value_counts().sort_index()
            st.bar_chart(q_counts, color="#FF4B4B")
            st.dataframe(q_counts.reset_index(name="Votes"), hide_index=True)

    # --- TAB 3: DEMOGRAPHICS ---
    with demo_spot:
        if demo_qs:
            df_demo = df_all[demo_qs].dropna(how="all")
            st.dataframe(df_demo, use_container_width=True, hide_index=True)

# --- 6. EXECUTION LOGIC ---
# Initial Load
render_dashboard_content(initial_responses)

# Smart Refresh
@st.fragment(run_every=5)
def auto_refresh_fragment():
    _, current_responses = fetch_live_data(admin_email)
    # Check if a new row was added to the database
    if len(current_responses) != st.session_state.last_total_responses:
        st.session_state.last_total_responses = len(current_responses)
        render_dashboard_content(current_responses)

auto_refresh_fragment()