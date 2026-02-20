import streamlit as st
from st_supabase_connection import SupabaseConnection

st.title("🔐 Access Portal")

conn = st.connection("supabase", type=SupabaseConnection)

# Create two tabs
tab1, tab2 = st.tabs(["Login", "Sign Up"])

# --- TAB 1: LOGIN ---
with tab1:
    st.header("Welcome Back")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Log In"):
        try:
            auth = conn.client.auth.sign_in_with_password({"email": email, "password": password})
            if auth.user:
                st.session_state.logged_in = True
                st.session_state.user_email = auth.user.email
                st.success("Login successful!")
                st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

# --- TAB 2: SIGN UP ---
with tab2:
    st.header("Create Account")
    new_email = st.text_input("Email", key="signup_email")
    new_password = st.text_input("Password", type="password", key="signup_pass")

    if st.button("Sign Up"):
        try:
            # 1. Register the user in Supabase
            response = conn.client.auth.sign_up({"email": new_email, "password": new_password})
            
            # 2. Check if user was created
            if response.user:
                st.success("Account created! 📧 Please check your email and click the confirmation link before logging in.")
                st.info("Note: If you don't see the email, check your Spam folder.")
            
        except Exception as e:
            st.error(f"Sign up failed: {e}")