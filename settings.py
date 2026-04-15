import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection

# ══════════════════════════════════════════
# 1. SETUP & CSS SHIELD (Daanalytics Theme)
# ══════════════════════════════════════════
st.set_page_config(page_title="Settings | Land public transportation", page_icon="⚙️", layout="wide")

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
# 2. AUTHENTICATION CHECK
# ══════════════════════════════════════════
admin_email = st.session_state.get("user_email")
if not admin_email:
    st.error("🔒 Please log in to view settings.")
    st.stop()

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

        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out"):
            st.session_state.clear()
            st.rerun()

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
    
    if st.button("🗑️ Permanently Delete Account", type="primary"):
        if del_confirm == "DELETE MY ACCOUNT":
            try:
                conn.client.table("form_responses").delete().eq("admin_email", admin_email).execute()
                conn.client.table("form_questions").delete().eq("admin_email", admin_email).execute()
                conn.client.table("form_meta").delete().eq("admin_email", admin_email).execute()
                
                try:
                    conn.client.rpc('delete_user').execute()
                except Exception:
                    pass 
                
                st.session_state.clear()
                st.success("Account deleted.")
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Error: {e}")
        else:
            st.error("⚠️ Confirmation text incorrect.")

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
                label="📥 Download Dataset (CSV)",
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