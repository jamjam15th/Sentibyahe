import streamlit as st
from st_supabase_connection import SupabaseConnection
import pathlib
from datetime import datetime, timezone, timedelta
import uuid
import hashlib
from forms import create_sample_form_for_new_user


st.html("""
    <style>
    .st-key-auth_card {
        padding: .85rem 1.4rem .8rem !important;
        max-width: 380px !important;
        width: 100% !important;
        margin: auto !important; 
        border-radius: 0.5rem; /* Optional: adds rounded corners often expected with shadows */
    }

    /* Target the internal vertical block inside this specific container */
    .st-key-auth_card div[data-testid="stVerticalBlock"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        border-radius: 0 !important;
    }
    </style>
""")

# ==========================================
# INITIAL SETUP & STATE
# ==========================================
def load_local_css(file_name):
    with open(file_name) as f:
        st.html(f"<style>{f.read()}</style>")

css_path = pathlib.Path("assets/styles.css") 
if css_path.exists():
    load_local_css(css_path)

st.set_page_config(
    page_title="Land Public Transportation · Sentiment analysis",
    page_icon="🚌",
    initial_sidebar_state="collapsed",
    layout="wide",
)

conn = st.connection("supabase", type=SupabaseConnection)

# ==========================================
# LOADING SCREEN
# ==========================================
st.markdown("""
<style>
    /* Hide Streamlit's Deploy button and toolbar */
    # [data-testid="stToolbar"] {
    #     display: none !important;
    # }
    # #MainMenu {
    #     display: none !important;
    # }
    # header[data-testid="stHeader"] {
    #     display: none !important;
    # }
            
    .st-emotion-cache-0 {
        display: none !important;
    }
            
    /* 1. KEEP SIDEBAR ON TOP OF LOADER */
    [data-testid="stSidebar"], 
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 999999999 !important; /* Highest priority */
    }

    .stAppDeployButton { display: none !important; }

    /* 2. COMPLETELY HIDE THE APP ROOT */
    /* visibility: hidden is bulletproof against React hydration overrides */
    .stApp [data-testid="stAppViewBlockContainer"] {
        visibility: hidden !important;
        animation: snapVisible 0.1s forwards 2s !important; /* 1 second wait */
    }

    /* 3. OVERLAY THAT COVERS EVERYTHING ELSE */
    #nuclear-loader {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: #f0f4f8; /* Matched to your app background */
        z-index: 999999998; /* Exactly one layer BELOW the sidebar */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        animation: fadeOutNuclear 0.4s ease-out 2s forwards; /* Matches the 1s wait */
    }

    .spinner {
        border: 4px solid #ffffff;
        border-top: 4px solid #1a2e55;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 0.8s linear infinite;
        margin-bottom: 15px;
    }

    .loading-text {
        color: #1a2e55;
        font-weight: 600;
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
    }

    /* 4. KEYFRAMES */
    @keyframes snapVisible {
        to { visibility: visible !important; }
    }

    @keyframes fadeOutNuclear {
        0% { opacity: 1; visibility: visible; }
        100% { opacity: 0; visibility: hidden; display: none; }
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>

<div id="nuclear-loader">
    <div class="spinner"></div>
    <div class="loading-text">Loading Sentibyahe...</div>
</div>
""", unsafe_allow_html=True)

if "auth_tab" not in st.session_state:
    st.session_state.auth_tab = "login"
if "tab" in st.query_params:
    st.session_state.auth_tab = st.query_params["tab"]
active_tab = st.session_state.auth_tab

