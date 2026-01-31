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

# Brand colors
DARK_PURPLE = '#4A4458'
CREAM = '#E8D7A0'
OFF_WHITE = '#FBFBEF'
DARK_BG = '#1c1c1c'


def render():
    """Render the prompt library manager page."""
    st.title("📚 Prompt Library")

    # Show active client banner
    if 'active_client' in st.session_state and st.session_state.active_client:
        client_name = st.session_state.generation_config.get('client_name', 'Unknown Client')
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {DARK_PURPLE} 0%, #5a5468 100%);
                    padding: 16px 24px;
                    border-radius: 8px;
                    border-left: 4px solid {CREAM};
                    margin-bottom: 24px;'>
            <p style='color: white; margin: 0; font-size: 1.1em;'>
                <strong>🌟 Active Client:</strong> {client_name}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No client selected. Go to **Client Manager** to select a client first.")
        return

    # Help text
    st.markdown(f"""
    <div style='background-color: {DARK_PURPLE}; padding: 16px; border-radius: 6px; margin-bottom: 20px;'>
        <p style='color: {OFF_WHITE}; margin: 0;'>
            View and manage all prompt batches for this client. Archive batches from expired campaigns
            or restore previously archived batches.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize batch manager
    batch_manager = BatchManager()
    client_name = st.session_state.generation_config.get('client_name', 'Unknown Client')

    # Get batches
    active_batches = batch_manager.get_active_batches(client_name)
    archived_batches = batch_manager.get_archived_batches(client_name)

    total_active_prompts = sum(b.get('prompt_count', 0) for b in active_batches)
    total_archived_prompts = sum(b.get('prompt_count', 0) for b in archived_batches)

    # Summary metrics
    st.markdown("### 📊 Library Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Batches", len(active_batches))

    with col2:
        st.metric("Active Prompts", total_active_prompts)

    with col3:
        st.metric("Archived Batches", len(archived_batches))

    with col4:
        st.metric("Archived Prompts", total_archived_prompts)

    st.markdown("---")

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
            border_color = CREAM if is_baseline else "rgba(232, 215, 160, 0.3)"
            bg_color = f"linear-gradient(135deg, {DARK_PURPLE} 0%, #5a5468 100%)" if is_baseline else DARK_PURPLE

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
                    <p style='color: {CREAM}; margin: 4px 0; font-size: 0.9em;'>
                        <strong>Added:</strong> {formatted_date} | <strong>Prompts:</strong> {prompt_count}
                    </p>
                    {f"<p style='color: {OFF_WHITE}; margin: 8px 0 0 0; font-size: 0.85em;'><em>{notes}</em></p>" if notes else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

            with col1:
                if st.button("📋 View Prompts", key=f"view_{batch_id}"):
                    st.session_state[f'show_prompts_{batch_id}'] = not st.session_state.get(f'show_prompts_{batch_id}', False)

            with col2:
                if st.button("📊 Export", key=f"export_{batch_id}"):
                    st.info("Export functionality coming soon!")

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
