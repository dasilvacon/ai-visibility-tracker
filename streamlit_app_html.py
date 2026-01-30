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

# Logo SVG (inline for Streamlit Cloud compatibility)
LOGO_SVG = """
<svg id="Layer_1" xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 249.69 100" style="width: 180px; height: auto;">
  <defs>
    <style>
      .st0 {
        fill: currentColor;
      }
    </style>
  </defs>
  <g>
    <path class="st0" d="M135.29,99.35c-1.06,0-1.98-.23-2.76-.69-.77-.46-1.37-1.1-1.78-1.93-.42-.82-.62-1.78-.62-2.86s.21-2.04.62-2.87c.41-.83,1.01-1.48,1.78-1.94.77-.47,1.69-.7,2.76-.7,1.29,0,2.34.32,3.15.96.81.64,1.32,1.53,1.53,2.67h-2.19c-.12-.58-.39-1.03-.82-1.35-.43-.32-.99-.49-1.7-.49-.65,0-1.2.15-1.67.45-.47.3-.82.73-1.08,1.28-.25.56-.38,1.22-.38,1.99s.13,1.43.38,1.98c.25.55.61.98,1.08,1.28.47.3,1.02.45,1.67.45.71,0,1.27-.15,1.69-.46.42-.3.7-.74.83-1.32h2.17c-.19,1.12-.7,2-1.51,2.62-.81.62-1.86.93-3.15.93Z"/>
    <path class="st0" d="M149.05,99.35c-1.05,0-1.98-.23-2.78-.7-.8-.47-1.42-1.11-1.87-1.93-.45-.82-.68-1.78-.68-2.87s.23-2.04.68-2.86c.45-.82,1.08-1.47,1.87-1.94.8-.47,1.73-.7,2.78-.7s1.99.23,2.79.7c.79.47,1.42,1.11,1.87,1.94.45.82.68,1.78.68,2.86s-.23,2.05-.68,2.87c-.45.82-1.07,1.46-1.87,1.93-.79.47-1.72.7-2.79.7ZM149.06,97.58c.67,0,1.25-.15,1.75-.45.5-.3.88-.73,1.15-1.28.27-.56.41-1.22.41-1.99s-.14-1.43-.41-1.99c-.27-.56-.66-.98-1.15-1.28-.5-.3-1.08-.45-1.75-.45s-1.25.15-1.75.45c-.5.3-.89.73-1.16,1.28-.27.56-.41,1.22-.41,1.99s.14,1.43.41,1.99c.27.56.66.98,1.16,1.28.5.3,1.09.45,1.75.45Z"/>
    <path class="st0" d="M158.69,99.17v-10.63h1.97l4.96,7.44v-7.44h1.97v10.63h-1.97l-4.96-7.42v7.42h-1.97Z"/>
    <path class="st0" d="M176.13,99.35c-.5,0-.99-.07-1.47-.2-.49-.14-.93-.35-1.34-.65-.4-.3-.74-.68-1.01-1.15-.27-.47-.43-1.03-.48-1.69h1.82c.08.52.25.92.51,1.21.26.29.57.5.93.61.36.12.72.17,1.07.17.39,0,.75-.06,1.05-.18s.55-.3.73-.52c.18-.23.27-.49.27-.8s-.09-.59-.26-.84c-.17-.25-.54-.42-1.11-.52l-1.81-.33c-.87-.16-1.55-.51-2.04-1.04-.49-.53-.74-1.16-.74-1.89,0-.67.17-1.23.5-1.7.33-.47.78-.82,1.35-1.08.57-.25,1.19-.38,1.87-.38s1.35.12,1.91.36c.57.24,1.03.61,1.38,1.12.35.5.57,1.15.64,1.94h-1.85c-.06-.46-.19-.81-.4-1.06-.21-.25-.46-.42-.74-.52-.29-.1-.58-.15-.89-.15-.28,0-.58.05-.88.14-.3.09-.56.24-.76.45-.2.21-.3.49-.3.84,0,.3.11.57.34.81.23.24.59.4,1.1.49l1.67.3c.89.16,1.59.48,2.1.95s.77,1.16.77,2.06c0,.54-.11,1-.34,1.4-.23.4-.53.74-.9,1.02-.37.28-.79.49-1.26.63-.47.14-.94.21-1.43.21Z"/>
    <path class="st0" d="M188.49,99.35c-.78,0-1.48-.15-2.11-.46-.63-.31-1.13-.78-1.5-1.41-.37-.63-.56-1.43-.56-2.39v-6.54h1.97v6.56c0,.82.2,1.43.6,1.84.4.4.95.61,1.65.61s1.25-.2,1.65-.61c.4-.4.6-1.02.6-1.84v-6.56h1.97v6.54c0,.96-.19,1.76-.58,2.39-.38.63-.9,1.1-1.55,1.41-.65.31-1.36.46-2.14.46Z"/>
    <path class="st0" d="M197.39,99.17v-10.63h1.97v9.08h4.71v1.55h-6.68Z"/>
    <path class="st0" d="M209.41,99.17v-9.03h-3.11v-1.59h8.18v1.59h-3.1v9.03h-1.97Z"/>
    <path class="st0" d="M218.47,99.17v-10.63h1.97v10.63h-1.97Z"/>
    <path class="st0" d="M225.21,99.17v-10.63h1.97l4.96,7.44v-7.44h1.97v10.63h-1.97l-4.96-7.42v7.42h-1.97Z"/>
    <path class="st0" d="M243.9,99.35c-1.15,0-2.14-.23-2.95-.68-.81-.45-1.44-1.08-1.87-1.9-.43-.81-.65-1.76-.65-2.85s.21-2.06.65-2.9c.43-.84,1.04-1.5,1.84-1.97.79-.47,1.74-.71,2.83-.71,1.25,0,2.29.3,3.11.9.82.6,1.35,1.42,1.59,2.47h-2.22c-.16-.49-.45-.87-.87-1.14-.42-.27-.96-.41-1.62-.41s-1.29.15-1.78.46c-.49.3-.87.74-1.13,1.3s-.39,1.23-.39,2.01.14,1.42.41,1.97c.27.54.67.96,1.18,1.25.51.29,1.14.44,1.87.44.88,0,1.58-.25,2.09-.74.51-.5.77-1.18.78-2.06h-2.96v-1.49h4.95v.85c0,1.14-.21,2.1-.63,2.87-.42.77-.99,1.35-1.72,1.74-.73.39-1.56.58-2.5.58Z"/>
  </g>
  <g>
    <path class="st0" d="M124.07,46.29c-2.43-3.98-6.29-8.13-11.58-12.43-4.94-3.95-8.39-7.3-10.37-10.05-1.98-2.75-2.96-5.64-2.96-8.68,0-3.6.9-6.38,2.7-8.36,1.8-1.97,4.21-2.96,7.25-2.96s5.17,1.25,6.82,3.76c1.66,2.5,3.26,6.47,4.81,11.9l.74,2.64c.28.99.74,1.48,1.38,1.48.92,0,1.38-.6,1.38-1.8V5.83c0-.56-.12-1.02-.37-1.38-.25-.35-.58-.67-1.01-.95-1.27-.92-2.89-1.62-4.87-2.12-1.98-.49-4.02-.74-6.14-.74-5.64,0-10.28,1.57-13.91,4.71-3.63,3.14-5.45,7.32-5.45,12.54,0,3.95,1.2,7.67,3.6,11.16,2.4,3.49,6.21,7.11,11.43,10.84,4.72,3.53,8.16,7.09,10.31,10.68,2.15,3.6,3.23,7.48,3.23,11.64s-1.04,7.64-3.12,10c-2.08,2.36-4.22,3.54-6.96,3.54-6.12,0-10.43-4.13-12.83-14.22l-.95-3.57c-.35-1.49-.99-2.11-1.97-1.88-.79.18-.99,1.12-.99,2.85,0,9.02-.79,13.32-5.75,13.32-1.48,0-2.95-1.48-2.95-4.44v-32.37c0-8.11-3.88-12.17-10.86-12.17-7.82,0-15.26,7.21-16.56,15.47-.47,3,1.15,4.52,2.84,4.52,1.95,0,4.85-1.42,5.54-5.73.74-4.62,1.21-11.09,6.42-11.09s5.42,5.26,5.42,9.42v9.63c0,.92-.46,1.52-1.38,1.8-4.23,1.34-8.01,3.1-11.32,5.29-3.32,2.19-5.92,4.64-7.83,7.35-1.9,2.72-2.86,5.59-2.86,8.62s.95,5.59,2.86,7.46c1.9,1.87,4.34,2.8,7.3,2.8,2.61,0,4.8-.6,6.56-1.8,1.76-1.2,3.49-2.96,5.18-5.29.49-.7,1.01-1.04,1.53-1.01.53.04.83.41.9,1.11.35,1.9,1.02,3.54,2.01,4.92.08.11.16.21.25.3,3.94,3.96,9.93.31,11.76-1.91.49-.6,1.4-.66,1.96-.12.88.83,2.26,1.81,3.91,2.31,1.51.45,3.14.78,4.87,1.06,1.73.28,3.3.41,4.71.42,2.98.04,6.01-.83,9.08-2.49,3.07-1.66,5.48-3.97,7.25-6.93,1.76-2.96,2.64-6.42,2.64-10.37,0-4.51-1.22-8.76-3.65-12.75ZM78.33,59.36c0,2.75-.49,5.22-1.48,7.41-.99,2.19-2.26,3.93-3.81,5.24-1.55,1.31-3.24,1.96-5.08,1.96-3.6,0-5.4-2.43-5.4-7.3,0-3.81,1.18-7.07,3.54-9.79,2.36-2.71,5.69-4.85,10-6.4,1.48-.56,2.22-.18,2.22,1.16v7.72Z"/>
    <path class="st0" d="M190.99,78.83c-.63,0-1.09-.39-1.38-1.16l-14.07-46.65c-.49-1.69-.97-2.79-1.43-3.28-.46-.49-1.18-.85-2.17-1.06l-1.59-.32c-.92-.21-1.38-.67-1.38-1.38s.49-1.06,1.48-1.06h17.46c.99,0,1.48.35,1.48,1.06,0,.78-.46,1.23-1.38,1.38l-1.69.21c-1.69.21-2.75.62-3.17,1.22-.42.6-.42,1.68,0,3.23l8.78,30.57c.21.78.56,1.16,1.06,1.16s.85-.39,1.06-1.16l8.57-28.67c.56-1.9.72-3.33.48-4.28-.25-.95-1.25-1.57-3.01-1.85l-2.22-.42c-.92-.21-1.38-.67-1.38-1.38s.49-1.06,1.48-1.06h13.44c.99,0,1.48.39,1.48,1.16,0,.71-.42,1.2-1.27,1.48l-.95.32c-1.06.35-1.96.99-2.7,1.9-.74.92-1.46,2.5-2.17,4.76l-13.44,44.12c-.28.78-.74,1.16-1.38,1.16Z"/>
    <path class="st0" d="M247.86,62.43c-.92,0-1.38.57-1.38,1.69,0,2.96-.39,5.06-1.16,6.29-.78,1.23-1.95,1.85-2.87,1.85-1.48,0-2.68-1.48-2.68-4.44v-32.37h0c0-8.11-3.88-12.17-10.86-12.17-7.82,0-15.26,7.21-16.56,15.47-.47,3,1.15,4.52,2.84,4.52,1.95,0,4.85-1.42,5.54-5.73.74-4.62,1.21-11.09,6.42-11.09s5.42,5.26,5.42,9.42h0v9.63c0,.92-.46,1.52-1.38,1.8-4.23,1.34-8.01,3.1-11.32,5.29-3.32,2.19-5.92,4.64-7.83,7.35-1.9,2.72-2.86,5.59-2.86,8.62s.95,5.59,2.86,7.46c1.9,1.87,4.34,2.8,7.3,2.8,2.61,0,4.8-.6,6.56-1.8,1.76-1.2,3.49-2.96,5.18-5.29.49-.7,1.01-1.04,1.53-1.01.53.04.83.41.9,1.11.35,1.9,1.02,3.54,2.01,4.92.99,1.38,2.78,2.06,4.47,2.06,2.26,0,4.62-1.15,6.41-3.44,1.8-2.29,2.7-6.01,2.7-11.16,0-1.2-.42-1.8-1.27-1.8ZM232.58,59.36c0,2.75-.49,5.22-1.48,7.41-.99,2.19-2.26,3.93-3.81,5.24-1.55,1.31-3.24,1.96-5.08,1.96-3.6,0-5.4-2.43-5.4-7.3,0-3.81,1.18-7.07,3.54-9.79,2.36-2.71,5.69-4.85,10-6.4,1.48-.56,2.22-.18,2.22,1.16v7.72Z"/>
    <path class="st0" d="M136.89,33.86c0-1.27-.2-2.15-.58-2.64-.39-.49-1.08-.78-2.06-.85l-2.43-.32c-.78-.14-1.16-.56-1.16-1.27s.39-1.13,1.16-1.27c1.97-.42,3.67-.92,5.08-1.48,1.41-.56,2.57-1.13,3.49-1.69,1.13-.7,1.97-1.06,2.54-1.06.78,0,1.16.57,1.16,1.69v45.81c0,3.38,2.05,4.56,6.58,4.56h0c4.53,0,6.58-1.18,6.58-4.56V11.23c0-1.27-.2-2.15-.58-2.64-.39-.49-1.08-.78-2.06-.85l-2.43-.32c-.78-.14-1.16-.56-1.16-1.27s.39-1.13,1.16-1.27c1.97-.42,3.67-.92,5.08-1.48,1.41-.56,2.57-1.13,3.49-1.69,1.13-.7,1.97-1.06,2.54-1.06.78,0,1.16.57,1.16,1.69v68.45c0,1.48.23,2.52.69,3.12.46.6,1.43,1.01,2.91,1.22l2.43.32c.78.14,1.16.57,1.16,1.27,0,.78-.42,1.16-1.27,1.16h-39.4c-.85,0-1.27-.39-1.27-1.16,0-.7.39-1.13,1.16-1.27l2.43-.32c1.48-.21,2.45-.62,2.91-1.22.46-.6.69-1.64.69-3.12v-36.92Z"/>
    <ellipse class="st0" cx="140.48" cy="11.87" rx="4.92" ry="5.21"/>
    <path class="st0" d="M47.12,20.01c-2.19-5.78-5.29-10.28-9.31-13.49-4.02-3.21-8.78-4.81-14.28-4.81H2.16c-1.06,0-1.59.39-1.59,1.16,0,.63.46,1.06,1.38,1.27l2.43.42c1.48.28,2.45.67,2.91,1.16.46.49.69,1.48.69,2.96v62.21c0,1.48-.23,2.47-.69,2.96-.46.49-1.43.88-2.91,1.16l-2.43.42c-.92.21-1.38.63-1.38,1.27,0,.78.53,1.16,1.59,1.16h21.37c5.5,0,10.26-1.6,14.28-4.81,4.02-3.21,7.12-7.71,9.31-13.49,2.19-5.78,3.28-12.17,3.28-19.78s-1.09-14-3.28-19.78ZM37.44,65.76c-3.14,6.24-7.78,9.36-13.91,9.36-5.36,0-8.04-2.58-8.04-7.72V12.18c0-5.15,2.68-7.72,8.04-7.72,6.14,0,10.77,3.12,13.91,9.36,3.14,6.24,4.71,14.69,4.71,25.97s-1.57,19.73-4.71,25.97Z"/>
  </g>
</svg>
"""

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
    @import url('https://fonts.googleapis.com/css2?family=Host+Grotesk:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&display=swap');

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

    * {{
        font-family: 'Host Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    .main {{
        background-color: {DARK_BG};
    }}
    .stApp {{
        background-color: {DARK_BG};
    }}
    [data-testid="stAppViewContainer"] {{
        background-color: {DARK_BG};
    }}
    .login-title-card {{
        max-width: 420px;
        margin: 100px auto 0 auto;
        background: {DARK_PURPLE};
        padding: 40px;
        border-radius: 8px 8px 0 0;
        border: 1px solid rgba(232, 215, 160, 0.2);
        text-align: center;
    }}
    .login-form-card {{
        max-width: 420px;
        margin: 0 auto;
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
        font-size: 0.75em;
        margin-top: 24px;
        font-family: 'DM Mono', monospace;
        letter-spacing: 0.02em;
    }}
    .footer-text a {{
        color: {DARK_PURPLE};
        text-decoration: none;
    }}
    .footer-text small {{
        font-family: 'DM Mono', monospace;
    }}
