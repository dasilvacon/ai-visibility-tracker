"""Competitor Analysis page."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Brand colors
DEEP_PLUM = '#402E3A'
DUSTY_ROSE = '#A78E8B'
ACCENT_PINK = '#D4698B'
CHARCOAL = '#1C1C1C'
RED = '#E74C3C'
GREEN = '#27AE60'


def show(brand_name: str, data: dict):
    """Display competitor analysis page."""

    st.title("🏆 Competitor Analysis")

    st.markdown("""
    Detailed competitive landscape showing how your brand compares to competitors
    across AI visibility metrics.
    """)

    if data.get('competitors') is None:
        st.warning("No competitor data available.")
        return

    comp_df = data['competitors'].copy()

    # Convert percentage strings to float
    comp_df['Mention Rate'] = comp_df['Mention Rate %'].str.rstrip('%').astype(float)
    comp_df['Gap'] = comp_df['Gap vs Your Brand'].str.rstrip('%').astype(float)

    # Your brand row
    your_row = comp_df[comp_df['Brand Name'] == brand_name].iloc[0]
    your_rate = your_row['Mention Rate']

    # Competitor rows
    competitors = comp_df[comp_df['Brand Name'] != brand_name].copy()

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Your Position", "#1" if your_rate == comp_df['Mention Rate'].max() else f"#{(comp_df['Mention Rate'] > your_rate).sum() + 1}")

    with col2:
        leader = comp_df.loc[comp_df['Mention Rate'].idxmax(), 'Brand Name']
        leader_rate = comp_df['Mention Rate'].max()
        st.metric("Market Leader", leader, f"{leader_rate:.1f}%")

    with col3:
        avg_competitor = competitors['Mention Rate'].mean()
        st.metric("Competitor Average", f"{avg_competitor:.1f}%")

    with col4:
        gap_to_leader = leader_rate - your_rate if leader != brand_name else 0
        st.metric("Gap to Leader", f"{gap_to_leader:.1f}%", delta=f"-{gap_to_leader:.1f}%", delta_color="inverse")

    st.markdown("---")

    # Competitive Positioning Chart
    st.subheader("📊 Competitive Positioning")

    fig = go.Figure()

    # Add bars for each brand
    colors = [DEEP_PLUM if row['Brand Name'] == brand_name else
             RED if row['Status'] == 'Top Competitor' else
             ACCENT_PINK if 'Rising' in row['Status'] else
             DUSTY_ROSE
             for _, row in comp_df.iterrows()]

    fig.add_trace(go.Bar(
        x=comp_df['Brand Name'],
        y=comp_df['Mention Rate'],
        marker_color=colors,
        text=comp_df['Mention Rate %'],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' +
                     'Mention Rate: %{y:.1f}%<br>' +
                     '<extra></extra>'
    ))

    # Add average line
    fig.add_hline(y=avg_competitor, line_dash="dash", line_color=DUSTY_ROSE,
                 annotation_text=f"Competitor Avg: {avg_competitor:.1f}%",
                 annotation_position="right")

    fig.update_layout(
        title="Brand Visibility Comparison",
        xaxis_title="Brand",
        yaxis_title="Mention Rate (%)",
        height=500,
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color=CHARCOAL)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Detailed competitor breakdown
    st.subheader("🔍 Detailed Competitor Breakdown")

    # Show competitor cards
    for _, row in competitors.iterrows():
        with st.expander(f"**{row['Brand Name']}** - {row['Status']}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Mention Rate", f"{row['Mention Rate']:.1f}%")

            with col2:
                st.metric("Total Mentions", row['Total Mentions'])

            with col3:
                gap = row['Gap']
                if gap > 0:
                    st.metric("Lead vs You", f"+{gap:.1f}%", delta=f"+{gap:.1f}%", delta_color="inverse")
                else:
                    st.metric("Behind You", f"{gap:.1f}%", delta=f"{gap:.1f}%", delta_color="normal")

            # Gap visualization
            fig = go.Figure()

            # Create horizontal bar showing comparison
            fig.add_trace(go.Bar(
                y=['Your Brand', row['Brand Name']],
                x=[your_rate, row['Mention Rate']],
                orientation='h',
                marker_color=[DEEP_PLUM, RED if gap > 0 else GREEN],
                text=[f"{your_rate:.1f}%", f"{row['Mention Rate']:.1f}%"],
                textposition='outside'
            ))

            fig.update_layout(
                height=150,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False,
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False),
                plot_bgcolor='white',
                paper_bgcolor='white'
            ))

            st.plotly_chart(fig, use_container_width=True)

            # Strategic insights
            if gap > 5:
                st.warning(f"⚠️ **Significant gap:** {row['Brand Name']} is ahead by {gap:.1f} percentage points. Priority competitor to address.")
            elif gap > 0:
                st.info(f"ℹ️ **Small gap:** Close competition. Focus on differentiation to overtake.")
            else:
                st.success(f"✅ **Leading:** You're ahead by {-gap:.1f} percentage points. Maintain advantage.")

    st.markdown("---")

    # Market share visualization
    st.subheader("🥧 Market Share (AI Visibility)")

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=comp_df['Brand Name'],
        values=comp_df['Total Mentions'],
        marker=dict(
            colors=[DEEP_PLUM if name == brand_name else DUSTY_ROSE
                   for name in comp_df['Brand Name']]
        ),
        textinfo='label+percent',
        hole=0.4
    ))

    fig.update_layout(
        title="Share of AI Mentions",
        height=400,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Competitive matrix
    st.subheader("📈 Competitive Performance Matrix")

    # Calculate mention count vs rate
    fig = go.Figure()

    for _, row in comp_df.iterrows():
        is_your_brand = row['Brand Name'] == brand_name

        fig.add_trace(go.Scatter(
            x=[row['Total Mentions']],
            y=[row['Mention Rate']],
            mode='markers+text',
            name=row['Brand Name'],
            marker=dict(
                size=20,
                color=DEEP_PLUM if is_your_brand else DUSTY_ROSE,
                line=dict(width=2, color=ACCENT_PINK if is_your_brand else 'white')
            ),
            text=row['Brand Name'],
            textposition='top center',
            showlegend=False
        ))

    # Add quadrant lines
    avg_mentions = comp_df['Total Mentions'].mean()
    avg_rate = comp_df['Mention Rate'].mean()

    fig.add_hline(y=avg_rate, line_dash="dash", line_color=DUSTY_ROSE)
    fig.add_vline(x=avg_mentions, line_dash="dash", line_color=DUSTY_ROSE)

    # Add quadrant labels
    max_mentions = comp_df['Total Mentions'].max()
    max_rate = comp_df['Mention Rate'].max()

    fig.add_annotation(x=avg_mentions + (max_mentions - avg_mentions)/2, y=avg_rate + (max_rate - avg_rate)/2,
                      text="Leaders", showarrow=False, font=dict(color=GREEN, size=12))
    fig.add_annotation(x=avg_mentions/2, y=avg_rate + (max_rate - avg_rate)/2,
                      text="Niche Players", showarrow=False, font=dict(color=CHARCOAL, size=10))
    fig.add_annotation(x=avg_mentions + (max_mentions - avg_mentions)/2, y=avg_rate/2,
                      text="Volume Players", showarrow=False, font=dict(color=CHARCOAL, size=10))
    fig.add_annotation(x=avg_mentions/2, y=avg_rate/2,
                      text="Challengers", showarrow=False, font=dict(color=RED, size=10))

    fig.update_layout(
        title="Brand Positioning: Frequency vs Visibility",
        xaxis_title="Total Mentions (Volume)",
        yaxis_title="Mention Rate (% Visibility)",
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption("""
    **Leaders** = High visibility & high volume (top right)
    **Niche Players** = High visibility, lower volume (top left)
    **Volume Players** = High volume, lower visibility (bottom right)
    **Challengers** = Building presence (bottom left)
    """)

    # Download section
    st.markdown("---")
    st.subheader("📥 Export Competitor Data")

    csv = comp_df.to_csv(index=False)
    brand_slug = brand_name.replace(' ', '_')

    st.download_button(
        "📊 Download Competitor Comparison (CSV)",
        data=csv,
        file_name=f"competitors_{brand_slug}.csv",
        mime="text/csv"
    )
