"""Sources & Citations page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# Brand colors
DEEP_PLUM = '#402E3A'
DUSTY_ROSE = '#A78E8B'
ACCENT_PINK = '#D4698B'
GREEN = '#27AE60'
ORANGE = '#F39C12'
RED = '#E74C3C'


def show(brand_name: str, data: dict):
    """Display sources and citations page."""

    st.title("🎯 Sources & Citations")

    st.markdown("""
    This section shows which third-party sites (Sephora, Reddit, beauty blogs, etc.)
    are citing your brand vs competitors in AI responses.
    """)

    if data.get('sources') is None:
        st.warning("No source data available.")
        return

    sources_df = data['sources'].copy()

    # Summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        total_sources = len(sources_df)
        st.metric("Total Sources Found", total_sources)

    with col2:
        sources_with_you = len(sources_df[sources_df['Your Brand Mentions'] > 0])
        st.metric("Sources Mentioning You", sources_with_you)

    with col3:
        gap_opportunities = len(sources_df[sources_df['Should Target'] == 'YES'])
        st.metric("Gap Opportunities", gap_opportunities, delta=f"-{gap_opportunities}")

    st.markdown("---")

    # Filter section
    st.subheader("🔍 Filter Sources")

    col1, col2 = st.columns(2)

    with col1:
        filter_option = st.selectbox(
            "Show:",
            ["All Sources", "Where You're Mentioned", "Gap Opportunities Only", "High Priority Targets"]
        )

    with col2:
        sort_by = st.selectbox(
            "Sort by:",
            ["Opportunity Score", "Total Appearances", "Your Brand %", "Competitor %"]
        )

    # Apply filters
    filtered_df = sources_df.copy()

    if filter_option == "Where You're Mentioned":
        filtered_df = filtered_df[filtered_df['Your Brand Mentions'] > 0]
    elif filter_option == "Gap Opportunities Only":
        filtered_df = filtered_df[filtered_df['Should Target'] == 'YES']
    elif filter_option == "High Priority Targets":
        filtered_df = filtered_df[
            (filtered_df['Should Target'] == 'YES') &
            (filtered_df['Priority'] == 'HIGH')
        ]

    # Apply sorting
    sort_map = {
        "Opportunity Score": "Opportunity Score",
        "Total Appearances": "Total Appearances",
        "Your Brand %": "Your Brand %",
        "Competitor %": "Competitor %"
    }
    sort_col = sort_map[sort_by]

    # Convert percentage strings to float for sorting
    if '%' in str(filtered_df[sort_col].iloc[0]):
        filtered_df['_sort_key'] = filtered_df[sort_col].str.rstrip('%').astype(float)
    else:
        filtered_df['_sort_key'] = filtered_df[sort_col]

    filtered_df = filtered_df.sort_values('_sort_key', ascending=False).drop('_sort_key', axis=1)

    st.markdown("---")

    # Display sources
    if filtered_df.empty:
        st.info("No sources match the selected filters.")
    else:
        st.subheader(f"📊 {len(filtered_df)} Sources Found")

        # Display as expandable cards
        for idx, row in filtered_df.iterrows():
            with st.expander(f"**{row['Source']}** - Opportunity Score: {row['Opportunity Score']}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**Your Brand**")
                    st.markdown(f"Mentions: {row['Your Brand Mentions']}")
                    st.markdown(f"Rate: {row['Your Brand %']}")

                with col2:
                    st.markdown("**Competitors**")
                    st.markdown(f"Mentions: {row['Competitor Mentions']}")
                    st.markdown(f"Rate: {row['Competitor %']}")
                    if row['Top Competitor']:
                        st.markdown(f"Top: {row['Top Competitor']}")

                with col3:
                    st.markdown("**Status**")
                    if row['Should Target'] == 'YES':
                        priority = row.get('Priority', 'MEDIUM')
                        emoji = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
                        st.markdown(f"{emoji} **TARGET** ({priority} Priority)")
                    else:
                        st.markdown("✅ **Present**")

                # Recommended action
                st.markdown("**Recommended Action:**")
                st.info(row.get('Recommended Action', 'Maintain current relationship'))

                # Example URLs if available
                if row.get('Example URLs'):
                    st.markdown("**Example URLs:**")
                    urls = row['Example URLs'].split('; ')
                    for url in urls[:3]:
                        if url.strip():
                            st.markdown(f"- {url}")

        # Visualization
        st.markdown("---")
        st.subheader("📈 Source Opportunity Visualization")

        # Create bubble chart
        viz_df = filtered_df.copy()
        viz_df['Your Brand %'] = viz_df['Your Brand %'].str.rstrip('%').astype(float)
        viz_df['Competitor %'] = viz_df['Competitor %'].str.rstrip('%').astype(float)

        fig = go.Figure()

        # Add scatter points
        fig.add_trace(go.Scatter(
            x=viz_df['Your Brand %'],
            y=viz_df['Competitor %'],
            mode='markers+text',
            marker=dict(
                size=viz_df['Opportunity Score'],
                color=viz_df['Opportunity Score'],
                colorscale=[[0, DUSTY_ROSE], [1, RED]],
                showscale=True,
                colorbar=dict(title="Opportunity<br>Score"),
                line=dict(width=1, color=DEEP_PLUM)
            ),
            text=viz_df['Source'],
            textposition='top center',
            hovertemplate='<b>%{text}</b><br>' +
                         'Your Brand: %{x:.1f}%<br>' +
                         'Competitors: %{y:.1f}%<br>' +
                         '<extra></extra>'
        ))

        # Add quadrant lines
        fig.add_shape(type="line", x0=0, y0=50, x1=100, y1=50,
                     line=dict(color=DUSTY_ROSE, width=1, dash="dash"))
        fig.add_shape(type="line", x0=50, y0=0, x1=50, y1=100,
                     line=dict(color=DUSTY_ROSE, width=1, dash="dash"))

        # Add quadrant labels
        fig.add_annotation(x=75, y=75, text="Both Present",
                          showarrow=False, font=dict(color=GREEN, size=10))
        fig.add_annotation(x=25, y=75, text="Target Zone",
                          showarrow=False, font=dict(color=RED, size=12, family="Arial Black"))
        fig.add_annotation(x=75, y=25, text="Your Advantage",
                          showarrow=False, font=dict(color=GREEN, size=10))
        fig.add_annotation(x=25, y=25, text="Low Priority",
                          showarrow=False, font=dict(color=DUSTY_ROSE, size=10))

        fig.update_layout(
            title="Source Opportunity Matrix",
            xaxis_title="Your Brand Mention Rate (%)",
            yaxis_title="Competitor Mention Rate (%)",
            height=500,
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(range=[0, 100], gridcolor='lightgray'),
            yaxis=dict(range=[0, 100], gridcolor='lightgray')
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption("💡 **Target Zone** = High competitor presence, low your brand presence (biggest opportunities)")

    # Download section
    st.markdown("---")
    st.subheader("📥 Export Source List")

    csv = filtered_df.to_csv(index=False)
    brand_slug = brand_name.replace(' ', '_')

    st.download_button(
        "📊 Download Filtered Sources (CSV)",
        data=csv,
        file_name=f"sources_{brand_slug}_filtered.csv",
        mime="text/csv"
    )
