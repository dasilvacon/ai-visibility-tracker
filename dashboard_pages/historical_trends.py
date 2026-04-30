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

        Historical tracking starts automatically when you run a test from the **Run Report** page.

        Run tests monthly to build up your trend data!
        """)
        return

    # ============================================================
    # WHAT CHANGED THIS WEEK
    # ============================================================
    # Lead component — turns the dashboard from "static snapshot" into
    # "what's new this week." Only renders if we have at least 2 weekly
    # snapshots in the data (otherwise there's no week-over-week to show).
    wow = tracker.get_week_over_week_delta(client_name)

    if wow:
        st.markdown("## 🔔 What Changed This Week")
        st.caption(
            f"Comparing **{wow['current_week']}** to **{wow['previous_week']}**. "
            "Green = improvement, red = drop, gray = unchanged."
        )

        # Three big delta cards at the top
        m = wow['metrics']
        col1, col2, col3 = st.columns(3)

        with col1:
            d = m['visibility_rate']
            st.metric(
                "Visibility Rate",
                f"{d['current']:.1f}%",
                f"{d['delta']:+.1f}% pts",
                delta_color="normal",
            )
            st.caption(f"Was {d['previous']:.1f}% last week")

        with col2:
            d = m['prominence_rate']
            st.metric(
                "Prominence Score",
                f"{d['current']:.1f}/10",
                f"{d['delta']:+.1f}",
                delta_color="normal",
            )
            st.caption(f"Was {d['previous']:.1f}/10 last week")

        with col3:
            d = m['share_of_voice']
            st.metric(
                "Share of Voice",
                f"{d['current']:.1f}%",
                f"{d['delta']:+.1f}% pts",
                delta_color="normal",
            )
            st.caption(f"Was {d['previous']:.1f}% last week")

        # Notable changes — surface non-metric signals worth flagging
        notable = []
        if wow['new_competitors']:
            notable.append(
                f"🆕 **New competitors detected:** {', '.join(wow['new_competitors'])}"
            )
        if wow['lost_competitors']:
            notable.append(
                f"⏬ **Stopped appearing alongside:** {', '.join(wow['lost_competitors'])}"
            )

        # Platform shifts (only call out platforms with notable swings)
        platform_swings = []
        for plat, d in (wow.get('platforms_changed') or {}).items():
            delta = d['visibility_delta']
            if abs(delta) >= 2:  # ≥2 percentage points
                arrow = "↑" if delta > 0 else "↓"
                platform_swings.append(
                    f"{arrow} **{plat}**: {d['visibility_previous']:.1f}% → {d['visibility_current']:.1f}% "
                    f"({delta:+.1f} pts)"
                )
        if platform_swings:
            notable.append("📡 **Platform shifts:** " + " · ".join(platform_swings))

        if notable:
            for line in notable:
                st.markdown(line)
        else:
            st.caption("No new competitors or significant platform shifts this week.")

        st.markdown("---")

    # ============================================================
    # MONTHLY COMPARISON (existing)
    # ============================================================
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

    # Helper for the three monthly charts below. Centralizes:
    #   - the "only 1 month" callout (so a single dot doesn't look broken)
    #   - the categorical x-axis (prevents Plotly auto-parsing "2026-04" as
    #     datetime and zooming to millisecond precision around one point)
    def _render_monthly_chart(trend_data, *, y_title, y_range=None, reverse_y=False, value_fmt):
        if not trend_data:
            return

        if len(trend_data) == 1:
            d = trend_data[0]
            st.info(
                f"📅 Only **{d['month']}** has data so far — "
                f"value is **{value_fmt(d['value'])}**. "
                "Trend chart will populate as additional monthly runs accumulate."
            )
            return

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[d['month'] for d in trend_data],
            y=[d['value'] for d in trend_data],
            mode='lines+markers',
            line=dict(color=DARK_PURPLE, width=3),
            marker=dict(size=10),
        ))

        layout = dict(
            xaxis_title="Month",
            yaxis_title=y_title,
            xaxis=dict(type='category'),  # force discrete labels, no datetime parsing
            height=400,
            hovermode='x unified',
        )
        if y_range is not None:
            layout['yaxis_range'] = y_range
        if reverse_y:
            layout['yaxis_autorange'] = 'reversed'

        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

    with tab1:
        st.markdown("### Visibility Rate Over Time")
        st.caption("% of prompts where your brand is mentioned")

        trend_data = tracker.get_trend_data(client_name, 'visibility_rate')

        _render_monthly_chart(
            trend_data,
            y_title="Visibility Rate (%)",
            y_range=[0, 100],
            value_fmt=lambda v: f"{v}%",
        )

        if trend_data:
            with st.expander("📊 View Data Table"):
                for d in reversed(trend_data):
                    st.write(f"**{d['month']}:** {d['value']}%")

    with tab2:
        st.markdown("### Prominence Rate Over Time")
        st.caption("Average position in AI responses (1st, 2nd, 3rd, etc.) - Lower is better!")

        trend_data = tracker.get_trend_data(client_name, 'prominence_rate')

        _render_monthly_chart(
            trend_data,
            y_title="Average Position",
            reverse_y=True,
            value_fmt=lambda v: f"#{int(v)}" if v else "N/A",
        )

        if trend_data:
            with st.expander("📊 View Data Table"):
                for d in reversed(trend_data):
                    st.write(f"**{d['month']}:** Position #{int(d['value'])}")

    with tab3:
        st.markdown("### Share of Voice Over Time")
        st.caption("Your brand mentions vs. competitor mentions")

        trend_data = tracker.get_trend_data(client_name, 'share_of_voice')

        # Data-integrity guard: a long-standing bug in historical_tracker meant
        # competitor_mentions silently defaulted to 0, so SOV was stored as
        # exactly 100% whenever the brand had any mentions. Detect and flag
        # those bad rows so we don't display them as "correct trend."
        suspicious_months = []
        for month_key, snap in history.items():
            # Only consider monthly keys (YYYY-MM), not weekly (YYYY-WNN)
            if not (len(month_key) == 7 and month_key[4] == '-'):
                continue
            sov = snap.get('metrics', {}).get('share_of_voice')
            comp_mentions = snap.get('detailed_stats', {}).get('competitor_mentions', 0)
            if sov == 100 and comp_mentions == 0:
                suspicious_months.append(month_key)

        if suspicious_months:
            st.warning(
                "⚠️ **Heads up — historical SOV bug:** "
                f"{len(suspicious_months)} stored snapshot(s) "
                f"({', '.join(sorted(suspicious_months))}) were calculated with a "
                "broken formula that always produced 100%. They've been excluded "
                "from the chart below. The fix is deployed — next weekly run will "
                "populate a correct value, and you can delete the bad entries "
                "from the **All Test Runs** section below."
            )
            trend_data = [d for d in trend_data if d['month'] not in suspicious_months]

        _render_monthly_chart(
            trend_data,
            y_title="Share of Voice (%)",
            y_range=[0, 100],
            value_fmt=lambda v: f"{v}%",
        )

        if trend_data:
            with st.expander("📊 View Data Table"):
                for d in reversed(trend_data):
                    st.write(f"**{d['month']}:** {d['value']}%")

    st.markdown("---")

    # ============================================================
    # WEEKLY TREND + PER-PLATFORM BREAKDOWN
    # ============================================================
    weekly_snapshots = tracker.get_weekly_snapshots(client_name)
    if len(weekly_snapshots) >= 2:
        st.markdown("## 📅 Weekly Visibility Trend")
        st.caption(
            "Week-over-week visibility for the last "
            f"{len(weekly_snapshots)} weeks of data we have. "
            "More granular than the monthly chart above — "
            "shows what's moving inside the month."
        )

        # Composite chart: visibility rate per week with platform overlays
        fig = go.Figure()

        weeks = [s['week'] for s in weekly_snapshots]
        overall_visibility = [s['metrics']['visibility_rate'] for s in weekly_snapshots]

        fig.add_trace(go.Scatter(
            x=weeks,
            y=overall_visibility,
            mode='lines+markers',
            name='Overall',
            line=dict(color=DARK_PURPLE, width=4),
            marker=dict(size=12),
        ))

        # Find every platform that appears in any week's snapshot
        all_platforms = set()
        for s in weekly_snapshots:
            for p in (s.get('by_platform') or {}):
                all_platforms.add(p)

        # Distinct colors per platform — readable on light bg
        platform_palette = [
            '#10b981', '#3b82f6', '#f59e0b',
            '#ef4444', '#8b5cf6', '#06b6d4',
        ]
        for i, plat in enumerate(sorted(all_platforms)):
            # For weeks where this platform is missing, plot as None so the
            # line breaks instead of dropping to zero (visually misleading)
            ys = [
                (s.get('by_platform') or {}).get(plat, {}).get('visibility')
                for s in weekly_snapshots
            ]
            fig.add_trace(go.Scatter(
                x=weeks,
                y=ys,
                mode='lines+markers',
                name=plat.replace('_', ' ').title(),
                line=dict(color=platform_palette[i % len(platform_palette)], width=2, dash='dot'),
                marker=dict(size=7),
                connectgaps=False,
            ))

        fig.update_layout(
            xaxis_title="ISO Week",
            yaxis_title="Visibility Rate (%)",
            yaxis_range=[0, max(100, max(overall_visibility) + 10) if overall_visibility else 100],
            height=440,
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        )

        st.plotly_chart(fig, use_container_width=True)

        # Data table for the curious
        with st.expander("📊 View Weekly Data Table"):
            import pandas as pd
            rows = []
            for s in weekly_snapshots:
                row = {
                    'Week': s['week'],
                    'Visibility %': s['metrics']['visibility_rate'],
                    'Prominence': s['metrics']['prominence_rate'],
                    'SOV %': s['metrics']['share_of_voice'],
                    'Total Prompts': s.get('total_prompts', 0),
                }
                for p in sorted(all_platforms):
                    pdata = (s.get('by_platform') or {}).get(p, {})
                    row[f"{p} %"] = pdata.get('visibility', '—')
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

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
