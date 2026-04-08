import streamlit as st
from st_supabase_connection import SupabaseConnection
import base64
import json 
import streamlit.components.v1 as components

# ── 1. Init ──
conn = st.connection("supabase", type=SupabaseConnection)

# ── 2. Page config ──
st.set_page_config(
    page_title="PUV Sentiment Analysis",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 3. Global CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Mulish:wght@300;400;500;600;700&display=swap');

:root {
  --gold:    rgb(255, 197, 112);
  --sand:    rgb(239, 210, 176);
  --steel:   rgb(84, 119, 146);
  --navy:    rgb(26, 50, 99);
  --navydk:  rgb(18, 34, 68);
  --navylt:  rgb(36, 65, 120);
  --white:   #ffffff;
  --off:     #f7f6f2;
  --muted:   rgb(140, 160, 180);
}

* { box-sizing: border-box; }
html, body, [class*="st-"] { font-family: 'Mulish', sans-serif !important; }

i, .material-symbols-rounded, .material-icons, [data-testid="stIconMaterial"], [class*="stIcon"] {
  font-family: 'Material Symbols Rounded', 'Material Icons' !important;
}

[data-testid="stSidebarNav"]   { display: none !important; }
#MainMenu                      { display: none !important; }
footer                         { display: none !important; }
[data-testid="stDecoration"]   { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

[data-testid="stSidebarCollapsedControl"] {
  display: flex !important; visibility: visible !important;
  z-index: 999999 !important; left: 10px !important; top: 10px !important;
  background: var(--navy) !important; border-radius: 8px !important;
  border: 1px solid var(--gold) !important; color: var(--gold) !important; padding: 5px !important;
}

[data-testid="stSidebar"] {
  background: var(--navy) !important;
  border-right: 1px solid rgba(255,197,112,0.12) !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  padding: 0 0 2rem 0 !important; background: var(--navy) !important;
}
[data-testid="stSidebar"] * { color: var(--sand) !important; }

.sidebar-brand { padding: 1.6rem 1.4rem 1.2rem; border-bottom: 1px solid rgba(255,197,112,0.12); margin-bottom: .5rem; }
.sidebar-brand h2 { font-family: 'Libre Baskerville', serif !important; font-size: 1.05rem !important; font-weight: 700; color: #ffffff !important; margin: 0; }

.sidebar-user { padding: .8rem 1.4rem; background: rgba(255,197,112,0.05); border-bottom: 1px solid rgba(255,197,112,0.10); margin-bottom: .4rem; }
.sidebar-user .user-name { font-size: .82rem !important; font-weight: 700 !important; color: #ffffff !important; }
.sidebar-user .user-email { font-size: .65rem !important; color: var(--muted) !important; display: block; }

.sidebar-nav-label { font-size: .55rem !important; font-weight: 700 !important; letter-spacing: .18em; text-transform: uppercase; color: var(--muted) !important; padding: .6rem 1.4rem .25rem; display: block; }

[data-testid="stSidebar"] [data-testid="stPageLink"] a {
  display: flex !important; align-items: center !important; gap: .6rem !important;
  padding: .52rem 1.4rem !important; border-radius: 0 !important; font-size: .78rem !important;
  font-weight: 600 !important; color: rgba(239,210,176,0.80) !important; text-decoration: none !important;
  border-left: 3px solid transparent !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover { background: rgba(255,197,112,0.08) !important; color: var(--gold) !important; }
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] a { background: rgba(255,197,112,0.12) !important; color: var(--gold) !important; border-left-color: var(--gold) !important; font-weight: 700 !important; }

[data-testid="stSidebar"] div.stButton > button {
  background: rgba(255,197,112,0.08) !important; color: var(--sand) !important;
  border: 1px solid rgba(255,197,112,0.20) !important; border-radius: 7px !important;
  font-size: .72rem !important; font-weight: 700 !important; margin: .3rem 1.4rem !important; width: calc(100% - 2.8rem) !important;
}

[data-testid="stMain"] { background: var(--off) !important; }
.block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }

.sidebar-footer { padding: 1.5rem 1.4rem 1rem; margin-top: 3.5rem !important; border-top: 1px solid rgba(255,197,112,0.10); text-align: center; }
.sidebar-footer .ver { font-size: .58rem !important; color: rgba(140,160,180,0.6) !important; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ── 4. SECURE SESSION RESOLUTION (Cross-Device Fix) ──
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

try:
    # 1. First Priority: Check URL token (Fresh login redirect)
    if "session" in st.query_params:
        token_str = st.query_params["session"]
        padded_token = token_str + "=" * ((4 - len(token_str) % 4) % 4)
        user_data = json.loads(base64.urlsafe_b64decode(padded_token).decode("utf-8"))
        
        st.session_state.logged_in = True
        st.session_state.user_email = user_data.get("e", "")
        st.session_state.first_name = user_data.get("f", "Admin")
        st.session_state.last_name  = user_data.get("l", "")
        
        # CLEAR URL so it can't be copied to other devices
        st.query_params.clear()

    # 2. Second Priority: Strict Server-Side Validation
    else:
        # Check if the Supabase Server actually recognizes a user for this browser
        user_res = conn.client.auth.get_user()
        if user_res and user_res.user:
            st.session_state.logged_in = True
            st.session_state.user_email = user_res.user.email
            metadata = user_res.user.user_metadata or {}
            st.session_state.first_name = metadata.get("full_name", metadata.get("first_name", "Admin"))
            st.session_state.last_name = metadata.get("last_name", "")
        else:
            # If server says NO, ensure session state is false
            st.session_state.logged_in = False
            
except Exception:
    st.session_state.logged_in = False


# ── 5. Pages ──
login_page       = st.Page("login.py",               title="Log in",               icon="🔐")
dashboard_page   = st.Page("dashboard.py",           title="Sentiment Dashboard", icon="📊")
builder_page     = st.Page("builder.py",             title="Form Builder",         icon="🛠️")
testing_page     = st.Page("sentiment_analysis.py", title="Analysis",             icon="📝")
settings_page    = st.Page("settings.py",            title="Settings",            icon="⚙️")
public_form_page = st.Page("public_form.py",        title="Take Survey",          icon="📋")

# ── 6. Router ──
if "form_id" in st.query_params:
    st.html('<style>[data-testid="stSidebar"] { display: none !important; }</style>')
    pg = st.navigation([public_form_page], position="hidden")

elif st.session_state.get("logged_in"):
    pg = st.navigation(
        [dashboard_page, builder_page, testing_page, settings_page],
        position="sidebar"
    )

    with st.sidebar:
        st.html("""
        <div class="sidebar-brand">
          <div class="brand-badge"><span>🚌 PUV Analytics</span></div>
          <h2>Sentiment<br><em>Analysis</em> Platform</h2>
        </div>
        """)

        f_name = st.session_state.get("first_name", "Admin")
        l_name = st.session_state.get("last_name", "")
        u_email = st.session_state.get("user_email", "")
        
        st.html(f"""
        <div class="sidebar-user">
          <div class="user-name">{f_name} {l_name}</div>
          <span class="user-email">{u_email}</span>
        </div>
        """)

        st.html('<span class="sidebar-nav-label">Navigation</span>')
        st.page_link(dashboard_page)
        st.page_link(testing_page)
        st.page_link(builder_page)
        st.page_link(settings_page)

        st.divider()

        if st.button("🚪 Hard Logout", use_container_width=True):
            try:
                # Sign out with 'global' scope to invalidate session on all tabs
                conn.client.auth.sign_out(scope='global')
            except: pass
            
            st.query_params.clear()
            st.session_state.clear()
            
            # JavaScript Nuke: Force the browser to forget everything immediately
            components.html("""
                <script>
                    window.localStorage.clear();
                    window.sessionStorage.clear();
                    window.parent.location.reload();
                </script>
            """, height=0)
            st.rerun()

        st.html("""
        <div class="sidebar-footer">
          <span class="ver">PUV Sentiment v1.0</span>
        </div>
        """)

else:
    st.html('<style>[data-testid="stSidebar"] { display: none !important; }</style>')
    pg = st.navigation([login_page], position="hidden")

pg.run()