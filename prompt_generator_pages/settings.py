"""
Settings page for prompt generator app.
"""

import streamlit as st
from pathlib import Path
import json
import sys

sys.path.insert(0, 'src')


def render():
    """Render the settings page."""
    st.title("⚙ Settings")
    st.markdown("Configure data sources and generation defaults.")

    # Config file path
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / 'prompt_generator_config.json'

    # Load existing config
    if config_file.exists():
        with open(config_file, 'r') as f:
            saved_config = json.load(f)
    else:
        saved_config = {}

    # Merge with session state
    config = {**saved_config, **st.session_state.generation_config}

    # Data Sources Section
    st.markdown("## 📁 Data Sources")

    with st.container():
        st.markdown("### Personas File")

        personas_file = st.text_input(
            "Path to personas JSON file",
            value=config.get('personas_file', 'data/natasha_denona_personas.json'),
            help="JSON file containing persona definitions with weights and priority topics"
        )

        personas_path = Path(personas_file)
        if personas_path.exists():
            st.success(f"✓ File found: {personas_file}")

            # Show preview
            if st.checkbox("Show personas preview", key="preview_personas"):
                try:
                    with open(personas_path, 'r') as f:
                        personas_data = json.load(f)

                    st.json(personas_data)
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
        else:
            st.error(f"✗ File not found: {personas_file}")

        st.markdown("### Keywords File")

        keywords_file = st.text_input(
            "Path to keywords CSV file",
            value=config.get('keywords_file', 'data/natasha_denona_keywords.csv'),
            help="CSV file containing keywords with intent types, search volumes, and competitor brands"
        )

        keywords_path = Path(keywords_file)
        if keywords_path.exists():
            st.success(f"✓ File found: {keywords_file}")

            # Show preview
            if st.checkbox("Show keywords preview", key="preview_keywords"):
                try:
                    import pandas as pd
                    df = pd.read_csv(keywords_path)
                    st.dataframe(df.head(10), use_container_width=True)
                    st.markdown(f"**Total keywords:** {len(df)}")

                    # Show distribution by intent
                    if 'intent_type' in df.columns:
                        st.markdown("**Distribution by intent:**")
                        intent_counts = df['intent_type'].value_counts()
                        for intent, count in intent_counts.items():
                            st.markdown(f"- {intent}: {count}")

                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
        else:
            st.error(f"✗ File not found: {keywords_file}")

    st.markdown("---")

    # Generation Defaults Section
    st.markdown("## 🎯 Generation Defaults")

    with st.container():
        default_prompts = st.number_input(
            "Default number of prompts",
            min_value=10,
            max_value=1000,
            value=config.get('total_prompts', 100),
            step=10,
            help="Default value for total prompts slider"
        )

        default_competitor_ratio = st.slider(
            "Default competitor mention ratio (%)",
            min_value=0,
            max_value=50,
            value=int(config.get('competitor_ratio', 0.3) * 100),
            step=5,
            help="Default percentage of prompts with competitor mentions"
        ) / 100

        default_ai_ratio = st.slider(
            "Default AI generation ratio (%)",
            min_value=0,
            max_value=100,
            value=int(config.get('ai_ratio', 0.7) * 100),
            step=10,
            help="Default percentage of prompts generated using AI vs templates"
        ) / 100

        default_dedup = st.selectbox(
            "Default deduplication mode",
            ["Exact Match", "High Similarity (90%)", "Disabled"],
            index=1,
            help="Default deduplication strategy"
        )

    st.markdown("---")

    # Advanced Settings Section
    st.markdown("## 🔧 Advanced Settings")

    with st.container():
        pagination_size = st.number_input(
            "Table pagination size",
            min_value=10,
            max_value=200,
            value=config.get('pagination_size', 50),
            step=10,
            help="Number of prompts to show per page in Review & Approve"
        )

        autosave_interval = st.number_input(
            "Auto-save interval (seconds)",
            min_value=15,
            max_value=300,
            value=config.get('autosave_interval', 30),
            step=15,
            help="How often to auto-save draft sessions"
        )

    st.markdown("---")

    # Save button
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            # Update session state
            st.session_state.generation_config.update({
                'personas_file': personas_file,
                'keywords_file': keywords_file,
                'total_prompts': default_prompts,
                'competitor_ratio': default_competitor_ratio,
                'ai_ratio': default_ai_ratio,
                'deduplication_mode': default_dedup,
                'pagination_size': pagination_size,
                'autosave_interval': autosave_interval
            })

            # Save to file
            with open(config_file, 'w') as f:
                json.dump(st.session_state.generation_config, f, indent=2)

            st.success("✅ Settings saved successfully!")
            st.balloons()

    # Reset to defaults
    with col3:
        if st.button("↺ Reset to Defaults", use_container_width=True):
            default_config = {
                'personas_file': 'data/natasha_denona_personas.json',
                'keywords_file': 'data/natasha_denona_keywords.csv',
                'total_prompts': 100,
                'competitor_ratio': 0.3,
                'ai_ratio': 0.7,
                'deduplication_mode': 'High Similarity (90%)',
                'pagination_size': 50,
                'autosave_interval': 30
            }

            st.session_state.generation_config = default_config

            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)

            st.success("✅ Reset to default settings!")
            st.rerun()

    st.markdown("---")

    # System Info
    with st.expander("📊 System Information"):
        st.markdown("### Current Configuration")
        st.json(st.session_state.generation_config)

        st.markdown("### File Paths")
        st.markdown(f"- **Config file:** `{config_file}`")
        st.markdown(f"- **Drafts directory:** `data/prompt_generation/drafts/`")
        st.markdown(f"- **Approved directory:** `data/prompt_generation/approved/`")
        st.markdown(f"- **Archived directory:** `data/prompt_generation/archived/`")

        # Check data directories
        st.markdown("### Data Directories Status")
        for dir_name in ['drafts', 'approved', 'archived']:
            dir_path = Path(f'data/prompt_generation/{dir_name}')
            if dir_path.exists():
                file_count = len(list(dir_path.iterdir()))
                st.success(f"✓ {dir_name}: {file_count} files")
            else:
                st.warning(f"⚠ {dir_name}: Directory not found")

    # Help section
    with st.expander("❓ Help"):
        st.markdown("""
        ### How to Use Settings

        **Data Sources:**
        - Point to your personas JSON and keywords CSV files
        - Files must exist at the specified paths
        - Use the preview checkboxes to verify file contents

        **Generation Defaults:**
        - These values will be pre-filled when you go to the Generate page
        - You can still adjust them per session

        **Advanced Settings:**
        - Pagination size: Controls how many prompts show per page in Review
        - Auto-save interval: How often draft sessions are saved (future feature)

        **File Formats:**
        - **Personas JSON:** Should contain persona objects with `id`, `name`, `weight`, `description`, and `priority_topics`
        - **Keywords CSV:** Should have columns: `keyword`, `intent_type`, `search_volume`, `competitor_brands`
        """)
