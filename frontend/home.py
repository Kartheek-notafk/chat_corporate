import streamlit as st
from styles import SHARED_CSS

st.set_page_config(
    page_title="Chat Application - Home",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(SHARED_CSS, unsafe_allow_html=True)

# Custom CSS for home page
home_css = """
<style>
    .hero-container {
        position: relative;
        padding: 2rem;
        margin-bottom: 3rem;
    }
    .top-right-box {
        position: absolute;
        top: 0;
        right: 0;
        background: linear-gradient(135deg, #A87B33 0%, #8C662A 100%);
        padding: 1rem 1.5rem;
        border-radius: 0 0 0 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .hero-content {
        text-align: center;
        padding: 3rem 2rem;
    }
    .hero-title { 
        font-size: 3.5rem; 
        font-weight: bold; 
        margin-bottom: 1rem;
        color: #41525d;
    }
    .hero-subtitle { 
        font-size: 1.5rem; 
        margin-bottom: 2rem;
        color: #8696a0;
    }
    .hero-description {
        font-size: 1.1rem;
        color: #8696a0;
        max-width: 600px;
        margin: 0 auto;
    }
    .button-container {
        display: flex;
        gap: 0.5rem;
    }
    .feature-card { 
        background: white; 
        padding: 2rem; 
        border-radius: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
        min-height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin: 0.5rem;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    .feature-icon { 
        font-size: 3rem; 
        margin-bottom: 1rem;
    }
    .feature-title { 
        color: #A87B33; 
        font-size: 1.5rem; 
        font-weight: bold; 
        margin-bottom: 1rem;
    }
    .feature-description { 
        color: #8696a0; 
        line-height: 1.6;
        font-size: 0.95rem;
        flex-grow: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .primary-btn {
        background-color: white;
        color: #A87B33;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        transition: all 0.3s ease;
        font-size: 0.9rem;
    }
    .primary-btn:hover {
        background-color: #f8f9fa;
        color: #8C662A;
    }
    .secondary-btn {
        background-color: transparent;
        color: white;
        border: 2px solid white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        transition: all 0.3s ease;
        font-size: 0.9rem;
    }
    .secondary-btn:hover {
        background-color: white;
        color: #A87B33;
    }
    /* Style Streamlit buttons */
    .stButton > button {
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        transform: scale(1);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stButton:nth-child(1) > button {
        background-color: white;
        color: #A87B33;
        border: 1px solid #A87B33;
    }
    .stButton:nth-child(1) > button:hover {
        background-color: #f8f9fa;
        color: #8C662A;
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(168, 123, 51, 0.3);
    }
    .stButton:nth-child(2) > button {
        background-color: #A87B33;
        color: white;
        border: 1px solid #A87B33;
    }
    .stButton:nth-child(2) > button:hover {
        background-color: #8C662A;
        color: white;
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(168, 123, 51, 0.4);
    }
</style>
"""

st.markdown(home_css, unsafe_allow_html=True)

# Hero Section
col1, col2 = st.columns([3, 1])
with col2:
    # Login button only - no signup
    login_btn = st.columns([1, 2, 1])[1]
    with login_btn:
        if st.button("🚀 Get Started", use_container_width=True, type="primary"):
            st.switch_page("pages/streamlit_login.py")

st.markdown("""
<div class="hero-content">
    <div class="hero-title">💬 Corporate Smart Messenger</div>
    <div class="hero-subtitle">Connect, Communicate, and Collaborate Seamlessly</div>
    <div class="hero-description">
        Experience the next generation of corporate communication with our secure,
        intelligent messaging platform designed for modern teams.
    </div>
</div>
""", unsafe_allow_html=True)

# Features Section
st.markdown("## 🚀 Features", unsafe_allow_html=True)
st.markdown("Discover what makes our chat application special", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🔐</div>
        <div class="feature-title">🔐 Enterprise Security</div>
        <div class="feature-description">
            Military-grade encryption and multi-factor authentication keep your 
            corporate communications completely secure and compliant.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">👥</div>
        <div class="feature-title">👥 Smart User Management</div>
        <div class="feature-description">
            Powerful admin dashboard with role-based access control, department 
            management, and comprehensive user analytics.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📱</div>
        <div class="feature-title">⚡ Instant Messaging</div>
        <div class="feature-description">
            Lightning-fast message delivery with read receipts, file sharing, 
            and rich media support for seamless collaboration.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Additional Features
col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🎨</div>
        <div class="feature-title">🎨 Beautiful Interface</div>
        <div class="feature-description">
            Stunning, intuitive design that adapts perfectly to any device. 
            Experience corporate communication like never before.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">📊 Advanced Analytics</div>
        <div class="feature-description">
            Real-time insights into user activity, engagement metrics, and 
            communication patterns to drive informed business decisions.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🔔</div>
        <div class="feature-title">🔔 Intelligent Notifications</div>
        <div class="feature-description">
            Smart, customizable alerts that learn your preferences. 
            Stay connected without being overwhelmed by unnecessary noise.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #8696a0; margin-top: 2rem;">
    <p>© 2024 Chat Application. Built with ❤️ using Streamlit</p>
    <p style="margin-top: 0.5rem; font-size: 0.9rem;">
        Need help? Contact our support team
    </p>
</div>
""", unsafe_allow_html=True)
