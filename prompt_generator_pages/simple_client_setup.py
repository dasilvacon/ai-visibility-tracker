"""
Simple Client Setup - No technical knowledge required
Accepts Ahrefs exports, keyword lists, link building targets, etc.
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import re


# Brand colors
DARK_PURPLE = '#4A4458'
CREAM = '#E8D7A0'
OFF_WHITE = '#FBFBEF'


def detect_keyword_column(df):
    """Auto-detect which column contains keywords."""
    # Common column names for keywords
    keyword_columns = [
        'keyword', 'keywords', 'search term', 'search_term', 'query',
        'search query', 'term', 'keyphrase', 'key phrase'
    ]

    # Check for exact matches (case-insensitive)
    for col in df.columns:
        if col.lower() in keyword_columns:
            return col

    # Check for partial matches
    for col in df.columns:
        for kw_col in keyword_columns:
            if kw_col in col.lower():
                return col

    # If no match, use first column
    return df.columns[0]


def detect_volume_column(df):
    """Auto-detect which column contains search volume."""
    volume_columns = [
        'volume', 'search volume', 'searches', 'monthly searches',
        'search_volume', 'monthly_searches', 'vol'
    ]

    for col in df.columns:
        col_lower = col.lower()
        for vol_col in volume_columns:
            if vol_col in col_lower:
                return col

    return None


def infer_intent_type(keyword):
    """Infer intent type from keyword."""
    keyword_lower = keyword.lower()

    # Transactional keywords
    transactional_words = ['buy', 'purchase', 'order', 'shop', 'discount', 'coupon', 'deal', 'sale', 'price']
    if any(word in keyword_lower for word in transactional_words):
        return 'transactional'

    # Navigational keywords
    navigational_words = ['website', 'official site', 'login', 'near me', 'store']
    if any(word in keyword_lower for word in navigational_words):
        return 'navigational'

    # Informational keywords
    informational_words = ['how', 'what', 'why', 'when', 'guide', 'tutorial', 'tips', 'learn', 'review']
    if any(word in keyword_lower for word in informational_words):
        return 'informational'

    # Default to commercial
    return 'commercial'


def parse_keyword_file(uploaded_file):
    """Parse uploaded keyword file and standardize format."""
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)

        # Detect keyword column
        keyword_col = detect_keyword_column(df)

        # Detect volume column
        volume_col = detect_volume_column(df)

        # Create standardized dataframe
        standardized = pd.DataFrame()
        standardized['keyword'] = df[keyword_col]

        # Add search volume if found
        if volume_col:
            standardized['search_volume'] = df[volume_col]
        else:
            standardized['search_volume'] = 0

        # Infer intent type
        standardized['intent_type'] = standardized['keyword'].apply(infer_intent_type)

        # Add empty competitor_brands column
        standardized['competitor_brands'] = ''

        # Remove any empty keywords
        standardized = standardized[standardized['keyword'].notna()]
        standardized = standardized[standardized['keyword'].str.strip() != '']

        return standardized, keyword_col, volume_col

    except Exception as e:
        st.error(f"Error parsing file: {str(e)}")
        return None, None, None


def generate_default_personas(client_name, keywords_df):
    """Auto-generate basic personas from keywords."""
    # Analyze keywords to determine personas
    total_keywords = len(keywords_df)

    # Count intent types
    intent_counts = keywords_df['intent_type'].value_counts()

    personas = []

    # Persona 1: Based on dominant intent
    if 'commercial' in intent_counts.index or 'transactional' in intent_counts.index:
        personas.append({
            "id": "persona_buyer",
            "name": "Active Buyer",
            "weight": 0.4,
            "description": f"Consumers actively researching and ready to purchase {client_name} products",
            "priority_topics": ["product comparisons", "reviews", "pricing", "best options"]
        })

    # Persona 2: Information seeker
    if 'informational' in intent_counts.index:
        personas.append({
            "id": "persona_researcher",
            "name": "Information Seeker",
            "weight": 0.35,
            "description": f"People learning about {client_name} products and how to use them",
            "priority_topics": ["how to", "guides", "tutorials", "tips"]
        })

    # Persona 3: Brand explorer
    personas.append({
        "id": "persona_explorer",
        "name": "Brand Explorer",
        "weight": 0.25,
        "description": f"Users discovering {client_name} and comparing with alternatives",
        "priority_topics": ["brand information", "alternatives", "comparisons"]
    })

    # Normalize weights
    total_weight = sum(p['weight'] for p in personas)
    for p in personas:
        p['weight'] = round(p['weight'] / total_weight, 2)

    return {"personas": personas}


def render_simple_setup():
    """Render simplified client setup with tabbed interface."""
    st.markdown(f"""
    <div style='background-color: {DARK_PURPLE}; padding: 20px; border-radius: 8px; border-left: 4px solid {CREAM}; margin-bottom: 24px;'>
        <h3 style='color: white; margin-top: 0;'>✨ Simple Client Setup</h3>
        <p style='color: {OFF_WHITE}; margin-bottom: 12px;'>
            Create a new client with comprehensive information for AI visibility tracking.
        </p>
        <ul style='color: {OFF_WHITE}; margin: 0;'>
            <li><strong>Basic Info:</strong> Name, website, description</li>
            <li><strong>Business Goals:</strong> Revenue targets, positioning strategy</li>
            <li><strong>Keywords:</strong> Upload Ahrefs exports or any keyword CSVs</li>
            <li><strong>Competitors:</strong> Categorize direct, adjacent, and aspirational competitors</li>
        </ul>
        <p style='color: {CREAM}; margin: 12px 0 0 0; font-size: 0.9em;'>
            Complete the tabs below - you can skip competitors and add them later via Edit Client.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session state for client data
    if 'new_client_data' not in st.session_state:
        st.session_state.new_client_data = {
            'name': '',
            'website': '',
            'description': '',
            'business_goals': {
                'revenue_targets': '',
                'market_positioning': '',
                'target_metrics': '',
                'freeform_notes': ''
            },
            'competitors': []
        }

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "1️⃣ Basic Info",
        "2️⃣ Business Goals",
        "3️⃣ Keywords",
        "4️⃣ Competitors (Optional)"
    ])

    # TAB 1: BASIC INFO
    with tab1:
        st.markdown(f"<h3 style='color: {CREAM};'>Basic Client Information</h3>", unsafe_allow_html=True)

        new_client_name = st.text_input(
            "Client/Brand Name *",
            placeholder="e.g., Rare Beauty, Natasha Denona",
            help="Enter the client's brand name",
            value=st.session_state.new_client_data['name'],
            key="setup_client_name"
        )
        st.session_state.new_client_data['name'] = new_client_name

        website = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            help="The client's primary website URL",
            value=st.session_state.new_client_data['website'],
            key="setup_website"
        )
        st.session_state.new_client_data['website'] = website

        description = st.text_area(
            "Brand Description",
            placeholder="e.g., Luxury makeup brand specializing in high-end eyeshadow palettes...",
            help="A brief 2-3 sentence description of the brand",
            value=st.session_state.new_client_data['description'],
            height=100,
            key="setup_description"
        )
        st.session_state.new_client_data['description'] = description

        if new_client_name:
            st.success(f"✓ Basic info for {new_client_name}")
        else:
            st.info("👆 Please fill in at least the client name to continue")

    # TAB 2: BUSINESS GOALS
    with tab2:
        st.markdown(f"<h3 style='color: {CREAM};'>Business Goals & Strategy</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: {OFF_WHITE}; margin-bottom: 16px;'>Help us understand what this client wants to achieve with AI visibility.</p>", unsafe_allow_html=True)

        revenue_targets = st.text_input(
            "Revenue/Growth Targets for 2026",
            placeholder="e.g., Increase online sales by 30%, Reach $5M in AI-influenced revenue",
            help="What are the client's revenue or growth objectives?",
            value=st.session_state.new_client_data['business_goals']['revenue_targets'],
            key="setup_revenue"
        )
        st.session_state.new_client_data['business_goals']['revenue_targets'] = revenue_targets

        market_positioning = st.text_input(
            "How do they want to be positioned in AI responses?",
            placeholder="e.g., Premium luxury beauty leader, Affordable eco-friendly alternative",
            help="Their desired market position when AI tools recommend them",
            value=st.session_state.new_client_data['business_goals']['market_positioning'],
            key="setup_positioning"
        )
        st.session_state.new_client_data['business_goals']['market_positioning'] = market_positioning

        target_metrics = st.text_area(
            "What metrics matter most to them?",
            placeholder="e.g.,\n- AI visibility rate >60%\n- Top 3 in luxury eyeshadow category\n- Featured in ChatGPT product recommendations",
            help="List the key success metrics they're tracking (one per line)",
            value=st.session_state.new_client_data['business_goals']['target_metrics'],
            height=100,
            key="setup_metrics"
        )
        st.session_state.new_client_data['business_goals']['target_metrics'] = target_metrics

        freeform_notes = st.text_area(
            "Additional Strategy Notes (Optional)",
            placeholder="Any other context about their business strategy, target audience, or competitive positioning...",
            help="Freeform notes about their strategy",
            value=st.session_state.new_client_data['business_goals']['freeform_notes'],
            height=120,
            key="setup_notes"
        )
        st.session_state.new_client_data['business_goals']['freeform_notes'] = freeform_notes

        if any([revenue_targets, market_positioning, target_metrics, freeform_notes]):
            st.success("✓ Business goals captured")

    # TAB 3: KEYWORDS
    with tab3:
        st.markdown(f"<h3 style='color: {CREAM};'>Upload Keywords</h3>", unsafe_allow_html=True)
        st.markdown(f"""
        <p style='color: {OFF_WHITE}; margin-bottom: 16px;'>
            Upload one or more keyword files. We'll combine them automatically.
        </p>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"<p style='color: {OFF_WHITE}; font-weight: 600;'>Primary Keywords</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: {CREAM}; font-size: 0.85em; margin-bottom: 8px;'>Ahrefs export, organic keywords, etc.</p>", unsafe_allow_html=True)
        primary_keywords = st.file_uploader(
            "primary",
            type=['csv', 'xlsx'],
            key="simple_primary_keywords",
            label_visibility="collapsed"
        )

    with col2:
        st.markdown(f"<p style='color: {OFF_WHITE}; font-weight: 600;'>Additional Keywords (Optional)</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: {CREAM}; font-size: 0.85em; margin-bottom: 8px;'>Link building targets, campaign keywords, etc.</p>", unsafe_allow_html=True)
        secondary_keywords = st.file_uploader(
            "secondary",
            type=['csv', 'xlsx'],
            key="simple_secondary_keywords",
            label_visibility="collapsed"
        )

    # Preview uploaded files
    if primary_keywords or secondary_keywords:
        st.markdown(f"<h3 style='color: white; margin-top: 24px;'>Step 3: Preview & Confirm</h3>", unsafe_allow_html=True)

        all_keywords = []

        # Parse primary keywords
        if primary_keywords:
            with st.expander(f"📄 Preview: {primary_keywords.name}", expanded=True):
                parsed_df, kw_col, vol_col = parse_keyword_file(primary_keywords)

                if parsed_df is not None:
                    st.success(f"✓ Detected {len(parsed_df)} keywords")
                    st.info(f"📌 Keyword column: **{kw_col}**" + (f" | Volume column: **{vol_col}**" if vol_col else " | No volume column found"))

                    # Show intent breakdown
                    intent_counts = parsed_df['intent_type'].value_counts()
                    st.markdown(f"<p style='color: {OFF_WHITE};'><strong>Intent breakdown:</strong></p>", unsafe_allow_html=True)
                    for intent, count in intent_counts.items():
                        st.markdown(f"- {intent}: {count}")

                    # Show sample
                    st.dataframe(parsed_df.head(10), use_container_width=True)

                    all_keywords.append(parsed_df)

        # Parse secondary keywords
        if secondary_keywords:
            with st.expander(f"📄 Preview: {secondary_keywords.name}", expanded=True):
                parsed_df, kw_col, vol_col = parse_keyword_file(secondary_keywords)

                if parsed_df is not None:
                    st.success(f"✓ Detected {len(parsed_df)} keywords")
                    st.info(f"📌 Keyword column: **{kw_col}**" + (f" | Volume column: **{vol_col}**" if vol_col else " | No volume column found"))

                    # Show intent breakdown
                    intent_counts = parsed_df['intent_type'].value_counts()
                    st.markdown(f"<p style='color: {OFF_WHITE};'><strong>Intent breakdown:</strong></p>", unsafe_allow_html=True)
                    for intent, count in intent_counts.items():
                        st.markdown(f"- {intent}: {count}")

                    # Show sample
                    st.dataframe(parsed_df.head(10), use_container_width=True)

                    all_keywords.append(parsed_df)

    # TAB 4: COMPETITORS
    with tab4:
        st.markdown(f"<h3 style='color: {CREAM};'>Competitor Tracking (Optional)</h3>", unsafe_allow_html=True)
        st.markdown(f"""
        <p style='color: {OFF_WHITE}; margin-bottom: 16px;'>
            Add competitors to track in AI responses. You can categorize them and skip this step to add competitors later via Edit Client.
        </p>
        """, unsafe_allow_html=True)

        # Category explanations
        with st.expander("ℹ️ What do these categories mean?"):
            st.markdown(f"""
            - **Direct:** Head-to-head competitors in the same market segment
            - **Adjacent:** Overlapping products/audience but different positioning
            - **Aspirational:** Brands you aspire to compete with or learn from
            """)

        # Add competitor form
        st.markdown(f"<p style='color: {CREAM}; font-weight: 600;'>Add Competitor</p>", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            comp_name = st.text_input(
                "Competitor Name",
                placeholder="e.g., Pat McGrath Labs",
                key="comp_name"
            )

        with col2:
            comp_category = st.selectbox(
                "Category",
                options=["Direct", "Adjacent", "Aspirational"],
                key="comp_category"
            )

        comp_website = st.text_input(
            "Website (Optional)",
            placeholder="https://competitor.com",
            key="comp_website"
        )

        comp_notes = st.text_area(
            "Notes (Optional)",
            placeholder="Why are you tracking this competitor? What makes them relevant?",
            height=80,
            key="comp_notes"
        )

        if st.button("➕ Add Competitor", key="add_comp"):
            if comp_name:
                # Check for duplicates
                if any(c['name'].lower() == comp_name.lower() for c in st.session_state.new_client_data['competitors']):
                    st.warning(f"⚠️ {comp_name} is already in your competitor list")
                else:
                    st.session_state.new_client_data['competitors'].append({
                        'name': comp_name,
                        'website': comp_website,
                        'category': comp_category.lower(),
                        'notes': comp_notes
                    })
                    st.success(f"✅ Added {comp_name} as {comp_category} competitor")
                    st.rerun()
            else:
                st.warning("Please enter a competitor name")

        # Display added competitors
        if st.session_state.new_client_data['competitors']:
            st.markdown("---")
            st.markdown(f"<p style='color: {CREAM}; font-weight: 600;'>Added Competitors ({len(st.session_state.new_client_data['competitors'])})</p>", unsafe_allow_html=True)

            for i, comp in enumerate(st.session_state.new_client_data['competitors']):
                col1, col2 = st.columns([4, 1])

                with col1:
                    category_emoji = {"direct": "🎯", "adjacent": "🔄", "aspirational": "⭐"}
                    emoji = category_emoji.get(comp['category'], "📊")

                    st.markdown(f"""
                    <div style='background-color: rgba(74, 68, 88, 0.5); padding: 12px; border-radius: 6px; margin-bottom: 8px;'>
                        <p style='color: white; margin: 0; font-weight: 600;'>{emoji} {comp['name']} <span style='color: {CREAM};'>({comp['category'].title()})</span></p>
                        {f"<p style='color: {CREAM}; margin: 4px 0 0 0; font-size: 0.85em;'>{comp['notes']}</p>" if comp['notes'] else ""}
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    if st.button("Remove", key=f"remove_comp_{i}"):
                        st.session_state.new_client_data['competitors'].pop(i)
                        st.rerun()
        else:
            st.info("No competitors added yet. You can skip this step and add competitors later via Edit Client.")

    # SAVE SECTION (outside tabs)
    st.markdown("---")
    st.markdown(f"<h3 style='color: white;'>Ready to Create Client?</h3>", unsafe_allow_html=True)

    # Preview uploaded files
    if (primary_keywords or secondary_keywords) and new_client_name:
        all_keywords = []

        # Parse primary keywords
        if primary_keywords:
            parsed_df, kw_col, vol_col = parse_keyword_file(primary_keywords)
            if parsed_df is not None:
                all_keywords.append(parsed_df)

        # Parse secondary keywords
        if secondary_keywords:
            parsed_df, kw_col, vol_col = parse_keyword_file(secondary_keywords)
            if parsed_df is not None:
                all_keywords.append(parsed_df)

        # Combine and save
        if all_keywords and new_client_name:
            # Combine all keyword dataframes
            combined_df = pd.concat(all_keywords, ignore_index=True)

            # Remove duplicates
            original_count = len(combined_df)
            combined_df = combined_df.drop_duplicates(subset=['keyword'])
            final_count = len(combined_df)

            if original_count > final_count:
                st.info(f"ℹ️ Removed {original_count - final_count} duplicate keywords")

            st.success(f"✅ Ready to create client with {final_count} unique keywords")

            # Save button
            if st.button("💾 Create Client", type="primary", use_container_width=True, key="simple_save"):
                try:
                    # Import BrandConfigManager
                    import sys
                    sys.path.insert(0, 'src')
                    from src.data.brand_config_manager import BrandConfigManager

                    # Create slug
                    client_slug = new_client_name.lower().replace(' ', '_')
                    client_slug = re.sub(r'[^a-z0-9_]', '', client_slug)

                    # Save keywords CSV
                    data_dir = Path('data')
                    data_dir.mkdir(exist_ok=True)

                    keywords_path = data_dir / f"{client_slug}_keywords.csv"
                    combined_df.to_csv(keywords_path, index=False)

                    # Generate and save personas
                    personas_data = generate_default_personas(new_client_name, combined_df)
                    personas_path = data_dir / f"{client_slug}_personas.json"

                    with open(personas_path, 'w') as f:
                        json.dump(personas_data, f, indent=2)

                    # Create brand_config.json with BrandConfigManager
                    manager = BrandConfigManager()

                    # Parse target metrics from text area (newline-separated)
                    target_metrics = []
                    if st.session_state.new_client_data['business_goals']['target_metrics']:
                        metrics_text = st.session_state.new_client_data['business_goals']['target_metrics']
                        target_metrics = [m.strip() for m in metrics_text.split('\n') if m.strip()]

                    # Create config
                    config = manager.create_default_config(
                        brand_name=new_client_name,
                        website=st.session_state.new_client_data['website'],
                        description=st.session_state.new_client_data['description'],
                        aliases=[]
                    )

                    # Add business goals
                    config['brand']['business_goals'] = {
                        'revenue_targets': st.session_state.new_client_data['business_goals']['revenue_targets'],
                        'market_positioning': st.session_state.new_client_data['business_goals']['market_positioning'],
                        'target_metrics': target_metrics,
                        'freeform_notes': st.session_state.new_client_data['business_goals']['freeform_notes']
                    }

                    # Add competitors
                    from datetime import datetime
                    for comp in st.session_state.new_client_data['competitors']:
                        config['competitors']['expected'].append({
                            'name': comp['name'],
                            'website': comp['website'],
                            'category': comp['category'],
                            'added_date': datetime.utcnow().strftime('%Y-%m-%d'),
                            'notes': comp['notes']
                        })

                    # Save brand config
                    brand_config_path = data_dir / f"{client_slug}_brand_config.json"
                    manager.save_config(str(brand_config_path), config)

                    st.success(f"✅ {new_client_name} created successfully!")
                    st.balloons()

                    # Clear session data
                    st.session_state.new_client_data = {
                        'name': '',
                        'website': '',
                        'description': '',
                        'business_goals': {
                            'revenue_targets': '',
                            'market_positioning': '',
                            'target_metrics': '',
                            'freeform_notes': ''
                        },
                        'competitors': []
                    }

                    # Auto-activate
                    st.session_state.active_client = client_slug
                    st.session_state.generation_config.update({
                        'personas_file': str(personas_path),
                        'keywords_file': str(keywords_path),
                        'client_name': new_client_name
                    })

                    st.info("🔄 Refreshing...")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error creating client: {str(e)}")
                    st.exception(e)

        elif not new_client_name:
            st.warning("⚠️ Please enter a client name above")
