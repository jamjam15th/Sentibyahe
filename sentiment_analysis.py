# sentiment_analysis.py — Analysis (playground, batch upload, model comparison)
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from st_supabase_connection import SupabaseConnection

from sentiment_compare_utils import (
    COMPARISON_MODEL_CHOICES,
    OUR_MODEL_DISPLAY_NAME,
    normalize_comparison_prediction,
)

# ══════════════════════════════════════════
# PAGE CONFIG & CSS THEME
# ══════════════════════════════════════════
st.set_page_config(
    page_title="Analysis | Land public transportation",
    page_icon="🧠",
    layout="wide",
)

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
    import os
    
    try:
        # Use online model in production, local for development
        use_online = os.getenv("USE_ONLINE_MODEL", "false").lower() == "true"
        
        if not use_online:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            local_model_path = os.path.join(script_dir, "model")
            
            if os.path.exists(local_model_path) and os.path.exists(os.path.join(local_model_path, "model.safetensors")):
                model_path = local_model_path
            else:
                model_path = "jamjam15th/land-public-transportation-model-2"
        else:
            model_path = "jamjam15th/land-public-transportation-model-2"
        
        return transformers.pipeline(
            "sentiment-analysis",
            model=model_path,
            tokenizer=model_path,
            top_k=None,
            device=-1
        )
    except Exception as e:
        st.error(f"❌ Model failed to load: {e}")
        st.stop()


@st.cache_resource(show_spinner="Loading comparison model…")
def load_comparison_pipeline(model_id: str):
    import transformers
    return transformers.pipeline("sentiment-analysis", model=model_id, device=-1)


classifier = load_sentiment_model()

conn = st.connection("supabase", type=SupabaseConnection)

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
        <h1>🧠 Analysis</h1>
        <p>Run <strong>fine-tuned XLM-RoBERTa</strong> on text or files, or open <strong>Compare Models</strong> to see how our model performs against industry baseline models on your feedback (English, Tagalog, or mixed).</p>
    </div>
