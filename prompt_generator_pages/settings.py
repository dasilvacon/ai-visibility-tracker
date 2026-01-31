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
    # Custom CSS to improve text visibility in forms
    st.markdown(f"""
    <style>
        /* Override label colors for better contrast */
        .stTextInput label, .stFileUploader label {{
            color: {OFF_WHITE} !important;
            font-weight: 600 !important;
        }}

        /* File uploader text */
        .stFileUploader p {{
            color: {OFF_WHITE} !important;
        }}

        /* Drag and drop text */
        [data-testid="stFileUploadDropzone"] {{
            color: {OFF_WHITE} !important;
        }}

        [data-testid="stFileUploadDropzone"] small {{
            color: {CREAM} !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.title("🎯 Client Manager")

    # Helpful intro section
    st.markdown(f"""
    <div style='background-color: {DARK_PURPLE}; padding: 20px; border-radius: 8px; border-left: 4px solid {CREAM}; margin-bottom: 24px;'>
        <h3 style='color: white; margin-top: 0;'>📋 What is Client Manager?</h3>
        <p style='color: {OFF_WHITE}; margin-bottom: 12px;'>
            This is where you <strong>set up clients for AI visibility tracking</strong>. Each client needs two files
            that define WHO searches for them and WHAT they search for:
        </p>
        <ul style='color: {OFF_WHITE};'>
            <li><strong>Personas JSON</strong> - Target audience profiles (who searches for this client's products)</li>
            <li><strong>Keywords CSV</strong> - Search terms and intent types (what people actually search)</li>
        </ul>
        <div style='background-color: rgba(232, 215, 160, 0.15); padding: 12px; border-radius: 6px; margin-top: 16px;'>
            <p style='color: {CREAM}; margin: 0;'>
                <strong>Workflow:</strong> Add client here → Generate initial prompts → Export → Track monthly in Main Dashboard
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize active client in session state
    if 'active_client' not in st.session_state:
        st.session_state.active_client = None

    # Auto-detect clients
    clients = detect_clients()

    # Active Client Section
    st.markdown("## 🌟 Active Client")
    st.markdown(f"<p style='color: {CREAM}; margin-bottom: 16px;'>This is the client you're currently working with. All prompts will be generated for this client.</p>", unsafe_allow_html=True)

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
        st.markdown(f"""
        <div style='background-color: {DARK_PURPLE}; padding: 24px; border-radius: 12px; border: 2px dashed {CREAM}; text-align: center;'>
            <h3 style='color: {CREAM}; margin: 0;'>👆 No Client Selected</h3>
            <p style='color: {OFF_WHITE}; margin: 12px 0 0 0;'>
                Choose a client from the "Available Clients" section below, or add a new one to get started.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Available Clients Section
    st.markdown("## 📋 Available Clients")
    st.markdown(f"<p style='color: {CREAM}; margin-bottom: 16px;'>Click on a client card to activate them for prompt generation.</p>", unsafe_allow_html=True)

    if not clients:
        st.warning("⚠️ No clients found. Add a new client below to get started.")
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

    # Tab for simple vs advanced setup
    setup_tab1, setup_tab2 = st.tabs(["✨ Simple Setup (Recommended)", "🔧 Advanced Setup"])

    with setup_tab1:
        from prompt_generator_pages import simple_client_setup
        simple_client_setup.render_simple_setup()

    with setup_tab2:
        st.markdown(f"""
        <div style='background-color: rgba(255,165,0,0.1); padding: 12px; border-radius: 6px; border-left: 3px solid orange; margin-bottom: 16px;'>
            <p style='color: {OFF_WHITE}; margin: 0; font-size: 0.9em;'>
                ⚠️ <strong>Advanced users only:</strong> Use this if you need to manually create JSON personas or have specific file requirements.
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📤 Manual Setup", expanded=False):
            # Instructions
            st.markdown(f"""
            <div style='background-color: rgba(255,255,255,0.05); padding: 16px; border-radius: 6px; margin-bottom: 20px;'>
            <p style='color: {OFF_WHITE}; margin: 0;'>
                <strong>📝 Instructions:</strong> Enter your client's name and upload both required files.
                The tool will automatically detect and activate the new client.
            </p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<h3 style='color: white;'>Client Information</h3>", unsafe_allow_html=True)

            new_client_name = st.text_input(
            "Client Name",
            placeholder="e.g., Rare Beauty, Fenty Beauty",
            help="Enter the client's brand name exactly as it should appear"
            )

            st.markdown("<h3 style='color: white;'>Upload Files</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: {CREAM}; font-size: 0.9em; margin-bottom: 16px;'>Both files are required. Click 'Browse files' or drag and drop.</p>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
            st.markdown(f"<p style='color: {OFF_WHITE}; font-weight: 600; font-size: 0.95em; margin-bottom: 8px;'>Personas JSON</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: {OFF_WHITE}; font-size: 0.85em; margin-bottom: 8px;'>Upload personas file</p>", unsafe_allow_html=True)
            personas_upload = st.file_uploader(
                "personas",
                type=['json'],
                key="personas_upload",
                help="JSON file with persona definitions",
                label_visibility="collapsed"
            )

            if personas_upload:
                st.success(f"✓ {personas_upload.name}")

            with col2:
            st.markdown(f"<p style='color: {OFF_WHITE}; font-weight: 600; font-size: 0.95em; margin-bottom: 8px;'>Keywords CSV</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: {OFF_WHITE}; font-size: 0.85em; margin-bottom: 8px;'>Upload keywords file</p>", unsafe_allow_html=True)
            keywords_upload = st.file_uploader(
                "keywords",
                type=['csv'],
                key="keywords_upload",
                help="CSV file with keywords and intent types",
                label_visibility="collapsed"
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

            st.markdown("---")

    # Help Section
    with st.expander("❓ Help & Quick Start Guide"):
        st.markdown(f"""
        <h3 style='color: white;'>📚 Quick Start: Adding Your First Client</h3>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background-color: {DARK_PURPLE}; padding: 20px; border-radius: 6px; margin-bottom: 20px;'>
            <h4 style='color: {CREAM}; margin-top: 0;'>✨ Simple Setup (Recommended)</h4>

            <p style='color: {OFF_WHITE};'><strong>What you need:</strong></p>
            <ul style='color: {OFF_WHITE};'>
                <li>Client's brand name</li>
                <li>Keyword file(s) - any of these work:
                    <ul>
                        <li><strong>Ahrefs organic keywords export</strong> (CSV)</li>
                        <li><strong>Link building target keywords</strong> (CSV/Excel)</li>
                        <li><strong>Any spreadsheet with keywords</strong> in any column</li>
                    </ul>
                </li>
            </ul>

            <p style='color: {OFF_WHITE};'><strong>Steps:</strong></p>
            <ol style='color: {OFF_WHITE};'>
                <li>Go to "Simple Setup" tab above</li>
                <li>Enter client name</li>
                <li>Upload your keyword file(s) - no formatting needed!</li>
                <li>Preview the detected keywords</li>
                <li>Click "Create Client"</li>
                <li>Done! Personas are auto-generated</li>
            </ol>

            <p style='color: {CREAM}; margin: 16px 0 0 0;'>
                💡 <strong>No JSON files, no reformatting, no technical setup!</strong>
            </p>
        </div>

        <div style='background-color: rgba(255,255,255,0.05); padding: 16px; border-radius: 6px; margin-bottom: 20px;'>
            <h4 style='color: {CREAM}; margin-top: 0;'>🎯 After Setup</h4>

            <p style='color: {OFF_WHITE};'><strong>Selecting a Client:</strong></p>
            <ul style='color: {OFF_WHITE};'>
                <li>Browse available clients in "Available Clients" section</li>
                <li>Click "Activate [Client Name]"</li>
                <li>Active client shows at top with gold border</li>
                <li>Go to "Generate" page to create prompts</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <h4 style='color: {CREAM};'>📄 Supported File Formats</h4>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background-color: rgba(232, 215, 160, 0.15); padding: 16px; border-radius: 6px; margin-bottom: 20px;'>
            <h5 style='color: white; margin-top: 0;'>✅ What Files Can You Upload?</h5>
            <p style='color: {OFF_WHITE}; margin-bottom: 12px;'><strong>Simple Setup accepts:</strong></p>
            <ul style='color: {OFF_WHITE};'>
                <li><strong>Ahrefs exports</strong> - Organic keywords, top pages, etc.</li>
                <li><strong>Link building keywords</strong> - Your target keyword spreadsheets</li>
                <li><strong>SEMrush exports</strong> - Keyword research data</li>
                <li><strong>Custom keyword lists</strong> - Any CSV/Excel with keywords</li>
            </ul>
            <p style='color: {CREAM}; margin: 12px 0 0 0;'>
                💡 We auto-detect keyword columns regardless of name or order!
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<h5 style='color: white;'>Example: Ahrefs Organic Keywords Export</h5>", unsafe_allow_html=True)
        st.code("""
Keyword,Position,Search Volume,KD,Traffic,CPC
best luxury eyeshadow,5,5000,45,250,2.50
natasha denona review,12,2500,25,120,1.80
luxury makeup brands,8,8000,60,400,3.20
        """, language="csv")
        st.markdown(f"<p style='color: {CREAM}; font-size: 0.85em;'>✅ Simple Setup will detect 'Keyword' column and 'Search Volume' automatically</p>", unsafe_allow_html=True)

        st.markdown(f"<h5 style='color: white; margin-top: 20px;'>Example: Your Link Building Keywords</h5>", unsafe_allow_html=True)
        st.code("""
Target Keywords,Priority,Notes
buy natasha denona online,High,Ecommerce focus
natasha denova palette,Medium,Typo variant
best eyeshadow for mature skin,High,Demographic target
        """, language="csv")
        st.markdown(f"<p style='color: {CREAM}; font-size: 0.85em;'>✅ Simple Setup will detect 'Target Keywords' column, ignore other columns</p>", unsafe_allow_html=True)

        st.markdown(f"<h5 style='color: white; margin-top: 20px;'>Example: Basic Keyword List</h5>", unsafe_allow_html=True)
        st.code("""
Search Terms
natasha denona biba palette
how to apply eyeshadow
luxury makeup tutorial
best high-end eyeshadow
        """, language="csv")
        st.markdown(f"<p style='color: {CREAM}; font-size: 0.85em;'>✅ Simple Setup will detect this single-column format too!</p>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background-color: {DARK_PURPLE}; padding: 16px; border-radius: 6px; margin-top: 20px;'>
            <h5 style='color: {CREAM}; margin-top: 0;'>🔍 Intent Types Explained:</h5>
            <ul style='color: {OFF_WHITE};'>
                <li><strong>Transactional:</strong> Ready to buy (e.g., "buy eyeshadow", "natasha denona sale")</li>
                <li><strong>Informational:</strong> Learning/researching (e.g., "how to apply eyeshadow", "best makeup tips")</li>
                <li><strong>Navigational:</strong> Looking for specific brand/page (e.g., "natasha denona website", "sephora natasha denona")</li>
                <li><strong>Commercial:</strong> Comparing options (e.g., "best luxury eyeshadow", "natasha denona vs urban decay")</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background-color: rgba(232, 215, 160, 0.1); padding: 16px; border-radius: 6px; margin-top: 20px; border-left: 4px solid {CREAM};'>
            <h5 style='color: white; margin-top: 0;'>✨ What Gets Generated?</h5>
            <p style='color: {OFF_WHITE};'>
                Once you activate a client and go to "Generate", the tool will create AI-optimized prompts like:
            </p>
            <p style='color: {CREAM}; font-style: italic; margin: 12px 0;'>
                "Best luxury eyeshadow palettes for mature skin - high-end brands like Natasha Denona with creamy, blendable formulas"
            </p>
            <p style='color: {OFF_WHITE};'>
                Each prompt combines your keywords with persona insights to match how real people search.
            </p>
        </div>
        """, unsafe_allow_html=True)