</style>
"""

dashboard_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:wght@400;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Host+Grotesk:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&display=swap');

    * {{
        font-family: 'Host Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}

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
    .stApp {{
        background-color: {DARK_BG};
    }}
    [data-testid="stAppViewContainer"] {{
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
        font-size: 0.75em;
        color: rgba(232, 215, 160, 0.7);
        font-family: 'DM Mono', monospace;
        letter-spacing: 0.02em;
    }}
    .stButton button {{
        background-color: {DARK_PURPLE};
        color: white;
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
        background-color: {DARK_ACCENT};
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(74, 68, 88, 0.4);
    }}
    .stSelectbox label {{
        color: {CREAM} !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.85em !important;
    }}
    .stSelectbox > div > div {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(232, 215, 160, 0.4) !important;
        color: white !important;
    }}
    .stSelectbox [data-baseweb="select"] {{
        background-color: rgba(255, 255, 255, 0.1) !important;
    }}
    .stSelectbox [data-baseweb="select"] > div {{
        color: white !important;
    }}
    .stDownloadButton button {{
        background-color: {DARK_PURPLE};
        color: white;
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
        background-color: {DARK_ACCENT};
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(74, 68, 88, 0.4);
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
    small {{
        font-family: 'DM Mono', monospace;
        font-size: 0.75em;
        letter-spacing: 0.02em;
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

    # Spacer
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)

    # Logo and title (centered using columns)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Open title card container
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 0;'>
            <div style='background: {DARK_PURPLE}; padding: 40px 40px 20px 40px; border-radius: 8px 8px 0 0; border: 1px solid rgba(232, 215, 160, 0.2);'>
                <div style='color: white; margin-bottom: 24px;'>
        """, unsafe_allow_html=True)

        # Logo only (separate to avoid quote conflicts)
        st.markdown(LOGO_SVG, unsafe_allow_html=True)

        # Close logo div and add title/subtitle
        st.markdown(f"""
                </div>
                <h1 style='color: white; font-family: "Instrument Serif", Georgia, serif; font-size: 2.5em; font-weight: 400; margin: 0 0 8px 0; letter-spacing: -0.02em;'>AI Visibility Report</h1>
                <p style='color: {CREAM}; margin: 0; font-size: 0.9em; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 400;'>Client Portal</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Form container
        st.markdown("""
        <div style='background: white; padding: 40px; border-radius: 0 0 8px 8px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); margin-top: -10px;'>
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
                    st.session_state.role = get_user_role(username)
                    brand = get_user_brand(username)

                    # If admin (ALL), set to None so they can select
                    st.session_state.brand_name = None if brand == "ALL" else brand
                    st.session_state.login_time = datetime.now()
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

        st.markdown("</div>", unsafe_allow_html=True)

        # Footer - open container
        st.markdown("""
        <div style='text-align: center; margin-top: 32px;'>
            <div style='color: #4A4458; margin-bottom: 12px;'>
        """, unsafe_allow_html=True)

        # Footer logo (separate to avoid quote conflicts)
        st.markdown(LOGO_SVG.replace('width: 180px', 'width: 120px'), unsafe_allow_html=True)

        # Close footer
        st.markdown(f"""
            </div>
            <p style='color: #999; font-size: 0.75em; font-family: "DM Mono", monospace; letter-spacing: 0.02em;'>
                Need help? <a href='mailto:{SUPPORT_EMAIL}' style='color: #4A4458; text-decoration: none;'>Contact support</a>
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
                if st.button("View Report", use_container_width=True):
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

        # Logo
        st.markdown(f"""
        <div style='text-align: center; margin-top: 24px; color: {CREAM}; opacity: 0.6;'>
            {LOGO_SVG.replace('width: 180px', 'width: 140px')}
        </div>
        """, unsafe_allow_html=True)

        # Footer text
        st.markdown(f"""
        <p style='text-align: center; color: rgba(232, 215, 160, 0.6); font-size: 0.85em; margin-top: 12px;'>
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
