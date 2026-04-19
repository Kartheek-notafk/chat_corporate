import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from styles import SHARED_CSS
from auth import change_password

st.set_page_config(
    page_title="User Dashboard – CSM",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(SHARED_CSS, unsafe_allow_html=True)
st.markdown("""
<style>

/* App Background */
.stApp{
    background:#F7F3EC;
}

/* GLOBAL TEXT = FULL BLACK */
html, body, p, span, div, label, small, strong,
h1, h2, h3, h4, h5, h6, li {
    color:#000000 !important;
}

/* Streamlit generated text */
[class*="css"] {
    color:#000000 !important;
}

/* Dashboard Cards */
.dash-card{
    background:#FFFDF8;
    border:2px solid #C9B28A;
    border-radius:12px;
    padding:1rem;
    margin:0.5rem;
    color:#000000 !important;
}

/* Buttons */
.stButton > button{
    background:#A87B33 !important;
    color:#FFFFFF !important;
    border:none;
    border-radius:10px;
    font-weight:700;
}

.stButton > button:hover{
    background:#8C662A !important;
    color:#FFFFFF !important;
}

/* Brown Header Section */
.user-info-card{
    background:linear-gradient(135deg,#A87B33 0%, #8C662A 100%);
    border-radius:12px;
    padding:1.5rem;
}

/* Keep white text only here */
.user-info-card,
.user-info-card h1,
.user-info-card h2,
.user-info-card h3,
.user-info-card h4,
.user-info-card p,
.user-info-card span,
.user-info-card strong{
    color:#FFFFFF !important;
}

/* Inputs */
input, textarea,
.stTextInput input,
.stTextArea textarea{
    color:#000000 !important;
    background:#FFFFFF !important;
    border:1px solid #C9B28A !important;
}

/* Selectbox */
.stSelectbox *{
    color:#000000 !important;
}

/* Checkbox / Radio */
.stCheckbox label,
.stRadio label{
    color:#000000 !important;
}

/* Chat */
[data-testid="stChatMessage"] *{
    color:#000000 !important;
}

/* Expander */
.streamlit-expanderHeader{
    color:#000000 !important;
}

/* Tables */
table, th, td{
    color:#000000 !important;
}

</style>
""", unsafe_allow_html=True)

# Auth guard
if not st.session_state.get("logged_in"):
    st.switch_page("pages/streamlit_login.py")

if st.session_state.get("role") == "admin":
    st.switch_page("pages/admin_dashboard.py")

# Login success toast
if st.session_state.pop("login_toast", False):
    st.toast(f"✅ Login successful! Welcome, {st.session_state['first_name']}!", icon="🎉")

# Header with user info
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.markdown(f"## 💬 User Dashboard")
    st.markdown(f"Welcome, **{st.session_state['first_name']} {st.session_state['last_name']}**")
with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
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

# Dashboard Features Grid - 2x2 Layout
row1_col1, row1_col2 = st.columns(2, gap="small")
row2_col1, row2_col2 = st.columns(2, gap="small")

with row1_col1:
    if st.button("💬\n\n**Messages**\n\n0 unread messages\n\n**View**", key="messages_view_btn", use_container_width=True):
        st.switch_page("pages/messages.py")

with row1_col2:
    if st.button("📅\n\n**Calendar**\n\nSchedule & events\n\n**Open**", key="calendar_open_btn", use_container_width=True):
        st.switch_page("pages/calendar.py")

with row2_col1:
    if st.button("🤖\n\n**Chatbot**\n\nAI assistant\n\n**Chat**", key="chatbot_chat_btn", use_container_width=True):
        st.session_state["selected_feature"] = "chatbot"
        st.rerun()

with row2_col2:
    if st.button("⚙️\n\n**Settings**\n\nPreferences\n\n**Config**", key="settings_config_btn", use_container_width=True):
        st.session_state["selected_feature"] = "settings"
        st.rerun()

from rag_assistant import answer
# Feature Details Section
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
            st.session_state["chatbot_messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.spinner("Thinking..."):
                try:
                    user_id = st.session_state.get("user_id", "")
                    bot_response = answer(prompt, user_id)
                except Exception as e:
                    bot_response = f"Sorry, I encountered an error: {str(e)}"

            st.session_state["chatbot_messages"].append({"role": "assistant", "content": bot_response})
            with st.chat_message("assistant"):
                st.write(bot_response)

        col_clear, _ = st.columns([1, 3])
        with col_clear:
            if st.button("Clear Selection", use_container_width=True):
                st.session_state.pop("selected_feature", None)
                st.rerun()

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
        st.markdown("**Change Password**")
        with st.expander("🔑 Change Your Password"):
            with st.form("change_password_form"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")

                submitted = st.form_submit_button("Change Password", type="primary")

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
            if st.button("Save Settings", type="primary", use_container_width=True):
                st.success("Settings saved successfully!")
        with col_clear:
            if st.button("Clear Selection", use_container_width=True):
                st.session_state.pop("selected_feature", None)
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)