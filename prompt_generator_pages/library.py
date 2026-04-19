"""
Prompt Library Manager - View and manage prompt batches
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, 'src')

from src.prompt_generator.batch_manager import BatchManager, load_prompts_with_batches

# Brand colors - LIGHT THEME
BACKGROUND = '#FFFFFF'
TEXT_COLOR = '#000000'
LIGHT_BG = '#F5F5F5'
BORDER = '#CCCCCC'
ACCENT = '#4A4458'


def render():
    """Render the prompt library manager page."""

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

    st.title("📚 Prompt Library")

    st.markdown(f"""
    <div style='background-color: {LIGHT_BG}; padding: 16px; border-radius: 6px; margin-bottom: 20px;'>
        <p style='color: {TEXT_COLOR}; margin: 0;'>
            <strong>Your complete prompt collection.</strong> Browse all active prompts, archive ones you don't want to test anymore,
            or manage batches from expired campaigns.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Show active client banner
    if 'active_client' in st.session_state and st.session_state.active_client:
        client_name = st.session_state.generation_config.get('client_name', 'Unknown Client')
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {LIGHT_BG} 0%, #5a5468 100%);
                    padding: 16px 24px;
                    border-radius: 8px;
                    border-left: 4px solid {ACCENT};
                    margin-bottom: 24px;'>
            <p style='color: white; margin: 0; font-size: 1.1em;'>
                <strong>🌟 Active Client:</strong> {client_name}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No client selected. Go to **Client Manager** to select a client first.")
        return

    # Initialize batch manager
    batch_manager = BatchManager()
    client_name = st.session_state.generation_config.get('client_name', 'Unknown Client')

    # Get batches
    active_batches = batch_manager.get_active_batches(client_name)
    archived_batches = batch_manager.get_archived_batches(client_name)

    # Load all prompts from main CSV
    import csv
    main_csv_path = Path('data/generated_prompts.csv')
    all_active_prompts = []
    if main_csv_path.exists():
        with open(main_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only include prompts for this client
                if row.get('client_name', '') == client_name:
                    all_active_prompts.append(row)

    # Load archived prompts
    archived_csv_path = Path('data/archived_prompts.csv')
    all_archived_prompts = []
    if archived_csv_path.exists():
        with open(archived_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('client_name', '') == client_name:
                    all_archived_prompts.append(row)

    # Summary metrics
    st.markdown("### 📊 Library Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Prompts", len(all_active_prompts))

    with col2:
        st.metric("Archived Prompts", len(all_archived_prompts))

    with col3:
        st.metric("Active Batches", len(active_batches))

    with col4:
        st.metric("Archived Batches", len(archived_batches))

    st.markdown("---")

    # Tabs for different management views
    tab1, tab2 = st.tabs(["📝 Individual Prompts", "📦 Batch Management"])

    with tab1:
        render_prompt_management(all_active_prompts, all_archived_prompts, client_name, main_csv_path, archived_csv_path)

    with tab2:
        render_batch_management(batch_manager, client_name, active_batches, archived_batches)


def render_prompt_management(all_active_prompts, all_archived_prompts, client_name, main_csv_path, archived_csv_path):
    """Render individual prompt management interface."""
    import csv

    st.markdown("## 🔍 Browse & Manage Individual Prompts")
    st.markdown("View, search, and archive specific prompts from your library.")

    # Active Prompts Section
    st.markdown("### ✅ Active Prompts")
    st.markdown(f"These prompts are available for testing in the AI Visibility Dashboard.")

    if not all_active_prompts:
        st.info("No active prompts yet. Go to **Generate** and **Export** to add prompts to your library!")
    else:
        # Filters
        with st.expander("🔍 Filter Prompts", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                # Batch filter
                all_batches = sorted(set(p.get('batch_name', 'Unknown') for p in all_active_prompts))
                selected_batches = st.multiselect(
                    "Batch",
                    all_batches,
                    default=all_batches,
                    help="Filter by batch"
                )

            with col2:
                # Persona filter
                all_personas = sorted(set(p.get('persona', 'Unknown') for p in all_active_prompts))
                selected_personas = st.multiselect(
                    "Persona",
                    all_personas,
                    default=all_personas,
                    help="Filter by persona"
                )

            with col3:
                # Category filter
                all_categories = sorted(set(p.get('category', 'Unknown') for p in all_active_prompts))
                selected_categories = st.multiselect(
                    "Category",
                    all_categories,
                    default=all_categories,
                    help="Filter by category"
                )

            # Text search
            search_text = st.text_input(
                "🔎 Search prompt text",
                placeholder="Search for keywords in prompt text...",
                help="Search within prompt text"
            )

        # Apply filters
        filtered_prompts = all_active_prompts
        if selected_batches:
            filtered_prompts = [p for p in filtered_prompts if p.get('batch_name', 'Unknown') in selected_batches]
        if selected_personas:
            filtered_prompts = [p for p in filtered_prompts if p.get('persona', 'Unknown') in selected_personas]
        if selected_categories:
            filtered_prompts = [p for p in filtered_prompts if p.get('category', 'Unknown') in selected_categories]
        if search_text:
            filtered_prompts = [p for p in filtered_prompts if search_text.lower() in p.get('prompt_text', '').lower()]

        st.info(f"📊 Showing {len(filtered_prompts)} of {len(all_active_prompts)} active prompts")

        # Display prompts table
        if filtered_prompts:
            df = pd.DataFrame(filtered_prompts)
            display_columns = ['prompt_id', 'batch_name', 'persona', 'category', 'intent_type', 'prompt_text', 'expected_visibility_score']
            available_columns = [col for col in display_columns if col in df.columns]

            st.dataframe(
                df[available_columns],
                use_container_width=True,
                height=400
            )

            # Archive actions
            st.markdown("---")
            st.markdown("### 🗄️ Archive Prompts")
            st.markdown("Remove prompts you don't want to test anymore. They'll be moved to archived prompts (can be restored later).")

            archive_mode = st.radio(
                "What to archive?",
                ["Archive by Prompt ID", "Archive All Filtered Prompts"],
                help="Choose how to select prompts for archiving"
            )

            if archive_mode == "Archive by Prompt ID":
                prompt_ids_input = st.text_area(
                    "Prompt IDs to Archive (one per line)",
                    placeholder="sayido_001\nsayido_002\nsayido_003",
                    help="Enter prompt IDs, one per line"
                )

                if st.button("🗄️ Archive Selected Prompts", type="primary"):
                    if not prompt_ids_input.strip():
                        st.warning("Please enter at least one prompt ID")
                    else:
                        ids_to_archive = [id.strip() for id in prompt_ids_input.split('\n') if id.strip()]
                        archive_prompts_by_ids(ids_to_archive, client_name, main_csv_path, archived_csv_path)
                        # Sync to GCS
                        try:
                            from src.client_manager.gcs_sync import GCSClientSync
                            GCSClientSync().upload_prompt_data()
                        except Exception:
                            pass
                        st.success(f"✅ Archived {len(ids_to_archive)} prompts!")
                        st.rerun()

            else:  # Archive All Filtered
                st.warning(f"⚠️ This will archive **{len(filtered_prompts)} prompts** currently shown in the table above.")

                archive_reason = st.text_input(
                    "Reason for archiving (optional)",
                    placeholder="e.g., Campaign ended, Poor performance",
                    key="archive_reason_bulk"
                )

                if st.button(f"🗄️ Archive {len(filtered_prompts)} Filtered Prompts", type="primary"):
                    if len(filtered_prompts) == 0:
                        st.warning("No prompts to archive")
                    else:
                        ids_to_archive = [p['prompt_id'] for p in filtered_prompts]
                        archive_prompts_by_ids(ids_to_archive, client_name, main_csv_path, archived_csv_path, reason=archive_reason)
                        # Sync to GCS
                        try:
                            from src.client_manager.gcs_sync import GCSClientSync
                            GCSClientSync().upload_prompt_data()
                        except Exception:
                            pass
                        st.success(f"✅ Archived {len(filtered_prompts)} prompts!")
                        st.rerun()

    st.markdown("---")

    # Archived Prompts Section
    st.markdown("### 📦 Archived Prompts")
    st.markdown("Previously archived prompts. These are not used in testing but can be restored if needed.")

    if not all_archived_prompts:
        st.info("No archived prompts.")
    else:
        st.info(f"📊 {len(all_archived_prompts)} archived prompts")

        df_archived = pd.DataFrame(all_archived_prompts)
        display_columns = ['prompt_id', 'batch_name', 'persona', 'category', 'prompt_text', 'archive_date', 'archive_reason']
        available_columns = [col for col in display_columns if col in df_archived.columns]

        st.dataframe(
            df_archived[available_columns],
            use_container_width=True,
            height=300
        )

        # Restore actions
        st.markdown("---")
        st.markdown("### 🔄 Restore Prompts")

        restore_ids_input = st.text_area(
            "Prompt IDs to Restore (one per line)",
            placeholder="sayido_001\nsayido_002",
            help="Enter prompt IDs to restore, one per line",
            key="restore_ids"
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Restore Prompts", type="primary"):
                if not restore_ids_input.strip():
                    st.warning("Please enter at least one prompt ID")
                else:
                    ids_to_restore = [id.strip() for id in restore_ids_input.split('\n') if id.strip()]
                    restore_prompts_by_ids(ids_to_restore, client_name, main_csv_path, archived_csv_path)
                    # Sync to GCS
                    try:
                        from src.client_manager.gcs_sync import GCSClientSync
                        GCSClientSync().upload_prompt_data()
                    except Exception:
                        pass
                    st.success(f"✅ Restored {len(ids_to_restore)} prompts!")
                    st.rerun()

        # Permanent-delete button is intentionally hidden. Archived prompts are kept
        # indefinitely as a historical reference. If a permanent purge is ever needed,
        # it should be a scripted, reviewed operation — not a one-click UI action.


def archive_prompts_by_ids(prompt_ids, client_name, main_csv_path, archived_csv_path, reason=""):
    """Archive specific prompts by their IDs."""
    import csv
    from datetime import datetime

    # Read all prompts from main CSV
    all_prompts = []
    with open(main_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        all_prompts = list(reader)
        fieldnames = reader.fieldnames

    # Separate prompts to archive vs keep
    to_archive = []
    to_keep = []

    for prompt in all_prompts:
        if prompt['prompt_id'] in prompt_ids and prompt.get('client_name', '') == client_name:
            # Add archive metadata
            prompt['archive_date'] = datetime.now().isoformat()
            prompt['archive_reason'] = reason
            to_archive.append(prompt)
        else:
            to_keep.append(prompt)

    # Write remaining prompts back to main CSV
    with open(main_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(to_keep)

    # Append archived prompts to archived CSV
    archived_csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Add archive fields to fieldnames if needed
    archive_fieldnames = list(fieldnames) if fieldnames else []
    if 'archive_date' not in archive_fieldnames:
        archive_fieldnames.append('archive_date')
    if 'archive_reason' not in archive_fieldnames:
        archive_fieldnames.append('archive_reason')

    file_exists = archived_csv_path.exists()
    with open(archived_csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=archive_fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(to_archive)


def restore_prompts_by_ids(prompt_ids, client_name, main_csv_path, archived_csv_path):
    """Restore prompts from archived back to active."""
    import csv

    if not archived_csv_path.exists():
        return

    # Read archived prompts
    archived_prompts = []
    with open(archived_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        archived_prompts = list(reader)
        fieldnames = reader.fieldnames

    # Separate prompts to restore vs keep archived
    to_restore = []
    to_keep_archived = []

    for prompt in archived_prompts:
        if prompt['prompt_id'] in prompt_ids and prompt.get('client_name', '') == client_name:
            # Remove archive metadata
            if 'archive_date' in prompt:
                del prompt['archive_date']
            if 'archive_reason' in prompt:
                del prompt['archive_reason']
            to_restore.append(prompt)
        else:
            to_keep_archived.append(prompt)

    # Write remaining archived prompts back
    with open(archived_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(to_keep_archived)

    # Read main CSV
    main_prompts = []
    main_fieldnames = []
    if main_csv_path.exists():
        with open(main_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            main_prompts = list(reader)
            main_fieldnames = list(reader.fieldnames)

    # Append restored prompts to main CSV
    with open(main_csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=main_fieldnames)
        if not main_prompts:  # File was empty, write header
            writer.writeheader()
        writer.writerows(to_restore)


def render_batch_management(batch_manager, client_name, active_batches, archived_batches):
    """Render batch management interface (original functionality)."""
    st.markdown("## 📦 Manage Batches")
    st.markdown("Archive or restore entire batches of prompts from campaigns or projects.")

    total_active_prompts = sum(b.get('prompt_count', 0) for b in active_batches)
    total_archived_prompts = sum(b.get('prompt_count', 0) for b in archived_batches)

    # Active Batches Section
    st.markdown("## ✅ Active Batches")

    if not active_batches:
        st.info("No active batches yet. Go to **Generate** to create your first batch!")
    else:
        for batch in active_batches:
            batch_id = batch['batch_id']
            batch_name = batch['batch_name']
            prompt_count = batch.get('prompt_count', 0)
            date_added = batch.get('date_added', '')
            notes = batch.get('notes', '')

            # Format date
            try:
                date_obj = datetime.fromisoformat(date_added)
                formatted_date = date_obj.strftime('%b %d, %Y')
            except:
                formatted_date = 'Unknown date'

            # Determine if this is the baseline batch
            is_baseline = 'baseline' in batch_name.lower() or 'initial' in batch_name.lower()

            # Batch card
            border_color = ACCENT if is_baseline else "rgba(232, 215, 160, 0.3)"
            bg_color = f"linear-gradient(135deg, {LIGHT_BG} 0%, #5a5468 100%)" if is_baseline else LIGHT_BG

            st.markdown(f"""
            <div style='background: {bg_color};
                        padding: 20px;
                        border-radius: 8px;
                        border: 2px solid {border_color};
                        margin-bottom: 16px;'>
                <h3 style='color: white; margin: 0 0 12px 0;'>
                    {'🌟 ' if is_baseline else '📦 '}{batch_name}
                </h3>
                <div style='margin-bottom: 12px;'>
                    <p style='color: {ACCENT}; margin: 4px 0; font-size: 0.9em;'>
                        <strong>Added:</strong> {formatted_date} | <strong>Prompts:</strong> {prompt_count}
                    </p>
                    {f"<p style='color: {TEXT_COLOR}; margin: 8px 0 0 0; font-size: 0.85em;'><em>{notes}</em></p>" if notes else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

            with col1:
                if st.button("📋 View Prompts", key=f"view_{batch_id}"):
                    st.session_state[f'show_prompts_{batch_id}'] = not st.session_state.get(f'show_prompts_{batch_id}', False)

            with col2:
                # Export button is hidden until batch-level export is implemented.
                # Full prompt export is available from the main prompts CSV on disk.
                pass

            with col3:
                if not is_baseline:  # Don't allow archiving baseline
                    if st.button("📥 Archive", key=f"archive_{batch_id}"):
                        st.session_state[f'confirm_archive_{batch_id}'] = True

            # Show prompts if expanded
            if st.session_state.get(f'show_prompts_{batch_id}', False):
                with st.expander(f"Prompts in {batch_name}", expanded=True):
                    # Load prompts for this batch
                    prompts_file = Path('data/generated_prompts.csv')
                    if prompts_file.exists():
                        df = load_prompts_with_batches(str(prompts_file))
                        batch_prompts = df[df['batch_id'] == batch_id]

                        if len(batch_prompts) > 0:
                            st.dataframe(
                                batch_prompts[['prompt_text', 'persona', 'category', 'intent_type', 'expected_visibility_score']],
                                use_container_width=True
                            )
                        else:
                            st.info("No prompts found for this batch in the main CSV yet. They may still be in review.")
                    else:
                        st.info("No prompts CSV found yet.")

            # Confirm archive dialog
            if st.session_state.get(f'confirm_archive_{batch_id}', False):
                st.warning(f"⚠️ Are you sure you want to archive **{batch_name}**?")

                archive_reason = st.text_input(
                    "Reason for archiving (optional)",
                    placeholder="e.g., Campaign ended, Low performance",
                    key=f"archive_reason_{batch_id}"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Yes, Archive", key=f"confirm_yes_{batch_id}", type="primary"):
                        batch_manager.archive_batch(batch_id, reason=archive_reason)
                        st.success(f"✅ Archived {batch_name}")
                        del st.session_state[f'confirm_archive_{batch_id}']
                        st.rerun()

                with col2:
                    if st.button("✗ Cancel", key=f"confirm_no_{batch_id}"):
                        del st.session_state[f'confirm_archive_{batch_id}']
                        st.rerun()

            st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Archived Batches Section
    st.markdown("## 📦 Archived Batches")

    if not archived_batches:
        st.info("No archived batches.")
    else:
        for batch in archived_batches:
            batch_id = batch['batch_id']
            batch_name = batch['batch_name']
            prompt_count = batch.get('prompt_count', 0)
            date_added = batch.get('date_added', '')
            date_archived = batch.get('date_archived', '')
            archive_reason = batch.get('archive_reason', '')
            notes = batch.get('notes', '')

            # Format dates
            try:
                date_obj = datetime.fromisoformat(date_added)
                formatted_date = date_obj.strftime('%b %d, %Y')
            except:
                formatted_date = 'Unknown date'

            try:
                archived_obj = datetime.fromisoformat(date_archived)
                formatted_archived = archived_obj.strftime('%b %d, %Y')
            except:
                formatted_archived = 'Unknown date'

            # Archived batch card (muted styling)
            st.markdown(f"""
            <div style='background-color: rgba(74, 68, 88, 0.3);
                        padding: 20px;
                        border-radius: 8px;
                        border: 1px dashed rgba(232, 215, 160, 0.5);
                        margin-bottom: 16px;'>
                <h3 style='color: rgba(255,255,255,0.7); margin: 0 0 12px 0;'>
                    📦 {batch_name} <span style='font-size: 0.7em;'>(Archived)</span>
                </h3>
                <div style='margin-bottom: 12px;'>
                    <p style='color: rgba(232, 215, 160, 0.7); margin: 4px 0; font-size: 0.9em;'>
                        <strong>Added:</strong> {formatted_date} | <strong>Archived:</strong> {formatted_archived}<br>
                        <strong>Prompts:</strong> {prompt_count}
                    </p>
                    {f"<p style='color: rgba(251, 251, 239, 0.6); margin: 8px 0 0 0; font-size: 0.85em;'><em>Reason: {archive_reason}</em></p>" if archive_reason else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("🔄 Restore", key=f"restore_{batch_id}"):
                    batch_manager.restore_batch(batch_id)
                    st.success(f"✅ Restored {batch_name}")
                    st.rerun()

            with col2:
                if st.button("🗑️ Delete Forever", key=f"delete_{batch_id}"):
                    st.session_state[f'confirm_delete_{batch_id}'] = True

            # Confirm delete dialog
            if st.session_state.get(f'confirm_delete_{batch_id}', False):
                st.error(f"⚠️ **WARNING:** Permanently delete **{batch_name}**? This cannot be undone!")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Yes, Delete Forever", key=f"delete_yes_{batch_id}", type="primary"):
                        batch_manager.delete_batch(batch_id)
                        st.success(f"✅ Permanently deleted {batch_name}")
                        del st.session_state[f'confirm_delete_{batch_id}']
                        st.rerun()

                with col2:
                    if st.button("✗ Cancel", key=f"delete_no_{batch_id}"):
                        del st.session_state[f'confirm_delete_{batch_id}']
                        st.rerun()

            st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)
