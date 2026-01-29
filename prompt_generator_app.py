"""
Prompt Generator & Approval Tool - Standalone Streamlit App
Interactive tool for generating, reviewing, and approving prompts before importing to dashboard.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Page config
st.set_page_config(
    page_title="Prompt Generator & Approval Tool",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication - ADMIN ONLY (blocks clients)
from src.authentication import require_authentication, show_user_info
require_authentication(allow_clients=False)  # Only admin can access

# DaSilva brand colors (from main dashboard)
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
    .stButton button {{
        background-color: {DEEP_PLUM};
        color: white;
        border-radius: 6px;
        font-weight: 600;
    }}
    .stButton button:hover {{
        background-color: {ACCENT_PINK};
    }}
    div[data-testid="stSidebarNav"] {{
        background-color: {DEEP_PLUM};
    }}
    .sidebar .sidebar-content {{
        background-color: {DEEP_PLUM};
    }}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'generate'
if 'generated_prompts' not in st.session_state:
    st.session_state.generated_prompts = []
if 'approval_manager' not in st.session_state:
    from src.prompt_generator.approval_manager import ApprovalManager
    st.session_state.approval_manager = ApprovalManager()
if 'generation_config' not in st.session_state:
    st.session_state.generation_config = {
        'total_prompts': 100,
        'competitor_ratio': 0.3,
        'ai_ratio': 0.7,
        'deduplication_mode': 'high_similarity',
        'personas_file': 'data/natasha_denona_personas.json',
        'keywords_file': 'data/natasha_denona_keywords.csv'
    }

# Sidebar navigation
with st.sidebar:
    st.markdown(f"<h1 style='color: white;'>✨ Prompt Generator</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Navigation
    st.markdown("<p style='color: white; font-weight: 600;'>Navigation</p>", unsafe_allow_html=True)

    page = st.radio(
        "",
        ["Generate", "Review & Approve", "Export", "Settings"],
        key="nav_radio",
        label_visibility="collapsed"
    )

    # Update session state
    st.session_state.page = page.lower().replace(" & ", "_").replace(" ", "_")

    st.markdown("---")

    # Quick stats
    if st.session_state.generated_prompts:
        st.markdown("<p style='color: white; font-weight: 600;'>Session Stats</p>", unsafe_allow_html=True)
        stats = st.session_state.approval_manager.get_approval_stats()
        st.markdown(f"<p style='color: {OFF_WHITE};'>Total: {stats['total']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: {OFF_WHITE};'>✓ Approved: {stats['approved']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: {OFF_WHITE};'>✗ Rejected: {stats['rejected']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: {OFF_WHITE};'>⏳ Pending: {stats['pending']}</p>", unsafe_allow_html=True)

    # Show user info and logout button
    show_user_info()

    st.markdown(f"<p style='color: {DUSTY_ROSE}; font-size: 12px;'>DaSilva Consulting</p>", unsafe_allow_html=True)

# Main content - route to appropriate page
if st.session_state.page == 'generate':
    from prompt_generator_pages import generate
    generate.render()
elif st.session_state.page == 'review_&_approve':
    from prompt_generator_pages import review
    review.render()
elif st.session_state.page == 'export':
    from prompt_generator_pages import export_page
    export_page.render()
elif st.session_state.page == 'settings':
    from prompt_generator_pages import settings
    settings.render()
