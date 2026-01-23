"""
AI Visibility Tracker - HTML Report Viewer with Authentication
Displays the full HTML report for each client

Improvements:
- Removed debug section for production security
- Added session timeout (30 minutes)
- Welcome message with report context
- Loading state while report renders
- Last Updated timestamp
- Branded error states with contact info
- Improved logout button placement
"""

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import datetime, timedelta
import os

# Page config
st.set_page_config(
    page_title="AI Visibility Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# CONFIGURATION
# ============================================

# Session timeout in minutes
SESSION_TIMEOUT_MINUTES = 30

# Contact info for error states
SUPPORT_EMAIL = "tiffany@dasilvaconsulting.com"

# DaSilva brand colors
DEEP_PLUM = '#402E3A'
DUSTY_ROSE = '#A78E8B'
OFF_WHITE = '#FBFBEF'
ACCENT_PINK = '#D4698B'

# ============================================
# SESSION STATE INITIALIZATION
# ============================================

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'brand_name' not in st.session_state:
    st.session_state.brand_name = None
if 'login_time' not in st.session_state:
    st.session_state.login_time = None

# ============================================
# CSS STYLES
# ============================================

login_css = f"""
<style>
    .main {{
        background-color: {OFF_WHITE};
    }}
    .login-container {{
        max-width: 400px;
        margin: 80px auto;
        padding: 40px;
        background: white;
        border-radius: 12px;
        border: 2px solid {DUSTY_ROSE};
        box-shadow: 0 4px 20px rgba(64, 46, 58, 0.1);
    }}
    .login-header {{
        color: {DEEP_PLUM};
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        margin-bottom: 8px;
    }}
    .login-subheader {{
        text-align: center;
        color: #666;
        margin-bottom: 24px;
    }}
    .stButton button {{
        background-color: {DEEP_PLUM};
        color: white;
        border-radius: 6px;
        width: 100%;
        padding: 12px;
        font-weight: 600;
        border: none;
        transition: background-color 0.2s ease;
    }}
    .stButton button:hover {{
        background-color: {ACCENT_PINK};
    }}
    .footer-text {{
        text-align: center;
        color: #999;
        font-size: 0.85em;
        margin-top: 40px;
    }}
</style>
"""

dashboard_css = f"""
<style>
    .main {{
        background-color: {OFF_WHITE};
    }}
    .welcome-header {{
        background: linear-gradient(135deg, {DEEP_PLUM} 0%, {ACCENT_PINK} 100%);
        color: white;
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(64, 46, 58, 0.15);
    }}
    .welcome-title {{
        font-size: 1.5em;
        font-weight: 600;
        margin-bottom: 4px;
    }}
    .welcome-subtitle {{
        opacity: 0.9;
        font-size: 0.95em;
    }}
    .report-meta {{
        display: flex;
        gap: 24px;
        margin-top: 12px;
        font-size: 0.85em;
        opacity: 0.85;
    }}
    .error-container {{
        max-width: 500px;
        margin: 60px auto;
        padding: 40px;
        background: white;
        border-radius: 12px;
        border-left: 4px solid {ACCENT_PINK};
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        text-align: center;
    }}
    .error-icon {{
        font-size: 3em;
        margin-bottom: 16px;
    }}
    .error-title {{
        color: {DEEP_PLUM};
        font-size: 1.3em;
        font-weight: 600;
        margin-bottom: 12px;
    }}
    .error-message {{
        color: #666;
        margin-bottom: 20px;
    }}
    .error-contact {{
        background: {OFF_WHITE};
        padding: 16px;
        border-radius: 8px;
        font-size: 0.9em;
    }}
</style>
"""

# ============================================
# HELPER FUNCTIONS
# ============================================

def check_session_timeout() -> bool:
    """Check if the session has timed out."""
    if st.session_state.login_time is None:
        return True

    elapsed = datetime.now() - st.session_state.login_time
    if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        # Clear session
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.brand_name = None
        st.session_state.login_time = None
        return True
    return False

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

def get_report_metadata(report_path: Path) -> dict:
    """Get metadata about the report file."""
    if not report_path.exists():
        return None

    stat = report_path.stat()
    modified_time = datetime.fromtimestamp(stat.st_mtime)

    return {
        'last_updated': modified_time.strftime('%B %d, %Y at %I:%M %p'),
        'file_size': f"{stat.st_size / 1024:.1f} KB"
    }

def logout():
    """Clear session and log out user."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.brand_name = None
    st.session_state.login_time = None

# ============================================
# PAGE COMPONENTS
# ============================================

def login_page():
    """Display login page."""
    st.markdown(login_css, unsafe_allow_html=True)

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div class='login-container'>
            <h1 class='login-header'>🎯 AI Visibility Report</h1>
            <p class='login-subheader'>Client Portal</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                username = username.strip()
                password = password.strip()

                if check_password(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.brand_name = get_user_brand(username)
                    st.session_state.login_time = datetime.now()
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

        st.markdown("""
        <p class='footer-text'>
            DaSilva Consulting • AI Visibility Analysis<br>
            <small>Need help? Contact support</small>
        </p>
        """, unsafe_allow_html=True)

def display_error_state(title: str, message: str):
    """Display a branded error state."""
    st.markdown(dashboard_css, unsafe_allow_html=True)
    st.markdown(f"""
    <div class='error-container'>
        <div class='error-icon'>📋</div>
        <div class='error-title'>{title}</div>
        <div class='error-message'>{message}</div>
        <div class='error-contact'>
            <strong>Need assistance?</strong><br>
            Contact us at <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_html_report():
    """Display the full HTML report with improved UX."""
    st.markdown(dashboard_css, unsafe_allow_html=True)

    # Check for session timeout
    if check_session_timeout():
        st.warning("⏰ Your session has expired. Please log in again.")
        st.rerun()
        return

    brand_slug = st.session_state.brand_name.replace(' ', '_')
    html_report_path = Path(f'data/reports/visibility_report_{brand_slug}.html')

    # Get report metadata
    metadata = get_report_metadata(html_report_path)

    # Header row with welcome message and logout
    header_col1, header_col2 = st.columns([4, 1])

    with header_col1:
        if metadata:
            st.markdown(f"""
            <div class='welcome-header'>
                <div class='welcome-title'>Welcome, {st.session_state.brand_name}</div>
                <div class='welcome-subtitle'>Here's your latest AI Visibility Report</div>
                <div class='report-meta'>
                    <span>📅 Last Updated: {metadata['last_updated']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='welcome-header'>
                <div class='welcome-title'>Welcome, {st.session_state.brand_name}</div>
                <div class='welcome-subtitle'>AI Visibility Dashboard</div>
            </div>
            """, unsafe_allow_html=True)

    with header_col2:
        st.write("")  # Spacing
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

    # Check if report exists
    if not html_report_path.exists():
        display_error_state(
            "Report Not Found",
            f"We couldn't find a report for {st.session_state.brand_name}. "
            "Your report may still be in progress or there might be a configuration issue."
        )
        return

    # Show loading state
    with st.spinner("Loading your report..."):
        # Read the HTML report
        with open(html_report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Calculate approximate height based on content length
        # This is a rough heuristic - adjust multiplier as needed
        content_length = len(html_content)
        estimated_height = min(max(1500, content_length // 50), 5000)

        # Display the HTML report
        components.html(html_content, height=estimated_height, scrolling=True)

    # Footer with download option
    st.markdown("---")

    footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])

    with footer_col2:
        with open(html_report_path, 'r', encoding='utf-8') as f:
            st.download_button(
                label="📥 Download Full Report",
                data=f.read(),
                file_name=f"AI_Visibility_Report_{brand_slug}.html",
                mime="text/html",
                use_container_width=True
            )

        st.markdown(f"""
        <p style='text-align: center; color: #999; font-size: 0.85em; margin-top: 16px;'>
            Report generated by DaSilva Consulting<br>
            Questions? <a href="mailto:{SUPPORT_EMAIL}">Contact us</a>
        </p>
        """, unsafe_allow_html=True)

# ============================================
# MAIN APP LOGIC
# ============================================

def main():
    """Main application entry point."""
    # Check if already authenticated but session expired
    if st.session_state.authenticated and check_session_timeout():
        st.session_state.authenticated = False

    # Route to appropriate page
    if not st.session_state.authenticated:
        login_page()
    else:
        display_html_report()

if __name__ == "__main__":
    main()
