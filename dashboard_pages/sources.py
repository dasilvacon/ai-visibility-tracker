"""
Sources & Citations Dashboard Page.

Redesigned to use enriched source data with context-aware co-mention tracking,
source categories, and relevance scoring.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import sys
from pathlib import Path
from collections import defaultdict

# Add src to path
sys.path.insert(0, 'src')
from analysis.source_analyzer import SourceAnalyzer

# Light theme colors
LIGHT_BG = '#FFFFFF'
TEXT_DARK = '#1c1c1c'
DARK_PURPLE = '#4A4458'
BORDER_LIGHT = '#E0E0E0'
GREEN = '#27AE60'
ORANGE = '#F39C12'
RED = '#E74C3C'
BLUE = '#3498DB'

# Category colors
CATEGORY_COLORS = {
    'government': '#3498DB',
    'industry': '#27AE60',
    'media': '#9B59B6',
    'social': '#E74C3C',
    'academic': '#F39C12',
    'resource': '#1ABC9C',
    'general': '#95A5A6',
    'uncategorized': '#BDC3C7'
}


def show(brand_name: str, data: dict):
    """Display the redesigned sources and citations page."""

    st.title("Source Intelligence")

    st.markdown("""
    <div style='background-color: #F5F5F5; padding: 16px; border-radius: 8px; margin-bottom: 24px;'>
        <p style='margin: 0; color: #1c1c1c;'>
            Analyze which third-party sites, organizations, and platforms are citing your brand in AI responses.
            Sources are categorized by type and scored for relevance to help you prioritize outreach.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Check for data
    if data.get('sources') is None:
        st.warning("No source data available. Run a test from the Run Report page first.")
        return

    sources_df = data['sources'].copy()
    source_analysis = data.get('source_analysis', {})

    # Get brand config for flagging irrelevant sources
    client_slug = st.session_state.get('client_slug', '')
    brand_config_path = None
    if client_slug:
        brand_config_path = f"data/{client_slug}/{client_slug}_brand_config.json"

    # ============================================================
    # SECTION 1: Source Intelligence Overview
    # ============================================================
    st.markdown("## Source Intelligence Overview")

    col1, col2, col3, col4 = st.columns(4)

    total_sources = len(sources_df)

    # Count sources with brand co-mentions
    brand_co_mention_col = 'Brand Co-mentions' if 'Brand Co-mentions' in sources_df.columns else 'Your Brand Mentions'
    sources_with_brand = len(sources_df[sources_df.get(brand_co_mention_col, sources_df.get('Your Brand Mentions', 0)) > 0])

    # Count industry-relevant sources (have a category)
    category_col = 'Category' if 'Category' in sources_df.columns else None
    if category_col:
        industry_relevant = len(sources_df[
            (sources_df[category_col] != 'uncategorized') &
            (sources_df[category_col] != 'general') &
            (sources_df[category_col].notna())
        ])
    else:
        industry_relevant = 0

    # Count noise sources (uncategorized with 0 brand co-mentions)
    if category_col:
        noise_sources = len(sources_df[
            ((sources_df[category_col] == 'uncategorized') | (sources_df[category_col] == 'general')) &
            (sources_df.get(brand_co_mention_col, sources_df.get('Your Brand Mentions', 0)) == 0)
        ])
    else:
        noise_sources = 0

    with col1:
        st.metric("Total Sources", total_sources)

    with col2:
        st.metric("With Brand Co-mentions", sources_with_brand,
                 help="Sources where your brand appears in the same context snippet")

    with col3:
        st.metric("Industry-Relevant", industry_relevant,
                 help="Sources matching your configured categories")

    with col4:
        st.metric("Noise/Uncategorized", noise_sources,
                 delta=f"-{noise_sources}" if noise_sources > 0 else None,
                 delta_color="inverse",
                 help="Uncategorized sources with no brand co-mentions")

    st.markdown("---")

    # ============================================================
    # SECTION 2: Sources by Category
    # ============================================================
    st.markdown("## Sources by Category")

    if category_col and category_col in sources_df.columns:
        # Group by category
        category_groups = sources_df.groupby(category_col).agg({
            'Source': 'count',
            brand_co_mention_col if brand_co_mention_col in sources_df.columns else 'Your Brand Mentions': 'sum',
            'Total Appearances': 'sum'
        }).reset_index()

        category_groups.columns = ['Category', 'Source Count', 'Brand Co-mentions', 'Total Appearances']

        # Calculate overall brand co-mention rate per category
        category_groups['Brand Co-mention Rate'] = (
            category_groups['Brand Co-mentions'] / category_groups['Total Appearances'] * 100
        ).fillna(0).round(1)

        # Sort by source count
        category_groups = category_groups.sort_values('Source Count', ascending=False)

        # Create expandable cards for each category
        cols = st.columns(min(3, len(category_groups)))

        for i, (_, row) in enumerate(category_groups.iterrows()):
            col_idx = i % 3
            category = row['Category']
            color = CATEGORY_COLORS.get(category, CATEGORY_COLORS['uncategorized'])

            with cols[col_idx]:
                with st.container():
                    st.markdown(f"""
                    <div style='background-color: #F8F9FA; padding: 16px; border-radius: 8px;
                                border-left: 4px solid {color}; margin-bottom: 12px;'>
                        <h4 style='margin: 0 0 8px 0; color: {color};'>{category.title()}</h4>
                        <p style='margin: 4px 0; font-size: 24px; font-weight: bold;'>{int(row['Source Count'])} sources</p>
                        <p style='margin: 4px 0; font-size: 14px; color: #666;'>
                            Brand Co-mention Rate: {row['Brand Co-mention Rate']:.1f}%
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

            # Reset columns every 3 categories
            if col_idx == 2 and i < len(category_groups) - 1:
                cols = st.columns(min(3, len(category_groups) - i - 1))

        # Category distribution chart
        with st.expander("View Category Distribution Chart"):
            fig = px.pie(
                category_groups,
                values='Source Count',
                names='Category',
                color='Category',
                color_discrete_map=CATEGORY_COLORS
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Source categories not configured. Add source_categories to your brand_config.json.")

    st.markdown("---")

    # ============================================================
    # SECTION 3: Source Detail Table
    # ============================================================
    st.markdown("## Source Detail Table")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        if category_col and category_col in sources_df.columns:
            categories = ['All Categories'] + sorted(sources_df[category_col].unique().tolist())
            selected_category = st.selectbox("Filter by Category", categories)
        else:
            selected_category = 'All Categories'

    with col2:
        min_appearances = st.number_input("Min Appearances", min_value=0, value=0, step=1)

    with col3:
        brand_filter = st.selectbox(
            "Brand Co-mention",
            ["All", "With Brand Co-mention", "Without Brand Co-mention"]
        )

    # Sort options
    sort_options = {
        'Relevance Score': 'Relevance Score',
        'Total Appearances': 'Total Appearances',
        'Brand Co-mention Rate': 'Brand Co-mention %' if 'Brand Co-mention %' in sources_df.columns else 'Your Brand %'
    }
    sort_by = st.selectbox("Sort by", list(sort_options.keys()))

    # Apply filters
    filtered_df = sources_df.copy()

    if selected_category != 'All Categories' and category_col:
        filtered_df = filtered_df[filtered_df[category_col] == selected_category]

    if min_appearances > 0:
        filtered_df = filtered_df[filtered_df['Total Appearances'] >= min_appearances]

    brand_col = brand_co_mention_col if brand_co_mention_col in filtered_df.columns else 'Your Brand Mentions'
    if brand_filter == "With Brand Co-mention":
        filtered_df = filtered_df[filtered_df[brand_col] > 0]
    elif brand_filter == "Without Brand Co-mention":
        filtered_df = filtered_df[filtered_df[brand_col] == 0]

    # Apply sorting
    sort_col = sort_options[sort_by]
    if sort_col in filtered_df.columns:
        if '%' in str(filtered_df[sort_col].iloc[0]) if len(filtered_df) > 0 else False:
            filtered_df['_sort_key'] = filtered_df[sort_col].str.rstrip('%').astype(float)
        else:
            filtered_df['_sort_key'] = pd.to_numeric(filtered_df[sort_col], errors='coerce').fillna(0)
        filtered_df = filtered_df.sort_values('_sort_key', ascending=False).drop('_sort_key', axis=1)

    st.caption(f"Showing {len(filtered_df)} sources")

    # ============================================================
    # SECTION 4: Source Deep Dive (Expandable Cards)
    # ============================================================
    if filtered_df.empty:
        st.info("No sources match the selected filters.")
    else:
        for idx, row in filtered_df.iterrows():
            source_name = row['Source']
            category = row.get('Category', row.get(category_col, 'uncategorized')) if category_col else 'uncategorized'
            category_color = CATEGORY_COLORS.get(category, CATEGORY_COLORS['uncategorized'])

            # Determine position badge
            avg_pos = row.get('Avg Position', 0.5)
            if isinstance(avg_pos, str):
                try:
                    avg_pos = float(avg_pos)
                except:
                    avg_pos = 0.5

            if avg_pos < 0.3:
                position_badge = "Early"
                position_color = GREEN
            elif avg_pos < 0.7:
                position_badge = "Mid"
                position_color = ORANGE
            else:
                position_badge = "Late"
                position_color = RED

            # Relevance score
            relevance = row.get('Relevance Score', 0)
            if isinstance(relevance, str):
                try:
                    relevance = int(relevance)
                except:
                    relevance = 0

            # Create header with key info
            brand_co_mentions = row.get('Brand Co-mentions', row.get('Your Brand Mentions', 0))
            total_appearances = row.get('Total Appearances', 0)

            header_html = f"""
            <div style='display: flex; align-items: center; gap: 12px;'>
                <span style='background-color: {category_color}; color: white; padding: 2px 8px;
                            border-radius: 4px; font-size: 12px;'>{category}</span>
                <span style='font-weight: bold;'>{source_name}</span>
                <span style='color: #666;'>|</span>
                <span>{total_appearances} appearances</span>
                <span style='color: #666;'>|</span>
                <span style='background-color: {position_color}; color: white; padding: 2px 6px;
                            border-radius: 4px; font-size: 11px;'>{position_badge}</span>
                <span style='color: #666;'>|</span>
                <span>Relevance: {relevance}/100</span>
            </div>
            """

            with st.expander(f"{source_name} - {category} ({relevance}/100 relevance)"):
                st.markdown(header_html, unsafe_allow_html=True)
                st.markdown("")

                # Metrics row
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Appearances", total_appearances)

                with col2:
                    brand_rate = row.get('Brand Co-mention %', row.get('Your Brand %', '0%'))
                    st.metric("Brand Co-mentions", f"{brand_co_mentions} ({brand_rate})")

                with col3:
                    top_comp = row.get('Top Competitor', 'None')
                    comp_count = row.get('Competitor Co-mentions', row.get('Competitor Mentions', 0))
                    st.metric("Top Competitor", f"{top_comp}" if top_comp else "None")

                with col4:
                    st.metric("Avg Position", f"{avg_pos:.2f}" if isinstance(avg_pos, float) else avg_pos)

                # Context samples
                context_samples = source_analysis.get('all_sources', [])
                source_data = next((s for s in context_samples if s.get('domain') == source_name), None)

                if source_data and source_data.get('context_samples'):
                    st.markdown("**Context Snippets:**")
                    for sample in source_data['context_samples'][:3]:
                        st.markdown(f"> {sample[:200]}...")

                # Prompt IDs
                if source_data and source_data.get('prompt_ids'):
                    st.markdown("**Triggered by Prompts:**")
                    prompt_ids = source_data['prompt_ids'][:5]
                    st.markdown(", ".join(prompt_ids))

                # Example URLs
                if row.get('Example URLs'):
                    st.markdown("**Example URLs:**")
                    urls = str(row['Example URLs']).split('; ')
                    for url in urls[:3]:
                        if url.strip():
                            st.markdown(f"- {url}")

                # Flag as Irrelevant button
                st.markdown("---")
                if brand_config_path:
                    if st.button(f"Flag as Irrelevant", key=f"flag_{source_name}"):
                        analyzer = SourceAnalyzer()
                        if analyzer.flag_irrelevant_source(source_name, brand_config_path):
                            st.success(f"Flagged '{source_name}' as irrelevant. It will be excluded from future analyses.")
                            st.rerun()
                        else:
                            st.error("Could not flag source. Check brand_config.json permissions.")

    st.markdown("---")

    # ============================================================
    # SECTION 5: Gap Opportunities
    # ============================================================
    st.markdown("## Gap Opportunities")

    st.markdown("""
    Sources where competitors appear but your brand doesn't. Filtered to show only
    relevant sources (relevance score > 30).
    """)

    # Filter for gap opportunities
    relevance_col = 'Relevance Score'
    should_target_col = 'Should Target'

    gap_df = sources_df.copy()

    if relevance_col in gap_df.columns and should_target_col in gap_df.columns:
        # Convert relevance to numeric
        gap_df['_relevance'] = pd.to_numeric(gap_df[relevance_col], errors='coerce').fillna(0)

        gap_df = gap_df[
            (gap_df[should_target_col] == 'YES') &
            (gap_df['_relevance'] > 30)
        ].drop('_relevance', axis=1)

        # Sort by opportunity score
        if 'Opportunity Score' in gap_df.columns:
            gap_df['_opp'] = pd.to_numeric(gap_df['Opportunity Score'], errors='coerce').fillna(0)
            gap_df = gap_df.sort_values('_opp', ascending=False).drop('_opp', axis=1)

        if gap_df.empty:
            st.success("No significant gap opportunities found. You're present in relevant sources!")
        else:
            st.warning(f"Found {len(gap_df)} gap opportunities where competitors are cited but you're not.")

            for idx, row in gap_df.head(10).iterrows():
                source_name = row['Source']
                opp_score = row.get('Opportunity Score', 0)
                top_comp = row.get('Top Competitor', 'Unknown')
                category = row.get('Category', row.get(category_col, 'uncategorized')) if category_col else 'uncategorized'

                with st.expander(f"{source_name} - Opportunity Score: {opp_score}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**Category:** {category}")
                        st.markdown(f"**Total Appearances:** {row.get('Total Appearances', 0)}")
                        st.markdown(f"**Top Competitor:** {top_comp}")

                    with col2:
                        st.markdown(f"**Competitor Mentions:** {row.get('Competitor Mentions', row.get('Competitor Co-mentions', 0))}")
                        st.markdown(f"**Relevance Score:** {row.get('Relevance Score', 0)}/100")

                    st.markdown("**Recommended Action:**")
                    st.info(row.get('Recommended Action', 'Reach out for backlink opportunities and product features'))
    else:
        st.info("Gap opportunity data not available.")

    st.markdown("---")

    # ============================================================
    # Export Section
    # ============================================================
    st.markdown("## Export Data")

    col1, col2 = st.columns(2)

    with col1:
        csv = filtered_df.to_csv(index=False)
        brand_slug = brand_name.replace(' ', '_')

        st.download_button(
            "Download Filtered Sources (CSV)",
            data=csv,
            file_name=f"sources_{brand_slug}_filtered.csv",
            mime="text/csv"
        )

    with col2:
        if not gap_df.empty:
            gap_csv = gap_df.to_csv(index=False)
            st.download_button(
                "Download Gap Opportunities (CSV)",
                data=gap_csv,
                file_name=f"gap_opportunities_{brand_slug}.csv",
                mime="text/csv"
            )
