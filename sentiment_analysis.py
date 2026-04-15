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
        if os.path.exists("model"):
            model_path = "model"
        else:
            model_path = "jamjam15th/fine-tuned-land-public-transportation"
        
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


with st.spinner(f"Loading {OUR_MODEL_DISPLAY_NAME}…"):
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
        <p>Run <strong>fine-tuned XLM-RoBERTa</strong> on text or files, or open <strong>Our model vs baselines</strong> to see how your saved labels compare with other standard models on the same respondent comments (English, Tagalog, or mixed).</p>
    </div>
</div>
""", unsafe_allow_html=True)

tab_single, tab_batch, tab_compare = st.tabs(
    ["Try one comment", "Upload a file", "Our model vs baselines"]
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
    st.info("Upload a CSV file with a column named **feedback** (one comment per row).")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if 'feedback' in df.columns:
            if st.button("Process Batch"):
                with st.spinner(f"Analyzing {len(df)} rows..."):
                    sentiments = []
                    confidences = []
                    for text in df["feedback"].astype(str):
                        seq = _unwrap(classifier(text))
                        top_res = max(seq, key=lambda x: x["score"])
                        sentiments.append(label_map.get(top_res["label"], str(top_res["label"]).capitalize()))
                        confidences.append(round(top_res["score"], 4))
                    
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


with tab_compare:
    st.markdown(
        f"""
**Our model vs baselines — what this tab is for**

1. **Model Comparison Overview** - This section presents a **side-by-side comparison** between our fine-tuned sentiment analysis model and baseline models. The goal is to evaluate how effectively each model classifies feedback related to **land public transportation**.

2. **Purpose of Comparison** - The comparison demonstrates why our model is **better suited** for transportation sentiment analysis and allows users to see the **strengths and weaknesses** of each approach.

3. **Models Included** - **Fine-tuned Model (Primary Model):** A customized model trained on **transportation-related data** to improve **accuracy** and **contextual understanding**. - **Baseline Models:** General-purpose sentiment models used as **benchmarks** for comparison.

4. **Evaluation Criteria** - Models are evaluated based on **accuracy** in sentiment classification (**positive, neutral, negative**), ability to understand **transportation-related context**, and **consistency** across feedback samples.

