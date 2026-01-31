"""
Generation page for prompt generator app.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, 'src')

from src.prompt_generator.generator import PromptGenerator
from src.prompt_generator.deduplicator import PromptDeduplicator
from src.prompt_generator.batch_manager import BatchManager, add_batch_metadata_to_prompts


def render():
    """Render the generation page."""
    st.title("✨ Generate Prompts")

    # Quick context
    st.markdown("""
    <div style='background-color: #4A4458; padding: 16px; border-radius: 6px; margin-bottom: 20px;'>
        <h4 style='color: #E8D7A0; margin-top: 0;'>📌 When to Use This Page</h4>
        <ul style='color: #FBFBEF; margin-bottom: 0;'>
            <li><strong>Initial Setup:</strong> Generate your core prompt library (100-200 prompts)</li>
            <li><strong>New Product/Campaign:</strong> Generate additional prompts for new offerings</li>
            <li><strong>NOT for monthly tracking:</strong> Reuse the same prompts each month to measure improvement!</li>
        </ul>
        <p style='color: #E8D7A0; margin: 12px 0 0 0; font-size: 0.9em;'>
            💡 <strong>Tip:</strong> Once you have your prompts, use the Main Dashboard monthly to track if your visibility is improving.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Show active client banner
    if 'active_client' in st.session_state and st.session_state.active_client:
        client_name = st.session_state.generation_config.get('client_name', 'Unknown Client')
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #4A4458 0%, #5a5468 100%);
                    padding: 16px 24px;
                    border-radius: 8px;
                    border-left: 4px solid #E8D7A0;
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

    # Check for existing prompts
    existing_prompt_count = batch_manager.count_existing_prompts(client_name, status='active')

    # Batch Management UI
    st.markdown("### 📦 Batch Configuration")

    if existing_prompt_count > 0:
        st.markdown(f"""
        <div style='background-color: rgba(232, 215, 160, 0.15); padding: 16px; border-radius: 6px; margin-bottom: 20px;'>
            <p style='color: #E8D7A0; margin: 0; font-size: 1.05em;'>
                ℹ️ You have <strong>{existing_prompt_count} existing prompts</strong> for {client_name}
            </p>
        </div>
        """, unsafe_allow_html=True)

        batch_mode = st.radio(
            "What do you want to do?",
            ["🔄 Start Fresh (Replace all existing prompts)", "➕ Add New Prompts (Keep existing, add more)"],
            index=1,  # Default to adding new
            help="Choose whether to replace all existing prompts or add new ones to your library"
        )

        start_fresh = batch_mode.startswith("🔄")

        if start_fresh:
            st.warning("⚠️ **Warning:** This will replace all existing prompts. Existing prompts will be archived but not deleted.")
    else:
        st.info("🎉 This will be your **first batch of prompts** for this client!")
        start_fresh = True
        batch_mode = "🌟 Initial Baseline"

    # Batch details
    st.markdown("#### Batch Details")

    col1, col2 = st.columns([1, 1])

    with col1:
        if start_fresh and existing_prompt_count == 0:
            default_name = "Initial Baseline"
        elif start_fresh:
            default_name = "Complete Refresh"
        else:
            default_name = ""

        batch_name = st.text_input(
            "Batch Name *",
            value=default_name,
            placeholder="e.g., New Product Launch, Q3 Campaign, Holiday Keywords",
            help="Give this batch a descriptive name so you can track it later"
        )

    with col2:
        if start_fresh and existing_prompt_count == 0:
            default_notes = "Core prompt library for ongoing monthly tracking"
        else:
            default_notes = ""

        batch_notes = st.text_area(
            "Notes (Optional)",
            value=default_notes,
            placeholder="e.g., Testing new lipstick line visibility, Campaign runs through Q2",
            help="Add context about why these prompts are being generated",
            height=100
        )

    st.markdown("---")
    st.markdown("Configure and generate prompts with real-time deduplication.")

    # Sidebar configuration
    with st.sidebar:
        st.markdown("### Generation Settings")

        # Number of prompts (PROMINENT CONTROL)
        total_prompts = st.slider(
            "Total Prompts to Generate",
            min_value=10,
            max_value=1000,
            value=st.session_state.generation_config.get('total_prompts', 100),
            step=10,
            help="Choose how many prompts you want to generate"
        )
        st.session_state.generation_config['total_prompts'] = total_prompts

        # Competitor mention ratio
        competitor_ratio = st.slider(
            "Competitor Mentions (%)",
            min_value=0,
            max_value=50,
            value=int(st.session_state.generation_config.get('competitor_ratio', 0.3) * 100),
            step=5,
            help="Percentage of prompts that should include competitor brand mentions"
        ) / 100
        st.session_state.generation_config['competitor_ratio'] = competitor_ratio

        # AI generation ratio
        ai_ratio = st.slider(
            "AI Generation (%)",
            min_value=0,
            max_value=100,
            value=int(st.session_state.generation_config.get('ai_ratio', 0.7) * 100),
            step=10,
            help="Percentage of prompts generated using AI vs templates"
        ) / 100
        st.session_state.generation_config['ai_ratio'] = ai_ratio

        # Deduplication mode
        dedup_mode = st.selectbox(
            "Deduplication Mode",
            ["Exact Match", "High Similarity (90%)", "Disabled"],
            index=1,  # Default to high similarity
            help="Choose how aggressive deduplication should be"
        )

        if dedup_mode == "Exact Match":
            dedup_threshold = 1.0
            enable_dedup = True
        elif dedup_mode == "High Similarity (90%)":
            dedup_threshold = 0.90
            enable_dedup = True
        else:
            dedup_threshold = 0
            enable_dedup = False

        st.session_state.generation_config['deduplication_mode'] = dedup_mode
        st.session_state.generation_config['dedup_threshold'] = dedup_threshold
        st.session_state.generation_config['enable_dedup'] = enable_dedup

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Configuration Summary")
        st.markdown(f"- **Prompts to generate:** {total_prompts}")
        st.markdown(f"- **Competitor mentions:** {int(competitor_ratio * 100)}% ({int(total_prompts * competitor_ratio)} prompts)")
        st.markdown(f"- **AI generation:** {int(ai_ratio * 100)}%")
        st.markdown(f"- **Deduplication:** {dedup_mode}")

    with col2:
        st.markdown("### Data Sources")
        personas_file = Path(st.session_state.generation_config.get('personas_file', 'data/natasha_denoma_personas.json'))
        keywords_file = Path(st.session_state.generation_config.get('keywords_file', 'data/natasha_denoda_keywords.csv'))

        if personas_file.exists():
            st.success(f"✓ Personas loaded")
        else:
            st.warning(f"⚠ Personas file not found")

        if keywords_file.exists():
            st.success(f"✓ Keywords loaded")
        else:
            st.warning(f"⚠ Keywords file not found")

    st.markdown("---")

    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Validate batch name
        can_generate = bool(batch_name and batch_name.strip())

        if not can_generate:
            st.warning("⚠️ Please enter a batch name above")

        generate_button = st.button(
            "🚀 Generate Prompts",
            type="primary",
            use_container_width=True,
            disabled=not can_generate
        )

    # Generation process
    if generate_button:
        personas_file = st.session_state.generation_config.get('personas_file', 'data/natasha_denoma_personas.json')
        keywords_file = st.session_state.generation_config.get('keywords_file', 'data/natasha_denoda_keywords.csv')

        if not Path(personas_file).exists() or not Path(keywords_file).exists():
            st.error("Please configure valid personas and keywords files in Settings.")
            return

        # Initialize deduplicator
        if enable_dedup:
            deduplicator = PromptDeduplicator(
                exact_match=True,
                similarity_threshold=dedup_threshold
            )
        else:
            deduplicator = None

        # Initialize generator
        generator = PromptGenerator(
            personas_file=personas_file,
            keywords_file=keywords_file,
            api_client=None,  # No AI client for now (template-based only)
            use_ai_generation=False,  # Disable AI for now
            deduplicator=deduplicator,
            enable_deduplication=enable_dedup
        )

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        stats_placeholder = st.empty()

        try:
            # Create batch
            status_text.text("📦 Creating batch...")
            batch_id = batch_manager.create_batch(
                batch_name=batch_name,
                notes=batch_notes,
                client_name=client_name
            )

            # If starting fresh, archive existing batches
            if start_fresh and existing_prompt_count > 0:
                status_text.text("📥 Archiving existing prompts...")
                active_batches = batch_manager.get_active_batches(client_name)
                for batch in active_batches:
                    batch_manager.archive_batch(
                        batch['batch_id'],
                        reason="Replaced by new generation"
                    )

            status_text.text("🔄 Generating prompts...")

            # Generate prompts
            prompts = generator.generate_prompts(
                total_count=total_prompts,
                competitor_ratio=competitor_ratio
            )

            progress_bar.progress(80)

            # Add batch metadata to prompts
            status_text.text("🏷️ Adding batch metadata...")
            prompts = add_batch_metadata_to_prompts(
                prompts,
                batch_id=batch_id,
                batch_name=batch_name,
                batch_manager=batch_manager
            )

            progress_bar.progress(100)

            # Update session state
            st.session_state.generated_prompts = prompts
            st.session_state.approval_manager.load_prompts(prompts, default_status='pending')

            # Store batch info in session for review page
            st.session_state.current_batch_id = batch_id
            st.session_state.current_batch_name = batch_name

            # Show stats
            stats = generator.generation_stats
            duplicates_removed = stats.get('duplicates_removed', 0)

            status_text.success(f"✅ Generation complete!")

            # Show batch info
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #4A4458 0%, #5a5468 100%);
                        padding: 20px 24px;
                        border-radius: 8px;
                        border-left: 4px solid #E8D7A0;
                        margin-bottom: 24px;'>
                <h3 style='color: white; margin: 0 0 12px 0;'>📦 Batch Created: {batch_name}</h3>
                <p style='color: #FBFBEF; margin: 0; font-size: 0.95em;'>
                    <strong>Batch ID:</strong> {batch_id}<br>
                    <strong>Prompts Generated:</strong> {len(prompts)}<br>
                    {"<strong>Notes:</strong> " + batch_notes if batch_notes else ""}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Display stats
            st.markdown("### Generation Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Generated", len(prompts))

            with col2:
                st.metric("Duplicates Removed", duplicates_removed)

            with col3:
                if duplicates_removed > 0:
                    dup_rate = (duplicates_removed / (len(prompts) + duplicates_removed)) * 100
                    st.metric("Deduplication Rate", f"{dup_rate:.1f}%")
                else:
                    st.metric("Deduplication Rate", "0%")

            with col4:
                duration = (stats['end_time'] - stats['start_time']).total_seconds()
                st.metric("Duration", f"{duration:.1f}s")

            # Breakdown by persona
            st.markdown("### Distribution by Persona")
            persona_cols = st.columns(len(stats['by_persona']))
            for i, (persona, count) in enumerate(stats['by_persona'].items()):
                with persona_cols[i]:
                    st.metric(persona, count)

            # Show preview of last 10 prompts
            st.markdown("### Preview (Last 10 Prompts)")
            preview_prompts = prompts[-10:]

            for prompt in preview_prompts:
                with st.expander(f"{prompt['persona']} - {prompt['intent_type']}"):
                    st.markdown(f"**Prompt:** {prompt['prompt_text']}")
                    st.markdown(f"**Category:** {prompt['category']}")
                    st.markdown(f"**Expected Score:** {prompt['expected_visibility_score']}")
                    st.markdown(f"**Notes:** {prompt['notes']}")

            # Auto-save draft
            draft_dir = Path('data/prompt_generation/drafts')
            draft_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            draft_file = draft_dir / f"session_{timestamp}.json"

            session_data = {
                'timestamp': timestamp,
                'config': st.session_state.generation_config,
                'prompts': prompts,
                'stats': stats
            }

            with open(draft_file, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)

            st.success(f"✅ Session auto-saved to {draft_file}")

            # Navigation hint
            st.info("👉 Go to **Review & Approve** to filter and approve prompts.")

        except Exception as e:
            st.error(f"❌ Error during generation: {str(e)}")
            st.exception(e)

    # Show current session if exists
    elif st.session_state.generated_prompts:
        st.markdown("### Current Session")
        st.info(f"You have {len(st.session_state.generated_prompts)} prompts loaded. Go to **Review & Approve** to continue working with them.")
