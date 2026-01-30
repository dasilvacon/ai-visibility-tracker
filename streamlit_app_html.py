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

# DaSilva brand colors (updated to match new website)
DARK_BG = '#1c1c1c'
DARK_PURPLE = '#4A4458'
CREAM = '#E8D7A0'
DARK_ACCENT = '#402e3a'
OFF_WHITE = '#FBFBEF'

# ============================================
# SESSION STATE INITIALIZATION
# ============================================

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'brand_name' not in st.session_state:
    st.session_state.brand_name = None
if 'login_time' not in st.session_state:
    st.session_state.login_time = None

# ============================================
# CSS STYLES
# ============================================

login_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:wght@400;600&display=swap');

    /* Hide sidebar completely */
    section[data-testid="stSidebar"] {{
        display: none;
    }}

    /* Hide top hamburger menu button */
    button[kind="header"] {{
        display: none;
    }}

    /* Hide Streamlit branding and menu */
    #MainMenu {{
        display: none;
    }}

    footer {{
        display: none;
    }}

    header {{
        display: none;
    }}

    .main {{
        background-color: {DARK_BG};
    }}
    .login-container {{
        max-width: 420px;
        margin: 100px auto;
        padding: 0;
        background: transparent;
        border-radius: 8px;
    }}
    .login-title-card {{
        background: {DARK_PURPLE};
        padding: 40px;
        border-radius: 8px 8px 0 0;
        border: 1px solid rgba(232, 215, 160, 0.2);
        text-align: center;
    }}
    .login-form-card {{
        background: white;
        padding: 40px;
        border-radius: 0 0 8px 8px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }}
    .login-header {{
        color: white;
        text-align: center;
        font-family: 'Instrument Serif', Georgia, serif;
        font-size: 2.5em;
        font-weight: 400;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }}
    .login-subheader {{
        text-align: center;
        color: {CREAM};
        margin-bottom: 0;
        font-size: 0.9em;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 400;
    }}
    .stTextInput input {{
        background-color: #f9f9f9 !important;
        border: 1px solid #ddd !important;
        color: {DARK_BG} !important;
        border-radius: 4px !important;
        padding: 12px !important;
    }}
    .stTextInput input:focus {{
        border-color: {DARK_PURPLE} !important;
        box-shadow: 0 0 0 1px {DARK_PURPLE} !important;
    }}
    .stTextInput label {{
        color: {DARK_PURPLE} !important;
        font-size: 0.85em !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }}
    .stButton button {{
        background-color: {DARK_PURPLE};
        color: white;
        border-radius: 4px;
        width: 100%;
        padding: 14px;
        font-weight: 600;
        border: none;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.85em;
        transition: all 0.2s ease;
    }}
    .stButton button:hover {{
        background-color: {DARK_ACCENT};
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(74, 68, 88, 0.4);
    }}
    .stAlert {{
        background-color: #fee;
        border-left: 4px solid #c33;
        color: #c33;
    }}
    .footer-text {{
        text-align: center;
        color: #999;
        font-size: 0.85em;
        margin-top: 24px;
    }}
    .footer-text a {{
        color: {DARK_PURPLE};
        text-decoration: none;
    }}
