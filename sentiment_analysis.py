import streamlit as st
from st_supabase_connection import SupabaseConnection
import torch

st.set_page_config(page_title="Thesis: Sentiment Analysis", page_icon="📊")
st.title("📊 Multilingual Sentiment Analysis")
st.write("Using a Fine-Tuned XLM-RoBERTa for English, Tagalog, and Taglish.")

conn = st.connection("supabase", type=SupabaseConnection)

@st.cache_resource 
def load_sentiment_model():
    # Lazy import to prevent the error from crashing other pages
    from transformers import pipeline, AutoTokenizer
    
    model_path = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    
    # Explicitly load tokenizer to avoid tiktoken/file errors
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    return pipeline(
        "sentiment-analysis", 
        model=model_path, 
        tokenizer=tokenizer,
        # Use CPU (-1) for stability on Streamlit Cloud unless GPU is verified
        device=-1 if not torch.cuda.is_available() else 0
    )

with st.spinner("Loading AI model..."):
    classifier = load_sentiment_model()

# Mapping for CardiffNLP XLM-RoBERTa labels
# LABEL_0 = Negative, LABEL_1 = Neutral, LABEL_2 = Positive
label_map = {
    "LABEL_0": "Negative",
    "LABEL_1": "Neutral",
    "LABEL_2": "Positive"
}

user_input = st.text_area("Enter text (English, Tagalog, or Taglish):", 
                          placeholder="Example: Ang bagal ng biyahe, nakakainis!")

if st.button("Analyze Sentiment"):
    if user_input:
        # Run prediction
        result = classifier(user_input)[0]
        raw_label = result['label']
        score = result['score']
        
        # Convert raw label (LABEL_X) to readable text
        readable_label = label_map.get(raw_label, raw_label)

        st.divider()
        
        # Display results based on the mapped label
        if readable_label == "Positive":
            st.success(f"**Sentiment: {readable_label}** (Confidence: {score:.2f})")
            st.balloons()
        elif readable_label == "Negative":
            st.error(f"**Sentiment: {readable_label}** (Confidence: {score:.2f})")
        else:
            st.info(f"**Sentiment: {readable_label}** (Confidence: {score:.2f})")
            
        # Optional: Show a progress bar for confidence
        st.progress(score)