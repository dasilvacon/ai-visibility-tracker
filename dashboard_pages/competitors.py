"""Competitor Analysis page."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from pathlib import Path
from collections import Counter

# Brand colors
DEEP_PLUM = '#402E3A'
DUSTY_ROSE = '#A78E8B'
ACCENT_PINK = '#D4698B'
CHARCOAL = '#1C1C1C'
RED = '#E74C3C'
GREEN = '#27AE60'
BLUE = '#3498DB'  # For untracked brands


def extract_all_mentioned_brands(raw_data: pd.DataFrame, tracked_competitors: list, brand_name: str) -> pd.DataFrame:
    """
    Extract all brands/organizations mentioned in AI responses.

    Args:
        raw_data: DataFrame with 'Competitors Mentioned' column
        tracked_competitors: List of competitor names you're tracking
        brand_name: Your brand name

    Returns:
        DataFrame with all mentioned brands and their stats
    """
    if raw_data is None or 'Competitors Mentioned' not in raw_data.columns:
        return pd.DataFrame()

    all_mentions = Counter()
    total_responses = len(raw_data)

    # Parse all competitors mentioned across all responses
    for _, row in raw_data.iterrows():
        competitors_str = row.get('Competitors Mentioned', '')
        if pd.isna(competitors_str) or not competitors_str:
            continue

        # Split by comma and clean up
        competitors = [c.strip() for c in str(competitors_str).split(',') if c.strip()]
        for comp in competitors:
            all_mentions[comp] += 1

    # Build list of all brands with tracking status
    brand_name_lower = brand_name.lower()
    tracked_lower = {t.lower(): t for t in tracked_competitors}

    brands_data = []
    for brand, count in all_mentions.items():
        brand_lower = brand.lower()

        # Skip your own brand
        if brand_lower == brand_name_lower:
            continue

        # Determine if this is a tracked competitor
        is_tracked = brand_lower in tracked_lower

        mention_rate = (count / total_responses * 100) if total_responses > 0 else 0

        brands_data.append({
            'Brand Name': brand,
            'Mentions': count,
            'Mention Rate': mention_rate,
            'Is Tracked': is_tracked,
            'Status': 'Tracked Competitor' if is_tracked else 'Discovered'
        })

    # Sort by mentions descending
    brands_df = pd.DataFrame(brands_data)
    if not brands_df.empty:
        brands_df = brands_df.sort_values('Mentions', ascending=False).reset_index(drop=True)

    return brands_df


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

    # Full Competitive Landscape Section - ALL mentioned brands
    st.subheader("🌐 Full Competitive Landscape")

    st.info("""
    **All brands/organizations appearing in AI responses** — See who's showing up when users ask questions
    about your industry. Tracked competitors are highlighted with a ⭐ tag.
    """)

    # Get list of tracked competitors from the competitor CSV
    tracked_competitors = comp_df[comp_df['Brand Name'] != brand_name]['Brand Name'].tolist()

    # Extract all mentioned brands from raw data
    all_brands_df = extract_all_mentioned_brands(data.get('raw_data'), tracked_competitors, brand_name)

    if not all_brands_df.empty:
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 All Brands", "⭐ Tracked Only", "🔍 Untracked Only"])

        with tab1:
            # Bar chart showing ALL mentioned brands
            st.markdown("### All Brands Mentioned in AI Responses")

            # Color code: tracked = deep plum, untracked = blue
            colors = [DEEP_PLUM if row['Is Tracked'] else BLUE for _, row in all_brands_df.head(20).iterrows()]

            fig_all = go.Figure()
            fig_all.add_trace(go.Bar(
                x=all_brands_df.head(20)['Brand Name'],
                y=all_brands_df.head(20)['Mention Rate'],
                marker_color=colors,
                text=[f"{r:.1f}%" for r in all_brands_df.head(20)['Mention Rate']],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>' +
                             'Mentions: ' + all_brands_df.head(20)['Mentions'].astype(str) + '<br>' +
                             'Rate: %{y:.1f}%<br>' +
                             '<extra></extra>'
            ))

            fig_all.update_layout(
                title="Top 20 Brands by AI Mention Rate",
                xaxis_title="Brand",
                yaxis_title="Mention Rate (%)",
                height=500,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(color=CHARCOAL),
                xaxis_tickangle=-45
            )

            st.plotly_chart(fig_all, use_container_width=True)

            # Legend
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<span style='color:{DEEP_PLUM}'>■</span> **Tracked Competitors**", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<span style='color:{BLUE}'>■</span> **Other Brands (Not Tracked)**", unsafe_allow_html=True)

            # Full data table
            st.markdown("### Complete List")

            # Add visual tags to names
            display_df = all_brands_df.copy()
            display_df['Brand'] = display_df.apply(
                lambda row: f"⭐ {row['Brand Name']}" if row['Is Tracked'] else row['Brand Name'],
                axis=1
            )
            display_df['Mention Rate %'] = display_df['Mention Rate'].apply(lambda x: f"{x:.1f}%")

            st.dataframe(
                display_df[['Brand', 'Mentions', 'Mention Rate %', 'Status']],
                use_container_width=True,
                hide_index=True
            )

        with tab2:
            # Only tracked competitors
            tracked_df = all_brands_df[all_brands_df['Is Tracked'] == True]

            if not tracked_df.empty:
                st.markdown("### Your Tracked Competitors Performance")

                fig_tracked = go.Figure()
                fig_tracked.add_trace(go.Bar(
                    x=tracked_df['Brand Name'],
                    y=tracked_df['Mention Rate'],
                    marker_color=DEEP_PLUM,
                    text=[f"{r:.1f}%" for r in tracked_df['Mention Rate']],
                    textposition='outside'
                ))

                fig_tracked.update_layout(
                    title="Tracked Competitors by AI Mention Rate",
                    xaxis_title="Competitor",
                    yaxis_title="Mention Rate (%)",
                    height=400,
                    showlegend=False,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    xaxis_tickangle=-45
                )

                st.plotly_chart(fig_tracked, use_container_width=True)

                # Table
                display_tracked = tracked_df.copy()
                display_tracked['Mention Rate %'] = display_tracked['Mention Rate'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(
                    display_tracked[['Brand Name', 'Mentions', 'Mention Rate %']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("None of your tracked competitors appeared in the AI responses.")

        with tab3:
            # Untracked brands only
            untracked_df = all_brands_df[all_brands_df['Is Tracked'] == False]

            if not untracked_df.empty:
                st.markdown("### Brands You're NOT Tracking (But AI Mentions)")

                st.warning(f"""
                **{len(untracked_df)} brands** are appearing in AI responses but you're not tracking them.
                Consider adding high-frequency ones to your competitor list!
                """)

                fig_untracked = go.Figure()
                fig_untracked.add_trace(go.Bar(
                    x=untracked_df.head(15)['Brand Name'],
                    y=untracked_df.head(15)['Mention Rate'],
                    marker_color=BLUE,
                    text=[f"{r:.1f}%" for r in untracked_df.head(15)['Mention Rate']],
                    textposition='outside'
                ))

                fig_untracked.update_layout(
                    title="Top 15 Untracked Brands in AI Responses",
                    xaxis_title="Brand",
                    yaxis_title="Mention Rate (%)",
                    height=400,
                    showlegend=False,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    xaxis_tickangle=-45
                )

                st.plotly_chart(fig_untracked, use_container_width=True)

                # Table with action buttons
                st.markdown("### Should You Track These?")
                for idx, row in untracked_df.head(10).iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        priority = "🔴 High" if row['Mentions'] >= 5 else "🟡 Medium" if row['Mentions'] >= 3 else "🟢 Low"
                        st.markdown(f"""
                        **{row['Brand Name']}** — {row['Mentions']} mentions ({row['Mention Rate']:.1f}%)
                        Priority: {priority}
                        """)

                    with col2:
                        if st.button("➕ Track", key=f"track_new_{idx}_{row['Brand Name']}"):
                            st.info(f"To track {row['Brand Name']}, add it to your brand_config.json competitors list")

                    with col3:
                        if st.button("✖ Ignore", key=f"ignore_{idx}_{row['Brand Name']}"):
                            st.info("Marked as not a competitor")

                    st.markdown("---")
            else:
                st.success("All brands appearing in AI responses are already being tracked!")

    else:
        st.info("Run a report to see all brands mentioned in AI responses.")

    st.markdown("---")

    # Discovered Competitors Section (from brand_config - legacy)
    st.subheader("📡 Saved Competitor Discoveries")

    st.caption("""
    Previously discovered competitors that were saved to your brand configuration.
    Use the "Full Competitive Landscape" section above for the most current view.
    """)

    # Construct brand_config_path from brand_name
    client_slug = brand_name.replace(' ', '_').lower()
    brand_config_path = f'data/{client_slug}/{client_slug}_brand_config.json'

    # Load brand_config to get discovered competitors
    discovered_shown = False
    brand_config_data = None

    # Try local file first
    if os.path.exists(brand_config_path):
        try:
            with open(brand_config_path, 'r') as f:
                brand_config_data = json.load(f)
        except Exception:
            pass

    # Try GCS if local not found
    if brand_config_data is None:
        try:
            from src.storage.gcs_manager import GCSManager
            gcs = GCSManager()
            content = gcs.get_report_content(brand_name, f"{client_slug}_brand_config.json")
            brand_config_data = json.loads(content.decode('utf-8'))
        except Exception:
            pass

    if brand_config_data:
        discovered = brand_config_data.get('competitors', {}).get('discovered', [])

        if discovered:
            # Filter out promoted competitors
            active_discovered = [d for d in discovered if not d.get('promoted_to_expected', False)]

            if active_discovered:
                discovered_shown = True

                # Sort by mention count (highest first)
                active_discovered.sort(key=lambda x: x.get('mention_count', 0), reverse=True)

                st.markdown("### Brands Appearing in AI Responses")

                # Display each discovered competitor with action buttons
                for idx, disc in enumerate(active_discovered):
                    status = disc.get('status', 'occasional_mention')
                    status_emoji = "🔴" if status == "emerging_threat" else "🟡"
                    mention_count = disc.get('mention_count', 0)
                    mention_rate = disc.get('mention_rate', 0)

                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"""
                        **{status_emoji} {disc['name']}**
                        - Mentions: {mention_count} ({mention_rate:.1f}%)
                        - First seen: {disc.get('first_seen', 'Unknown')}
                        - Status: {status.replace('_', ' ').title()}
                        """)

                    with col2:
                        # Add to tracked button
                        if st.button("➕ Track", key=f"track_{idx}_{disc['name']}", help="Add to your tracked competitors"):
                            try:
                                from src.data.brand_config_manager import BrandConfigManager
                                manager = BrandConfigManager()

                                # Reload config
                                config = manager.load_config(brand_config_path)

                                # Promote to expected (default to 'direct' category)
                                config = manager.promote_discovered_competitor(
                                    config,
                                    disc['name'],
                                    category='direct',
                                    notes=f"Auto-promoted from dashboard. {mention_count} mentions detected."
                                )

                                # Save config
                                manager.save_config(brand_config_path, config)

                                st.success(f"✓ Added {disc['name']} to tracked competitors!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

                    with col3:
                        # Dismiss button
                        if st.button("✖ Dismiss", key=f"dismiss_{idx}_{disc['name']}", help="Not a real competitor"):
                            try:
                                from src.data.brand_config_manager import BrandConfigManager
                                manager = BrandConfigManager()

                                # Reload config
                                config = manager.load_config(brand_config_path)

                                # Dismiss
                                config = manager.dismiss_discovered_competitor(config, disc['name'])

                                # Save config
                                manager.save_config(brand_config_path, config)

                                st.success(f"✓ Dismissed {disc['name']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")

                    st.markdown("---")

                # Summary
                emerging_threats = [d for d in active_discovered if d.get('status') == 'emerging_threat']
                if emerging_threats:
                    st.warning(f"""
                    ⚠️ **{len(emerging_threats)} Emerging Threat(s) Detected!**

                    These brands were mentioned 5+ times. Consider adding them to your tracked competitors
                    by clicking the **➕ Track** button.
                    """)

    if not discovered_shown:
        st.success("✅ No new competitors discovered. All mentioned brands are already on your tracking list.")

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