</style>
"""

dashboard_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:wght@400;600&display=swap');

    /* Hide sidebar completely */
    section[data-testid="stSidebar"] {{
        display: none;
    }}

    /* Hide top hamburger menu button */
    button[kind="header"] {{
        display: none;
    }}

    /* Hide Streamlit branding and menu */
    #MainMenu {{
        display: none;
    }}

    footer {{
        display: none;
    }}

    header {{
        display: none;
    }}

    .main {{
        background-color: {DARK_BG};
    }}
    .welcome-header {{
        background: {DARK_PURPLE};
        color: white;
        padding: 32px 40px;
        border-radius: 8px;
        margin-bottom: 32px;
        border: 1px solid rgba(232, 215, 160, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }}
    .welcome-title {{
        font-family: 'Instrument Serif', Georgia, serif;
        font-size: 2.2em;
        font-weight: 400;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }}
    .welcome-subtitle {{
        opacity: 0.85;
        font-size: 1em;
        color: {CREAM};
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.85em;
    }}
    .report-meta {{
        display: flex;
        gap: 24px;
        margin-top: 16px;
        font-size: 0.85em;
        color: rgba(232, 215, 160, 0.7);
    }}
    .stButton button {{
        background-color: {CREAM};
        color: {DARK_BG};
        border-radius: 4px;
        padding: 10px 20px;
        font-weight: 700;
        border: none;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.75em;
        transition: all 0.2s ease;
    }}
    .stButton button:hover {{
        background-color: #f5e4b3;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(232, 215, 160, 0.3);
    }}
    .stSelectbox label {{
        color: {CREAM} !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.85em !important;
    }}
    .stSelectbox > div > div {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(232, 215, 160, 0.3) !important;
        color: white !important;
    }}
    .stDownloadButton button {{
        background-color: {CREAM};
        color: {DARK_BG};
        border-radius: 4px;
        padding: 12px 24px;
        font-weight: 700;
        border: none;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.85em;
        transition: all 0.2s ease;
    }}
    .stDownloadButton button:hover {{
        background-color: #f5e4b3;
        transform: translateY(-1px);
    }}
    .error-container {{
        max-width: 500px;
        margin: 60px auto;
        padding: 40px;
        background: {DARK_PURPLE};
        border-radius: 8px;
        border: 1px solid rgba(232, 215, 160, 0.3);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        text-align: center;
    }}
    .error-icon {{
        font-size: 3em;
        margin-bottom: 16px;
    }}
    .error-title {{
        color: white;
        font-family: 'Instrument Serif', Georgia, serif;
        font-size: 1.5em;
        font-weight: 400;
        margin-bottom: 12px;
    }}
    .error-message {{
        color: rgba(232, 215, 160, 0.8);
        margin-bottom: 20px;
        line-height: 1.6;
    }}
    .error-contact {{
        background: rgba(232, 215, 160, 0.1);
        padding: 16px;
        border-radius: 4px;
        font-size: 0.9em;
        color: {CREAM};
    }}
    .error-contact a {{
        color: {CREAM};
        text-decoration: underline;
    }}
    hr {{
        border-color: rgba(232, 215, 160, 0.2) !important;
    }}
    p {{
        color: rgba(232, 215, 160, 0.8);
    }}
    p a {{
        color: {CREAM};
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
        st.session_state.role = None
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

def get_user_role(username: str) -> str:
    """Get user role (admin or client)."""
    try:
        if hasattr(st, 'secrets') and 'roles' in st.secrets:
            return st.secrets['roles'].get(username, 'client')
    except Exception:
        pass
    return 'client'

def get_user_brand(username: str) -> str:
    """Get the brand name assigned to a user."""
    try:
        if hasattr(st, 'secrets') and 'clients' in st.secrets:
            brand = st.secrets['clients'].get(username)
            if brand == "ALL":
                # Admin - return first available brand or let them choose
                return "ALL"
            return brand
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
    st.session_state.role = None
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
            <div class='login-title-card'>
                <h1 class='login-header'>AI Visibility Report</h1>
                <p class='login-subheader'>Client Portal</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='login-form-card'>", unsafe_allow_html=True)
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
                    st.session_state.role = get_user_role(username)
                    brand = get_user_brand(username)

                    # If admin (ALL), set to None so they can select
                    st.session_state.brand_name = None if brand == "ALL" else brand
                    st.session_state.login_time = datetime.now()
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

        st.markdown(f"""
            <p class='footer-text'>
                <strong style='font-family: "Instrument Serif", Georgia, serif; font-size: 1.1em; color: {DARK_PURPLE};'>DaSilva</strong> <span style='text-transform: uppercase; letter-spacing: 0.15em; font-size: 0.85em;'>CONSULTING</span><br>
                <small style='opacity: 0.7;'>Need help? <a href='mailto:{SUPPORT_EMAIL}'>Contact support</a></small>
            </p>
        </div>
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

    # If admin and no brand selected, show brand selector
    if st.session_state.get('role') == 'admin' and st.session_state.brand_name is None:
        reports_dir = Path('data/reports')
        if reports_dir.exists():
            html_reports = list(reports_dir.glob('visibility_report_*.html'))
            available_brands = [f.stem.replace('visibility_report_', '').replace('_', ' ') for f in html_reports]

            if available_brands:
                st.markdown("""
                <div class='welcome-header'>
                    <div class='welcome-title'>Welcome, Administrator</div>
                    <div class='welcome-subtitle'>Select a brand to view their report</div>
                </div>
                """, unsafe_allow_html=True)

                selected_brand = st.selectbox("Select Brand", available_brands)
                if st.button("View Report", type="primary"):
                    st.session_state.brand_name = selected_brand
                    st.rerun()
                return
            else:
                display_error_state("No Reports Found", "No brand reports are available yet.")
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
        # Show change brand button for admin
        if st.session_state.get('role') == 'admin':
            if st.button("🔄 Change Brand", use_container_width=True):
                st.session_state.brand_name = None
                st.rerun()
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
        <p style='text-align: center; color: rgba(232, 215, 160, 0.6); font-size: 0.85em; margin-top: 16px;'>
            <span style='font-family: "Instrument Serif", Georgia, serif;'>DaSilva</span> <span style='text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.8em;'>CONSULTING</span><br>
            <small style='opacity: 0.8;'>Questions? <a href="mailto:{SUPPORT_EMAIL}" style='color: {CREAM};'>Contact us</a></small>
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
