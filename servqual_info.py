import streamlit as st
from st_supabase_connection import SupabaseConnection
from components import inject_css, render_dimension_cards

# ══════════════════════════════════════════
# PAGE CONFIG & CSS
# ══════════════════════════════════════════
st.set_page_config(page_title="SERVQUAL Guide", page_icon="ℹ️", layout="wide")

st.session_state["current_page"] = "servqual_info"
st.session_state["_prev_page"] = "servqual_info"

# 🔥 THE NUCLEAR FULL-PAGE LOADER (WITH SIDEBAR FIX) 🔥
# Must go BEFORE Supabase connections and inject_css()
st.markdown("""
<style>
    /* Hide Streamlit's Deploy button and toolbar */
    # [data-testid="stToolbar"] {
    #     display: none !important;
    # }
    # #MainMenu {
    #     display: none !important;
    # }
    # header[data-testid="stHeader"] {
    #     display: none !important;
    # }
            
    /* 1. KEEP SIDEBAR ON TOP OF LOADER */
    [data-testid="stSidebar"], 
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 999999999 !important; /* Highest priority */
    }

    .stAppDeployButton { display: none !important; }

    /* 2. COMPLETELY HIDE THE APP ROOT */
    /* visibility: hidden is bulletproof against React hydration overrides */
    .stApp [data-testid="stAppViewBlockContainer"] {
        visibility: hidden !important;
        animation: snapVisible 0.1s forwards 2.5s !important; /* 2.5 seconds wait */
    }

    /* 3. OVERLAY THAT COVERS EVERYTHING ELSE */
    #nuclear-loader {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: #f0f4f8; /* Matched to your app background */
        z-index: 999999998; /* Exactly one layer BELOW the sidebar */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        animation: fadeOutNuclear 0.4s ease-out 2.5s forwards; /* Matches the 2.5s wait */
    }

    .spinner {
        border: 4px solid #ffffff;
        border-top: 4px solid #1a2e55;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 0.8s linear infinite;
        margin-bottom: 15px;
    }

    .loading-text {
        color: #1a2e55;
        font-weight: 600;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
    }

    /* 4. KEYFRAMES */
    @keyframes snapVisible {
        to { visibility: visible !important; }
    }

    @keyframes fadeOutNuclear {
        0% { opacity: 1; visibility: visible; }
        100% { opacity: 0; visibility: hidden; display: none; }
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>

<div id="nuclear-loader">
    <div class="spinner"></div>
    <div class="loading-text">Loading Info...</div>
</div>
""", unsafe_allow_html=True)

inject_css()

# ══════════════════════════════════════════
# SUPABASE SETUP
# ══════════════════════════════════════════
conn = st.connection("supabase", type=SupabaseConnection)

# ══════════════════════════════════════════
# PAGE CONTENT
# ══════════════════════════════════════════
st.markdown("""
<style>
.servqual-intro {
    background: linear-gradient(135deg, rgba(26, 50, 99, 0.05) 0%, rgba(255, 197, 112, 0.05) 100%);
    border: 1px solid rgba(26, 50, 99, 0.1);
    border-radius: 8px;
    padding: 2rem;
    margin-bottom: 2rem;
}

.servqual-intro h1 {
    color: #1a2e55;
    margin-top: 0;
}

.servqual-intro p {
    color: #54778e;
    font-size: 1.05rem;
    line-height: 1.6;
}

.dimension-section {
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="servqual-intro">
    <h1>ℹ️ SERVQUAL Framework</h1>
    <p>
    The <strong>SERVQUAL</strong> model is a widely-recognized framework for measuring service quality. 
    It evaluates customer perceptions across five key dimensions to help you understand and improve your service delivery.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("### The Five Dimensions")
st.markdown("""
Service quality is measured through these five critical dimensions:
""")

render_dimension_cards()

st.markdown("---")

st.markdown("### How to Use SERVQUAL in Your Survey")
st.markdown("""
When creating survey questions in the **Form Builder**:

1. **Assign Dimensions**: Tag each question with the relevant SERVQUAL dimension
2. **Track Sentiment**: Enable sentiment analysis to understand respondent feelings
3. **Analyze Results**: View aggregated scores by dimension in the **Sentiment Dashboard**
4. **Identify Gaps**: Compare perceptions vs. expectations to find improvement areas

This helps you systematically evaluate and enhance your service quality.
""")

st.markdown("---")

st.markdown("### Resources")
st.markdown("""
- **Tangibles** 📍: Physical facilities, equipment, and appearance
- **Reliability** ✅: Ability to perform services accurately and dependably
- **Responsiveness** ⚡: Willingness to help and provide prompt service
- **Assurance** 🛡️: Knowledge, courtesy, and ability to inspire confidence
- **Empathy** 💙: Individualized attention and understanding of customer needs

Use these dimensions as you design your survey to ensure comprehensive quality assessment.
""")