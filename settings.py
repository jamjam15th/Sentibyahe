import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection
import requests

# ══════════════════════════════════════════
# 1. SETUP & PAGE CONFIG
# ══════════════════════════════════════════
st.set_page_config(page_title="Settings | Land public transportation", page_icon="⚙️", layout="wide")

# settings.py — top of file
st.session_state["current_page"] = "settings"
st.session_state["_prev_page"] = "settings"

# 🔥 THE NUCLEAR FULL-PAGE LOADER 🔥
# Must go BEFORE Supabase connections and main CSS
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

    /* 1. KEEP SIDEBAR ON TOP OF LOADER */
    [data-testid="stSidebar"], 
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 999999999 !important; /* Highest priority */
    }

    /* 2. COMPLETELY HIDE THE APP ROOT */
    /* visibility: hidden is bulletproof against React hydration overrides */
    .stApp [data-testid="stAppViewBlockContainer"] {
        visibility: hidden !important;
        animation: snapVisible 0.1s forwards 2.5s !important; /* 2.5 seconds wait */
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
        animation: fadeOutNuclear 0.4s ease-out 2.5s forwards; /* Matches the 2.5s wait */
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
    <div class="loading-text">Loading Settings...</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# MAIN CSS SHIELD (Daanalytics Theme)
# ══════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Mulish:wght@300;400;500;600;700&display=swap');

:root {
    --navy:   rgb(26, 50, 99);
    --gold:   rgb(255, 197, 112);
    --steel:  rgb(84, 119, 146);
    --card:   #ffffff;
    --bdr:    rgba(84,119,146,0.2);
    --danger: #b03a2e; 
}

.stAppToolbar { background: #f7f6f2 !important;}
            
.stAppDeployButton { display: none !important; }

*, html, body, p, span, div { font-family: 'Mulish', sans-serif !important; }
.stApp { background-color: #f0f4f8; }

/* 🌟 UNIQUE PREMIUM HEADER 🌟 */
.premium-header {
    background: linear-gradient(135deg, var(--navy) 0%, rgb(40, 75, 140) 100%);
    border-radius: 12px;
    padding: 2.5rem 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 25px rgba(26,50,99,0.15);
    color: white;
}
.premium-header h1 { 
    font-family: 'Libre Baskerville', serif !important; 
    color: #ffffff !important; 
    margin: 0 0 0.5rem 0; 
    font-size: 2.2rem; 
}
.premium-header p { 
    color: #b0bcd8; 
    margin: 0; 
    font-size: 1rem; 
}

/* Red button override for critical actions */
button[kind="primary"] {
    background-color: var(--danger) !important;
    color: white !important;
    border: none !important;
    width: 100% !important; /* Full width for mobile-friendly tapping */
}

/* 📱 RESPONSIVE MOBILE FIXES 📱 */
@media screen and (max-width: 768px) {
    .premium-header {
        padding: 1.5rem 1.2rem !important;
        margin-bottom: 1.2rem !important;
    }
    .premium-header h1 {
        font-size: 1.6rem !important;
    }
    .premium-header p {
        font-size: 0.85rem !important;
    }
    
    /* Responsive Tabs for Settings */
    [data-testid="stTabs"] [role="tablist"] {
        overflow-x: auto;
        flex-wrap: nowrap !important;
        scrollbar-width: none;
    }
    [data-testid="stTabs"] [role="tab"] {
        font-size: 0.8rem !important;
        white-space: nowrap;
    }
}
</style>
""", unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection)

# ══════════════════════════════════════════
# CONFIRMATION DIALOG
# ══════════════════════════════════════════
@st.dialog("Delete Account?")
def confirm_delete_account():
    admin_email = st.session_state.get("user_email")
    st.markdown(
        "⚠️ **This will permanently delete:**\n\n"
        "- All your survey forms\n"
        "- All response data\n"
        "- Your account and login credentials\n\n"
        "**This action cannot be undone.**"
    )
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Delete My Account", type="primary", use_container_width=True):
            try:
                # Get current user ID before deleting
                current_user = conn.client.auth.get_user()
                user_id = current_user.user.id if current_user and current_user.user else None
                
                # Delete all user data in order (respecting foreign key constraints)
                conn.client.table("form_responses").delete().eq("admin_email", admin_email).execute()
                conn.client.table("form_questions").delete().eq("admin_email", admin_email).execute()
                conn.client.table("form_meta").delete().eq("admin_email", admin_email).execute()
                conn.client.table("form_list").delete().eq("admin_email", admin_email).execute()
                conn.client.table("active_sessions").delete().eq("user_email", admin_email).execute()
                
                # Delete the auth user account using Supabase admin API
                # Method 1: Try using secrets from st.secrets (for deployed environments)
                deleted_user = False
                SUPABASE_URL = ""
                SUPABASE_SERVICE_ROLE = ""
                
                # Try to get from st.secrets (may fail if secrets.toml doesn't exist)
                try:
                    SUPABASE_URL = st.secrets.get("connections", {}).get("supabase", {}).get("SUPABASE_URL", "")
                    SUPABASE_SERVICE_ROLE = st.secrets.get("connections", {}).get("supabase", {}).get("SUPABASE_SERVICE_ROLE_KEY", "")
                except Exception:
                    pass  # Secrets file not found, fall back to env vars
                
                # Method 2: Try environment variables (for DigitalOcean with env vars)
                if not SUPABASE_SERVICE_ROLE:
                    import os
                    SUPABASE_URL = SUPABASE_URL or os.getenv("SUPABASE_URL", "")
                    SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
                
                if SUPABASE_URL and SUPABASE_SERVICE_ROLE and user_id:
                    try:
                        # Use admin API to delete user
                        import requests
                        headers = {
                            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE}",
                            "apikey": SUPABASE_SERVICE_ROLE,
                            "Content-Type": "application/json"
                        }
                        delete_url = f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}"
                        response = requests.delete(delete_url, headers=headers)
                        if response.status_code in [200, 204]:
                            deleted_user = True
                        else:
                            st.warning(f"⚠️ Auth deletion status: {response.status_code}")
                    except Exception as auth_error:
                        st.warning(f"⚠️ Could not delete auth via admin API: {auth_error}")
                elif user_id and not SUPABASE_SERVICE_ROLE:
                    st.warning("⚠️ SUPABASE_SERVICE_ROLE_KEY not configured - auth credentials not deleted. Please delete your password separately in Account Settings.")
                
                # Sign out from Supabase Auth
                try:
                    conn.client.auth.sign_out()
                except Exception:
                    pass
                
                # Clear session state
                st.session_state.clear()
                st.success("✅ Account deleted successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Error deleting account: {e}")
    
    with c2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

# ══════════════════════════════════════════
# 2. AUTHENTICATION CHECK & SESSION RECOVERY
# ══════════════════════════════════════════
# Priority 1: Check URL query params (survives reload)
admin_email = None
session_id_from_url = st.query_params.get("session_id")

if session_id_from_url:
    try:
        # Restore user from database using session_id from URL
        result = conn.client.table("active_sessions").select("user_email").eq("session_id", session_id_from_url).execute()
        if result.data:
            admin_email = result.data[0].get("user_email")
            st.session_state.user_email = admin_email
            st.session_state.session_id = session_id_from_url
            st.session_state.logged_in = True
    except Exception:
        pass

# Priority 2: Check session state (cache from previous interaction)
if not admin_email:
    admin_email = st.session_state.get("user_email")
    session_id = st.session_state.get("session_id")
    
    # If we have session_id in state but not email, try to restore from DB
    if session_id and not admin_email:
        try:
            result = conn.client.table("active_sessions").select("user_email").eq("session_id", session_id).execute()
            if result.data:
                admin_email = result.data[0].get("user_email")
                st.session_state.user_email = admin_email
                # Add to URL for future reloads
                st.query_params["session_id"] = session_id
        except Exception:
            pass

# If no email found, redirect to login
if not admin_email:
    st.error("🔒 Please log in to view settings.")
    st.stop()

# CRITICAL: Persist session_id in URL so it survives reloads and navigation
if session_id_from_url and "session_id" not in st.query_params:
    st.query_params["session_id"] = session_id_from_url
elif st.session_state.get("session_id") and "session_id" not in st.query_params:
    st.query_params["session_id"] = st.session_state.get("session_id")

st.markdown("""
<div class="premium-header">
    <div>
        <h1>System Settings</h1>
        <p>Manage your researcher profile and survey data exports.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# 3. TABS LAYOUT
# ══════════════════════════════════════════
tab1, tab2 = st.tabs(["👤 Profile & Security", "💾 Data Management"])

# ── TAB 1: PROFILE & SECURITY ──
with tab1:
    # On mobile, Streamlit automatically turns this into 1 column
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### 👤 Profile Details")
        st.text_input("Account Email", value=admin_email, disabled=True)
        
        current_name = st.session_state.get("user_name", "")
        new_name = st.text_input("Full Name", value=current_name, placeholder="e.g., Juan Dela Cruz")
        
        if st.button("💾 Update Name"):
            try:
                conn.client.auth.update_user({"data": {"full_name": new_name}})
                st.session_state.user_name = new_name
                st.success("✅ Name updated successfully!")
            except Exception as e:
                st.error(f"⚠️ Error updating name: {e}")

    with c2:
        st.markdown("### 🔐 Change Password")
        new_pw = st.text_input("New Password", type="password", placeholder="Enter new password")
        confirm_pw = st.text_input("Confirm New Password", type="password", placeholder="Re-enter new password")
        
        if st.button("🔑 Update Password"):
            if new_pw and new_pw == confirm_pw:
                if len(new_pw) >= 6:
                    try:
                        conn.client.auth.update_user({"password": new_pw})
                        st.success("✅ Password updated!")
                    except Exception as e:
                        st.error(f"⚠️ Error: {e}")
                else:
                    st.warning("⚠️ Min. 6 characters.")
            elif new_pw != confirm_pw:
                st.error("⚠️ Passwords do not match.")
                
    st.divider()
    
    st.markdown("<h3 style='color: #b03a2e; margin-top: 0;'>🛑 Delete Account</h3>", unsafe_allow_html=True)
    st.write("This will permanently delete everything. **Action cannot be undone.**")
    
    del_confirm = st.text_input("To confirm, type exactly: **DELETE MY ACCOUNT**")
    
    delete_enabled = del_confirm == "DELETE MY ACCOUNT"
    if st.button("🗑️ Permanently Delete Account", type="primary", disabled=not delete_enabled):
        confirm_delete_account()

    st.divider()

    st.markdown("### 📝 Sentiment Analysis")
    st.write("Run AI-powered sentiment analysis on your collected survey responses.")

    if st.button("📝 Go to Analysis", use_container_width=True):
        st.switch_page("sentiment_analysis.py")

# ── TAB 2: DATA MANAGEMENT ──
with tab2:
    st.markdown("### Export Dataset")
    st.write("Download response data.")
    
    try:
        res = conn.client.table("form_responses").select("*").eq("admin_email", admin_email).execute()
        responses = res.data or []
        
        if not responses:
            st.warning("No data yet.")
        else:
            flat_data = []
            for r in responses:
                row = {"Submission ID": r.get("id"), "Timestamp": r.get("created_at")}
                row.update(r.get("answers", {}))
                flat_data.append(row)
                
            df_export = pd.DataFrame(flat_data)
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Download Data",
                data=csv_data,
                file_name="survey_dataset_export.csv",
                mime="text/csv",
                use_container_width=True
            )
            
    except Exception as e:
        st.error(f"Error: {e}")

    st.divider()
    
    st.markdown("<h3 style='color: #b03a2e; margin-top: 0;'>⚠️ Wipe Data</h3>", unsafe_allow_html=True)
    st.write("Delete all responses but keep questions. Useful for resetting test data.")
    
    wipe_confirm = st.checkbox("I understand this is permanent.", key="wipe_checkbox")
    if st.button("🗑️ Wipe All Survey Responses", disabled=not wipe_confirm, type="primary"):
        try:
            conn.client.table("form_responses").delete().eq("admin_email", admin_email).execute()
            st.success("✅ Data wiped clean.")
            st.balloons()
        except Exception as e:
            st.error(f"Failed: {e}")