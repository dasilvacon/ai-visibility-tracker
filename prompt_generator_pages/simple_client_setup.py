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
    """Render simplified client setup."""
    st.markdown(f"""
    <div style='background-color: {DARK_PURPLE}; padding: 20px; border-radius: 8px; border-left: 4px solid {CREAM}; margin-bottom: 24px;'>
        <h3 style='color: white; margin-top: 0;'>✨ Simple Client Setup</h3>
        <p style='color: {OFF_WHITE}; margin-bottom: 12px;'>
            Just upload your keyword files - we'll handle the rest!
        </p>
        <ul style='color: {OFF_WHITE}; margin: 0;'>
            <li><strong>Ahrefs organic keywords?</strong> Upload as-is ✓</li>
            <li><strong>Link building keywords?</strong> Upload as-is ✓</li>
            <li><strong>Any CSV with keywords?</strong> Upload as-is ✓</li>
        </ul>
        <p style='color: {CREAM}; margin: 12px 0 0 0; font-size: 0.9em;'>
            No formatting, no JSON files, no technical setup required.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Client name
    st.markdown(f"<h3 style='color: white;'>Step 1: Client Name</h3>", unsafe_allow_html=True)
    new_client_name = st.text_input(
        "Client/Brand Name",
        placeholder="e.g., Rare Beauty, Acme Corp",
        help="Enter the client's brand name",
        key="simple_client_name"
    )

    # Keyword uploads
    st.markdown(f"<h3 style='color: white; margin-top: 24px;'>Step 2: Upload Keywords</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    <p style='color: {CREAM}; margin-bottom: 16px;'>
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

                    st.success(f"✅ {new_client_name} created successfully!")
                    st.balloons()

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
