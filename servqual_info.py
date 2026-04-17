import streamlit as st
from st_supabase_connection import SupabaseConnection
from components import inject_css, render_dimension_cards

# ══════════════════════════════════════════
# PAGE CONFIG & CSS
# ══════════════════════════════════════════
st.set_page_config(page_title="SERVQUAL Info", page_icon="ℹ️", layout="wide")
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
