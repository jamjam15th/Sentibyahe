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
                
                # --- NEW: EXTRACT NAMES FROM SUPABASE ---
                # Safely get the metadata dictionary (defaults to empty if none exists)
                metadata = auth.user.user_metadata or {}
                st.session_state.first_name = metadata.get("first_name", "Admin")
                st.session_state.last_name = metadata.get("last_name", "")
                
                st.success("Login successful!")
                st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

# --- TAB 2: SIGN UP ---
with tab2:
    st.header("Create Account")
    
    # --- NEW: ADD NAME FIELDS TO UI ---
    col1, col2 = st.columns(2)
    with col1:
        new_first_name = st.text_input("First Name", key="signup_fname")
    with col2:
        new_last_name = st.text_input("Last Name", key="signup_lname")
        
    new_email = st.text_input("Email", key="signup_email")
    new_password = st.text_input("Password", type="password", key="signup_pass")

    if st.button("Sign Up"):
        if not new_first_name or not new_last_name:
            st.warning("⚠️ Please enter your first and last name.")
        else:
            try:
                # --- NEW: PACK NAMES INTO METADATA ---
                sign_up_data = {
                    "email": new_email, 
                    "password": new_password,
                    "options": {
                        "data": {
                            "first_name": new_first_name,
                            "last_name": new_last_name
                        }
                    }
                }
                
                # 1. Register the user in Supabase with their names
                response = conn.client.auth.sign_up(sign_up_data)
                
                # 2. Check if user was created
                if response.user:
                    st.success("Account created! 📧 Please check your email and click the confirmation link before logging in.")
                    st.info("Note: If you don't see the email, check your Spam folder.")
                
            except Exception as e:
                st.error(f"Sign up failed: {e}")