# ==========================================
# CSS INJECTION
# ==========================================
def inject_custom_css():
    st.html("""
      <style>
        /* 1. Nuke the Header and Toolbar */
        header[data-testid="stHeader"], 
        [data-testid="stHeader"],
        [data-testid="collapsedControl"] {
            display: none !important;
            height: 0 !important;
            width: 0 !important;
        }

        /* 2. Remove the padding from the root main container */
        .main .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
        }

        /* 3. Force the app view to start at the absolute top */
        [data-testid="stAppViewContainer"] {
            padding: 0 !important;
        }
        
        [data-testid="stMainViewContainer"] {
            margin-top: -5rem !important; /* Forces content to slide up into the header gap */
        }

        /* 4. Fix for the Columns to ensure they stretch to the top */
        [data-testid="stHorizontalBlock"] {
            margin-top: 0 !important;
        }

        /* 5. Ensure your left container actually touches the edge */
        .left-container {
            margin: 0 !important;
            padding-top: 0 !important;
            min-height: 100vh;
        }

        .main, section.main,
        .block-container {
          overflow: hidden !important; height: 100vh !important; padding: 0 !important; margin: 0 !important; max-width: 100% !important;
        }
        #MainMenu, footer, header,
        [data-testid="stToolbar"], [data-testid="collapsedControl"],
        [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
        [data-testid="stHorizontalBlock"] { gap: 0 !important; padding: 0 !important; margin: 0 !important; height: 100vh !important; align-items: stretch !important; }
        [data-testid="stHorizontalBlock"] > div:first-child { height: 100vh !important; padding: 0 !important; overflow: hidden !important; }
        [data-testid="stHorizontalBlock"] > div:first-child > div[data-testid="stVerticalBlock"] { height: 100vh !important; padding: 0 !important; margin: 0 !important; }
        [data-testid="stHorizontalBlock"] > div:last-child { height: 100vh !important; padding: 1rem 2.5rem !important; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; overflow-y: auto !important; }
        [data-testid="stHorizontalBlock"] > div:last-child > div[data-testid="stVerticalBlock"] { margin: auto !important; width: 100% !important; display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important; }
        [data-testid="stVerticalBlockBorderWrapper"] { background: transparent !important; }
        [data-testid="stTextInput"] input { background-color: #ffffff !important; color: #122244 !important; border: 1px solid rgba(84, 119, 146, 0.3) !important; border-radius: 6px !important; }
        [data-testid="stTextInput"] input::placeholder { color: rgba(18, 34, 68, 0.4) !important; }
        [data-testid="stTextInput"] input:focus { border-color: var(--gold) !important; box-shadow: 0 0 0 1px var(--gold) !important; }
        .left-container { height: 100vh; background-color: var(--navy); position: relative; overflow: hidden !important; display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important; }
        .left-container::before { content: ""; position: absolute; top: -90px; right: -90px; width: 320px; height: 320px; border-radius: 50%; background: rgba(255,197,112,0.08); pointer-events: none; }
        .left-container::after { content: ""; position: absolute; bottom: -70px; left: -50px; width: 240px; height: 240px; border-radius: 50%; background: rgba(84,119,146,0.16); pointer-events: none; }
        .acc-bar { position: absolute; top: 18%; right: 0; width: 4px; height: 30%; background: linear-gradient(to bottom, var(--gold), transparent); border-radius: 4px 0 0 4px; pointer-events: none; }
        .text-container { color: white; padding: 2.8rem 2.6rem; max-width: 85%; }
        .lp-badge { display: inline-flex; align-items: center; gap: .45rem; background: rgba(255,197,112,0.13); border: 1px solid rgba(255,197,112,0.32); border-radius: 999px; padding: .3rem .9rem; margin-bottom: 2rem; width: fit-content; font-size: 1.3rem; }
        .mobile-badge-wrapper { display: none; width: 100%; margin-bottom: 1.2rem; }
        .mobile-badge-wrapper .lp-badge { margin: 0 auto !important; }
        .lp-h1 { font-family: 'Libre Baskerville', serif !important; font-size: clamp(2.3rem, 4vw, 3rem) !important; font-weight: 700 !important; color: #ffffff !important; line-height: 1.25; margin: 0 0 .85rem; }
        .lp-h1 em { font-style: italic !important; color: var(--gold) !important; }
        .lp-desc { font-size: 1.3rem !important; font-weight: 400 !important; color: var(--sand) !important; line-height: 1.72; max-width: 300px; margin: 0 0 1.6rem; }
        .card-header { padding-bottom: 0; margin-bottom: 0; }
        .card-label { font-size: 1rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; color: var(--steel); display: block; margin-bottom: .15rem; }
        .tab-switcher { display: flex; gap: 3px; background: rgba(26,50,99,0.07); border-radius: 7px; padding: 2px; margin-bottom: 1rem; }
        .tb { flex: 1; text-align: center; padding: .22rem; border-radius: 5px; font-size: 1rem; font-weight: 700; text-decoration: none; color: var(--muted); background: transparent; }
        .tb.active { color: var(--gold); background: var(--navy); }
        [data-testid="stTextInput"] { margin-bottom: 0 !important; }
        [data-testid="stTextInput"] label { font-size: .55rem !important; font-weight: 700 !important; letter-spacing: .09em !important; text-transform: uppercase !important; color: var(--navy) !important; margin-bottom: 0 !important; margin-top: .22rem !important; line-height: 1 !important; display: block !important; }
        [data-testid="stTextInput"] input { padding: .2rem .6rem !important; font-size: .78rem !important; line-height: 1.2 !important; }
        [data-testid="stTextInput"] > div { margin-bottom: 0 !important; padding-bottom: 0 !important; }
        [data-testid="stVerticalBlock"] > * { margin-top: 0 !important; margin-bottom: 0 !important; gap: 0 !important; }
        div.stButton > button { width: 100% !important; background: var(--navy) !important; color: var(--gold) !important; border: none !important; border-radius: 6px !important; font-size: .60rem !important; font-weight: 700 !important; letter-spacing: .14em !important; text-transform: uppercase !important; padding: .3rem .8rem !important; margin-top: .28rem !important; transition: background .2s, transform .15s !important; box-shadow: 0 3px 10px rgba(26,50,99,0.18) !important; }
        div.stButton > button:hover { background: var(--navydk) !important; transform: translateY(-1px) !important; }
        div.stButton > button:active { transform: translateY(0) !important; }
        [data-testid="stColumns"] { gap: .4rem !important; }
        [data-testid="stColumns"] > div > [data-testid="stVerticalBlock"] { background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important; border-radius: 0 !important; }
        [data-testid="stAlert"] { font-size: .62rem !important; padding: .18rem .5rem !important; margin-top: .15rem !important; margin-bottom: 0 !important; border-radius: 5px !important; line-height: 1.2 !important; }
        [data-testid="stAlert"] > div { padding: 0 !important; gap: .25rem !important; }
        @media screen and (max-width: 992px) {
          html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, section.main { overflow: hidden !important; height: 100vh !important; }
          .block-container { overflow-y: auto !important; overflow-x: hidden !important; height: 100vh !important; padding: 0 !important; }
          [data-testid="stHorizontalBlock"] > div:first-child { display: none !important; }
          [data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: column !important; height: auto !important; min-height: 100vh !important; }
          [data-testid="stHorizontalBlock"] > div:last-child { width: 100% !important; max-width: 100% !important; box-sizing: border-box !important; padding: 2rem 1.5rem !important; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; }
          [data-testid="stHorizontalBlock"] > div:last-child > div[data-testid="stVerticalBlock"] { margin: auto 0 !important; width: 100% !important; height: auto !important; }
          .mobile-badge-wrapper { display: flex !important; justify-content: center !important; width: 100% !important; }
        }
      </style>
    """)


