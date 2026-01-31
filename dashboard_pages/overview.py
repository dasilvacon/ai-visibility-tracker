"""Overview dashboard page."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import re

# Brand colors
DEEP_PLUM = '#402E3A'
DUSTY_ROSE = '#A78E8B'
ACCENT_PINK = '#D4698B'
CHARCOAL = '#1C1C1C'


def show(brand_name: str, data: dict):
    """Display overview dashboard."""

    st.title(f"AI Visibility Dashboard - {brand_name}")

    # Parse key metrics from text report
    metrics = parse_metrics(data.get('text_report', ''))

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Your Visibility",
            f"{metrics.get('visibility_rate', 0):.1f}%",
            delta=None,
            help="Percentage of AI responses that mention your brand"
        )

    with col2:
        top_comp = metrics.get('top_competitor', 'N/A')
        top_comp_rate = metrics.get('top_competitor_rate', 0)
        st.metric(
            "Top Competitor",
            top_comp,
            delta=f"{top_comp_rate:.1f}%",
            help="Leading competitor and their visibility rate"
        )

    with col3:
        gap = metrics.get('top_competitor_rate', 0) - metrics.get('visibility_rate', 0)
        st.metric(
            "Gap to Close",
            f"{gap:.1f}%",
            delta=f"{-gap:.1f}%",
            delta_color="inverse",
            help="Percentage points behind top competitor"
        )

    with col4:
        st.metric(
            "Queries Tested",
            metrics.get('queries_tested', 0),
            help="Total number of prompts tested across all scenarios"
        )

    st.markdown("---")

    # Competitive Landscape
    if data.get('competitors') is not None:
        st.subheader("🏆 Competitive Landscape")

        comp_df = data['competitors'].copy()

        # Create bar chart
        fig = go.Figure()

        # Add bars
        colors = [DEEP_PLUM if row['Brand Name'] == brand_name else DUSTY_ROSE
                 for _, row in comp_df.iterrows()]

        fig.add_trace(go.Bar(
            x=comp_df['Brand Name'],
            y=comp_df['Mention Rate %'].str.rstrip('%').astype(float),
            marker_color=colors,
            text=comp_df['Mention Rate %'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Mention Rate: %{y:.1f}%<extra></extra>'
        ))

        fig.update_layout(
            title="Brand Visibility Comparison",
            xaxis_title="Brand",
            yaxis_title="Mention Rate (%)",
            height=400,
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color=CHARCOAL)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Competitor table
        with st.expander("📊 Detailed Comparison"):
            st.dataframe(
                comp_df,
                use_container_width=True,
                hide_index=True
            )

    st.markdown("---")

    # Source Overview
    if data.get('sources') is not None:
        st.subheader("🎯 Source Overview")

        sources_df = data['sources'].copy()

        col1, col2 = st.columns(2)

        with col1:
            # Top sources with your brand
            st.markdown("**Where You're Being Mentioned**")
            your_sources = sources_df[sources_df['Your Brand Mentions'] > 0].copy()
            your_sources = your_sources.sort_values('Your Brand Mentions', ascending=False).head(5)

            if not your_sources.empty:
                for _, row in your_sources.iterrows():
                    st.markdown(f"- **{row['Source']}**: {row['Your Brand Mentions']} mentions ({row['Your Brand %']})")
            else:
                st.info("No sources found mentioning your brand yet.")

        with col2:
            # Top gap opportunities
            st.markdown("**Top PR Opportunities**")
            gap_sources = sources_df[sources_df['Should Target'] == 'YES'].copy()
            gap_sources = gap_sources.sort_values('Opportunity Score', ascending=False).head(5)

            if not gap_sources.empty:
                for _, row in gap_sources.iterrows():
                    priority = row.get('Priority', 'MEDIUM')
                    emoji = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
                    st.markdown(f"{emoji} **{row['Source']}** (Score: {row['Opportunity Score']})")
            else:
                st.success("Great! You're present in all major sources.")

    st.markdown("---")

    # Action Plan Summary
    if data.get('action_plan') is not None:
        st.subheader("✅ Top Priority Actions")

        action_df = data['action_plan'].copy()

        # Show top 3 high priority items
        high_priority = action_df[action_df['Priority'] == 'HIGH'].head(3)

        for idx, row in high_priority.iterrows():
            with st.container():
                st.markdown(f"### {idx + 1}. {row['Opportunity Name'].title()}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Current Visibility", row['Current Visibility %'])
                with col2:
                    st.metric("Competitor Avg", row['Competitor Avg %'])
                with col3:
                    st.metric("Estimated Impact", row['Estimated Monthly Impact'])

                # Show specific actions
                actions = row['Specific Actions'].split(' | ')
                st.markdown("**Actions:**")
                for action in actions:
                    st.markdown(f"- {action}")

                st.markdown("---")

    # Download section
    st.subheader("📥 Download Reports")

    col1, col2, col3 = st.columns(3)

    brand_slug = brand_name.replace(' ', '_')

    with col1:
        try:
            with open(f'data/reports/executive_summary_{brand_slug}.pdf', 'rb') as f:
                st.download_button(
                    "📄 Executive Summary (PDF)",
                    data=f,
                    file_name=f"executive_summary_{brand_slug}.pdf",
                    mime="application/pdf"
                )
        except FileNotFoundError:
            st.info("PDF not available")

    with col2:
        try:
            with open(f'data/reports/visibility_report_{brand_slug}.html', 'r') as f:
                st.download_button(
                    "🌐 Full HTML Report",
                    data=f,
                    file_name=f"visibility_report_{brand_slug}.html",
                    mime="text/html"
                )
        except FileNotFoundError:
            st.info("HTML report not available")

    with col3:
        if data.get('raw_data') is not None:
            csv = data['raw_data'].to_csv(index=False)
            st.download_button(
                "📊 Raw Data (CSV)",
                data=csv,
                file_name=f"raw_data_{brand_slug}.csv",
                mime="text/csv"
            )


def parse_metrics(text_report: str) -> dict:
    """Parse key metrics from text report."""
    metrics = {
        'visibility_rate': 0,
        'top_competitor': 'N/A',
        'top_competitor_rate': 0,
        'queries_tested': 0
    }

    if not text_report:
        return metrics

    # Parse visibility rate
    vis_match = re.search(r'You(?:\'re| are) visible in ([\d.]+)%', text_report)
    if vis_match:
        metrics['visibility_rate'] = float(vis_match.group(1))

    # Parse top competitor
    comp_match = re.search(r'Your top competitor: ([^(]+) at ([\d.]+)%', text_report)
    if comp_match:
        metrics['top_competitor'] = comp_match.group(1).strip()
        metrics['top_competitor_rate'] = float(comp_match.group(2))

    # Parse queries tested
    query_match = re.search(r'Tested: (\d+)', text_report)
    if query_match:
        metrics['queries_tested'] = int(query_match.group(1))

    return metrics
