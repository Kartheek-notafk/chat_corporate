import streamlit as st
import sys, os

# Add backend and frontend paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
sys.path.insert(0, os.path.dirname(__file__))

from styles import SHARED_CSS

st.set_page_config(
    page_title="Chat Application",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(SHARED_CSS, unsafe_allow_html=True)

# Simple navigation logic
if "page" not in st.session_state:
    st.session_state.page = "home"

# Navigation buttons
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
with col1:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()
with col2:
    if st.button("🔑 Login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
with col3:
    if st.button("📝 Sign Up", use_container_width=True):
        st.session_state.page = "signup"
        st.rerun()
with col4:
    if st.button("👤 User Dashboard", use_container_width=True):
        st.session_state.page = "user_dashboard"
        st.rerun()
with col5:
    if st.button("🛡️ Admin Dashboard", use_container_width=True):
        st.session_state.page = "admin_dashboard"
        st.rerun()

st.divider()

# Page content based on session state
if st.session_state.page == "home":
    # Import and run home page content
    exec(open("home.py", encoding="utf-8").read())
elif st.session_state.page == "login":
    # Import and run login page content
    exec(open("pages/streamlit_login.py", encoding="utf-8").read())
elif st.session_state.page == "signup":
    # Import and run signup page content
    exec(open("pages/signup.py", encoding="utf-8").read())
elif st.session_state.page == "user_dashboard":
    # Import and run user dashboard content
    exec(open("pages/user_dashboard.py", encoding="utf-8").read())
elif st.session_state.page == "admin_dashboard":
    # Import and run admin dashboard content
    exec(open("pages/admin_dashboard.py", encoding="utf-8").read())
