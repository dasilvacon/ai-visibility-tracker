"""
Client Manager - Visual client selection and management.
"""

import streamlit as st
from pathlib import Path
import json
import pandas as pd
import re

# Brand colors
DARK_PURPLE = '#4A4458'
CREAM = '#E8D7A0'
OFF_WHITE = '#FBFBEF'
DARK_BG = '#1c1c1c'


def detect_clients():
    """Auto-detect clients from data directory."""
    data_dir = Path('data')
    clients = {}

    # Find all personas files
    for personas_file in data_dir.glob('*_personas.json'):
        # Extract client name from filename (e.g., "natasha_denona_personas.json" -> "Natasha Denona")
        client_slug = personas_file.stem.replace('_personas', '')
        client_name = client_slug.replace('_', ' ').title()

        # Look for matching keywords file
        keywords_file = data_dir / f"{client_slug}_keywords.csv"

        if keywords_file.exists():
            # Count personas
            try:
                with open(personas_file, 'r') as f:
                    personas_data = json.load(f)
                    if isinstance(personas_data, dict) and 'personas' in personas_data:
                        persona_count = len(personas_data['personas'])
                    elif isinstance(personas_data, list):
                        persona_count = len(personas_data)
                    else:
                        persona_count = 1
            except:
                persona_count = 0

            # Count keywords
            try:
                df = pd.read_csv(keywords_file)
                keyword_count = len(df)
            except:
                keyword_count = 0

            clients[client_slug] = {
                'name': client_name,
                'slug': client_slug,
                'personas_file': str(personas_file),
                'keywords_file': str(keywords_file),
                'persona_count': persona_count,
                'keyword_count': keyword_count
            }

    return clients