5. **Why Results May Differ** - Differences occur due to variations in **training datasets**, **model architecture**, and level of **domain-specific fine-tuning**. General models may misinterpret **transportation-related terms**, while the fine-tuned model is **optimized for this domain**.
        """
    )

    admin = st.session_state.get("user_email")
    if not admin:
        st.warning("Please **log in** from the main app first. We only load comments from **your** respondents' submissions.")
    else:
        dc1, dc2 = st.columns(2)
        with dc1:
            cmp_from = st.date_input(
                "From date",
                value=datetime.today() - timedelta(days=30),
                key="cmp_date_from",
            )
        with dc2:
            cmp_to = st.date_input(
                "To date",
                value=datetime.today(),
                key="cmp_date_to",
            )

        try:
            r = (
                conn.client.table("form_responses")
                .select("*")
                .eq("admin_email", admin)
                .order("created_at")
                .execute()
            )
            df_all = pd.DataFrame(r.data or [])
        except Exception as e:
            df_all = pd.DataFrame()
            st.error(f"Could not load your responses: {e}")

        if df_all.empty:
            st.info("No survey responses found yet. Collect some answers from your public link, then come back here.")
        else:
            if "created_at" in df_all.columns:
                df_all["created_at"] = pd.to_datetime(
                    df_all["created_at"], utc=True, errors="coerce"
                ).dt.tz_localize(None)
                mask = (df_all["created_at"].dt.date >= cmp_from) & (
                    df_all["created_at"].dt.date <= cmp_to
                )
                df_win = df_all.loc[mask].copy()
            else:
                df_win = df_all.copy()

            if df_win.empty:
                st.info("No responses fall in the dates you picked. Try a wider **From / To** range.")
            else:
                sent_col = "sentiment_status"
                if sent_col not in df_win.columns or "raw_feedback" not in df_win.columns:
                    st.info("Your data does not include mood labels or comment text yet.")
                else:
                    ok_sent = df_win[sent_col].isin(["POSITIVE", "NEUTRAL", "NEGATIVE"])
                    txt = df_win["raw_feedback"].astype(str).str.strip()
                    df_use = df_win[ok_sent & txt.ne("")].copy()
                    if df_use.empty:
                        st.info("No labeled comments with text in this date range.")
                    else:
                        pick_label = st.selectbox(
                            "Which baseline model should we run on the same comments?",
                            [c["user_label"] for c in COMPARISON_MODEL_CHOICES],
                            key="cmp_model_pick",
                        )
                        choice = next(
                            c for c in COMPARISON_MODEL_CHOICES if c["user_label"] == pick_label
                        )
                        model_b_id = choice["model_id"]
                        kind_b = choice["kind"]

                        nmax = len(df_use)

                        presets = [1, 5, 10, 25, 50, 75, 100, 150, 200, 300, 500]
                        count_choices = sorted({c for c in presets if 1 <= c <= nmax} | {nmax})
                        if not count_choices:
                            count_choices = [max(1, nmax)]

                        def _limit_label(n: int) -> str:
                            if n >= nmax:
                                return f"All {nmax} comment(s) in this date range (newest first)"
                            return f"Only the {n} newest comment(s) — skip the older {nmax - n}"

                        limit_pairs = [(n, _limit_label(n)) for n in count_choices]
                        default_n = min(50, nmax)
                        default_i = min(
                            range(len(limit_pairs)),
                            key=lambda i: abs(limit_pairs[i][0] - default_n),
                        )
                        pick_lbl = st.selectbox(
                            "How many comments should we send to the baseline model?",
                            [lbl for _, lbl in limit_pairs],
                            index=default_i,
                            key="cmp_limit_pick",
                            help="Starts from the latest submission and works backward. Smaller numbers run faster.",
                        )
                        max_cmp = next(n for n, lbl in limit_pairs if lbl == pick_lbl)

                        if st.button("Run comparison", type="primary", key="cmp_run_btn"):
                            rows_cmp = []
                            if "created_at" in df_use.columns:
                                sub = df_use.sort_values("created_at", ascending=False).head(max_cmp)
                            else:
                                sub = df_use.head(max_cmp)

                            with st.spinner("Loading the baseline model and scoring your comments…"):
                                pipe_b = load_comparison_pipeline(model_b_id)
                                for _, row in sub.iterrows():
                                    txtv = str(row.get("raw_feedback") or "").strip()
                                    if not txtv:
                                        continue
                                    lab_a = str(row.get(sent_col) or "").strip().upper()
                                    if lab_a not in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
                                        continue
                                    raw_b = pipe_b(txtv[:512])
                                    seq_b = raw_b if isinstance(raw_b, list) else [raw_b]
                                    res_b = max(seq_b, key=lambda x: x["score"])
                                    lab_b, sc_b = normalize_comparison_prediction(kind_b, res_b)
                                    rows_cmp.append(
                                        {
                                            f"Ours ({OUR_MODEL_DISPLAY_NAME})": lab_a,
                                            "Baseline model": lab_b,
                                            "Baseline confidence": f"{sc_b * 100:.1f}%",
                                            "Same label?": "Yes" if lab_a == lab_b else "No",
                                            "Comment (short)": (txtv[:400] + "…") if len(txtv) > 400 else txtv,
                                            "When": row.get("created_at"),
                                        }
                                    )

                            cmp_df = pd.DataFrame(rows_cmp)
                            if cmp_df.empty:
                                st.warning("Nothing to compare in this slice.")
                            else:
                                agree = cmp_df["Same label?"] == "Yes"
                                agree_pct = 100.0 * float(agree.mean())
                                m1, m2, m3 = st.columns(3)
                                m1.metric("Comments compared", len(cmp_df))
                                m2.metric("Baseline agreed with ours", f"{agree_pct:.0f}%")
                                m3.metric("Baseline disagreed", int((~agree).sum()))

                                col_ours = f"Ours ({OUR_MODEL_DISPLAY_NAME})"
                                st.subheader("Match summary")
                                st.caption(
                                    f"Each cell counts how many comments got that **{OUR_MODEL_DISPLAY_NAME}** label (row) and that **baseline** label (column). "
                                    "The diagonal is where **both models agreed**. Off-diagonal cells are **disagreements** — often worth reading when the text is Tagalog or mixed."
                                )
                                ct = pd.crosstab(
                                    cmp_df[col_ours],
                                    cmp_df["Baseline model"],
                                    margins=True,
                                )
                                st.dataframe(ct, use_container_width=True)

                                dis = cmp_df[cmp_df["Same label?"] == "No"].copy()
                                if not dis.empty:
                                    st.subheader("Comments where the baseline disagreed")
                                    st.caption(
                                        f"Same text, two models — **{OUR_MODEL_DISPLAY_NAME}** (what the app saved) vs the **baseline** you picked. Read each line to see which label feels right for your respondents' wording."
                                    )
                                    st.dataframe(
                                        dis.drop(columns=["Same label?"]),
                                        use_container_width=True,
                                        hide_index=True,
                                        height=min(480, 80 + 28 * len(dis)),
                                    )

                                st.caption(
                                    "The first time you use a baseline, download can take a minute. Nothing here rewrites your database — saved sentiment stays from **fine-tuned XLM-RoBERTa**."
                                )

    with st.expander("Quick guide (for anyone using this tab)", expanded=False):
        st.markdown(
            f"""
**Understanding the Comparison Interface**

This page provides a comparative analysis of two sentiment classifications for a given piece of feedback: the results from our **Fine-tuned XLM-RoBERTa** (the primary model used in the application) and a **baseline model** of your selection. Both models categorize the feedback into **positive, neutral, or negative** sentiments.

**Why do the models yield different results?**

Variances in predictions stem from differences in underlying training data and model architecture. Many baseline models are restricted to **monolingual English datasets** or derive sentiment by mapping **5-star rating scales** into categorical labels. Conversely, our **fine-tuned XLM-RoBERTa** is **natively multilingual** and explicitly designed to output the exact **ternary classification** used by this dashboard.

**Why is our fine-tuned model optimal for this dataset?**

The collected feedback frequently consists of **concise, code-switched (English and Tagalog) text**. A specialized multilingual model is inherently better equipped to process these linguistic nuances and accurately capture contextual sentiment compared to **standard monolingual** or **rating-mapped baselines**.

**How should the "Agreement" percentage be interpreted?**

This percentage indicates how often both models assigned the **identical sentiment label** to a specific comment. Please note that this is strictly a measure of **agreement**, not an **empirical accuracy score**. In instances of divergence, we recommend a **manual review** of the comment to determine the most contextually accurate label.

**Will these comparisons affect my saved data?**

**No.** Baseline predictions are generated dynamically for comparative purposes on this specific page only. Your core dashboard metrics and exported datasets will remain unaltered, relying solely on the official labels generated by the **Fine-tuned XLM-RoBERTa** model.
            """
        )