# ==========================================
# COMPONENTS & FORMS
# ==========================================
def render_card_header(active):
    l_cls = "tb active" if active == "login" else "tb"
    s_cls = "tb active" if active == "signup" else "tb"
    card_title = "Welcome back" if active == "login" else "Join the platform"
    st.html(f"""
    <div style="text-align: center;">
        <h1 style="margin-bottom: 5px; color: ;">Sentibyahe</h1>
        <p style="font-size: 1.3rem; color: #7c8db5; margin-top: 0; font-style: italic;">
        AI-Powered Sentiment Surveys
        </p>
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

def handle_login_form():
    email    = st.text_input("Email address", key="login_email", placeholder="you@example.com")
    password = st.text_input("Password", key="login_pass", placeholder="Enter your password", type="password")

    if st.button("Sign In →", key="btn_login"):
        if not email or not password:
            st.warning("⚠️ Please fill in all fields.")
            return
        try:
            auth = conn.client.auth.sign_in_with_password({"email": email, "password": password})
            if auth.user:
                session_id = str(uuid.uuid4())
                metadata   = auth.user.user_metadata or {}

                st.session_state.logged_in   = True
                st.session_state.local_login = True
                st.session_state.session_id  = session_id
                st.session_state.user_email  = auth.user.email
                st.session_state.first_name  = metadata.get("first_name", "Admin")
                st.session_state.last_name   = metadata.get("last_name", "")
                st.session_state.login_time  = datetime.now(timezone.utc)

                # ✅ Generate device fingerprint
                device_id = hashlib.md5(
                    st.context.headers.get("User-Agent", "unknown").encode()
                ).hexdigest()
                st.session_state.device_id = device_id

                conn.client.table("active_sessions").upsert({
                    "user_email": auth.user.email,
                    "session_id": session_id,
                    "device_id": device_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }, on_conflict="user_email").execute()

                # Store session_id in session state for persistence
                st.session_state.session_id = session_id
                st.session_state.user_email = auth.user.email
                st.session_state.logged_in = True
                st.session_state.local_login = True
                st.session_state.first_name = metadata.get("first_name", "Admin")
                st.session_state.last_name = metadata.get("last_name", "")
                
                # Pass session_id in URL so it persists across reloads
                st.query_params["session_id"] = session_id
                st.rerun()

        except Exception as e:
            st.error(f"❌ Login failed: {e}")

    st.html('<div style="text-align:center;margin-top:.3rem;font-size:1rem;color:var(--muted);">Don\'t have an account? <a href="?tab=signup" style="color:var(--steel);font-weight:700;text-decoration:none;">Create one</a></div>')

def handle_signup_form():
    new_first    = st.text_input("First name",        key="signup_fname")
    new_last     = st.text_input("Last name",         key="signup_lname")
    new_email    = st.text_input("Email address",     key="signup_email")
    new_password = st.text_input("Password",          key="signup_pass",    type="password")
    confirm_pass = st.text_input("Confirm password",  key="signup_confirm", type="password")

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
                    # Create a sample form with default questions for the new user
                    sample_form = create_sample_form_for_new_user(new_email)
                    if sample_form:
                        st.success("🎉 Account created! A sample feedback form has been automatically created for you. You can sign in now and customize it in the Form Builder.")
                    else:
                        st.success("🎉 Account created! You can sign in now.")
            except Exception as e:
                st.error(f"❌ Sign up failed: {e}")

    st.html('<div style="text-align:center;margin-top:.3rem;font-size:1rem;color:var(--muted);">Already have an account? <a href="?tab=login" style="color:var(--steel);font-weight:700;text-decoration:none;">Sign in here</a></div>')


# ==========================================
# MAIN APP LAYOUT
# ==========================================
inject_custom_css()

left_col, right_col = st.columns([48, 52])

with left_col:
    st.html("""
    <div class="left-container">
      <div class="acc-bar"></div>
      <div class="text-container">
        <div class="lp-badge"><span>Land Public Transportation Analytics</span></div>
        <h1 class="lp-h1">Understanding the<br><em>Voice</em> of Every<br>Respondent</h1>
        <p class="lp-desc">Real-time sentiment analysis for Land Public Transportation — supporting planners, operators, and policymakers with data-driven insights.</p>
      </div>
    </div>
    """)

with right_col:
    with st.container(key="auth_card"):
        render_card_header(active_tab)
        if active_tab == "login":
            handle_login_form()
        else:
            handle_signup_form()