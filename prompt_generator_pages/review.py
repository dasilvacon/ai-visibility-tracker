"""
Review & Approval page for prompt generator app.
"""

import streamlit as st
import pandas as pd
import sys
import json
from pathlib import Path

sys.path.insert(0, 'src')


def save_approval_statuses_to_drafts(client_name):
    """Save current approval statuses back to draft files."""
    if 'approval_manager' not in st.session_state:
        return

    approval_mgr = st.session_state.approval_manager
    all_prompts = approval_mgr.get_all_prompts()

    # Group prompts by batch_id
    prompts_by_batch = {}
    for prompt in all_prompts:
        batch_id = prompt.get('batch_id', 'unknown')
        if batch_id not in prompts_by_batch:
            prompts_by_batch[batch_id] = []
        prompts_by_batch[batch_id].append(prompt)

    # Update each draft file
    draft_dir = Path('data/prompt_generation/drafts')
    if not draft_dir.exists():
        return

    for batch_id, prompts in prompts_by_batch.items():
        draft_file = draft_dir / f"batch_{batch_id}_prompts.json"

        if draft_file.exists():
            try:
                # Read existing draft data
                with open(draft_file, 'r') as f:
                    draft_data = json.load(f)

                # Update approval statuses
                draft_data['approval_statuses'] = {
                    p['prompt_id']: p.get('approval_status', 'pending')
                    for p in prompts
                }

                # Write back
                with open(draft_file, 'w') as f:
                    json.dump(draft_data, f, indent=2, default=str)

            except Exception as e:
                st.error(f"Error saving approval statuses to {draft_file.name}: {str(e)}")


