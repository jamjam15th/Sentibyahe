import streamlit as st
from st_supabase_connection import SupabaseConnection
from streamlit_extras.stylable_container import stylable_container
import pathlib
import base64
import json

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
    page_title="PUV Sentiment Analysis",
    page_icon="🚌",
    initial_sidebar_state="collapsed",
    layout="wide",
)

conn = st.connection("supabase", type=SupabaseConnection)

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
        
        [data-testid="stHorizontalBlock"] > div:last-child {
          height: 100vh !important; padding: 1rem 2.5rem !important; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; overflow-y: auto !important;
        }
        [data-testid="stHorizontalBlock"] > div:last-child > div[data-testid="stVerticalBlock"] {
          margin: auto !important; width: 100% !important; display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] { background: transparent !important; }

        /* INPUT FIELD STYLING FIX */
        [data-testid="stTextInput"] input {
            background-color: #ffffff !important;
            color: #122244 !important;
            border: 1px solid rgba(84, 119, 146, 0.3) !important;
            border-radius: 6px !important;
        }
        [data-testid="stTextInput"] input::placeholder { color: rgba(18, 34, 68, 0.4) !important; }
        [data-testid="stTextInput"] input:focus { border-color: var(--gold) !important; box-shadow: 0 0 0 1px var(--gold) !important; }

        .left-container {
          height: 100vh; background-color: var(--navy); position: relative; overflow: hidden !important; display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important;
        }
        .left-container::before {
          content: ""; position: absolute; top: -90px; right: -90px; width: 320px; height: 320px; border-radius: 50%; background: rgba(255,197,112,0.08); pointer-events: none;
        }
        .left-container::after {
          content: ""; position: absolute; bottom: -70px; left: -50px; width: 240px; height: 240px; border-radius: 50%; background: rgba(84,119,146,0.16); pointer-events: none;
        }
        .acc-bar {
          position: absolute; top: 18%; right: 0; width: 4px; height: 30%; background: linear-gradient(to bottom, var(--gold), transparent); border-radius: 4px 0 0 4px; pointer-events: none;
        }
        
        .text-container { color: white; padding: 2.8rem 2.6rem; max-width: 85%; }
        
        .lp-badge {
          display: inline-flex; align-items: center; gap: .45rem; background: rgba(255,197,112,0.13); border: 1px solid rgba(255,197,112,0.32); border-radius: 999px; padding: .3rem .9rem; margin-bottom: 2rem; width: fit-content; font-size: 1.3rem; 
        }
        
        .mobile-badge-wrapper { display: none; width: 100%; margin-bottom: 1.2rem; }
        .mobile-badge-wrapper .lp-badge { margin: 0 auto !important; }

        .lp-h1 { font-family: 'Libre Baskerville', serif !important; font-size: clamp(2.3rem, 4vw, 3rem) !important; font-weight: 700 !important; color: #ffffff !important; line-height: 1.25; margin: 0 0 .85rem; }
        .lp-h1 em { font-style: italic !important; color: var(--gold) !important; }
        .lp-desc { font-size: 1.3rem !important; font-weight: 400 !important; color: var(--sand) !important; line-height: 1.72; max-width: 280px; margin: 0 0 1.6rem; }

        .card-header { padding-bottom: 0; margin-bottom: 0; }
        .card-label { font-size: .55rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; color: var(--steel); display: block; margin-bottom: .15rem; font-size: 1rem; }
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
                metadata = auth.user.user_metadata or {}
                
                # 1. Setup session state
                st.session_state.logged_in = True
                st.session_state.user_email = auth.user.email
                st.session_state.first_name = metadata.get("first_name", "Admin")
                st.session_state.last_name  = metadata.get("last_name", "")

                # 2. Package the data into a tiny dictionary (using short keys to save space)
                token_payload = {
                    "e": auth.user.email,
                    "f": st.session_state.first_name,
                    "l": st.session_state.last_name
                }
                
                # 3. Compress, encode, and convert to a URL-safe string
                json_str = json.dumps(token_payload)
                token_bytes = base64.urlsafe_b64encode(json_str.encode("utf-8"))
                safe_token = token_bytes.decode("utf-8")

                # 4. Push the single "code" to the URL
                st.query_params.clear() # Clear any old params first
                st.query_params["session"] = safe_token

                st.rerun() 
        except Exception as e:
            st.error(f"❌ Login failed: {e}")

    st.html('<div style="text-align:center;margin-top:.3rem;font-size:1rem;color:var(--muted);">Don\'t have an account? <a href="?tab=signup" style="color:var(--steel);font-weight:700;text-decoration:none;">Create one</a></div>')
    email = st.text_input("Email address", key="login_email", placeholder="you@example.com")
    password = st.text_input("Password", key="login_pass", placeholder="Enter your password", type="password")

    if st.button("Sign In →", key="btn_login"):
        if not email or not password:
            st.warning("⚠️ Please fill in all fields.")
            return
        try:
            auth = conn.client.auth.sign_in_with_password({"email": email, "password": password})
            if auth.user:
                metadata = auth.user.user_metadata or {}
                
                # 1. Setup session state
                st.session_state.logged_in = True
                st.session_state.user_email = auth.user.email
                st.session_state.first_name = metadata.get("first_name", "Admin")
                st.session_state.last_name  = metadata.get("last_name", "")

                # 2. Append URL parameters to survive a browser refresh
                st.query_params["logged_in"] = "true"
                st.query_params["email"] = auth.user.email
                st.query_params["fname"] = st.session_state.first_name
                st.query_params["lname"] = st.session_state.last_name

                st.rerun() 
        except Exception as e:
            st.error(f"❌ Login failed: {e}")

    st.html('<div style="text-align:center;margin-top:.3rem;font-size:1rem;color:var(--muted);">Don\'t have an account? <a href="?tab=signup" style="color:var(--steel);font-weight:700;text-decoration:none;">Create one</a></div>')

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
                    st.success("🎉 Account created! Check your inbox.")
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