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

# Authentication - Both admin and clients can access main dashboard
from authentication import require_authentication, show_user_info, get_available_brands
require_authentication(allow_clients=True)  # Clients allowed

# DaSilva brand colors
DEEP_PLUM = '#402E3A'
DUSTY_ROSE = '#A78E8B'
CHARCOAL = '#1C1C1C'
OFF_WHITE = '#FBFBEF'
ACCENT_PINK = '#D4698B'

# Custom CSS for branding with high contrast
st.markdown(f"""
<style>
    /* Main background */
    .main {{
        background-color: {OFF_WHITE};
        color: {CHARCOAL};
    }}

    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        color: {DEEP_PLUM} !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}

    /* Regular text */
    p, label, span, div {{
        color: {CHARCOAL} !important;
    }}

    /* Metrics */
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
    .stMetric [data-testid="stMetricValue"] {{
        color: {CHARCOAL} !important;
    }}

    /* Buttons */
    .stButton > button {{
        background-color: {DUSTY_ROSE};
        color: white !important;
        border: none;
        border-radius: 6px;
        font-weight: 500;
    }}
    .stButton > button:hover {{
        background-color: {ACCENT_PINK};
    }}
    .stButton > button[kind="primary"] {{
        background-color: {DEEP_PLUM};
        color: white !important;
    }}
    .stDownloadButton button {{
        background-color: {DEEP_PLUM};
        color: white !important;
        border-radius: 6px;
    }}
    .stDownloadButton button:hover {{
        background-color: {ACCENT_PINK};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {DEEP_PLUM};
    }}
    [data-testid="stSidebar"] * {{
        color: {OFF_WHITE} !important;
    }}
    div[data-testid="stSidebarNav"] {{
        background-color: {DEEP_PLUM};
    }}

    /* Form inputs - MAXIMUM CONTRAST */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {{
        background-color: #FFFFFF !important;
        border: 2px solid {DUSTY_ROSE} !important;
        color: {CHARCOAL} !important;
        border-radius: 6px !important;
    }}

    /* Selectbox */
    .stSelectbox select,
    .stSelectbox > div > div {{
        background-color: #FFFFFF !important;
        color: {CHARCOAL} !important;
        border: 2px solid {DUSTY_ROSE} !important;
        border-radius: 6px !important;
    }}
    .stSelectbox [data-baseweb="select"] {{
        background-color: #FFFFFF !important;
    }}
    .stSelectbox [data-baseweb="select"] > div {{
        color: {CHARCOAL} !important;
        background-color: #FFFFFF !important;
    }}

    /* Placeholder text */
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {{
        color: {DUSTY_ROSE} !important;
        opacity: 0.7 !important;
    }}

    /* Input labels - dark and readable */
    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label,
    .stTextArea label,
    .stMultiSelect label,
    .stFileUploader label {{
        color: {DEEP_PLUM} !important;
        font-weight: 500 !important;
    }}

    /* Multi-select */
    .stMultiSelect > div > div {{
        background-color: #FFFFFF !important;
        border: 2px solid {DUSTY_ROSE} !important;
    }}
    .stMultiSelect [data-baseweb="tag"] {{
        background-color: {DUSTY_ROSE} !important;
        color: white !important;
    }}

    /* Tabs - fix yellow on yellow */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {OFF_WHITE} !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: white !important;
        color: {DEEP_PLUM} !important;
        border: 2px solid {DUSTY_ROSE} !important;
        border-radius: 4px 4px 0 0 !important;
        font-weight: 500 !important;
    }}

    .stTabs [data-baseweb="tab"] > div {{
        color: {DEEP_PLUM} !important;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: {DEEP_PLUM} !important;
        border: 2px solid {DEEP_PLUM} !important;
        color: white !important;
    }}

    .stTabs [aria-selected="true"] > div {{
        color: white !important;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        background-color: {OFF_WHITE} !important;
    }}

    /* File uploader */
    .stFileUploader section {{
        background-color: #FFFFFF !important;
        border: 2px dashed {DUSTY_ROSE} !important;
    }}
    .stFileUploader section > div {{
        color: {DEEP_PLUM} !important;
    }}

    /* Alert boxes */
    .stAlert {{
        background-color: #FFFFFF !important;
        border-left: 4px solid {DUSTY_ROSE} !important;
        color: {CHARCOAL} !important;
    }}

    /* Dataframe */
    .stDataFrame {{
        border: 1px solid {DUSTY_ROSE} !important;
    }}

    /* Expander */
    .stExpander {{
        background-color: #FFFFFF !important;
        border: 1px solid {DUSTY_ROSE} !important;
    }}
    .stExpander summary {{
        color: {DEEP_PLUM} !important;
        font-weight: 500 !important;
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
        all_brands = [f.stem.replace('visibility_report_', '').replace('_', ' ') for f in html_reports]

        # Filter brands based on user access
        available_brands = get_available_brands(all_brands)

        if available_brands:
            selected_brand = st.selectbox(
                "Select Brand",
                available_brands,
                index=0 if st.session_state.brand_name is None else available_brands.index(st.session_state.brand_name) if st.session_state.brand_name in available_brands else 0
            )
            st.session_state.brand_name = selected_brand
        else:
            st.warning("No reports found for your account. Contact your administrator.")
            st.stop()

    st.markdown("---")

    # Show user info and logout button
    show_user_info()

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
    from dashboard_pages import overview
    overview.show(st.session_state.brand_name, data)
elif page == "🎯 Sources & Citations":
    from dashboard_pages import sources
    sources.show(st.session_state.brand_name, data)
elif page == "✅ Action Plan":
    from dashboard_pages import action_plan
    action_plan.show(st.session_state.brand_name, data)
elif page == "🏆 Competitor Analysis":
    from dashboard_pages import competitors
    competitors.show(st.session_state.brand_name, data)
