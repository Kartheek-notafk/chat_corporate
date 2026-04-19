import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from styles import SHARED_CSS
from database import get_users_collection, get_registered_users
from auth import register_user, change_password, DEPARTMENTS, ROLES

st.set_page_config(
    page_title="Admin Dashboard – CSM",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(SHARED_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
.dash-card {
    transition: all 0.3s ease;
    cursor: pointer;
    border: 2px solid #d0d0d0;
    border-radius: 10px;
    background-color: #ffffff;
    padding: 1rem;
    margin: 0.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.dash-card:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    background-color: #fafafa;
}
.stButton > button {
    background-color: #A87B33 !important;
    color: white !important;
    border: none;
    border-radius: 8px;
    padding: 0.5rem;
    font-weight: bold;
    transition: all 0.3s ease;
    margin-top: 0.5rem;
}
.stButton > button:hover {
    background-color: #8C662A !important;
    transform: scale(1.05);
    box-shadow: 0 4px 15px rgba(168, 123, 51, 0.3);
}
.user-info-card {
    background: linear-gradient(135deg, #A87B33 0%, #8C662A 100%);
    color: white;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 15px rgba(168, 123, 51, 0.3);
}
.role-badge-admin {
    background-color: #1a1a1a;
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8em;
}
</style>
""", unsafe_allow_html=True)

# Auth guard – admins only
if not st.session_state.get("logged_in"):
    st.switch_page("../streamlit_login.py")

if st.session_state.get("role") != "admin":
    st.error("⛔ Access denied. Admin privileges required.")
    st.stop()

# Login success toast
if st.session_state.pop("login_toast", False):
    st.toast(f"✅ Login successful! Welcome, {st.session_state['first_name']}!", icon="🎉")

# Header with user info
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.markdown(f"## 🛡️ Admin Dashboard &nbsp;<span class='role-badge-admin'>ADMIN</span>", unsafe_allow_html=True)
    st.markdown(f"Welcome, **{st.session_state['first_name']} {st.session_state['last_name']}**")
with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True):
        for k in ("logged_in", "role", "first_name", "last_name"):
            st.session_state.pop(k, None)
        st.switch_page("pages/streamlit_login.py")

# User information card
st.markdown(f"""
<div class="user-info-card">
    <h3>👋 Welcome back, {st.session_state['first_name']}!</h3>
    <p><strong>🏢 Department:</strong> {st.session_state.get('department', 'N/A')}</p>
    <p><strong>💼 Role:</strong> {st.session_state.get('role', 'N/A')}</p>
    <p><strong>🔑 Login ID:</strong> {st.session_state.get('login_id', 'N/A')}</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# Dashboard Features Grid - 3x2 Layout
row1_col1, row1_col2 = st.columns(2, gap="small")
row2_col1, row2_col2 = st.columns(2, gap="small")
row3_col1, row3_col2 = st.columns(2, gap="small")

# Messages Feature - Top Left
with row1_col1:
    if st.button("💬\n\n**Messages**\n\nTeam communications\n\n**Open Chat**", key="messages_view_btn", use_container_width=True):
        st.switch_page("pages/messages.py")

# Calendar Feature - Top Right
with row1_col2:
    if st.button("📅\n\n**Calendar**\n\nEvents & meetings\n\n**View Schedule**", key="calendar_open_btn", use_container_width=True):
        st.switch_page("pages/calendar.py")

# Chatbot Feature - Middle Left
with row2_col1:
    if st.button("🤖\n\n**AI Assistant**\n\nSmart help & insights\n\n**Start Chat**", key="chatbot_chat_btn", use_container_width=True):
        st.session_state["selected_feature"] = "chatbot"
        st.rerun()

# Settings Feature - Middle Right
with row2_col2:
    if st.button("⚙️\n\n**Settings**\n\nAccount & preferences\n\n**Configure**", key="settings_config_btn", use_container_width=True):
        st.session_state["selected_feature"] = "settings"
        st.rerun()

# Register New User - Bottom Left
with row3_col1:
    if st.button("👥\n\n**Add Employee**\n\nRegister new team member\n\n**Create Account**", key="register_user_btn", use_container_width=True):
        st.session_state["selected_feature"] = "register"
        st.rerun()

# View Users - Bottom Right
with row3_col2:
    if st.button("📋\n\n**Team Directory**\n\nManage team members\n\n**View All**", key="view_users_btn", use_container_width=True):
        st.session_state["selected_feature"] = "view"
        st.rerun()

# Feature Details Section (only for selected inline features)
if "selected_feature" in st.session_state:
    st.divider()
    
    if st.session_state["selected_feature"] == "chatbot":
        st.markdown("#### 🤖 AI Chatbot Assistant")
        if "chatbot_messages" not in st.session_state:
            st.session_state["chatbot_messages"] = []

        for m in st.session_state["chatbot_messages"]:
            with st.chat_message(m["role"]):
                st.write(m["content"])

        prompt = st.chat_input("Ask me anything...")
        if prompt:
            st.session_state["chatbot_messages"].append({"role":"user","content":prompt})

            with st.chat_message("user"):
                st.write(prompt)

            with st.spinner("Thinking..."):
                from rag_assistant import answer
                user_id = st.session_state.get("user_id", "")
                bot_response = answer(prompt, user_id, None)

            st.session_state["chatbot_messages"].append({"role":"assistant","content":bot_response})

            with st.chat_message("assistant"):
                st.write(bot_response)
        
        col_clear, _ = st.columns([1, 3])
        with col_clear:
            if st.button("❌ Close Chat", use_container_width=True):
                st.session_state.pop("selected_feature", None)
                st.rerun()
                
    elif st.session_state["selected_feature"] == "register":
        st.markdown("#### 👥 Register New User")
        st.markdown("<div class='dash-card' style='padding: 1rem;'>", unsafe_allow_html=True)
        st.markdown("Fill in the details below to register a new employee.")
        
        with st.form("register_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("First Name*", help="Employee's first name")
                last_name = st.text_input("Last Name*", help="Employee's last name")
            
            with col2:
                # Department dropdown
                dept_options = [(code, name) for code, name in DEPARTMENTS.items()]
                selected_dept = st.selectbox(
                    "Department*",
                    options=[code for code, name in dept_options],
                    format_func=lambda x: next(name for code, name in dept_options if code == x),
                    help="Select the employee's department"
                )
                
                # Role dropdown (exclude admin for regular users)
                role_options = [(code, name) for code, name in ROLES.items() if code != "adm"]
                selected_role = st.selectbox(
                    "Role*",
                    options=[code for code, name in role_options],
                    format_func=lambda x: next(name for code, name in role_options if code == x),
                    help="Select the employee's role"
                )
            
            st.markdown("---")
            
            col_submit, col_cancel = st.columns([1, 1])
            with col_submit:
                submitted = st.form_submit_button("✅ Create Employee Account", type="primary", use_container_width=True)
            with col_cancel:
                if st.form_submit_button("❌ Close", use_container_width=True):
                    st.session_state.pop("selected_feature", None)
                    st.rerun()
            
            if submitted:
                if first_name and last_name and selected_dept and selected_role:
                    success, message, login_id, initial_password = register_user(
                        first_name, last_name, selected_dept, selected_role
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        
                        # Show generated credentials
                        st.markdown("#### 🔑 Generated Credentials")
                        st.markdown(f"""
                        <div style="background-color: #f0f2f5; padding: 1rem; border-radius: 8px;">
                            <p><strong>Login ID:</strong> <code>{login_id}</code></p>
                            <p><strong>Initial Password:</strong> <code>{initial_password}</code></p>
                            <p><strong>Department:</strong> {DEPARTMENTS[selected_dept]}</p>
                            <p><strong>Role:</strong> {ROLES[selected_role]}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.info("📋 Please share these credentials with the employee. They will need to change their password on first login.")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all required fields.")
                    
        st.markdown("</div>", unsafe_allow_html=True)
        
    elif st.session_state["selected_feature"] == "view":
        st.markdown("#### 📋 View Department Users")
        st.markdown("<div class='dash-card' style='padding: 1rem;'>", unsafe_allow_html=True)
        
        admin_dept = st.session_state.get('department_code')
        users_col = get_users_collection()
        
        # Get count of users under them
        num_users = users_col.count_documents({"department_code": admin_dept, "role": {"$ne": "admin"}})
        
        st.markdown(f"**Total users under your department ({DEPARTMENTS.get(admin_dept, 'N/A')}):** {num_users}")
        
        # Get actual users
        dept_users = list(users_col.find({"department_code": admin_dept, "role": {"$ne": "admin"}}, {"password_hash": 0}).sort("created_at", -1))
        
        if dept_users:
            header = st.columns([2, 2, 3, 2])
            for col, label in zip(header, ["First Name", "Last Name", "Login ID", "Role"]):
                col.markdown(f"**{label}**")
            st.divider()
            
            for u in dept_users:
                row = st.columns([2, 2, 3, 2])
                row[0].write(u.get("first_name", "N/A"))
                row[1].write(u.get("last_name", "N/A"))
                row[2].write(f"`{u.get('login_id', 'N/A')}`")
                row[3].write(u.get("role", "N/A"))
                
                with st.expander(f"View specific details and credentials for {u.get('first_name', '')}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Created At:** {u.get('created_at', 'N/A')}")
                        password_status = "✅ Changed" if u.get('password_changed', False) else "⚠️ Not Changed"
                        st.write(f"**Password Status:** {password_status}")
                    with c2:
                        st.write(f"**Initial Password:** `{u.get('login_id', 'N/A')}`")
                        if st.button(f"📋 Copy Credentials", key=f"copy_{u.get('_id', u.get('login_id'))}"):
                            credentials = f"Login ID: {u.get('login_id', 'N/A')}\nPassword: {u.get('login_id', 'N/A')}\nName: {u.get('first_name', '')} {u.get('last_name', '')}\nDepartment: {u.get('department', 'N/A')}\nRole: {u.get('role', 'N/A')}"
                            st.code(credentials)
                            st.success("Credentials ready for copying!")
        else:
            st.info("No users found in your department.")
            
        col_clear, _ = st.columns([1, 1])
        with col_clear:
            if st.button("❌ Close Directory", use_container_width=True):
                st.session_state.pop("selected_feature", None)
                st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)
        
    elif st.session_state["selected_feature"] == "settings":
        st.markdown("#### ⚙️ Settings")
        st.markdown("<div class='dash-card' style='padding: 1rem;'>", unsafe_allow_html=True)
        
        st.markdown("**👤 Profile Information**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {st.session_state['first_name']} {st.session_state['last_name']}")
            st.markdown(f"**Login ID:** {st.session_state.get('login_id', 'N/A')}")
        with col2:
            st.markdown(f"**Department:** {st.session_state.get('department', 'N/A')}")
            st.markdown(f"**Role:** {st.session_state.get('role', 'N/A')}")
        
        st.markdown("---")
        
        st.markdown("**🔐 Security Settings**")
        
        # Password change section
        st.markdown("**Change Password**")
        with st.expander("🔑 Change Your Password"):
            with st.form("change_password_form"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                
                submitted = st.form_submit_button("🔐 Update Password", type="primary")
                
                if submitted:
                    if current_password and new_password and confirm_password:
                        login_id = st.session_state.get('login_id')
                        success, message = change_password(login_id, current_password, new_password, confirm_password)
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.session_state["password_changed"] = True
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Please fill in all password fields.")
        
        st.markdown("---")
        
        st.markdown("**🔔 Notification Preferences**")
        col1, col2 = st.columns(2)
        with col1:
            email_notifications = st.checkbox("Email notifications", value=True)
        with col2:
            push_notifications = st.checkbox("Push notifications", value=True)
        
        st.markdown("---")
        
        st.markdown("**🎨 Appearance**")
        theme = st.selectbox("Theme", ["Light", "Dark"], index=0)
        
        st.markdown("---")
        
        col_save, col_clear = st.columns([1, 1])
        with col_save:
            if st.button("💾 Save Settings", type="primary", use_container_width=True):
                st.success("Settings saved successfully!")
        with col_clear:
            if st.button("❌ Close Settings", use_container_width=True):
                st.session_state.pop("selected_feature", None)
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
