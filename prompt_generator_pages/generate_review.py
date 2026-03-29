"""
Generate & Review — consolidated prompt generation, review, and export page.
Replaces the old 3-page flow (generate.py, review.py, export_page.py) with one streamlined page.
"""

import streamlit as st
import pandas as pd
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from io import BytesIO

sys.path.insert(0, 'src')

from src.prompt_generator.generator import PromptGenerator
from src.prompt_generator.deduplicator import PromptDeduplicator
from src.prompt_generator.batch_manager import BatchManager, add_batch_metadata_to_prompts
from src.client_manager.client_registry import ClientRegistry


# Brand colors - LIGHT THEME
BACKGROUND = '#FFFFFF'
TEXT_COLOR = '#000000'
LIGHT_BG = '#F5F5F5'
BORDER = '#CCCCCC'
ACCENT = '#4A4458'


def _apply_theme():
    """Apply light theme CSS."""
    st.markdown(f"""
    <style>
        .main {{ background-color: {BACKGROUND}; }}
        h1, h2, h3, h4, h5, h6, p, label, span {{ color: {TEXT_COLOR} !important; }}
        .stTextInput input, .stTextArea textarea, .stNumberInput input {{
            background-color: {BACKGROUND} !important;
            color: {TEXT_COLOR} !important;
            border: 1px solid {BORDER} !important;
        }}
        .stSelectbox select, .stSelectbox > div > div {{
            background-color: {BACKGROUND} !important;
            color: {TEXT_COLOR} !important;
            border: 1px solid {BORDER} !important;
        }}
        .stRadio label, .stCheckbox label {{ color: {TEXT_COLOR} !important; }}
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


def _save_approval_statuses(client_name):
    """Save current approval statuses back to draft files and sync to GCS."""
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
                with open(draft_file, 'r') as f:
                    draft_data = json.load(f)
                draft_data['approval_statuses'] = {
                    p['prompt_id']: p.get('approval_status', 'pending')
                    for p in prompts
                }
                with open(draft_file, 'w') as f:
                    json.dump(draft_data, f, indent=2, default=str)
            except Exception:
                pass

    # Sync to GCS
    try:
        from src.client_manager.gcs_sync import GCSClientSync
        GCSClientSync().upload_prompt_data()
    except Exception:
        pass


def _sync_to_gcs():
    """Sync prompt data to GCS."""
    try:
        from src.client_manager.gcs_sync import GCSClientSync
        gcs_sync = GCSClientSync()
        return gcs_sync.upload_prompt_data()
    except Exception:
        return False


def _load_drafts(client_name):
    """Load prompts from persistent draft files."""
    draft_dir = Path('data/prompt_generation/drafts')
    all_prompts = []
    draft_files = []

    if not draft_dir.exists():
        return all_prompts, draft_files

    for draft_file in draft_dir.glob('batch_*_prompts.json'):
        try:
            with open(draft_file, 'r') as f:
                draft_data = json.load(f)

            if draft_data.get('client_name') == client_name:
                draft_files.append(draft_file)
                prompts = draft_data.get('prompts', [])
                approval_statuses = draft_data.get('approval_statuses', {})

                for prompt in prompts:
                    prompt['approval_status'] = approval_statuses.get(
                        prompt['prompt_id'], 'pending'
                    )
                    all_prompts.append(prompt)
        except Exception:
            pass

    return all_prompts, draft_files


def _render_methodology():
    """Render the methodology section explaining how prompts are generated."""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #4A4458 0%, #5a5468 100%);
                padding: 24px; border-radius: 10px; margin: 20px 0;
                border-left: 4px solid #E8D7A0;'>
        <h3 style='color: #E8D7A0; margin-top: 0;'>🔬 How Our Prompts Are Generated</h3>
        <p style='color: #FBFBEF; line-height: 1.6;'>
            This tool uses a research-backed methodology aligned with the latest in
            <strong>Generative Engine Optimization (GEO)</strong> — the emerging discipline
            of optimizing content for visibility in AI-powered search engines like
            ChatGPT, Perplexity, Google AI Overviews, and Microsoft Copilot.
        </p>

        <h4 style='color: #E8D7A0; margin-top: 20px;'>1. Keyword-to-Prompt Mapping</h4>
        <p style='color: #FBFBEF; line-height: 1.6;'>
            Every prompt starts with a <strong>real keyword from your keyword research</strong>.
            Instead of testing generic phrases, we convert your actual target keywords into
            conversational prompts — because that's how people actually query AI engines.
            The industry standard in 2026 is to map existing keyword research into prompt
            sets, then layer intent and persona context on top.
        </p>
        <p style='color: #d0d0d0; font-size: 0.85em; font-style: italic;'>
            Source: Ahrefs (2026) — "Custom Prompt Tracking: How to Choose the Best Prompts
            to Monitor AI Search Visibility"; The Rank Masters (2026) — "Keyword-to-Prompt Mapping
            for AI Visibility Tools"
        </p>

        <h4 style='color: #E8D7A0; margin-top: 20px;'>2. Persona-Driven Generation</h4>
        <p style='color: #FBFBEF; line-height: 1.6;'>
            Prompts are distributed across your defined audience personas, weighted by
            importance. Each persona's unique triggers, barriers, and priority topics
            shape the prompts — but <strong>persona labels never appear in the prompt text
            itself</strong>. Real people don't say "as an adult child caregiver, find me
            resources." They say "my mom just got out of the hospital, what do I do now?"
            This natural-language approach produces prompts that mirror how your actual
            audience talks to AI.
        </p>
        <p style='color: #d0d0d0; font-size: 0.85em; font-style: italic;'>
            Source: Omniscient Digital (2025) — "How I Created the Perfect Prompt Set for
            AI Visibility Research"; Search Engine Journal (2026) — "GEO Strategies To Make
            AI Search Engines Recommend Your Brand"
        </p>

        <h4 style='color: #E8D7A0; margin-top: 20px;'>3. Intent & Journey Coverage</h4>
        <p style='color: #FBFBEF; line-height: 1.6;'>
            Prompts span multiple intent types — informational ("what is..."),
            commercial ("best options for..."), comparison ("X vs Y"), and navigational
            ("near me"). This ensures coverage across the full buyer journey from
            awareness through decision, because AI engines cite different sources depending
            on the intent behind the query.
        </p>
        <p style='color: #d0d0d0; font-size: 0.85em; font-style: italic;'>
            Source: LLM Clicks (2026) — "AI Visibility Framework: Map User Intent to LLM Prompts";
            Passionfruit (2026) — "GEO Prompts That Unlock AI Search Visibility"
        </p>

        <h4 style='color: #E8D7A0; margin-top: 20px;'>4. Deduplication</h4>
        <p style='color: #FBFBEF; line-height: 1.6;'>
            Semantic deduplication ensures no two prompts test the same thing,
            giving you a clean prompt set that produces reliable, actionable results.
        </p>

        <h4 style='color: #E8D7A0; margin-top: 20px;'>5. Competitive Intelligence</h4>
        <p style='color: #FBFBEF; line-height: 1.6;'>
            A configurable percentage of prompts include competitor brand mentions
            (e.g., "X vs Y" or "alternatives to Z"). This tests head-to-head
            visibility — critical because the research shows that AI engines are
            increasingly being used for brand comparison and purchase decisions.
            After testing, our competitor researcher identifies which competitors are
            winning, what content strategies they use, and what you should do about it.
        </p>
        <p style='color: #d0d0d0; font-size: 0.85em; font-style: italic;'>
            Source: GenOptima (2026) — "Generative Engine Optimization Best Practices:
            12 Proven Strategies"; Discovered Labs (2026) — "Profound vs Peec vs Otterly:
            Which AI Visibility Platform Should You Buy?"
        </p>

        <h4 style='color: #E8D7A0; margin-top: 20px;'>6. Monthly Tracking (Same Prompts Over Time)</h4>
        <p style='color: #FBFBEF; line-height: 1.6;'>
            The key to measuring AI visibility improvement is consistency: run the
            <strong>same prompt set</strong> every month against the same AI engines. This
            is the standard approach used by all leading AI visibility tools (Otterly,
            Peec, Profound). Generate once → test monthly → track your progress. Only
            generate new prompts when you launch new products, campaigns, or want to
            test new keyword areas.
        </p>
        <p style='color: #d0d0d0; font-size: 0.85em; font-style: italic;'>
            Source: Otterly.ai (2026) — AI Search Monitoring; Conbersa (2026) — "AI Search
            Monitoring Tools Comparison: Peec AI vs Otterly vs Profound"
        </p>

        <div style='background-color: rgba(232, 215, 160, 0.15); padding: 16px;
                    border-radius: 6px; margin-top: 20px;'>
            <p style='color: #E8D7A0; margin: 0; font-size: 0.95em;'>
                <strong>💡 Bottom line:</strong> This tool generates prompts the way your
                real audience actually talks to AI — grounded in your keyword data and shaped
                by your audience personas. The approach is aligned with the GEO best practices
                from Ahrefs, Search Engine Journal, and the leading AI visibility platforms in 2026.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_generation_section(client_name, batch_manager):
    """Render the generation controls and execute generation."""
    existing_prompt_count = batch_manager.count_existing_prompts(client_name, status='active')

    # Batch config
    with st.expander("📦 Batch Configuration", expanded=existing_prompt_count == 0):
        if existing_prompt_count > 0:
            st.info(f"You have **{existing_prompt_count} existing prompts** for {client_name}")
            batch_mode = st.radio(
                "What do you want to do?",
                ["🔄 Start Fresh (Replace all existing prompts)",
                 "➕ Add New Prompts (Keep existing, add more)"],
                index=1
            )
            start_fresh = batch_mode.startswith("🔄")
            if start_fresh:
                st.warning("⚠️ This will replace all existing prompts. Existing prompts will be archived.")
        else:
            st.info("🎉 This will be your **first batch of prompts** for this client!")
            start_fresh = True

        col1, col2 = st.columns(2)
        with col1:
            default_name = "Initial Baseline" if (start_fresh and existing_prompt_count == 0) else (
                "Complete Refresh" if start_fresh else ""
            )
            batch_name = st.text_input("Batch Name *", value=default_name,
                                        placeholder="e.g., Q3 Campaign, Holiday Keywords")
        with col2:
            default_notes = "Core prompt library for ongoing monthly tracking" if (
                start_fresh and existing_prompt_count == 0
            ) else ""
            batch_notes = st.text_area("Notes (Optional)", value=default_notes,
                                        placeholder="Context about why these prompts are being generated",
                                        height=80)

    # Generation settings
    with st.expander("⚙️ Generation Settings", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            total_prompts = st.slider(
                "Total Prompts to Generate", min_value=10, max_value=1000,
                value=st.session_state.generation_config.get('total_prompts', 100), step=10
            )
            st.session_state.generation_config['total_prompts'] = total_prompts

            ai_ratio = st.slider(
                "AI Generation (%)", min_value=0, max_value=100,
                value=int(st.session_state.generation_config.get('ai_ratio', 0.7) * 100), step=10
            ) / 100
            st.session_state.generation_config['ai_ratio'] = ai_ratio

        with col2:
            competitor_ratio = st.slider(
                "Competitor Mentions (%)", min_value=0, max_value=50,
                value=int(st.session_state.generation_config.get('competitor_ratio', 0.3) * 100), step=5
            ) / 100
            st.session_state.generation_config['competitor_ratio'] = competitor_ratio

            dedup_mode = st.selectbox(
                "Deduplication Mode",
                ["Exact Match", "High Similarity (90%)", "Disabled"], index=1
            )
            if dedup_mode == "Exact Match":
                dedup_threshold, enable_dedup = 1.0, True
            elif dedup_mode == "High Similarity (90%)":
                dedup_threshold, enable_dedup = 0.90, True
            else:
                dedup_threshold, enable_dedup = 0, False

    # Summary
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**{total_prompts}** prompts · **{int(competitor_ratio*100)}%** competitor mentions · "
                     f"**{int(ai_ratio*100)}%** AI generated · **{dedup_mode}** dedup")
    with col2:
        personas_file_path = st.session_state.generation_config.get('personas_file')
        keywords_file_path = st.session_state.generation_config.get('keywords_file')
        if personas_file_path and Path(personas_file_path).exists():
            st.success("✓ Data sources loaded")
        else:
            st.warning("⚠ Data sources missing")

    # Generate button
    can_generate = bool(batch_name and batch_name.strip())
    if not can_generate:
        st.warning("⚠️ Please enter a batch name above")

    generate_button = st.button("🚀 Generate Prompts", type="primary",
                                 use_container_width=True, disabled=not can_generate)

    if generate_button:
        personas_file = st.session_state.generation_config.get('personas_file')
        keywords_file = st.session_state.generation_config.get('keywords_file')

        if not personas_file or not keywords_file:
            st.error("❌ No data sources configured. Select a client in Client Manager first.")
            return
        if not Path(personas_file).exists() or not Path(keywords_file).exists():
            st.error("❌ Data files not found. Check your client configuration.")
            return

        # Initialize deduplicator
        deduplicator = PromptDeduplicator(
            exact_match=True, similarity_threshold=dedup_threshold
        ) if enable_dedup else None

        # Load brand config
        brand_config = {}
        brand_config_file = st.session_state.generation_config.get('brand_config_file')
        if brand_config_file and Path(brand_config_file).exists():
            try:
                with open(brand_config_file, 'r') as f:
                    brand_config = json.load(f)
            except Exception:
                pass

        # Initialize generator
        generator = PromptGenerator(
            personas_file=personas_file,
            keywords_file=keywords_file,
            api_client=None,
            use_ai_generation=False,
            deduplicator=deduplicator,
            enable_deduplication=enable_dedup,
            brand_config=brand_config
        )

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("📦 Creating batch...")
            batch_id = batch_manager.create_batch(
                batch_name=batch_name, notes=batch_notes, client_name=client_name
            )

            if start_fresh and existing_prompt_count > 0:
                status_text.text("📥 Archiving existing prompts...")
                for batch in batch_manager.get_active_batches(client_name):
                    batch_manager.archive_batch(batch['batch_id'], reason="Replaced by new generation")

            status_text.text("🔄 Generating prompts...")
            prompts = generator.generate_prompts(
                total_count=total_prompts, competitor_ratio=competitor_ratio
            )
            progress_bar.progress(80)

            status_text.text("🏷️ Adding batch metadata...")
            prompts = add_batch_metadata_to_prompts(
                prompts, batch_id=batch_id, batch_name=batch_name, batch_manager=batch_manager
            )
            progress_bar.progress(100)

            # Update session state
            st.session_state.generated_prompts = prompts
            st.session_state.approval_manager.load_prompts(prompts, default_status='pending')
            st.session_state.current_batch_id = batch_id
            st.session_state.current_batch_name = batch_name

            stats = generator.generation_stats
            status_text.success(f"✅ Generated {len(prompts)} prompts!")

            # Show generation metrics
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            st.metric("Duration", f"{duration:.1f}s")

            # Save to draft files
            draft_dir = Path('data/prompt_generation/drafts')
            draft_dir.mkdir(parents=True, exist_ok=True)
            draft_file = draft_dir / f"batch_{batch_id}_prompts.json"

            session_data = {
                'batch_id': batch_id,
                'batch_name': batch_name,
                'client_name': client_name,
                'timestamp': datetime.now().isoformat(),
                'config': st.session_state.generation_config,
                'prompts': prompts,
                'stats': stats,
                'approval_statuses': {p['prompt_id']: 'pending' for p in prompts}
            }
            with open(draft_file, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)

            try:
                from src.client_manager.gcs_sync import GCSClientSync
                GCSClientSync().upload_prompt_data()
                st.success("✅ Prompts saved and synced to cloud!")
            except Exception:
                st.success("✅ Prompts saved locally!")

        except Exception as e:
            st.error(f"❌ Error during generation: {str(e)}")
            st.exception(e)


def _render_review_section(client_name):
    """Render the review table with inline approve/reject/delete and export."""
    # Load prompts from drafts if needed
    all_draft_prompts, draft_files = _load_drafts(client_name)

    if not st.session_state.get('generated_prompts') and all_draft_prompts:
        st.session_state.generated_prompts = all_draft_prompts
        if 'approval_manager' in st.session_state:
            st.session_state.approval_manager.load_prompts(all_draft_prompts, default_status='pending')
        st.info(f"📂 Loaded {len(all_draft_prompts)} prompts from {len(draft_files)} saved batches")

    if not st.session_state.get('generated_prompts') and not all_draft_prompts:
        st.info("No prompts generated yet. Use the controls above to generate your first batch.")
        return

    # Clear all prompts option
    with st.expander("Clear all prompts"):
        st.caption("Delete all generated prompts and draft files for this client. This cannot be undone.")
        confirm_text = st.text_input(
            f"Type **{client_name}** to confirm",
            key="clear_prompts_confirm",
            placeholder=client_name,
        )
        if st.button("Delete all prompts", type="secondary", key="clear_prompts_btn",
                      disabled=(confirm_text != client_name)):
            # Clear session state
            st.session_state.generated_prompts = []
            if 'approval_manager' in st.session_state:
                st.session_state.approval_manager.load_prompts([], default_status='pending')
            # Delete draft files for this client (local + GCS)
            draft_dir = Path('data/prompt_generation/drafts')
            deleted_files = []
            if draft_dir.exists():
                for df in draft_dir.glob('batch_*_prompts.json'):
                    try:
                        with open(df, 'r') as f:
                            data = json.load(f)
                        if data.get('client_name') == client_name:
                            deleted_files.append(df.name)
                            df.unlink()
                    except Exception:
                        pass
            # Clean batch metadata
            batches_file = Path('data/prompt_batches.json')
            if batches_file.exists():
                try:
                    with open(batches_file, 'r') as f:
                        batches = json.load(f)
                    batches = {k: v for k, v in batches.items()
                               if v.get('client_name') != client_name}
                    with open(batches_file, 'w') as f:
                        json.dump(batches, f, indent=2, default=str)
                except Exception:
                    pass

            # ── GCS cleanup — delete drafts from cloud so they don't come back ──
            gcs_status = ""
            try:
                from src.client_manager.gcs_sync import GCSClientSync
                gcs = GCSClientSync()
                bucket = gcs.bucket
                for filename in deleted_files:
                    gcs_path = f"prompt-data/drafts/{filename}"
                    blob = bucket.blob(gcs_path)
                    if blob.exists():
                        blob.delete()
                if batches_file.exists():
                    blob = bucket.blob('prompt-data/prompt_batches.json')
                    blob.upload_from_filename(str(batches_file))
                gcs_status = " (including cloud storage)"
            except Exception as e:
                gcs_status = f" (local only — cloud cleanup failed: {e})"

            st.success(f"All prompts for {client_name} have been deleted{gcs_status}.")
            st.rerun()

    approval_mgr = st.session_state.approval_manager

    try:
        all_prompts = approval_mgr.get_all_prompts()
        if not all_prompts:
            return
    except Exception:
        return

    # Stats bar
    stats = approval_mgr.get_approval_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", stats['total'])
    with col2:
        st.metric("Approved", stats['approved'], delta=f"{stats['approval_rate']:.0f}%")
    with col3:
        st.metric("Rejected", stats['rejected'])
    with col4:
        st.metric("Pending", stats['pending'])

    # Filters in sidebar
    with st.sidebar:
        st.markdown("### 🔍 Filters")

        personas = sorted(set(p['persona'] for p in all_prompts))
        selected_personas = st.multiselect("Persona", personas, default=personas)

        intent_types = sorted(set(p['intent_type'] for p in all_prompts))
        selected_intents = st.multiselect("Intent Type", intent_types, default=intent_types)

        status_filter = st.radio("Status", ["All", "Pending", "Approved", "Rejected"], index=0)

        search_text = st.text_input("Search Text", "")

    # Apply filters
    if status_filter == "All":
        filtered = all_prompts
    else:
        filtered = approval_mgr.get_prompts_by_status(status_filter.lower())

    filtered = [p for p in filtered if p['persona'] in selected_personas]
    filtered = [p for p in filtered if p['intent_type'] in selected_intents]

    if search_text:
        filtered = [p for p in filtered if search_text.lower() in p['prompt_text'].lower()]

    # Bulk actions + download all
    action_col, dl_col = st.columns([3, 1])
    with action_col:
        st.markdown(f"**{len(filtered)} prompts** matching filters")
    with dl_col:
        # Build CSV of ALL filtered prompts (not just current page)
        all_csv_rows = []
        for p in filtered:
            all_csv_rows.append({
                'ID': p['prompt_id'],
                'Persona': p['persona'],
                'Intent': p['intent_type'],
                'Prompt Text': p['prompt_text'],
                'Score': p.get('expected_visibility_score', ''),
                'Status': p.get('status', 'pending').title(),
            })
        if all_csv_rows:
            import io
            csv_buf = io.StringIO()
            w = csv.DictWriter(csv_buf, fieldnames=all_csv_rows[0].keys())
            w.writeheader()
            w.writerows(all_csv_rows)
            st.download_button(
                "⬇ Download All",
                data=csv_buf.getvalue(),
                file_name=f"all_prompts_{client_name.replace(' ', '_')}.csv",
                mime="text/csv",
                key="download_all_csv",
                use_container_width=True,
            )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✓ Approve All Visible", use_container_width=True, key="bulk_approve"):
            approval_mgr.bulk_approve_filtered(filtered)
            _save_approval_statuses(client_name)
            st.rerun()
    with col2:
        if st.button("✗ Reject All Visible", use_container_width=True, key="bulk_reject"):
            approval_mgr.bulk_reject_filtered(filtered)
            _save_approval_statuses(client_name)
            st.rerun()
    with col3:
        if st.button("↺ Reset All Visible", use_container_width=True, key="bulk_reset"):
            prompt_ids = [p['prompt_id'] for p in filtered]
            approval_mgr.reset_prompts(prompt_ids)
            _save_approval_statuses(client_name)
            st.rerun()

    # Pagination
    page_size = 50
    total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
    page = st.selectbox("Page", range(1, total_pages + 1),
                         format_func=lambda x: f"Page {x} of {total_pages}") if total_pages > 1 else 1

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(filtered))
    page_prompts = filtered[start_idx:end_idx]

    # Display table
    if page_prompts:
        df_data = []
        for prompt in page_prompts:
            row = {
                'ID': prompt['prompt_id'],
                'Persona': prompt['persona'],
                'Intent': prompt['intent_type'],
                'Prompt Text': prompt['prompt_text'],
                'Score': prompt['expected_visibility_score'],
                'Status': prompt.get('approval_status', 'pending').title()
            }
            df_data.append(row)

        df = pd.DataFrame(df_data)

        def highlight_status(row):
            status = row['Status'].lower()
            if status == 'approved':
                return ['background-color: #d4edda'] * len(row)
            elif status == 'rejected':
                return ['background-color: #f8d7da'] * len(row)
            return [''] * len(row)

        styled_df = df.style.apply(highlight_status, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=500)

        # Individual prompt actions
        with st.expander("✏️ Edit Individual Prompt", expanded=False):
            selected_id = st.selectbox(
                "Select a prompt",
                df['ID'].tolist(),
                format_func=lambda x: f"{x} - {df[df['ID']==x]['Prompt Text'].values[0][:60]}..."
            )

            if selected_id:
                selected_prompt = next(p for p in page_prompts if p['prompt_id'] == selected_id)

                new_text = st.text_area("Prompt Text", value=selected_prompt['prompt_text'],
                                         height=80, key=f"edit_{selected_id}")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("💾 Save", key=f"save_{selected_id}"):
                        approval_mgr.edit_prompt(selected_id, {'prompt_text': new_text})
                        st.success("Saved!")
                        st.rerun()
                with col2:
                    if st.button("✓ Approve", key=f"approve_{selected_id}"):
                        approval_mgr.approve_prompts([selected_id])
                        _save_approval_statuses(client_name)
                        st.rerun()
                with col3:
                    if st.button("✗ Reject", key=f"reject_{selected_id}"):
                        approval_mgr.reject_prompts([selected_id])
                        _save_approval_statuses(client_name)
                        st.rerun()
                with col4:
                    if st.button("↺ Reset", key=f"reset_{selected_id}"):
                        approval_mgr.reset_prompts([selected_id])
                        _save_approval_statuses(client_name)
                        st.rerun()
    else:
        st.info("No prompts match the current filters.")


def _render_export_section(client_name):
    """Render the export controls."""
    approval_mgr = st.session_state.approval_manager
    stats = approval_mgr.get_approval_stats()

    if stats['approved'] == 0:
        st.info("No approved prompts to export yet. Approve prompts above first.")
        return

    approved_prompts = approval_mgr.get_prompts_by_status('approved')

    st.markdown(f"**{stats['approved']} approved prompts** ready to export")

    col1, col2, col3 = st.columns(3)

    with col1:
        # CSV export for dashboard
        if st.button("📊 Export to Dashboard CSV", type="primary", use_container_width=True,
                      key="export_csv_btn"):
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                # Save to approved directory
                approved_dir = Path('data/prompt_generation/approved')
                approved_dir.mkdir(parents=True, exist_ok=True)
                approved_file = approved_dir / f"approved_{client_name.replace(' ', '_')}_{timestamp}.csv"

                fieldnames = ['prompt_id', 'client_name', 'persona', 'category', 'intent_type',
                              'prompt_text', 'expected_visibility_score', 'notes',
                              'batch_id', 'batch_name', 'date_added', 'status']

                with open(approved_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for prompt in approved_prompts:
                        row = {k: prompt.get(k, '') for k in fieldnames}
                        row['client_name'] = client_name
                        writer.writerow(row)

                # Also write to main CSV
                main_csv = Path('data/generated_prompts.csv')
                existing_ids = set()
                if main_csv.exists():
                    with open(main_csv, 'r') as f:
                        existing_ids = {r['prompt_id'] for r in csv.DictReader(f)}

                new_prompts = [p for p in approved_prompts if p['prompt_id'] not in existing_ids]

                mode = 'a' if main_csv.exists() else 'w'
                with open(main_csv, mode, newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    if mode == 'w':
                        writer.writeheader()
                    for prompt in new_prompts:
                        row = {k: prompt.get(k, '') for k in fieldnames}
                        row['client_name'] = client_name
                        writer.writerow(row)

                _sync_to_gcs()
                st.success(f"✅ Exported {len(new_prompts)} new prompts to dashboard CSV")
                if len(new_prompts) < len(approved_prompts):
                    st.info(f"Skipped {len(approved_prompts) - len(new_prompts)} duplicates")

            except Exception as e:
                st.error(f"❌ Export error: {str(e)}")

    with col2:
        # Excel export for client review
        if st.button("📤 Export Client Review Excel", use_container_width=True,
                      key="export_excel_btn"):
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                review_data = []
                for prompt in approved_prompts:
                    review_data.append({
                        'Prompt ID': prompt['prompt_id'],
                        'Persona': prompt['persona'],
                        'Category': prompt['category'],
                        'Intent Type': prompt['intent_type'],
                        'Prompt Text': prompt['prompt_text'],
                        'Expected Score': prompt['expected_visibility_score'],
                        'Notes': prompt.get('notes', ''),
                    })

                df = pd.DataFrame(review_data)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Prompts')
                    ws = writer.sheets['Prompts']
                    ws.freeze_panes = 'A2'
                    ws.column_dimensions['E'].width = 60

                st.download_button(
                    label="💾 Download Excel",
                    data=output.getvalue(),
                    file_name=f"prompts_{client_name.replace(' ', '_')}_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel"
                )
            except Exception as e:
                st.error(f"❌ Excel export error: {str(e)}")

    with col3:
        # JSON export
        json_data = json.dumps(approved_prompts, indent=2, default=str)
        st.download_button(
            label="📋 Download JSON",
            data=json_data,
            file_name=f"prompts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="download_json"
        )


def render():
    """Render the consolidated Generate & Review page."""
    _apply_theme()

    st.title("✨ Generate & Review")

    # Always re-sync generation_config from the registry for the active client.
    # This prevents stale/cross-client file paths from a previous session.
    active_slug = st.session_state.get('active_client', '')
    if active_slug:
        registry = ClientRegistry()
        client_data = registry.get_client(active_slug)
        if client_data:
            files = client_data.get('files', {})
            st.session_state.generation_config = {
                'client_name': client_data.get('name', active_slug),
                'personas_file': files.get('personas', ''),
                'keywords_file': files.get('keywords', ''),
                'brand_config_file': files.get('brand_config', ''),
            }

    # Check client
    client_name = st.session_state.generation_config.get('client_name')
    personas_file = st.session_state.generation_config.get('personas_file')
    keywords_file = st.session_state.generation_config.get('keywords_file')

    if not (client_name and personas_file and keywords_file):
        st.warning("⚠️ No client selected. Go to **Quick Setup** to select a client first.")
        return

    # Active client banner
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #4A4458 0%, #5a5468 100%);
                padding: 12px 20px; border-radius: 8px; border-left: 4px solid #E8D7A0;
                margin-bottom: 20px;'>
        <p style='color: white; margin: 0; font-size: 1.1em;'>
            <strong>🌟 Active Client:</strong> {client_name}
        </p>
    </div>
    """, unsafe_allow_html=True)

    batch_manager = BatchManager()

    # Three tabs for the workflow
    tab_generate, tab_review, tab_methodology = st.tabs([
        "🚀 Generate", "🔍 Review & Export", "📖 How It Works"
    ])

    with tab_generate:
        _render_generation_section(client_name, batch_manager)

    with tab_review:
        st.markdown("### Review Prompts")
        st.markdown("Approve, reject, or edit prompts. Then export when ready.")
        st.markdown("---")
        _render_review_section(client_name)

        st.markdown("---")
        st.markdown("### 📤 Export")
        _render_export_section(client_name)

    with tab_methodology:
        _render_methodology()
