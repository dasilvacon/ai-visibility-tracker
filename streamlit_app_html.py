"""
AI Visibility Tracker - HTML Report Viewer with Authentication
Displays the full HTML report for each client
"""

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

# Page config
st.set_page_config(
    page_title="AI Visibility Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'brand_name' not in st.session_state:
    st.session_state.brand_name = None

# DaSilva brand colors
DEEP_PLUM = '#402E3A'
DUSTY_ROSE = '#A78E8B'
OFF_WHITE = '#FBFBEF'
ACCENT_PINK = '#D4698B'

# Login page CSS
login_css = f"""
<style>
    .main {{
        background-color: {OFF_WHITE};
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
    h1 {{
        color: {DEEP_PLUM};
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    .stButton button {{
        background-color: {DEEP_PLUM};
        color: white;
        border-radius: 6px;
        width: 100%;
        padding: 12px;
        font-weight: 600;
    }}
    .stButton button:hover {{
        background-color: {ACCENT_PINK};
    }}
</style>
"""

def check_password(username: str, password: str) -> bool:
    """Check if username/password combination is valid."""
    try:
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
    st.markdown(login_css, unsafe_allow_html=True)
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)

    st.markdown(f"<h1>🎯 AI Visibility Report</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Client Portal</p>", unsafe_allow_html=True)
    st.markdown("---")

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            # Strip whitespace
            username = username.strip()
            password = password.strip()

            if check_password(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.brand_name = get_user_brand(username)
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #999;'>DaSilva Consulting • AI Visibility Analysis</p>", unsafe_allow_html=True)

def display_html_report():
    """Display the full HTML report."""
    brand_slug = st.session_state.brand_name.replace(' ', '_')
    html_report_path = Path(f'data/reports/visibility_report_{brand_slug}.html')

    if not html_report_path.exists():
        st.error(f"Report not found for {st.session_state.brand_name}")
        st.info("Please generate the report first using the analysis tool.")
        return

    # Add logout button in a floating container
    st.markdown(f"""
    <style>
        .logout-container {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
        }}
    </style>
    <div class="logout-container">
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.brand_name = None
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Read and display the HTML report
    with open(html_report_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Display the full HTML report
    components.html(html_content, height=3000, scrolling=True)

    # Add download button at the bottom
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with open(html_report_path, 'r', encoding='utf-8') as f:
            st.download_button(
                label="📥 Download Full Report",
                data=f.read(),
                file_name=f"AI_Visibility_Report_{brand_slug}.html",
                mime="text/html",
                use_container_width=True
            )

# Main app logic
if not st.session_state.authenticated:
    login_page()
else:
    display_html_report()
