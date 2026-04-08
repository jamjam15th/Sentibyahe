import streamlit as st
from st_supabase_connection import SupabaseConnection
from streamlit_extras.stylable_container import stylable_container
import pathlib
import base64
import json
from datetime import datetime, timedelta, timezone
import uuid

# ==========================
# INITIAL SETUP & STATE
# ==========================
def load_local_css(file_name):
    with open(file_name) as f:
        st.html(f"<style>{f.read()}</style>")

css_path = pathlib.Path("assets/styles.css") 
if css_path.exists():
    load_local_css(css_path)

st.set_page_config(
    page_title="PUV Sentiment Analysis",
    page_icon="🚌",
    initial_sidebar_state="collapsed",
    layout="wide",
)

conn = st.connection("supabase", type=SupabaseConnection)

SESSION_TIMEOUT_MINUTES = 30

if "auth_tab" not in st.session_state:
    st.session_state.auth_tab = "login"
if "tab" in st.query_params:
    st.session_state.auth_tab = st.query_params["tab"]
active_tab = st.session_state.auth_tab

# ==========================
# SESSION MANAGEMENT
# ==========================
def set_session(user):
    """Set session state and store session in Supabase active_sessions table"""
    session_id = str(uuid.uuid4())
    st.session_state.logged_in = True
    st.session_state.local_login = True
    st.session_state.session_id = session_id
    st.session_state.user_email = user.email or ""

    metadata = user.user_metadata or {}
    st.session_state.first_name = metadata.get("first_name", "Admin")
    st.session_state.last_name  = metadata.get("last_name", "")
    st.session_state.login_time = datetime.now(timezone.utc)

    # Save session in Supabase table
    conn.client.table("active_sessions").upsert({
        "user_email": st.session_state.user_email,
        "session_id": session_id
    }).execute()

def clear_session():
    """Clear session state and remove from Supabase"""
    try:
        conn.client.table("active_sessions") \
            .delete() \
            .eq("user_email", st.session_state.get("user_email", "")) \
            .execute()
    except Exception:
        pass

    st.session_state.clear()

def is_session_expired():
    if "login_time" not in st.session_state:
        return False
    now = datetime.now(timezone.utc)
    login_time = st.session_state.login_time
    return now - login_time > timedelta(minutes=SESSION_TIMEOUT_MINUTES)

# ==========================
# CSS INJECTION
# ==========================
def inject_custom_css():
    st.html("""
    <style>
    /* Add your previous left/right card CSS here */
    </style>
    """)  # Keep all your previous CSS for left/right columns

inject_custom_css()

# ==========================
# UI COMPONENTS
# ==========================
def render_card_header(active):
    l_cls = "tb active" if active == "login" else "tb"
    s_cls = "tb active" if active == "signup" else "tb"
    card_title = "Welcome back" if active == "login" else "Join the platform"
    st.html(f"""
    <div class="mobile-badge-wrapper">
        <div class="lp-badge"><span>🚌 PUV Analytics Platform</span></div>
    </div>
    <div class="card-header">
        <span class="card-label">Secure Access</span>
        <div class="tab-switcher">
            <a href="?tab=login" class="{l_cls}">Sign In</a>
            <a href="?tab=signup" class="{s_cls}">Create Account</a>
        </div>
        <span style="font-family:'Libre Baskerville',serif;font-size:.95rem;font-weight:700;color:var(--navy);display:block;margin-bottom:.2rem;">{card_title}</span>
    </div>
    """)

# ==========================
# LOGIN FORM
# ==========================
def handle_login_form():
    email = st.text_input("Email address", key="login_email", placeholder="you@example.com")
    password = st.text_input("Password", key="login_pass", placeholder="Enter your password", type="password")

    if st.button("Sign In →", key="btn_login"):
        if not email or not password:
            st.warning("⚠️ Please fill in all fields.")
            return
        try:
            auth = conn.client.auth.sign_in_with_password({"email": email, "password": password})
            if auth.user:
                set_session(auth.user)
                st.success("✅ Logged in successfully!")
                st.experimental_rerun()
        except Exception as e:
            st.error(f"❌ Login failed: {e}")

    st.html('<div style="text-align:center;margin-top:.3rem;font-size:1rem;color:var(--muted);">Don\'t have an account? <a href="?tab=signup" style="color:var(--steel);font-weight:700;text-decoration:none;">Create one</a></div>')

# ==========================
# SIGNUP FORM
# ==========================
def handle_signup_form():
    new_first = st.text_input("First name", key="signup_fname")
    new_last = st.text_input("Last name", key="signup_lname")
    new_email = st.text_input("Email address", key="signup_email")
    new_password = st.text_input("Password", key="signup_pass", type="password")
    confirm_pass = st.text_input("Confirm password", key="signup_confirm", type="password")

    if st.button("Create Account →", key="btn_signup"):
        if new_password != confirm_pass:
            st.error("❌ Passwords do not match.")
        else:
            try:
                response = conn.client.auth.sign_up({
                    "email": new_email,
                    "password": new_password,
                    "options": {"data": {"first_name": new_first, "last_name": new_last}},
                })
                if response.user:
                    st.success("🎉 Account created! You can now log in.")
            except Exception as e:
                st.error(f"❌ Sign up failed: {e}")

    st.html('<div style="text-align:center;margin-top:.3rem;font-size:1rem;color:var(--muted);">Already have an account? <a href="?tab=login" style="color:var(--steel);font-weight:700;text-decoration:none;">Sign in here</a></div>')

# ==========================
# MAIN LAYOUT
# ==========================
left_col, right_col = st.columns([48, 52])

with left_col:
    st.html("""
    <div class="left-container">
      <div class="acc-bar"></div>
      <div class="text-container">
        <div class="lp-badge"><span>🚌 PUV Analytics Platform</span></div>
        <h1 class="lp-h1">Understanding the<br><em>Voice</em> of Every<br>Commuter</h1>
        <p class="lp-desc">Real-time sentiment analysis across public utility vehicle routes — empowering planners, operators, and policymakers with data-driven insights.</p>
      </div>
    </div>
    """)

with right_col:
    with stylable_container(
        key="auth_card",
        css_styles="""
            {
                background: #ffffff !important;
                border: 1px solid rgba(84,119,146,0.15) !important;
                box-shadow: 0 4px 8px rgba(26,50,99,0.06),
                            0 20px 60px rgba(26,50,99,0.14) !important;
                padding: .85rem 1.4rem .8rem !important;
                max-width: 380px !important;
                width: 100% !important;
                margin: auto !important; 
            }
            div[data-testid="stVerticalBlock"] {
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
                border-radius: 0 !important;
            }
        """,
    ):
        render_card_header(active_tab)
        if active_tab == "login":
            handle_login_form()
        else:
            handle_signup_form()