"""
AI Visibility Tracker - Streamlit Dashboard
Interactive web dashboard for client reports
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import json
import sys
from datetime import datetime

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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'brand_name' not in st.session_state:
    st.session_state.brand_name = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None

# Sidebar
with st.sidebar:
    st.markdown(f"<h1 style='color: white;'>🎯 AI Visibility</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Brand selector
    reports_dir = Path('data/reports')
    if reports_dir.exists():
        # Find available brands
        html_reports = list(reports_dir.glob('visibility_report_*.html'))
        brands = [f.stem.replace('visibility_report_', '').replace('_', ' ') for f in html_reports]

        if brands:
            selected_brand = st.selectbox(
                "Select Brand",
                brands,
                index=0 if st.session_state.brand_name is None else brands.index(st.session_state.brand_name) if st.session_state.brand_name in brands else 0
            )
            st.session_state.brand_name = selected_brand
        else:
            st.warning("No reports found. Run analysis first.")
            st.stop()

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

# Load data
if st.session_state.brand_name:
    data = load_analysis_data(st.session_state.brand_name)
else:
    st.error("Please select a brand from the sidebar")
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
