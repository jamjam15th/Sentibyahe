import streamlit as st
from st_supabase_connection import SupabaseConnection

# 1. Setup Page Config
st.set_page_config(page_title="Thesis App", layout="wide")

# 2. Initialize Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 3. Define the Pages
login_page = st.Page("login.py", title="Log in", icon="🔐")
testing_page = st.Page("sentiment_analysis.py", title="Testing", icon="📝")
builder_page = st.Page("builder.py", title="Form Builder", icon="🛠️")
settings_page = st.Page("settings.py", title="Settings", icon="⚙️")
public_form_page = st.Page("public_form.py", title="Take Survey", icon="📝", url_path="survey")
dashboard_page = st.Page("dashboard.py", title="Sentiment Dashboard", icon="📊")

# 4. The Router Logic
if st.session_state.logged_in:
    # If logged in, show the Dashboard

    pg = st.navigation([dashboard_page, builder_page, testing_page, settings_page, public_form_page], position="hidden")

    with st.sidebar:
        st.write(f"**{st.session_state.user_email}**")
        st.divider()

        st.page_link(dashboard_page)
        st.page_link(testing_page)
        st.page_link(builder_page)
        st.page_link(public_form_page)
        st.page_link(settings_page)

        # The Logout Button
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()
else:
    # If NOT logged in, ONLY show the Login Page
    pg = st.navigation({
        "Commuter Survey": [public_form_page], # <--- THIS IS FIRST!
        "Admin Access": [login_page]
    })
# 5. Run the selected page
pg.run()