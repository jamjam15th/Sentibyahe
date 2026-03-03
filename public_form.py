import streamlit as st
import hashlib
from st_supabase_connection import SupabaseConnection

st.set_page_config(initial_sidebar_state="collapsed", page_title="Take Survey")

# --- 1. DETERMINE WHICH FORM TO SHOW ---
if st.session_state.get("logged_in") and st.session_state.get("user_email"):
    # If Admin is logged in, generate their ID for Live Preview
    target_form_id = hashlib.md5(st.session_state.user_email.encode()).hexdigest()[:12]
    st.info("👁️ **Live Preview Mode:** You are viewing your own form.")
else:
    # If commuter, read the ID from the URL
    query_params = st.query_params
    if "form_id" not in query_params:
        st.error("⚠️ Invalid survey link. Please make sure you copied the full link provided by the researcher.")
        st.stop()
    target_form_id = query_params["form_id"]

# --- 2. BUILD THE FORM ---
st.title("🚐 PUV Feedback Form")
st.write("Please share your honest experience. Your feedback is completely anonymous.")

conn = st.connection("supabase", type=SupabaseConnection)

# Fetch questions using the Public ID instead of the email
try:
    res = conn.client.table("form_questions").select("*").eq("public_id", target_form_id).order("id").execute()
    form_schema = res.data
except Exception:
    form_schema = []

if len(form_schema) == 0:
    st.info("This survey is currently closed or has no questions.")
else:
    with st.form("public_survey_form", clear_on_submit=True):
        user_answers = {}
        
        for q in form_schema:
            if q["q_type"] == "Short Answer":
                user_answers[q["prompt"]] = st.text_input(q["prompt"], key=f"ans_{q['id']}")
            elif q["q_type"] == "Paragraph":
                user_answers[q["prompt"]] = st.text_area(q["prompt"], key=f"ans_{q['id']}")
            elif q["q_type"] == "Multiple Choice":
                opts = q["options"] if q["options"] else ["Option 1"]
                user_answers[q["prompt"]] = st.radio(q["prompt"], opts, key=f"ans_{q['id']}")
            elif q["q_type"] == "Rating (1-5)":
                user_answers[q["prompt"]] = st.slider(q["prompt"], min_value=1, max_value=5, value=3, key=f"ans_{q['id']}")
                
        st.divider()
        submitted = st.form_submit_button("Submit Response", type="primary")
        
        if submitted:
            # We secretly grab the admin's email from the question data 
            # so it still shows up correctly on your dashboard!
            hidden_admin_email = form_schema[0]["admin_email"]
            
            conn.client.table("form_responses").insert({
                "answers": user_answers,
                "public_id": target_form_id,
                "admin_email": hidden_admin_email
            }).execute()
            
            st.success("🎉 Thank you! Your response has been securely submitted.")