def render():
    """Render the review & approval page."""

    # Brand colors - LIGHT THEME
    BACKGROUND = '#FFFFFF'
    TEXT_COLOR = '#000000'
    LIGHT_BG = '#F5F5F5'
    BORDER = '#CCCCCC'
    ACCENT = '#4A4458'

    # Simple light theme CSS
    st.markdown(f"""
    <style>
        .main {{
            background-color: {BACKGROUND};
        }}

        /* All text - black on white */
        h1, h2, h3, h4, h5, h6, p, label, span {{
            color: {TEXT_COLOR} !important;
        }}

        /* Text inputs */
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {{
            background-color: {BACKGROUND} !important;
            color: {TEXT_COLOR} !important;
            border: 1px solid {BORDER} !important;
        }}

        /* Selectbox */
        .stSelectbox select,
        .stSelectbox > div > div {{
            background-color: {BACKGROUND} !important;
            color: {TEXT_COLOR} !important;
            border: 1px solid {BORDER} !important;
        }}

        /* Radio and checkboxes */
        .stRadio label,
        .stCheckbox label {{
            color: {TEXT_COLOR} !important;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab"] {{
            background-color: {BACKGROUND} !important;
            color: {TEXT_COLOR} !important;
            border-bottom: 2px solid {BORDER} !important;
        }}

        .stTabs [aria-selected="true"] {{
            background-color: {LIGHT_BG} !important;
            border-bottom: 2px solid {ACCENT} !important;
            color: {TEXT_COLOR} !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.title("🔍 Review & Approve Prompts")

    # Load prompts from persistent draft files (critical for not losing work!)
    client_name = st.session_state.generation_config.get('client_name', 'Unknown Client')
    draft_dir = Path('data/prompt_generation/drafts')

    # Find all draft files for this client
    all_draft_prompts = []
    draft_files = []

    if draft_dir.exists():
        import json
        for draft_file in draft_dir.glob('batch_*_prompts.json'):
            try:
                with open(draft_file, 'r') as f:
                    draft_data = json.load(f)

                # Only load drafts for the active client
                if draft_data.get('client_name') == client_name:
                    draft_files.append(draft_file)
                    prompts = draft_data.get('prompts', [])
                    approval_statuses = draft_data.get('approval_statuses', {})

                    # Add approval status to each prompt
                    for prompt in prompts:
                        prompt['approval_status'] = approval_statuses.get(prompt['prompt_id'], 'pending')
                        all_draft_prompts.append(prompt)

            except Exception as e:
                st.error(f"Error loading draft file {draft_file.name}: {str(e)}")

    # Load prompts into session state and approval manager if empty
    if not st.session_state.get('generated_prompts') and all_draft_prompts:
        st.session_state.generated_prompts = all_draft_prompts
        if 'approval_manager' in st.session_state:
            # Load with existing approval statuses
            st.session_state.approval_manager.load_prompts(all_draft_prompts, default_status='pending')
        st.info(f"📂 Loaded {len(all_draft_prompts)} prompts from {len(draft_files)} saved batches")

    st.markdown("---")

    # Check if we have prompts to review
    if not st.session_state.get('generated_prompts') and not all_draft_prompts:
        st.warning("⚠️ No prompts found to review.")
        st.info("💡 **What to do:**\n- Go to **Generate** page\n- Generate prompts\n- They'll be automatically saved and you can review them anytime")
        return

    st.success(f"✅ Found {len(st.session_state.generated_prompts)} prompts to review")

    # Get approval manager
    approval_mgr = st.session_state.approval_manager

    # Get all prompts first - with error handling
    try:
        all_prompts = approval_mgr.get_all_prompts()

        if not all_prompts:
            st.error("Approval manager has no prompts. This is unexpected!")
            st.write(f"Debug: generated_prompts count = {len(st.session_state.generated_prompts)}")
            return

    except Exception as e:
        st.error(f"Error getting prompts from approval manager: {str(e)}")
        st.exception(e)
        return

    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filters")

        # Get all unique values for filters - with error handling
        try:
            personas = sorted(set(p['persona'] for p in all_prompts))
            categories = sorted(set(p['category'] for p in all_prompts))
            intent_types = sorted(set(p['intent_type'] for p in all_prompts))
        except Exception as e:
            st.error(f"Error extracting filter values: {str(e)}")
            st.exception(e)
            return

        # Get unique batches - with error handling
        try:
            batches = sorted(set(p.get('batch_name', 'Unknown') for p in all_prompts))

            # Batch filter (NEW)
            if len(batches) > 1:
                selected_batches = st.multiselect(
                    "Batch",
                    batches,
                    default=batches,
                    help="Filter by prompt batch"
                )
            else:
                selected_batches = batches
        except Exception as e:
            st.error(f"Error creating batch filter: {str(e)}")
            selected_batches = ['Unknown']

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

    # Apply filters - with error handling
    try:
        if status_filter == "All":
            filtered_prompts = all_prompts
        else:
            filtered_prompts = approval_mgr.get_prompts_by_status(status_filter.lower())

        # Apply batch filter (NEW)
        filtered_prompts = [p for p in filtered_prompts if p.get('batch_name', 'Unknown') in selected_batches]

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

        st.write(f"🔍 Debug: Filtered {len(filtered_prompts)} prompts from {len(all_prompts)} total")

    except Exception as e:
        st.error(f"❌ Error applying filters: {str(e)}")
        st.exception(e)
        return

    # Stats dashboard - with error handling
    try:
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
    except Exception as e:
        st.error(f"❌ Error displaying stats: {str(e)}")
        st.exception(e)

    st.markdown("---")

    # Client Review Workflow Section
    st.markdown("### 📋 Client Review Workflow")
    st.markdown("If your client wants to approve prompts, export a review file for them to fill out, then import their decisions.")

    col1, col2 = st.columns(2)

    # Export for Client Review
    with col1:
        with st.expander("📤 Export for Client Review", expanded=False):
            st.markdown("""
            **Create an Excel file for your client to review and approve prompts.**

            The file includes an "Approved?" column they can fill with "Yes" or "No".
            """)

            # Choose which prompts to export for review
            review_status_filter = st.radio(
                "Which prompts to include?",
                ["Pending Only", "All Prompts", "Pending + Approved"],
                index=0,  # Default to pending only
                help="Choose which prompts to send to client for review",
                key="client_review_filter"
            )

            # Get prompts based on filter
            if review_status_filter == "All Prompts":
                review_prompts = all_prompts
            elif review_status_filter == "Pending Only":
                review_prompts = approval_mgr.get_prompts_by_status('pending')
            else:  # Pending + Approved
                pending = approval_mgr.get_prompts_by_status('pending')
                approved_for_review = approval_mgr.get_prompts_by_status('approved')
                review_prompts = pending + approved_for_review

            st.info(f"📊 {len(review_prompts)} prompts will be included")

            if len(review_prompts) == 0:
                st.warning("No prompts to export for review.")
            else:
                # Preview
                st.markdown("**Preview (First 5)**")
                preview_df = pd.DataFrame(review_prompts[:5])[['prompt_id', 'persona', 'prompt_text']]
                st.dataframe(preview_df, use_container_width=True, height=200)

                if st.button("📥 Export Client Review File", key="export_client_review_btn", type="primary", use_container_width=True):
                    try:
                        from datetime import datetime
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        client_name = st.session_state.generation_config.get('client_name', 'Unknown Client')

                        # Create DataFrame for Excel export
                        review_data = []
                        for prompt in review_prompts:
                            review_data.append({
                                'Prompt ID': prompt['prompt_id'],
                                'Persona': prompt['persona'],
                                'Category': prompt['category'],
                                'Intent Type': prompt['intent_type'],
                                'Prompt Text': prompt['prompt_text'],
                                'Expected Score': prompt['expected_visibility_score'],
                                'Notes': prompt.get('notes', ''),
                                'Current Status': prompt.get('approval_status', 'pending').title(),
                                'Approved?': ''  # Empty column for client to fill
                            })

                        df = pd.DataFrame(review_data)

                        # Create Excel file with formatting
                        from io import BytesIO
                        output = BytesIO()

                        # Use pandas ExcelWriter with openpyxl engine
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='Prompts for Review')

                            # Get workbook and worksheet
                            workbook = writer.book
                            worksheet = writer.sheets['Prompts for Review']

                            # Freeze header row
                            worksheet.freeze_panes = 'A2'

                            # Set column widths
                            worksheet.column_dimensions['A'].width = 15  # Prompt ID
                            worksheet.column_dimensions['B'].width = 20  # Persona
                            worksheet.column_dimensions['C'].width = 20  # Category
                            worksheet.column_dimensions['D'].width = 15  # Intent Type
                            worksheet.column_dimensions['E'].width = 60  # Prompt Text
                            worksheet.column_dimensions['F'].width = 12  # Expected Score
                            worksheet.column_dimensions['G'].width = 30  # Notes
                            worksheet.column_dimensions['H'].width = 15  # Current Status
                            worksheet.column_dimensions['I'].width = 15  # Approved?

                            # Add instructions in a note
                            from openpyxl.comments import Comment
                            worksheet['I1'].comment = Comment(
                                'Fill this column with "Yes" or "No" to approve or reject each prompt',
                                'Instructions'
                            )

                        excel_data = output.getvalue()

                        # Provide download button
                        st.download_button(
                            label="💾 Download Excel File",
                            data=excel_data,
                            file_name=f"client_review_{client_name.replace(' ', '_')}_{timestamp}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_client_review"
                        )

                        st.success(f"✅ Client review file ready!")
                        st.info("📧 Send this file to your client. After they fill it out, use 'Import Client Approvals' to upload their decisions.")

                    except Exception as e:
                        st.error(f"❌ Error creating client review file: {str(e)}")
                        st.exception(e)

    # Import Client Approvals
    with col2:
        with st.expander("📥 Import Client Approvals", expanded=False):
            st.markdown("""
            **Upload the Excel file that your client filled out with their approval decisions.**

            The file should have:
            - A "Prompt ID" column (to match prompts)
            - An "Approved?" column with "Yes" or "No" values
            """)

            uploaded_file = st.file_uploader(
                "Choose client review file",
                type=['xlsx', 'xls', 'csv'],
                help="Upload the Excel or CSV file with client approvals"
            )

            if uploaded_file is not None:
                try:
                    # Read file based on type
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)

                    # Validate required columns
                    if 'Prompt ID' not in df.columns or 'Approved?' not in df.columns:
                        st.error("❌ File must contain 'Prompt ID' and 'Approved?' columns")
                    else:
                        st.success(f"✅ File loaded: {len(df)} prompts found")

                        # Preview
                        st.markdown("**Preview**")
                        st.dataframe(df.head(10), use_container_width=True, height=200)

                        # Process approvals
                        if st.button("🚀 Import Approvals", key="import_approvals_btn", type="primary", use_container_width=True):
                            approved_ids = []
                            rejected_ids = []
                            skipped_count = 0

                            for _, row in df.iterrows():
                                prompt_id = str(row['Prompt ID']).strip()
                                approval_value = str(row['Approved?']).strip().lower()

                                # Check if prompt exists
                                prompt_exists = any(p['prompt_id'] == prompt_id for p in all_prompts)

                                if not prompt_exists:
                                    skipped_count += 1
                                    continue

                                # Process approval decision
                                if approval_value in ['yes', 'y', 'approve', 'approved', 'true', '1']:
                                    approved_ids.append(prompt_id)
                                elif approval_value in ['no', 'n', 'reject', 'rejected', 'false', '0']:
                                    rejected_ids.append(prompt_id)
                                # If empty or anything else, leave as is (pending)

                            # Apply approvals
                            if approved_ids:
                                approval_mgr.approve_prompts(approved_ids)
                            if rejected_ids:
                                approval_mgr.reject_prompts(rejected_ids)

                            # Save approval statuses to draft files
                            save_approval_statuses_to_drafts(client_name)

                            # Show summary
                            st.success("✅ Client approvals imported successfully!")

                            subcol1, subcol2, subcol3 = st.columns(3)
                            with subcol1:
                                st.metric("Approved", len(approved_ids))
                            with subcol2:
                                st.metric("Rejected", len(rejected_ids))
                            with subcol3:
                                st.metric("Skipped", skipped_count)

                            st.info("🔄 Refreshing page...")
                            st.rerun()

                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
                    st.exception(e)

    st.markdown("---")

    # Bulk actions bar
    st.markdown(f"### Filtered Results ({len(filtered_prompts)} prompts)")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("✓ Approve All Visible", use_container_width=True):
            approval_mgr.bulk_approve_filtered(filtered_prompts)
            save_approval_statuses_to_drafts(client_name)
            st.success(f"Approved {len(filtered_prompts)} prompts!")
            st.rerun()

    with col2:
        if st.button("✗ Reject All Visible", use_container_width=True):
            approval_mgr.bulk_reject_filtered(filtered_prompts)
            save_approval_statuses_to_drafts(client_name)
            st.success(f"Rejected {len(filtered_prompts)} prompts!")
            st.rerun()

    with col3:
        if st.button("↺ Reset All Visible", use_container_width=True):
            prompt_ids = [p['prompt_id'] for p in filtered_prompts]
            approval_mgr.reset_prompts(prompt_ids)
            save_approval_statuses_to_drafts(client_name)
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
        try:
            df_data = []
            for prompt in page_prompts:
                df_data.append({
                    'ID': prompt['prompt_id'],
                    'Batch': prompt.get('batch_name', 'Unknown'),
                    'Persona': prompt['persona'],
                    'Category': prompt['category'],
                    'Intent': prompt['intent_type'],
                    'Prompt Text': prompt['prompt_text'],
                    'Score': prompt['expected_visibility_score'],
                    'Competitor': '✓' if 'vs' in prompt.get('notes', '') else '',
                    'Status': prompt.get('approval_status', 'pending').title()
                })

            df = pd.DataFrame(df_data)
        except Exception as e:
            st.error(f"❌ Error creating dataframe: {str(e)}")
            st.exception(e)
            st.write("First prompt sample:")
            st.json(page_prompts[0])
            return

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
                            save_approval_statuses_to_drafts(client_name)
                            st.success("Approved!")
                            st.rerun()

                with col_b:
                    if current_status != 'rejected':
                        if st.button("✗ Reject", key=f"reject_{selected_id}", use_container_width=True):
                            approval_mgr.reject_prompts([selected_id])
                            save_approval_statuses_to_drafts(client_name)
                            st.success("Rejected!")
                            st.rerun()

                with col_c:
                    if current_status != 'pending':
                        if st.button("↺ Reset", key=f"reset_{selected_id}", use_container_width=True):
                            approval_mgr.reset_prompts([selected_id])
                            save_approval_statuses_to_drafts(client_name)
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