</div>
""", unsafe_allow_html=True)

tab_single, tab_batch, tab_compare = st.tabs(
    ["Try one comment", "Upload a file", "Compare Models"]
)

# ─── helper: unwrap top_k=None output ([[{...}]]) into a flat list of dicts ───
def _unwrap(raw):
    if isinstance(raw, list) and len(raw) > 0 and isinstance(raw[0], list):
        return raw[0]
    if isinstance(raw, list):
        return raw
    return [raw]

with tab_single:
    st.write("**Type a short comment (English, Tagalog, or Taglish):**")
    user_input = st.text_area("", placeholder="Example: Sobrang init sa loob ng jeep...", height=120, label_visibility="collapsed")
    
    if st.button("🚀 Analyze Sentiment"):
        if user_input.strip():
            # 🧠 Brain 1: Sentiment Analysis
            results = _unwrap(classifier(user_input.strip()))
            scores_dict = {
                label_map.get(res["label"], str(res["label"]).capitalize()): res["score"]
                for res in results
            }

            top_sentiment = max(scores_dict, key=scores_dict.get)
            top_score = scores_dict[top_sentiment]
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        # Using columns for desktop, Streamlit automatically stacks these on mobile
        col1, col2 = st.columns([1, 1.2])
            
        with col1:
            st.markdown(f"""
            <div class="result-card {top_sentiment}">
                <div class="res-title">{OUR_MODEL_DISPLAY_NAME}</div>
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
    st.info("Upload a CSV or Excel file with a column named **feedback** (one comment per row).")
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        # Detect file type
        is_csv = uploaded_file.type == "text/csv" or uploaded_file.name.endswith(".csv")
        st.session_state.batch_is_csv = is_csv
        
        if is_csv:
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        if 'feedback' in df.columns:
            # Show Process Batch button only if not yet processed
            if "batch_df" not in st.session_state:
                if st.button("Process Batch"):
                    sentiments = []
                    confidences = []
                    
                    for text in df["feedback"].astype(str):
                        # 🧠 Brain 1: Sentiment Analysis
                        seq = _unwrap(classifier(text))
                        top_res = max(seq, key=lambda x: x["score"])
                        sentiments.append(label_map.get(top_res["label"], str(top_res["label"]).capitalize()))
                        confidences.append(round(top_res["score"], 4))
                    
                    df['Sentiment'] = sentiments
                    df['Sentiment Confidence'] = confidences
                    st.session_state.batch_df = df
                    
                    st.success("✅ Batch processing complete!")
                    st.rerun()
            
            # Show results and download button if processed
            if "batch_df" in st.session_state:
                df = st.session_state.batch_df
                st.dataframe(df.head(10), use_container_width=True)
                
                is_csv = st.session_state.get("batch_is_csv", True)
                
                if is_csv:
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Annotated",
                        data=csv_data,
                        file_name="sentiment_dimension_results.csv",
                        mime="text/csv",
                    )
                else:
                    from io import BytesIO
                    excel_buffer = BytesIO()
                    df.to_excel(excel_buffer, index=False, engine='openpyxl')
                    excel_data = excel_buffer.getvalue()
                    st.download_button(
                        label="📥 Download Annotated",
                        data=excel_data,
                        file_name="sentiment_dimension_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                
                # Option to reset and upload new file
                if st.button("📤 Upload Different File"):
                    st.session_state.pop("batch_df", None)
                    st.session_state.pop("batch_is_csv", None)
                    st.rerun()
        else:
            st.error("⚠️ The uploaded file must contain a column named exactly 'feedback'.")


with tab_compare:
    st.markdown("### 🤖 Upload Feedback to Compare Models")
    
    st.markdown("""
    **Why use this?**
    
    Compare how our fine-tuned XLM-RoBERTa model performs against a baseline model of your choice. This helps you:
    - Verify model accuracy on your specific feedback domain
    - Understand how our model compares to industry standard models
    - Identify cases where models disagree (potential edge cases or ambiguous sentiment)
    - Make informed decisions about model reliability for your use case
    """)
    
    st.info("Upload a CSV or Excel file with a **feedback** column and select a baseline model to compare.")
    
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"], key="model_compare_upload")
    
    if uploaded_file is not None:
        # Store file data in session state for consistent reads across model selections
        if "comparison_file_data" not in st.session_state or st.session_state.comparison_file_name != uploaded_file.name:
            st.session_state.comparison_file_data = uploaded_file.getvalue()
            st.session_state.comparison_file_name = uploaded_file.name
            st.session_state.comparison_file_is_csv = uploaded_file.type == "text/csv" or uploaded_file.name.endswith(".csv")
        
        # Read file fresh from stored data (ensures clean dataframe each time)
        import io
        if st.session_state.comparison_file_is_csv:
            df = pd.read_csv(io.BytesIO(st.session_state.comparison_file_data))
        else:
            df = pd.read_excel(io.BytesIO(st.session_state.comparison_file_data))
        
        if 'feedback' not in df.columns:
            st.error("⚠️ File must have a column named exactly **feedback**")
        else:
            # ═══════════════════════════════════════════════════════════════
            # SELECT BASELINE MODEL
            # ═══════════════════════════════════════════════════════════════
            st.subheader("Step 1: Select a Baseline Model")
            
            # Create display labels without "Baseline — " prefix
            model_options = {i: model for i, model in enumerate(COMPARISON_MODEL_CHOICES)}
            model_display = {i: model["user_label"].split(" — ")[1] if " — " in model["user_label"] else model["user_label"] for i, model in model_options.items()}
            
            selected_idx = st.selectbox(
                "Choose a baseline model to compare against our model",
                options=list(model_options.keys()),
                format_func=lambda idx: model_display[idx],
                key="baseline_model_select"
            )
            selected_model = model_options[selected_idx]
            
            st.subheader(f"📊 Analyzing {len(df)} feedback comments...")
            
            if st.button("🔍 Run Comparison", type="primary", key="run_comparison"):
                from transformers import pipeline as hf_pipeline
                
                # Create a fresh dataframe with ONLY feedback column (ensures no old predictions)
                fresh_df = df[["feedback"]].copy()
                
                # Run OUR model
                our_predictions = []
                our_confidences = []
                
                for text in fresh_df["feedback"].astype(str):
                    seq = _unwrap(classifier(text))
                    top_res = max(seq, key=lambda x: x["score"])
                    our_predictions.append(label_map.get(top_res["label"], str(top_res["label"]).capitalize()))
                    our_confidences.append(round(top_res["score"], 4))
                
                fresh_df[f"{OUR_MODEL_DISPLAY_NAME} Prediction"] = our_predictions
                fresh_df[f"{OUR_MODEL_DISPLAY_NAME} Confidence"] = our_confidences
                
                # Run SELECTED baseline model
                baseline_name = selected_model["user_label"].split(" — ")[0]
                model_id = selected_model["model_id"]
                kind = selected_model["kind"]
                
                try:
                    baseline_pipe = hf_pipeline("sentiment-analysis", model=model_id)
                    baseline_preds = []
                    baseline_confs = []
                    
                    for text in fresh_df["feedback"].astype(str):
                        try:
                            res = baseline_pipe(text[:512])[0]
                            sent, conf = normalize_comparison_prediction(kind, res)
                            baseline_preds.append(sent)
                            baseline_confs.append(round(conf, 4))
                        except:
                            baseline_preds.append("NEUTRAL")
                            baseline_confs.append(0.0)
                    
                    fresh_df[f"{baseline_name} Prediction"] = baseline_preds
                    fresh_df[f"{baseline_name} Confidence"] = baseline_confs
                    
                except Exception as e:
                    st.error(f"Could not load model: {e}")
                    st.stop()
                
                st.session_state.comparison_df = fresh_df
                st.session_state.comparison_baseline = baseline_name
                st.session_state.comparison_our_model = OUR_MODEL_DISPLAY_NAME
                st.success("✅ Comparison complete!")
                st.rerun()
            
            if "comparison_df" in st.session_state:
                df_results = st.session_state.comparison_df
                our_col = f"{st.session_state.comparison_our_model} Prediction"
                baseline_col = f"{st.session_state.comparison_baseline} Prediction"
                our_conf_col = f"{st.session_state.comparison_our_model} Confidence"
                baseline_conf_col = f"{st.session_state.comparison_baseline} Confidence"
                
                # ═══════════════════════════════════════════════════════════════
                # 1. DETAILED PREDICTION TABLE
                # ═══════════════════════════════════════════════════════════════
                st.subheader("📋 Detailed Predictions Comparison")
                
                display_cols = ["feedback", our_col, our_conf_col, baseline_col, baseline_conf_col]
                display_df = df_results[display_cols].head(15)
                st.dataframe(display_df, use_container_width=True, height=400)
                
                # ═══════════════════════════════════════════════════════════════
                # 2. AGREEMENT METRICS
                # ═══════════════════════════════════════════════════════════════
                st.subheader("🎯 Model Comparison Metrics")
                
                # Normalize both to uppercase for fair comparison
                matches = (df_results[our_col].str.upper() == df_results[baseline_col].str.upper()).sum()
                match_pct = (matches / len(df_results) * 100) if len(df_results) > 0 else 0
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        f"{st.session_state.comparison_our_model}",
                        "Our Model",
                        ""
                    )
                with col2:
                    st.metric(
                        f"{st.session_state.comparison_baseline}",
                        "Selected Baseline",
                        ""
                    )
                
                st.divider()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Agreement Rate", f"{match_pct:.1f}%", f"{matches}/{len(df_results)} cases")
                with col2:
                    disagreement_count = len(df_results) - matches
                    st.metric("Disagreement Rate", f"{100-match_pct:.1f}%", f"{disagreement_count}/{len(df_results)} cases")
                
                # ═══════════════════════════════════════════════════════════════
                # 3. DISAGREEMENT CASES
                # ═══════════════════════════════════════════════════════════════
                if match_pct < 100:
                    st.subheader("⚡ Cases Where Models Disagree")
                    
                    # Normalize both columns for comparison
                    disagreement_mask = df_results[our_col].str.upper() != df_results[baseline_col].str.upper()
                    disagreement_cases = df_results[disagreement_mask][["feedback", our_col, baseline_col]].head(10)
                    
                    if len(disagreement_cases) > 0:
                        st.dataframe(
                            disagreement_cases.rename(columns={
                                our_col: f"{st.session_state.comparison_our_model}",
                                baseline_col: f"{st.session_state.comparison_baseline}"
                            }),
                            use_container_width=True,
                            height=350
                        )
                    else:
                        st.success("All models agree on all feedback! 🎉")
                else:
                    st.success("✅ Perfect agreement! All predictions match!")
                
                # ═══════════════════════════════════════════════════════════════
                # 4. SENTIMENT DISTRIBUTION COMPARISON
                # ═══════════════════════════════════════════════════════════════
                st.subheader("📈 Sentiment Distribution")
                
                dist_data = {
                    st.session_state.comparison_our_model: df_results[our_col].value_counts(),
                    st.session_state.comparison_baseline: df_results[baseline_col].value_counts()
                }
                
                dist_df = pd.DataFrame(dist_data).fillna(0).astype(int)
                st.bar_chart(dist_df)
                
                # ═══════════════════════════════════════════════════════════════
                # 5. DOWNLOAD RESULTS
                # ═══════════════════════════════════════════════════════════════
                st.subheader("💾 Export Results")
                csv_data = df_results.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Comparison Results (CSV)",
                    data=csv_data,
                    file_name="model_comparison_results.csv",
                    mime="text/csv",
                )
                
                # Reset button
                if st.button("🔄 Try Different Model"):
                    st.session_state.pop("comparison_df", None)
                    st.rerun()