import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from styles import SHARED_CSS
from auth import change_password

st.set_page_config(
    page_title="Change Password – CSM",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# Auth guard - must be logged in
if not st.session_state.get("logged_in"):
    st.switch_page("../streamlit_login.py")

# Check if password change is forced
if not st.session_state.get("force_password_change", False):
    st.warning("You can change your password from Settings.")
    if st.button("Go to Dashboard", use_container_width=True):
        if st.session_state.get("role") == "admin":
            st.switch_page("pages/admin_dashboard.py")
        else:
            st.switch_page("pages/user_dashboard.py")
    st.stop()

st.markdown("""
<div class="login-container">
    <div class="login-card">
        <div class="login-header">
            <h2>🔐 Change Password</h2>
            <p>You must change your password on first login</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# User info
st.info(f"**Login ID:** {st.session_state.get('login_id', 'Unknown')}")
st.info(f"**Name:** {st.session_state.get('first_name', '')} {st.session_state.get('last_name', '')}")

# Password requirements
with st.expander("📋 Password Requirements"):
    st.markdown("""
    Your password must contain:
    - ✅ At least 8 characters
    - ✅ At least one uppercase letter (A-Z)
    - ✅ At least one number (0-9)
    - ✅ At least one special character (@, #, $, %, etc.)
    """)

with st.form("change_password_form", clear_on_submit=False):
    st.markdown("### 🔒 Change Your Password")
    
    current_password = st.text_input(
        "Current Password",
        type="password",
        help="Enter your current password (same as your login ID)"
    )
    
    new_password = st.text_input(
        "New Password",
        type="password",
        help="Choose a strong password that meets the requirements"
    )
    
    confirm_password = st.text_input(
        "Confirm New Password",
        type="password",
        help="Re-enter your new password to confirm"
    )
    
    submitted = st.form_submit_button("Change Password", use_container_width=True, type="primary")
    
    if submitted:
        if current_password and new_password and confirm_password:
            login_id = st.session_state.get("login_id")
            success, message = change_password(login_id, current_password, new_password, confirm_password)
            
            if success:
                st.success(f"✅ {message}")
                
                # Update session state
                st.session_state["password_changed"] = True
                st.session_state.pop("force_password_change", None)
                
                # Show success message and redirect
                st.balloons()
                st.markdown("### 🎉 Password Changed Successfully!")
                st.markdown("You will be redirected to your dashboard in 3 seconds...")
                
                # Auto-redirect after delay
                import time
                time.sleep(3)
                
                if st.session_state.get("role") == "admin":
                    st.switch_page("pages/admin_dashboard.py")
                else:
                    st.switch_page("pages/user_dashboard.py")
            else:
                st.error(f"❌ {message}")
        else:
            st.error("❌ Please fill in all password fields.")

# Cancel button outside the form
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("Cancel", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/streamlit_login.py")

# Additional security note
st.markdown("""
<div class="security-note">
    <p style="font-size: 0.8rem; color: #666; text-align: center;">
        🔒 Your password is encrypted and stored securely. 
        Never share your password with anyone.
    </p>
</div>
""", unsafe_allow_html=True)
