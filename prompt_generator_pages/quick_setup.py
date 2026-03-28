"""
Quick Setup — streamlined client onboarding.

Enter a client name and domain → auto-pull keywords + competitors from Ahrefs
→ review with filters → create client. Under 2 minutes.

Falls back to CSV upload if Ahrefs API key isn't configured.
"""

import streamlit as st
import pandas as pd
import json
import re
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'src')

from src.client_manager.auto_onboard import ClientAutoOnboarder
from src.client_manager.ahrefs_client import AhrefsClient
from src.client_manager.client_registry import ClientRegistry


# Brand colors - LIGHT THEME
BACKGROUND = '#FFFFFF'
TEXT_COLOR = '#000000'
LIGHT_BG = '#F5F5F5'
BORDER = '#CCCCCC'
ACCENT = '#4A4458'
SUCCESS = '#2E7D32'
WARNING = '#F57C00'


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
        .setup-card {{
            background: {LIGHT_BG};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
        }}
        .metric-badge {{
            display: inline-block;
            background: {ACCENT};
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            margin: 2px;
        }}
        .keyword-row {{
            padding: 6px 0;
            border-bottom: 1px solid {BORDER};
        }}
        .step-header {{
            background: linear-gradient(135deg, {ACCENT} 0%, #5a5468 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            margin: 15px 0 10px 0;
        }}
        .step-header h3 {{ color: white !important; margin: 0; }}
    </style>
    """, unsafe_allow_html=True)


def _clean_domain(domain: str) -> str:
    """Clean a domain input — strip protocol, www, trailing slashes."""
    domain = domain.strip()
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    domain = domain.rstrip('/')
    return domain


def _init_session_state():
    """Initialize session state for quick setup."""
    defaults = {
        'qs_step': 'input',          # input → review → done
        'qs_client_name': '',
        'qs_domain': '',
        'qs_country': 'ca',
        'qs_description': '',
        'qs_keywords_data': [],       # raw Ahrefs keyword dicts
        'qs_keywords_selected': {},   # keyword -> True/False
        'qs_competitors_data': [],    # raw Ahrefs competitor dicts
        'qs_competitors_selected': {},# domain -> True/False
        'qs_personas': [],            # auto-generated persona dicts
        'qs_source': 'ahrefs',        # 'ahrefs' or 'csv'
        'qs_filter_text': '',
        'qs_filter_intent': 'All',
        'qs_min_volume': 0,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def _render_input_step():
    """Render the initial input form: name + domain."""
    st.markdown("""
    <div class='step-header'>
        <h3>Step 1 — Tell me about the client</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        client_name = st.text_input(
            "Client name",
            value=st.session_state.qs_client_name,
            placeholder="e.g., Ontario Caregiver Organization",
            key="qs_name_input"
        )
    with col2:
        domain = st.text_input(
            "Domain",
            value=st.session_state.qs_domain,
            placeholder="e.g., ontariocaregiver.ca",
            key="qs_domain_input"
        )

    col3, col4 = st.columns(2)
    with col3:
        country = st.selectbox(
            "Primary market",
            options=['ca', 'us', 'gb', 'au', 'global'],
            format_func=lambda x: {
                'ca': 'Canada', 'us': 'United States', 'gb': 'United Kingdom',
                'au': 'Australia', 'global': 'Global'
            }.get(x, x),
            index=['ca', 'us', 'gb', 'au', 'global'].index(st.session_state.qs_country),
            key="qs_country_input"
        )
    with col4:
        description = st.text_input(
            "One-line description (optional)",
            value=st.session_state.qs_description,
            placeholder="e.g., Nonprofit supporting family caregivers across Ontario",
            key="qs_desc_input"
        )

    # Optional: paste strategy questionnaire answers
    with st.expander("Paste strategy questionnaire answers (optional)"):
        st.caption("Paste the client's full questionnaire responses below. The system will automatically extract target audiences, business goals, topics, and competitors.")
        questionnaire_raw = st.text_area(
            "Strategy questionnaire answers",
            value=st.session_state.get('qs_questionnaire_raw', ''),
            placeholder="Paste the full questionnaire here — any format works.\n\nExample:\nTarget audience: Adult child caregivers over 50, spousal caregivers, healthcare providers\nMain goals: Increase awareness of support programs, drive helpline calls\nKey topics: caregiver burnout, respite care, navigating the healthcare system\nCompetitors: Caregiver Action Network, AARP Caregiving",
            height=200,
            key="qs_questionnaire_input"
        )

    # Check Ahrefs availability
    ahrefs = AhrefsClient()
    ahrefs_available = ahrefs.is_configured

    st.markdown("---")

    if ahrefs_available:
        st.markdown(f"""
        <div style='background: #E8F5E9; padding: 12px 16px; border-radius: 8px;
                    border-left: 4px solid {SUCCESS}; margin: 10px 0;'>
            <strong>Ahrefs API connected</strong> — Keywords and competitors will be pulled automatically from the domain.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background: #FFF3E0; padding: 12px 16px; border-radius: 8px;
                    border-left: 4px solid {WARNING}; margin: 10px 0;'>
            <strong>Ahrefs API not configured</strong> — You can upload an Ahrefs CSV export instead.
            To enable auto-fetch, add your Ahrefs API key to Streamlit secrets under <code>[api_keys] ahrefs = "your_token"</code>.
        </div>
        """, unsafe_allow_html=True)

    # Action buttons
    if ahrefs_available:
        if st.button("Pull Data from Ahrefs", type="primary", use_container_width=True, disabled=not (client_name and domain)):
            if not client_name or not domain:
                st.error("Please enter both a client name and domain.")
                return

            clean_domain = _clean_domain(domain)
            st.session_state.qs_client_name = client_name
            st.session_state.qs_domain = clean_domain
            st.session_state.qs_country = country
            st.session_state.qs_description = description
            st.session_state.qs_questionnaire_raw = questionnaire_raw
            st.session_state.qs_source = 'ahrefs'

            with st.spinner(f"Pulling keywords and competitors for {clean_domain}..."):
                _fetch_ahrefs_data(ahrefs, clean_domain, country)

            if st.session_state.qs_keywords_data or st.session_state.qs_competitors_data:
                st.session_state.qs_step = 'review'
                st.rerun()
            else:
                st.error("No data returned from Ahrefs. Check the domain and try again, or upload a CSV below.")

    # CSV fallback — always show as an option
    with st.expander("Upload Ahrefs CSV export instead" if ahrefs_available else "Upload keyword data (CSV)"):
        _render_csv_upload(client_name, domain, country, description)


def _fetch_ahrefs_data(ahrefs: AhrefsClient, domain: str, country: str):
    """Fetch keywords and competitors from Ahrefs API.

    Strategy: Always pull GLOBAL keywords first (all countries) to get the
    full picture, then also pull the selected country separately for
    competitor data. This ensures we don't miss keywords just because
    the site ranks in multiple markets (e.g., US, CA, GB, DE).
    """
    errors = []

    # Pull keywords globally first — get everything Ahrefs has
    kw_result = ahrefs.get_organic_keywords(domain, country='global', limit=1000, min_volume=10)
    if kw_result.get('error'):
        errors.append(f"Keywords: {kw_result['error']}")
    keywords = kw_result.get('keywords', [])

    # Deduplicate by keyword text (global query may return same keyword from multiple countries)
    seen_kws = set()
    unique_keywords = []
    for kw in keywords:
        kw_text = kw.get('keyword', '').lower().strip()
        if kw_text and kw_text not in seen_kws:
            seen_kws.add(kw_text)
            unique_keywords.append(kw)
    keywords = unique_keywords

    if len(keywords) > 0:
        errors.append(f"Pulled {len(keywords)} unique keywords across all countries")

    # If global query failed or returned nothing, fall back to country + US
    if not keywords:
        kw_result = ahrefs.get_organic_keywords(domain, country=country, limit=500, min_volume=10)
        if not kw_result.get('error'):
            keywords = kw_result.get('keywords', [])
        if len(keywords) < 20 and country.lower() not in ('us', 'global'):
            us_result = ahrefs.get_organic_keywords(domain, country='us', limit=500, min_volume=10)
            if not us_result.get('error'):
                existing_kws = {kw.get('keyword', '').lower() for kw in keywords}
                for kw in us_result.get('keywords', []):
                    if kw.get('keyword', '').lower() not in existing_kws:
                        keywords.append(kw)
                        existing_kws.add(kw.get('keyword', '').lower())

    # Pull competitors — use selected country (competitors endpoint requires a country)
    comp_result = ahrefs.get_organic_competitors(domain, country=country, limit=10)
    if comp_result.get('error'):
        errors.append(f"Competitors: {comp_result['error']}")
    competitors = comp_result.get('competitors', [])

    # If no competitors in selected country, try US
    if not competitors and country.lower() not in ('us', 'global'):
        us_comp_result = ahrefs.get_organic_competitors(domain, country='us', limit=10)
        if not us_comp_result.get('error'):
            competitors = us_comp_result.get('competitors', [])
            if competitors:
                errors.append("Note: Competitors pulled from US data (none found in selected country)")

    # Store any errors/notes so they persist after rerun
    st.session_state.qs_fetch_notes = errors

    # Run through auto-onboarder filtering
    onboarder = ClientAutoOnboarder(
        brand_name=st.session_state.qs_client_name,
        domain=domain,
        countries=country
    )
    onboarder.ingest_ahrefs_keywords(keywords)
    onboarder.ingest_ahrefs_competitors(competitors)

    # Parse questionnaire if provided
    questionnaire = _parse_questionnaire(
        st.session_state.get('qs_questionnaire_raw', ''),
        st.session_state.get('qs_description', '')
    )
    if questionnaire:
        onboarder.ingest_questionnaire(questionnaire)

    filtered = onboarder.filter_keywords()
    personas = onboarder.generate_personas()

    # Store in session
    st.session_state.qs_keywords_data = filtered
    st.session_state.qs_keywords_selected = {
        kw.get('keyword', ''): True for kw in filtered
    }
    st.session_state.qs_competitors_data = onboarder.raw_competitors
    st.session_state.qs_competitors_selected = {
        c.get('domain', ''): True for c in onboarder.raw_competitors
    }
    st.session_state.qs_personas = personas


def _render_csv_upload(client_name, domain, country, description):
    """Render the CSV upload fallback."""
    uploaded_file = st.file_uploader(
        "Upload Ahrefs keyword export or any CSV with keywords",
        type=['csv'],
        key="qs_csv_upload"
    )

    if uploaded_file and client_name and domain:
        try:
            df = pd.read_csv(uploaded_file)
            if df.empty:
                st.error("CSV is empty.")
                return

            # Auto-detect keyword column
            keyword_col = _detect_keyword_column(df)
            volume_col = _detect_volume_column(df)

            # Convert to Ahrefs-like format for the onboarder
            keywords_data = []
            for _, row in df.iterrows():
                kw = str(row[keyword_col]).strip()
                if not kw or kw == 'nan':
                    continue
                vol = 0
                if volume_col:
                    try:
                        vol = int(float(row[volume_col]))
                    except (ValueError, TypeError):
                        vol = 0

                keywords_data.append({
                    'keyword': kw,
                    'volume': vol,
                    'sum_traffic': vol,
                    'best_position': 0,
                    'keyword_difficulty': 0,
                    'is_informational': False,
                    'is_commercial': False,
                    'is_transactional': False,
                    'is_navigational': False,
                })

            st.success(f"Found {len(keywords_data)} keywords from CSV")

            if st.button("Use these keywords", type="primary", key="qs_use_csv"):
                clean_domain = _clean_domain(domain)
                st.session_state.qs_client_name = client_name
                st.session_state.qs_domain = clean_domain
                st.session_state.qs_country = country
                st.session_state.qs_description = description
                st.session_state.qs_source = 'csv'

                # Run through onboarder filtering
                onboarder = ClientAutoOnboarder(
                    brand_name=client_name,
                    domain=clean_domain,
                    countries=country
                )
                onboarder.ingest_ahrefs_keywords(keywords_data)

                # Parse questionnaire if provided
                csv_questionnaire = _parse_questionnaire(
                    st.session_state.get('qs_questionnaire_raw', ''),
                    description
                )
                if csv_questionnaire:
                    onboarder.ingest_questionnaire(csv_questionnaire)

                filtered = onboarder.filter_keywords()
                personas = onboarder.generate_personas()

                st.session_state.qs_keywords_data = filtered
                st.session_state.qs_keywords_selected = {
                    kw.get('keyword', ''): True for kw in filtered
                }
                st.session_state.qs_competitors_data = []
                st.session_state.qs_competitors_selected = {}
                st.session_state.qs_personas = personas
                st.session_state.qs_step = 'review'
                st.rerun()

        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")
    elif not client_name or not domain:
        st.info("Enter a client name and domain above first, then upload your CSV.")


def _render_review_step():
    """Render the review step — filterable keywords, competitors, personas."""

    client_name = st.session_state.qs_client_name
    domain = st.session_state.qs_domain
    keywords = st.session_state.qs_keywords_data
    competitors = st.session_state.qs_competitors_data
    personas = st.session_state.qs_personas

    st.markdown(f"""
    <div style='background: {LIGHT_BG}; padding: 16px; border-radius: 8px; margin-bottom: 20px;'>
        <h4 style='margin: 0;'>{client_name}</h4>
        <span style='color: #666;'>{domain} &middot; {len(keywords)} keywords found &middot;
        {len(competitors)} competitors &middot; {len(personas)} personas</span>
    </div>
    """, unsafe_allow_html=True)

    # Show any fetch notes/errors from the pull
    fetch_notes = st.session_state.get('qs_fetch_notes', [])
    for note in fetch_notes:
        if note.startswith("Note:"):
            st.info(note)
        else:
            st.warning(note)

    # Back button
    if st.button("< Back to setup", key="qs_back"):
        st.session_state.qs_step = 'input'
        st.rerun()

    # Three sections
    tab_kw, tab_comp, tab_personas = st.tabs([
        f"Keywords ({len(keywords)})",
        f"Competitors ({len(competitors)})",
        f"Personas ({len(personas)})"
    ])

    with tab_kw:
        _render_keywords_review(keywords)

    with tab_comp:
        _render_competitors_review(competitors)

    with tab_personas:
        _render_personas_review(personas)

    # Create client button
    st.markdown("---")
    selected_kw_count = sum(1 for v in st.session_state.qs_keywords_selected.values() if v)
    selected_comp_count = sum(1 for v in st.session_state.qs_competitors_selected.values() if v)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Keywords selected", selected_kw_count)
    with col2:
        st.metric("Competitors selected", selected_comp_count)
    with col3:
        st.metric("Personas", len(personas))

    if st.button(
        f"Create {client_name}",
        type="primary",
        use_container_width=True,
        disabled=selected_kw_count == 0,
        key="qs_create_client"
    ):
        _create_client()


def _render_keywords_review(keywords):
    """Render filterable keyword checklist."""

    if not keywords:
        st.info("No keywords found. Go back and try a different domain or upload a CSV.")
        return

    # Filters
    col_filter, col_intent, col_vol = st.columns([2, 1, 1])
    with col_filter:
        filter_text = st.text_input(
            "Filter keywords",
            placeholder="Type to filter...",
            key="qs_kw_filter"
        )
    with col_intent:
        # Collect all intents
        all_intents = set()
        for kw in keywords:
            intent = _infer_intent(kw)
            all_intents.add(intent)
        intent_options = ['All'] + sorted(all_intents)
        filter_intent = st.selectbox("Intent", intent_options, key="qs_kw_intent_filter")
    with col_vol:
        max_vol = max((kw.get('volume', 0) for kw in keywords), default=1000)
        min_volume = st.number_input("Min volume", min_value=0, max_value=max_vol, value=0, key="qs_kw_vol_filter")

    # Bulk actions
    col_all, col_none = st.columns(2)
    with col_all:
        if st.button("Select all visible", key="qs_select_all_kw"):
            for kw in _filter_keywords(keywords, filter_text, filter_intent, min_volume):
                st.session_state.qs_keywords_selected[kw.get('keyword', '')] = True
            st.rerun()
    with col_none:
        if st.button("Deselect all visible", key="qs_deselect_all_kw"):
            for kw in _filter_keywords(keywords, filter_text, filter_intent, min_volume):
                st.session_state.qs_keywords_selected[kw.get('keyword', '')] = False
            st.rerun()

    # Filtered list
    filtered = _filter_keywords(keywords, filter_text, filter_intent, min_volume)
    st.caption(f"Showing {len(filtered)} of {len(keywords)} keywords")

    # Render as checkboxes in a scrollable area
    for i, kw in enumerate(filtered[:100]):  # Cap at 100 for performance
        keyword = kw.get('keyword', '')
        volume = kw.get('volume', 0)
        intent = _infer_intent(kw)
        is_selected = st.session_state.qs_keywords_selected.get(keyword, True)

        col_check, col_info = st.columns([3, 1])
        with col_check:
            new_val = st.checkbox(
                keyword,
                value=is_selected,
                key=f"qs_kw_{i}"
            )
            if new_val != is_selected:
                st.session_state.qs_keywords_selected[keyword] = new_val
        with col_info:
            st.caption(f"vol: {volume:,} · {intent}")

    if len(filtered) > 100:
        st.info(f"Showing first 100 of {len(filtered)} matching keywords. Use filters to narrow down.")

    # Manual add
    with st.expander("Add keywords manually"):
        manual_kw = st.text_area(
            "One keyword per line",
            placeholder="caregiver support programs\nrespite care options near me\nhow to prevent caregiver burnout",
            key="qs_manual_kw"
        )
        if st.button("Add keywords", key="qs_add_manual_kw"):
            if manual_kw:
                for line in manual_kw.strip().split('\n'):
                    kw = line.strip()
                    if kw and kw not in st.session_state.qs_keywords_selected:
                        st.session_state.qs_keywords_data.append({
                            'keyword': kw,
                            'volume': 0,
                            'traffic_potential': 0,
                            'position': None,
                            'difficulty': 0,
                            'is_informational': False,
                            'is_commercial': False,
                            'is_transactional': False,
                            'is_navigational': False,
                        })
                        st.session_state.qs_keywords_selected[kw] = True
                st.rerun()


def _render_competitors_review(competitors):
    """Render competitor checklist."""

    if not competitors:
        st.info("No competitors found. You can add them manually below.")
    else:
        st.caption("Uncheck any competitors that aren't relevant. These will be used for comparison prompts.")
        for i, comp in enumerate(competitors):
            domain = comp.get('domain', '')
            common_kw = comp.get('keywords_common', 0)
            traffic = comp.get('traffic', 0)
            is_selected = st.session_state.qs_competitors_selected.get(domain, True)

            col_check, col_info = st.columns([2, 2])
            with col_check:
                new_val = st.checkbox(
                    domain,
                    value=is_selected,
                    key=f"qs_comp_{i}"
                )
                if new_val != is_selected:
                    st.session_state.qs_competitors_selected[domain] = new_val
            with col_info:
                st.caption(f"{common_kw:,} shared keywords · {traffic:,} est. traffic")

    # Manual add
    with st.expander("Add competitors manually"):
        manual_comp = st.text_area(
            "One domain per line",
            placeholder="competitor1.com\ncompetitor2.ca",
            key="qs_manual_comp"
        )
        if st.button("Add competitors", key="qs_add_manual_comp"):
            if manual_comp:
                for line in manual_comp.strip().split('\n'):
                    domain = _clean_domain(line.strip())
                    if domain and domain not in st.session_state.qs_competitors_selected:
                        st.session_state.qs_competitors_data.append({
                            'domain': domain,
                            'keywords_common': 0,
                            'keywords_exclusive': 0,
                            'traffic': 0,
                        })
                        st.session_state.qs_competitors_selected[domain] = True
                st.rerun()


def _render_personas_review(personas):
    """Render auto-generated personas with ability to tweak."""

    if not personas:
        st.info("Personas will be auto-generated from keyword clusters.")
        return

    st.caption("These were auto-generated from your keyword data. You can rename or remove them.")

    updated_personas = []
    for i, persona in enumerate(personas):
        col_name, col_weight, col_remove = st.columns([3, 1, 1])
        with col_name:
            new_name = st.text_input(
                f"Persona {i+1}",
                value=persona.get('name', ''),
                key=f"qs_persona_name_{i}"
            )
        with col_weight:
            new_weight = st.number_input(
                "Weight",
                min_value=0.0,
                max_value=1.0,
                value=float(persona.get('weight', 0.2)),
                step=0.05,
                key=f"qs_persona_weight_{i}"
            )
        with col_remove:
            st.write("")  # spacer
            remove = st.checkbox("Remove", key=f"qs_persona_remove_{i}")

        if not remove:
            updated = dict(persona)
            updated['name'] = new_name
            updated['weight'] = new_weight
            updated_personas.append(updated)

    # Store updates back
    if updated_personas != personas:
        st.session_state.qs_personas = updated_personas

    # Add persona
    with st.expander("Add a persona"):
        new_persona_name = st.text_input("Persona name", key="qs_new_persona_name")
        if st.button("Add persona", key="qs_add_persona"):
            if new_persona_name:
                st.session_state.qs_personas.append({
                    'id': f"persona_{len(st.session_state.qs_personas) + 1}",
                    'name': new_persona_name,
                    'weight': 0.15,
                    'description': f"Target audience: {new_persona_name}",
                    'priority_topics': [],
                })
                st.rerun()


def _create_client():
    """Create all client files and register."""
    client_name = st.session_state.qs_client_name
    domain = st.session_state.qs_domain
    country = st.session_state.qs_country
    description = st.session_state.qs_description

    # Get selected keywords only
    selected_keywords = [
        kw for kw in st.session_state.qs_keywords_data
        if st.session_state.qs_keywords_selected.get(kw.get('keyword', ''), False)
    ]

    # Get selected competitors only
    selected_competitors = [
        comp for comp in st.session_state.qs_competitors_data
        if st.session_state.qs_competitors_selected.get(comp.get('domain', ''), False)
    ]

    personas = st.session_state.qs_personas

    if not selected_keywords:
        st.error("No keywords selected. Please select at least some keywords.")
        return

    try:
        # Create slug
        client_slug = client_name.lower().replace(' ', '_')
        client_slug = re.sub(r'[^a-z0-9_]', '', client_slug)

        # Build onboarder with selected data
        onboarder = ClientAutoOnboarder(
            brand_name=client_name,
            domain=domain,
            countries=country
        )

        # Set the filtered data directly (user already filtered via checkboxes)
        onboarder.filtered_keywords = selected_keywords
        onboarder.raw_competitors = selected_competitors
        onboarder.generated_personas = personas

        if description:
            onboarder.questionnaire_data = {'business_description': description}

        # Save files
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        summary = onboarder.save_client_files(str(data_dir))

        # Register client
        registry = ClientRegistry()
        registry.add_client(
            client_name=client_name,
            client_slug=client_slug,
            files=summary['files']
        )

        # Sync to GCS
        gcs_success = False
        try:
            from src.client_manager.gcs_sync import GCSClientSync
            gcs_sync = GCSClientSync()
            gcs_success = gcs_sync.sync_client_to_gcs(
                client_slug=client_slug,
                files=summary['files']
            )
        except Exception as e:
            st.warning(f"Cloud backup: {str(e)}")

        # Set as active client
        st.session_state.active_client = client_slug
        st.session_state.generation_config = st.session_state.get('generation_config', {})
        st.session_state.generation_config.update({
            'personas_file': summary['files'].get('personas', ''),
            'keywords_file': summary['files'].get('keywords', ''),
            'client_name': client_name
        })

        # Success!
        st.session_state.qs_step = 'done'
        st.session_state.qs_summary = summary
        st.session_state.qs_gcs_success = gcs_success
        st.balloons()
        st.rerun()

    except Exception as e:
        st.error(f"Error creating client: {str(e)}")
        st.exception(e)


def _render_done_step():
    """Render the success screen after client creation."""
    summary = st.session_state.get('qs_summary', {})
    gcs_success = st.session_state.get('qs_gcs_success', False)
    client_name = st.session_state.qs_client_name

    st.markdown(f"""
    <div style='background: #E8F5E9; padding: 24px; border-radius: 10px;
                border-left: 4px solid {SUCCESS}; text-align: center; margin: 20px 0;'>
        <h2 style='color: {SUCCESS} !important; margin-top: 0;'>{client_name} is ready!</h2>
        <p style='color: {TEXT_COLOR}; font-size: 1.1em;'>
            {summary.get('files', {}).get('keywords_count', 0)} keywords &middot;
            {summary.get('files', {}).get('personas_count', 0)} personas &middot;
            {summary.get('files', {}).get('competitors_count', 0)} competitors
        </p>
        <p style='color: #666;'>
            {'Saved to cloud storage' if gcs_success else 'Saved locally (cloud backup pending)'}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### What's next?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Prompts", type="primary", use_container_width=True, key="qs_goto_generate"):
            st.session_state.page = 'Generate & Review'
            _reset_quick_setup()
            st.rerun()
    with col2:
        if st.button("Set up another client", use_container_width=True, key="qs_another"):
            _reset_quick_setup()
            st.rerun()


def _reset_quick_setup():
    """Reset quick setup session state for a fresh start."""
    keys_to_reset = [k for k in st.session_state if k.startswith('qs_')]
    for key in keys_to_reset:
        del st.session_state[key]


# --- Helper functions ---

def _parse_questionnaire(raw_text: str, description: str = '') -> dict:
    """
    Parse raw strategy questionnaire text into structured data.

    Handles any format — the questionnaire could be Q&A pairs, bullet points,
    freeform paragraphs, or anything else. Extracts:
    - business_description
    - target_audiences (list)
    - important_topics (list)
    - competitors_manual (list)
    - key_features (list)
    - differentiators (list)
    - customer_questions (list)
    """
    if not raw_text.strip() and not description:
        return {}

    result = {}
    if description:
        result['business_description'] = description

    raw = raw_text.strip()
    if not raw:
        return result

    # Normalize: lowercase version for pattern matching, original for extraction
    raw_lower = raw.lower()

    # --- Extract target audiences ---
    audiences = _extract_section(raw, [
        r'target\s*audience[s]?', r'who\s*(?:are|is)\s*(?:your|the|their)\s*(?:target|ideal|primary)',
        r'audience[s]?', r'customer\s*segment[s]?', r'persona[s]?',
        r'who\s*(?:do|does|would)\s*(?:you|they)\s*serve',
        r'who\s*(?:are|is)\s*(?:you|they)\s*trying\s*to\s*reach',
    ])
    if audiences:
        result['target_audiences'] = audiences

    # --- Extract topics / services / focus areas ---
    topics = _extract_section(raw, [
        r'(?:key|priority|important|main|core)\s*topic[s]?',
        r'(?:key|main|core)\s*service[s]?',
        r'(?:key|main|core)\s*offering[s]?',
        r'what\s*(?:do|does)\s*(?:you|they)\s*(?:offer|provide|do)',
        r'focus\s*area[s]?', r'program[s]?',
        r'what\s*(?:topic|subject|area)[s]?',
    ])
    if topics:
        result['important_topics'] = topics

    # --- Extract competitors ---
    competitors = _extract_section(raw, [
        r'competitor[s]?', r'competing\s*(?:brand|company|org)',
        r'who\s*(?:do|does)\s*(?:you|they)\s*compete\s*with',
        r'alternative[s]?', r'similar\s*(?:brand|company|org|business)',
    ])
    if competitors:
        result['competitors_manual'] = competitors

    # --- Extract differentiators ---
    diffs = _extract_section(raw, [
        r'differentiator[s]?', r'what\s*(?:make|set)[s]?\s*(?:you|them)\s*(?:different|unique|apart)',
        r'unique\s*(?:value|selling|advantage)', r'(?:key|main)\s*(?:strength|advantage)[s]?',
        r'why\s*(?:should|would)\s*(?:someone|people|clients)\s*choose',
    ])
    if diffs:
        result['differentiators'] = diffs

    # --- Extract customer questions ---
    questions = _extract_section(raw, [
        r'(?:common|frequent|typical)\s*question[s]?',
        r'what\s*(?:do|does)\s*(?:people|customer|client)[s]?\s*(?:ask|want to know)',
        r'FAQ', r'question[s]?\s*(?:you|they)\s*(?:get|hear|receive)',
    ])
    if questions:
        result['customer_questions'] = questions

    # --- Extract key features ---
    features = _extract_section(raw, [
        r'(?:key|main|core)\s*feature[s]?',
        r'product[s]?\s*(?:or|and|/)\s*service[s]?',
    ])
    if features:
        result['key_features'] = features

    # If we got nothing structured but have raw text, use it as business description
    if not result.get('target_audiences') and not result.get('important_topics'):
        # Fall back: just store the whole thing as business description
        if not result.get('business_description'):
            result['business_description'] = raw[:500]

    return result


def _extract_section(raw_text: str, patterns: list) -> list:
    """
    Extract a list of items from raw text by finding a section header
    that matches one of the patterns, then parsing the content after it.

    Handles formats like:
    - "Target audience: X, Y, Z"
    - "Target audience:\n- X\n- Y\n- Z"
    - "Q: Who is your target audience?\nA: X, Y, and Z"
    - "1. Target audiences\n  - X\n  - Y"
    """
    import re

    for pattern in patterns:
        # Try to find the section header
        match = re.search(
            rf'(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:Q:\s*)?{pattern}\s*[:\?\-—]*\s*(?:A:\s*)?\n?(.*?)(?=\n\s*(?:\d+[\.\)]\s*)?(?:Q:\s*)?[A-Z][a-z]{{3,}}.*?[:\?]|\Z)',
            raw_text,
            re.IGNORECASE | re.DOTALL
        )
        if match:
            content = match.group(1).strip()
            if not content:
                continue

            items = _parse_list_items(content)
            if items:
                return items

    return []


def _parse_list_items(text: str) -> list:
    """
    Parse a block of text into individual list items.
    Handles bullet points, numbered lists, comma-separated, newline-separated.
    """
    import re

    # First try: bullet points or numbered items
    bullets = re.findall(r'(?:^|\n)\s*(?:[-•*●◦▪]|\d+[\.\)])\s*(.+)', text)
    if bullets:
        return [b.strip().rstrip(',;') for b in bullets if b.strip() and len(b.strip()) > 2]

    # Second try: newline-separated (if multiple lines)
    lines = [l.strip().rstrip(',;') for l in text.split('\n') if l.strip() and len(l.strip()) > 2]
    if len(lines) > 1:
        return lines

    # Third try: comma or semicolon separated
    if ',' in text or ';' in text:
        items = re.split(r'[,;]', text)
        # Handle "X, Y, and Z" pattern
        cleaned = []
        for item in items:
            item = item.strip()
            item = re.sub(r'^(?:and|or)\s+', '', item).strip()
            if item and len(item) > 2:
                cleaned.append(item)
        if cleaned:
            return cleaned

    # Single item
    if text.strip() and len(text.strip()) > 2:
        return [text.strip()]

    return []


def _infer_intent(kw_data: dict) -> str:
    """Infer intent from keyword data."""
    if kw_data.get('is_informational'):
        return 'informational'
    if kw_data.get('is_commercial'):
        return 'commercial'
    if kw_data.get('is_transactional'):
        return 'transactional'
    if kw_data.get('is_navigational'):
        return 'navigational'

    # Fallback: pattern matching
    keyword = kw_data.get('keyword', '').lower()
    if any(w in keyword for w in ['how', 'what', 'why', 'when', 'guide', 'tips']):
        return 'informational'
    if any(w in keyword for w in ['best', 'top', 'compare', 'vs', 'review']):
        return 'commercial'
    if any(w in keyword for w in ['buy', 'price', 'order', 'shop', 'discount']):
        return 'transactional'
    return 'informational'


def _filter_keywords(keywords, filter_text, filter_intent, min_volume):
    """Apply filters to keyword list."""
    filtered = keywords

    if filter_text:
        ft = filter_text.lower()
        filtered = [kw for kw in filtered if ft in kw.get('keyword', '').lower()]

    if filter_intent and filter_intent != 'All':
        filtered = [kw for kw in filtered if _infer_intent(kw) == filter_intent]

    if min_volume > 0:
        filtered = [kw for kw in filtered if kw.get('volume', 0) >= min_volume]

    return filtered


def _detect_keyword_column(df):
    """Auto-detect keyword column in CSV."""
    keyword_columns = [
        'keyword', 'keywords', 'search term', 'search_term', 'query',
        'search query', 'term', 'keyphrase', 'key phrase'
    ]
    for col in df.columns:
        if col.lower() in keyword_columns:
            return col
    for col in df.columns:
        for kw_col in keyword_columns:
            if kw_col in col.lower():
                return col
    return df.columns[0]


def _detect_volume_column(df):
    """Auto-detect volume column in CSV."""
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


# --- Existing client management ---

def _render_existing_clients():
    """Show existing clients with edit/delete options."""
    registry = ClientRegistry()
    clients = registry.get_all_clients()

    if not clients:
        return

    st.markdown("---")
    st.markdown("### Your clients")

    for client in clients:
        name = client.get('name', 'Unknown')
        slug = client.get('slug', '')
        created = client.get('created_at', '')[:10]

        col_name, col_date, col_actions = st.columns([3, 1, 1])
        with col_name:
            is_active = st.session_state.get('active_client') == slug
            active_badge = " *(active)*" if is_active else ""
            st.markdown(f"**{name}**{active_badge}")
        with col_date:
            st.caption(created)
        with col_actions:
            if not is_active:
                if st.button("Activate", key=f"qs_activate_{slug}"):
                    st.session_state.active_client = slug
                    files = client.get('files', {})
                    st.session_state.generation_config = st.session_state.get('generation_config', {})
                    st.session_state.generation_config.update({
                        'personas_file': files.get('personas', ''),
                        'keywords_file': files.get('keywords', ''),
                        'client_name': name
                    })
                    st.rerun()


# --- Main render ---

def render():
    """Main render function for Quick Setup page."""
    _apply_theme()
    _init_session_state()

    st.title("Quick Setup")
    st.caption("Add a new client in under 2 minutes")

    step = st.session_state.qs_step

    if step == 'input':
        _render_input_step()
        _render_existing_clients()
    elif step == 'review':
        _render_review_step()
    elif step == 'done':
        _render_done_step()
    else:
        st.session_state.qs_step = 'input'
        st.rerun()
