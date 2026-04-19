import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from styles import SHARED_CSS
from auth import login_user

st.set_page_config(
    page_title="Corporate Smart Messenger – Login",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# Redirect if already logged in
if st.session_state.get("logged_in"):
    if st.session_state.get("role") == "admin":
        st.switch_page("pages/admin_dashboard.py")
    else:
        st.switch_page("pages/user_dashboard.py")

# Show signup success message
if st.session_state.pop("signup_success", False):
    st.success("✅ Signed up successfully! Please log in.")

st.markdown("<h1 style='text-align: center; margin-bottom: 0.5rem;'>🏢 Corporate Smart Messenger</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4a5568; font-size: 18px; margin-bottom: 2rem;'>Welcome back! Please sign in to continue</p>", unsafe_allow_html=True)

# Login form
st.markdown("""
<div class="login-container">
    <div class="login-card">
        <div class="login-header">
            <h2>🏢 Welcome Back</h2>
            <p>Sign in to your Corporate Smart Messenger</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Login ID format help
with st.expander("ℹ️ Login ID Format Help"):
    st.markdown("""
    **Login ID Format:** `[Department Code][Role Code][6-Digit Number]`
    
    **Department Codes:**
    - `dev` = Developer
    - `hrs` = Human Resources  
    - `fin` = Finance
    - `mkt` = Marketing
    - `sal` = Sales
    - `sup` = Support
    
    **Role Codes:**
    - `adm` = Admin
    - `man` = Manager
    - `asm` = Assistant Manager
    - `tld` = Team Lead
    - `sen` = Senior Employee
    - `clk` = Clerk
    - `int` = Intern
    
    **Examples:**
    - `devadm000000` (Developer Admin)
    - `hrsmen000001` (HR Manager)
    - `fintld000002` (Finance Team Lead)
    """)

with st.form("login_form", clear_on_submit=False):
    login_id = st.text_input(
        "� Corporate Login ID", 
        placeholder="Enter your login ID (e.g., devadm000000)",
        help="Format: [Department][Role][6-digit number]"
    )
    password = st.text_input(
        "� Password", 
        type="password",
        placeholder="Enter your password",
        help="Your secure corporate password"
    )
    
    submitted = st.form_submit_button("🚀 Sign In to Workspace", use_container_width=True)
    
    if submitted:
        if login_id and password:
            success, message, user_data = login_user(login_id, password)
            
            if success and user_data:
                # Store user info in session state
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user_data.get("login_id")  # ← FIXED: set user_id for RAG
                st.session_state["first_name"] = user_data["first_name"]
                st.session_state["last_name"] = user_data["last_name"]
                st.session_state["role"] = user_data["role"]
                st.session_state["role_code"] = user_data["role_code"]
                st.session_state["department"] = user_data["department"]
                st.session_state["department_code"] = user_data["department_code"]
                st.session_state["login_id"] = user_data["login_id"]
                st.session_state["password_changed"] = user_data["password_changed"]
                
                # Check if password change is required
                if not user_data["password_changed"]:
                    st.session_state["force_password_change"] = True
                    st.switch_page("pages/change_password.py")
                elif user_data["role"] == "admin":
                    st.session_state["login_toast"] = True
                    st.switch_page("pages/admin_dashboard.py")
                else:
                    st.session_state["login_toast"] = True
                    st.switch_page("pages/user_dashboard.py")
            else:
                st.error(f"❌ {message}")
        else:
            st.error("⚠️ Please enter both your login ID and password to continue.")

# Footer
st.markdown("""
<div class="login-footer">
    <p>🔐 Secure Corporate Communication System</p>
    <p style="font-size: 0.8rem; color: #666;">
        Contact your department administrator for login credentials
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📝 Need an Account? Contact Your Admin", type="secondary", use_container_width=True):
        st.info("💡 Please contact your department administrator to get your login credentials.")