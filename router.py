import streamlit as st
from st_supabase_connection import SupabaseConnection
import base64
import json 
import extra_streamlit_components as stx

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

/* ── GLOBAL FONT & BOXING ── */
* { box-sizing: border-box; }

/* Apply font safely so it doesn't break the sidebar arrow */
html, body, [class*="st-"] {
  font-family: 'Mulish', sans-serif !important;
}

/* ⭐️ FIX 1: Explicitly protect all Material Icons so 'keyboard_double' turns back into an arrow */
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
[data-testid="stSidebarCollapsedControl"] svg { fill: var(--gold) !important; color: var(--gold) !important; }

[data-testid="stSidebar"] {
  background: var(--navy) !important;
  border-right: 1px solid rgba(255,197,112,0.12) !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
  padding: 0 0 2rem 0 !important; background: var(--navy) !important; overflow-y: auto !important;
}
[data-testid="stSidebar"] * { color: var(--sand) !important; }

.sidebar-brand { padding: 1.6rem 1.4rem 1.2rem; border-bottom: 1px solid rgba(255,197,112,0.12); margin-bottom: .5rem; }
.sidebar-brand .brand-badge {
  display: inline-flex; align-items: center; gap: .4rem;
  background: rgba(255,197,112,0.12); border: 1px solid rgba(255,197,112,0.28);
  border-radius: 999px; padding: .22rem .75rem; margin-bottom: .7rem;
}
.sidebar-brand .brand-badge span { font-size: .6rem !important; font-weight: 700 !important; letter-spacing: .16em; text-transform: uppercase; color: var(--gold) !important; }
.sidebar-brand h2 { font-family: 'Libre Baskerville', serif !important; font-size: 1.05rem !important; font-weight: 700 !important; color: #ffffff !important; line-height: 1.3; margin: 0; }
.sidebar-brand h2 em { font-style: italic !important; color: var(--gold) !important; }

.sidebar-user { padding: .8rem 1.4rem; background: rgba(255,197,112,0.05); border-bottom: 1px solid rgba(255,197,112,0.10); margin-bottom: .4rem; }
.sidebar-user .user-name { font-size: .82rem !important; font-weight: 700 !important; color: #ffffff !important; display: flex; align-items: center; gap: .4rem; }
.sidebar-user .user-email { font-size: .65rem !important; color: var(--muted) !important; margin-top: .18rem; display: block; }

.sidebar-nav-label { font-size: .55rem !important; font-weight: 700 !important; letter-spacing: .18em; text-transform: uppercase; color: var(--muted) !important; padding: .6rem 1.4rem .25rem; display: block; }

[data-testid="stSidebar"] [data-testid="stPageLink"] a {
  display: flex !important; align-items: center !important; gap: .6rem !important;
  padding: .52rem 1.4rem !important; border-radius: 0 !important; font-size: .78rem !important;
  font-weight: 600 !important; color: rgba(239,210,176,0.80) !important; text-decoration: none !important;
  transition: background .18s, color .18s !important; border-left: 3px solid transparent !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover { background: rgba(255,197,112,0.08) !important; color: var(--gold) !important; }
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] a { background: rgba(255,197,112,0.12) !important; color: var(--gold) !important; border-left-color: var(--gold) !important; font-weight: 700 !important; }

[data-testid="stSidebar"] div.stButton > button {
  background: rgba(255,197,112,0.08) !important; color: var(--sand) !important;
  border: 1px solid rgba(255,197,112,0.20) !important; border-radius: 7px !important;
  font-size: .72rem !important; font-weight: 700 !important; padding: .48rem 1rem !important;
  margin: .3rem 1.4rem !important; width: calc(100% - 2.8rem) !important;
}

[data-testid="stAppViewContainer"] { background-color: transparent !important; }
[data-testid="stMain"] { background: var(--off) !important; }
.block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }

/* ⭐️ FIX 2: Added margin-top to push the footer away from the logout button */
.sidebar-footer { 
  padding: 1.5rem 1.4rem 1rem; 
  margin-top: 3.5rem !important; 
  border-top: 1px solid rgba(255,197,112,0.10); 
  text-align: center;
}
.sidebar-footer .ver { font-size: .58rem !important; color: rgba(140,160,180,0.6) !important; text-transform: uppercase; letter-spacing: 0.1em; }
</style>
""", unsafe_allow_html=True)

from datetime import datetime, timedelta, timezone

SESSION_TIMEOUT_MINUTES = 30  # ⏱️ change if needed

import uuid

def set_session(user):
    session_id = str(uuid.uuid4())

    st.session_state.logged_in = True
    st.session_state.local_login = True
    st.session_state.session_id = session_id
    st.session_state.user_email = user.email or ""

    metadata = user.user_metadata or {}
    st.session_state.first_name = metadata.get("first_name", "Admin")
    st.session_state.last_name  = metadata.get("last_name", "")
    st.session_state.login_time = datetime.now(timezone.utc)

    # ✅ on_conflict ensures only ONE row per user, never overwrites another user
    conn.client.table("active_sessions").upsert({
        "user_email": st.session_state.user_email,
        "session_id": session_id,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }, on_conflict="user_email").execute()

def is_valid_session():
    if "session_id" not in st.session_state:
        return False

    # ✅ Filter by THIS user's email only
    res = conn.client.table("active_sessions") \
        .select("session_id") \
        .eq("user_email", st.session_state.user_email) \
        .limit(1) \
        .execute()

    if not res.data:
        return False

    return res.data[0]["session_id"] == st.session_state.session_id

def clear_session():
    try:
        conn.client.table("active_sessions") \
            .delete() \
            .eq("user_email", st.session_state.get("user_email", "")) \
            .execute()
    except Exception:
        pass

    # ✅ Delete cookies
    try:
        cookie_manager.delete("puv_session_id")
        cookie_manager.delete("puv_user_email")
    except Exception:
        pass

    st.session_state.clear()

    try:
        conn.client.auth.sign_out()
    except Exception:
        pass

def is_session_expired():
    if "login_time" not in st.session_state:
        return False

    now = datetime.now(timezone.utc)
    login_time = st.session_state.login_time

    return now - login_time > timedelta(minutes=SESSION_TIMEOUT_MINUTES)


# ── Cookie Manager (dapat sa labas ng function, top-level) ──
@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager(key="puv_cookie_manager")

cookie_manager = stx.CookieManager(key="puv_cookie_manager")

# ── AUTH CHECK ──
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "local_login" not in st.session_state:
    st.session_state.local_login = False

# ✅ Try to restore from cookie on refresh
if not st.session_state.get("logged_in", False):
    cookie_sid   = cookie_manager.get("puv_session_id")
    cookie_email = cookie_manager.get("puv_user_email")

    if cookie_sid and cookie_email:
        try:
            res = conn.client.table("active_sessions") \
                .select("session_id") \
                .eq("user_email", cookie_email) \
                .limit(1) \
                .execute()

            if res.data and res.data[0]["session_id"] == cookie_sid:
                supabase_session = conn.client.auth.get_session()
                if supabase_session and supabase_session.user:
                    metadata = supabase_session.user.user_metadata or {}
                    st.session_state.logged_in    = True
                    st.session_state.local_login  = True
                    st.session_state.session_id   = cookie_sid
                    st.session_state.user_email   = cookie_email
                    st.session_state.first_name   = metadata.get("first_name", "Admin")
                    st.session_state.last_name    = metadata.get("last_name", "")
                    st.session_state.login_time   = datetime.now(timezone.utc)
                    st.rerun()
        except Exception:
            pass

try:
    if st.session_state.get("logged_in", False):
        if not is_valid_session():
            cookie_manager.delete("puv_session_id")
            cookie_manager.delete("puv_user_email")
            clear_session()
            st.warning("Naka-login na ang account mo sa ibang device.")
            st.rerun()

        if is_session_expired():
            cookie_manager.delete("puv_session_id")
            cookie_manager.delete("puv_user_email")
            clear_session()
            st.warning("Session expired. Please log in again.")
            st.rerun()

        st.session_state.login_time = datetime.now(timezone.utc)

    else:
        st.session_state.logged_in   = False
        st.session_state.local_login = False

except Exception:
    st.session_state.logged_in   = False
    st.session_state.local_login = False

# ── 5. Pages ──
login_page       = st.Page("login.py",              title="Log in",              icon="🔐")
dashboard_page   = st.Page("dashboard.py",          title="Sentiment Dashboard", icon="📊")
builder_page     = st.Page("builder.py",            title="Form Builder",        icon="🛠️")
testing_page     = st.Page("sentiment_analysis.py", title="Analysis",            icon="📝")
settings_page    = st.Page("settings.py",           title="Settings",            icon="⚙️")
public_form_page = st.Page("public_form.py",        title="Take Survey",         icon="📋")

# ── 6. Router ──
if "form_id" in st.query_params:
    # Hide sidebar for public commuters taking the survey
    st.html('<style>[data-testid="stSidebarCollapsedControl"] { display: none !important; } [data-testid="stSidebar"] { display: none !important; }</style>')
    pg = st.navigation([public_form_page], position="hidden")

elif st.session_state.get("logged_in", False):
    pg = st.navigation(
        [dashboard_page, builder_page, testing_page, settings_page, public_form_page],
        position="sidebar"
    )

    with st.sidebar:
        st.html("""
        <div class="sidebar-brand">
          <div class="brand-badge"><span>🚌 PUV Analytics</span></div>
          <h2>Sentiment<br><em>Analysis</em> Platform</h2>
        </div>
        """)

        first_name = st.session_state.get("first_name", "Admin")
        last_name  = st.session_state.get("last_name", "")
        user_email = st.session_state.get("user_email", "")
        st.html(f"""
        <div class="sidebar-user">
          <div class="user-name">{first_name} {last_name}</div>
          <span class="user-email">{user_email}</span>
        </div>
        """)

        st.html('<span class="sidebar-nav-label">Navigation</span>')
        st.page_link(dashboard_page)
        st.page_link(testing_page)
        st.page_link(builder_page)
        st.page_link(settings_page)

        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            clear_session()
            st.rerun()

        st.html("""
        <div class="sidebar-footer">
          <span class="ver">PUV Sentiment v1.0</span>
        </div>
        """)

else:
    # Hide sidebar for logged-out users on the login screen
    st.html('<style>[data-testid="stSidebarCollapsedControl"] { display: none !important; } [data-testid="stSidebar"] { display: none !important; }</style>')
    pg = st.navigation([login_page], position="hidden")

pg.run()