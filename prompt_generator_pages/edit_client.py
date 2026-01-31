"""
Edit Client - Comprehensive client information editing interface
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, 'src')
from src.data.brand_config_manager import BrandConfigManager

# Brand colors
DARK_PURPLE = '#4A4458'
CREAM = '#E8D7A0'
OFF_WHITE = '#FBFBEF'


def render_edit_client(client_slug: str, client_name: str):
    """
    Render the edit client interface.

    Args:
        client_slug: Client slug (e.g., 'natasha_denona')
        client_name: Client display name (e.g., 'Natasha Denona')
    """
    st.title(f"✏️ Edit Client: {client_name}")

    # Load brand config
    data_dir = Path('data')
    brand_config_path = data_dir / f"{client_slug}_brand_config.json"

    if not brand_config_path.exists():
        st.error(f"❌ Brand config not found for {client_name}")
        st.info("This client may have been created before the brand config system was implemented.")
        if st.button("Create Brand Config"):
            # Create a default config
            manager = BrandConfigManager()
            config = manager.create_default_config(
                brand_name=client_name,
                website='',
                description='',
                aliases=[]
            )
            manager.save_config(str(brand_config_path), config)
            st.success("✅ Brand config created! Refresh the page.")
            st.rerun()
        return

    # Load config
    manager = BrandConfigManager()
    config = manager.load_config(str(brand_config_path))

    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Basic Info",
        "🎯 Business Goals",
        "🏆 Expected Competitors",
        "🔍 Discovered Competitors",
        "⚙️ Advanced"
    ])

    # TAB 1: BASIC INFO
    with tab1:
        st.markdown(f"<h3 style='color: {CREAM};'>Basic Client Information</h3>", unsafe_allow_html=True)

        with st.form("basic_info_form"):
            brand_name = st.text_input(
                "Client/Brand Name",
                value=config['brand'].get('name', ''),
                help="The primary brand name"
            )

            website = st.text_input(
                "Website URL",
                value=config['brand'].get('website', ''),
                help="The client's primary website URL"
            )

            description = st.text_area(
                "Brand Description",
                value=config['brand'].get('description', ''),
                help="A brief description of the brand",
                height=100
            )

            aliases_text = st.text_area(
                "Brand Aliases (one per line)",
                value='\n'.join(config['brand'].get('aliases', [])),
                help="Alternative names or abbreviations for this brand",
                height=80
            )

            submitted = st.form_submit_button("💾 Save Basic Info", use_container_width=True)

            if submitted:
                # Update config
                config['brand']['name'] = brand_name
                config['brand']['website'] = website
                config['brand']['description'] = description
                config['brand']['aliases'] = [a.strip() for a in aliases_text.split('\n') if a.strip()]

                try:
                    manager.save_config(str(brand_config_path), config)
                    st.success("✅ Basic info updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving: {str(e)}")

    # TAB 2: BUSINESS GOALS
    with tab2:
        st.markdown(f"<h3 style='color: {CREAM};'>Business Goals & Strategy</h3>", unsafe_allow_html=True)

        business_goals = config['brand'].get('business_goals', {})

        with st.form("business_goals_form"):
            revenue_targets = st.text_input(
                "Revenue/Growth Targets for 2026",
                value=business_goals.get('revenue_targets', ''),
                help="What are the client's revenue or growth objectives?"
            )

            market_positioning = st.text_input(
                "How do they want to be positioned in AI responses?",
                value=business_goals.get('market_positioning', ''),
                help="Their desired market position when AI tools recommend them"
            )

            # Convert target metrics from list to text
            target_metrics_list = business_goals.get('target_metrics', [])
            target_metrics_text = '\n'.join(target_metrics_list) if isinstance(target_metrics_list, list) else target_metrics_list

            target_metrics = st.text_area(
                "What metrics matter most to them?",
                value=target_metrics_text,
                help="List the key success metrics they're tracking (one per line)",
                height=100
            )

            freeform_notes = st.text_area(
                "Additional Strategy Notes",
                value=business_goals.get('freeform_notes', ''),
                help="Freeform notes about their strategy",
                height=120
            )

            submitted = st.form_submit_button("💾 Save Business Goals", use_container_width=True)

            if submitted:
                # Parse target metrics
                target_metrics_list = [m.strip() for m in target_metrics.split('\n') if m.strip()]

                # Update config
                if 'business_goals' not in config['brand']:
                    config['brand']['business_goals'] = {}

                config['brand']['business_goals'] = {
                    'revenue_targets': revenue_targets,
                    'market_positioning': market_positioning,
                    'target_metrics': target_metrics_list,
                    'freeform_notes': freeform_notes
                }

                try:
                    manager.save_config(str(brand_config_path), config)
                    st.success("✅ Business goals updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving: {str(e)}")

    # TAB 3: EXPECTED COMPETITORS
    with tab3:
        st.markdown(f"<h3 style='color: {CREAM};'>Expected Competitors</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: {OFF_WHITE}; margin-bottom: 16px;'>Manage your tracked competitors. Categorize them as Direct, Adjacent, or Aspirational.</p>", unsafe_allow_html=True)

        expected_competitors = config.get('competitors', {}).get('expected', [])

        # Add new competitor form
        with st.expander("➕ Add New Competitor", expanded=False):
            with st.form("add_competitor_form"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    new_comp_name = st.text_input("Competitor Name *")

                with col2:
                    new_comp_category = st.selectbox(
                        "Category *",
                        options=["direct", "adjacent", "aspirational"]
                    )

                new_comp_website = st.text_input("Website URL (Optional)")
                new_comp_notes = st.text_area("Notes (Optional)", height=80)

                submitted = st.form_submit_button("Add Competitor")

                if submitted and new_comp_name:
                    try:
                        config = manager.add_competitor(
                            config,
                            name=new_comp_name,
                            website=new_comp_website,
                            category=new_comp_category,
                            notes=new_comp_notes
                        )
                        manager.save_config(str(brand_config_path), config)
                        st.success(f"✅ Added {new_comp_name}!")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Error adding competitor: {str(e)}")

        # Display existing competitors
        if expected_competitors:
            st.markdown(f"<p style='color: {CREAM}; font-weight: 600; margin-top: 24px;'>Current Competitors ({len(expected_competitors)})</p>", unsafe_allow_html=True)

            category_emoji = {"direct": "🎯", "adjacent": "🔄", "aspirational": "⭐"}

            for comp in expected_competitors:
                category = comp.get('category', 'direct')
                emoji = category_emoji.get(category, "📊")

                with st.expander(f"{emoji} {comp['name']} ({category.title()})"):
                    st.markdown(f"**Website:** {comp.get('website', 'N/A')}")
                    st.markdown(f"**Added:** {comp.get('added_date', 'Unknown')}")
                    st.markdown(f"**Notes:** {comp.get('notes', 'No notes')}")

                    # Edit form
                    with st.form(f"edit_comp_{comp['name']}"):
                        st.markdown("#### Edit Competitor")

                        new_category = st.selectbox(
                            "Category",
                            options=["direct", "adjacent", "aspirational"],
                            index=["direct", "adjacent", "aspirational"].index(category),
                            key=f"cat_{comp['name']}"
                        )

                        new_website = st.text_input(
                            "Website",
                            value=comp.get('website', ''),
                            key=f"web_{comp['name']}"
                        )

                        new_notes = st.text_area(
                            "Notes",
                            value=comp.get('notes', ''),
                            height=80,
                            key=f"notes_{comp['name']}"
                        )

                        col1, col2 = st.columns(2)

                        with col1:
                            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                try:
                                    config = manager.update_competitor(
                                        config,
                                        competitor_name=comp['name'],
                                        category=new_category,
                                        website=new_website,
                                        notes=new_notes
                                    )
                                    manager.save_config(str(brand_config_path), config)
                                    st.success(f"✅ Updated {comp['name']}!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating: {str(e)}")

                        with col2:
                            if st.form_submit_button("🗑️ Remove", use_container_width=True):
                                try:
                                    config = manager.remove_competitor(config, comp['name'])
                                    manager.save_config(str(brand_config_path), config)
                                    st.success(f"✅ Removed {comp['name']}!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error removing: {str(e)}")
        else:
            st.info("No competitors added yet. Use the form above to add your first competitor.")

    # TAB 4: DISCOVERED COMPETITORS
    with tab4:
        st.markdown(f"<h3 style='color: {CREAM};'>Discovered Competitors</h3>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background-color: rgba(232, 215, 160, 0.15); padding: 16px; border-radius: 6px; margin-bottom: 20px;'>
            <p style='color: {CREAM}; margin: 0;'>
                ⚠️ <strong>These brands appeared in AI responses but weren't on your expected list.</strong>
            </p>
            <p style='color: {OFF_WHITE}; margin: 8px 0 0 0; font-size: 0.9em;'>
                They represent emerging threats or market shifts. You can promote them to your expected competitors or dismiss them.
            </p>
        </div>
        """, unsafe_allow_html=True)

        discovered_competitors = config.get('competitors', {}).get('discovered', [])

        if discovered_competitors:
            for disc in discovered_competitors:
                if disc.get('promoted_to_expected', False):
                    continue  # Skip already promoted

                status = disc.get('status', 'occasional_mention')
                status_emoji = "🔴" if status == "emerging_threat" else "🟡"
                status_label = status.replace('_', ' ').title()

                with st.expander(f"{status_emoji} {disc['name']} - {disc.get('mention_count', 0)} mentions"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Mention Rate", f"{disc.get('mention_rate', 0):.1f}%")

                    with col2:
                        st.metric("First Seen", disc.get('first_seen', 'Unknown'))

                    with col3:
                        st.metric("Status", status_label)

                    st.warning(f"⚠️ This competitor wasn't on your tracking list but showed up {disc.get('mention_count', 0)} times in AI responses.")

                    # Actions
                    col1, col2 = st.columns(2)

                    with col1:
                        with st.form(f"promote_{disc['name']}"):
                            st.markdown("**Promote to Expected Competitors**")

                            promote_category = st.selectbox(
                                "Choose category",
                                options=["direct", "adjacent", "aspirational"],
                                key=f"promote_cat_{disc['name']}"
                            )

                            promote_notes = st.text_area(
                                "Notes",
                                placeholder=f"Discovered in AI responses on {disc.get('first_seen', 'unknown date')}",
                                height=60,
                                key=f"promote_notes_{disc['name']}"
                            )

                            if st.form_submit_button("⬆️ Promote", use_container_width=True):
                                try:
                                    config = manager.promote_discovered_competitor(
                                        config,
                                        discovered_name=disc['name'],
                                        category=promote_category,
                                        notes=promote_notes
                                    )
                                    manager.save_config(str(brand_config_path), config)
                                    st.success(f"✅ Promoted {disc['name']} to {promote_category} competitors!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error promoting: {str(e)}")

                    with col2:
                        st.markdown("**Dismiss**")
                        st.markdown("Remove from discovered list if not relevant")

                        if st.button(f"🗑️ Dismiss {disc['name']}", key=f"dismiss_{disc['name']}", use_container_width=True):
                            try:
                                config = manager.dismiss_discovered_competitor(config, disc['name'])
                                manager.save_config(str(brand_config_path), config)
                                st.success(f"✅ Dismissed {disc['name']}!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error dismissing: {str(e)}")
        else:
            st.success("✅ No unexpected competitors found. All mentioned brands are on your tracking list or haven't been analyzed yet.")

    # TAB 5: ADVANCED
    with tab5:
        st.markdown(f"<h3 style='color: {CREAM};'>Advanced Configuration</h3>", unsafe_allow_html=True)
        st.warning("⚠️ Advanced users only. Editing raw JSON/CSV can break client configuration.")

        # Brand Config JSON Editor
        with st.expander("📝 Edit Brand Config JSON"):
            config_json = st.text_area(
                "Brand Configuration JSON",
                value=json.dumps(config, indent=2),
                height=400,
                key="config_json"
            )

            if st.button("💾 Save Brand Config JSON"):
                try:
                    new_config = json.loads(config_json)
                    is_valid, errors = manager.validate_schema(new_config)

                    if is_valid:
                        manager.save_config(str(brand_config_path), new_config)
                        st.success("✅ Brand config updated!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid schema:")
                        for error in errors:
                            st.error(f"- {error}")
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {str(e)}")
                except Exception as e:
                    st.error(f"Error saving: {str(e)}")

        # Personas JSON Editor
        personas_path = data_dir / f"{client_slug}_personas.json"
        if personas_path.exists():
            with st.expander("👥 Edit Personas JSON"):
                with open(personas_path, 'r') as f:
                    personas_data = json.load(f)

                personas_json = st.text_area(
                    "Personas JSON",
                    value=json.dumps(personas_data, indent=2),
                    height=400,
                    key="personas_json"
                )

                if st.button("💾 Save Personas JSON"):
                    try:
                        new_personas = json.loads(personas_json)
                        with open(personas_path, 'w') as f:
                            json.dump(new_personas, f, indent=2)
                        st.success("✅ Personas updated!")
                        st.rerun()
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON: {str(e)}")
                    except Exception as e:
                        st.error(f"Error saving: {str(e)}")

        # Keywords CSV Editor
        keywords_path = data_dir / f"{client_slug}_keywords.csv"
        if keywords_path.exists():
            with st.expander("🔑 Edit Keywords CSV"):
                df = pd.read_csv(keywords_path)

                st.markdown("**Current Keywords:**")
                st.dataframe(df, use_container_width=True, height=300)

                st.markdown("**Upload Replacement CSV:**")
                new_keywords_file = st.file_uploader(
                    "Upload new keywords CSV",
                    type=['csv'],
                    key="new_keywords"
                )

                if new_keywords_file and st.button("💾 Replace Keywords CSV"):
                    try:
                        new_df = pd.read_csv(new_keywords_file)
                        new_df.to_csv(keywords_path, index=False)
                        st.success("✅ Keywords updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving: {str(e)}")


def render():
    """Render edit client page based on active client."""
    if 'active_client' not in st.session_state or not st.session_state.active_client:
        st.warning("⚠️ No active client. Go to **Client Manager** to select a client first.")
        return

    client_slug = st.session_state.active_client
    client_name = st.session_state.generation_config.get('client_name', 'Unknown Client')

    render_edit_client(client_slug, client_name)
