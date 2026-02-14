import streamlit as st
from transformers import pipeline
import torch

st.set_page_config(page_title="Thesis: Sentiment Analysis", page_icon="📊")
st.title("📊 Multilingual Sentiment Analysis")
st.write("Using a Fine-Tuned XLM-RoBERTa")

@st.cache_resource 
def load_sentiment_model():
    model_path = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    return pipeline("sentiment-analysis", model=model_path, device_map="auto" if torch.cuda.is_available() else None)

with st.spinner("Loading AI model..."):
    classifier = load_sentiment_model()

user_input = st.text_area("Enter text (English, Tagalog, or Taglish):", 
                          placeholder="Example: Sobrang ganda ng view sa Baguio!")

if st.button("Analyze Sentiment"):
    if user_input:
        result = classifier(user_input)[0]
        label = result['label'].capitalize() 
        score = result['score']

        st.divider()
        if label == "Positive":
            st.success(f"**Sentiment: {label}** (Confidence: {score:.2f})")
        elif label == "Negative":
            st.error(f"**Sentiment: {label}** (Confidence: {score:.2f})")
        else:
            st.info(f"**Sentiment: {label}** (Confidence: {score:.2f})")

def add_question():
    with st.form("my form"):
        st.write("Inside the form")
        input_1 = st.text_input("What is your current say in transportation?")
        submitted = st.form_submit_button("Submit")

st.button("Add Question", on_click=add_question)
