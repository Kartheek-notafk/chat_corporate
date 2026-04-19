SHARED_CSS = """
<style>
    .stApp { background-color: #f0f2f5; }
    .stApp header { background-color: #A87B33; }
    [data-testid="collapsedControl"] { display: none; }
    [data-testid="stSidebar"] { display: none; }
    
    /* Enhanced Input Styling */
    .stTextInput input { 
        border-radius: 12px; 
        border: 2px solid #e1e5e9; 
        background-color: white !important; 
        color: #2c3e50 !important;
        font-size: 16px !important;
        padding: 12px 16px !important;
        transition: all 0.3s ease;
    }
    .stTextInput input:focus {
        border-color: #A87B33 !important;
        box-shadow: 0 0 0 3px rgba(168, 123, 51, 0.1) !important;
    }
    .stTextInput p { 
        color: #4a5568 !important; 
        font-weight: 500 !important;
        margin-bottom: 8px !important;
    }
    .stCheckbox p { color: #4a5568 !important; font-weight: 500 !important; }
    .stSelectbox label { color: #4a5568 !important; font-weight: 500 !important; }
    
    /* Enhanced Button Styling */
    .stForm [data-testid="stFormSubmitButton"] > button { 
        width: 100%; 
        border-radius: 12px; 
        background-color: #A87B33; 
        color: white; 
        font-weight: 600; 
        border: none; 
        padding: 14px 20px; 
        margin-top: 1rem;
        font-size: 16px !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(168, 123, 51, 0.3);
    }
    .stForm [data-testid="stFormSubmitButton"] > button:hover { 
        background-color: #8C662A; 
        color: white; 
        border: none;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(168, 123, 51, 0.4);
    }
    
    /* General Button Improvements */
    button[kind="primary"] {
        background-color: #A87B33 !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 14px 24px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(168, 123, 51, 0.3) !important;
    }
    button[kind="primary"]:hover {
        background-color: #8C662A !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(168, 123, 51, 0.4) !important;
    }
    
    button[kind="secondary"] { 
        color: #A87B33 !important; 
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: 2px solid #A87B33 !important;
        background-color: white !important;
        padding: 12px 24px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    button[kind="secondary"]:hover {
        background-color: #A87B33 !important;
        color: white !important;
        transform: translateY(-2px) !important;
    }
    
    /* All Streamlit buttons */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        padding: 14px 24px !important;
        transition: all 0.3s ease !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* Typography Improvements */
    h1 { 
        text-align: center; 
        color: #2c3e50 !important;
        font-weight: 700 !important;
        margin-bottom: 1.5rem !important;
    }
    h2 { 
        color: #2c3e50 !important;
        font-weight: 600 !important;
    }
    h3 { 
        color: #2c3e50 !important;
        font-weight: 600 !important;
    }
    p  { 
        color: #4a5568 !important; 
        line-height: 1.6 !important;
        font-size: 16px !important;
    }
    
    /* Form Styling */
    [data-testid="stForm"] { 
        background-color: white; 
        padding: 2.5rem; 
        border-radius: 16px; 
        border: none; 
        box-shadow: 0 8px 25px rgba(0,0,0,0.08); 
    }
    
    /* Dashboard Cards */
    .dash-card { 
        background: white; 
        border-radius: 16px; 
        padding: 2rem; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.08); 
        margin-bottom: 1.5rem; 
        color: #2c3e50;
        transition: all 0.3s ease;
        border: 1px solid #e1e5e9;
    }
    .dash-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    .dash-card h3 { 
        color: #A87B33; 
        margin-top: 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    /* Role Badges */
    .role-badge-admin { 
        display: inline-block; 
        background: #A87B33; 
        color: white; 
        border-radius: 20px; 
        padding: 6px 16px; 
        font-size: 0.85rem; 
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(168, 123, 51, 0.3);
    }
    .role-badge-user  { 
        display: inline-block; 
        background: #4a5568; 
        color: white; 
        border-radius: 20px; 
        padding: 6px 16px; 
        font-size: 0.85rem; 
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(74, 85, 104, 0.3);
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background-color: #d4edda !important;
        border-left: 4px solid #28a745 !important;
        color: #155724 !important;
        font-weight: 500 !important;
    }
    .stError {
        background-color: #f8d7da !important;
        border-left: 4px solid #dc3545 !important;
        color: #721c24 !important;
        font-weight: 500 !important;
    }
    .stWarning {
        background-color: #fff3cd !important;
        border-left: 4px solid #ffc107 !important;
        color: #856404 !important;
        font-weight: 500 !important;
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background-color: #f8f9fa !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #2c3e50 !important;
    }
</style>
"""
