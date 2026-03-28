"""
Historical Trends Page - Shows monthly visibility metrics over time.

Displays three key metrics:
1. Visibility Rate - % of prompts where brand is mentioned
2. Prominence Rate - Average citation position
3. Share of Voice - Brand vs. competitor mentions
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from tracking.historical_tracker import HistoricalTracker


def render():
    """Render the historical trends page."""

    # Light theme colors
    LIGHT_BG = '#FFFFFF'
    TEXT_DARK = '#1c1c1c'
    DARK_PURPLE = '#4A4458'
    BORDER_LIGHT = '#E0E0E0'

    st.title("📈 Historical Trends")

    st.markdown(f"""
    <div style='background-color: #F5F5F5; padding: 20px; border-radius: 8px; border-left: 4px solid {DARK_PURPLE}; margin-bottom: 24px;'>
        <h3 style='color: {TEXT_DARK}; margin-top: 0;'>📊 Track Your AI Visibility Over Time</h3>
        <p style='color: {TEXT_DARK}; margin-bottom: 12px;'>
            See how your brand's visibility in AI responses changes month-over-month. Track three key metrics:
        </p>
        <ul style='color: {TEXT_DARK};'>
            <li><strong>Visibility Rate</strong> - % of prompts where your brand appears</li>
            <li><strong>Prominence Rate</strong> - Average position in AI responses (lower is better)</li>
            <li><strong>Share of Voice</strong> - Your mentions vs. competitor mentions</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Get active client from session state
    client_name = st.session_state.get('brand_name')

    if not client_name:
        st.warning("⚠️ No client selected. Please select a client from the Dashboard page.")
        return

    # Initialize historical tracker with per-client isolation
    client_slug = client_name.replace(' ', '_').lower()
    tracker = HistoricalTracker(client_slug=client_slug)

    # Get historical data
    history = tracker.get_client_history(client_name)

    if not history:
        st.info(f"""
        📅 **No historical data yet for {client_name}**

        Historical tracking starts automatically when you run tests via CLI:
        ```bash
        python main.py --client "{client_name}" --prompts your_prompts.csv
        ```

        Run tests monthly to build up your trend data!
        """)
        return

    # Show summary stats
    st.markdown("## 📊 Latest vs. Previous Month")

    comparison = tracker.get_latest_vs_previous(client_name)

    if comparison:
        col1, col2, col3 = st.columns(3)

        with col1:
            latest_vis = comparison['latest_metrics']['visibility_rate']
            change_vis = comparison['changes']['visibility_rate']
            trend_vis = "🟢" if change_vis > 0 else "🔴" if change_vis < 0 else "⚪"

            st.metric(
                "Visibility Rate",
                f"{latest_vis}%",
                f"{change_vis:+.1f}%",
                delta_color="normal"
            )
            st.caption(f"{trend_vis} vs. {comparison['previous_month']}")

        with col2:
            latest_prom = comparison['latest_metrics']['prominence_rate']
            change_prom = comparison['changes']['prominence_rate']
            # Lower is better for prominence
            trend_prom = "🟢" if change_prom < 0 else "🔴" if change_prom > 0 else "⚪"

            st.metric(
                "Prominence Rate",
                f"#{int(latest_prom)}" if latest_prom else "N/A",
                f"{change_prom:+.1f}",
                delta_color="inverse"  # Lower is better
            )
            st.caption(f"{trend_prom} Position (lower is better)")

        with col3:
            latest_sov = comparison['latest_metrics']['share_of_voice']
            change_sov = comparison['changes']['share_of_voice']
            trend_sov = "🟢" if change_sov > 0 else "🔴" if change_sov < 0 else "⚪"

            st.metric(
                "Share of Voice",
                f"{latest_sov}%",
                f"{change_sov:+.1f}%",
                delta_color="normal"
            )
            st.caption(f"{trend_sov} vs. competitors")

        # Overall trend
        trend = comparison['trend']
        if trend == 'improving':
            st.success(f"🎉 **Overall Trend: Improving!** Your visibility is getting better.")
        elif trend == 'stable':
            st.info(f"📊 **Overall Trend: Stable** - Minor changes month-over-month.")
        else:
            st.warning(f"⚠️ **Overall Trend: Declining** - Consider reviewing your content strategy.")

    st.markdown("---")

    # Trend Charts
    st.markdown("## 📈 Historical Trends")

    # Create tabs for each metric
    tab1, tab2, tab3 = st.tabs(["Visibility Rate", "Prominence Rate", "Share of Voice"])

    with tab1:
        st.markdown("### Visibility Rate Over Time")
        st.caption("% of prompts where your brand is mentioned")

        trend_data = tracker.get_trend_data(client_name, 'visibility_rate')

        if trend_data:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[d['month'] for d in trend_data],
                y=[d['value'] for d in trend_data],
                mode='lines+markers',
                name='Visibility Rate',
                line=dict(color=DARK_PURPLE, width=3),
                marker=dict(size=10)
            ))

            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Visibility Rate (%)",
                yaxis_range=[0, 100],
                height=400,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Show data table
            with st.expander("📊 View Data Table"):
                for d in reversed(trend_data):
                    st.write(f"**{d['month']}:** {d['value']}%")

    with tab2:
        st.markdown("### Prominence Rate Over Time")
        st.caption("Average position in AI responses (1st, 2nd, 3rd, etc.) - Lower is better!")

        trend_data = tracker.get_trend_data(client_name, 'prominence_rate')

        if trend_data:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[d['month'] for d in trend_data],
                y=[d['value'] for d in trend_data],
                mode='lines+markers',
                name='Prominence Rate',
                line=dict(color=DARK_PURPLE, width=3),
                marker=dict(size=10)
            ))

            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Average Position",
                yaxis_autorange='reversed',  # Lower is better
                height=400,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Show data table
            with st.expander("📊 View Data Table"):
                for d in reversed(trend_data):
                    st.write(f"**{d['month']}:** Position #{int(d['value'])}")

    with tab3:
        st.markdown("### Share of Voice Over Time")
        st.caption("Your brand mentions vs. competitor mentions")

        trend_data = tracker.get_trend_data(client_name, 'share_of_voice')

        if trend_data:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[d['month'] for d in trend_data],
                y=[d['value'] for d in trend_data],
                mode='lines+markers',
                name='Share of Voice',
                line=dict(color=DARK_PURPLE, width=3),
                marker=dict(size=10)
            ))

            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Share of Voice (%)",
                yaxis_range=[0, 100],
                height=400,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Show data table
            with st.expander("📊 View Data Table"):
                for d in reversed(trend_data):
                    st.write(f"**{d['month']}:** {d['value']}%")

    st.markdown("---")

    # All Months List
    st.markdown("## 📅 All Test Runs")

    all_months = tracker.get_all_months(client_name)

    if all_months:
        st.caption(f"Total test runs: {len(all_months)}")

        for month in reversed(all_months):
            month_data = history[month]
            metrics = month_data['metrics']

            with st.expander(f"📆 {month} - {datetime.fromisoformat(month_data['test_date']).strftime('%B %d, %Y')}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Visibility Rate", f"{metrics['visibility_rate']}%")

                with col2:
                    prom = metrics['prominence_rate']
                    st.metric("Prominence", f"#{int(prom)}" if prom else "N/A")

                with col3:
                    st.metric("Share of Voice", f"{metrics['share_of_voice']}%")

                st.caption(f"Total prompts tested: {month_data['total_prompts']}")
                st.caption(f"Brand mentions: {month_data['detailed_stats']['brand_mentions']}")
                st.caption(f"Competitor mentions: {month_data['detailed_stats']['competitor_mentions']}")

                # Platform breakdown if available
                if 'by_platform' in month_data:
                    st.markdown("**By Platform:**")
                    for platform, data in month_data['by_platform'].items():
                        st.write(f"- **{platform.title()}:** {data['visibility']}% visibility, #{int(data['prominence'])} prominence, {data['share_of_voice']}% SOV")

                # Delete button
                st.markdown("---")
                if st.button(f"🗑️ Delete This Test Run", key=f"delete_{month}"):
                    if tracker.delete_month(client_name, month):
                        st.success(f"Deleted {month} data.")
                        st.rerun()
                    else:
                        st.error("Could not delete.")
