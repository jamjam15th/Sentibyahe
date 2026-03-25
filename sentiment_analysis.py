# sentiment_sandbox.py
import pandas as pd
import streamlit as st
from st_supabase_connection import SupabaseConnection

# ══════════════════════════════════════════
# PAGE CONFIG & CSS THEME
# ══════════════════════════════════════════
st.set_page_config(page_title="Sentiment Sandbox | Daanalytics", page_icon="🧠", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Mulish:wght@300;400;500;600;700&display=swap');

:root {
    --navy:   rgb(26, 50, 99);
    --gold:   rgb(255, 197, 112);
    --steel:  rgb(84, 119, 146);
    --card:   #ffffff;
    --bdr:    rgba(84,119,146,0.2);
    --pos:    #4a7c59; /* Green */
    --neu:    #8b9dc3; /* Muted Blue */
    --neg:    #b03a2e; /* Red */
}

*, html, body, p, span, div { font-family: 'Mulish', sans-serif !important; }
.stApp { background-color: #f0f4f8; }

/* 🌟 UNIQUE PREMIUM HEADER 🌟 */
.premium-header {
    background: linear-gradient(135deg, var(--navy) 0%, rgb(40, 75, 140) 100%);
    border-radius: 12px;
    padding: 2.5rem 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 25px rgba(26,50,99,0.15);
    color: white;
}
.premium-header h1 { 
    font-family: 'Libre Baskerville', serif !important; 
    color: #ffffff !important; 
    margin: 0 0 0.5rem 0; 
    font-size: 2.2rem; 
}
.premium-header p { 
    color: #b0bcd8; 
    margin: 0; 
    font-size: 1rem; 
}

/* Result Cards */
.result-card {
    background: var(--card); border: 1px solid var(--bdr); border-radius: 10px;
    padding: 1.5rem; text-align: center; box-shadow: 0 4px 15px rgba(26,50,99,0.05);
}
.result-card.Positive { border-bottom: 6px solid var(--pos); }
.result-card.Negative { border-bottom: 6px solid var(--neg); }
.result-card.Neutral  { border-bottom: 6px solid var(--neu); }

.res-title { font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--steel); }
.res-sentiment { font-family: 'Libre Baskerville', serif !important; font-size: 2.2rem; font-weight: 700; margin: 0.5rem 0; }
.res-sentiment.Positive { color: var(--pos); }
.res-sentiment.Negative { color: var(--neg); }
.res-sentiment.Neutral  { color: var(--neu); }

/* Distribution Bars */
.dist-row { display: flex; align-items: center; margin-bottom: 0.5rem; }
.dist-label { width: 80px; font-size: 0.8rem; font-weight: 700; color: var(--steel); text-align: right; margin-right: 15px; }
.dist-bar-bg { flex: 1; background: #e0e6ed; height: 10px; border-radius: 5px; overflow: hidden; }
.dist-bar-fill { height: 100%; border-radius: 5px; transition: width 0.4s ease; }
.fill-Positive { background: var(--pos); }
.fill-Negative { background: var(--neg); }
.fill-Neutral  { background: var(--neu); }
.dist-pct { width: 50px; font-size: 0.8rem; font-weight: 700; color: var(--navy); text-align: right; margin-left: 10px; }

/* 📱 RESPONSIVE MOBILE FIXES 📱 */
@media screen and (max-width: 768px) {
    .premium-header {
        padding: 1.5rem 1.2rem !important;
        margin-bottom: 1.2rem !important;
    }
    .premium-header h1 {
        font-size: 1.6rem !important;
    }
    .premium-header p {
        font-size: 0.9rem !important;
    }
    .res-sentiment {
        font-size: 1.8rem !important;
    }
    .dist-label {
        width: 65px !important;
        font-size: 0.7rem !important;
        margin-right: 10px !important;
    }
    .dist-pct {
        width: 45px !important;
        font-size: 0.7rem !important;
    }
}

/* Text Area */
[data-testid="stTextArea"] textarea { border: 1.5px solid var(--bdr) !important; border-radius: 8px !important; font-size: 1rem !important; }
[data-testid="stTextArea"] textarea:focus { border-color: var(--navy) !important; box-shadow: 0 0 0 2px rgba(26,50,99,0.1) !important; }

/* Buttons */
div.stButton > button {
    background: var(--navy) !important; color: var(--gold) !important;
    font-weight: 700 !important; letter-spacing: 0.05em !important;
    border-radius: 6px !important; padding: 0.5rem 2rem !important;
    border: none !important; transition: all 0.2s !important;
    width: 100% !important; /* Fully responsive button */
}
div.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 4px 12px rgba(26,50,99,0.2) !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# MODEL LOADING
# ══════════════════════════════════════════
@st.cache_resource 
def load_sentiment_model():
    import transformers
    model_path = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    return transformers.pipeline("sentiment-analysis", model=model_path, top_k=None, device=-1)

with st.spinner("Initializing XLM-RoBERTa Model..."):
    classifier = load_sentiment_model()

label_map = {
    "LABEL_0": "Negative", "LABEL_1": "Neutral", "LABEL_2": "Positive",
    "negative": "Negative", "neutral": "Neutral", "positive": "Positive"
}
emoji_map = {"Positive": "😊", "Neutral": "😐", "Negative": "😠"}

# ══════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════
st.markdown("""
<div class="premium-header">
    <div>
        <h1>🧠 Sentiment Engine</h1>
        <p>Analyze English, Tagalog, and Taglish PUV commuter feedback.</p>
    </div>
</div>
""", unsafe_allow_html=True)

tab_single, tab_batch = st.tabs(["🧪 Playground", "📁 Batch Processing"])

with tab_single:
    st.write("**Enter Commuter Feedback:**")
    user_input = st.text_area("", placeholder="Example: Sobrang init sa loob ng jeep...", height=120, label_visibility="collapsed")
    
    if st.button("🚀 Analyze Sentiment"):
        if user_input.strip():
            results = classifier(user_input)[0] 
            scores_dict = {label_map.get(res['label'], str(res['label']).capitalize()): res['score'] for res in results}     

            top_sentiment = max(scores_dict, key=scores_dict.get)
            top_score = scores_dict[top_sentiment]
            
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            # Using columns for desktop, Streamlit automatically stacks these on mobile
            col1, col2 = st.columns([1, 1.2])
            
            with col1:
                st.markdown(f"""
                <div class="result-card {top_sentiment}">
                    <div class="res-title">Primary Sentiment</div>
                    <div class="res-sentiment {top_sentiment}">{top_sentiment} {emoji_map[top_sentiment]}</div>
                    <div style="color: var(--steel); font-size: 0.85rem;">Confidence: <strong>{top_score*100:.1f}%</strong></div>
                </div>
                """, unsafe_allow_html=True)
                
            with col2:
                st.markdown("<div style='padding-top: 15px;'><strong>📊 Probability Distribution</strong></div>", unsafe_allow_html=True)
                for sent in ["Positive", "Neutral", "Negative"]:
                    pct = scores_dict.get(sent, 0) * 100
                    st.markdown(f"""
                    <div class="dist-row">
                        <div class="dist-label">{sent}</div>
                        <div class="dist-bar-bg"><div class="dist-bar-fill fill-{sent}" style="width: {pct}%;"></div></div>
                        <div class="dist-pct">{pct:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
            if top_sentiment == "Positive":
                st.balloons()
        else:
            st.warning("⚠️ Please enter some text to analyze.")

with tab_batch:
    st.info("Upload a CSV file containing a column named **'feedback'**.")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if 'feedback' in df.columns:
            if st.button("Process Batch"):
                with st.spinner(f"Analyzing {len(df)} rows..."):
                    sentiments = []
                    confidences = []
                    for text in df['feedback'].astype(str):
                        res = classifier(text)[0]
                        top_res = max(res, key=lambda x: x['score'])
                        sentiments.append(label_map[top_res['label']])
                        confidences.append(round(top_res['score'], 4))
                    
                    df['Sentiment'] = sentiments
                    df['Confidence'] = confidences
                    
                st.success("✅ Batch processing complete!")
                st.dataframe(df.head(10), use_container_width=True) # use_container_width for responsiveness
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Annotated CSV",
                    data=csv,
                    file_name="sentiment_results.csv",
                    mime="text/csv",
                )
        else:
            st.error("⚠️ The uploaded CSV must contain a column named exactly 'feedback'.")