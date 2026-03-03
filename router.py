import streamlit as st

# 1. Setup Page Config
st.set_page_config(page_title="Thesis App", layout="wide")

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

# SCENARIO A: A commuter clicked a shareable link (/?form_id=...)
query_params = st.query_params
if "form_id" in query_params:
    # If the URL has a form_id, force Streamlit to ONLY load the public form.
    # No sidebar, no login, just the survey!
    pg = st.navigation([public_form_page], position="sidebar")

# SCENARIO B: An Admin is fully logged in
elif st.session_state.logged_in:
    # Load all the admin tools and hide the default ugly Streamlit menu
    pg = st.navigation([dashboard_page, builder_page, testing_page, settings_page, public_form_page], position="sidebar")

    # 2. Add this CSS to hide the 'default' menu but keep the 'arrow' toggle
    st.markdown("""
        <style>
            /* Hides the default Streamlit nav links */
            [data-testid="stSidebarNav"] {display: none;}
            
            /* Ensures the sidebar toggle (arrow) is always visible */
            [data-testid="stSidebarCollapsedControl"] {
                display: flex;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Build your custom, beautiful sidebar
    with st.sidebar:
        first_name = st.session_state.get("first_name", "Admin")
        last_name = st.session_state.get("last_name", "")
        st.write(f"👤 **{first_name} {last_name}**")
        st.caption(st.session_state.get("user_email", ""))
        
        st.divider()

        st.page_link(dashboard_page)
        st.page_link(testing_page)
        st.page_link(builder_page)
        # Note: I removed the public form from the admin sidebar to keep things clean!
        # You can test your form by clicking the shareable link in the builder instead.
        st.page_link(settings_page)

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.first_name = "" 
            st.session_state.last_name = ""
            st.rerun()

# SCENARIO C: Someone goes to the base URL without logging in (The default landing)
else:
    # Only show the login page
    pg = st.navigation([login_page], position="hidden")

# 5. Run the selected page
pg.run()