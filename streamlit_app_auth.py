"""
AI Visibility Tracker - Authenticated Streamlit Dashboard
Client login with brand-specific access
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import json
import sys
from datetime import datetime
import hashlib

# Add src to path
sys.path.insert(0, 'src')

# Page config
st.set_page_config(
    page_title="AI Visibility Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DaSilva brand colors
DEEP_PLUM = '#402E3A'
DUSTY_ROSE = '#A78E8B'
CHARCOAL = '#1C1C1C'
OFF_WHITE = '#FBFBEF'
ACCENT_PINK = '#D4698B'

# Custom CSS for branding
st.markdown(f"""
<style>
    .main {{
        background-color: {OFF_WHITE};
    }}
    h1, h2, h3 {{
        color: {DEEP_PLUM};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    .stMetric {{
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        border: 2px solid {DUSTY_ROSE};
    }}
    .stMetric label {{
        color: {DEEP_PLUM} !important;
        font-weight: 600;
    }}
    .stDownloadButton button {{
        background-color: {DEEP_PLUM};
        color: white;
        border-radius: 6px;
    }}
    .stDownloadButton button:hover {{
        background-color: {ACCENT_PINK};
    }}
    div[data-testid="stSidebarNav"] {{
        background-color: {DEEP_PLUM};
    }}
    .login-container {{
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        background: white;
        border-radius: 10px;
        border: 2px solid {DUSTY_ROSE};
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'brand_name' not in st.session_state:
    st.session_state.brand_name = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None

def check_password(username: str, password: str) -> bool:
    """Check if username/password combination is valid."""
    try:
        # Try to get credentials from Streamlit secrets
        if hasattr(st, 'secrets') and 'passwords' in st.secrets:
            stored_password = st.secrets['passwords'].get(username)
            if stored_password and stored_password == password:
                return True
    except Exception:
        pass
    return False

def get_user_brand(username: str) -> str:
    """Get the brand name assigned to a user."""
    try:
        if hasattr(st, 'secrets') and 'brands' in st.secrets:
            return st.secrets['brands'].get(username, username.replace('_', ' ').title())
    except Exception:
        pass
    return username.replace('_', ' ').title()

def login_page():
    """Display login page."""
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)

    st.markdown(f"<h1 style='text-align: center; color: {DEEP_PLUM};'>🎯 AI Visibility Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Client Portal Login</p>", unsafe_allow_html=True)
    st.markdown("---")

    # DEBUG - Remove after testing
    with st.expander("🔍 Debug Info (Remove after testing)"):
        if hasattr(st, 'secrets'):
            st.write("✅ Secrets found:", list(st.secrets.keys()))
            if 'passwords' in st.secrets:
                st.write("✅ Usernames available:", list(st.secrets['passwords'].keys()))
            else:
                st.write("❌ No 'passwords' section in secrets")
            if 'brands' in st.secrets:
                st.write("✅ Brands available:", list(st.secrets['brands'].keys()))
            else:
                st.write("❌ No 'brands' section in secrets")
        else:
            st.write("❌ No secrets loaded at all")

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            # DEBUG - Check what we're comparing
            if hasattr(st, 'secrets') and 'passwords' in st.secrets:
                stored_password = st.secrets['passwords'].get(username)
                st.write(f"DEBUG - Username entered: '{username}'")
                st.write(f"DEBUG - Password entered length: {len(password)}")
                st.write(f"DEBUG - Stored password length: {len(stored_password) if stored_password else 0}")
                st.write(f"DEBUG - Passwords match: {stored_password == password}")

            if check_password(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.brand_name = get_user_brand(username)
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #999;'>DaSilva Consulting • AI Visibility Analysis</p>", unsafe_allow_html=True)

def logout():
    """Log out the current user."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.brand_name = None
    st.session_state.analysis_data = None
    st.rerun()

# Load data function
@st.cache_data
def load_analysis_data(brand_name: str):
    """Load all analysis data for a brand."""
    brand_slug = brand_name.replace(' ', '_')
    data = {}

    # Load CSVs
    try:
        data['sources'] = pd.read_csv(f'data/reports/sources_{brand_slug}.csv')
    except FileNotFoundError:
        data['sources'] = None

    try:
        data['action_plan'] = pd.read_csv(f'data/reports/action_plan_{brand_slug}.csv')
    except FileNotFoundError:
        data['action_plan'] = None

    try:
        data['competitors'] = pd.read_csv(f'data/reports/competitors_{brand_slug}.csv')
    except FileNotFoundError:
        data['competitors'] = None

    try:
        data['raw_data'] = pd.read_csv(f'data/reports/raw_data_{brand_slug}.csv')
    except FileNotFoundError:
        data['raw_data'] = None

    # Load text report for summary stats
    try:
        with open(f'data/reports/visibility_analysis_{brand_slug}.txt', 'r') as f:
            data['text_report'] = f.read()
    except FileNotFoundError:
        data['text_report'] = None

    return data

# Main app logic
if not st.session_state.authenticated:
    login_page()
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"<h1 style='color: white;'>🎯 AI Visibility</h1>", unsafe_allow_html=True)
        st.markdown("---")

        # User info
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        st.markdown(f"**Brand:** {st.session_state.brand_name}")

        if st.button("🚪 Logout", use_container_width=True):
            logout()

        st.markdown("---")

        # Navigation
        st.markdown("### Navigation")
        page = st.radio(
            "Go to:",
            ["📊 Overview", "🎯 Sources & Citations", "✅ Action Plan", "🏆 Competitor Analysis"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Info
        st.markdown("### About")
        st.caption(f"Generated: {datetime.now().strftime('%B %d, %Y')}")
        st.caption("AI Visibility Analysis")

    # Load data
    if st.session_state.brand_name:
        data = load_analysis_data(st.session_state.brand_name)
    else:
        st.error("Brand not found")
        st.stop()

    # Main content based on selected page
    if page == "📊 Overview":
        from pages import overview
        overview.show(st.session_state.brand_name, data)
    elif page == "🎯 Sources & Citations":
        from pages import sources
        sources.show(st.session_state.brand_name, data)
    elif page == "✅ Action Plan":
        from pages import action_plan
        action_plan.show(st.session_state.brand_name, data)
    elif page == "🏆 Competitor Analysis":
        from pages import competitors
        competitors.show(st.session_state.brand_name, data)
