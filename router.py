import streamlit as st

# 1. Setup Page Config
st.set_page_config(page_title="Thesis App", layout="wide")

# --- GLOBAL CSS FIX ---
# We move this to the top so it's always active, forcing the toggle to show.
st.markdown("""
    <style>
        /* Force the sidebar toggle button to exist and be visible */
        [data-testid="stSidebarCollapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            left: 0 !important;
        }
        
        /* Hide the default navigation links so they don't double up */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# 2. Initialize Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 3. Define ALL Available Pages
login_page = st.Page("login.py", title="Log in", icon="🔐")
testing_page = st.Page("sentiment_analysis.py", title="Testing", icon="📝")
builder_page = st.Page("builder.py", title="Form Builder", icon="🛠️")
settings_page = st.Page("settings.py", title="Settings", icon="⚙️")
public_form_page = st.Page("public_form.py", title="Take Survey", icon="📝")
dashboard_page = st.Page("dashboard.py", title="Sentiment Dashboard", icon="📊")

# --- 4. THE ROUTER LOGIC ---

query_params = st.query_params

# SCENARIO A: A commuter clicked a shareable link
if "form_id" in query_params:
    pg = st.navigation([public_form_page], position="hidden")

# SCENARIO B: An Admin is fully logged in
elif st.session_state.logged_in:
    # Use position="sidebar" to ensure the container exists
    pg = st.navigation(
        [dashboard_page, builder_page, testing_page, settings_page, public_form_page], 
        position="sidebar"
    )

    with st.sidebar:
        first_name = st.session_state.get("first_name", "Admin")
        last_name = st.session_state.get("last_name", "")
        st.write(f"👤 **{first_name} {last_name}**")
        st.caption(st.session_state.get("user_email", ""))
        
        st.divider()

        st.page_link(dashboard_page)
        st.page_link(testing_page)
        st.page_link(builder_page)
        st.page_link(settings_page)

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            for key in ["user_email", "first_name", "last_name"]:
                st.session_state[key] = ""
            st.rerun()

# SCENARIO C: Default landing
else:
    pg = st.navigation([login_page], position="hidden")

# 5. Run the selected page
pg.run()