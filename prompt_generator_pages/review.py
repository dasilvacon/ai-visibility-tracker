"""
Review & Approval page for prompt generator app.
"""

import streamlit as st
import pandas as pd
import sys

sys.path.insert(0, 'src')


def render():
    """Render the review & approval page."""
    st.title("🔍 Review & Approve Prompts")

    if not st.session_state.generated_prompts:
        st.warning("No prompts generated yet. Go to **Generate** to create prompts first.")
        return

    # Get approval manager
    approval_mgr = st.session_state.approval_manager

    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filters")

        # Get all unique values for filters
        all_prompts = approval_mgr.get_all_prompts()
        personas = sorted(set(p['persona'] for p in all_prompts))
        categories = sorted(set(p['category'] for p in all_prompts))
        intent_types = sorted(set(p['intent_type'] for p in all_prompts))

        # Persona filter
        selected_personas = st.multiselect(
            "Persona",
            personas,
            default=personas,
            help="Filter by target persona"
        )

        # Category filter
        selected_categories = st.multiselect(
            "Category",
            categories,
            default=categories,
            help="Filter by content category"
        )

        # Intent type filter
        selected_intents = st.multiselect(
            "Intent Type",
            intent_types,
            default=intent_types,
            help="Filter by search intent"
        )

        # Competitor mention filter
        has_competitor = st.checkbox(
            "Only with competitors",
            value=False,
            help="Show only prompts with competitor mentions"
        )

        # Score range filter
        score_range = st.slider(
            "Expected Score Range",
            min_value=1.0,
            max_value=10.0,
            value=(1.0, 10.0),
            step=0.5,
            help="Filter by expected visibility score"
        )

        # Text search
        search_text = st.text_input(
            "Search Prompt Text",
            "",
            help="Search within prompt text"
        )

        # Approval status filter
        status_filter = st.radio(
            "Approval Status",
            ["All", "Pending", "Approved", "Rejected"],
            index=0
        )

        # Clear filters button
        if st.button("Clear All Filters"):
            st.rerun()

    # Apply filters
    if status_filter == "All":
        filtered_prompts = all_prompts
    else:
        filtered_prompts = approval_mgr.get_prompts_by_status(status_filter.lower())

    # Apply persona filter
    filtered_prompts = [p for p in filtered_prompts if p['persona'] in selected_personas]

    # Apply category filter
    filtered_prompts = [p for p in filtered_prompts if p['category'] in selected_categories]

    # Apply intent filter
    filtered_prompts = [p for p in filtered_prompts if p['intent_type'] in selected_intents]

    # Apply competitor filter
    if has_competitor:
        filtered_prompts = [p for p in filtered_prompts if 'vs' in p.get('notes', '')]

    # Apply score range filter
    filtered_prompts = [p for p in filtered_prompts
                       if score_range[0] <= p['expected_visibility_score'] <= score_range[1]]

    # Apply text search
    if search_text:
        filtered_prompts = [p for p in filtered_prompts
                          if search_text.lower() in p['prompt_text'].lower()]

    # Stats dashboard
    stats = approval_mgr.get_approval_stats()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Prompts", stats['total'])

    with col2:
        st.metric("Approved", stats['approved'], delta=f"{stats['approval_rate']:.1f}%")

    with col3:
        st.metric("Rejected", stats['rejected'], delta=f"{stats['rejection_rate']:.1f}%")

    with col4:
        st.metric("Pending", stats['pending'])

    st.markdown("---")

    # Bulk actions bar
    st.markdown(f"### Filtered Results ({len(filtered_prompts)} prompts)")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("✓ Approve All Visible", use_container_width=True):
            approval_mgr.bulk_approve_filtered(filtered_prompts)
            st.success(f"Approved {len(filtered_prompts)} prompts!")
            st.rerun()

    with col2:
        if st.button("✗ Reject All Visible", use_container_width=True):
            approval_mgr.bulk_reject_filtered(filtered_prompts)
            st.success(f"Rejected {len(filtered_prompts)} prompts!")
            st.rerun()

    with col3:
        if st.button("↺ Reset All Visible", use_container_width=True):
            prompt_ids = [p['prompt_id'] for p in filtered_prompts]
            approval_mgr.reset_prompts(prompt_ids)
            st.success(f"Reset {len(filtered_prompts)} prompts to pending!")
            st.rerun()

    with col4:
        approve_selected_button = st.empty()

    with col5:
        reject_selected_button = st.empty()

    # Pagination settings
    page_size = 50
    total_pages = (len(filtered_prompts) + page_size - 1) // page_size

    if total_pages > 1:
        page = st.selectbox(
            "Page",
            range(1, total_pages + 1),
            format_func=lambda x: f"Page {x} of {total_pages}"
        )
    else:
        page = 1

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(filtered_prompts))
    page_prompts = filtered_prompts[start_idx:end_idx]

    # Convert to DataFrame for display
    if page_prompts:
        df_data = []
        for prompt in page_prompts:
            df_data.append({
                'ID': prompt['prompt_id'],
                'Persona': prompt['persona'],
                'Category': prompt['category'],
                'Intent': prompt['intent_type'],
                'Prompt Text': prompt['prompt_text'],
                'Score': prompt['expected_visibility_score'],
                'Competitor': '✓' if 'vs' in prompt.get('notes', '') else '',
                'Status': prompt.get('approval_status', 'pending').title()
            })

        df = pd.DataFrame(df_data)

        # Interactive table with selection
        st.markdown(f"Showing {start_idx + 1} - {end_idx} of {len(filtered_prompts)} prompts")

        # Display table with color coding based on status
        def highlight_status(row):
            status = row['Status'].lower()
            if status == 'approved':
                return ['background-color: #d4edda'] * len(row)
            elif status == 'rejected':
                return ['background-color: #f8d7da'] * len(row)
            else:
                return [''] * len(row)

        styled_df = df.style.apply(highlight_status, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=600)

        # Individual prompt actions
        st.markdown("### Individual Prompt Actions")

        selected_id = st.selectbox(
            "Select a prompt to edit",
            df['ID'].tolist(),
            format_func=lambda x: f"{x} - {df[df['ID']==x]['Prompt Text'].values[0][:50]}..."
        )

        if selected_id:
            selected_prompt = next(p for p in page_prompts if p['prompt_id'] == selected_id)

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("#### Edit Prompt")

                new_text = st.text_area(
                    "Prompt Text",
                    value=selected_prompt['prompt_text'],
                    height=100,
                    key=f"edit_{selected_id}"
                )

                new_notes = st.text_input(
                    "Notes",
                    value=selected_prompt.get('notes', ''),
                    key=f"notes_{selected_id}"
                )

                if st.button("💾 Save Changes", key=f"save_{selected_id}"):
                    approval_mgr.edit_prompt(
                        selected_id,
                        {'prompt_text': new_text, 'notes': new_notes}
                    )
                    st.success("Changes saved!")
                    st.rerun()

            with col2:
                st.markdown("#### Actions")
                current_status = selected_prompt.get('approval_status', 'pending')

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    if current_status != 'approved':
                        if st.button("✓ Approve", key=f"approve_{selected_id}", use_container_width=True):
                            approval_mgr.approve_prompts([selected_id])
                            st.success("Approved!")
                            st.rerun()

                with col_b:
                    if current_status != 'rejected':
                        if st.button("✗ Reject", key=f"reject_{selected_id}", use_container_width=True):
                            approval_mgr.reject_prompts([selected_id])
                            st.success("Rejected!")
                            st.rerun()

                with col_c:
                    if current_status != 'pending':
                        if st.button("↺ Reset", key=f"reset_{selected_id}", use_container_width=True):
                            approval_mgr.reset_prompts([selected_id])
                            st.success("Reset to pending!")
                            st.rerun()

                # Show current details
                st.markdown("#### Details")
                st.markdown(f"**Persona:** {selected_prompt['persona']}")
                st.markdown(f"**Category:** {selected_prompt['category']}")
                st.markdown(f"**Intent:** {selected_prompt['intent_type']}")
                st.markdown(f"**Score:** {selected_prompt['expected_visibility_score']}")
                st.markdown(f"**Status:** {current_status.title()}")

    else:
        st.info("No prompts match the current filters.")

    # Navigation hint
    if stats['approved'] > 0:
        st.markdown("---")
        st.info(f"👉 You have {stats['approved']} approved prompts. Go to **Export** to save them.")