def render():
    """Render the client manager page."""
    st.title("🎯 Client Manager")
    st.markdown("Select a client to generate prompts for, or add a new client.")

    # Initialize active client in session state
    if 'active_client' not in st.session_state:
        st.session_state.active_client = None

    # Auto-detect clients
    clients = detect_clients()

    # Active Client Section
    st.markdown("## 🌟 Active Client")

    if st.session_state.active_client and st.session_state.active_client in clients:
        active = clients[st.session_state.active_client]

        # Show active client card
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {DARK_PURPLE} 0%, #5a5468 100%);
                    padding: 30px; border-radius: 12px;
                    border: 2px solid {CREAM};
                    box-shadow: 0 8px 16px rgba(0,0,0,0.3);'>
            <h2 style='color: white; margin: 0 0 16px 0; font-size: 2em;'>✨ {active['name']}</h2>
            <div style='display: flex; gap: 40px; margin-top: 20px;'>
                <div>
                    <p style='color: {CREAM}; margin: 0; font-size: 0.9em; text-transform: uppercase; letter-spacing: 0.1em;'>Personas</p>
                    <p style='color: white; margin: 4px 0 0 0; font-size: 2.5em; font-weight: bold;'>{active['persona_count']}</p>
                </div>
                <div>
                    <p style='color: {CREAM}; margin: 0; font-size: 0.9em; text-transform: uppercase; letter-spacing: 0.1em;'>Keywords</p>
                    <p style='color: white; margin: 4px 0 0 0; font-size: 2.5em; font-weight: bold;'>{active['keyword_count']}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")  # Spacing

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📂 View Personas", use_container_width=True):
                with st.expander("Personas Data", expanded=True):
                    try:
                        with open(active['personas_file'], 'r') as f:
                            personas_data = json.load(f)
                        st.json(personas_data)
                    except Exception as e:
                        st.error(f"Error loading personas: {str(e)}")

        with col2:
            if st.button("📊 View Keywords", use_container_width=True):
                with st.expander("Keywords Data", expanded=True):
                    try:
                        df = pd.read_csv(active['keywords_file'])
                        st.dataframe(df, use_container_width=True)

                        # Show stats
                        if 'intent_type' in df.columns:
                            st.markdown("**Distribution by intent:**")
                            intent_counts = df['intent_type'].value_counts()
                            for intent, count in intent_counts.items():
                                st.markdown(f"- {intent}: {count}")
                    except Exception as e:
                        st.error(f"Error loading keywords: {str(e)}")

    else:
        st.info("👆 No client selected. Choose a client from the list below.")

    st.markdown("---")

    # Available Clients Section
    st.markdown("## 📋 Available Clients")

    if not clients:
        st.warning("No clients found. Add a new client below to get started.")
    else:
        # Show client cards in a grid
        cols_per_row = 2
        client_list = list(clients.values())

        for i in range(0, len(client_list), cols_per_row):
            cols = st.columns(cols_per_row)

            for j, col in enumerate(cols):
                if i + j < len(client_list):
                    client = client_list[i + j]

                    with col:
                        is_active = st.session_state.active_client == client['slug']

                        # Client card
                        border_color = CREAM if is_active else "rgba(232, 215, 160, 0.3)"
                        bg_gradient = f"linear-gradient(135deg, {DARK_PURPLE} 0%, #5a5468 100%)" if is_active else DARK_PURPLE

                        st.markdown(f"""
                        <div style='background: {bg_gradient};
                                    padding: 24px;
                                    border-radius: 8px;
                                    border: 2px solid {border_color};
                                    margin-bottom: 16px;
                                    min-height: 180px;'>
                            <h3 style='color: white; margin: 0 0 12px 0; font-size: 1.4em;'>
                                {'🌟 ' if is_active else ''}{client['name']}
                            </h3>
                            <div style='margin: 16px 0;'>
                                <p style='color: {CREAM}; margin: 4px 0; font-size: 0.95em;'>
                                    📝 {client['persona_count']} personas
                                </p>
                                <p style='color: {CREAM}; margin: 4px 0; font-size: 0.95em;'>
                                    🔑 {client['keyword_count']} keywords
                                </p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if is_active:
                            st.success("✓ Active")
                        else:
                            if st.button(f"Activate {client['name']}", key=f"activate_{client['slug']}", use_container_width=True):
                                st.session_state.active_client = client['slug']

                                # Update generation config
                                st.session_state.generation_config.update({
                                    'personas_file': client['personas_file'],
                                    'keywords_file': client['keywords_file'],
                                    'client_name': client['name']
                                })

                                st.success(f"✅ {client['name']} is now active!")
                                st.rerun()

    st.markdown("---")

    # Add New Client Section
    st.markdown("## ➕ Add New Client")

    with st.expander("📤 Add New Client", expanded=False):
        st.markdown("### Client Information")

        new_client_name = st.text_input(
            "Client Name",
            placeholder="e.g., Rare Beauty, Fenty Beauty",
            help="Enter the client's brand name"
        )

        st.markdown("### Upload Files")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Personas JSON**")
            personas_upload = st.file_uploader(
                "Upload personas file",
                type=['json'],
                key="personas_upload",
                help="JSON file with persona definitions"
            )

            if personas_upload:
                st.success(f"✓ {personas_upload.name}")

        with col2:
            st.markdown("**Keywords CSV**")
            keywords_upload = st.file_uploader(
                "Upload keywords file",
                type=['csv'],
                key="keywords_upload",
                help="CSV file with keywords and intent types"
            )

            if keywords_upload:
                st.success(f"✓ {keywords_upload.name}")

        st.markdown("---")

        # Save button
        if st.button("💾 Add Client", type="primary", use_container_width=True):
            if not new_client_name:
                st.error("Please enter a client name.")
            elif not personas_upload or not keywords_upload:
                st.error("Please upload both personas and keywords files.")
            else:
                try:
                    # Create slug from client name
                    client_slug = new_client_name.lower().replace(' ', '_')
                    client_slug = re.sub(r'[^a-z0-9_]', '', client_slug)

                    # Save files to data directory
                    data_dir = Path('data')
                    data_dir.mkdir(exist_ok=True)

                    personas_path = data_dir / f"{client_slug}_personas.json"
                    keywords_path = data_dir / f"{client_slug}_keywords.csv"

                    # Write personas file
                    with open(personas_path, 'wb') as f:
                        f.write(personas_upload.getvalue())

                    # Write keywords file
                    with open(keywords_path, 'wb') as f:
                        f.write(keywords_upload.getvalue())

                    st.success(f"✅ {new_client_name} added successfully!")
                    st.balloons()

                    # Auto-activate the new client
                    st.session_state.active_client = client_slug
                    st.session_state.generation_config.update({
                        'personas_file': str(personas_path),
                        'keywords_file': str(keywords_path),
                        'client_name': new_client_name
                    })

                    st.info("🔄 Refreshing to show new client...")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error adding client: {str(e)}")
                    st.exception(e)

    # Help Section
    with st.expander("❓ Help & File Formats"):
        st.markdown("""
        ### How to Use Client Manager

        **Selecting a Client:**
        1. Browse available clients in the "Available Clients" section
        2. Click "Activate [Client Name]" to select them
        3. The active client will show at the top with a gold border
        4. Go to "Generate" to create prompts for the active client

        **Adding a New Client:**
        1. Click "Add New Client" to expand the wizard
        2. Enter the client's brand name
        3. Upload their personas JSON file
        4. Upload their keywords CSV file
        5. Click "Add Client" - it will be activated automatically!

        **File Format Requirements:**

        **Personas JSON** should look like:
        ```json
        {
          "personas": [
            {
              "id": "persona_1",
              "name": "Luxury Beauty Enthusiast",
              "weight": 0.3,
              "description": "...",
              "priority_topics": ["luxury makeup", "high-end cosmetics"]
            }
          ]
        }
        ```

        **Keywords CSV** should have columns:
        - `keyword`: The search term
        - `intent_type`: transactional, informational, navigational, or commercial
        - `search_volume`: Monthly search volume (optional)
        - `competitor_brands`: Comma-separated list (optional)

        Example:
        ```
        keyword,intent_type,search_volume,competitor_brands
        best luxury eyeshadow,commercial,5000,"Pat McGrath,Natasha Denona"
        how to apply eyeshadow,informational,8000,
        ```
        """)
