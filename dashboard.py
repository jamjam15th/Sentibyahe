import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# 1. SETUP PAGE
st.set_page_config(page_title="Live Sentiment Dashboard", layout="wide")

# 2. CSS SHIELD (Stops flickering and keeps the sidebar toggle visible)
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

# --- FORCE RESET ON PAGE LOAD ---
# This ensures the table draws immediately when you navigate from another page
if "page_init" not in st.session_state or st.session_state.page_init != "dashboard":
    st.session_state.last_total_responses = -1
    st.session_state.page_init = "dashboard"

conn = st.connection("supabase", type=SupabaseConnection)

# 3. CACHED RESOURCES
@st.cache_resource(show_spinner="Initializing AI Engine...")
def load_model():
    from transformers import pipeline
    # Path to your thesis model
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

# Build the layout structure once
schema, _ = fetch_live_data(admin_email)
text_qs = [q["prompt"] for q in schema if q["q_type"] in ["Short Answer", "Paragraph"] and not q.get("is_demographic")]
quant_qs = [q["prompt"] for q in schema if q["q_type"] in ["Multiple Choice", "Rating (1-5)"] and not q.get("is_demographic")]
demo_qs = [q["prompt"] for q in schema if q.get("is_demographic")]

tab1, tab2, tab3 = st.tabs(["💬 Sentiment Analysis", "📊 Quantitative Results", "👥 Demographics"])

with tab1:
    # Added an 'on_change' trigger so switching questions forces the AI to re-analyze
    sel_text_q = st.selectbox("Select feedback question:", text_qs, key="text_static", on_change=lambda: st.session_state.update({"last_total_responses": -1})) if text_qs else None
    sentiment_spot = st.empty() # Placeholder for smooth, non-jumping updates

with tab2:
    sel_quant_q = st.selectbox("Select quantitative question:", quant_qs, key="quant_static", on_change=lambda: st.session_state.update({"last_total_responses": -1})) if quant_qs else None
    quant_spot = st.empty()

with tab3:
    demo_spot = st.empty()

# 5. THE SMART FRAGMENT (Efficient, Conditional Rerunning)
@st.fragment(run_every=5)
def live_dashboard_view():
    # A. Quick database check for any NEW responses
    _, responses = fetch_live_data(admin_email)
    current_count = len(responses)
    
    # B. If no new data has arrived since the last draw, do nothing (STOPS FLICKERING)
    if current_count == st.session_state.last_total_responses:
        return
    
    # C. Data detected or page just loaded! Update state and process.
    st.session_state.last_total_responses = current_count
    
    if not responses:
        with sentiment_spot: st.info("Waiting for commuter feedback to begin analysis...")
        return

    # Process all raw answers into a DataFrame
    df_all = pd.DataFrame([r.get("answers", {}) for r in responses])
    
    # Mapping for CardiffNLP XLM-RoBERTa labels
    label_map = {"LABEL_0": "NEGATIVE", "LABEL_1": "NEUTRAL", "LABEL_2": "POSITIVE"}

    # --- UPDATE TAB 1: SENTIMENT ---
    with sentiment_spot.container():
        if sel_text_q and sel_text_q in df_all.columns:
            valid_texts = df_all[sel_text_q].dropna().astype(str)
            valid_texts = valid_texts[valid_texts.str.strip() != ""]
            
            if not valid_texts.empty:
                results = []
                for text in valid_texts:
                    # Run the AI model on each text entry
                    res = sentiment_analyzer(text)[0]
                    results.append({
                        "Commuter Feedback": text, 
                        "Sentiment": label_map.get(res['label'], res['label']), 
                        "Confidence": round(res['score'], 4)
                    })
                
                df_sent = pd.DataFrame(results)
                c1, c2 = st.columns([2, 1])
                counts = df_sent['Sentiment'].value_counts()
                c1.bar_chart(counts, color="#4F8BF9")
                c2.metric("Total Responses", len(df_sent))
                
                # Dynamic metric for Positive Rate
                if "POSITIVE" in counts:
                    pos_rate = (counts['POSITIVE'] / len(df_sent)) * 100
                    c2.metric("Positive Rate", f"{pos_rate:.1f}%")
                
                st.dataframe(df_sent, use_container_width=True, hide_index=True, key=f"sent_tbl_{current_count}")

    # --- UPDATE TAB 2: QUANTITATIVE ---
    with quant_spot.container():
        if sel_quant_q and sel_quant_q in df_all.columns:
            q_counts = df_all[sel_quant_q].value_counts().sort_index()
            st.bar_chart(q_counts, color="#FF4B4B")
            st.dataframe(q_counts.reset_index(name="Votes"), hide_index=True, key=f"quant_tbl_{current_count}")

    # --- UPDATE TAB 3: DEMOGRAPHICS ---
    with demo_spot.container():
        if demo_qs:
            df_demo = df_all[demo_qs].dropna(how="all")
            st.dataframe(df_demo, use_container_width=True, hide_index=True, key=f"demo_tbl_{current_count}")
            # Small breakdown charts for each demographic category
            for d_q in demo_qs:
                st.caption(f"**{d_q} Breakdown**")
                st.bar_chart(df_demo[d_q].value_counts(), height=150)

# Finally, execute the fragment
live_dashboard_view()