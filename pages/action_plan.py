"""Action Plan page with task management."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Brand colors
DEEP_PLUM = '#402E3A'
DUSTY_ROSE = '#A78E8B'
RED = '#E74C3C'
ORANGE = '#F39C12'
GREEN = '#27AE60'


def show(brand_name: str, data: dict):
    """Display action plan page."""

    st.title("✅ Action Plan")

    st.markdown("""
    Your prioritized content and audience opportunities based on visibility gaps.
    Use this as a task checklist for your content team.
    """)

    if data.get('action_plan') is None:
        st.warning("No action plan data available.")
        return

    action_df = data['action_plan'].copy()

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        high_priority = len(action_df[action_df['Priority'] == 'HIGH'])
        st.metric("High Priority", high_priority, help="Tasks requiring immediate attention")

    with col2:
        medium_priority = len(action_df[action_df['Priority'] == 'MEDIUM'])
        st.metric("Medium Priority", medium_priority, help="Important but not urgent")

    with col3:
        low_priority = len(action_df[action_df['Priority'] == 'LOW'])
        st.metric("Low Priority", low_priority, help="Nice-to-have improvements")

    with col4:
        total_impact = action_df['Estimated Monthly Impact'].str.extract(r'(\d+)').astype(float).sum()[0]
        st.metric("Total Potential Impact", f"~{int(total_impact)} mentions/mo")

    st.markdown("---")

    # Filter section
    st.subheader("🔍 Filter Tasks")

    col1, col2, col3 = st.columns(3)

    with col1:
        priority_filter = st.multiselect(
            "Priority:",
            ["HIGH", "MEDIUM", "LOW"],
            default=["HIGH", "MEDIUM", "LOW"]
        )

    with col2:
        category_filter = st.multiselect(
            "Category:",
            action_df['Category'].unique().tolist(),
            default=action_df['Category'].unique().tolist()
        )

    with col3:
        sort_by = st.selectbox(
            "Sort by:",
            ["Priority", "Estimated Impact", "Gap", "Opportunity Name"]
        )

    # Apply filters
    filtered_df = action_df[
        (action_df['Priority'].isin(priority_filter)) &
        (action_df['Category'].isin(category_filter))
    ].copy()

    # Apply sorting
    if sort_by == "Priority":
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        filtered_df['_sort_key'] = filtered_df['Priority'].map(priority_order)
        filtered_df = filtered_df.sort_values('_sort_key').drop('_sort_key', axis=1)
    elif sort_by == "Estimated Impact":
        filtered_df['_sort_key'] = filtered_df['Estimated Monthly Impact'].str.extract(r'(\d+)').astype(float)
        filtered_df = filtered_df.sort_values('_sort_key', ascending=False).drop('_sort_key', axis=1)
    elif sort_by == "Gap":
        filtered_df['_sort_key'] = filtered_df['Gap'].str.rstrip('%').astype(float)
        filtered_df = filtered_df.sort_values('_sort_key', ascending=False).drop('_sort_key', axis=1)
    else:
        filtered_df = filtered_df.sort_values('Opportunity Name')

    st.markdown("---")

    # Display tasks
    if filtered_df.empty:
        st.info("No tasks match the selected filters.")
    else:
        st.subheader(f"📋 {len(filtered_df)} Tasks")

        # Task cards
        for idx, row in filtered_df.iterrows():
            # Priority color and emoji
            if row['Priority'] == 'HIGH':
                color = RED
                emoji = "🔴"
            elif row['Priority'] == 'MEDIUM':
                color = ORANGE
                emoji = "🟡"
            else:
                color = GREEN
                emoji = "🟢"

            with st.container():
                # Header with priority
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### {emoji} {row['Opportunity Name'].title()}")
                    st.caption(f"{row['Category']} • {row['Priority']} Priority")
                with col2:
                    st.markdown(f"<div style='text-align: right; color: {color}; font-size: 24px; font-weight: bold;'>{row['Priority']}</div>", unsafe_allow_html=True)

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Your Visibility", row['Current Visibility %'])
                with col2:
                    st.metric("Competitor Avg", row['Competitor Avg %'])
                with col3:
                    st.metric("Potential Impact", row['Estimated Monthly Impact'])

                # Gap visualization
                your_vis = float(row['Current Visibility %'].rstrip('%'))
                comp_avg = float(row['Competitor Avg %'].rstrip('%'))

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=[your_vis, comp_avg],
                    y=['You', 'Competitors'],
                    orientation='h',
                    marker_color=[DEEP_PLUM, DUSTY_ROSE],
                    text=[f"{your_vis:.1f}%", f"{comp_avg:.1f}%"],
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
                )
                st.plotly_chart(fig, use_container_width=True)

                # Specific actions
                st.markdown("**🎯 Specific Actions:**")
                actions = row['Specific Actions'].split(' | ')
                for i, action in enumerate(actions, 1):
                    # Clean up action text
                    action_text = action.split('. ', 1)[-1] if '. ' in action else action
                    st.checkbox(action_text, key=f"action_{idx}_{i}", value=False)

                # Where to implement
                st.markdown(f"**📍 Where to Implement:** {row['Where to Implement']}")

                # Target keywords
                if row['Target Keywords']:
                    st.markdown(f"**🔑 Target Keywords:** `{row['Target Keywords']}`")

                # Example questions
                if row['Example Questions']:
                    with st.expander("📝 Example Questions from Test Data"):
                        examples = row['Example Questions'].split(' | ')
                        for ex in examples[:3]:
                            st.markdown(f"- {ex}")

                # Task management fields
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.selectbox("Status", ["TODO", "In Progress", "Done"], key=f"status_{idx}")
                with col2:
                    st.text_input("Assigned To", key=f"assigned_{idx}", placeholder="Enter name")
                with col3:
                    st.date_input("Due Date", key=f"due_{idx}", value=None)

                st.markdown("---")

        # Visualization: Priority distribution
        st.subheader("📊 Priority Distribution")

        priority_counts = filtered_df['Priority'].value_counts()

        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=priority_counts.index,
            values=priority_counts.values,
            marker=dict(colors=[RED, ORANGE, GREEN]),
            hole=0.4
        ))
        fig.update_layout(
            title="Tasks by Priority",
            height=300,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    # Download section
    st.markdown("---")
    st.subheader("📥 Export Action Plan")

    col1, col2 = st.columns(2)

    brand_slug = brand_name.replace(' ', '_')

    with col1:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            "📊 Download as CSV",
            data=csv,
            file_name=f"action_plan_{brand_slug}_filtered.csv",
            mime="text/csv"
        )

    with col2:
        # Create simple task list format
        task_list = "# Action Plan Task List\n\n"
        for idx, row in filtered_df.iterrows():
            task_list += f"## {row['Priority']} - {row['Opportunity Name'].title()}\n\n"
            task_list += f"**Category:** {row['Category']}\n"
            task_list += f"**Impact:** {row['Estimated Monthly Impact']}\n\n"
            task_list += "**Actions:**\n"
            actions = row['Specific Actions'].split(' | ')
            for action in actions:
                task_list += f"- [ ] {action}\n"
            task_list += "\n---\n\n"

        st.download_button(
            "📝 Download as Markdown",
            data=task_list,
            file_name=f"action_plan_{brand_slug}.md",
            mime="text/markdown"
        )
